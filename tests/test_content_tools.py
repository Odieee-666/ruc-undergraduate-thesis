import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

BASE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('recover', BASE/'ruc-undergraduate-thesis/scripts/recover_content.py')
r = importlib.util.module_from_spec(spec); spec.loader.exec_module(r)


class ContentToolsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        def chars(value, x, y, font='Courier'):
            return [{'text': c, 'x0': x+i*6, 'x1': x+(i+1)*6, 'top': y, 'bottom': y+10,
                     'fontname': font, 'size': 10} for i, c in enumerate(value)]
        r.write(self.root/'inventory.json', {'source_sha256': 'fixture', 'pages': [
            {'page': i, 'glyph_file': f'page-{i:04d}.json'} for i in [1, 2]]})
        r.write(self.root/'page-0001.json', {'page': 1, 'width': 600, 'height': 800,
            'chars': chars('def f(x):', 60, 100) + chars('if x:', 84, 120) + chars('(2.1)', 500, 300, 'Times')
                     + chars('See (2.1) in prose', 60, 400, 'Times')})
        r.write(self.root/'page-0002.json', {'page': 2, 'width': 600, 'height': 800,
            'chars': chars('return x', 108, 100) + chars('return 0', 84, 120)
                     + chars('(2.3)', 500, 300, 'Times') + chars('(2.3)', 500, 400, 'Times')})

    def test_code_indent_continues_across_pages_and_is_only_parsed(self):
        code, mapping = r.recover_code(self.root, [{'page': 1}, {'page': 2}], True)
        self.assertEqual(code, 'def f(x):\n    if x:\n        return x\n    return 0\n')
        self.assertEqual(mapping['python_syntax'], 'passed (not executed)')
        self.assertEqual(mapping['lines'][2]['source_page'], 2)
        self.assertEqual(mapping['warnings'], [])

    def test_equation_candidates_distinguish_margin_and_prose(self):
        result = r.equation_inventory(self.root)
        self.assertEqual(result['right_margin_count'], 3)
        self.assertEqual(len(result['candidates']), 4)
        self.assertEqual(result['duplicate_candidates'], {'2.3': 2})
        self.assertEqual(result['gap_candidates'][0]['missing_count'], 1)

    def test_locate_returns_physical_page_and_coordinates(self):
        result = r.locate(self.root, 'return x')
        self.assertEqual(len(result['matches']), 1)
        self.assertEqual(result['matches'][0]['page'], 2)
        self.assertEqual(result['matches'][0]['bbox'], [108, 100, 156, 110])


if __name__ == '__main__': unittest.main()
