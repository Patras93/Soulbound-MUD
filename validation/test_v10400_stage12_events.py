# -*- coding: utf-8 -*-
"""Bezpieczne offline testy etapu 12, bez TCP i baz produkcyjnych."""
from __future__ import annotations
import sqlite3
import tempfile
from pathlib import Path
import unittest

from core.sqlite_numeric_guard_v10400 import SQLiteNumericLimitV104
from storage.db_accounts import DatabaseAccountsMixin
from storage.big_number_events_v10400 import (
    apply_event_copy, verify_events_copy, EventConflictV104,
)
from storage.big_number_ledger_v10400 import get_exact_copy, StaleLegacyValueV104
from storage.big_number_shadow_v10400 import check_shadow


class DB(DatabaseAccountsMixin): pass


class Stage12V104Test(unittest.TestCase):
    def setUp(self):
        self.conn=sqlite3.connect(':memory:')
        self.conn.row_factory=sqlite3.Row
        self.conn.executescript('''
            CREATE TABLE characters(account_id INTEGER PRIMARY KEY,
                 character_xp INTEGER,soul_xp INTEGER,silver INTEGER,gold INTEGER,mithril INTEGER);
            CREATE TABLE class_progress(account_id INTEGER,class_name TEXT,xp INTEGER,
                 PRIMARY KEY(account_id,class_name));
            INSERT INTO characters VALUES(1,50,0,100,0,0);
            INSERT INTO class_progress VALUES(1,'Druid',400);
            INSERT INTO class_progress VALUES(1,'Mag',700);
        ''')
    def tearDown(self): self.conn.close()

    def test_exact_huge_replay(self):
        huge=10**100
        self.assertEqual(apply_event_copy(self.conn,1,'characters.character_xp',huge,'kill:500'),huge+50)
        self.assertEqual(apply_event_copy(self.conn,1,'characters.character_xp',huge,'kill:500'),huge+50)
        self.assertEqual(check_shadow(self.conn),1)
        self.assertEqual(verify_events_copy(self.conn),1)
        self.assertEqual(self.conn.execute('SELECT character_xp FROM characters').fetchone()[0],50)

    def test_replay_after_other_event_is_noop(self):
        apply_event_copy(self.conn,1,'characters.character_xp',100,'kill:1')
        apply_event_copy(self.conn,1,'characters.character_xp',300,'kill:2')
        self.assertEqual(apply_event_copy(self.conn,1,'characters.character_xp',100,'kill:1'),450)
        self.assertEqual(verify_events_copy(self.conn),2)

    def test_conflicting_event_rejected(self):
        apply_event_copy(self.conn,1,'characters.character_xp',100,'quest:7')
        with self.assertRaises(EventConflictV104):
            apply_event_copy(self.conn,1,'characters.character_xp',101,'quest:7')
        self.assertEqual(get_exact_copy(self.conn,1,'characters.character_xp'),150)

    def test_separate_class_keys(self):
        self.assertEqual(apply_event_copy(self.conn,1,'class_progress.xp',10**80,'boss:2',source_key='Druid'),400+10**80)
        self.assertEqual(apply_event_copy(self.conn,1,'class_progress.xp',10**70,'boss:2',source_key='Mag'),700+10**70)
        self.assertEqual(verify_events_copy(self.conn),2)

    def test_negative_delta_and_replay(self):
        self.assertEqual(apply_event_copy(self.conn,1,'characters.character_xp',-20,'expense:1'),30)
        self.assertEqual(apply_event_copy(self.conn,1,'characters.character_xp',-20,'expense:1'),30)
        with self.assertRaises(ValueError):
            apply_event_copy(self.conn,1,'characters.character_xp',-100,'expense:2')
        self.assertEqual(get_exact_copy(self.conn,1,'characters.character_xp'),30)
        self.assertEqual(verify_events_copy(self.conn),1)

    def test_stale_source_rejects_new_and_replay(self):
        apply_event_copy(self.conn,1,'characters.character_xp',900,'kill:3')
        self.conn.execute('UPDATE characters SET character_xp=51 WHERE account_id=1')
        with self.assertRaises(StaleLegacyValueV104):
            apply_event_copy(self.conn,1,'characters.character_xp',900,'kill:3')
        with self.assertRaises(StaleLegacyValueV104):
            apply_event_copy(self.conn,1,'characters.character_xp',200,'kill:4')
        self.assertEqual(verify_events_copy(self.conn),1)

    def test_trigger_failure_rolls_back_shadow_and_event(self):
        apply_event_copy(self.conn,1,'characters.character_xp',10,'kill:1')
        self.conn.execute('''CREATE TRIGGER forbid_event BEFORE INSERT ON big_number_events_v10400
               WHEN NEW.event_id='kill:2' BEGIN SELECT RAISE(ABORT,'fault'); END''')
        with self.assertRaises(sqlite3.IntegrityError):
            apply_event_copy(self.conn,1,'characters.character_xp',200,'kill:2')
        self.assertEqual(get_exact_copy(self.conn,1,'characters.character_xp'),60)
        self.assertEqual(verify_events_copy(self.conn),1)

    def test_outer_savepoint_rollback(self):
        self.conn.execute('SAVEPOINT outer_test')
        apply_event_copy(self.conn,1,'characters.character_xp',10**100,'kill:5')
        self.conn.execute('ROLLBACK TO outer_test')
        self.conn.execute('RELEASE outer_test')
        self.assertEqual(self.conn.execute('SELECT character_xp FROM characters').fetchone()[0],50)
        with self.assertRaises(sqlite3.OperationalError):
            self.conn.execute('SELECT * FROM big_number_events_v10400')

    def test_tamper_detected(self):
        apply_event_copy(self.conn,1,'characters.character_xp',10,'kill:1')
        self.conn.execute("UPDATE big_number_events_v10400 SET value_after_text='999'")
        with self.assertRaises(EventConflictV104):
            apply_event_copy(self.conn,1,'characters.character_xp',10,'kill:1')
        with self.assertRaises(ValueError): verify_events_copy(self.conn)

    def test_invalid_event_ids(self):
        for eid in ('', 'a b', '../escape', 'a'*121):
            with self.subTest(eid=eid), self.assertRaises(ValueError):
                apply_event_copy(self.conn,1,'characters.character_xp',5,eid)
        self.assertEqual(self.conn.execute("SELECT count(*) FROM sqlite_master WHERE name='big_number_events_v10400'").fetchone()[0],0)

    def test_reconnect_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'trial.db'
            out=sqlite3.connect(path)
            out.execute('CREATE TABLE characters(account_id INTEGER PRIMARY KEY,character_xp INTEGER)')
            out.execute('INSERT INTO characters VALUES(7,13)')
            apply_event_copy(out,7,'characters.character_xp',10**100,'first')
            out.commit();out.close()
            out=sqlite3.connect(path)
            self.assertEqual(apply_event_copy(out,7,'characters.character_xp',10**100,'first'),10**100+13)
            self.assertEqual(verify_events_copy(out),1)
            out.close()

    def test_python_exact_wallet_fallback(self):
        db=DB();db.conn=self.conn
        self.conn.executescript('''
             CREATE TABLE account_characters(character_account_id INTEGER, master_account_id INTEGER);
             CREATE TABLE account_wallet(master_account_id INTEGER PRIMARY KEY, silver INTEGER, gold INTEGER, mithril INTEGER,updated_at TEXT);
             INSERT INTO account_characters VALUES(1,1);
             INSERT INTO characters VALUES(2,0,0,50,0,0);
             INSERT INTO account_characters VALUES(2,1);
        ''')
        self.assertEqual(db.shared_wallet_for_master(1),(150,0,0))
        self.assertEqual(self.conn.execute('SELECT silver FROM account_wallet WHERE master_account_id=1').fetchone()[0],150)

    def test_float_or_text_wallet_never_truncated(self):
        db=DB();db.conn=self.conn
        self.conn.executescript('''
             CREATE TABLE account_wallet(master_account_id INTEGER PRIMARY KEY,
                 silver INTEGER,gold INTEGER,mithril INTEGER,updated_at TEXT);
             INSERT INTO account_wallet VALUES(1,1.5,0,0,NULL);
        ''')
        with self.assertRaises(TypeError): db.shared_wallet_for_master(1)
        self.assertEqual(self.conn.execute('SELECT silver FROM account_wallet').fetchone()[0],1.5)
        self.conn.execute("UPDATE account_wallet SET silver='nie-liczba'")
        with self.assertRaises(TypeError): db.shared_wallet_for_master(1)
        self.assertEqual(self.conn.execute('SELECT silver FROM account_wallet').fetchone()[0],'nie-liczba')

    def test_sum_overflow_does_not_create_wallet(self):
        db=DB();db.conn=self.conn
        self.conn.executescript('''
             CREATE TABLE account_characters(character_account_id INTEGER, master_account_id INTEGER);
             CREATE TABLE account_wallet(master_account_id INTEGER PRIMARY KEY, silver INTEGER,gold INTEGER,mithril INTEGER,updated_at TEXT);
             INSERT INTO account_characters VALUES(1,1);
             INSERT INTO characters VALUES(2,0,0,4611686018427387904,0,0);
             INSERT INTO account_characters VALUES(2,1);
             UPDATE characters SET silver=4611686018427387904 WHERE account_id=1;
        ''')
        with self.assertRaises(SQLiteNumericLimitV104): db.shared_wallet_for_master(1)
        self.assertEqual(self.conn.execute('SELECT count(*) FROM account_wallet').fetchone()[0],0)


def run():
    result=unittest.TextTestRunner(verbosity=0).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(Stage12V104Test))
    if not result.wasSuccessful(): raise AssertionError('V104 stage12 failed')
    return result.testsRun

if __name__=='__main__': print('V104 ETAP 12:',run(),'PASS',flush=True)
