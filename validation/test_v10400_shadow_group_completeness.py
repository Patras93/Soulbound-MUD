# -*- coding: utf-8 -*-
"""Fail closed on partially removed copy-only BigNumber shadow groups."""
from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from player.character import Character
from validation.test_v10400_currency_big_number_copy import CopyMoneyDB
from storage.big_number_copy_runtime_v10400 import (
    AXES, read_exact_currency_copy, read_exact_progression_copy,
    write_exact_progression_copy,
)


class ShadowGroupCompletenessTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='sb104_group_')
        root = Path(self.temp.name)
        (root / '.SOULBOUND_V104_WYLACZNIE_KOPIA_TESTOWA').write_text('ONLY COPY\n')
        self.db = CopyMoneyDB(root)
        self.db.enable_big_number_copy_rehearsal_v104()

    def tearDown(self):
        self.db.conn.close()
        self.temp.cleanup()

    def test_missing_one_wallet_shadow_detected_not_truncated(self):
        self.db.set_shared_wallet_for_master(1, 10**120, 0, 0)
        self.db.conn.execute("DELETE FROM big_number_shadow_v10400 WHERE account_id=1 AND axis='account_wallet.gold'")
        with self.assertRaisesRegex(ValueError, 'niekompletny zestaw'):
            self.db.shared_wallet_for_master(1)
        with self.assertRaisesRegex(ValueError, 'niekompletny zestaw'):
            self.db.set_shared_wallet_for_master(1, 5, 0, 0)
        self.assertEqual(self.db.conn.execute('SELECT silver FROM account_wallet').fetchone()[0], (1<<63)-1)

    def test_missing_one_character_currency_shadow_detected(self):
        self.db.set_shared_wallet_for_master(1, 10**120, 0, 0)
        self.db.conn.execute("DELETE FROM big_number_shadow_v10400 WHERE account_id=1 AND axis='characters.mithril'")
        with self.assertRaisesRegex(ValueError, 'niekompletny zestaw'):
            self.db.character_for_account(1)

    def test_missing_one_progress_shadow_detected(self):
        c = Character.from_row(self.db.character_for_account(1))
        c.character_xp = 10**125
        self.db.save_character(c)
        self.assertEqual(self.db.character_for_account(1)['character_xp'],10**125)
        self.db.conn.execute("DELETE FROM big_number_shadow_v10400 WHERE account_id=1 AND axis='characters.soul_tier'")
        with self.assertRaisesRegex(ValueError, 'niekompletny zestaw'):
            self.db.character_for_account(1)
        with self.assertRaisesRegex(ValueError, 'niekompletny zestaw'):
            self.db.save_character(c)

    def test_old_two_axis_pilot_stays_valid(self):
        # The small pre-v104 pilot can write only two XP columns.
        write_exact_progression_copy(self.db, 1, character_xp=10**110, soul_xp=10**111)
        self.assertEqual(read_exact_progression_copy(self.db,1,'character_xp'),10**110)
        self.assertEqual(read_exact_progression_copy(self.db,1,'soul_xp'),10**111)
        self.assertEqual(len(AXES),14)

    def test_plain_unmigrated_currency_still_works(self):
        self.assertEqual(read_exact_currency_copy(self.db,1,'wallet'),(20,0,0))
        self.assertEqual(self.db.character_for_account(1)['silver'],20)

    def test_corrupted_bank_shadow_bundle_detected(self):
        self.db.change_bank_currency(1,'silver',10**125)
        self.db.conn.execute("DELETE FROM big_number_shadow_v10400 WHERE account_id=1 AND axis='bank_balances.gold'")
        with self.assertRaisesRegex(ValueError, 'niekompletny zestaw'):
            self.db.bank_balance(1)


if __name__ == '__main__':
    unittest.main()
