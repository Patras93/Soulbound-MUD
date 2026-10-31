# -*- coding: utf-8 -*-
"""Regression for an isolated single-axis BigNumber XP write."""
from __future__ import annotations
import unittest
import tempfile
import sqlite3
from pathlib import Path
from validation.test_v10400_currency_big_number_copy import CopyMoneyDB
from storage.big_number_copy_runtime_v10400 import (
    read_exact_progression_copy, write_exact_progression_copy,
)
from core.big_numbers_v10400 import SQLITE_INT64_MAX


class SingleAxisReceiptTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='sb104_one_axis_')
        root = Path(self.temp.name)
        (root / '.SOULBOUND_V104_WYLACZNIE_KOPIA_TESTOWA').write_text('COPY ONLY\n')
        self.db = CopyMoneyDB(root)
        self.db.enable_big_number_copy_rehearsal_v104()

    def tearDown(self):
        self.db.conn.close()
        self.temp.cleanup()

    def test_missing_only_character_xp_shadow_is_rejected(self):
        big = 10**120+271
        write_exact_progression_copy(self.db, 1, character_xp=big)
        self.assertEqual(read_exact_progression_copy(self.db, 1, 'character_xp'), big)
        self.db.conn.execute("DELETE FROM big_number_shadow_v10400 WHERE axis='characters.character_xp'")
        with self.assertRaisesRegex(ValueError, 'brak dokładnego rekordu'):
            read_exact_progression_copy(self.db, 1, 'character_xp')
        with self.assertRaisesRegex(ValueError, 'brak dokładnego rekordu'):
            write_exact_progression_copy(self.db, 1, character_xp=big+1)
        self.assertEqual(self.db.conn.execute('SELECT character_xp FROM characters WHERE account_id=1').fetchone()[0], SQLITE_INT64_MAX)

    def test_missing_only_soul_xp_shadow_after_reopen_is_rejected(self):
        big = 10**100+11
        write_exact_progression_copy(self.db, 1, soul_xp=big)
        self.db.conn.commit()
        self.db.conn.close()
        self.db.conn = sqlite3.connect(self.db.path)
        self.db.conn.row_factory = sqlite3.Row
        self.assertEqual(read_exact_progression_copy(self.db, 1, 'soul_xp'), big)
        self.db.conn.execute("DELETE FROM big_number_shadow_v10400 WHERE axis='characters.soul_xp'")
        with self.assertRaisesRegex(ValueError, 'brak dokładnego rekordu'):
            read_exact_progression_copy(self.db, 1, 'soul_xp')

    def test_drop_whole_shadow_table_is_rejected(self):
        write_exact_progression_copy(self.db, 1, character_xp=10**95)
        self.db.conn.execute('DROP TABLE big_number_shadow_v10400')
        with self.assertRaisesRegex(ValueError, 'brak dokładnego rekordu'):
            read_exact_progression_copy(self.db, 1, 'character_xp')

    def test_damaged_receipt_is_rejected(self):
        write_exact_progression_copy(self.db, 1, soul_xp=10**95)
        self.db.conn.execute("UPDATE big_number_copy_axis_receipt_v10400 SET digest='bad'")
        with self.assertRaisesRegex(ValueError, 'uszkodzone potwierdzenie'):
            read_exact_progression_copy(self.db, 1, 'soul_xp')

    def test_outer_transaction_rollback_removes_receipt_and_value(self):
        before = read_exact_progression_copy(self.db, 1, 'character_xp')
        self.db.conn.execute('SAVEPOINT outer_one_axis')
        write_exact_progression_copy(self.db, 1, character_xp=10**90)
        self.db.conn.execute('ROLLBACK TO outer_one_axis')
        self.db.conn.execute('RELEASE outer_one_axis')
        self.assertEqual(read_exact_progression_copy(self.db, 1, 'character_xp'), before)
        self.assertIsNone(self.db.conn.execute("SELECT name FROM sqlite_master WHERE name='big_number_copy_axis_receipt_v10400'").fetchone())

    def test_two_axis_pilot_retains_compatibility(self):
        big = 10**85
        write_exact_progression_copy(self.db, 1, character_xp=big, soul_xp=big+7)
        self.assertEqual(read_exact_progression_copy(self.db, 1, 'soul_xp'), big+7)
        self.db.conn.execute("DELETE FROM big_number_shadow_v10400 WHERE axis='characters.character_xp'")
        with self.assertRaises(ValueError):
            read_exact_progression_copy(self.db, 1, 'character_xp')


def run():
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(SingleAxisReceiptTest)
    result = unittest.TextTestRunner(verbosity=0).run(suite)
    if not result.wasSuccessful():
        raise AssertionError('One-axis BigNumber receipt regression FAIL')
    return result.testsRun

if __name__ == '__main__':
    print('One-axis receipts:', run(), 'PASS')
