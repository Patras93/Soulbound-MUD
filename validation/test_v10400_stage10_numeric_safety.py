# -*- coding: utf-8 -*-
"""v104 stage 10 offline safety regression. Never opens a production DB."""
from __future__ import annotations

from contextlib import closing
from types import SimpleNamespace
import sqlite3
import unittest

from core.big_numbers_v10400 import SQLITE_INT64_MAX, SQLITE_INT64_MIN
from core.sqlite_numeric_guard_v10400 import (
    SQLiteNumericLimitV104, preflight_character_v104, require_sqlite_int64,
)
from core.bootstrap_economy_professions import (
    normalize_currency_values, legacy_currency_to_coins,
    CURRENCY_SQLITE_SAFE_TOTAL,
)
from storage.db_accounts import DatabaseAccountsMixin


class _NoSqlConnection:
    def __init__(self): self.count=0
    def execute(self, *_args, **_kwargs):
        self.count += 1
        raise AssertionError('Nie wolno wykonywac SQL przed walidacja liczb.')
    def commit(self):
        self.count += 1
        raise AssertionError('Commit przed walidacja.')


class _NoWriteDB(DatabaseAccountsMixin):
    def __init__(self):
        self.conn=_NoSqlConnection()
        self.wallet_calls=0
    def set_shared_wallet_for_character(self, *_args, **_kwargs):
        self.wallet_calls+=1
        raise AssertionError('Portfel zapisany przed walidacja.')


def sample_character():
    numeric=('account_id strength dexterity constitution intelligence willpower charisma '
             'stat_progress strength_progress dexterity_progress constitution_progress '
             'intelligence_progress willpower_progress charisma_progress soul_level '
             'soul_xp soul_tier soul_weapon_mastery_level soul_weapon_mastery_xp '
             'silver gold mithril character_level character_xp deaths').split()
    data={axis:1 for axis in numeric}
    data.update(account_id=1,soul_xp=0,character_xp=50,silver=100,gold=0,mithril=0)
    return SimpleNamespace(**data)


class NumericSafetyV104Test(unittest.TestCase):
    def test_int64_exact_limits(self):
        for n in (SQLITE_INT64_MIN, -1, 0, 1, SQLITE_INT64_MAX):
            self.assertEqual(require_sqlite_int64('test',n),n)
        for n in (SQLITE_INT64_MIN-1, SQLITE_INT64_MAX+1, 10**100):
            with self.assertRaises(SQLiteNumericLimitV104): require_sqlite_int64('test',n)
        for n in (float(1),True,'99',None):
            with self.assertRaises(TypeError): require_sqlite_int64('test',n)

    def test_currency_no_silent_loss(self):
        self.assertEqual(normalize_currency_values(100,2,3),
                         (legacy_currency_to_coins(100,2,3),0,0))
        self.assertEqual(normalize_currency_values(CURRENCY_SQLITE_SAFE_TOTAL,0,0),
                         (CURRENCY_SQLITE_SAFE_TOTAL,0,0))
        for silver,gold,mithril in ((CURRENCY_SQLITE_SAFE_TOTAL+1,0,0),
                                    (0,0,CURRENCY_SQLITE_SAFE_TOTAL),
                                    (10**100,0,0)):
            with self.subTest(silver=silver,gold=gold,mithril=mithril):
                with self.assertRaises(SQLiteNumericLimitV104):
                    normalize_currency_values(silver,gold,mithril)

    def test_sqlite_original_wallet_remains_unchanged_after_overflow(self):
        with closing(sqlite3.connect(':memory:')) as db:
            db.execute('CREATE TABLE wallet(balance INTEGER NOT NULL)')
            db.execute('INSERT INTO wallet VALUES (100)')
            db.commit()
            before=db.execute('SELECT balance FROM wallet').fetchone()[0]
            with self.assertRaises(SQLiteNumericLimitV104):
                value,_,_=normalize_currency_values(10**100,0,0)
                db.execute('UPDATE wallet SET balance=?',(value,))
            self.assertEqual(db.execute('SELECT balance FROM wallet').fetchone()[0],before)

    def test_real_sqlite_character_wallet_write_and_overflow_rollback(self):
        # Exercise the actual DatabaseAccountsMixin methods against a tiny,
        # disposable SQLite schema (not a mocked execute counter).
        numeric=('strength dexterity constitution intelligence willpower '
                 'stat_progress strength_progress dexterity_progress '
                 'constitution_progress intelligence_progress willpower_progress '
                 'charisma_progress soul_level soul_xp soul_tier '
                 'soul_weapon_mastery_level soul_weapon_mastery_xp '
                 'silver gold mithril charisma character_level character_xp deaths').split()
        txt=('room_id guild_reputation_json guild_exams_json '
             'guild_class_quests_json guild_bounty_json loot_filter active_title').split()
        class Trial(DatabaseAccountsMixin): pass
        db=Trial()
        db.conn=sqlite3.connect(':memory:')
        db.conn.row_factory=sqlite3.Row
        try:
            fields=', '.join(['account_id INTEGER PRIMARY KEY'] +
                             [name+' INTEGER NOT NULL DEFAULT 0' for name in numeric] +
                             [name+" TEXT NOT NULL DEFAULT ''" for name in txt])
            db.conn.execute('CREATE TABLE characters ('+fields+')')
            db.conn.execute('CREATE TABLE account_characters ('
                            'character_account_id INTEGER, master_account_id INTEGER)')
            db.conn.execute('CREATE TABLE account_wallet ('
                            'master_account_id INTEGER PRIMARY KEY, silver INTEGER, '
                            'gold INTEGER, mithril INTEGER, updated_at TEXT)')
            db.conn.execute('INSERT INTO characters(account_id,character_xp,silver) VALUES(1,50,100)')
            db.conn.execute('INSERT INTO account_characters VALUES(1,1)')
            c=sample_character()
            c.__dict__.update({name:'' for name in txt})
            c.room_id='square'
            db.save_character(c)
            saved=db.conn.execute('SELECT character_xp,silver FROM characters WHERE account_id=1').fetchone()
            self.assertEqual(tuple(saved),(50,100))
            self.assertEqual(db.conn.execute('SELECT silver FROM account_wallet').fetchone()[0],100)
            c.character_xp=10**100
            c.silver=200
            with self.assertRaises(SQLiteNumericLimitV104):db.save_character(c)
            self.assertEqual(tuple(db.conn.execute('SELECT character_xp,silver FROM characters').fetchone()),(50,100))
            self.assertEqual(db.conn.execute('SELECT silver FROM account_wallet').fetchone()[0],100)
            c.character_xp=50
            c.silver=CURRENCY_SQLITE_SAFE_TOTAL+1
            with self.assertRaises(SQLiteNumericLimitV104):db.save_character(c)
            self.assertEqual(db.conn.execute('SELECT silver FROM account_wallet').fetchone()[0],100)
        finally:
            db.conn.close()

    def test_character_preflight_all_persistent_fields(self):
        c=sample_character()
        preflight_character_v104(c)
        for axis in vars(c):
            with self.subTest(axis=axis):
                setattr(c,axis,SQLITE_INT64_MAX+1)
                with self.assertRaises(SQLiteNumericLimitV104):
                    preflight_character_v104(c)
                setattr(c,axis,1)

    def test_no_wallet_or_sql_on_unrepresentable_character(self):
        db=_NoWriteDB()
        for axis in ('character_xp','soul_xp','character_level','soul_level',
                     'strength','soul_weapon_mastery_xp','silver'):
            with self.subTest(axis=axis):
                c=sample_character()
                setattr(c,axis,10**100)
                with self.assertRaises(SQLiteNumericLimitV104):
                    db.save_character(c)
                self.assertEqual(db.conn.count,0)
                self.assertEqual(db.wallet_calls,0)


def run():
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(NumericSafetyV104Test)
    result=unittest.TextTestRunner(verbosity=0).run(suite)
    if not result.wasSuccessful(): raise AssertionError('V104 stage 10 tests FAIL')
    return result.testsRun


if __name__=='__main__':
    print('V104 STAGE 10:',run(),'PASS',flush=True)
