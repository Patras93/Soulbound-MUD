# -*- coding: utf-8 -*-
"""Isolated offline tests of atomic TEXT ledger. No production database."""
from __future__ import annotations
import sqlite3
import unittest
from storage.big_number_ledger_v10400 import (
    MissingLedgerRowV104, StaleLegacyValueV104,
    add_exact_copy, get_exact_copy,
)
from storage.big_number_shadow_v10400 import check_shadow


class LedgerV104Test(unittest.TestCase):
    def setUp(self):
        self.db=sqlite3.connect(':memory:')
        self.db.executescript('''
            CREATE TABLE characters(account_id INTEGER PRIMARY KEY,character_xp INTEGER,
                soul_xp INTEGER,silver INTEGER,gold INTEGER,mithril INTEGER);
            CREATE TABLE class_progress(account_id INTEGER,class_name TEXT,xp INTEGER,
                PRIMARY KEY(account_id,class_name));
            INSERT INTO characters VALUES(1,42,55,100,0,0);
            INSERT INTO class_progress VALUES(1,'Druid',400);
            INSERT INTO class_progress VALUES(1,'Mag',700);
        ''')
    def tearDown(self): self.db.close()
    def test_enormous_text_roundtrip(self):
        huge=10**100
        out=add_exact_copy(self.db,1,'characters.character_xp',huge)
        self.assertEqual(out,huge+42)
        self.assertEqual(get_exact_copy(self.db,1,'characters.character_xp'),out)
        self.assertEqual(self.db.execute('SELECT character_xp FROM characters').fetchone()[0],42)
        self.assertEqual(check_shadow(self.db),1)
    def test_separate_class_keys(self):
        add_exact_copy(self.db,1,'class_progress.xp',10**80,source_key='Druid')
        add_exact_copy(self.db,1,'class_progress.xp',10**70,source_key='Mag')
        self.assertEqual(get_exact_copy(self.db,1,'class_progress.xp',source_key='Druid'),10**80+400)
        self.assertEqual(get_exact_copy(self.db,1,'class_progress.xp',source_key='Mag'),10**70+700)
        self.assertEqual(check_shadow(self.db),2)
    def test_atomic_fail_no_partial_delta(self):
        add_exact_copy(self.db,1,'characters.soul_xp',100)
        with self.assertRaises(ValueError):add_exact_copy(self.db,1,'characters.soul_xp',-1000)
        self.assertEqual(get_exact_copy(self.db,1,'characters.soul_xp'),155)
    def test_refuses_stale_legacy_source(self):
        add_exact_copy(self.db,1,'characters.character_xp',10**40)
        self.db.execute('UPDATE characters SET character_xp=43 WHERE account_id=1')
        with self.assertRaises(StaleLegacyValueV104):add_exact_copy(self.db,1,'characters.character_xp',500)
        with self.assertRaises(StaleLegacyValueV104):get_exact_copy(self.db,1,'characters.character_xp')
        self.assertEqual(check_shadow(self.db),1)
    def test_rollback_in_parent_transaction(self):
        self.db.execute('SAVEPOINT parent_test')
        add_exact_copy(self.db,1,'characters.character_xp',10**45)
        self.db.execute('ROLLBACK TO parent_test')
        self.db.execute('RELEASE parent_test')
        self.assertEqual(self.db.execute('SELECT character_xp FROM characters').fetchone()[0],42)
        with self.assertRaises(sqlite3.OperationalError):
            self.db.execute('SELECT * FROM big_number_shadow_v10400')
    def test_missing_account_does_not_create_one(self):
        with self.assertRaises(MissingLedgerRowV104):
            add_exact_copy(self.db,777,'characters.character_xp',100)
        self.assertEqual(self.db.execute('SELECT count(*) FROM characters').fetchone()[0],1)
    def test_tampered_checksum_fails_and_does_not_overwrite(self):
        add_exact_copy(self.db,1,'characters.character_xp',300)
        self.db.execute('UPDATE big_number_shadow_v10400 SET balance_text=? WHERE axis=?',
                        ('9999','characters.character_xp'))
        with self.assertRaises(ValueError):add_exact_copy(self.db,1,'characters.character_xp',2)
        self.assertEqual(self.db.execute('SELECT balance_text FROM big_number_shadow_v10400').fetchone()[0],'9999')
    def test_disallow_float_input(self):
        with self.assertRaises(ValueError):add_exact_copy(self.db,1,'characters.character_xp',1.5)


def run():
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(LedgerV104Test)
    result=unittest.TextTestRunner(verbosity=0).run(suite)
    if not result.wasSuccessful():raise AssertionError('Ledger v104 tests FAIL')
    return result.testsRun

if __name__=='__main__':print('LEDGER',run(),'PASS',flush=True)
