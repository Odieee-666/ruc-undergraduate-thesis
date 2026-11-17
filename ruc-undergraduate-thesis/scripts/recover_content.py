"""Reusable PDF evidence tools; never execute extracted code or correct formulas."""
import argparse
import ast
from collections import Counter, defaultdict
import json
from pathlib import Path
import re
import statistics


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8-sig'))


def write(path, value):
    Path(path).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def lines(chars, tolerance=2):
    """Group horizontal glyphs by top; each returned line retains source geometry."""
    grouped = []
    for char in sorted(chars, key=lambda c: (c['top'], c['x0'])):
        if not grouped or abs(char['top'] - grouped[-1][0]['top']) > tolerance:
            grouped.append([char])
        else: grouped[-1].append(char)
    return [sorted(line, key=lambda c: c['x0']) for line in grouped]


def bounds(chars):
    return [min(c['x0'] for c in chars), min(c['top'] for c in chars),
            max(c['x1'] for c in chars), max(c['bottom'] for c in chars)]


def text(chars):
    result = ''
    for i, char in enumerate(chars):
        if i and char['x0'] - chars[i-1]['x1'] > max(1, char.get('size', 10) * .2):
            result += ' '
        result += char['text']
    return result


def pages(directory):
    root = Path(directory)
    inventory = read(root / 'inventory.json')
    return inventory, [read(root / page['glyph_file']) for page in inventory['pages']]


def recover_code(directory, regions, python_check=False):
    inventory, source_pages = pages(directory)
    by_page = {page['page']: page for page in source_pages}
    selected = []
    for region in regions:
        page = by_page[region['page']]
        box = region.get('bbox', [0, 0, page['width'], page['height']])
        chars = [c for c in page['chars'] if c['text'].strip()
                 and box[0] <= c['x0'] < box[2] and box[1] <= c['top'] < box[3]
                 and re.search(region.get('font_pattern', r'Mono|Courier|Consolas'), c.get('fontname', ''), re.I)]
        if not chars: raise ValueError(f'No matching code glyphs in page {region["page"]} region {box}')
        if any(abs(c.get('matrix', [1, 0, 0, 1])[1]) > .01 for c in chars):
            raise ValueError('Rotated code requires visual reconstruction.')
        selected.append((region, lines(chars, region.get('line_tolerance', 2))))
    if not selected: raise ValueError('Select at least one code region.')
    # One common origin across pages preserves continuation indentation. An
    # explicit per-region origin handles margins that move between pages.
    origin = min(c['x0'] for _, group in selected for line in group for c in line)
    widths = [(c['x1'] - c['x0']) / len(c['text']) for _, group in selected
              for line in group for c in line if c['text'] and c['x1'] > c['x0']]
    width = statistics.median(widths)
    output, mapping, warnings = [], [], []
    for region, group in selected:
        left, advance = region.get('left', origin), region.get('char_width', width)
        if advance <= 0: raise ValueError('char_width must be positive.')
        for glyphs in group:
            row = ''
            for char in glyphs:
                position = (char['x0'] - left) / advance
                column = round(position)
                if position < -.25 or abs(position - column) > .25 or column < len(row):
                    warnings.append({'page': region['page'], 'bbox': bounds([char]), 'reason': 'glyph does not align to inferred character grid'})
                row += ' ' * max(0, column - len(row)) + char['text']
            output.append(row.rstrip())
            mapping.append({'output_line': len(output), 'source_page': region['page'],
                            'bbox': bounds(glyphs), 'left': left, 'char_width': advance})
    code = '\n'.join(output) + '\n'
    syntax = 'not-requested'
    if python_check:
        try: ast.parse(code); syntax = 'passed (not executed)'
        except SyntaxError as exc:
            syntax = {'status': 'failed', 'line': exc.lineno, 'message': exc.msg}
    return code, {'source_sha256': inventory['source_sha256'], 'status': 'needs-review',
                  'lines': mapping, 'warnings': warnings, 'python_syntax': syntax}


TAG = re.compile(r'[（(]\s*((?:\d+(?:\.\d+)*|[A-Za-z](?:\.\d+)+)[a-z]?)\s*[）)]')


def equation_inventory(directory, right_fraction=.65):
    if not 0 <= right_fraction <= 1: raise ValueError('right_fraction must be between 0 and 1.')
    inventory, source_pages = pages(directory)
    candidates = []
    for page in source_pages:
        for line in lines(page['chars']):
            # No inserted spaces here, so regex character offsets map to glyphs.
            joined = ''.join(c['text'] for c in line)
            owners = [c for c in line for _ in c['text']]
            for match in TAG.finditer(joined):
                box = bounds(owners[match.start():match.end()])
                candidates.append({'number': match[1], 'page': page['page'], 'bbox': box,
                                   'right_margin': box[0] >= right_fraction * page['width'],
                                   'context': text(line)})
    likely = [c for c in candidates if c['right_margin']]
    counts = Counter(c['number'] for c in likely)
    groups = defaultdict(set)
    for number in counts:
        match = re.fullmatch(r'(?:(.*)\.)?(\d+)', number)
        if match: groups[match[1] or ''].add(int(match[2]))
    gaps = []
    for prefix, values in groups.items():
        ordered = sorted(values)
        for before, after in zip(ordered, ordered[1:]):
            if after > before + 1:
                gaps.append({'prefix': prefix, 'after': before, 'before': after, 'missing_count': after-before-1})
    return {'source_sha256': inventory['source_sha256'], 'status': 'candidates-only',
            'candidates': candidates, 'right_margin_count': len(likely),
            'duplicate_candidates': {k: v for k, v in counts.items() if v > 1},
            'gap_candidates': gaps,
            'note': 'Right-margin prose references may be false positives; unnumbered or unmapped equations may be absent. No formula is changed.'}


def locate(directory, query, regex=False):
    inventory, source_pages = pages(directory)
    pattern = re.compile(query if regex else re.escape(query))
    hits = []
    for page in source_pages:
        for line in lines(page['chars']):
            value = text(line)
            if pattern.search(value):
                hits.append({'page': page['page'], 'bbox': bounds(line), 'text': value,
                             'glyph_file': f'page-{page["page"]:04d}.json'})
    return {'source_sha256': inventory['source_sha256'], 'query': query, 'matches': hits,
            'note': 'PDF physical page numbers, starting at 1; bounding boxes use top-left origin in points.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest='command', required=True)
    for command in ('code', 'equations', 'locate'):
        p = sub.add_parser(command)
        p.add_argument('glyphs'); p.add_argument('output')
        if command == 'code':
            p.add_argument('--regions', required=True)
            p.add_argument('--python-check', action='store_true')
        elif command == 'equations': p.add_argument('--right-fraction', type=float, default=.65)
        else:
            p.add_argument('--query', required=True); p.add_argument('--regex', action='store_true')
    args = parser.parse_args()
    if Path(args.output).exists(): parser.error('Output already exists; choose a new file.')
    if args.command == 'code':
        mapping = Path(args.output + '.json')
        if mapping.exists(): parser.error('Source map already exists; choose a new output.')
        code, report = recover_code(args.glyphs, read(args.regions), args.python_check)
        Path(args.output).write_text(code, encoding='utf-8'); write(mapping, report)
    elif args.command == 'equations': write(args.output, equation_inventory(args.glyphs, args.right_fraction))
    else: write(args.output, locate(args.glyphs, args.query, args.regex))


if __name__ == '__main__': main()
