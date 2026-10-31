# -*- coding: utf-8 -*-
"""v104: approval must remain valid until immediately before server STOP.

Synthetic ZIPs only; never connects to / starts a server or writes live data.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import zipfile

from aktualizuj_soulbound import run_update, UpdateError


class StagingContract(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory(prefix='sb104_stage_contract_')
        self.addCleanup(self.folder.cleanup)
        self.base = Path(self.folder.name)
        self.root = self.base / 'game'
        (self.root / 'core').mkdir(parents=True)
        (self.root / 'core/bootstrap_economy_professions.py').write_text(
            'VERSION = "103.00.0"\n', encoding='utf-8')
        self.archive = self.base / 'Soulbound-MUD-v104.00.0-FINAL.zip'
        self.create_zip()
        self.statefile = self.base / 'Soulbound_PREDEPLOY' / 'last_result.json'
        self.statefile.parent.mkdir()
        self.approve()

    def create_zip(self, *, named_version='104.00.0', root_version='104.00.0'):
        with zipfile.ZipFile(self.archive, 'w') as z:
            z.writestr('VERSION', root_version + '\n')
            z.writestr('server.py', '# test placeholder\n')
            z.writestr('core/bootstrap_economy_professions.py',
                       f'VERSION = "{named_version}"\n')
            z.writestr('CHANGELOG_PL.txt', 'test only\n')
            z.writestr('START_Soulbound.bat', '@echo off\n')
            z.writestr('STOP_Soulbound.bat', '@echo off\n')
            z.writestr('predeploy_check.py', '# test only\n')

    def approve(self):
        info = dict(status='PASS', quality_gate='ULTIMATE-60-PLUS',
                    completed_stages=60, required_stages=60, returncode=0,
                    version='104.00.0', installed_at_test='103.00.0',
                    zip=str(self.archive),
                    sha256=hashlib.sha256(self.archive.read_bytes()).hexdigest())
        self.statefile.write_text(json.dumps(info), encoding='utf-8')

    def test_changed_archive_while_staging_cannot_stop_server(self):
        def swap(_archive, _stage, _mapping):
            # Simulate another process altering the approved release while
            # files are staged, even though the ZIP still parses correctly.
            self.create_zip(root_version='103.00.0')
        with mock.patch('aktualizuj_soulbound.stage_release', side_effect=swap), \
             mock.patch('aktualizuj_soulbound.stop_local_server') as stop, \
             mock.patch('aktualizuj_soulbound.backup_existing') as backup:
            with self.assertRaisesRegex(UpdateError, 'zmieniono ZIP'):
                run_update(self.root, self.archive, '104.00.0', restart=False)
            stop.assert_not_called()
            backup.assert_not_called()

    def test_missing_version_file_fails_before_stopping(self):
        with zipfile.ZipFile(self.archive,'w') as z:
            for name in ('server.py','core/bootstrap_economy_professions.py',
                         'CHANGELOG_PL.txt','START_Soulbound.bat',
                         'STOP_Soulbound.bat','predeploy_check.py'):
                data = 'VERSION = "104.00.0"\n' if name.startswith('core/') else 'test\n'
                z.writestr(name,data)
        self.approve()
        with mock.patch('aktualizuj_soulbound.stop_local_server') as stop:
            with self.assertRaisesRegex(UpdateError, 'VERSION'):
                run_update(self.root, self.archive, '104.00.0', restart=False)
            stop.assert_not_called()

    def test_bad_release_filename_fails_before_stopping(self):
        wrong = self.base / 'unlabelled.zip'
        wrong.write_bytes(self.archive.read_bytes())
        self.archive = wrong
        self.approve()
        with mock.patch('aktualizuj_soulbound.stop_local_server') as stop:
            with self.assertRaisesRegex(UpdateError, 'nazwa ZIP'):
                run_update(self.root, self.archive, '104.00.0', restart=False)
            stop.assert_not_called()


if __name__ == '__main__':
    unittest.main()
