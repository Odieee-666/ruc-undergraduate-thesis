import argparse
import contextlib
import io
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from test_pipeline import t


class BuildCommandsTests(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.project = t.init_project(Path(temp.name)/'project')
        self.out = self.project/'build'
        tool = patch.object(t, 'tool', side_effect=lambda name, *args: name)
        tool.start()
        self.addCleanup(tool.stop)

    def cli(self, *args):
        with patch.object(sys, 'argv', ['thesis.py', 'build', str(self.project), *args]), \
                contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return t.main()

    def test_doctor_and_standalone_build_use_selected_engine(self):
        for distro, is_miktex, timeout in [('MiKTeX', True, 180), ('TeX Live', False, 9)]:
            with self.subTest(distro=distro):
                version = f'XeTeX test engine\nDistribution: {distro}\n'
                commands = []
                def run(command, **options):
                    commands.append((command, options.get('timeout')))
                    if '--version' in command:
                        return version if command[0] == 'xelatex' else 'test version'
                    if command[0] == 'kpsewhich':
                        return 'packages/' + command[1]
                    if command[-1] == 'probe.tex':
                        return '\n'.join(f'RUC-FONT-{i}-OK' for i in range(8))
                    if command[-1] == 'main.tex':
                        for name in ('main.pdf', 'main.log', 'main.bcf', 'main.aux'):
                            (self.out/name).touch()
                    return ''
                with patch.object(t, 'run', side_effect=run):
                    # A stale report claiming a different distribution cannot control build.
                    t.write_json(self.project/'environment.json', {'tools': {'xelatex': {'version': 'old'}}})
                    options = [] if timeout == 180 else ['--timeout', str(timeout)]
                    for after_doctor in (False, True):
                        if after_doctor:
                            self.assertTrue(t.doctor(argparse.Namespace(input_type='tex', portable=False))['ready'])
                            probes = [cmd for cmd, _ in commands if cmd[-1] == 'probe.tex']
                            self.assertEqual(len(probes), 2)
                            for cmd in probes:
                                self.assertEqual(cmd.count('--disable-installer'), int(is_miktex))
                        commands.clear()
                        self.assertEqual(self.cli(*options), 0)
                        self.assertTrue(all(seconds == timeout for _, seconds in commands))
                        argv = [cmd for cmd, _ in commands]
                        self.assertEqual(argv.count(['xelatex', '--version']), 1)
                        passes = [cmd for cmd in argv if cmd[-1] == 'main.tex']
                        self.assertEqual(len(passes), 3)
                        for cmd in passes:
                            self.assertEqual(cmd.count('--disable-installer'), int(is_miktex))
                        biber, = [cmd for cmd in argv if cmd[0] == 'biber']
                        self.assertNotIn('--disable-installer', biber)
                        self.assertEqual(argv, t.read_json(self.out/'build-report.json')['commands'])
                        commands.clear()

    def test_missing_package_and_timeout_diagnostics(self):
        for timeout in (False, True):
            with self.subTest(timeout=timeout):
                def run(command, **kw):
                    if '--version' in command:
                        return 'MiKTeX'
                    self.assertIn('--disable-installer', command)
                    if timeout:
                        raise subprocess.TimeoutExpired(command, kw['timeout'], output=b'partial output')
                    raise RuntimeError("LaTeX Error: File 'ruc-missing.sty' not found.")
                with patch.object(t, 'run', side_effect=run):
                    self.assertEqual(self.cli('--timeout', '7'), 1)
                report = t.read_json(self.out/'build-report.json')
                log = (self.out/'build-transcript.txt').read_text(encoding='utf-8')
                self.assertEqual(report['status'], 'failed')
                diagnostic, = report['diagnostics']
                self.assertEqual(diagnostic['command'], report['commands'][-1])
                if timeout:
                    self.assertEqual(diagnostic['kind'], 'timeout')
                    self.assertEqual(diagnostic['seconds'], 7)
                    self.assertIn('partial output', log)
                    for marker in ('7 seconds', '--timeout', 'main.tex'):
                        self.assertIn(marker, report['error'])
                        self.assertIn(marker, log)
                else:
                    self.assertEqual(diagnostic['file'], 'ruc-missing.sty')
                    for marker in ("File 'ruc-missing.sty' not found", 'MiKTeX Console'):
                        self.assertIn(marker, report['error'])
                        self.assertIn(marker, log)
