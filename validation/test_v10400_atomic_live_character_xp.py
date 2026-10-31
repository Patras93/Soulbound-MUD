# -*- coding: utf-8 -*-
"""Stage 15: real EXP gateway, SQLite bank/character/wallet atomicity, no TCP."""
from __future__ import annotations
import sqlite3
import unittest
from types import MethodType, SimpleNamespace
from unittest.mock import patch
from storage.db_accounts import DatabaseAccountsMixin
from storage.db_experience_bank_v2011 import DatabaseExperienceBankV2011Mixin
from storage.database import _DeferredCommitConnection
from validation.test_v10400_stage11_atomic import new_char, NUMERIC, TEXT
from player.character import Character
from systems.atomic_character_experience_v10400 import award_character_xp_atomic_v10400


class DB(DatabaseAccountsMixin, DatabaseExperienceBankV2011Mixin):
    def multi_cap_v23215(self, account_id): return 100


def fixture():
    db=DB()
    base=sqlite3.connect(':memory:')
    base.row_factory=sqlite3.Row
    base.execute('PRAGMA foreign_keys=ON')
    db.conn=_DeferredCommitConnection(base)
    cols=(', '.join(['account_id INTEGER PRIMARY KEY'] +
         [f'{name} INTEGER NOT NULL DEFAULT 0' for name in NUMERIC] +
         [f'{name} TEXT NOT NULL DEFAULT ""' for name in TEXT]))
    db.conn.execute('CREATE TABLE characters ('+cols+')')
    db.conn.executescript('''
        CREATE TABLE accounts(id INTEGER PRIMARY KEY);
        INSERT INTO accounts VALUES(1);
        CREATE TABLE account_characters(character_account_id INTEGER, master_account_id INTEGER);
        INSERT INTO account_characters VALUES(1,1);
        CREATE TABLE account_wallet(master_account_id INTEGER PRIMARY KEY, silver INTEGER, gold INTEGER, mithril INTEGER, updated_at TEXT);
        INSERT INTO account_wallet(master_account_id,silver,gold,mithril) VALUES (1,100,0,0);
        INSERT INTO characters(account_id,character_level,character_xp,silver) VALUES (1,2,50,100);
    ''')
    db.create_experience_bank_schema_v2011()
    c=new_char()
    c.character_level=2
    c.character_xp=50
    c.add_character_xp=MethodType(Character.add_character_xp,c)
    return db,c


class LiveAwardTests(unittest.TestCase):
    def setUp(self):
        self.db,self.c=fixture()
        self.patcher=patch('player.character.character_xp_to_next',return_value=100)
        self.patcher.start()
    def tearDown(self):
        self.patcher.stop()
        self.db.conn.close()
    def bank(self):
        row=self.db.conn.execute("SELECT balance FROM experience_bank_v2011 WHERE account_id=1 AND kind='character'").fetchone()
        return int(row[0]) if row else 0
    def saved(self):
        row=self.db.conn.execute('SELECT character_level,character_xp,silver FROM characters WHERE account_id=1').fetchone()
        return tuple(row)
    def wallet(self):
        return self.db.conn.execute('SELECT silver FROM account_wallet WHERE master_account_id=1').fetchone()[0]

    def test_real_payout_save_and_multicap(self):
        paid,notes=award_character_xp_atomic_v10400(self.db,self.c,1,200)
        self.assertEqual(paid,100)
        self.assertEqual(self.bank(),100)
        self.assertEqual(self.saved(),(3,50,100))
        self.assertEqual(self.wallet(),100)
        self.assertTrue(notes)

    def test_no_loss_on_sqlite_trigger_failure(self):
        self.db.conn.execute("CREATE TRIGGER forbid_update BEFORE UPDATE OF character_xp ON characters BEGIN SELECT RAISE(ABORT,'write fail'); END")
        with self.assertRaises(sqlite3.IntegrityError):
            award_character_xp_atomic_v10400(self.db,self.c,1,200)
        self.assertEqual(self.saved(),(2,50,100))
        self.assertEqual((self.c.character_level,self.c.character_xp),(2,50))
        self.assertEqual(self.bank(),0)
        self.assertEqual(self.wallet(),100)

    def test_wallet_failure_rolls_back_bank(self):
        self.db.conn.execute("CREATE TRIGGER forbid_wallet BEFORE UPDATE ON account_wallet BEGIN SELECT RAISE(ABORT,'wallet fail'); END")
        with self.assertRaises(sqlite3.IntegrityError):
            award_character_xp_atomic_v10400(self.db,self.c,1,200)
        self.assertEqual(self.saved(),(2,50,100))
        self.assertEqual(self.bank(),0)
        self.assertEqual((self.c.character_level,self.c.character_xp),(2,50))

    def test_very_large_award_retains_shadow_balance(self):
        huge=10**100
        paid,_=award_character_xp_atomic_v10400(self.db,self.c,1,huge)
        self.assertEqual(paid,100)
        self.assertEqual(self.bank(),huge-100)
        self.assertEqual(self.saved(),(3,50,100))

    def test_zero_cap_banks_without_character_write(self):
        with patch('core.progression_resources.character_xp_to_next',return_value=0):
            paid,notes=award_character_xp_atomic_v10400(self.db,self.c,1,500)
        self.assertEqual((paid,notes),(0,[]))
        self.assertEqual(self.bank(),500)
        self.assertEqual(self.saved(),(2,50,100))

    def test_zero_cap_preserves_reward_if_save_triggers_invalid(self):
        self.db.conn.execute("CREATE TRIGGER forbid_update BEFORE UPDATE ON characters BEGIN SELECT RAISE(ABORT,'x'); END")
        with patch('core.progression_resources.character_xp_to_next',return_value=0):
            paid,_=award_character_xp_atomic_v10400(self.db,self.c,1,5)
        self.assertEqual(paid,0)
        self.assertEqual(self.bank(),5)

    def test_overflow_rolls_back_bank(self):
        self.c.strength=10**100
        with self.assertRaises(OverflowError):
            award_character_xp_atomic_v10400(self.db,self.c,1,200)
        self.assertEqual(self.bank(),0)
        self.assertEqual(self.saved(),(2,50,100))
        self.assertEqual((self.c.character_level,self.c.character_xp),(2,50))

    def test_recovery_after_failed_save(self):
        self.db.conn.execute("CREATE TRIGGER forbid_update BEFORE UPDATE ON characters BEGIN SELECT RAISE(ABORT,'x'); END")
        with self.assertRaises(sqlite3.IntegrityError):
            award_character_xp_atomic_v10400(self.db,self.c,1,200)
        self.db.conn.execute('DROP TRIGGER forbid_update')
        paid,_=award_character_xp_atomic_v10400(self.db,self.c,1,200)
        self.assertEqual((paid,self.bank()),(100,100))

    def test_invalid_identity(self):
        with self.assertRaises(ValueError):award_character_xp_atomic_v10400(self.db,self.c,2,100)
        self.assertEqual(self.bank(),0)

    def test_live_session_gateway_calls_atomic_api(self):
        from player.session_mixins.session_runtime_state import SessionRuntimeStateMixin
        recorded=[]
        fake=SimpleNamespace(
            server=SimpleNamespace(db=self.db), account_id=1, character=self.c,
            scale_progression_xp_v11342=lambda v,level,content_scaled=False:v,
            apply_double_xp=lambda x:x,
            session_summary_add=lambda key,val: recorded.append((key,val)),
        )
        notes=SessionRuntimeStateMixin.add_character_xp_with_event(fake,200)
        self.assertEqual(self.saved(),(3,50,100))
        self.assertEqual(self.bank(),100)
        self.assertEqual(recorded,[('character_xp',100)])
        self.assertTrue(notes)


def run():
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(LiveAwardTests)
    result=unittest.TextTestRunner(verbosity=0).run(suite)
    if not result.wasSuccessful():raise AssertionError('V104 active EXP atomic FAIL')
    return result.testsRun
if __name__=='__main__':print('LIVE EXP ATOMIC:',run(),'PASS')
