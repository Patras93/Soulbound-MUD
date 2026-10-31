# -*- coding: utf-8 -*-
"""End-to-end SQLite fixture: all five main kill reward axes, no TCP."""
import sqlite3
import unittest
from unittest.mock import patch
from validation.test_v10400_live_multiaxis_atomic import LiveRewards
from storage.db_progression import DatabaseProgressionMixin
from systems.combat_kill_settlement_v10400 import settle_combat_full_progression_v10400

class FullKillAtomic(LiveRewards):
    def setUp(self):
        super().setUp()
        self.db.__class__ = type('FullKillDB', (self.db.__class__, DatabaseProgressionMixin), {})
        self.db.conn.execute('CREATE TABLE class_progress(account_id INTEGER,class_name TEXT,level INTEGER NOT NULL,xp INTEGER NOT NULL,active_slot INTEGER,PRIMARY KEY(account_id,class_name))')
        self.db.conn.commit()

    def do_kill(self):
        return settle_combat_full_progression_v10400(
            self.db, self.char, 1, silver=11, gold=1, stat_xp=200,
            character_xp=300, soul_xp=200, class_xp=200,
            class_levels=(('Wojownik', 1),))

    def test_all_axes_commit_together(self):
        with patch('player.character.character_xp_to_next', return_value=100), \
             patch('storage.db_progression.class_mastery_xp_to_next', return_value=1000):
            result = self.do_kill()
        self.assertEqual(result['character'][0], 100)
        self.assertEqual(result['soul'][0], 100)
        self.assertEqual(result['classes'][0][0], 100)
        self.assertEqual(self.saved('silver','gold','character_level','character_xp','soul_level','soul_xp'),
                         (211, 0, 3, 50, 3, 9))
        self.assertEqual(self.balance('character'), 200)
        self.assertEqual(self.balance('soul'), 100)
        self.assertEqual(self.balance('class','Wojownik'), 100)
        self.assertEqual(self.balance('stat','strength'), 100)
        self.assertEqual(tuple(self.db.conn.execute('SELECT level,xp FROM class_progress WHERE account_id=1 AND class_name=?', ('Wojownik',)).fetchone()),(1,100))

    def test_failed_class_restores_all_previous_axes(self):
        self.db.conn.execute("CREATE TRIGGER reject_class BEFORE INSERT ON class_progress BEGIN SELECT RAISE(ABORT,'class failed'); END")
        with patch('player.character.character_xp_to_next', return_value=100), \
             patch('storage.db_progression.class_mastery_xp_to_next', return_value=1000), \
             self.assertRaises(sqlite3.IntegrityError):
            self.do_kill()
        self.assertEqual(self.saved('silver','gold','character_level','character_xp','soul_level','soul_xp'),
                         (100,0,2,50,2,9))
        self.assertEqual((self.char.silver,self.char.gold,self.char.character_level,self.char.character_xp,self.char.soul_level,self.char.soul_xp),
                         (100,0,2,50,2,9))
        for kind,key in (('character',''),('soul',''),('class','Wojownik'),('stat','strength')):
            self.assertEqual(self.balance(kind,key),0)

    def test_failed_soul_restores_wallet_character_and_stats(self):
        self.db.conn.execute("CREATE TRIGGER reject_soul BEFORE UPDATE OF soul_xp ON characters BEGIN SELECT RAISE(ABORT,'soul failed'); END")
        with patch('player.character.character_xp_to_next', return_value=100), \
             self.assertRaises(sqlite3.IntegrityError):
            self.do_kill()
        self.assertEqual((self.char.silver,self.char.gold,self.char.character_level,self.char.soul_level), (100,0,2,2))
        self.assertEqual(self.balance('character'),0)
        self.assertEqual(self.balance('stat','strength'),0)

    def test_invalid_class_preflight_does_not_change_wallet(self):
        with self.assertRaises(ValueError):
            settle_combat_full_progression_v10400(self.db,self.char,1,silver=1,class_xp=20)
        self.assertEqual(self.char.silver,100)
        self.assertEqual(self.saved('silver'),(100,))

    def test_invalid_big_soul_keeps_everything(self):
        self.char.soul_xp=2**63-5
        from types import MethodType
        def soul_without_level(c, paid, **kwargs):
            c.soul_xp += paid
            return []
        self.char.add_soul_xp=MethodType(soul_without_level,self.char)
        with patch('player.character.character_xp_to_next', return_value=100), \
             patch('storage.db_progression.class_mastery_xp_to_next', return_value=1000), \
             self.assertRaises(OverflowError):
            self.do_kill()
        self.assertEqual(self.char.soul_xp,2**63-5)
        self.assertEqual(self.char.silver,100)
        self.assertEqual(self.balance('stat','strength'),0)
        self.assertEqual(self.balance('character'),0)

def run():
    names=[n for n in unittest.defaultTestLoader.getTestCaseNames(FullKillAtomic)
           if n.startswith(('test_all_axes_','test_failed_class_','test_failed_soul_',
                            'test_invalid_class_','test_invalid_big_soul_'))]
    outcome=unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(FullKillAtomic(n) for n in names))
    if not outcome.wasSuccessful():
        raise AssertionError('Full combat atomic suite failed')
    return outcome.testsRun

if __name__ == '__main__':
    print('V104 full combat atomic:',run(),'PASS')
