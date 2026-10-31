# -*- coding: utf-8 -*-
"""Bez sieci: odcięcie produkcyjnych zmiennych i kontrola paczek."""
from __future__ import annotations
import tempfile
from pathlib import Path
import unittest
from validation.v10400_release_isolation_guard import (
    private_tcp_environment, forbidden_release_paths, DROP_ENV)

class ReleaseIsolation(unittest.TestCase):
    def test_all_sensitive_settings_removed(self):
        with tempfile.TemporaryDirectory(prefix='sb104_tcp_lab_') as td:
            source={k:'PRODUCTION_SECRET' for k in DROP_ENV}
            source.update(RAILWAY_SECRET_TOKEN='SECRET', SOULBOUND_SECRET_TEST='SECRET',
                          SOULBOUND_TOKEN_TEST='SECRET', PATH='/usr/bin')
            env=private_tcp_environment(source,td,54321)
            for field in DROP_ENV - {'PORT','SOULBOUND_PORT','SOULBOUND_HOST','SOULBOUND_DB',
                                     'SOULBOUND_WORLD_SEED_FILE','SOULBOUND_LOG_DIR'}:
                self.assertNotIn(field,env)
            for key,val in env.items():
                self.assertNotEqual(val,'PRODUCTION_SECRET',key)
                self.assertNotEqual(val,'SECRET',key)
            self.assertEqual(env['SOULBOUND_HOST'],'127.0.0.1')
            self.assertEqual(env['SOULBOUND_PORT'],'54321')
            self.assertTrue(Path(env['SOULBOUND_DB']).is_relative_to(td))
            self.assertEqual(env['PATH'],'/usr/bin')
    def test_reject_port_4000_and_invalid_test_location(self):
        with tempfile.TemporaryDirectory(prefix='sb104_tcp_lab_') as td:
            with self.assertRaises(ValueError):private_tcp_environment({},td,4000)
            with self.assertRaises(ValueError):private_tcp_environment({},td,True)
            with self.assertRaises(ValueError):private_tcp_environment({},td,65536)
            with self.assertRaises(ValueError):private_tcp_environment({},Path(td).parent,54321)
    def test_detect_sqlite_and_cache_in_any_folder(self):
        bad=['soulbound.db','world/soulbound.db-wal','soulbound.db-shm',
             'data/private.sqlite3','data/private.sqlite-journal',
             'validation/__pycache__/x.pyc','.env','config/credentials.json',
             'a/../../escape.py','secrets/private.key','logs/server.log']
        self.assertEqual(set(forbidden_release_paths(bad)),set(bad))
    def test_keep_legitimate_game_data(self):
        good=['world/quests.py','data/items.py','LIVE_CONTENT/sample.json',
              'validation/test_v10400_stage14_live_expbank.py', 'CHANGELOG_PL.txt']
        self.assertFalse(forbidden_release_paths(good))

def run():
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(ReleaseIsolation)
    result=unittest.TextTestRunner(verbosity=1).run(suite)
    if not result.wasSuccessful():raise AssertionError('RELEASE ISOLATION FAIL')
    return result.testsRun

if __name__=='__main__':print('V104 RELEASE ISOLATION:',run(),'PASS')
