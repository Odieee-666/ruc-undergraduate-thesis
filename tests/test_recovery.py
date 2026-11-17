"""Failure injection verifies progress reuse and preservation of existing data."""
import argparse
import importlib.util
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

BASE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('thesis_recovery', BASE / 'ruc-undergraduate-thesis/scripts/thesis.py')
t = importlib.util.module_from_spec(spec)
spec.loader.exec_module(t)


class RecoveryTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)

    def docx_args(self):
        from zipfile import ZipFile
        src = self.root / 'input.docx'
        with ZipFile(src, 'w') as z:
            z.writestr('word/document.xml', '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body/></w:document>')
        return argparse.Namespace(source=str(src), output=str(self.root / 'result'), metadata=None,
                                  portable=True, pandoc=None, track_changes='error', resume=False, retry=False)

    def test_docx_resume_reuses_ast_and_preserves_existing_output(self):
        args = self.docx_args()
        calls = []
        fail = True
        def run(command, cwd=None, **kw):
            if '--version' in command: return 'pandoc test'
            dest = Path(cwd)
            calls.append(command[command.index('-t') + 1])
            if calls[-1] == 'json':
                (dest / 'source/document.json').write_text('{}')
                (dest / 'media/image.png').write_bytes(b'image')
            elif fail: raise RuntimeError('injected conversion failure')
            else: (dest / 'content/body.tex').write_text('Recovered body')
            return ''
        with patch.object(t, 'doctor', return_value={'ready': True}), patch.object(t, 'tool', return_value='pandoc'), patch.object(t, 'run', side_effect=run):
            with self.assertRaisesRegex(RuntimeError, 'injected'): t.import_docx(args)
            self.assertFalse(Path(args.output).exists())
            state = t.read_json(self.root / '.result.import/state.json')
            self.assertEqual(state['status'], 'failed')
            self.assertIn('docx-ast', state['completed'])
            self.assertEqual(state['attempts'][-1]['stage'], 'docx-latex')
            fail = False; args.resume = True
            t.import_docx(args)
            self.assertEqual(calls, ['json', 'latex', 'latex'])
            self.assertEqual((Path(args.output) / 'content/body.tex').read_text(), 'Recovered body')
            with self.assertRaisesRegex(ValueError, 'already exists'): t.import_docx(args)

    def test_missing_dependencies_leave_no_final_directory_and_can_resume(self):
        args = self.docx_args()
        with patch.object(t, 'doctor', return_value={'ready': False, 'missing': [{'item': 'pandoc', 'remedy': 'install'}]}):
            with self.assertRaisesRegex(ValueError, 'pandoc'): t.import_docx(args)
        self.assertFalse(Path(args.output).exists())
        state = t.read_json(self.root / '.result.import/state.json')
        self.assertEqual(state['attempts'][-1]['stage'], 'preflight')
        self.assertEqual(state['completed'], {})

    def test_changed_source_requires_retry_and_retry_archives_work(self):
        args = self.docx_args()
        with patch.object(t, 'doctor', side_effect=RuntimeError('missing')):
            with self.assertRaises(RuntimeError): t.import_docx(args)
            with Path(args.source).open('ab') as stream: stream.write(b'changed')
            args.resume = True
            with self.assertRaisesRegex(ValueError, 'changed'): t.import_docx(args)
            args.resume = False; args.retry = True
            with self.assertRaises(RuntimeError): t.import_docx(args)
        self.assertEqual(len(list(self.root.glob('.result.import.saved-*'))), 1)

    def test_pdf_resume_skips_completed_pages(self):
        from reportlab.pdfgen.canvas import Canvas
        src = self.root / 'input.pdf'
        canvas = Canvas(str(src))
        for i in range(3):
            canvas.drawString(50, 700, 'A sufficiently long native text line on page ' + str(i))
            canvas.showPage()
        canvas.save()
        args = argparse.Namespace(source=str(src), output=str(self.root/'result'), metadata=None,
            portable=True, dpi=72, ocr=False, ocr_all=False, tesseract=None, ocr_language='eng', resume=False)
        from PIL import Image
        original = Image.Image.save
        counts = []
        def save(image, file, *a, **kw):
            counts.append(Path(file).name)
            if Path(file).name == 'page-0002.png': raise OSError('disk full')
            return original(image, file, *a, **kw)
        with patch.object(t, 'doctor', return_value={'ready': True}), patch.object(Image.Image, 'save', save):
            with self.assertRaisesRegex(OSError, 'disk full'): t.import_pdf(args)
        self.assertFalse(Path(args.output).exists())
        counts.clear()
        def save_ok(image, file, *a, **kw):
            counts.append(Path(file).name)
            return original(image, file, *a, **kw)
        args.resume = True
        with patch.object(t, 'doctor', return_value={'ready': True}), patch.object(Image.Image, 'save', save_ok):
            t.import_pdf(args)
        self.assertEqual(counts, ['page-0002.png', 'page-0003.png'])
        self.assertEqual(len(t.read_json(Path(args.output)/'source/pages.json')), 3)

    def test_changed_checkpoint_is_not_silently_used(self):
        args = self.docx_args()
        def run(command, cwd=None, **kw):
            if '--version' in command: return 'pandoc test'
            if 'json' == command[command.index('-t')+1]:
                (Path(cwd)/'source/document.json').write_text('{}'); return ''
            raise RuntimeError('failed')
        with patch.object(t, 'doctor', return_value={'ready': True}), patch.object(t, 'tool', return_value='pandoc'), patch.object(t, 'run', side_effect=run):
            with self.assertRaises(RuntimeError): t.import_docx(args)
            (self.root/'.result.import/project/source/document.json').write_text('edited')
            args.resume = True
            with self.assertRaisesRegex(ValueError, 'Checkpoint artifact changed'): t.import_docx(args)

    def test_doctor_aggregates_missing_tools(self):
        api = SimpleNamespace(TEMPLATE=t.TEMPLATE, tool=lambda *a: None, run=t.run)
        result = t.helper('preflight').check(api, argparse.Namespace(input_type='docx', portable=True))
        self.assertFalse(result['ready'])
        self.assertEqual({x['item'] for x in result['missing']}, {'xelatex', 'biber', 'kpsewhich', 'pandoc'})

    def test_ocr_language_and_font_failures_are_actionable(self):
        def run(command, **kw):
            if '--version' in command: return 'fake 1.0'
            if '--list-langs' in command: return 'List of available languages (1):\neng\n'
            if command[0] == 'kpsewhich': return 'tex/' + command[1]
            return ''  # No font success markers.
        api = SimpleNamespace(TEMPLATE=t.TEMPLATE, tool=lambda name, *a: name, run=run)
        args = argparse.Namespace(input_type='pdf', portable=False, ocr=True, ocr_language='chi_sim+eng')
        result = t.helper('preflight').check(api, args)
        missing = {x['item'] for x in result['missing']}
        self.assertIn('tesseract:chi_sim', missing)
        self.assertIn('SimSun', missing)
        self.assertNotIn('tesseract:eng', missing)

    def test_missing_tex_package_is_reported_before_probe(self):
        def run(command, **kw):
            if '--version' in command: return 'fake 1.0'
            if command[0] == 'kpsewhich':
                if command[1] == 'ctexart.cls': raise RuntimeError('not found')
                return 'tex/' + command[1]
            return '\n'.join(f'RUC-FONT-{i}-OK' for i in range(8))
        api = SimpleNamespace(TEMPLATE=t.TEMPLATE, tool=lambda name, *a: name, run=run)
        result = t.helper('preflight').check(api, argparse.Namespace(input_type='tex', portable=False))
        self.assertFalse(result['ready'])
        self.assertIn('ctexart.cls', {x['item'] for x in result['missing']})
        self.assertNotIn('template_probe', result)

    def test_lock_prevents_two_importers_and_keeps_checkpoint(self):
        args = self.docx_args()
        lock = self.root/'.result.import.lock'
        lock.write_text('another process')
        with self.assertRaisesRegex(ValueError, 'Import lock exists'): t.import_docx(args)
        self.assertEqual(lock.read_text(), 'another process')
        self.assertFalse(Path(args.output).exists())


if __name__ == '__main__': unittest.main(verbosity=2)
