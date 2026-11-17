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
    def run(command, name):
        result = subprocess.run([str(x) for x in command], capture_output=True, timeout=300)
        (root/(name+'.log')).write_bytes(result.stdout + b'\n' + result.stderr)
        report['steps'].append({'name': name, 'exit_code': result.returncode})
        if result.returncode: raise RuntimeError(f'{name} failed; see {root/(name+".log")}')
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
        if shutil.which('tlmgr'): run(['tlmgr', 'info', '--only-installed'], 'texlive-packages')
        source = root/'inputs'; source.mkdir()
        (source/'main.tex').write_text('\\documentclass{article}\n\\begin{document}\\section{Fixture}Text $x^2$.\\end{document}', encoding='utf-8')
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
            allowed = {'incomplete-content', 'empty-bibliography', 'bibliography-warning', 'font-substitution'}
            bad = [d for d in build['diagnostics'] if d['kind'] not in allowed]
            if bad: raise RuntimeError(f'{kind}: unexpected build diagnostics: {bad}')
            cli(kind+'-render', 'render', project/'build/main.pdf', root/(kind+'-pages'), '--dpi', '72')
        # Real bibliography exercises Biber compatibility, beyond --version.
        demo = root/'demo'
        cli('demo-init', 'init', demo, '--demo', '--portable')
        cli('demo-build', 'build', demo)
        demo_report = json.loads((demo/'build/build-report.json').read_text(encoding='utf-8'))
        if any(d['kind'] != 'font-substitution' for d in demo_report['diagnostics']):
            raise RuntimeError(f'Demo diagnostics: {demo_report["diagnostics"]}')
        if not (demo/'build/main.bbl').stat().st_size: raise RuntimeError('Empty bibliography output')
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
