# -*- coding: utf-8 -*-
"""v104: real quest-stat gateway and class-batch transactions on isolated SQLite."""
import asyncio
import sqlite3
import unittest
from types import SimpleNamespace, MethodType
from unittest.mock import patch
from validation.test_v10400_live_multiaxis_atomic import LiveRewards
from storage.db_progression import DatabaseProgressionMixin
from systems.atomic_progression_rewards_v10400 import (
    award_stats_xp_atomic_v10400, award_class_xp_batch_atomic_v10400,
)
from player.session_methods_v4200 import dungeonprogression_part02 as gateway

NAMES = ('strength','dexterity','constitution','intelligence','willpower','charisma')

class QuestClassAtomic(unittest.TestCase):
    def setUp(self):
        # Reuse the real SQLite, real save_character and real bank from earlier tests.
        self.base = LiveRewards('test_soul_real_save_bank')
        self.base.setUp()
        self.db, self.char = self.base.db,self.base.char
        self.sent=[]
        async def send(msg): self.sent.append(msg)
        self.session=SimpleNamespace(
            character=self.char,account_id=1,server=SimpleNamespace(db=self.db),
            send=send, scale_progression_xp_v11342=lambda value,cl,content_scaled=False: value,
            apply_double_xp=lambda value: value,
        )
    def tearDown(self): self.base.tearDown()
    def quest(self,rewards,repeatable=False):
        with patch.object(gateway,'v0874_quest_stat_progress_base_grant',
                          lambda _char,_name,amount,_repeatable: amount,create=True):
            return asyncio.run(gateway.grant_combat_quest_stat_xp(
                self.session,rewards,repeatable=repeatable))
    def test_quest_six_distinct_values_and_zero(self):
        paid=self.quest(dict(zip(NAMES,(15,35,0,120,250,60))))
        self.assertEqual(paid,[15,35,0,100,100,60])
        self.assertEqual([self.base.balance('stat',name) for name in NAMES],
                         [0,0,0,20,150,0])
        for name,exp in zip(NAMES,(16,36,1,101,101,61)):
            self.assertEqual(getattr(self.char,name+'_progress'),exp)
        self.assertEqual(tuple(self.db.conn.execute(
            'SELECT '+','.join(name+'_progress' for name in NAMES)+
            ' FROM characters WHERE account_id=1').fetchone()),(16,36,1,101,101,61))
        self.assertTrue(self.sent)
    def test_quest_uniform_reward(self):
        self.assertEqual(self.quest(200),[100]*6)
        self.assertEqual([self.base.balance('stat',name) for name in NAMES],[100]*6)
    def test_quest_fail_at_last_stat_rolls_back_everything(self):
        self.db.conn.execute("CREATE TRIGGER fail_quest BEFORE UPDATE OF charisma_progress ON characters BEGIN SELECT RAISE(ABORT,'quest fail'); END")
        before=tuple(self.db.conn.execute('SELECT '+','.join(n+'_progress' for n in NAMES)+' FROM characters').fetchone())
        with self.assertRaises(sqlite3.IntegrityError):
            self.quest(dict(zip(NAMES,(100,300,10,90,40,20))))
        after=tuple(self.db.conn.execute('SELECT '+','.join(n+'_progress' for n in NAMES)+' FROM characters').fetchone())
        self.assertEqual(after,before)
        self.assertEqual([self.base.balance('stat',name) for name in NAMES],[0]*6)
        self.assertEqual([getattr(self.char,name+'_progress') for name in NAMES],[1]*6)
        self.assertEqual(self.sent,[])
    def test_quest_recovery_after_failure(self):
        self.db.conn.execute("CREATE TRIGGER fail_quest BEFORE UPDATE ON characters BEGIN SELECT RAISE(ABORT,'fail'); END")
        with self.assertRaises(sqlite3.IntegrityError):self.quest(200)
        self.db.conn.execute('DROP TRIGGER fail_quest')
        self.assertEqual(self.quest(200),[100]*6)
    def test_quest_large_exact_banks(self):
        large=10**90
        self.assertEqual(self.quest(large),[100]*6)
        self.assertTrue(all(self.base.balance('stat',name)==large-100 for name in NAMES))
    def test_quest_invalid_distribution_is_atomic(self):
        with self.assertRaises(ValueError):self.quest({name:100 for name in NAMES[:-1]})
        self.assertEqual([self.base.balance('stat',name) for name in NAMES],[0]*6)
    def test_stat_mapping_rejects_float_and_negative(self):
        for problem in (1.5,-1,'23'):
            with self.assertRaises(ValueError):
                award_stats_xp_atomic_v10400(self.db,self.char,1,
                    {**{n:10 for n in NAMES},'strength':problem})
        self.assertEqual([self.base.balance('stat',name) for name in NAMES],[0]*6)
    def setup_class(self):
        self.db.__class__=type('ClassDB',(self.db.__class__,DatabaseProgressionMixin),{})
        self.db.conn.execute('CREATE TABLE class_progress(account_id INTEGER,class_name TEXT,level INTEGER NOT NULL,xp INTEGER NOT NULL,active_slot INTEGER,PRIMARY KEY(account_id,class_name))')
    def test_class_batch_two_classes_commit(self):
        self.setup_class()
        with patch('storage.db_progression.class_mastery_xp_to_next',return_value=1000):
            result=award_class_xp_batch_atomic_v10400(self.db,1,(('A',1),('B',1)),200)
        self.assertEqual([x[0] for x in result],[100,100])
        self.assertEqual([self.base.balance('class',x) for x in ('A','B')],[100,100])
    def test_class_batch_last_failure_rolls_back_first(self):
        self.setup_class()
        self.db.conn.execute("CREATE TRIGGER fail_class AFTER INSERT ON class_progress WHEN NEW.class_name='B' BEGIN SELECT RAISE(ABORT,'fail second'); END")
        with self.assertRaises(sqlite3.IntegrityError),patch('storage.db_progression.class_mastery_xp_to_next',return_value=1000):
            award_class_xp_batch_atomic_v10400(self.db,1,(('A',1),('B',1)),200)
        self.assertEqual(self.db.conn.execute('SELECT count(*) FROM class_progress').fetchone()[0],0)
        self.assertEqual([self.base.balance('class',x) for x in ('A','B')],[0,0])
    def test_class_batch_duplicate_rejected(self):
        self.setup_class()
        with self.assertRaises(ValueError):
            award_class_xp_batch_atomic_v10400(self.db,1,(('A',1),('A',2)),200)

def run():
    result=unittest.TextTestRunner(verbosity=1).run(unittest.defaultTestLoader.loadTestsFromTestCase(QuestClassAtomic))
    if not result.wasSuccessful():raise AssertionError('V104 quest/class atomic FAILED')
    return result.testsRun

if __name__=='__main__':print('V104 QUEST+CLASS:',run(),'PASS')
