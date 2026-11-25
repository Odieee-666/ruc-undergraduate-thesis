from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

import smoke_clean


class TexLivePackageInventoryTests(unittest.TestCase):
    def test_missing_tlmgr_is_recorded_as_skipped(self):
        with tempfile.TemporaryDirectory() as directory, \
                patch.object(smoke_clean.shutil, 'which', return_value=None), \
                patch.object(smoke_clean.subprocess, 'run') as run:
            step = smoke_clean.record_texlive_packages(Path(directory))
            self.assertEqual(step['status'], 'skipped')
            self.assertIn('PATH', step['reason'])
            self.assertFalse((Path(directory)/'texlive-packages.log').exists())
            run.assert_not_called()

    def test_inventory_exit_codes_and_output(self):
        command = [str(Path('texlive', 'bin', 'tlmgr.bat')), 'info', '--only-installed']
        for code, status, stderr in [(0, 'passed', b''), (1, 'failed', b'user mode not initialized')]:
            with self.subTest(code=code), tempfile.TemporaryDirectory() as directory, \
                    patch.object(smoke_clean.shutil, 'which', return_value=command[0]), \
                    patch.object(smoke_clean.subprocess, 'run', return_value=
                                 subprocess.CompletedProcess(command, code, b'package list', stderr)) as run:
                root = Path(directory)
                self.assertEqual(smoke_clean.record_texlive_packages(root), {
                    'name': 'texlive-packages', 'command': command, 'status': status, 'exit_code': code})
                self.assertEqual((root/'texlive-packages.log').read_bytes(), b'package list\n' + stderr)
                run.assert_called_once_with(command, capture_output=True, timeout=300)

    def test_launch_failure_and_timeout_keep_diagnostics(self):
        command = ['tlmgr', 'info', '--only-installed']
        cases = [
            (FileNotFoundError('resolved executable vanished'), 'vanished', b'\n'),
            (subprocess.TimeoutExpired(command, 300, output=b'partial output', stderr=b'partial error'),
             'timed out', b'partial output\npartial error'),
        ]
        for error, reason, output in cases:
            with self.subTest(error=error), tempfile.TemporaryDirectory() as directory, \
                    patch.object(smoke_clean.shutil, 'which', return_value=command[0]), \
                    patch.object(smoke_clean.subprocess, 'run', side_effect=error):
                root = Path(directory)
                step = smoke_clean.record_texlive_packages(root)
                self.assertEqual(step['status'], 'failed')
                self.assertEqual(step['command'], command)
                self.assertIn(reason, step['reason'])
                self.assertNotIn('exit_code', step)
                self.assertEqual((root/'texlive-packages.log').read_bytes(), output)
