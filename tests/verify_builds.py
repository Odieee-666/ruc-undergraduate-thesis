"""Compile independent cases; logs/outputs retained for manual visual review."""
import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import sys

BASE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('thesis', BASE / 'ruc-undergraduate-thesis/scripts/thesis.py')
t = importlib.util.module_from_spec(spec); spec.loader.exec_module(t)
sys.stdout.reconfigure(encoding='utf-8')

root = Path(sys.argv[1]).resolve()
results = []

for name in ['tex-import', 'docx-import', 'pdf-import']:
    project = root / name
    shutil.copy2(t.TEMPLATE / 'ructhesis.cls', project / 'ructhesis.cls')
    if name == 'tex-import':
        with (project / 'preamble-extra.tex').open('a', encoding='utf-8') as stream:
            stream.write('\n\\newcommand{\\custom}{kept}\n')
    # Missing metadata/bibliography are expected in these content-only fixtures.
    result = t.build(argparse.Namespace(project=project, strict=False, timeout=180))
    unexpected = [d for d in result['diagnostics'] if d['kind'] not in {'incomplete-content', 'empty-bibliography', 'bibliography-warning'}]
    if unexpected:
        raise RuntimeError(json.dumps(unexpected))
    results.append({'case': name, 'status': result['status'], 'expected_draft_warnings': result['diagnostics']})
    print(name + ': compiled; only expected draft warnings', flush=True)

stress = t.init_project(root / 'pagination-author-year', demo=True)
p = stress / 'main.tex'
p.write_text(p.read_text(encoding='utf-8').replace('[numeric]', '[author-year]'), encoding='utf-8')
zh = stress / 'content/abstract-zh.tex'
para = '本段是长摘要分页测试材料，用于检验中文字体、首行缩进、页眉与罗马页码的连续性。内容不构成研究发现。'
zh.write_text('\n\n'.join([para * 3] * 11) + '\n\\cnkeywords{分页测试}', encoding='utf-8')
ap = stress / 'content/appendix.tex'
rows = '\n'.join(f'{i} & 长表格中的第 {i} 行测试内容。 \\\\' for i in range(1,71))
ap.write_text('\\section{跨页表格}\n\\begin{longtable}{rp{100mm}}\n\\caption{分页测试表}\\label{tab:long}\\\\\n\\toprule 序号 & 内容 \\\\ \\midrule\n\\endfirsthead\n\\toprule 序号 & 内容 \\\\ \\midrule\n\\endhead\n\\bottomrule\\endfoot\n'+rows+'\n\\end{longtable}\n', encoding='utf-8')
result = t.build(argparse.Namespace(project=stress, strict=True, timeout=180))
results.append({'case': 'pagination-author-year', 'status': result['status'], 'diagnostics': result['diagnostics']})
print('pagination-author-year: strict build passed', flush=True)
t.write_json(root / 'integration-results.json', results)
