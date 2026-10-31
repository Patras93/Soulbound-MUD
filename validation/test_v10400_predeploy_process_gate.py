# -*- coding: utf-8 -*-
"""PREDEPLOY 60/60 launcher: exit status, bounded runtime and version contract.

This does NOT assert Windows 60/60 PASS. All tests use synthetic temporary files.
"""
from __future__ import annotations

import os
from pathlib import Path
import sys
import tempfile
import time
import unittest
from unittest.mock import patch
import zipfile

import predeploy_nowej_wersji as prep


class V104PredeployProcessGate(unittest.TestCase):
    def _candidate(self, folder, *, root_version='104.00.0', code_version='104.00.0'):
        path = Path(folder) / 'Soulbound-MUD-v104.00.0-TEST.zip'
        with zipfile.ZipFile(path, 'w') as f:
            f.writestr('VERSION', root_version + '\n')
            f.writestr('server.py', '# fake test only\n')
            f.writestr('core/bootstrap_economy_professions.py', f'VERSION = "{code_version}"\n')
        return path

    def test_all_three_versions_must_agree(self):
        with tempfile.TemporaryDirectory() as folder:
            with patch.object(prep, 'REQUIRED', ('VERSION', 'server.py', 'core/bootstrap_economy_professions.py')):
                self.assertEqual(prep.inspect_zip(self._candidate(folder))[0], '104.00.0')

    def test_conflicting_root_version_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = self._candidate(folder, root_version='103.00.0')
            with patch.object(prep, 'REQUIRED', ('VERSION', 'server.py', 'core/bootstrap_economy_professions.py')):
                with self.assertRaisesRegex(ValueError, 'VERSION'):
                    prep.inspect_zip(path)

    def test_conflicting_code_version_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            path = self._candidate(folder, code_version='103.00.0')
            with patch.object(prep, 'REQUIRED', ('VERSION', 'server.py', 'core/bootstrap_economy_professions.py')):
                with self.assertRaisesRegex(ValueError, 'Numer wersji'):
                    prep.inspect_zip(path)

    def _script(self, folder, source):
        root = Path(folder)
        (root / 'testuj_soulbound_windows.py').write_text(source, encoding='utf-8')
        return root, root / 'test.log'

    def test_main_process_exit_does_not_wait_for_inherited_pipe(self):
        with tempfile.TemporaryDirectory() as folder:
            root, log = self._script(folder,
                'import subprocess, sys\n'
                'subprocess.Popen([sys.executable,"-c","import time; time.sleep(6)"],'
                ' stdout=sys.stdout, stderr=sys.stderr)\n'
                'print("TEST PARENT FINISHED", flush=True)\n')
            started = time.monotonic()
            code = prep.run_tests(root, log, timeout_seconds=4)
            self.assertEqual(code, 0)
            self.assertLess(time.monotonic()-started, 3.5)
            self.assertIn('TEST PARENT FINISHED', log.read_text(encoding='utf-8'))

    def test_timeout_cannot_turn_into_pass(self):
        with tempfile.TemporaryDirectory() as folder:
            root, log = self._script(folder, 'import time\ntime.sleep(20)\n')
            started = time.monotonic()
            with self.assertRaisesRegex(TimeoutError, 'limit'):
                prep.run_tests(root, log, timeout_seconds=1)
            self.assertLess(time.monotonic()-started, 5)
            self.assertIn('TIMEOUT', log.read_text(encoding='utf-8'))

    def test_child_nonzero_exit_is_preserved(self):
        with tempfile.TemporaryDirectory() as folder:
            root, log = self._script(folder, 'import sys\nsys.exit(7)\n')
            self.assertEqual(prep.run_tests(root, log, timeout_seconds=2), 7)

    def test_nonsense_timeout_rejected(self):
        with tempfile.TemporaryDirectory() as folder:
            root, log = self._script(folder, 'pass\n')
            with self.assertRaisesRegex(ValueError, 'limit'):
                prep.run_tests(root, log, timeout_seconds=0)


if __name__ == '__main__':
    unittest.main()
