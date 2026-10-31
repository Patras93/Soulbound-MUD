# -*- coding: utf-8 -*-
"""Testy aktywnego rozliczenia monet + statystyk, w izolowanej SQLite."""
import sqlite3
import unittest
from types import MethodType
from validation.test_v10400_atomic_live_character_xp import fixture
from systems.combat_kill_settlement_v10400 import settle_combat_currency_stats_v10400
from core.bootstrap_economy_professions import normalize_currency_values

STATS=('strength','dexterity','constitution','intelligence','willpower','charisma')

class CombatCurrencyStat(unittest.TestCase):
    def setUp(self):
        self.db, self.char = fixture()
        self.char.STAT_PROGRESS_FIELDS = {name:(name,name,name+'_progress') for name in STATS}
        def add_stat(c, paid, *, targets, **_kw):
            n=targets[0]
            setattr(c,n+'_progress',getattr(c,n+'_progress') + paid)
            return [n + ': +' + str(paid)]
        self.char.add_stat_progress = MethodType(add_stat, self.char)
        self.db.conn.commit()
    def tearDown(self):self.db.conn.close()
    def saved(self):
        row=self.db.conn.execute('SELECT silver,gold,mithril,strength_progress,dexterity_progress FROM characters WHERE account_id=1').fetchone()
        return tuple(row)
    def wallet(self):
        row=self.db.conn.execute('SELECT silver,gold,mithril FROM account_wallet WHERE master_account_id=1').fetchone()
        return tuple(row)
    def bank(self,name):
        row=self.db.conn.execute("SELECT balance FROM experience_bank_v2011 WHERE account_id=1 AND kind='stat' AND source_key=?",(name,)).fetchone()
        return int(row[0]) if row else 0
    def test_full_reward(self):
        rewards=settle_combat_currency_stats_v10400(self.db,self.char,1,silver=25,gold=1,stat_xp=200)
        expected=normalize_currency_values(125,1,0)
        self.assertEqual(len(rewards),6)
        self.assertEqual(self.wallet(),expected)
        self.assertEqual(self.saved()[:3],expected)
        self.assertEqual(self.bank('strength'),100)
        self.assertEqual(self.bank('dexterity'),100)
        self.assertEqual(tuple(x[1] for x in rewards),(100,)*6)
    def test_wallet_failure_rolls_back_stat_bank(self):
        self.db.conn.execute("CREATE TRIGGER fail_wallet BEFORE UPDATE ON account_wallet BEGIN SELECT RAISE(ABORT,'wallet'); END")
        with self.assertRaises(sqlite3.IntegrityError):
            settle_combat_currency_stats_v10400(self.db,self.char,1,silver=25,stat_xp=200)
        self.assertEqual(self.wallet(),(100,0,0))
        self.assertEqual(self.saved()[:3],(100,0,0))
        self.assertEqual((self.char.silver,self.char.gold,self.char.mithril),(100,0,0))
        self.assertEqual(self.bank('strength'),0)
        self.assertEqual(self.char.strength_progress,1)
    def test_stat_failure_rolls_back_money(self):
        self.db.conn.execute("CREATE TRIGGER fail_stat BEFORE UPDATE OF strength_progress ON characters BEGIN SELECT RAISE(ABORT,'stat'); END")
        with self.assertRaises(sqlite3.IntegrityError):
            settle_combat_currency_stats_v10400(self.db,self.char,1,silver=20,stat_xp=200)
        self.assertEqual(self.wallet(),(100,0,0))
        self.assertEqual(self.saved()[:3],(100,0,0))
        self.assertEqual(self.bank('strength'),0)
        self.assertEqual(self.char.silver,100)
    def test_coin_only(self):
        r=settle_combat_currency_stats_v10400(self.db,self.char,1,silver=2)
        self.assertEqual(r,[])
        self.assertEqual(self.wallet(),normalize_currency_values(102,0,0))
    def test_exp_only(self):
        r=settle_combat_currency_stats_v10400(self.db,self.char,1,stat_xp=200)
        self.assertEqual(len(r),6)
        self.assertEqual(self.wallet(),(100,0,0))
    def test_overflow_without_modification(self):
        self.char.silver=(1<<63)-1
        with self.assertRaises(OverflowError):
            settle_combat_currency_stats_v10400(self.db,self.char,1,silver=1,stat_xp=200)
        self.assertEqual(self.wallet(),(100,0,0))
        self.assertEqual(self.bank('strength'),0)
        self.assertEqual(self.char.silver,(1<<63)-1)
    def test_bad_inputs(self):
        for payload in ({'silver':1.5},{'gold':-1},{'mithril':True},{'stat_xp':-10}):
            with self.assertRaises(ValueError):
                settle_combat_currency_stats_v10400(self.db,self.char,1,**payload)
        with self.assertRaises(ValueError):
            settle_combat_currency_stats_v10400(self.db,self.char,999,silver=5)
        self.assertEqual(self.wallet(),(100,0,0))

def run():
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(CombatCurrencyStat)
    result=unittest.TextTestRunner(verbosity=1).run(suite)
    if not result.wasSuccessful(): raise AssertionError('Combat waluta-stat FAIL')
    return result.testsRun

if __name__=='__main__':print('Combat wallet+stat:',run(),'PASS')
