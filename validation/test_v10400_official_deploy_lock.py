# -*- coding: utf-8 -*-
"""v104: never allow direct updater or --yes to bypass official PREDEPLOY."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock

from aktualizuj_soulbound import (
    UpdateError, require_v104_official_predeploy, run_update,
)


class DeployLockTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='sb104_deploylock_')
        self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.root = self.base / 'game'
        (self.root / 'core').mkdir(parents=True)
        (self.root / 'core' / 'bootstrap_economy_professions.py').write_text(
            'VERSION = "103.00.0"\n', encoding='utf-8')
        self.archive = self.base / 'candidate.zip'
        self.archive.write_bytes(b'fake test data, do not install')
        self.statefile = self.base / 'Soulbound_PREDEPLOY' / 'last_result.json'
        self.statefile.parent.mkdir()

    def make_state(self):
        obj = dict(status='PASS', quality_gate='ULTIMATE-60-PLUS',
                   completed_stages=60, required_stages=60, returncode=0,
                   version='104.00.0', installed_at_test='103.00.0',
                   zip=str(self.archive), sha256=hashlib.sha256(self.archive.read_bytes()).hexdigest())
        self.statefile.write_text(json.dumps(obj), encoding='utf-8')
        return obj

    def test_no_approval_fails_before_server_is_stopped(self):
        with mock.patch('aktualizuj_soulbound.stop_local_server') as stop:
            with self.assertRaises(UpdateError):
                run_update(self.root, self.archive, '104.00.0')
            stop.assert_not_called()

    def test_v103_compatibility(self):
        require_v104_official_predeploy(self.root, self.archive, '103.00.1')

    def test_real_approval_passes(self):
        self.make_state()
        require_v104_official_predeploy(self.root, self.archive, '104.00.0')

    def test_wrong_hash_fails(self):
        self.make_state()
        self.archive.write_bytes(b'changed bytes')
        with self.assertRaisesRegex(UpdateError, 'zmieniono ZIP'):
            require_v104_official_predeploy(self.root, self.archive, '104.00.0')

    def test_wrong_zip_path_fails(self):
        self.make_state()
        other = self.base / 'other.zip'
        other.write_bytes(self.archive.read_bytes())
        with self.assertRaisesRegex(UpdateError, 'innej paczki'):
            require_v104_official_predeploy(self.root, other, '104.00.0')

    def test_wrong_source_version_fails(self):
        obj = self.make_state()
        obj['installed_at_test'] = '102.00.13'
        self.statefile.write_text(json.dumps(obj), encoding='utf-8')
        with self.assertRaises(UpdateError):
            require_v104_official_predeploy(self.root, self.archive, '104.00.0')

    def test_59_of_60_fails(self):
        obj = self.make_state()
        obj['completed_stages'] = 59
        self.statefile.write_text(json.dumps(obj), encoding='utf-8')
        with self.assertRaises(UpdateError):
            require_v104_official_predeploy(self.root, self.archive, '104.00.0')

    def test_failed_exit_code_fails(self):
        obj = self.make_state()
        obj['returncode'] = 1
        self.statefile.write_text(json.dumps(obj), encoding='utf-8')
        with self.assertRaises(UpdateError):
            require_v104_official_predeploy(self.root, self.archive, '104.00.0')

    def test_malformed_state_fails(self):
        self.statefile.write_text('{bad', encoding='utf-8')
        with self.assertRaises(UpdateError):
            require_v104_official_predeploy(self.root, self.archive, '104.00.0')

    def test_missing_zip_fails(self):
        self.make_state()
        self.archive.unlink()
        with self.assertRaises(UpdateError):
            require_v104_official_predeploy(self.root, self.archive, '104.00.0')


if __name__ == '__main__':
    unittest.main()
