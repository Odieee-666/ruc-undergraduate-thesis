import argparse
import codecs
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from test_pipeline import t


class TexMigrationTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.src = self.root/'original'
        self.src.mkdir()
        self.output = self.root/'result'
        self.args = argparse.Namespace(source=str(self.src/'main.tex'), source_root=None,
                                       output=str(self.output), metadata=None, portable=True)
        doctor = patch.object(t, 'doctor', return_value={'ready': True})
        doctor.start()
        self.addCleanup(doctor.stop)

    def test_single_file_decoders(self):
        body = '\n中文内容 % 注释\n$x_1$\\label{eq:x}\n'
        for encoding, decoder in [('utf-8', 'utf-8'), ('utf-8-sig', 'utf-8-sig'), ('gbk', 'gb18030')]:
            with self.subTest(encoding=encoding):
                data = (r'\begin{document}' + body + r'\end{document}').encode(encoding)
                Path(self.args.source).write_bytes(data)
                out = self.root/encoding
                self.args.output = str(out)
                t.import_tex(self.args)
                self.assertEqual((out/'content/body.tex').read_text(encoding='utf-8'), body)
                self.assertEqual((out/'source/main.tex').read_bytes(), data)
                self.assertEqual(Path(self.args.source).read_bytes(), data)
                record = t.read_json(out/'conversion.json')
                self.assertEqual(record['details']['files'], [
                    {'source_path': 'main.tex', 'decoder': decoder, 'work_path': 'content/body.tex'}])
                self.assertEqual(any('fallback' in i for i in record['issues']), encoding == 'gbk')
                self.assertFalse((out/'tex-work').exists())

    def test_graph_paths_archive_and_review(self):
        entry = self.src/'paper'
        entry.mkdir()
        self.args.source_root = str(self.src)
        self.args.source = str(entry/'paper.tex')
        chapter = r'''章节。\input{小节}\input{../乙/小节.tex}\includegraphics{示意.png}
% \input{bad}
\verb|\input{bad}|
\begin{verbatim}\input{bad}\end{verbatim}
\input{\dynamic}\input{../../outside}\inputencoding{GBK}
'''
        sources = {'paper/paper.tex': r'''\usepackage{custom}
\addbibresource[location=local]{中文.bib}
\begin{document}\include{甲/章节.tex}\input{甲/章节}\end{document}'''.encode(),
                   'paper/甲/章节.tex': chapter.encode('gbk'), 'paper/甲/小节.tex': '甲文'.encode(),
                   'paper/乙/小节.tex': '乙文'.encode('gb2312'), 'paper/中文.bib': '中文书目'.encode('gbk'),
                   'paper/示意.png': b'\x89PNG\x00\xff', 'paper/bad.tex': b'\xff'}
        for name, data in sources.items():
            path = self.src/name
            path.parent.mkdir(exist_ok=True)
            path.write_bytes(data)
        t.import_tex(self.args)
        for name, data in sources.items():
            self.assertEqual((self.output/'source'/name).read_bytes(), data)
        record = t.read_json(self.output/'conversion.json')
        files = {f['source_path']: f for f in record['details']['files']}
        self.assertEqual(record['details']['include_aux_dirs'], ['tex-work/paper/甲'])
        self.assertEqual(len(record['details']['files']), 5)
        self.assertNotIn('paper/bad.tex', files)
        read = lambda name: (self.output/name).read_text(encoding='utf-8')
        body = read('content/body.tex')
        self.assertIn(r'\include{tex-work/paper/甲/章节}', body)
        self.assertIn(r'\input{tex-work/paper/甲/章节.tex}', body)
        child = read(files['paper/甲/章节.tex']['work_path'])
        for expr in (r'\input{source/paper/甲/小节.tex}', r'\input{tex-work/paper/乙/小节.tex}',
                     r'\includegraphics{source/paper/示意.png}', r'\input{\dynamic}', r'\input{../../outside}'):
            self.assertIn(expr, child)
        self.assertIn(r'\addbibresource[location=local]{tex-work/paper/中文.bib}', read('preamble-extra.tex'))
        self.assertEqual(read(files['paper/中文.bib']['work_path']), '中文书目')
        issues = '\n'.join(record['issues'])
        for marker in ('paper/甲/章节.tex:5', 'inputencoding', 'custom', 'paper/中文.bib: GB18030'):
            self.assertIn(marker, issues)

    def test_invalid_bytes_do_not_publish(self):
        for name, data, message in [('broken', b'OK\xff', 'GB18030 at byte 2'),
                                    ('bom', codecs.BOM_UTF8 + '中文'.encode('gbk'), 'after BOM at byte 3')]:
            with self.subTest(name=name):
                Path(self.args.source).write_text(r'\input{chapter}', encoding='utf-8')
                (self.src/'chapter.tex').write_bytes(data)
                self.args.output = str(self.root/name)
                with self.assertRaisesRegex(ValueError, 'chapter.tex: .*' + message):
                    t.import_tex(self.args)
                self.assertFalse(Path(self.args.output).exists())
                state = t.read_json(self.root/f'.{name}.import/state.json')
                self.assertIn(message, state['attempts'][-1]['error'])

    def test_resume_checks_chapters_and_working_copies(self):
        Path(self.args.source).write_text(r'\input{中文}', encoding='utf-8')
        chapter = self.src/'中文.tex'
        original = '章节文字'
        for case in ('clean', 'edited-work', 'edited-source'):
            with self.subTest(case=case):
                chapter.write_bytes(original.encode('gbk'))
                self.args.output = str(self.root/case)
                self.args.resume = self.args.retry = False
                with patch.object(t, 'report_import', side_effect=OSError('interrupted')):
                    with self.assertRaisesRegex(OSError, 'interrupted'):
                        t.import_tex(self.args)
                work = self.root/f'.{case}.import/project/tex-work/中文.tex'
                if case == 'edited-work':
                    work.write_text('manual edit', encoding='utf-8')
                if case == 'edited-source':
                    chapter.write_bytes('修改'.encode('gbk'))
                self.args.resume = True
                if case != 'clean':
                    with self.assertRaisesRegex(ValueError, '--retry'):
                        t.import_tex(self.args)
                    self.assertFalse(Path(self.args.output).exists())
                    self.args.resume, self.args.retry = False, True
                t.import_tex(self.args)
                self.assertEqual((Path(self.args.output)/'tex-work/中文.tex').read_text(encoding='utf-8'),
                                 '修改' if case == 'edited-source' else original)
                if case == 'edited-work':
                    backup, = self.root.glob('.edited-work.import.saved-*')
                    self.assertEqual((backup/'project/tex-work/中文.tex').read_text(), 'manual edit')
