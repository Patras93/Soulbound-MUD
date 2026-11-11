# -*- coding: utf-8 -*-
"""Safe tests for direct FAST PREDEPLOY execution. No live server import."""
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from validation.v10400_fast_predeploy_isolation import (
    isolated_predeploy_env, enable_isolated_fast_predeploy)

class FastPredeployIsolation(unittest.TestCase):
    def test_private_port_database_and_secrets(self):
        with tempfile.TemporaryDirectory(prefix='sb104_tcp_lab_') as folder:
            env = isolated_predeploy_env({
                'PORT':'4000', 'SOULBOUND_PORT':'4000',
                'SOULBOUND_HOST':'0.0.0.0', 'SOULBOUND_DB':'C:/Soulbound-MUD/soulbound.db',
                'RAILWAY_TCP_APPLICATION_PORT':'4000', 'RAILWAY_SECRET_TOKEN':'secret',
                'SOULBOUND_ADMIN_ACCOUNTS':'secret', 'PATH':'test_path'}, folder, 54033)
            self.assertEqual(env['SOULBOUND_HOST'],'127.0.0.1')
            self.assertEqual(env['SOULBOUND_PORT'],'54033')
            self.assertEqual(env['PORT'],'54033')
            self.assertTrue(Path(env['SOULBOUND_DB']).is_relative_to(folder))
            self.assertNotIn('RAILWAY_TCP_APPLICATION_PORT',env)
            self.assertNotIn('RAILWAY_SECRET_TOKEN',env)
            self.assertNotIn('SOULBOUND_ADMIN_ACCOUNTS',env)
            self.assertEqual(env['PATH'],'test_path')
    def test_reject_prod_port(self):
        with tempfile.TemporaryDirectory(prefix='sb104_tcp_lab_') as folder:
            with self.assertRaises(ValueError): isolated_predeploy_env({},folder,4000)
    def test_direct_install_sets_isolated_environment(self):
        with patch.dict(os.environ, {
                'SOULBOUND_DB':'C:/Soulbound-MUD/soulbound.db',
                'PORT':'4000', 'RAILWAY_TCP_APPLICATION_PORT':'4000',
                'RAILWAY_SECRET_TOKEN':'topsecret'},clear=False):
            before=dict(os.environ)
            try:
                lab,port=enable_isolated_fast_predeploy()
                self.assertNotEqual(port,4000)
                self.assertEqual(os.environ['SOULBOUND_HOST'],'127.0.0.1')
                self.assertEqual(os.environ['SOULBOUND_PORT'],str(port))
                self.assertTrue(Path(os.environ['SOULBOUND_DB']).is_relative_to(lab.name))
                self.assertNotIn('RAILWAY_SECRET_TOKEN',os.environ)
            finally:
                os.environ.clear()
                os.environ.update(before)
                if 'lab' in locals():lab.cleanup()
    def test_full_gate_clears_environment_before_server_import(self):
        source=Path(__file__).resolve().parents[1].joinpath('predeploy_full.py').read_text(encoding='utf-8')
        self.assertLess(source.index('os.environ.update(_safe)'),source.index('import server'))
        self.assertIn('isolated_predeploy_env',source)
        self.assertNotIn('os.environ["SOULBOUND_PORT"]',source)
    def test_gate_before_storage_import(self):
        src=Path(__file__).resolve().parents[1].joinpath('predeploy_check.py').read_text(encoding='utf-8')
        self.assertLess(src.index('enable_isolated_fast_predeploy()'),
                        src.index('from storage.database import Database'))

if __name__=='__main__': unittest.main()
