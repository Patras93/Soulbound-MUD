# -*- coding: utf-8 -*-
"""Exact wallet/bank persistence through actual DB methods, disposable copy only."""
import sqlite3
import tempfile
import unittest
from pathlib import Path
from player.character import Character
from storage.db_inventory import DatabaseInventoryMixin
from validation.test_v10400_real_character_big_number_rehearsal import CopyDB
from core.big_numbers_v10400 import SQLITE_INT64_MAX


class CopyMoneyDB(DatabaseInventoryMixin, CopyDB):
    def __init__(self, folder):
        super().__init__(folder)
        self.conn.execute('CREATE TABLE bank_balances (account_id INTEGER PRIMARY KEY, '
                          'silver INTEGER, gold INTEGER, mithril INTEGER)')
        self.conn.commit()


class CurrencyCopyTest(unittest.TestCase):
    def setUp(self):
        self.t = tempfile.TemporaryDirectory(prefix='soulbound_v104_wallet_')
        self.root = Path(self.t.name)
        (self.root / '.SOULBOUND_V104_WYLACZNIE_KOPIA_TESTOWA').write_text('TYLKO TEST\n')
        self.db = CopyMoneyDB(self.root)
        self.db.enable_big_number_copy_rehearsal_v104()

    def tearDown(self):
        self.db.conn.close()
        self.t.cleanup()

    def test_wallet_real_save_character_and_restart_exact(self):
        c = Character.from_row(self.db.character_for_account(1))
        c.silver = 10**190 + 34
        c.gold = 15
        c.mithril = 2
        self.db.save_character(c)
        from core.bootstrap_economy_professions import SILVER_PER_GOLD, SILVER_PER_MITHRIL
        expected = 10**190 + 34 + 15 * SILVER_PER_GOLD + 2 * SILVER_PER_MITHRIL
        row = self.db.conn.execute('SELECT silver,gold,mithril FROM account_wallet').fetchone()
        self.assertEqual(tuple(row), (SQLITE_INT64_MAX, 0, 0))
        ch = self.db.conn.execute('SELECT silver,gold,mithril FROM characters').fetchone()
        self.assertEqual(tuple(ch), (SQLITE_INT64_MAX, 0, 0))
        self.db.conn.close()
        self.db.conn = sqlite3.connect(self.db.path)
        self.db.conn.row_factory = sqlite3.Row
        self.assertEqual(self.db.shared_wallet_for_character(1), (expected, 0, 0))
        c2 = Character.from_row(self.db.character_for_account(1))
        self.assertEqual((c2.silver, c2.gold, c2.mithril), (expected, 0, 0))

    def test_direct_wallet_write_updates_both_readers(self):
        amount = 10**130 + 57
        self.assertEqual(self.db.set_shared_wallet_for_master(1, amount, 0, 0), (amount, 0, 0))
        self.assertEqual(self.db.shared_wallet_for_master(1), (amount, 0, 0))
        self.assertEqual(self.db.character_for_account(1)['silver'], amount)
        self.assertEqual(self.db.character_for_account(1)[self.db.character_for_account(1).keys().index('silver')], amount)

    def test_bank_change_large_plus_and_subtract(self):
        self.db.change_bank_currency(1, 'silver', 10**180 + 24)
        self.assertEqual(self.db.bank_balance(1)['silver'], 10**180 + 24)
        self.assertEqual(self.db.bank_balance(1)[0], 10**180 + 24)
        self.assertTrue(self.db.change_bank_currency(1,'silver', -7))
        self.assertEqual(self.db.bank_balance(1)['silver'], 10**180 + 17)
        self.assertFalse(self.db.change_bank_currency(1,'silver', -(10**180+100)))
        self.assertEqual(self.db.bank_balance(1)['silver'], 10**180 + 17)
        self.db.conn.close()
        self.db.conn = sqlite3.connect(self.db.path)
        self.db.conn.row_factory = sqlite3.Row
        self.assertEqual(self.db.bank_balance(1)['silver'], 10**180 + 17)
        self.assertEqual(self.db.conn.execute('SELECT silver FROM bank_balances').fetchone()[0], SQLITE_INT64_MAX)

    def test_checksum_tampering_and_stale_wallet_mirror_fail_closed(self):
        self.db.set_shared_wallet_for_master(1, 10**90, 0, 0)
        self.db.conn.execute("UPDATE account_wallet SET silver=123 WHERE master_account_id=1")
        with self.assertRaises(ValueError):
            self.db.shared_wallet_for_master(1)
        with self.assertRaises(ValueError):
            self.db.set_shared_wallet_for_master(1, 99, 0, 0)
        self.assertEqual(self.db.conn.execute('SELECT silver FROM account_wallet').fetchone()[0], 123)

    def test_rollback_on_shadow_trigger(self):
        self.db.conn.execute('''CREATE TABLE IF NOT EXISTS big_number_shadow_v10400
          (account_id INTEGER NOT NULL, axis TEXT NOT NULL,source_key TEXT NOT NULL,
           balance_text TEXT NOT NULL,base_int64_text TEXT NOT NULL,sha256 TEXT NOT NULL,
           PRIMARY KEY(account_id,axis,source_key))''')
        self.db.conn.execute('''CREATE TRIGGER deny_copy BEFORE INSERT ON big_number_shadow_v10400
          WHEN NEW.axis='characters.silver' BEGIN SELECT RAISE(ABORT,'no shadow'); END''')
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.set_shared_wallet_for_master(1, 10**110, 0, 0)
        self.assertEqual(self.db.conn.execute('SELECT silver FROM account_wallet').fetchone()[0],20)
        self.assertEqual(self.db.conn.execute('SELECT silver FROM characters').fetchone()[0],20)
        self.assertEqual(self.db.conn.execute('SELECT count(*) FROM big_number_shadow_v10400').fetchone()[0],0)

    def test_outer_rollback_undoes_wallet_shadow_and_mirror(self):
        self.db.conn.execute('SAVEPOINT external')
        self.db.set_shared_wallet_for_master(1, 10**100, 0, 0, commit=False)
        self.db.conn.execute('ROLLBACK TO SAVEPOINT external')
        self.db.conn.execute('RELEASE SAVEPOINT external')
        self.assertEqual(self.db.shared_wallet_for_master(1), (20,0,0))
        self.assertEqual(self.db.character_for_account(1)['silver'],20)

    def test_marker_disappears_blocks_read_write_bank(self):
        self.db.change_bank_currency(1, 'silver', 10**100)
        (self.root / '.SOULBOUND_V104_WYLACZNIE_KOPIA_TESTOWA').unlink()
        with self.assertRaises(PermissionError):
            self.db.bank_balance(1)
        with self.assertRaises(PermissionError):
            self.db.set_shared_wallet_for_master(1,100,0,0)

    def test_production_normal_route_still_rejects_large_wallet(self):
        self.db._v104_big_number_copy_rehearsal = False
        with self.assertRaises(OverflowError):
            self.db.set_shared_wallet_for_master(1,10**80,0,0)
        self.assertEqual(self.db.shared_wallet_for_master(1),(20,0,0))


    def test_shared_wallet_updates_two_character_slots_atomically(self):
        original = dict(self.db.conn.execute('SELECT * FROM characters WHERE account_id=1').fetchone())
        original['account_id'] = 2
        original['name'] = 'Second'
        keys = list(original)
        self.db.conn.execute('INSERT INTO characters (' + ','.join('"'+k+'"' for k in keys) +
                             ') VALUES (' + ','.join('?' for _ in keys) + ')',
                             tuple(original.values()))
        self.db.conn.execute('INSERT INTO account_characters VALUES (1,2)')
        exact = 10**121 + 6
        self.db.set_shared_wallet_for_master(1,exact,0,0)
        self.assertEqual(self.db.character_for_account(1)['silver'],exact)
        self.assertEqual(self.db.character_for_account(2)['silver'],exact)
        row=self.db.conn.execute('SELECT silver FROM characters WHERE account_id=2').fetchone()
        self.assertEqual(row[0],SQLITE_INT64_MAX)
        # A stale legacy slot must prevent the *entire* next wallet update.
        self.db.conn.execute('UPDATE characters SET silver=9 WHERE account_id=2')
        with self.assertRaises(ValueError):
            self.db.set_shared_wallet_for_master(1,exact+1,0,0)
        self.assertEqual(self.db.shared_wallet_for_master(1)[0],exact)
        self.assertEqual(self.db.character_for_account(1)['silver'],exact)

    def test_checksum_modification_does_not_resurrect_money(self):
        self.db.set_shared_wallet_for_master(1,10**95,0,0)
        self.db.conn.execute("UPDATE big_number_shadow_v10400 SET balance_text='999' "
                             "WHERE account_id=1 AND axis='account_wallet.silver'")
        with self.assertRaises(ValueError):
            self.db.shared_wallet_for_master(1)
        with self.assertRaises(ValueError):
            self.db.set_shared_wallet_for_master(1,5,0,0)
        self.assertEqual(self.db.conn.execute('SELECT silver FROM account_wallet').fetchone()[0],
                         SQLITE_INT64_MAX)

    def test_ordinary_money_does_not_expand_legacy_fourteen_axis_pilot(self):
        from storage.big_number_shadow_v10400 import check_shadow
        from storage.big_number_copy_runtime_v10400 import AXES
        c = Character.from_row(self.db.character_for_account(1))
        c.character_xp=10**70
        self.db.save_character(c)
        self.assertEqual(len(AXES),14)
        self.assertEqual(check_shadow(self.db.conn),14)


if __name__ == '__main__':
    unittest.main()
