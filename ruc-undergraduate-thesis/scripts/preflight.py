"""Read-only dependency checks plus an isolated XeLaTeX font/package probe."""
import importlib
import importlib.metadata
import platform
from pathlib import Path
import re
import tempfile


STRICT_FONTS = ['SimSun', 'SimHei', 'KaiTi', 'FangSong', 'Times New Roman', 'Arial', 'Courier New']
PORTABLE_FONTS = ['FandolSong-Regular.otf', 'FandolSong-Bold.otf', 'FandolHei-Regular.otf',
                  'FandolHei-Bold.otf', 'FandolKai-Regular.otf', 'FandolFang-Regular.otf'] + [
                  f'texgyre{family}-{style}.otf' for family in ['termes', 'heros', 'cursor']
                  for style in ['regular', 'bold', 'italic', 'bolditalic']]


def check(api, args=None):
    kind = getattr(args, 'input_type', None) or getattr(args, 'command', '').removeprefix('import-')
    portable = getattr(args, 'portable', False)
    report = {'platform': platform.platform(), 'python': platform.python_version(),
              'font_mode': 'portable' if portable else 'strict', 'tools': {},
              'python_packages': {}, 'tex_files': {}, 'tex_versions': {}, 'fonts': {}, 'missing': [], 'warnings': []}

    def missing(item, reason, remedy):
        report['missing'].append({'item': item, 'reason': str(reason), 'remedy': remedy})

    names = ['xelatex', 'biber', 'kpsewhich']
    if kind == 'docx': names.append('pandoc')
    if kind == 'pdf' and getattr(args, 'ocr', False): names.append('tesseract')
    for name in names:
        try:
            path = api.tool(name, getattr(args, name, None))
            if not path: raise ValueError('executable not found')
            version = api.run([path, '--version'], timeout=30).splitlines()[0]
            report['tools'][name] = {'path': path, 'version': version}
        except Exception as exc:
            missing(name, exc, f'Install/configure {name} in PATH (or its documented explicit option).')
    if kind == 'pdf':
        for module, package in [('pypdfium2', 'pypdfium2'), ('PIL.Image', 'Pillow'), ('pdfplumber', 'pdfplumber')]:
            try:
                importlib.import_module(module)
                report['python_packages'][package] = importlib.metadata.version(package)
            except Exception as exc:
                missing(package, exc, 'python -m pip install -r <skill>/scripts/requirements.txt')
        if getattr(args, 'ocr_all', False) and not getattr(args, 'ocr', False):
            missing('--ocr-all', 'requires --ocr', 'Add --ocr or remove --ocr-all.')
        if getattr(args, 'dpi', 144) <= 0: missing('dpi', 'must be positive', 'Use --dpi 144.')
        if 'tesseract' in report['tools']:
            try:
                languages = api.run([report['tools']['tesseract']['path'], '--list-langs'], timeout=30).splitlines()
                report['ocr_languages'] = languages[1:]
                for language in getattr(args, 'ocr_language', 'chi_sim+eng').split('+'):
                    if language not in languages:
                        missing('tesseract:' + language, 'language data missing', f'Install {language}.traineddata in Tesseract tessdata.')
            except Exception as exc:
                missing('tesseract languages', exc, 'Check tessdata and TESSDATA_PREFIX.')

    cls = (api.TEMPLATE / 'ructhesis.cls').read_text(encoding='utf-8')
    packages = set()
    for match in re.finditer(r'\\RequirePackage(?:\[[^]]*\])?\{([^}]+)\}', cls):
        packages.update(p.strip() + '.sty' for p in match[1].split(','))
    packages.update(['ctexart.cls', 'fontspec.sty', 'gb7714-2015.bbx', 'gb7714-2015.cbx',
                     'gb7714-2015ay.bbx', 'gb7714-2015ay.cbx', 'texgyretermes-math.otf'])
    if 'kpsewhich' in report['tools']:
        for name in sorted(packages):
            try:
                found = api.run([report['tools']['kpsewhich']['path'], name], timeout=30, output_only=True).strip()
                if not found: raise ValueError('not found in TeX search path')
                report['tex_files'][name] = found
                if Path(found).is_file() and Path(found).suffix != '.otf':
                    header = Path(found).read_text(encoding='utf-8', errors='replace')[:16000]
                    version = re.search(r'\\Provides(?:Package|Class|File)\s*\{[^}]+\}\s*\[([^]]+)\]', header)
                    if version: report['tex_versions'][name] = ' '.join(version[1].split())
            except Exception:
                missing(name, 'not found in TeX search path', 'Install the providing TeX package using TeX Live/MiKTeX package manager.')
    fonts = (PORTABLE_FONTS if portable else STRICT_FONTS) + ['texgyretermes-math.otf']
    if 'xelatex' in report['tools'] and 'fontspec.sty' in report['tex_files']:
        with tempfile.TemporaryDirectory(prefix='ruc-preflight-') as directory:
            root = Path(directory)
            probe = '\\documentclass{article}\n\\usepackage{fontspec}\n'
            for i, font in enumerate(fonts):
                probe += f'\\IfFontExistsTF{{{font}}}{{\\typeout{{RUC-FONT-{i}-OK}}}}{{\\typeout{{RUC-FONT-{i}-MISSING}}}}\n'
            probe += '\\begin{document}Dependency probe.\\end{document}\n'
            (root / 'probe.tex').write_text(probe, encoding='utf-8')
            engine = [report['tools']['xelatex']['path']]
            if 'miktex' in report['tools']['xelatex']['version'].lower(): engine.append('--disable-installer')
            try:
                output = api.run(engine + ['-no-shell-escape', '-interaction=nonstopmode', '-halt-on-error', 'probe.tex'], cwd=root)
                for i, font in enumerate(fonts):
                    ok = f'RUC-FONT-{i}-OK' in output
                    report['fonts'][font] = ok
                    if not ok:
                        remedy = ('Install TeX packages fandol and tex-gyre (tex-gyre-math for math fonts).'
                                  if portable else 'Install the licensed font; or explicitly use --portable for preview fonts.')
                        missing(font, 'XeLaTeX cannot load font', remedy)
                if not any(x['item'] in packages for x in report['missing']):
                    (root / 'ructhesis.cls').write_text(cls, encoding='utf-8')
                    option = '[portable]' if portable else ''
                    (root / 'probe.bib').write_text('@book{probe,author={Test Author},title={Dependency probe},year={2020},publisher={Test}}', encoding='utf-8')
                    (root / 'probe.tex').write_text('\\documentclass' + option + '{ructhesis}\n\\addbibresource{probe.bib}\n\\begin{document}\\pagestyle{empty}测试 $x^2$.\\cite{probe}\\printbibliography\\end{document}', encoding='utf-8')
                    if all(report['fonts'].values()):
                        api.run(engine + ['-no-shell-escape', '-interaction=nonstopmode', '-halt-on-error', 'probe.tex'], cwd=root)
                        if 'biber' in report['tools']:
                            api.run([report['tools']['biber']['path'], 'probe'], cwd=root)
                        report['template_probe'] = 'passed'
            except Exception as exc:
                missing('xelatex probe', exc, 'Resolve the font/package error shown by the probe before importing.')
    if portable: report['warnings'].append('Portable fonts are for previews, not strict school typography.')
    report['ready'] = not report['missing']
    return report
