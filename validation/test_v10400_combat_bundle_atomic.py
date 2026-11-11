# -*- coding: utf-8 -*-
"""Prawdziwa baza SQLite: jeden zapis monet+statystyk+EXP postaci.

Wymuszone awarie po zapisaniu statystyk nie mogą skasować ani
zduplikować monet, banku ani EXP. Nie uruchamia TCP.
"""
import sqlite3
import unittest
from unittest.mock import patch
from validation.test_v10400_live_multiaxis_atomic import LiveRewards
from systems.combat_kill_settlement_v10400 import settle_combat_currency_stats_v10400

class CombatBundleAtomic(LiveRewards):
    def test_full_wallet_stats_character_commits(self):
        with patch('player.character.character_xp_to_next',return_value=100):
            stats, (paid, notes) = settle_combat_currency_stats_v10400(
                self.db, self.char, 1, silver=45, stat_xp=200, character_xp=300)
        self.assertEqual(self.char.silver,145)
        self.assertEqual(self.saved('silver','character_level','character_xp'),(145,3,50))
        self.assertEqual(self.balance('stat','strength'),100)
        self.assertEqual(self.balance('character'),200)
        self.assertEqual(paid,100)
        self.assertEqual(len(stats),6)
        self.assertTrue(notes)
    def test_character_write_error_rolls_back_whole_bundle(self):
        self.db.conn.execute("CREATE TRIGGER ban_character BEFORE UPDATE OF character_xp ON characters BEGIN SELECT RAISE(ABORT,'xp fail'); END")
        old=self.saved('silver','character_level','character_xp','strength_progress')
        with patch('player.character.character_xp_to_next',return_value=100):
            with self.assertRaises(sqlite3.IntegrityError):
                settle_combat_currency_stats_v10400(
                    self.db, self.char, 1, silver=55, stat_xp=200, character_xp=300)
        self.assertEqual(self.saved('silver','character_level','character_xp','strength_progress'),old)
        self.assertEqual(self.balance('stat','strength'),0)
        self.assertEqual(self.balance('character'),0)
        self.assertEqual(self.char.silver,100)
        self.assertEqual(self.char.strength_progress,1)
        self.assertEqual((self.char.character_level,self.char.character_xp),(2,50))
    def test_wallet_error_rolls_back_character_and_stat_bank(self):
        self.db.conn.execute("CREATE TRIGGER ban_wallet BEFORE UPDATE ON account_wallet BEGIN SELECT RAISE(ABORT,'wallet'); END")
        with patch('player.character.character_xp_to_next',return_value=100):
            with self.assertRaises(sqlite3.IntegrityError):
                settle_combat_currency_stats_v10400(self.db,self.char,1,
                                                   gold=1,stat_xp=200,character_xp=300)
        self.assertEqual(self.balance('character'),0)
        self.assertEqual(self.balance('stat','strength'),0)
        self.assertEqual((self.char.character_level,self.char.character_xp),(2,50))
        self.assertEqual((self.char.silver,self.char.gold),(100,0))
    def test_invalid_big_character_field_no_partial_credit(self):
        self.char.strength = 10**100
        with self.assertRaises(OverflowError):
            settle_combat_currency_stats_v10400(self.db,self.char,1,
                                               silver=1,stat_xp=200,character_xp=300)
        self.assertEqual(self.balance('character'),0)
        self.assertEqual(self.balance('stat','strength'),0)
        self.assertEqual(self.saved('silver','character_level'),(100,2))
        self.assertEqual(self.char.silver,100)
    def test_no_char_requested_retains_legacy_result(self):
        result=settle_combat_currency_stats_v10400(self.db,self.char,1,silver=1)
        self.assertIsInstance(result,list)
        self.assertEqual(self.char.silver,101)

def run():
    testnames=[name for name in unittest.defaultTestLoader.getTestCaseNames(CombatBundleAtomic)
               if name in {"test_full_wallet_stats_character_commits",
                           "test_character_write_error_rolls_back_whole_bundle",
                           "test_wallet_error_rolls_back_character_and_stat_bank",
                           "test_invalid_big_character_field_no_partial_credit",
                           "test_no_char_requested_retains_legacy_result"}]
    suite=unittest.TestSuite(CombatBundleAtomic(name) for name in testnames)
    outcome=unittest.TextTestRunner(verbosity=1).run(suite)
    if not outcome.wasSuccessful():raise AssertionError('Combat bundle atomic FAIL')
    return outcome.testsRun

if __name__=='__main__':print('V104 combat bundle:',run(),'PASS')
