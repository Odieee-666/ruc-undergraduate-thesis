"""Migrate literal TeX dependencies from a byte-preserving source snapshot."""
import codecs
from pathlib import Path, PureWindowsPath
import re


def decode(path, relative):
    raw = path.read_bytes()
    bom = raw.startswith(codecs.BOM_UTF8)
    try:
        text = raw.decode('utf-8')
        return (text[1:], 'utf-8-sig') if bom else (text, 'utf-8')
    except UnicodeDecodeError as exc:
        if bom:
            raise ValueError(f'{relative}: invalid UTF-8 after BOM at byte {exc.start}') from exc
        utf8_offset = exc.start
    try:
        return raw.decode('gb18030'), 'gb18030'
    except UnicodeDecodeError as exc:
        raise ValueError(f'{relative}: invalid UTF-8 at byte {utf8_offset}; '
                         f'invalid GB18030 at byte {exc.start}') from exc


COMMAND = re.compile(r'\\(input|include|addbibresource|includegraphics|inputencoding|'
                     r'UseRawInputEncoding|XeTeX(?:input|default)encoding|usepackage|RequirePackage)(?![A-Za-z@])')
ARGUMENT = re.compile(r'\s*(?:\*\s*)?(?:\[[^\]]*\]\s*)?\{([^{}]*)\}')
PLAIN_INPUT = re.compile(r'[ \t]+([^\s{}\\%]+)(?=\s|%|$)')


class Migration:
    def __init__(self, project, root, entry, mask, session):
        self.project, self.root, self.entry, self.mask = project, root, entry, mask
        self.session = session
        self.files = {}
        self.issues = []
        self.active = set()
        self.bibliography = []
        self.preamble = ''

    def resolve(self, value, parent, name):
        if not value or re.search(r'[\\{}#$%&~^:\r\n\x00"]', value):
            return None
        if Path(value).is_absolute() or PureWindowsPath(value).anchor:
            return None
        if name in ('input', 'include') and not value.endswith('.tex'):
            value += '.tex'
        # Ordinary TeX searches from the entry's directory. Also support a
        # chapter-local literal when the entry-relative file does not exist.
        for directory in dict.fromkeys((self.entry.parent, parent)):
            path = (self.root / directory / value).resolve()
            if not path.is_relative_to(self.root):
                continue
            rel = path.relative_to(self.root)
            archived = self.project / 'source' / rel
            if archived.is_file():
                return rel
            if name == 'includegraphics' and not rel.suffix and any(
                archived.with_suffix(ext).is_file() for ext in ('.pdf', '.png', '.jpg', '.jpeg', '.eps')
            ):
                # Preserve the extensionless name so graphicx selects the format.
                return rel
        return None

    def convert(self, relative, bib=False):
        key = relative.as_posix()
        if key in self.files:
            return self.files[key]['work_path']
        original = Path('source') / relative
        text, encoding = decode(self.project / original, key)
        if encoding == 'gb18030':
            self.issues.append(f'{key}: GB18030 fallback used; verify the decoded Chinese text.')
        if bib:
            migrated = text
        else:
            text = text.replace('\r\n', '\n').replace('\r', '\n')
            self.active.add(relative)
            migrated = self.tex(relative, text)
            self.active.remove(relative)
        if relative == self.entry:
            work = Path('content/body.tex')
        elif migrated != text or encoding == 'gb18030':
            work = Path('tex-work') / relative
        else:
            work = original
        if work != original:
            target = self.project / work
            target.parent.mkdir(parents=True, exist_ok=True)
            self.session.step('tex-file:' + key, lambda: target.write_text(migrated, encoding='utf-8'),
                              [work.as_posix()])
        self.files[key] = {'source_path': key, 'decoder': encoding, 'work_path': work.as_posix()}
        return work.as_posix()

    def tex(self, relative, text):
        clean = self.mask(text)
        body_start, body_end = 0, len(text)
        if relative == self.entry:
            begin = re.search(r'\\begin\s*\{document\}', clean)
            end = re.search(r'\\end\s*\{document\}', clean)
            if bool(begin) != bool(end) or (begin and end.start() < begin.end()):
                raise ValueError('Unbalanced document environment; inspect source before migration.')
            if begin:
                body_start, body_end = begin.end(), end.start()
            self.preamble = text[:begin.start()] if begin else ''

        edits = []
        for command in COMMAND.finditer(clean, 0, body_end):
            name = command[1]
            arg = ARGUMENT.match(clean, command.end())
            if not arg and name == 'input':
                arg = PLAIN_INPUT.match(clean, command.end())
            value = text[arg.start(1):arg.end(1)] if arg else ''
            where = f'{relative.as_posix()}:{text.count(chr(10), 0, command.start()) + 1}'
            if name not in ('input', 'include', 'addbibresource', 'includegraphics'):
                self.issues.append(f'{where}: review original \\{name} {value} for XeLaTeX compatibility.')
                continue
            target = self.resolve(value, relative.parent, name)
            preamble_bib = name == 'addbibresource' and command.start() < body_start
            if not target or target in self.active:
                self.issues.append(f'{where}: review unresolved or cyclic \\{name} path in the original source.')
                continue
            if name == 'includegraphics':
                work = (Path('source') / target).as_posix()
            else:
                work = self.convert(target, bib=name == 'addbibresource')
            if name == 'include' and work.endswith('.tex'):
                work = work[:-4]  # LaTeX adds the extension to include files.
            if arg.re == PLAIN_INPUT:
                work = '{' + work + '}'
            if preamble_bib:
                self.bibliography.append(text[command.start():arg.start(1)] + work + text[arg.end(1):arg.end()])
            if command.start() >= body_start:
                edits.append((arg.start(1), arg.end(1), work))

        pieces = []
        cursor = body_start
        for start, end, replacement in edits:
            pieces.extend((text[cursor:start], replacement))
            cursor = end
        return ''.join(pieces) + text[cursor:body_end]

    def run(self):
        self.convert(self.entry)
        prefix = (Path('source') / self.entry.parent).as_posix() + '/'
        extra = ('% Review original-preamble.tex.txt; migrate required macros without old layout settings.\n'
                 '\\graphicspath{{' + prefix + '}}\n'
                 '\\makeatletter\n\\def\\input@path{{' + prefix + '}}\n\\makeatother\n')
        def write_preamble():
            (self.project / 'original-preamble.tex.txt').write_text(self.preamble, encoding='utf-8')
            (self.project / 'preamble-extra.tex').write_text(
                extra + ''.join(cmd + '\n' for cmd in self.bibliography), encoding='utf-8')
        self.session.step('tex-preamble', write_preamble, ['original-preamble.tex.txt', 'preamble-extra.tex'])
        return {'files': list(self.files.values()), 'issues': self.issues}
