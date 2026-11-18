# -*- coding: utf-8 -*-
import sqlite3
import unittest
from systems.v115 import fame_queue as q
from systems.v115.fame_legacy_bridge import queue_first_clear, settle_legacy_fame

class BridgeTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        self.db.execute('CREATE TABLE balances (account_id INTEGER PRIMARY KEY, exp INTEGER)')
        self.db.execute('INSERT INTO balances VALUES(3,0)')
        self.now = 10000.0
        self.assertTrue(queue_first_clear(self.db,3,'Cmentarz','boss_a','Boss A',250,now=self.now))
        self.due=self.now+q.deterministic_delay(3,'Cmentarz','boss_a')
    def exp(self,conn,amount):
        conn.execute('UPDATE balances SET exp=exp+? WHERE account_id=3',(amount,))
    def fame(self):
        return self.db.execute('SELECT COUNT(*) FROM fame_bosses_v1702').fetchone()[0] if self.db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='fame_bosses_v1702'").fetchone() else 0
    def test_exact_order_and_no_duplicate(self):
        self.assertFalse(settle_legacy_fame(self.db,3,'Cmentarz','boss_a',now=self.due))
        self.assertTrue(q.settle_exp(self.db,3,'Cmentarz','boss_a',self.exp,now=self.due))
        self.assertFalse(settle_legacy_fame(self.db,3,'Cmentarz','boss_a',now=self.due+1))
        self.assertTrue(settle_legacy_fame(self.db,3,'Cmentarz','boss_a',now=self.due+2))
        self.assertEqual(self.fame(),1)
        self.assertEqual(self.db.execute('SELECT exp FROM balances').fetchone()[0],250)
        self.assertFalse(settle_legacy_fame(self.db,3,'Cmentarz','boss_a',now=self.due+30))
        self.assertFalse(queue_first_clear(self.db,3,'Cmentarz','boss_a','Boss A',250,now=self.due+31))
    def test_historical_award_ignored(self):
        self.db.execute('CREATE TABLE fame_bosses_v1702(account_id INTEGER,boss_id TEXT,region TEXT, PRIMARY KEY(account_id,region,boss_id))')
        self.db.execute("INSERT INTO fame_bosses_v1702 VALUES(4,'old','Kraina')")
        self.assertFalse(queue_first_clear(self.db,4,'Kraina','old','Stary',200,now=self.now))
    def test_roll_back_with_outer_transaction(self):
        self.db.commit()
        self.db.execute('BEGIN')
        self.assertTrue(q.settle_exp(self.db,3,'Cmentarz','boss_a',self.exp,now=self.due))
        self.assertTrue(settle_legacy_fame(self.db,3,'Cmentarz','boss_a',now=self.due+2))
        self.db.rollback()
        self.assertEqual(self.db.execute('SELECT exp FROM balances').fetchone()[0],0)
        self.assertEqual(q.due_events(self.db,3,now=self.due)[0][3],'WAITING')
        self.assertEqual(self.fame(),0)
    def test_restart_persists_exactly_one(self):
        self.assertTrue(q.settle_exp(self.db,3,'Cmentarz','boss_a',self.exp,now=self.due))
        self.assertTrue(settle_legacy_fame(self.db,3,'Cmentarz','boss_a',now=self.due+2))
        self.db.commit()
        reopened=sqlite3.connect(':memory:')
        reopened.executescript('\n'.join(self.db.iterdump()))
        self.assertFalse(settle_legacy_fame(reopened,3,'Cmentarz','boss_a',now=self.due+3))
        self.assertEqual(reopened.execute('SELECT COUNT(*) FROM fame_bosses_v1702').fetchone()[0],1)
    def test_no_sound_dependency(self):
        import inspect
        source=inspect.getsource(settle_legacy_fame)
        self.assertNotIn('sound_events',source)
if __name__=='__main__': unittest.main()
