# -*- coding: utf-8 -*-
"""Direct SQLite write tests for v104 legacy numeric guard."""
from __future__ import annotations
import sqlite3
import tempfile
import unittest
from pathlib import Path
from storage.sqlite_numeric_integrity_v10400 import install_numeric_write_barriers


class NumericWriteBarrierTests(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(':memory:')
        self.conn.executescript('''
            CREATE TABLE characters(account_id INTEGER PRIMARY KEY,
                character_xp INTEGER, soul_xp INTEGER, silver INTEGER);
            INSERT INTO characters VALUES(1,100,50,200);
            CREATE TABLE class_progress(account_id INTEGER,class_name TEXT,
                xp INTEGER,level INTEGER,PRIMARY KEY(account_id,class_name));
            INSERT INTO class_progress VALUES(1,'Rycerz',42,1);
            CREATE TABLE professions(account_id INTEGER,profession TEXT,xp INTEGER,level INTEGER,actions INTEGER);
            CREATE TABLE tools(account_id INTEGER,tool_type TEXT,xp INTEGER,level INTEGER,uses INTEGER);
            CREATE TABLE bank_balances(account_id INTEGER PRIMARY KEY,silver INTEGER,gold INTEGER,mithril INTEGER);
            INSERT INTO bank_balances VALUES(1,20,0,0);
            CREATE TABLE account_wallet(master_account_id INTEGER PRIMARY KEY,silver INTEGER,gold INTEGER,mithril INTEGER);
            INSERT INTO account_wallet VALUES(1,200,0,0);
        ''')
        install_numeric_write_barriers(self.conn)

    def tearDown(self): self.conn.close()

    def test_direct_update_float_rejected(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute('UPDATE characters SET character_xp=12.5 WHERE account_id=1')
        self.assertEqual(self.conn.execute('SELECT character_xp FROM characters').fetchone()[0],100)

    def test_direct_insert_float_rejected(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute('INSERT INTO characters(account_id,character_xp) VALUES(2,7.25)')
        self.assertIsNone(self.conn.execute('SELECT 1 FROM characters WHERE account_id=2').fetchone())

    def test_numeric_text_and_non_numeric_text_rejected(self):
        for value in ('10' * 30, 'not-a-number'):
            with self.subTest(value=value):
                with self.assertRaises(sqlite3.IntegrityError):
                    self.conn.execute('UPDATE class_progress SET xp=? WHERE account_id=1', (value,))
        self.assertEqual(self.conn.execute('SELECT xp FROM class_progress').fetchone()[0],42)

    def test_every_table_has_both_barriers(self):
        from storage.sqlite_numeric_integrity_v10400 import NUMERIC_FIELDS
        rows = {r[0] for r in self.conn.execute("SELECT name FROM sqlite_master WHERE type='trigger'")}
        for table in NUMERIC_FIELDS:
            for action in ('insert','update'):
                self.assertIn(f'sb104_int_guard_{table}_{action}',rows)

    def test_in_range_legacy_upsert_still_works(self):
        self.conn.execute('INSERT INTO account_wallet VALUES(1,250,0,0) '
                          'ON CONFLICT(master_account_id) DO UPDATE SET silver=excluded.silver')
        self.assertEqual(self.conn.execute('SELECT silver FROM account_wallet').fetchone()[0],250)

    def test_bank_real_rejected(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute('UPDATE bank_balances SET gold=0.5 WHERE account_id=1')
        self.assertEqual(self.conn.execute('SELECT gold FROM bank_balances').fetchone()[0],0)

    def test_inner_savepoint_rollback_stays_valid(self):
        self.conn.execute('SAVEPOINT sb104_outer')
        self.conn.execute('UPDATE characters SET character_xp=101 WHERE account_id=1')
        with self.assertRaises(sqlite3.IntegrityError):
            self.conn.execute('UPDATE characters SET soul_xp=1.25 WHERE account_id=1')
        self.conn.execute('ROLLBACK TO SAVEPOINT sb104_outer')
        self.conn.execute('RELEASE SAVEPOINT sb104_outer')
        self.assertEqual(self.conn.execute('SELECT character_xp FROM characters').fetchone()[0],100)

    def test_idempotent_install(self):
        before = self.conn.execute("SELECT count(*) FROM sqlite_master WHERE type='trigger'").fetchone()[0]
        self.assertEqual(install_numeric_write_barriers(self.conn),12)
        after = self.conn.execute("SELECT count(*) FROM sqlite_master WHERE type='trigger'").fetchone()[0]
        self.assertEqual(before,after)

    def test_missing_tables_graceful(self):
        c=sqlite3.connect(':memory:')
        try:self.assertEqual(install_numeric_write_barriers(c),0)
        finally:c.close()

    def test_real_database_boot_installs_barriers(self):
        from storage.database import Database
        with tempfile.TemporaryDirectory(prefix='sb104_real_db_') as temp:
            db=Database(str(Path(temp)/'test.sqlite'))
            try:
                names={row[0] for row in db.conn.execute("SELECT name FROM sqlite_master WHERE type='trigger'")}
                self.assertIn('sb104_int_guard_characters_update',names)
                self.assertIn('sb104_int_guard_class_progress_insert',names)
                self.assertEqual(db.conn.execute('PRAGMA integrity_check').fetchone()[0],'ok')
            finally:db.conn.close()


def run():
    result=unittest.TextTestRunner(verbosity=1).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(NumericWriteBarrierTests))
    if not result.wasSuccessful():raise AssertionError('v104 numeric write barriers failed')
    return result.testsRun

if __name__=='__main__':print('V104 NUMERIC BARRIERS:',run(),'PASS')
