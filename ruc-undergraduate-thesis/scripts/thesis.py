#!/usr/bin/env python3
"""RUC thesis workspace creation, conservative imports, build and visual review."""
import argparse
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
from types import SimpleNamespace
import zipfile
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
TEMPLATE = ROOT / 'assets' / 'template'
PROFILE = 'ruc-2021-local'


def helper(name):
    spec = importlib.util.spec_from_file_location('ruc_' + name, ROOT / 'scripts' / (name + '.py'))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def managed_import(kind):
    def decorate(function):
        def wrapped(args):
            args = argparse.Namespace(**vars(args))
            args.command = 'import-' + kind
            return helper('import_state').Session(SimpleNamespace(**globals()), args, kind).execute(function)
        return wrapped
    return decorate


def stage(args, name, action, products):
    return args._session.step(name, action, products)


def write_json(path, data):
    Path(path).write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def tex_escape(value):
    replacements = {'\\': r'\textbackslash{}', '{': r'\{', '}': r'\}',
                    '#': r'\#', '$': r'\$', '%': r'\%', '&': r'\&',
                    '_': r'\_', '^': r'\textasciicircum{}', '~': r'\textasciitilde{}'}
    return ''.join(replacements.get(c, c) for c in str(value)).replace('\n', ' ')


def tool(name, explicit=None):
    if explicit:
        p = Path(explicit).expanduser().resolve()
        if not p.is_file():
            raise ValueError(f'Tool not found: {p}')
        return str(p)
    found = shutil.which(name)
    if found:
        return found
    if name == 'pandoc':
        codex_dir = Path(os.environ.get('CODEX_HOME', Path.home() / '.codex'))
        for base in (ROOT / 'tools', ROOT.parent / '.tools', codex_dir / 'tools' / 'ruc-thesis'):
            found = sorted(base.glob('**/pandoc.exe')) + sorted(base.glob('**/pandoc')) if base.exists() else []
            if found:
                return str(found[0])
    return None


def run(argv, cwd=None, timeout=180, output_only=False, full_output=False):
    env = os.environ.copy()
    # Windows Perl/Biber does not understand the Unix C.UTF-8 locale.
    if os.name == 'nt':
        env.update(LC_ALL='C', LC_CTYPE='C', LANG='C')
    p = subprocess.run([str(x) for x in argv], cwd=cwd, env=env,
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE if output_only else subprocess.STDOUT, timeout=timeout)
    output = p.stdout.decode('utf-8', errors='replace')
    if p.returncode:
        error = (p.stderr or b'').decode('utf-8', errors='replace')
        if not full_output:
            output, error = output[-6000:], error[-2000:]
        raise RuntimeError(f'Command failed ({p.returncode}): {argv[0]}\n{output}\n{error}')
    return output


def init_project(destination, metadata=None, demo=False, portable=False):
    dest = Path(destination).expanduser().resolve()
    if dest.exists():
        raise ValueError(f'Output already exists; choose a new directory: {dest}')
    values = read_json(metadata) if metadata else None
    allowed = ('title', 'subtitle', 'author', 'college', 'major', 'grade',
               'student-id', 'supervisor', 'score', 'date', 'code')
    if metadata:
        if not isinstance(values, dict) or set(values) - set(allowed):
            raise ValueError('Metadata must be an object using only the documented keys.')
        if any(type(v) not in (str, int, float) for v in values.values()):
            raise ValueError('Metadata values must be text or numbers; use an empty string for an explicit blank.')
    shutil.copytree(TEMPLATE, dest)
    if demo:
        for p in (ROOT / 'assets' / 'demo').rglob('*'):
            if p.is_file():
                target = dest / p.relative_to(ROOT / 'assets' / 'demo')
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(p, target)
    if portable:
        p = dest / 'main.tex'
        p.write_text(p.read_text(encoding='utf-8').replace('[numeric]', '[numeric,portable]'), encoding='utf-8')
    if metadata:
        defaults = {k: ('' if k in {'subtitle', 'score'} else '待填写') for k in allowed}
        defaults.update(values)
        body = ',\n'.join(f'  {k}={{{tex_escape(v)}}}' for k, v in defaults.items())
        (dest / 'metadata.tex').write_text('\\rucsetup{\n' + body + '\n}\n', encoding='utf-8')
    write_json(dest / 'project.json', {'profile': PROFILE, 'font_mode': 'portable' if portable else 'strict',
                                     'demo': demo, 'format_verified_for_college': False})
    return dest


def report_import(dest, src, mode, issues, details=None):
    write_json(dest / 'conversion.json', {
        'source_name': src.name, 'source_sha256': hashlib.sha256(src.read_bytes()).hexdigest(),
        'input_type': mode, 'status': 'needs-review', 'issues': issues,
        'details': details or {}, 'content_reviewed': False, 'visual_reviewed': False})


def tex_structure_mask(text):
    """Mask comments/literals for boundary searches, preserving source offsets.

    This is a conservative lexer for normal LaTeX, not a macro/catcode evaluator.
    Import the original source slices so comment-based space suppression survives.
    """
    result = list(text)
    literal_envs = {'verbatim', 'verbatim*', 'Verbatim', 'Verbatim*',
                    'lstlisting', 'minted', 'comment', 'filecontents', 'filecontents*'}
    def hide(start, end):
        result[start:end] = ['\n' if c == '\n' else ' ' for c in text[start:end]]
    i = 0
    while i < len(text):
        if text[i] == '%':
            end = text.find('\n', i)
            end = len(text) if end < 0 else end
            hide(i, end); i = end
        elif text[i] == '\\':
            command = re.match(r'\\([A-Za-z@]+|[^\n])', text[i:])
            if not command:
                i += 1; continue
            name = command.group(1)
            end = i + command.end()
            if name == 'verb':
                if end < len(text) and text[end] == '*': end += 1
                if end < len(text) and not text[end].isspace():
                    close = text.find(text[end], end + 1)
                    end = len(text) if close < 0 else close + 1
                hide(i, end)
            elif name == 'begin':
                env = re.match(r'\s*\{([^}]+)\}', text[end:])
                if env and env.group(1) in literal_envs:
                    marker = '\\end{' + env.group(1) + '}'
                    close = text.find(marker, end + env.end())
                    end = len(text) if close < 0 else close + len(marker)
                    hide(i, end)
            elif len(name) == 1 and not name.isalpha():
                hide(i, end)  # Escaped %, braces, and \\ are not structural tokens.
            i = end
        else:
            i += 1
    return ''.join(result)


@managed_import('tex')
def import_tex(args):
    src = Path(args.source).resolve()
    source_root = Path(args.source_root).resolve() if args.source_root else src.parent
    if not src.is_relative_to(source_root):
        raise ValueError('Source must be inside --source-root.')
    target = Path(args.output).resolve()
    if target == source_root or target.is_relative_to(source_root):
        raise ValueError('Use an output directory outside source-root to avoid recursive copying.')
    dest = args._session.initialize()
    def copy_source():
        shutil.copytree(source_root, dest / 'source', dirs_exist_ok=True, ignore=shutil.ignore_patterns(
            '.git', 'build', '__pycache__', '*.aux', '*.log', '*.toc', '*.bcf', '*.run.xml', '*.synctex.gz'))
    stage(args, 'source-copy', copy_source, ['source'])
    relative = src.relative_to(source_root)
    migrated = helper('tex_import').Migration(dest, source_root, relative, tex_structure_mask, args._session).run()
    issues = ['Check original-preamble.tex.txt and migrate needed macros/packages.',
              'Move old cover, abstracts, TOC and back matter out of content/body.tex; do not duplicate them.',
              'Verify included files, bibliography commands, figure paths, labels and citations.',
              'Populate metadata and both abstracts from the source; never invent missing information.']
    report_import(dest, src, 'tex', issues + migrated['issues'], {
        'copied_source_root': str(source_root), 'main_relative': relative.as_posix(),
        'files': migrated['files'], 'include_aux_dirs': migrated['include_aux_dirs']})
    return {'project': str(dest), 'status': 'needs-review'}


@managed_import('docx')
def import_docx(args):
    src = Path(args.source).resolve()
    if src.suffix.lower() != '.docx':
        raise ValueError('Convert legacy .doc to .docx with Word/LibreOffice first.')
    pandoc = tool('pandoc', args.pandoc)
    if not pandoc:
        raise ValueError('Pandoc is required. Supply --pandoc or install from https://pandoc.org/installing.html')
    ns = {'w': 'http://schemas.openxmlformats.org/wordprocessingml/2006/main',
          'm': 'http://schemas.openxmlformats.org/officeDocument/2006/math'}
    with zipfile.ZipFile(src) as z:
        xml = ET.fromstring(z.read('word/document.xml'))
        counts = {name: len(xml.findall('.//' + tag, ns)) for name, tag in {
            'paragraphs': 'w:p', 'tables': 'w:tbl', 'equations': 'm:oMath',
            'drawings': 'w:drawing', 'footnote_references': 'w:footnoteReference',
            'insertions': 'w:ins', 'deletions': 'w:del', 'fields': 'w:fldChar',
            'textboxes': 'w:txbxContent', 'objects': 'w:object', 'merged_cells': 'w:vMerge'}.items()}
        revision_tags = {'ins', 'del', 'moveFrom', 'moveTo', 'moveFromRangeStart',
                         'moveToRangeStart', 'rPrChange', 'pPrChange', 'sectPrChange',
                         'tblPrChange', 'tblPrExChange', 'tblGridChange', 'trPrChange',
                         'tcPrChange', 'cellIns', 'cellDel', 'cellMerge', 'numberingChange'}
        revision_parts = {}
        for name in z.namelist():
            if not name.startswith('word/') or not name.endswith('.xml'):
                continue
            part = xml if name == 'word/document.xml' else ET.fromstring(z.read(name))
            revisions = {}
            for element in part.iter():
                if element.tag.startswith('{' + ns['w'] + '}'):
                    tag = element.tag.split('}', 1)[1]
                    if tag in revision_tags: revisions[tag] = revisions.get(tag, 0) + 1
            if revisions: revision_parts[name] = revisions
        if revision_parts and args.track_changes == 'error':
            raise ValueError('Tracked changes found. Choose --track-changes accept/reject after deciding which revision to preserve.')
    dest = args._session.initialize()
    (dest / 'source').mkdir(exist_ok=True)
    stage(args, 'source-copy', lambda: (shutil.copy2(src, dest / 'source' / src.name) and None), ['source/' + src.name])
    revision = args.track_changes if args.track_changes != 'error' else 'accept'
    # JSON keeps the document structure for inspection and re-routing front/back matter.
    (dest / 'media').mkdir(exist_ok=True)
    log = stage(args, 'docx-ast', lambda: run([pandoc, str(src), '-f', 'docx', '-t', 'json', '--track-changes=' + revision,
               '--extract-media=media', '-o', 'source/document.json'], cwd=dest), ['source/document.json', 'media'])
    log += stage(args, 'docx-latex', lambda: run([pandoc, 'source/document.json', '-f', 'json', '-t', 'latex', '--wrap=none',
                '--top-level-division=section', '-o', 'content/body.tex'], cwd=dest), ['content/body.tex'])
    (dest / 'source' / 'pandoc.log').write_text(log, encoding='utf-8')
    issues = ['Separate title, abstracts, keywords, references and back matter from imported body.',
              'Check equations, figures, table structure, captions, footnotes, heading levels and bibliography against Word.',
              'Convert plain-text bibliography/citations to linked BibLaTeX only when identities are known.']
    for key in ['fields', 'textboxes', 'objects', 'merged_cells']:
        if counts[key]:
            issues.append(f'DOCX contains {key}: {counts[key]}; inspect for omitted or flattened content.')
    if revision_parts:
        issues.append('Tracked changes include ' + ', '.join(revision_parts) +
                      '; verify the chosen revision in notes, moved text and formatting as well as main paragraphs.')
    if log.strip():
        issues.append('Pandoc emitted messages; inspect source/pandoc.log.')
    report_import(dest, src, 'docx', issues, {'counts': counts, 'track_changes': revision, 'revision_parts': revision_parts,
                                           'pandoc_version': run([pandoc, '--version']).splitlines()[0]})
    return {'project': str(dest), 'status': 'needs-review', 'counts': counts}


@managed_import('pdf')
def import_pdf(args):
    if args.dpi <= 0:
        raise ValueError('DPI must be greater than zero.')
    try:
        import pypdfium2 as pdfium
    except ImportError:
        raise ValueError('PDF input requires pypdfium2 and Pillow in the selected Python environment.')
    src = Path(args.source).resolve()
    pdf = pdfium.PdfDocument(src)
    ocr = tool('tesseract', args.tesseract) if args.ocr else None
    if args.ocr and not ocr:
        raise ValueError('--ocr requires Tesseract with requested language data; use rendered pages for visual transcription otherwise.')
    if args.ocr_all and not args.ocr:
        raise ValueError('--ocr-all requires --ocr.')
    dest = args._session.initialize()
    source = dest / 'source'
    source.mkdir(exist_ok=True)
    stage(args, 'source-copy', lambda: (shutil.copy2(src, source / src.name) and None), ['source/' + src.name])
    pages_dir = source / 'pages'
    pages_dir.mkdir(exist_ok=True)
    pages = []
    draft = ['% PDF extraction draft: requires semantic reconstruction and page-by-page comparison.']
    issues = ['Reconstruct headings, paragraphs, abstracts and references from page images; remove recurring headers/footers.',
              'Rebuild formulas/tables and crop individual figures; full-page image inclusion is not completed conversion.',
              'Verify reading order and every page against source/pages before delivering.']
    try:
        for index in range(len(pdf)):
            name = f'page-{index+1:04d}'
            def extract_page():
                page = pdf[index]
                try:
                    tp = page.get_textpage()
                    try: text = tp.get_text_range().replace('\r\n', '\n')
                    finally: tp.close()
                    bitmap = page.render(scale=args.dpi / 72)
                    try: bitmap.to_pil().save(pages_dir / (name + '.png'))
                    finally: bitmap.close()
                    extracted = text
                    sparse = len(re.sub(r'\s', '', text)) < 40
                    method = 'text'
                    if args.ocr and (sparse or args.ocr_all):
                        text = run([ocr, pages_dir / (name + '.png'), 'stdout', '-l', args.ocr_language, '--psm', '3'], output_only=True)
                        method = 'ocr'
                    (pages_dir / (name + '.txt')).write_text(text, encoding='utf-8')
                    return {'page': index + 1, 'method': method, 'text': text, 'raw_text': extracted,
                            'sparse_text': sparse, 'image': 'pages/' + name + '.png', 'review_required': True}
                finally: page.close()
            record = stage(args, 'pdf-' + name, extract_page,
                           ['source/pages/' + name + suffix for suffix in ['.png', '.txt']])
            pages.append(record)
            text = record['text']
            draft.append(f'% Source PDF page {index+1}; {record["method"]}; not yet reviewed.\n')
            if not text.strip():
                draft.append('\\textbf{待核对：原 PDF 第 ' + str(index+1) + ' 页需要 OCR 或视觉转录。}\n')
            else:
                draft.extend(tex_escape(p.strip()) + '\n\n' for p in re.split(r'\n\s*\n', text) if p.strip())
    finally: pdf.close()
    write_json(source / 'pages.json', pages)
    # Import by file path so both CLI use and importlib-based callers work.
    spec = importlib.util.spec_from_file_location('ruc_pdf_inventory', ROOT / 'scripts' / 'pdf_inventory.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    try:
        inventory = stage(args, 'pdf-glyphs', lambda: module.inspect_pdf(src, source / 'glyphs'), ['source/glyphs'])
        flagged = [p['page'] for p in inventory['pages'] if p['flags']]
        if flagged:
            issues.append(f'Glyph/layout reconstruction flags on pages {flagged}; inspect source/glyphs/inventory.json even when text is not sparse.')
    except ImportError:
        issues.append('pdfplumber unavailable: character-position/font inventory missing; install scripts/requirements.txt before math/code reconstruction.')
    (dest / 'content' / 'body.tex').write_text('\n'.join(draft), encoding='utf-8')
    sparse_pages = [p['page'] for p in pages if p['sparse_text']]
    if sparse_pages:
        issues.append(f'Sparse/empty text on pages {sparse_pages}: may be scans, covers or extraction failure; inspect images.')
    report_import(dest, src, 'pdf', issues, {'page_count': len(pages), 'sparse_pages': sparse_pages,
                                           'ocr_requested': args.ocr})
    return {'project': str(dest), 'status': 'needs-review', 'pages': len(pages), 'sparse_pages': sparse_pages}


def diagnose(project, log):
    problems = []
    patterns = {
        'missing-glyph': r'Missing character:[^\n]*',
        'undefined-reference': r'(?:LaTeX|Package biblatex) Warning: [^\n]*(?:undefined|not found)[^\n]*',
        'rerun-required': r'[^\n]*(?:Please \(re\)run Biber|Rerun to get cross-references right|Label\(s\) may have changed)[^\n]*',
        'overfull-box': r'Overfull \\[hv]box[^\n]*',
        'font-warning': r'(?:LaTeX Font Warning|Package fontspec Warning)[^\n]*',
        'layout-warning': r'Package (?:fancyhdr|longtable|caption|titlesec) Warning:[^\n]*',
        'empty-bibliography': r'LaTeX Warning: Empty bibliography[^\n]*',
    }
    for kind, pattern in patterns.items():
        for match in re.findall(pattern, log, re.I):
            problems.append({'kind': kind, 'message': match})
    if 'PORTABLE FONTS' in log:
        problems.append({'kind': 'font-substitution', 'message': 'Portable preview fonts; not strict school typography.'})
    for name in ['metadata.tex', 'content/body.tex', 'content/abstract-zh.tex', 'content/abstract-en.tex']:
        p = project / name
        if p.exists() and re.search(r'待填写|待核对|to be supplied', p.read_text(encoding='utf-8'), re.I):
            problems.append({'kind': 'incomplete-content', 'message': name})
    return problems


def build(args):
    project = Path(args.project).resolve()
    if not (project / 'main.tex').is_file():
        raise ValueError('main.tex not found in project.')
    xelatex, biber = tool('xelatex'), tool('biber')
    out = project / 'build'
    out.mkdir(exist_ok=True)
    report = {'profile': PROFILE, 'status': 'failed', 'commands': [], 'diagnostics': [],
              'visual_reviewed': False, 'content_reviewed': False}
    transcript = []
    def invoke(command):
        report['commands'].append(command)
        transcript.append('$ ' + subprocess.list2cmdline(command))
        output = run(command, cwd=project, timeout=args.timeout, full_output=True)
        transcript.append(output)
        return output

    try:
        if not xelatex or not biber:
            raise ValueError('XeLaTeX and Biber required. Run doctor; use an existing MiKTeX/TeX Live installation.')
        conversion = project / 'conversion.json'
        if conversion.exists():
            record = read_json(conversion)
            report['conversion_status'] = record['status']
            # TeX Live opens \include's per-chapter .aux under -output-directory.
            for relative in record.get('details', {}).get('include_aux_dirs', []):
                directory = (out / relative).resolve()
                if not directory.is_relative_to(out.resolve()):
                    raise ValueError(f'Invalid include auxiliary directory: {relative}')
                directory.mkdir(parents=True, exist_ok=True)
        version = invoke([xelatex, '--version'])
        engine = helper('preflight').engine_command(xelatex, version)
        engine += ['-no-shell-escape', '-interaction=nonstopmode', '-halt-on-error',
                   '-file-line-error', '-synctex=1', '-output-directory=build', 'main.tex']
        # A bounded explicit sequence works on Windows even when latexmk has no Perl.
        # Hash auxiliaries to finish only once references/TOC have converged.
        invoke(engine)
        bcf = out / 'main.bcf'
        if bcf.exists():
            cmd = [biber, '--input-directory=build', '--output-directory=build', 'main']
            invoke(cmd)
        previous = None
        for _ in range(4):
            invoke(engine)
            digest = hashlib.sha256(b''.join(p.read_bytes() for p in sorted(out.glob('main.*'))
                                           if p.suffix in {'.aux', '.toc', '.out', '.lof', '.lot'})).hexdigest()
            if digest == previous:
                break
            previous = digest
        else:
            raise RuntimeError('Auxiliary files did not converge within four post-Biber passes.')
        log = (out / 'main.log').read_text(encoding='utf-8', errors='replace')
        report['environment_notes'] = sorted(set(re.findall(r'LaTeX Warning: You have requested release[^\n]*\n[^\n]*', log)))
        report['diagnostics'] = diagnose(project, log)
        blg = out / 'main.blg'
        if blg.exists():
            report['diagnostics'].extend({'kind': 'bibliography-warning', 'message': line}
                for line in blg.read_text(encoding='utf-8', errors='replace').splitlines()
                if re.search(r'\b(?:WARN|ERROR)\b', line))
        if not (out / 'main.pdf').is_file():
            raise RuntimeError('Engine exited without a PDF.')
        report['pdf'] = str(out / 'main.pdf')
        report['pdf_sha256'] = hashlib.sha256((out / 'main.pdf').read_bytes()).hexdigest()
        report['status'] = 'compiled-with-warnings' if report['diagnostics'] else 'compiled'
        report['delivery_status'] = 'needs-content-and-visual-review'
        if args.strict and report['diagnostics']:
            raise RuntimeError('Strict check failed: inspect build-report.json diagnostics.')
    except (RuntimeError, OSError, ValueError, subprocess.TimeoutExpired) as exc:
        report['status'] = 'failed'
        message = str(exc)
        command = report['commands'][-1] if report['commands'] else None
        if isinstance(exc, subprocess.TimeoutExpired):
            message = f'{subprocess.list2cmdline(command)} timed out after {exc.timeout} seconds. Adjust build --timeout.'
            for output in (exc.stdout, exc.stderr):
                if output:
                    transcript.append(output.decode('utf-8', errors='replace') if isinstance(output, bytes) else output)
            report['diagnostics'].append({'kind': 'timeout', 'command': command, 'seconds': exc.timeout})
        elif command and command[0] == xelatex and 'main.tex' in command:
            missing = re.search(r"""File ['`"]([^'`"\n]+)['`"] not found""", message, re.I)
            if missing:
                manager = 'MiKTeX Console' if '--disable-installer' in command else 'the TeX distribution package manager (tlmgr for TeX Live)'
                remedy = f'Install the package providing {missing[1]} with {manager}, or restore the local file.'
                message += '\n' + remedy
                report['diagnostics'].append({'kind': 'missing-file', 'file': missing[1], 'command': command, 'remedy': remedy})
        report['error'] = message
        transcript.append(message)
        if message != str(exc):
            raise RuntimeError(message) from exc
        raise
    finally:
        write_json(out / 'build-report.json', report)
        (out / 'build-transcript.txt').write_text('\n'.join(transcript), encoding='utf-8')
    return report


def render(args):
    import pypdfium2 as pdfium
    if args.dpi <= 0:
        raise ValueError('DPI must be greater than zero.')
    dest = Path(args.output).resolve()
    if dest.exists() and (not dest.is_dir() or any(dest.iterdir())):
        raise ValueError(f'Render output must be new or empty to avoid stale review pages: {dest}')
    pdf_path = Path(args.pdf).resolve()
    pdf = pdfium.PdfDocument(pdf_path)
    count = len(pdf)
    sizes = []
    for i in range(count):
        page = pdf[i]
        sizes.append(list(page.get_size()))
        page.close()
    pdf.close()
    dest.mkdir(parents=True, exist_ok=True)
    pages = []
    poppler = tool('pdftoppm')
    for i in range(count):
        name = f'page-{i+1:04d}.png'
        if poppler:
            run([poppler, '-f', str(i+1), '-l', str(i+1), '-singlefile', '-r', str(args.dpi),
                 '-png', pdf_path, dest / name[:-4]])
        else:
            # Fresh handles avoid PDFium shared-image state differences across pages.
            with pdfium.PdfDocument(pdf_path) as document:
                page = document[i]
                bitmap = page.render(scale=args.dpi / 72)
                bitmap.to_pil().save(dest / name)
                bitmap.close()
                page.close()
        pages.append({'page': i+1, 'file': name, 'size_points': sizes[i]})
    write_json(dest / 'pages.json', pages)
    write_json(dest / 'render-report.json', {'pdf_sha256': hashlib.sha256(pdf_path.read_bytes()).hexdigest(),
        'page_count': count, 'dpi': args.dpi, 'renderer': 'poppler' if poppler else 'pdfium', 'visual_reviewed': False})
    return {'rendered_pages': len(pages), 'directory': str(dest), 'renderer': 'poppler' if poppler else 'pdfium', 'visual_reviewed': False}


def doctor(args=None):
    return helper('preflight').check(SimpleNamespace(**globals()), args)


def main():
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    p = sub.add_parser('doctor')
    p.add_argument('--input-type', choices=['tex', 'docx', 'pdf'])
    p.add_argument('--portable', action='store_true'); p.add_argument('--pandoc'); p.add_argument('--tesseract')
    p.add_argument('--ocr', action='store_true'); p.add_argument('--ocr-language', default='chi_sim+eng')
    p.add_argument('--report', help='Write machine-readable dependency report.')
    p = sub.add_parser('init')
    p.add_argument('output'); p.add_argument('--metadata'); p.add_argument('--demo', action='store_true'); p.add_argument('--portable', action='store_true')
    for kind in ['tex', 'docx', 'pdf']:
        p = sub.add_parser('import-' + kind)
        p.add_argument('source'); p.add_argument('output'); p.add_argument('--metadata'); p.add_argument('--portable', action='store_true')
        recovery = p.add_mutually_exclusive_group()
        recovery.add_argument('--resume', action='store_true'); recovery.add_argument('--retry', action='store_true')
        if kind == 'tex':
            p.add_argument('--source-root')
        if kind == 'docx':
            p.add_argument('--pandoc'); p.add_argument('--track-changes', choices=['error', 'accept', 'reject'], default='error')
        if kind == 'pdf':
            p.add_argument('--dpi', type=int, default=144); p.add_argument('--ocr', action='store_true')
            p.add_argument('--ocr-all', action='store_true'); p.add_argument('--tesseract')
            p.add_argument('--ocr-language', default='chi_sim+eng')
    p = sub.add_parser('build')
    p.add_argument('project'); p.add_argument('--strict', action='store_true'); p.add_argument('--timeout', type=int, default=180)
    p = sub.add_parser('render')
    p.add_argument('pdf'); p.add_argument('output'); p.add_argument('--dpi', type=int, default=144)
    args = parser.parse_args()
    try:
        if args.command == 'doctor':
            result = doctor(args)
            if args.report: write_json(args.report, result)
        elif args.command == 'init':
            environment = doctor(args)
            if not environment['ready']:
                raise ValueError('Dependencies missing: ' + '; '.join(x['item'] + ': ' + x['remedy'] for x in environment['missing']))
            result = {'project': str(init_project(args.output, args.metadata, args.demo, args.portable))}
            write_json(Path(result['project']) / 'environment.json', environment)
        elif args.command == 'build': result = build(args)
        elif args.command == 'render': result = render(args)
        else: result = globals()[args.command.replace('-', '_')](args)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        if args.command == 'doctor' and not result['ready']: return 1
    except (ValueError, RuntimeError, OSError, subprocess.TimeoutExpired) as exc:
        print(str(exc), file=sys.stderr)
        if args.command.startswith('import-'):
            output = Path(args.output).expanduser().resolve()
            checkpoint = output.with_name('.' + output.name + '.import') / 'state.json'
            if checkpoint.exists():
                print(f'Checkpoint: {checkpoint}\nFix the cause, then repeat with --resume; use --retry to archive progress and start again.', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    sys.exit(main())
