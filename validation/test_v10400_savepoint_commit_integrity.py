# -*- coding: utf-8 -*-
"""Bank, profession, tool, class: no implicit commit may break caller SAVEPOINT.

All tests run on a marked, private, disposable sqlite database.  No production IO.
"""
import tempfile
import unittest
from pathlib import Path
from storage.db_progression import DatabaseProgressionMixin
from validation.test_v10400_currency_big_number_copy import CopyMoneyDB


class CopyAllDB(DatabaseProgressionMixin, CopyMoneyDB):
    def __init__(self, folder):
        super().__init__(folder)
        self.conn.executescript('''
            CREATE TABLE class_progress (account_id INTEGER, class_name TEXT,
                level INTEGER, xp INTEGER, active_slot INTEGER,
                PRIMARY KEY(account_id,class_name));
            CREATE TABLE professions (account_id INTEGER, profession TEXT,
                level INTEGER, xp INTEGER, actions INTEGER,
                PRIMARY KEY(account_id,profession));
            CREATE TABLE tools (account_id INTEGER, tool_type TEXT,
                level INTEGER, xp INTEGER, uses INTEGER,
                PRIMARY KEY(account_id,tool_type));
        ''')
        self.conn.commit()


class SavepointCommitIntegrity(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='sb104_savepoint_')
        self.root = Path(self.temp.name)
        (self.root / '.SOULBOUND_V104_WYLACZNIE_KOPIA_TESTOWA').write_text(
            'TYLKO TEST\n', encoding='utf-8')
        self.db = CopyAllDB(self.root)
        self.db.enable_big_number_copy_rehearsal_v104()

    def tearDown(self):
        self.db.conn.close()
        self.temp.cleanup()

    def test_all_four_lazy_records_rollback_together(self):
        self.db.conn.execute('SAVEPOINT full_reward')
        self.db.ensure_bank(1)
        self.db.ensure_profession(1, 'Zielarstwo')
        self.db.ensure_tool(1, 'Sierp')
        self.db.ensure_class_progress(1, 'Mag')
        self.db.conn.execute('ROLLBACK TO SAVEPOINT full_reward')
        self.db.conn.execute('RELEASE SAVEPOINT full_reward')
        for table in ('bank_balances', 'professions', 'tools', 'class_progress'):
            self.assertEqual(self.db.conn.execute(
                f'SELECT COUNT(*) FROM {table}').fetchone()[0], 0, table)

    def test_big_number_mutations_can_rollback_entire_bundle(self):
        self.db.conn.execute('SAVEPOINT full_reward')
        self.assertTrue(self.db.change_bank_currency(1, 'silver', 10**110))
        self.db.ensure_profession(1, 'Zielarstwo')
        self.db.save_profession(1, 'Zielarstwo', 100, 10**111, 2)
        self.db.ensure_tool(1, 'Sierp')
        self.db.save_tool(1, 'Sierp', 101, 10**112, 3)
        self.db.ensure_primary_class(1, 'Mag')
        self.db.add_class_mastery_xp(1, 'Mag', 500)
        self.assertGreater(self.db.bank_balance(1)['silver'], 2**63-1)
        self.db.conn.execute('ROLLBACK TO SAVEPOINT full_reward')
        self.db.conn.execute('RELEASE SAVEPOINT full_reward')
        for table in ('bank_balances', 'professions', 'tools', 'class_progress'):
            self.assertEqual(self.db.conn.execute(
                f'SELECT COUNT(*) FROM {table}').fetchone()[0], 0, table)

    def test_bank_rollback_does_not_erase_prior_committed_balance(self):
        self.assertTrue(self.db.change_bank_currency(1, 'silver', 55))
        self.db.conn.execute('SAVEPOINT spend')
        self.assertTrue(self.db.change_bank_currency(1, 'silver', 10**95))
        self.db.conn.execute('ROLLBACK TO SAVEPOINT spend')
        self.db.conn.execute('RELEASE SAVEPOINT spend')
        self.assertEqual(self.db.bank_balance(1)['silver'], 55)

    def test_default_wallet_save_respects_caller_savepoint(self):
        self.db.conn.execute('SAVEPOINT reward_bundle')
        self.db.set_shared_wallet_for_master(1, 10**120, 0, 0)
        self.db.conn.execute('ROLLBACK TO SAVEPOINT reward_bundle')
        self.db.conn.execute('RELEASE SAVEPOINT reward_bundle')
        self.assertEqual(self.db.shared_wallet_for_master(1), (20, 0, 0))

    def test_default_character_save_respects_caller_savepoint(self):
        from player.character import Character
        original = Character.from_row(self.db.character_for_account(1))
        self.db.conn.execute('SAVEPOINT reward_bundle')
        updated = Character.from_row(self.db.character_for_account(1))
        updated.character_xp = 10**125 + 14
        updated.silver = 10**120 + 3
        self.db.save_character(updated)
        self.db.conn.execute('ROLLBACK TO SAVEPOINT reward_bundle')
        self.db.conn.execute('RELEASE SAVEPOINT reward_bundle')
        restored = Character.from_row(self.db.character_for_account(1))
        self.assertEqual(restored.character_xp, original.character_xp)
        self.assertEqual(restored.silver, original.silver)
        self.assertEqual(self.db.shared_wallet_for_master(1), (20, 0, 0))

    def test_missing_wallet_fallback_inside_savepoint_can_rollback(self):
        self.db.conn.execute('DELETE FROM account_wallet WHERE master_account_id=1')
        self.db.conn.commit()
        self.db.conn.execute('SAVEPOINT reward_bundle')
        self.assertEqual(self.db.shared_wallet_for_master(1), (20, 0, 0))
        self.db.conn.execute('ROLLBACK TO SAVEPOINT reward_bundle')
        self.db.conn.execute('RELEASE SAVEPOINT reward_bundle')
        self.assertIsNone(self.db.conn.execute(
            'SELECT 1 FROM account_wallet WHERE master_account_id=1').fetchone())

    def test_noncanonical_legacy_bank_normalize_can_rollback(self):
        self.db.ensure_bank(1)
        self.db.conn.execute('UPDATE bank_balances SET gold=150 WHERE account_id=1')
        self.db.conn.commit()
        self.db.conn.execute('SAVEPOINT reward_bundle')
        self.db._v104_big_number_copy_rehearsal = False
        try:
            self.db.bank_balance(1)
        finally:
            self.db._v104_big_number_copy_rehearsal = True
        self.db.conn.execute('ROLLBACK TO SAVEPOINT reward_bundle')
        self.db.conn.execute('RELEASE SAVEPOINT reward_bundle')
        row = self.db.conn.execute('SELECT gold,mithril FROM bank_balances WHERE account_id=1').fetchone()
        self.assertEqual(tuple(row), (150, 0))

    def test_normal_single_operations_still_commit(self):
        self.db.ensure_bank(1)
        self.db.ensure_tool(1, 'Kilof')
        self.db.ensure_profession(1, 'Kowalstwo')
        self.db.ensure_class_progress(1, 'Wojownik')
        self.assertFalse(self.db.conn.in_transaction)
        self.assertEqual(self.db.conn.execute('SELECT COUNT(*) FROM tools').fetchone()[0],1)


if __name__ == '__main__':
    unittest.main()
