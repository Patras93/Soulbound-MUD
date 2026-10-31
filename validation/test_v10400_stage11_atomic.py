# -*- coding: utf-8 -*-
"""v104 stage 11: transactional safety of real save methods on disposable sqlite."""
from __future__ import annotations
import sqlite3
import unittest
from types import SimpleNamespace
from storage.db_accounts import DatabaseAccountsMixin
from core.sqlite_numeric_guard_v10400 import SQLiteNumericLimitV104

NUMERIC = ('strength dexterity constitution intelligence willpower '
           'stat_progress strength_progress dexterity_progress constitution_progress '
           'intelligence_progress willpower_progress charisma_progress soul_level '
           'soul_xp soul_tier soul_weapon_mastery_level soul_weapon_mastery_xp '
           'silver gold mithril charisma character_level character_xp deaths').split()
TEXT = ('room_id guild_reputation_json guild_exams_json '
        'guild_class_quests_json guild_bounty_json loot_filter active_title').split()


class DB(DatabaseAccountsMixin):
    pass


def new_char(account_id=1, silver=100):
    fields = {k: 1 for k in NUMERIC}
    fields.update(account_id=account_id, soul_xp=0, character_xp=50,
                  silver=silver, gold=0, mithril=0)
    fields.update({k: '' for k in TEXT})
    fields['room_id'] = 'square'
    return SimpleNamespace(**fields)


class AtomicV104Test(unittest.TestCase):
    def setUp(self):
        self.db = DB()
        self.db.conn = sqlite3.connect(':memory:')
        self.db.conn.row_factory = sqlite3.Row
        columns = ', '.join(['account_id INTEGER PRIMARY KEY'] +
                            [f'{name} INTEGER NOT NULL DEFAULT 0' for name in NUMERIC] +
                            [f'{name} TEXT NOT NULL DEFAULT ""' for name in TEXT])
        self.db.conn.execute('CREATE TABLE characters (' + columns + ')')
        self.db.conn.executescript('''
            CREATE TABLE account_characters(character_account_id INTEGER, master_account_id INTEGER);
            CREATE TABLE account_wallet(master_account_id INTEGER PRIMARY KEY, silver INTEGER,
                                        gold INTEGER, mithril INTEGER, updated_at TEXT);
            INSERT INTO characters(account_id,character_xp,silver) VALUES(1,50,100);
            INSERT INTO characters(account_id,character_xp,silver) VALUES(2,50,100);
            INSERT INTO account_characters VALUES(1,1);
            INSERT INTO account_characters VALUES(2,1);
            INSERT INTO account_wallet(master_account_id,silver,gold,mithril) VALUES(1,100,0,0);
        ''')
        self.db.conn.commit()

    def tearDown(self):
        self.db.conn.close()

    def balances(self):
        wallet = self.db.conn.execute('SELECT silver FROM account_wallet WHERE master_account_id=1').fetchone()[0]
        chars = tuple(row[0] for row in self.db.conn.execute('SELECT silver FROM characters ORDER BY account_id'))
        xp = self.db.conn.execute('SELECT character_xp FROM characters WHERE account_id=1').fetchone()[0]
        return wallet, chars, xp

    def test_success_mirrors_multiple_slots(self):
        c = new_char(silver=320)
        self.db.save_character(c)
        self.assertEqual(self.balances(), (320,(320,320),50))

    def test_character_update_fails_wallet_is_rolled_back(self):
        self.db.conn.execute('''CREATE TRIGGER prevent_xp BEFORE UPDATE OF character_xp ON characters
            WHEN NEW.account_id=1 BEGIN SELECT RAISE(ABORT,'xp failure'); END;''')
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.save_character(new_char(silver=321))
        self.assertEqual(self.balances(), (100,(100,100),50))

    def test_wallet_mirror_failure_no_partial_mirror(self):
        self.db.conn.execute('''CREATE TRIGGER prevent_wallet_mirror BEFORE UPDATE OF silver ON characters
            WHEN NEW.account_id=2 BEGIN SELECT RAISE(ABORT,'mirror failure'); END;''')
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.set_shared_wallet_for_master(1, 500, 0, 0)
        self.assertEqual(self.balances(), (100,(100,100),50))

    def test_nested_savepoint_preserves_parent(self):
        self.db.conn.execute('SAVEPOINT parent')
        self.db.conn.execute('UPDATE characters SET character_xp=49 WHERE account_id=1')
        self.db.conn.execute('''CREATE TRIGGER prevent_wallet_mirror BEFORE UPDATE OF silver ON characters
            WHEN NEW.account_id=2 BEGIN SELECT RAISE(ABORT,'mirror failure'); END;''')
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.save_character(new_char(silver=777), commit=False)
        self.assertEqual(self.balances(), (100,(100,100),49))
        self.db.conn.execute('ROLLBACK TO SAVEPOINT parent')
        self.db.conn.execute('RELEASE SAVEPOINT parent')
        self.assertEqual(self.balances(), (100,(100,100),50))

    def test_overflow_never_reaches_sql(self):
        c = new_char(silver=321)
        c.character_xp = 10**100
        with self.assertRaises(SQLiteNumericLimitV104):
            self.db.save_character(c)
        self.assertEqual(self.balances(), (100,(100,100),50))

    def test_commit_false_allows_outer_transaction_rollback(self):
        self.db.conn.execute('SAVEPOINT outer')
        self.db.save_character(new_char(silver=456), commit=False)
        self.assertEqual(self.balances(), (456,(456,456),50))
        self.db.conn.execute('ROLLBACK TO outer')
        self.db.conn.execute('RELEASE outer')
        self.assertEqual(self.balances(), (100,(100,100),50))

    def test_missing_character_rolls_back_wallet(self):
        self.db.conn.execute('INSERT INTO account_characters VALUES(3,1)')
        with self.assertRaises(LookupError):
            self.db.save_character(new_char(account_id=3, silver=999))
        self.assertEqual(self.balances(), (100,(100,100),50))

    def test_character_only_on_shared_wallet_failure_is_unchanged(self):
        self.db.conn.execute('''CREATE TRIGGER prevent_wallet BEFORE UPDATE OF silver ON account_wallet
            BEGIN SELECT RAISE(ABORT,'wallet failure'); END;''')
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.save_character(new_char(silver=222))
        self.assertEqual(self.balances(), (100,(100,100),50))


def run():
    suite = unittest.TestSuite((
        unittest.defaultTestLoader.loadTestsFromTestCase(AtomicV104Test),
        unittest.defaultTestLoader.loadTestsFromTestCase(AtomicFacadeV104Test),
    ))
    result = unittest.TextTestRunner(verbosity=0).run(suite)
    if not result.wasSuccessful():
        raise AssertionError('V104 stage 11 atomic tests FAIL')
    return result.testsRun



# Additional non-class tests are kept in the same suite via subclass below.
class AtomicFacadeV104Test(unittest.TestCase):
    def test_deferred_commit_proxy_preserves_atomicity(self):
        from storage.database import _DeferredCommitConnection
        conn = sqlite3.connect(':memory:')
        proxy = _DeferredCommitConnection(conn)
        try:
            proxy.execute('CREATE TABLE account_wallet(master_account_id INTEGER PRIMARY KEY, silver INTEGER, gold INTEGER, mithril INTEGER, updated_at TEXT)')
            proxy.execute('CREATE TABLE account_characters(character_account_id INTEGER,master_account_id INTEGER)')
            proxy.execute('CREATE TABLE characters(account_id INTEGER PRIMARY KEY,silver INTEGER,gold INTEGER,mithril INTEGER)')
            proxy.execute('INSERT INTO account_wallet VALUES(1,100,0,0,NULL)')
            proxy.execute('INSERT INTO account_characters VALUES(1,1)')
            proxy.execute('INSERT INTO characters VALUES(1,100,0,0)')
            proxy.commit()
            db = DB(); db.conn = proxy
            with proxy.deferred_commits():
                db.set_shared_wallet_for_master(1, 140, 0, 0)
                self.assertEqual(proxy.execute('SELECT silver FROM characters').fetchone()[0],140)
            self.assertEqual(conn.execute('SELECT silver FROM account_wallet').fetchone()[0],140)
            self.assertEqual(conn.execute('SELECT silver FROM characters').fetchone()[0],140)
        finally:
            conn.close()

if __name__=="__main__":
    print("V104 ETAP 11 ATOMIC:", run(), "PASS", flush=True)
