# -*- coding: utf-8 -*-
"""Regression: a fully erased copy-only shadow group must never fall back to int64."""
import sqlite3
import tempfile
import unittest
from pathlib import Path

from player.character import Character
from validation.test_v10400_currency_big_number_copy import CopyMoneyDB
from storage.big_number_copy_runtime_v10400 import (
    read_exact_progression_copy, write_exact_progression_copy,
)
from core.big_numbers_v10400 import SQLITE_INT64_MAX


class CopyReceipts(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='sb104_receipt_')
        root = Path(self.temp.name)
        (root / '.SOULBOUND_V104_WYLACZNIE_KOPIA_TESTOWA').write_text('TYLKO KOPIA TESTOWA\n')
        self.db = CopyMoneyDB(root)
        self.db.enable_big_number_copy_rehearsal_v104()

    def tearDown(self):
        self.db.conn.close()
        self.temp.cleanup()

    def _erase(self, scope):
        self.db.conn.execute('DELETE FROM big_number_shadow_v10400 WHERE account_id=1 AND axis LIKE ?', (scope+'%',))

    def test_wallet_all_entries_removed_blocks_read_and_overwrite(self):
        self.db.set_shared_wallet_for_master(1, 10**110, 0, 0)
        self._erase('account_wallet.')
        with self.assertRaisesRegex(ValueError, 'niekompletny zestaw'):
            self.db.shared_wallet_for_master(1)
        with self.assertRaises(ValueError):
            self.db.set_shared_wallet_for_master(1, 42, 0, 0)
        self.assertEqual(self.db.conn.execute('SELECT silver FROM account_wallet').fetchone()[0], SQLITE_INT64_MAX)

    def test_bank_all_entries_removed_blocks_read(self):
        self.db.change_bank_currency(1, 'silver', 10**120)
        self._erase('bank_balances.')
        with self.assertRaisesRegex(ValueError, 'niekompletny zestaw'):
            self.db.bank_balance(1)

    def test_character_currency_all_removed_blocks_read(self):
        self.db.set_shared_wallet_for_master(1, 10**115, 0, 0)
        self._erase('characters.silver')
        self._erase('characters.gold')
        self._erase('characters.mithril')
        with self.assertRaisesRegex(ValueError, 'niekompletny zestaw'):
            self.db.character_for_account(1)

    def test_character_progress_all_removed_blocks_read(self):
        c = Character.from_row(self.db.character_for_account(1))
        c.character_xp = 10**105
        self.db.save_character(c)
        # Remove all 14 progression shadow entries, leaving the signed receipt.
        from storage.big_number_copy_runtime_v10400 import AXES
        self.db.conn.executemany('DELETE FROM big_number_shadow_v10400 WHERE account_id=1 AND axis=?',
                                 [('characters.'+axis,) for axis in AXES])
        with self.assertRaisesRegex(ValueError, 'niekompletny zestaw'):
            self.db.character_for_account(1)

    def test_two_axis_pilot_full_deletion_detected(self):
        write_exact_progression_copy(self.db, 1, character_xp=10**118, soul_xp=10**119)
        self._erase('characters.character_xp')
        self._erase('characters.soul_xp')
        with self.assertRaisesRegex(ValueError, 'niekompletny zestaw'):
            read_exact_progression_copy(self.db, 1, 'character_xp')

    def test_receipt_is_rollback_aware(self):
        self.db.conn.execute('SAVEPOINT rollback_receipt')
        self.db.set_shared_wallet_for_master(1, 10**130, 0, 0, commit=False)
        self.assertGreater(self.db.conn.execute('SELECT COUNT(*) FROM big_number_copy_receipt_v10400').fetchone()[0], 0)
        self.db.conn.execute('ROLLBACK TO SAVEPOINT rollback_receipt')
        self.db.conn.execute('RELEASE SAVEPOINT rollback_receipt')
        self.assertEqual(self.db.shared_wallet_for_master(1), (20, 0, 0))
        count = self.db.conn.execute('''SELECT COUNT(*) FROM sqlite_master
            WHERE type='table' AND name='big_number_copy_receipt_v10400' ''').fetchone()[0]
        self.assertEqual(count, 0)

    def test_shadow_table_removed_after_wallet_migration_is_rejected(self):
        self.db.set_shared_wallet_for_master(1, 10**145, 0, 0)
        self.db.conn.execute('DROP TABLE big_number_shadow_v10400')
        with self.assertRaisesRegex(ValueError, 'brak calej tabeli shadow'):
            self.db.shared_wallet_for_master(1)

    def test_receipt_persists_after_reopen(self):
        self.db.change_bank_currency(1, 'silver', 10**116)
        self.db.conn.commit()
        self.db.conn.close()
        self.db.conn = sqlite3.connect(self.db.path)
        self.db.conn.row_factory = sqlite3.Row
        self._erase('bank_balances.')
        with self.assertRaisesRegex(ValueError, 'niekompletny zestaw'):
            self.db.bank_balance(1)

    def test_receipt_corruption_rejected(self):
        self.db.set_shared_wallet_for_master(1, 10**135, 0, 0)
        self.db.conn.execute('UPDATE big_number_copy_receipt_v10400 SET axes_count=999 WHERE account_id=1')
        with self.assertRaisesRegex(ValueError, 'uszkodzone potwierdzenie'):
            self.db.shared_wallet_for_master(1)

if __name__ == '__main__':
    unittest.main()
