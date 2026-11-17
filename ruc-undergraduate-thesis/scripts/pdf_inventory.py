"""Evidence for PDF reconstruction: glyph positions, math/code flags and links.

This is an inventory, NOT a math OCR or a semantic converter. A non-sparse native
text layer can still lose fractions, scripts, reading order and code indentation.
"""
import hashlib
import json
import re
from pathlib import Path


def inspect_pdf(source, destination):
    import pdfplumber
    source, destination = Path(source), Path(destination)
    destination.mkdir(parents=True, exist_ok=True)
    pages = []
    with pdfplumber.open(source) as pdf:
        for index, page in enumerate(pdf.pages, 1):
            chars = [{key: c[key] for key in ('text', 'fontname', 'size', 'x0', 'x1',
                     'top', 'bottom', 'matrix') if key in c} for c in page.chars]
            fonts = sorted({c['fontname'] for c in chars})
            math = [c for c in chars if re.search(r'(?:^|\+)(?:CM|MSAM|MSBM)|Math|Symbol', c['fontname'], re.I)
                    or re.search(r'[∑∫√≤≥∂∇]', c['text'])]
            mono = [c for c in chars if re.search(r'Mono|Courier|Consolas', c['fontname'], re.I)]
            invalid = [c for c in chars if '\ufffd' in c['text'] or '(cid:' in c['text']]
            sizes = sorted({round(c['size'], 2) for c in chars})
            flags = []
            if math: flags.append('math-reconstruction-required')
            if len(mono) > 40: flags.append('code-indentation-review')
            if invalid: flags.append('glyph-mapping-review')
            if len(chars) < 40: flags.append('sparse-text-review')
            name = f'page-{index:04d}.json'
            detail = {'page': index, 'width': page.width, 'height': page.height,
                      'chars': chars, 'lines': page.lines, 'rects': page.rects,
                      'links': [{k: link.get(k) for k in ('x0','x1','top','bottom','uri')} for link in page.hyperlinks],
                      'image_bounds': [{k: im.get(k) for k in ('x0','x1','top','bottom','width','height')} for im in page.images]}
            (destination / name).write_text(json.dumps(detail, ensure_ascii=False, default=str), encoding='utf-8')
            pages.append({'page': index, 'characters': len(chars), 'fonts': fonts,
                          'font_sizes': sizes, 'math_characters': len(math),
                          'monospace_characters': len(mono), 'unmapped_characters': len(invalid),
                          'vector_line_count': len(page.lines), 'link_count': len(page.hyperlinks),
                          'flags': flags, 'glyph_file': name, 'reviewed': False})
    result = {'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
              'page_count': len(pages), 'status': 'needs-review', 'pages': pages}
    (destination / 'inventory.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    return result


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source'); parser.add_argument('output')
    args = parser.parse_args()
    result = inspect_pdf(args.source, args.output)
    print(json.dumps({'pages': result['page_count'], 'status': result['status']}, indent=2))
