"""Same CLI workflow on clean Windows/Linux runners. No user thesis fixtures."""
import argparse
import importlib.metadata
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys
import tempfile

BASE = Path(__file__).resolve().parents[1]
SCRIPT = BASE / 'ruc-undergraduate-thesis/scripts/thesis.py'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--strict-fonts', action='store_true', help='Also compile a strict-font demo on licensed-font hosts.')
    args = parser.parse_args()
    (BASE/'output').mkdir(exist_ok=True)
    root = Path(tempfile.mkdtemp(prefix='clean-smoke-', dir=BASE/'output'))
    report = {'platform': platform.platform(), 'python': sys.version, 'status': 'running', 'steps': [],
              'packages': {p: importlib.metadata.version(p) for p in ['pypdfium2', 'Pillow', 'pdfplumber', 'pypdf', 'reportlab']}}
    def run(command, name, expected_code=0):
        result = subprocess.run([str(x) for x in command], capture_output=True, timeout=300)
        (root/(name+'.log')).write_bytes(result.stdout + b'\n' + result.stderr)
        report['steps'].append({'name': name, 'exit_code': result.returncode})
        if result.returncode != expected_code:
            raise RuntimeError(f'{name} returned {result.returncode}; see {root/(name+".log")}')
    def cli(name, *argv): run([sys.executable, SCRIPT, *argv], name)
    try:
        cli('doctor', 'doctor', '--input-type', 'pdf', '--portable', '--report', root/'environment.json')
        pandoc = shutil.which('pandoc')
        if not pandoc:
            # Match the documented explicit override, useful on a local checkout.
            pandoc = os.environ.get('RUC_TEST_PANDOC')
        if not pandoc: raise ValueError('Pandoc must be in PATH or RUC_TEST_PANDOC.')
        report['pandoc'] = subprocess.check_output([pandoc, '--version']).decode().splitlines()[0]
        run([sys.executable, '-m', 'pip', 'freeze'], 'pip-freeze')
        # Windows TeX Live exposes tlmgr.bat: CreateProcess needs its resolved
        # filename, not the extensionless command accepted by an interactive shell.
        tlmgr = shutil.which('tlmgr')
        if tlmgr: run([tlmgr, 'info', '--only-installed'], 'texlive-packages')
        source = root/'inputs'; source.mkdir()
        (source/'main.tex').write_text(r'''\documentclass{article}
\addbibresource{library.bib}
\begin{document}
\section{Fixture}\include{甲/章节.tex}\input{乙/小节}
\end{document}''', encoding='utf-8')
        (source/'甲').mkdir()
        (source/'乙').mkdir()
        (source/'甲/章节.tex').write_bytes(
            r'章节甲文 $x^2$。\input{小节}\includegraphics[width=1cm]{figure.png}\cite{fixture}'.encode('gbk'))
        (source/'甲/小节.tex').write_text('嵌套甲文', encoding='utf-8-sig')
        (source/'乙/小节.tex').write_text('嵌套乙文', encoding='utf-8')
        (source/'library.bib').write_bytes(
            '@book{fixture,author={张三},title={中文书目},year={2020},publisher={测试出版社}}'.encode('gbk'))
        shutil.copyfile(SCRIPT.parents[1]/'assets/template/assets/head.png', source/'figure.png')
        (source/'word.md').write_text('# Fixture\n\nText with $x^2$.\n', encoding='utf-8')
        run([pandoc, source/'word.md', '-o', source/'word.docx'], 'make-docx')
        from reportlab.pdfgen.canvas import Canvas
        c = Canvas(str(source/'paper.pdf')); c.drawString(50, 700, 'Synthetic PDF fixture for clean installation.'); c.save()
        for kind, filename in [('tex', 'main.tex'), ('docx', 'word.docx'), ('pdf', 'paper.pdf')]:
            project = root/kind
            extra = ['--pandoc', pandoc] if kind == 'docx' else []
            cli(kind+'-import', 'import-'+kind, source/filename, project, '--portable', *extra)
            cli(kind+'-build', 'build', project)
            build = json.loads((project/'build/build-report.json').read_text(encoding='utf-8'))
            if kind == 'tex':
                env = json.loads((root/'environment.json').read_text(encoding='utf-8'))
                miktex = 'miktex' in env['tools']['xelatex']['version'].lower()
                for cmd in build['commands']:
                    expected = int(miktex and cmd[-1] == 'main.tex')
                    if cmd.count('--disable-installer') != expected:
                        raise RuntimeError(f'Unexpected installer setting: {cmd}')
            allowed = {'incomplete-content', 'empty-bibliography', 'bibliography-warning', 'font-substitution'}
            bad = [d for d in build['diagnostics'] if d['kind'] not in allowed]
            if bad: raise RuntimeError(f'{kind}: unexpected build diagnostics: {bad}')
            if kind == 'tex':
                import pypdfium2 as pdfium
                with pdfium.PdfDocument(project/'build/main.pdf') as pdf:
                    text = ''.join(page.get_textpage().get_text_range() for page in pdf)
                for phrase in ('章节甲文', '嵌套甲文', '嵌套乙文', '中文书目'):
                    if phrase not in ''.join(text.split()):
                        raise RuntimeError(f'Missing from imported PDF: {phrase}')
                bbl = (project/'build/main.bbl').read_text(encoding='utf-8')
                if r'\entry{fixture}' not in bbl or '中文书目' not in bbl:
                    raise RuntimeError('Biber did not recover the cited Chinese entry.')
            cli(kind+'-render', 'render', project/'build/main.pdf', root/(kind+'-pages'), '--dpi', '72')
        # Real bibliography exercises Biber compatibility, beyond --version.
        demo = root/'demo'
        cli('demo-init', 'init', demo, '--demo', '--portable')
        cli('demo-build', 'build', demo)
        demo_report = json.loads((demo/'build/build-report.json').read_text(encoding='utf-8'))
        if any(d['kind'] != 'font-substitution' for d in demo_report['diagnostics']):
            raise RuntimeError(f'Demo diagnostics: {demo_report["diagnostics"]}')
        if not (demo/'build/main.bbl').stat().st_size: raise RuntimeError('Empty bibliography output')
        missing = root/'missing-package'
        missing.mkdir()
        (missing/'main.tex').write_text(r'''\documentclass{article}
\usepackage{ruc-absent-fixture}
\begin{document}Missing package test.\end{document}''', encoding='utf-8')
        run([sys.executable, SCRIPT, 'build', missing], 'missing-package-build', expected_code=1)
        failure = json.loads((missing/'build/build-report.json').read_text(encoding='utf-8'))
        diagnostic, = failure['diagnostics']
        if diagnostic['kind'] != 'missing-file' or diagnostic['file'] != 'ruc-absent-fixture.sty':
            raise RuntimeError(f'Unexpected missing-package diagnostic: {diagnostic}')
        if args.strict_fonts:
            cli('strict-doctor', 'doctor', '--report', root/'strict-environment.json')
            cli('strict-init', 'init', root/'strict-demo', '--demo')
            cli('strict-build', 'build', root/'strict-demo', '--strict')
        report['status'] = 'passed'
    except Exception as exc:
        report.update(status='failed', error=str(exc)); raise
    finally:
        (root/'verified-versions.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
        print('SMOKE_ARTIFACTS=' + str(root), flush=True)


if __name__ == '__main__': main()
