# -*- coding: utf-8 -*-
import sqlite3
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from storage.big_number_copy_runtime_v10400 import (
    read_exact_progression_copy, write_exact_progression_copy, make_offline_copy_for_rehearsal,
)
from storage.big_number_shadow_v10400 import check_shadow

class ExactCopyRuntime(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='sb104_copy_only_')
        self.folder = Path(self.temp.name)
        (self.folder / '.SOULBOUND_V104_WYLACZNIE_KOPIA_TESTOWA').write_text('TYLKO TEST',encoding='utf-8')
        self.path = self.folder / 'SB104_OFFLINE_TEST.sqlite'
        self.conn = sqlite3.connect(self.path)
        self.conn.execute('CREATE TABLE characters(account_id INTEGER PRIMARY KEY,character_xp INTEGER NOT NULL,soul_xp INTEGER NOT NULL)')
        self.conn.execute('INSERT INTO characters VALUES (1,1234,5678)')
        self.conn.commit()
        self.db=SimpleNamespace(path=str(self.path), conn=self.conn)
    def tearDown(self):
        self.conn.close(); self.temp.cleanup()
    def test_roundtrip_above_int64_after_reopen(self):
        big=10**250
        write_exact_progression_copy(self.db,1,character_xp=big,soul_xp=big+44)
        self.conn.commit()
        self.assertEqual(check_shadow(self.conn),2)
        self.assertEqual(self.conn.execute('SELECT typeof(character_xp),typeof(soul_xp) FROM characters').fetchone(),('integer','integer'))
        self.conn.close()
        self.conn=sqlite3.connect(self.path)
        self.db.conn=self.conn
        self.assertEqual(read_exact_progression_copy(self.db,1,'character_xp'),big)
        self.assertEqual(read_exact_progression_copy(self.db,1,'soul_xp'),big+44)
        write_exact_progression_copy(self.db,1,character_xp=big+55)
        self.assertEqual(read_exact_progression_copy(self.db,1,'character_xp'),big+55)
    def test_reject_non_disposable_database(self):
        (self.folder / '.SOULBOUND_V104_WYLACZNIE_KOPIA_TESTOWA').unlink()
        with self.assertRaises(PermissionError):
            write_exact_progression_copy(self.db,1,character_xp=10**100)
        self.assertEqual(self.conn.execute('SELECT character_xp FROM characters').fetchone()[0],1234)
    def test_reject_stale_legacy_without_writing(self):
        write_exact_progression_copy(self.db,1,character_xp=10**60)
        self.conn.execute('UPDATE characters SET character_xp=77 WHERE account_id=1')
        with self.assertRaisesRegex(ValueError,'poza migracją'):
            write_exact_progression_copy(self.db,1,character_xp=10**70)
        self.assertEqual(self.conn.execute('SELECT character_xp FROM characters').fetchone()[0],77)
    def test_two_axis_rollback_on_trigger_failure(self):
        self.conn.execute("CREATE TRIGGER no_soul BEFORE UPDATE OF soul_xp ON characters BEGIN SELECT RAISE(ABORT,'fail'); END")
        with self.assertRaises(sqlite3.IntegrityError):
            write_exact_progression_copy(self.db,1,character_xp=10**100,soul_xp=10**100)
        self.assertEqual(self.conn.execute('SELECT character_xp,soul_xp FROM characters').fetchone(),(1234,5678))
        self.assertEqual(self.conn.execute("SELECT count(*) FROM sqlite_master WHERE type='table' AND name='big_number_shadow_v10400'").fetchone()[0],0)
    def test_tampering_detected(self):
        write_exact_progression_copy(self.db,1,soul_xp=10**80)
        self.conn.execute("UPDATE big_number_shadow_v10400 SET balance_text='999' WHERE axis='characters.soul_xp'")
        with self.assertRaisesRegex(ValueError,'checksum'):
            read_exact_progression_copy(self.db,1,'soul_xp')
    def test_offline_backup_preserves_source(self):
        self.conn.commit()
        import hashlib
        before = hashlib.sha256(self.path.read_bytes()).hexdigest()
        with tempfile.TemporaryDirectory(prefix='sb104_dest_') as d:
            copy = make_offline_copy_for_rehearsal(self.path, d)
            self.assertNotEqual(copy,self.path)
            with sqlite3.connect(copy) as replica:
                replica_db=SimpleNamespace(path=str(copy),conn=replica)
                write_exact_progression_copy(replica_db,1,character_xp=10**180)
                replica.commit()
                self.assertEqual(read_exact_progression_copy(replica_db,1,'character_xp'),10**180)
            self.assertEqual(self.conn.execute('SELECT character_xp FROM characters').fetchone()[0],1234)
            self.assertEqual(hashlib.sha256(self.path.read_bytes()).hexdigest(),before)
            with self.assertRaises(FileExistsError):
                make_offline_copy_for_rehearsal(self.path,d)
    def test_boundary_and_rejection(self):
        with self.assertRaises((ValueError,TypeError)):
            write_exact_progression_copy(self.db,1,character_xp=1.5)
        with self.assertRaises(ValueError):
            write_exact_progression_copy(self.db,1,character_xp=-10)
        with self.assertRaises(ValueError):
            read_exact_progression_copy(self.db,1,'silver')

def run():
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(ExactCopyRuntime)
    result=unittest.TextTestRunner(verbosity=1).run(suite)
    if not result.wasSuccessful():raise AssertionError('BigNumber copy runtime FAILED')
    return result.testsRun

if __name__=='__main__': print('BigNumber isolated copy:',run(),'PASS')
