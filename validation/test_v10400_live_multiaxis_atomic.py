# -*- coding: utf-8 -*-
"""Zgodność z rzeczywistą bazą SQLite: postać, portfel, EXP Bank, klasa.
Nie otwiera portów ani baz użytkowników.
"""
import sqlite3
import unittest
from types import MethodType
from unittest.mock import patch
from validation.test_v10400_atomic_live_character_xp import fixture
from storage.db_progression import DatabaseProgressionMixin
from systems.atomic_progression_rewards_v10400 import (
    award_soul_xp_atomic_v10400, award_stats_xp_atomic_v10400,
    award_class_xp_atomic_v10400,
)

class LiveRewards(unittest.TestCase):
    def setUp(self):
        self.db,self.char = fixture()
        self.char.soul_level=2
        self.char.soul_xp=9
        self.db.conn.execute('UPDATE characters SET soul_level=2,soul_xp=9 WHERE account_id=1')
        self.db.conn.commit()
        # Mockowanie tylko matematyki poziomu; cała baza i ścieżka save są prawdziwe.
        def soul_gain(c, paid, **_kwargs):
            c.soul_xp += paid
            if c.soul_xp >= 100:
                c.soul_level += 1
                c.soul_xp -= 100
            return ['Soul XP naliczone.']
        self.char.add_soul_xp = MethodType(soul_gain,self.char)
        fields={n:(n,n,n+'_progress') for n in ('strength','dexterity','constitution','intelligence','willpower','charisma')}
        self.char.STAT_PROGRESS_FIELDS=fields
        def stat_gain(c, paid, targets, **_kwargs):
            field=targets[0]
            setattr(c,field+'_progress',getattr(c,field+'_progress')+paid)
            if paid>=90:
                setattr(c,field,getattr(c,field)+1)
            return [field+' XP']
        self.char.add_stat_progress=MethodType(stat_gain,self.char)
    def tearDown(self): self.db.conn.close()
    def balance(self,kind,key=''):
        row=self.db.conn.execute('SELECT balance FROM experience_bank_v2011 WHERE account_id=1 AND kind=? AND source_key=?',(kind,key)).fetchone()
        return int(row[0]) if row else 0
    def saved(self,*fields):
        return tuple(self.db.conn.execute('SELECT '+','.join(fields)+' FROM characters WHERE account_id=1').fetchone())
    def test_soul_real_save_bank(self):
        paid, msg=award_soul_xp_atomic_v10400(self.db,self.char,1,200)
        self.assertEqual((paid,self.balance('soul')),(100,100))
        self.assertEqual(self.saved('soul_level','soul_xp'),(3,9))
        self.assertTrue(msg)
    def test_soul_write_error_rolls_back(self):
        self.db.conn.execute("CREATE TRIGGER ban_soul BEFORE UPDATE OF soul_xp ON characters BEGIN SELECT RAISE(ABORT,'soul error'); END")
        with self.assertRaises(sqlite3.IntegrityError):
            award_soul_xp_atomic_v10400(self.db,self.char,1,200)
        self.assertEqual((self.balance('soul'),self.char.soul_level,self.char.soul_xp),(0,2,9))
        self.assertEqual(self.saved('soul_level','soul_xp'),(2,9))
    def test_soul_overflow_no_lost_bank(self):
        self.char.soul_xp=2**63-5
        # Tier zatrzymuje postęp, więc wszystkie otrzymane punkty zostają w saldzie.
        def no_level_up(c, paid, **_kwargs):
            c.soul_xp += paid
            return []
        self.char.add_soul_xp=MethodType(no_level_up,self.char)
        with self.assertRaises(OverflowError):
            award_soul_xp_atomic_v10400(self.db,self.char,1,200)
        self.assertEqual(self.balance('soul'),0)
        self.assertEqual(self.char.soul_xp,2**63-5)
    def test_two_stats_are_one_transaction(self):
        paid=award_stats_xp_atomic_v10400(self.db,self.char,1,200,targets=('strength','dexterity'))
        self.assertEqual(len(paid),2)
        self.assertEqual((self.balance('stat','strength'),self.balance('stat','dexterity')),(100,100))
        self.assertEqual(self.saved('strength_progress','dexterity_progress'),(101,101))
    def test_second_stat_failure_rollback_all(self):
        # Second stat mutates in memory, but the DB rejects the combined save.
        self.db.conn.execute("CREATE TRIGGER ban_stats BEFORE UPDATE OF dexterity_progress ON characters BEGIN SELECT RAISE(ABORT,'stat error'); END")
        with self.assertRaises(sqlite3.IntegrityError):
            award_stats_xp_atomic_v10400(self.db,self.char,1,200,targets=('strength','dexterity'))
        self.assertEqual((self.balance('stat','strength'),self.balance('stat','dexterity')),(0,0))
        self.assertEqual((self.char.strength_progress,self.char.dexterity_progress),(1,1))
        self.assertEqual(self.saved('strength_progress','dexterity_progress'),(0,0))
    def test_invalid_stats_fail_closed(self):
        for names in (('strength','strength'),('unknown',),()):
            with self.assertRaises(ValueError):
                award_stats_xp_atomic_v10400(self.db,self.char,1,10,targets=names)
        self.assertEqual(self.balance('stat','strength'),0)
    def test_class_update_and_bank_atomic(self):
        self.db.__class__ = type('ClassDB',(self.db.__class__,DatabaseProgressionMixin),{})
        self.db.conn.execute('CREATE TABLE IF NOT EXISTS class_progress(account_id INTEGER,class_name TEXT,level INTEGER NOT NULL,xp INTEGER NOT NULL,active_slot INTEGER,PRIMARY KEY(account_id,class_name))')
        with patch('storage.db_progression.class_mastery_xp_to_next',return_value=1000):
            paid,row=award_class_xp_atomic_v10400(self.db,1,'Wojownik',200,1)
        self.assertEqual((paid,row['xp']), (100,100))
        self.assertEqual(self.balance('class','Wojownik'),100)
        self.assertEqual(tuple(self.db.conn.execute("SELECT level,xp FROM class_progress WHERE account_id=1 AND class_name='Wojownik'").fetchone()),(1,100))
    def test_class_trigger_failure_preserves_bank(self):
        self.db.__class__ = type('ClassDB',(self.db.__class__,DatabaseProgressionMixin),{})
        self.db.conn.execute('CREATE TABLE IF NOT EXISTS class_progress(account_id INTEGER,class_name TEXT,level INTEGER NOT NULL,xp INTEGER NOT NULL,active_slot INTEGER,PRIMARY KEY(account_id,class_name))')
        self.db.conn.execute("CREATE TRIGGER ban_class BEFORE UPDATE ON class_progress BEGIN SELECT RAISE(ABORT,'class error'); END")
        with self.assertRaises(sqlite3.IntegrityError),patch('storage.db_progression.class_mastery_xp_to_next',return_value=1000):
            award_class_xp_atomic_v10400(self.db,1,'Wojownik',200,1)
        self.assertEqual(self.balance('class','Wojownik'),0)
        self.assertIsNone(self.db.conn.execute("SELECT * FROM class_progress WHERE account_id=1").fetchone())

def run():
    result=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(LiveRewards))
    if not result.wasSuccessful(): raise AssertionError('Atomic multiaxis v104 FAILED')
    return result.testsRun

if __name__=='__main__': print('V104 live multi-axis:',run(),'PASS')
