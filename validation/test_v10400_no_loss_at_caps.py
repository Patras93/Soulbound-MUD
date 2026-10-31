# -*- coding: utf-8 -*-
"""v104: authentic game EXP gateway, max-level edge cases, temporary SQLite.

Never starts a server, opens port 4000, reads players or modifies live caps.
"""
from __future__ import annotations
import sqlite3
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from player.character import Character
from storage.db_experience_bank_v2011 import DatabaseExperienceBankV2011Mixin
from systems.experience_bank_v2011 import banked_experience_v2011


class Bank(DatabaseExperienceBankV2011Mixin):
    def __init__(self):
        self.conn = sqlite3.connect(':memory:')
        self.conn.execute('PRAGMA foreign_keys=ON')
        self.conn.execute('CREATE TABLE accounts(id INTEGER PRIMARY KEY)')
        self.conn.execute('INSERT INTO accounts VALUES(1)')
        self.conn.execute('CREATE TABLE characters(account_id INTEGER PRIMARY KEY, character_level INTEGER, soul_level INTEGER)')
        self.conn.execute('INSERT INTO characters VALUES(1,800,800)')
        self.create_experience_bank_schema_v2011()
    def multi_cap_v23215(self, account_id):
        return 100
    def saved(self,kind):
        row=self.conn.execute('SELECT balance FROM experience_bank_v2011 WHERE account_id=1 AND kind=?', (kind,)).fetchone()
        return None if row is None else int(row[0])


class CapsNoLoss(unittest.TestCase):
    def setUp(self): self.db=Bank()
    def tearDown(self): self.db.conn.close()

    def test_character_full_cap_goes_entirely_to_bank(self):
        with patch('core.progression_resources.character_xp_to_next',return_value=0):
            paid=banked_experience_v2011(self.db,1,5000,'character',800)
            self.assertEqual(paid,0)
            self.assertEqual(self.db.saved('character'),5000)
            paid=banked_experience_v2011(self.db,1,100,'character',800,overcap=True)
            self.assertEqual(paid,0)
            self.assertEqual(self.db.saved('character'),5100)

    def test_soul_full_cap_goes_entirely_to_bank(self):
        with patch('core.progression_resources.soul_xp_to_next',return_value=0):
            paid=banked_experience_v2011(self.db,1,6000,'soul',800)
            self.assertEqual(paid,0)
            self.assertEqual(self.db.saved('soul'),6000)

    def test_cap_raised_bank_releases_exp(self):
        with patch('core.progression_resources.character_xp_to_next',return_value=0):
            self.assertEqual(banked_experience_v2011(self.db,1,6000,'character',800),0)
        with patch('core.progression_resources.character_xp_to_next',return_value=100000):
            self.assertEqual(banked_experience_v2011(self.db,1,10,'character',800),20)
            self.assertEqual(self.db.saved('character'),5990)

    def test_huge_full_cap_no_loss(self):
        with patch('core.progression_resources.character_xp_to_next',return_value=0):
            amount=10**100
            self.assertEqual(banked_experience_v2011(self.db,1,amount,'character',800),0)
            self.assertEqual(self.db.saved('character'),amount)

    def test_partial_final_level_keeps_remainder(self):
        c=SimpleNamespace(character_level=2,character_xp=0)
        with patch('player.character.CHARACTER_MAX_LEVEL',3), patch('player.character.character_xp_to_next',return_value=100):
            notes=Character.add_character_xp(c,147)
        self.assertEqual((c.character_level,c.character_xp),(3,47))
        self.assertTrue(notes)

    def test_direct_credit_when_capped_not_dropped(self):
        c=SimpleNamespace(character_level=3,character_xp=10)
        with patch('player.character.CHARACTER_MAX_LEVEL',3):
            Character.add_character_xp(c,999)
        self.assertEqual(c.character_xp,1009)

    def test_direct_soul_credit_at_cap_not_dropped(self):
        c=SimpleNamespace(soul_level=10,soul_xp=120)
        with patch('player.character.SOUL_MAX_LEVEL',10):
            Character.add_soul_xp(c,234)
        self.assertEqual(c.soul_xp,354)

    def test_soul_crosses_final_level_keeps_remainder(self):
        class Soul:
            add_soul_xp=Character.add_soul_xp
            soul_level_cap_for_current_tier=Character.soul_level_cap_for_current_tier
            soul_progress_is_tier_locked=Character.soul_progress_is_tier_locked
            soul_xp_to_next=lambda self:100
            racial_soul_xp_multiplier=lambda self:1
            soul_level=2
            soul_tier=1
            soul_xp=0
            race='Czlowiek'
            _guild_bonus_percent=0
        c=Soul()
        with patch('player.character.SOUL_MAX_LEVEL',3),patch('player.character.SOUL_MAX_TIER',1),patch('player.character.SOUL_TIER_THRESHOLDS',(3,)):
            Character.add_soul_xp(c,145)
        self.assertEqual((c.soul_level,c.soul_xp),(3,45))

    def test_invalid_bank_balance_rolls_back(self):
        self.db.conn.execute("INSERT INTO experience_bank_v2011 VALUES(1,'character','','not-a-number')")
        with patch('core.progression_resources.character_xp_to_next',return_value=0):
            with self.assertRaises(ValueError):
                banked_experience_v2011(self.db,1,1000,'character',800)
        self.assertEqual(self.db.conn.execute("SELECT balance FROM experience_bank_v2011").fetchone()[0],'not-a-number')


def run():
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(CapsNoLoss)
    out=unittest.TextTestRunner(verbosity=0).run(suite)
    if not out.wasSuccessful():raise AssertionError('v104 cap/no-loss FAIL')
    return out.testsRun
if __name__=='__main__':print('NO LOSS:',run(),'PASS')
