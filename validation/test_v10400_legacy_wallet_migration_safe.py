# -*- coding: utf-8 -*-
"""Nieusuwalne testy sald przy migracji kont: suma, WAL, rollback."""
from __future__ import annotations
import sqlite3
import unittest
from types import SimpleNamespace
from storage.migration_currency_v10400 import sum_slot_currency_v104
from storage.schema_migrate_economy import migrate_accounts_and_economy
from core.bootstrap_economy_professions import normalize_currency_values, legacy_currency_to_coins
from core.sqlite_numeric_guard_v10400 import SQLiteNumericLimitV104

FLAGS = ('class_starting_stats_v0851','character_start_balance_v0900',
         'unified_currency_v0859','legacy_mithril_ore_v0344')


class WalletMergeV104(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(':memory:')
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript('''
            CREATE TABLE migration_flags(flag TEXT PRIMARY KEY);
            CREATE TABLE account_characters(master_account_id INTEGER, character_account_id INTEGER,
                slot INTEGER,PRIMARY KEY(master_account_id,slot));
            CREATE TABLE characters(account_id INTEGER PRIMARY KEY,name TEXT,
                silver INTEGER NOT NULL DEFAULT 0,gold INTEGER NOT NULL DEFAULT 0,
                mithril INTEGER NOT NULL DEFAULT 0);
            CREATE TABLE account_wallet(master_account_id INTEGER PRIMARY KEY,
                silver INTEGER NOT NULL DEFAULT 0,gold INTEGER NOT NULL DEFAULT 0,
                mithril INTEGER NOT NULL DEFAULT 0,updated_at TEXT);
            CREATE TABLE bank_balances(account_id INTEGER PRIMARY KEY,
                silver INTEGER NOT NULL DEFAULT 0,gold INTEGER NOT NULL DEFAULT 0,
                mithril INTEGER NOT NULL DEFAULT 0);
        ''')
        self.conn.executemany('INSERT INTO migration_flags(flag) VALUES (?)', [(x,) for x in FLAGS])
        self.db = SimpleNamespace(conn=self.conn)

    def tearDown(self):
        self.conn.close()

    def migrate(self):
        return migrate_accounts_and_economy(self.db, legacy_currency_to_coins,
                normalize_currency_values, (), {}, (), {}, {})

    def seed(self):
        self.conn.executemany('INSERT INTO characters(account_id,name,silver,gold,mithril) VALUES(?,?,?,?,?)',
             [(1,'A',100,2,0),(2,'B',250,1,0),(3,'C',10,0,0)])
        self.conn.executemany('INSERT INTO account_characters VALUES(?,?,?)',
             [(1,1,1),(1,2,2),(3,3,1)])
        self.conn.executemany('INSERT INTO bank_balances VALUES(?,?,?,?)',
             [(1,300,1,0),(2,700,0,0),(3,100,0,0)])

    def test_full_merge_exact_without_duplication(self):
        self.seed()
        self.migrate()
        w=self.conn.execute('SELECT silver,gold,mithril FROM account_wallet WHERE master_account_id=1').fetchone()
        self.assertEqual(tuple(w),(650,0,0))
        self.assertEqual(self.conn.execute('SELECT silver FROM characters WHERE account_id=2').fetchone()[0],650)
        self.assertEqual(self.conn.execute('SELECT silver FROM bank_balances WHERE account_id=1').fetchone()[0],1100)
        self.assertIsNone(self.conn.execute('SELECT 1 FROM bank_balances WHERE account_id=2').fetchone())
        self.assertEqual(self.conn.execute('SELECT count(*) FROM migration_flags WHERE flag=?',('shared_account_wallet_v0832',)).fetchone()[0],1)
        self.migrate()
        self.assertEqual(self.conn.execute('SELECT silver FROM bank_balances WHERE account_id=1').fetchone()[0],1100)

    def test_aggregate_outside_int64_does_not_change_any_wallet(self):
        self.seed()
        # Individually valid int64, sum exceeds range of SQLite SUM.
        self.conn.execute('UPDATE characters SET silver=? WHERE account_id=2',(8_000_000_000_000_000_000,))
        with self.assertRaises(SQLiteNumericLimitV104):
            self.migrate()
        self.assertEqual(self.conn.execute('SELECT count(*) FROM account_wallet').fetchone()[0],0)
        self.assertIsNone(self.conn.execute('SELECT 1 FROM migration_flags WHERE flag=?',('shared_account_wallet_v0832',)).fetchone())
        self.assertEqual(self.conn.execute('SELECT silver FROM characters WHERE account_id=1').fetchone()[0],100)

    def test_bad_second_account_rolls_back_first_account(self):
        self.seed()
        self.conn.execute("UPDATE characters SET silver=? WHERE account_id=3",(1.25,))
        with self.assertRaises(TypeError):
            self.migrate()
        self.assertEqual(self.conn.execute('SELECT count(*) FROM account_wallet').fetchone()[0],0)
        self.assertEqual(self.conn.execute('SELECT silver FROM characters WHERE account_id=1').fetchone()[0],100)
        self.assertEqual(self.conn.execute('SELECT silver FROM bank_balances WHERE account_id=2').fetchone()[0],700)

    def test_bank_trigger_failure_rolls_back_wallet_and_characters(self):
        self.seed()
        self.conn.execute('''CREATE TRIGGER forbid_bank_merge BEFORE UPDATE ON bank_balances
                             BEGIN SELECT RAISE(ABORT,'bank denied'); END''')
        with self.assertRaises(sqlite3.IntegrityError):
            self.migrate()
        self.assertEqual(self.conn.execute('SELECT count(*) FROM account_wallet').fetchone()[0],0)
        self.assertEqual(self.conn.execute('SELECT silver FROM characters WHERE account_id=2').fetchone()[0],250)

    def test_parent_transaction_still_rollbackable(self):
        self.seed()
        self.conn.execute('SAVEPOINT owner')
        self.migrate()
        self.assertEqual(self.conn.execute('SELECT silver FROM account_wallet WHERE master_account_id=1').fetchone()[0],650)
        self.conn.execute('ROLLBACK TO SAVEPOINT owner')
        self.conn.execute('RELEASE SAVEPOINT owner')
        self.assertIsNone(self.conn.execute('SELECT 1 FROM migration_flags WHERE flag=?',('shared_account_wallet_v0832',)).fetchone())
        self.assertEqual(self.conn.execute('SELECT count(*) FROM account_wallet').fetchone()[0],0)

    def test_corrupt_negative_currency_rejected(self):
        self.seed()
        self.conn.execute('UPDATE bank_balances SET gold=-4 WHERE account_id=2')
        with self.assertRaises(ValueError):
            self.migrate()
        self.assertEqual(self.conn.execute('SELECT count(*) FROM account_wallet').fetchone()[0],0)

    def enable_old_nominal_conversion(self):
        self.conn.execute("DELETE FROM migration_flags WHERE flag='unified_currency_v0859'")
        self.conn.execute("INSERT INTO migration_flags(flag) VALUES('shared_account_wallet_v0832')")
        self.seed()
        self.conn.executemany('INSERT INTO account_wallet(master_account_id,silver,gold,mithril) VALUES(?,?,?,?)',
             [(1,300,1,0),(3,20,0,0)])

    def test_unified_nominals_convert_once_with_full_value(self):
        self.enable_old_nominal_conversion()
        self.migrate()
        expected=legacy_currency_to_coins(300,1,0)
        self.assertEqual(self.conn.execute('SELECT silver FROM account_wallet WHERE master_account_id=1').fetchone()[0],expected)
        self.assertEqual(self.conn.execute('SELECT silver FROM characters WHERE account_id=2').fetchone()[0],expected)
        self.assertEqual(self.conn.execute('SELECT silver FROM bank_balances WHERE account_id=1').fetchone()[0],legacy_currency_to_coins(300,1,0))
        self.migrate()
        self.assertEqual(self.conn.execute('SELECT silver FROM account_wallet WHERE master_account_id=1').fetchone()[0],expected)

    def test_bad_second_wallet_rolls_back_all_nominal_conversion(self):
        self.enable_old_nominal_conversion()
        self.conn.execute('UPDATE account_wallet SET gold=1.25 WHERE master_account_id=3')
        with self.assertRaises(TypeError):
            self.migrate()
        self.assertEqual(tuple(self.conn.execute('SELECT silver,gold FROM account_wallet WHERE master_account_id=1').fetchone()),(300,1))
        self.assertEqual(self.conn.execute('SELECT silver FROM characters WHERE account_id=2').fetchone()[0],250)
        self.assertIsNone(self.conn.execute("SELECT 1 FROM migration_flags WHERE flag='unified_currency_v0859'").fetchone())

    def test_unified_conversion_rejects_negative_and_huge(self):
        self.enable_old_nominal_conversion()
        self.conn.execute('UPDATE account_wallet SET mithril=-1 WHERE master_account_id=3')
        with self.assertRaises(ValueError):
            self.migrate()
        self.conn.execute('UPDATE account_wallet SET mithril=? WHERE master_account_id=3',(1_000_000_000_000_000,))
        with self.assertRaises(SQLiteNumericLimitV104):
            self.migrate()
        self.assertEqual(tuple(self.conn.execute('SELECT silver,gold FROM account_wallet WHERE master_account_id=1').fetchone()),(300,1))

    def test_auto_slots_rollback_on_invalid_currency(self):
        self.conn.execute("INSERT INTO characters(account_id,name,silver) VALUES(1,'A',100)")
        self.conn.execute("INSERT INTO characters(account_id,name,silver) VALUES(2,'B',1.5)")
        with self.assertRaises(TypeError):
            self.migrate()
        self.assertEqual(self.conn.execute('SELECT count(*) FROM account_characters').fetchone()[0],0)
        self.assertEqual(self.conn.execute('SELECT count(*) FROM account_wallet').fetchone()[0],0)

    def test_no_dynamic_table_names_allowed(self):
        with self.assertRaises(ValueError):
            sum_slot_currency_v104(self.conn,1,'characters; DROP TABLE accounts;')


def run():
    out=unittest.TextTestRunner(verbosity=0).run(unittest.defaultTestLoader.loadTestsFromTestCase(WalletMergeV104))
    if not out.wasSuccessful():
        raise AssertionError('Migracja starych portfeli v104 - FAIL')
    return out.testsRun

if __name__=='__main__':
    print('V104 STARE PORTFELE: ',run(),'PASS',flush=True)
