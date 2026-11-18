# -*- coding: utf-8 -*-
"""Shared wallet belongs to a non-empty real character roster, not login."""
import tempfile
import unittest
from pathlib import Path
from core.classes_skills import RACES, CLASSES
from core.bootstrap_economy_professions import STARTING_SILVER, STARTING_GOLD, STARTING_MITHRIL, SILVER_PER_GOLD, SILVER_PER_MITHRIL
from storage.database import Database

class WalletRosterLifecycle(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix="v115-wallet-roster-")
        self.addCleanup(self.tmp.cleanup)
        self.db = Database(str(Path(self.tmp.name)/"test.sqlite"))
        self.addCleanup(self.db.conn.close)
        self.race, self.cls = RACES[0], CLASSES[0]

    def create(self, owner, name):
        forms = {k:name for k in ('nom','gen','dat','acc','ins','loc','voc')}
        return self.db.create_character_for_master(owner,name,self.race,self.cls,forms)[0]

    def starter(self):
        return (STARTING_SILVER+STARTING_GOLD*SILVER_PER_GOLD+STARTING_MITHRIL*SILVER_PER_MITHRIL,0,0)

    def wallet_row(self, owner):
        row = self.db.conn.execute('SELECT silver,gold,mithril FROM account_wallet WHERE master_account_id=?',(owner,)).fetchone()
        return tuple(row) if row else None

    def test_last_deleted_resets_wallet_and_next_character_has_starters(self):
        owner = self.db.create_account('FirstAccount','test-secret-password')
        self.create(owner,'FirstOne')
        self.db.set_shared_wallet_for_master(owner,0,0,6)
        self.assertEqual(self.wallet_row(owner),(6*SILVER_PER_MITHRIL,0,0))
        self.db.delete_character_for_master(owner,owner)
        self.assertEqual(self.db.character_count_for_master(owner),0)
        self.assertIsNone(self.wallet_row(owner))
        self.assertEqual(self.db.shared_wallet_for_master(owner),(0,0,0))
        self.assertIsNotNone(self.db.account_by_name('FirstAccount'))
        self.create(owner,'NewOne')
        self.assertEqual(self.wallet_row(owner),self.starter())
        self.assertEqual(self.db.conn.execute('PRAGMA integrity_check').fetchone()[0],'ok')

    def test_delete_one_of_two_preserves_wallet_until_last(self):
        owner=self.db.create_account('SecondAccount','test-secret-password')
        first=self.create(owner,'SecondOne')
        second=self.create(owner,'SecondTwo')
        self.db.set_shared_wallet_for_master(owner,0,0,6)
        self.db.delete_character_for_master(owner,second)
        self.assertEqual(self.wallet_row(owner),(6*SILVER_PER_MITHRIL,0,0))
        self.assertEqual(self.db.character_count_for_master(owner),1)
        self.db.delete_character_for_master(owner,first)
        self.assertIsNone(self.wallet_row(owner))

    def test_old_zero_character_wallet_cannot_leak_into_first_character(self):
        owner=self.db.create_account('StaleAccount','test-secret-password')
        self.db.set_shared_wallet_for_master(owner,0,0,6)
        self.assertEqual(self.wallet_row(owner),(6*SILVER_PER_MITHRIL,0,0))
        self.assertEqual(self.db.shared_wallet_for_master(owner),(0,0,0))
        self.create(owner,'FreshFromOldLogin')
        self.assertEqual(self.wallet_row(owner),self.starter())

    def test_new_character_with_existing_roster_inherits_shared_wallet(self):
        owner=self.db.create_account('TwoAccount','test-secret-password')
        self.create(owner,'TwoOne')
        self.db.set_shared_wallet_for_master(owner,0,0,6)
        second=self.create(owner,'TwoTwo')
        self.assertEqual(self.wallet_row(owner),(6*SILVER_PER_MITHRIL,0,0))
        row=self.db.character_for_account(second)
        self.assertEqual((row['silver'],row['gold'],row['mithril']),(6*SILVER_PER_MITHRIL,0,0))

    def test_failed_first_creation_does_not_destroy_preexisting_sqlite(self):
        owner=self.db.create_account('FailAccount','test-secret-password')
        self.db.set_shared_wallet_for_master(owner,0,0,6)
        forms={k:'InvalidFirst' for k in ('nom','gen','dat','acc','ins','loc','voc')}
        cyborg_mec=next(c for c in CLASSES if c[0]=='Mec')
        human=next(r for r in RACES if r[0]!='Cyborg')
        with self.assertRaises(ValueError):
            self.db.create_character_for_master(owner,'InvalidFirst',human,cyborg_mec,forms)
        self.assertEqual(self.wallet_row(owner),(6*SILVER_PER_MITHRIL,0,0))
        self.assertEqual(self.db.character_count_for_master(owner),0)

if __name__=='__main__':unittest.main()
