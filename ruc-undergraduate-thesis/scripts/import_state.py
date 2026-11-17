"""Recoverable import workspace. Only promote completed imports to the destination."""
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import time


def digest(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''): h.update(block)
    return h.hexdigest()


def atomic_json(path, value):
    path = Path(path)
    temporary = path.with_name(path.name + '.tmp')
    temporary.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    os.replace(temporary, path)


class Session:
    def __init__(self, api, args, kind):
        self.api, self.args = api, args
        self.target = Path(args.output).expanduser().resolve()
        self.root = self.target.with_name('.' + self.target.name + '.import')
        self.project = self.root / 'project'
        self.state_path = self.root / 'state.json'
        self.identity = {'kind': kind, 'source': str(Path(args.source).resolve()),
                         'source_sha256': digest(args.source), 'options': {}}
        for key in ('portable', 'dpi', 'ocr', 'ocr_all', 'ocr_language', 'track_changes', 'source_root'):
            self.identity['options'][key] = getattr(args, key, None)
        self.identity['metadata_sha256'] = digest(args.metadata) if args.metadata else None
        self.identity['implementation'] = {p.name: digest(p) for p in sorted((api.ROOT / 'scripts').glob('*.py'))}
        self.identity['template'] = {p.relative_to(api.TEMPLATE).as_posix(): digest(p)
                                     for p in sorted(api.TEMPLATE.rglob('*')) if p.is_file()}
        if kind == 'tex':
            source_root = Path(getattr(args, 'source_root', None) or Path(args.source).parent).resolve()
            if self.target == source_root or self.target.is_relative_to(source_root):
                raise ValueError('Use an output directory outside source-root to avoid recursive copying.')
            self.identity['source_tree'] = {p.relative_to(source_root).as_posix(): digest(p)
                for p in sorted(source_root.rglob('*')) if p.is_file()
                and not any(x in {'.git', 'build', '__pycache__'} for x in p.relative_to(source_root).parts)
                and not p.name.endswith(('.aux', '.log', '.toc', '.bcf', '.run.xml', '.synctex.gz'))}

    def save(self):
        atomic_json(self.state_path, self.state)

    def step(self, name, action, products):
        self.state['current_stage'] = name
        self.save()
        completed = self.state['completed'].get(name)
        if completed:
            for rel, expected in completed['files'].items():
                path = self.project / rel
                if not path.is_file() or digest(path) != expected:
                    raise ValueError(f'Checkpoint artifact changed: {rel}; use --retry to preserve it and restart safely.')
            return completed['result']
        result = action()
        files = {}
        for relative in products:
            path = self.project / relative
            if not path.exists(): raise ValueError(f'Stage {name} did not produce {relative}')
            for p in sorted(path.rglob('*')) if path.is_dir() else [path]:
                if p.is_file(): files[p.relative_to(self.project).as_posix()] = digest(p)
        self.state['completed'][name] = {'files': files, 'result': result}
        self.save()
        return result

    def initialize(self):
        # Template copy may have been interrupted. Only this owned, uncheckpointed
        # project may be removed; completed stages and external paths are untouched.
        def create():
            if self.project.exists():
                if self.project.is_symlink() or self.project.resolve().parent != self.root.resolve():
                    raise ValueError('Unexpected workspace path; refusing cleanup.')
                shutil.rmtree(self.project)
            self.api.init_project(self.project, self.args.metadata, portable=self.args.portable)
        self.step('template', create, ['project.json', 'main.tex', 'metadata.tex', 'ructhesis.cls'])
        return self.project

    def execute(self, importer):
        if self.target.exists(): raise ValueError(f'Output already exists: {self.target}')
        self.target.parent.mkdir(parents=True, exist_ok=True)
        lock = self.root.with_name(self.root.name + '.lock')
        try:
            fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            raise ValueError(f'Import lock exists: {lock}. If its process has exited, remove only this lock and use --resume.')
        os.write(fd, str(os.getpid()).encode()); os.close(fd)
        try:
            resume, retry = getattr(self.args, 'resume', False), getattr(self.args, 'retry', False)
            if self.root.exists():
                if self.root.is_symlink() or not self.state_path.is_file():
                    raise ValueError(f'Unrecognized workspace: {self.root}; choose another output.')
                old = self.api.read_json(self.state_path)
                if old.get('schema') != 1 or old.get('target') != str(self.target):
                    raise ValueError('Workspace identity mismatch; choose another output.')
                if retry:
                    backup = self.root.with_name(self.root.name + '.saved-' + str(time.time_ns()))
                    self.root.rename(backup)
                elif not resume:
                    raise ValueError(f'Interrupted import at {self.root}; use --resume or --retry.')
                elif old['identity'] != self.identity:
                    raise ValueError('Input, options, template or scripts changed; use --retry (keeps old workspace).')
            elif resume:
                raise ValueError('No checkpoint to resume; omit --resume.')
            if not self.root.exists():
                self.root.mkdir()
                self.state = {'schema': 1, 'target': str(self.target), 'identity': self.identity,
                              'status': 'running', 'completed': {}, 'attempts': []}
            else: self.state = old
            self.state['attempts'].append({'started': time.time(), 'resume': resume})
            self.state['status'] = 'running'
            self.save()
            try:
                self.state['current_stage'] = 'preflight'; self.save()
                report = self.api.doctor(self.args)
                atomic_json(self.root / 'environment.json', report)
                if not report['ready']:
                    raise ValueError('Dependencies missing: ' + '; '.join(x['item'] + ': ' + x['remedy'] for x in report['missing']))
                args = copy.copy(self.args)
                args.output = str(self.project)
                args._session = self
                self.state['current_stage'] = 'input-validation'; self.save()
                result = importer(args)
                self.state['status'] = 'completed'
                self.state['current_stage'] = 'complete'; self.save()
                atomic_json(self.project / 'import-state.json', self.state)
                shutil.copy2(self.root / 'environment.json', self.project / 'environment.json')
                if self.target.exists(): raise ValueError('Destination appeared during import; refusing to replace it.')
                self.project.rename(self.target)
                # Keep small state/logs for diagnosis; the staging project is gone.
                result['project'] = str(self.target)
                return result
            except BaseException as exc:
                self.state['status'] = 'failed'
                self.state['attempts'][-1].update(error=str(exc), stage=self.state['current_stage'])
                self.save()
                raise
        finally:
            lock.unlink()
