"""Behavior checks with retained, isolated artifacts; run with bundled Python."""
import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

BASE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('thesis', BASE / 'ruc-undergraduate-thesis/scripts/thesis.py')
t = importlib.util.module_from_spec(spec)
spec.loader.exec_module(t)


class PipelineTests(unittest.TestCase):
    def setUp(self):
        # Dependency behavior is tested separately; these tests isolate import logic.
        probe = patch.object(t, 'doctor', return_value={'ready': True, 'missing': []})
        probe.start()
        self.addCleanup(probe.stop)

    @classmethod
    def setUpClass(cls):
        (BASE / 'output').mkdir(exist_ok=True)
        cls.root = Path(tempfile.mkdtemp(prefix='ruc-tests-', dir=BASE / 'output'))
        print('TEST_ARTIFACTS=' + str(cls.root))

    def args(self, source, output, **kw):
        defaults = dict(source=str(source), output=str(output), metadata=None, portable=False)
        defaults.update(kw)
        return argparse.Namespace(**defaults)

    def test_no_overwrite(self):
        dest = t.init_project(self.root / 'existing')
        (dest / 'marker').write_text('keep')
        with self.assertRaises(ValueError):
            t.init_project(dest)
        self.assertEqual((dest / 'marker').read_text(), 'keep')

    def test_pdf_native_math_code_and_links_require_review(self):
        from reportlab.pdfgen.canvas import Canvas
        src = self.root / 'math-code.pdf'
        canvas = Canvas(str(src))
        canvas.setFont('Helvetica',12)
        canvas.drawString(60,760,'Native selectable text ' * 5)
        canvas.setFont('Symbol',12)
        canvas.drawString(60,730,'a+b=g')
        canvas.setFont('Courier',10)
        canvas.drawString(60,700,'def f(value):')
        canvas.drawString(84,685,'return value + 1 # indented source line')
        canvas.linkURL('https://example.org/source', (60,670,200,682))
        canvas.save()
        dest = self.root / 'math-code-import'
        t.import_pdf(self.args(src,dest,dpi=72,ocr=False,ocr_all=False,tesseract=None,ocr_language='eng'))
        evidence = t.read_json(dest / 'source/glyphs/inventory.json')
        page = evidence['pages'][0]
        self.assertIn('math-reconstruction-required',page['flags'])
        self.assertIn('code-indentation-review',page['flags'])
        self.assertNotIn('sparse-text-review',page['flags'])
        self.assertFalse(page['reviewed'])
        glyphs = t.read_json(dest / 'source/glyphs/page-0001.json')
        self.assertEqual(glyphs['links'][0]['uri'],'https://example.org/source')
        self.assertTrue(all('matrix' in c for c in glyphs['chars']))
        self.assertTrue(any(abs(c['x0']-84)<.1 for c in glyphs['chars'] if 'Courier' in c['fontname']))

    def test_explicit_blank_metadata_stays_blank(self):
        meta = self.root / 'explicit-blank.json'
        t.write_json(meta,{'author':'作者','date':'','code':''})
        dest=t.init_project(self.root / 'explicit-blank',meta)
        text=(dest/'metadata.tex').read_text(encoding='utf-8')
        self.assertIn('date={}',text)
        self.assertIn('code={}',text)
        self.assertIn('college={待填写}',text)

    def test_metadata_escapes_literal_text(self):
        meta = self.root / 'meta.json'
        t.write_json(meta, {'title': 'A&B_50% #1 $x$ {z}', 'author': '张三'})
        dest = t.init_project(self.root / 'escaped', meta)
        content = (dest / 'metadata.tex').read_text(encoding='utf-8')
        self.assertIn(r'A\&B\_50\% \#1 \$x\$ \{z\}', content)
        self.assertIn('张三', content)

    def test_tex_literal_percent_is_preserved(self):
        source = '% \\begin{document}\n\\verb|\\begin{document}|\n\\begin{verbatim}\n\\end{document}\n\\end{verbatim}\n\\begin{document}Cost 50\\% still visible % comment\nnext\\end{document}'
        result = t.tex_structure_mask(source)
        self.assertEqual(len(result),len(source))
        self.assertEqual(result.count(r'\begin{document}'),1)
        self.assertEqual(result.count(r'\end{document}'),1)
        self.assertIn('still visible',result)
        self.assertNotIn('comment',result)

    def test_demo_keeps_portable_option(self):
        dest = t.init_project(self.root / 'portable-demo', demo=True, portable=True)
        self.assertIn('numeric,portable', (dest / 'main.tex').read_text(encoding='utf-8'))

    def test_tex_keeps_source_resources(self):
        src = self.root / 'tex-source'
        src.mkdir()
        (src / 'main.tex').write_text(r'\documentclass{article}\newcommand{\custom}{kept}\begin{document}\section{Input}\input{section}\end{document}', encoding='utf-8')
        (src / 'section.tex').write_text(r'Text $x_1=2$ and \custom.', encoding='utf-8')
        dest = self.root / 'tex-import'
        t.import_tex(self.args(src / 'main.tex', dest, source_root=None))
        self.assertEqual((src / 'section.tex').read_bytes(), (dest / 'source/section.tex').read_bytes())
        self.assertIn(r'\input{source/section.tex}', (dest / 'content/body.tex').read_text())
        self.assertIn(r'\newcommand{\custom}', (dest / 'original-preamble.tex.txt').read_text())
        self.assertEqual(t.read_json(dest / 'conversion.json')['status'], 'needs-review')
        with self.assertRaises(ValueError):
            t.import_tex(self.args(src / 'main.tex', src / 'nested', source_root=None))

    def test_docx_structural_conversion(self):
        pandoc = t.tool('pandoc')
        self.assertIsNotNone(pandoc, 'Install Pandoc before integration tests')
        md = self.root / 'input.md'
        # Independent markdown writer builds a DOCX with real OMML, image, table and footnote.
        md.write_text('# 研究方法\n\n中文内容与英文 text。公式 $x_i^2+1$。[^n]\n\n[^n]: 实际脚注内容。\n\n| 组别 | 数值 |\n|---|---:|\n| A | 12 |\n| B | 23 |\n\n![图形检查](fixture.png){width=2cm}\n', encoding='utf-8')
        from PIL import Image, ImageDraw
        im = Image.new('RGB', (100, 60), 'white')
        ImageDraw.Draw(im).line((5, 55, 95, 5), fill='black', width=3)
        im.save(self.root / 'fixture.png')
        docx = self.root / 'fixture.docx'
        t.run([pandoc, md.name, '-o', docx.name], cwd=self.root)
        dest = self.root / 'docx-import'
        result = t.import_docx(self.args(docx, dest, pandoc=pandoc, track_changes='error'))
        for key in ['tables', 'equations', 'drawings', 'footnote_references']:
            self.assertGreater(result['counts'][key], 0)
        body = (dest / 'content/body.tex').read_text(encoding='utf-8')
        for fragment in ['研究方法', '中文内容', 'footnote', 'includegraphics', 'longtable', 'x_{i}']:
            self.assertIn(fragment, body)
        self.assertTrue(list((dest / 'media').rglob('*.png')))
        # Add a real tracked insertion, verify default refusal precedes output creation.
        tracked = self.root / 'tracked.docx'
        with zipfile.ZipFile(docx) as z, zipfile.ZipFile(tracked, 'w') as out:
            for info in z.infolist():
                data = z.read(info.filename)
                if info.filename == 'word/document.xml':
                    data = data.replace(b'</w:body>', b'<w:p><w:ins w:id="1" w:author="Test"><w:r><w:t>revision</w:t></w:r></w:ins></w:p></w:body>')
                out.writestr(info, data)
        with self.assertRaises(ValueError):
            t.import_docx(self.args(tracked, self.root / 'tracked-output', pandoc=pandoc, track_changes='error'))
        self.assertFalse((self.root / 'tracked-output').exists())

    def test_pdf_text_and_scan_gate(self):
        from reportlab.pdfgen.canvas import Canvas
        from PIL import Image, ImageDraw
        textpdf = self.root / 'text.pdf'
        c = Canvas(str(textpdf)); c.drawString(50, 700, 'SOURCE SENTINEL: This paragraph must survive PDF extraction without silent loss.'); c.save()
        dest = self.root / 'pdf-import'
        args = self.args(textpdf, dest, dpi=96, ocr=False, tesseract=None, ocr_all=False, ocr_language='eng')
        t.import_pdf(args)
        self.assertIn('SOURCE SENTINEL', t.read_json(dest / 'source/pages.json')[0]['text'])
        im = Image.new('RGB', (600, 200), 'white'); ImageDraw.Draw(im).text((40, 50), 'SCANNED TEXT', fill='black')
        scan = self.root / 'scan.pdf'; im.save(scan, 'PDF')
        args.source = str(scan); args.output = str(self.root / 'scan-import')
        t.import_pdf(args)
        report = t.read_json(Path(args.output) / 'conversion.json')
        self.assertEqual(report['details']['sparse_pages'], [1])
        self.assertFalse(report['content_reviewed'])
        self.assertIn('OCR', (Path(args.output) / 'content/body.tex').read_text(encoding='utf-8'))

    def test_log_quality_gate(self):
        report = t.diagnose(self.root, 'Missing character: There is no 中\nLaTeX Warning: Reference `missing` undefined on input line 4.\nOverfull \\hbox (2.0pt too wide)\n')
        self.assertEqual({r['kind'] for r in report}, {'missing-glyph', 'undefined-reference', 'overfull-box'})

    def test_tex_document_markers_in_literals_do_not_truncate(self):
        src = self.root / 'literal-tex-source'
        src.mkdir()
        body = '\nSTART% join with no space\nEND\n\\verb|\\end{document}|\n\\begin{verbatim}\n\\end{document}\n\\end{verbatim}\nTAIL\n'
        (src/'main.tex').write_text('\\documentclass{article}\n\\begin{document}'+body+'\\end{document}\n',encoding='utf-8')
        dest = self.root/'literal-tex-import'
        t.import_tex(self.args(src/'main.tex',dest,source_root=None))
        self.assertEqual((dest/'content/body.tex').read_text(encoding='utf-8'),body)

    def test_invalid_metadata_leaves_destination_available(self):
        meta=self.root/'invalid-meta.json'
        t.write_json(meta,{'unknown-field':'x'})
        dest=self.root/'invalid-meta-output'
        with self.assertRaises(ValueError):t.init_project(dest,meta)
        self.assertFalse(dest.exists())
        t.write_json(meta,{'author':None})
        with self.assertRaises(ValueError):t.init_project(dest,meta)
        self.assertFalse(dest.exists())

    def test_render_refuses_stale_pages_and_invalid_dpi(self):
        from reportlab.pdfgen.canvas import Canvas
        src=self.root/'render-input.pdf'
        c=Canvas(str(src));c.drawString(50,700,'New one-page file');c.save()
        dest=self.root/'render-reused';dest.mkdir()
        (dest/'page-0002.png').write_bytes(b'previous render')
        with self.assertRaises(ValueError):t.render(argparse.Namespace(pdf=src,output=dest,dpi=72))
        self.assertEqual((dest/'page-0002.png').read_bytes(),b'previous render')
        self.assertFalse((dest/'page-0001.png').exists())
        fresh=self.root/'render-invalid'
        with self.assertRaises(ValueError):t.render(argparse.Namespace(pdf=src,output=fresh,dpi=0))
        self.assertFalse(fresh.exists())
        valid=self.root/'render-fresh'
        with patch.object(t,'tool',return_value=None):
            result=t.render(argparse.Namespace(pdf=src,output=valid,dpi=72))
        self.assertEqual(result['rendered_pages'],1)
        self.assertFalse(t.read_json(valid/'render-report.json')['visual_reviewed'])
        import hashlib
        self.assertEqual(t.read_json(valid/'render-report.json')['pdf_sha256'],hashlib.sha256(src.read_bytes()).hexdigest())

    def test_docx_non_insertion_revisions_and_notes_are_detected(self):
        pandoc=t.tool('pandoc')
        md=self.root/'revision-base.md';md.write_text('Base paragraph.\n',encoding='utf-8')
        base=self.root/'revision-base.docx';t.run([pandoc,md,'-o',base])
        for name,part,fragment in [
            ('move','word/document.xml',b'<w:p><w:moveFrom w:id="9"><w:r><w:t>Moved text</w:t></w:r></w:moveFrom></w:p>'),
            ('format','word/document.xml',b'<w:p><w:r><w:rPr><w:rPrChange w:id="10"><w:rPr><w:b/></w:rPr></w:rPrChange></w:rPr><w:t>Changed formatting</w:t></w:r></w:p>'),
            ('note','word/footnotes.xml',b'<w:footnote w:id="1"><w:p><w:ins w:id="11"><w:r><w:t>Changed footnote</w:t></w:r></w:ins></w:p></w:footnote>')]:
            src=self.root/(name+'-revision.docx')
            with zipfile.ZipFile(base) as z,zipfile.ZipFile(src,'w') as out:
                for info in z.infolist():
                    if info.filename==part and part!='word/document.xml':continue
                    data=z.read(info.filename)
                    if info.filename==part:data=data.replace(b'</w:body>',fragment+b'</w:body>')
                    out.writestr(info,data)
                if part!='word/document.xml':out.writestr(part,b'<w:footnotes xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'+fragment+b'</w:footnotes>')
            dest=self.root/(name+'-revision-output')
            with self.assertRaises(ValueError,msg=name):t.import_docx(self.args(src,dest,pandoc=pandoc,track_changes='error'))
            self.assertFalse(dest.exists())

    def test_failed_build_records_failing_command_output(self):
        project=t.init_project(self.root/'failed-build')
        failure='Command failed (1): xelatex\n! Undefined control sequence: \\badmacro'
        with patch.object(t,'tool',side_effect=lambda name:name),patch.object(t,'run',side_effect=['TeX Live', RuntimeError(failure)]):
            with self.assertRaises(RuntimeError):t.build(argparse.Namespace(project=project,strict=True,timeout=5))
        self.assertIn('badmacro',(project/'build/build-transcript.txt').read_text(encoding='utf-8'))
        self.assertEqual(t.read_json(project/'build/build-report.json')['status'],'failed')

    def test_missing_compiler_invalidates_previous_success(self):
        project=t.init_project(self.root/'missing-compiler')
        (project/'build').mkdir()
        t.write_json(project/'build/build-report.json',{'status':'compiled','pdf_sha256':'stale'})
        with patch.object(t,'tool',return_value=None):
            with self.assertRaises(ValueError):t.build(argparse.Namespace(project=project,strict=True,timeout=5))
        report=t.read_json(project/'build/build-report.json')
        self.assertEqual(report['status'],'failed')
        self.assertNotIn('pdf_sha256',report)


if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    unittest.main(verbosity=2)
