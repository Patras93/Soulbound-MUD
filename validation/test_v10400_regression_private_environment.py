# -*- coding: utf-8 -*-
"""Prevent all v104 offline test runners from reaching production resources."""
from __future__ import annotations
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from validation.v10400_suite_isolated import safe_env
from validation import v10400_release_gate


class OfflineIsolation(unittest.TestCase):
    def test_regression_never_falls_back_to_production_paths(self):
        with tempfile.TemporaryDirectory(prefix='sb104_tcp_lab_') as tmp:
            with patch.dict(os.environ, {
                'SOULBOUND_DB': r'C:\Soulbound-MUD\soulbound.db',
                'SOULBOUND_WORLD_SEED_FILE': r'C:\Soulbound-MUD\soulbound_world_seed.txt',
                'PORT': '4000', 'SOULBOUND_PORT': '4000',
                'RAILWAY_VOLUME_MOUNT_PATH': r'C:\Soulbound-MUD',
                'DATABASE_URL': 'sqlite:///private',
                'DB_PATH': r'C:\\Soulbound-MUD\\other.sqlite',
                'DATABASE_PATH': r'C:\\Soulbound-MUD\\data.sqlite',
                'HOST': '0.0.0.0', 'PYTHONPATH': r'C:\\Soulbound-MUD',
            }):
                env = safe_env(Path(tmp))
            self.assertEqual(env['SOULBOUND_HOST'], '127.0.0.1')
            self.assertNotEqual(env['PORT'], '4000')
            self.assertEqual(env['SOULBOUND_DB'], str(Path(tmp) / 'tcp_test.sqlite'))
            self.assertEqual(env['SOULBOUND_WORLD_SEED_FILE'], str(Path(tmp) / 'world_seed.txt'))
            self.assertEqual(env['SOULBOUND_LOG_DIR'], str(Path(tmp) / 'logs'))
            self.assertNotIn('DATABASE_URL', env)
            self.assertNotIn('RAILWAY_VOLUME_MOUNT_PATH', env)
            for name in ('DB_PATH', 'DATABASE_PATH', 'HOST', 'PYTHONPATH'):
                self.assertNotIn(name, env)
            self.assertFalse(Path(env['SOULBOUND_DB']).exists())

    def test_misnamed_folder_cannot_be_used_as_private_lab(self):
        with tempfile.TemporaryDirectory(prefix='unsafe_') as tmp:
            with self.assertRaises(ValueError):
                safe_env(Path(tmp))

    def test_unit_gate_preserves_source_seed_and_database(self):
        # The real release gate invokes the same isolation policy in a
        # temporary folder, independent of CWD or inherited env variables.
        from unittest.mock import MagicMock
        observed = []
        with patch('subprocess.run') as subprocess_run:
            subprocess_run.return_value = MagicMock(returncode=0, stdout='OK')
            with patch.dict(os.environ, {
                'SOULBOUND_DB': r'C:\Soulbound-MUD\soulbound.db',
                'PORT': '4000',
            }):
                v10400_release_gate.run_tests(timeout=10)
            observed.append(subprocess_run.call_args.kwargs['env'])
        env = observed[0]
        self.assertEqual(env['SOULBOUND_HOST'], '127.0.0.1')
        self.assertNotEqual(env['PORT'], '4000')
        self.assertNotEqual(env['SOULBOUND_DB'], r'C:\Soulbound-MUD\soulbound.db')
        self.assertIn('sb104_tcp_lab_', env['SOULBOUND_DB'])


if __name__ == '__main__':
    unittest.main()
