# -*- coding: utf-8 -*-
import sqlite3
import unittest
from systems.v115.fame_queue import (
    deterministic_delay, ensure_schema, schedule_fame, due_events,
    mark_exp_settled, mark_fame_settled, MIN_DELAY_SECONDS, MAX_DELAY_SECONDS,
)

class DeferredFameTests(unittest.TestCase):
    def setUp(self):
        self.db=sqlite3.connect(':memory:')
        ensure_schema(self.db)

    def tearDown(self): self.db.close()

    def test_delay_range_and_stability(self):
        for i in range(1000):
            d=deterministic_delay(i,'kraina','boss')
            self.assertTrue(MIN_DELAY_SECONDS<=d<=MAX_DELAY_SECONDS)
            self.assertEqual(d,deterministic_delay(i,'kraina','boss'))

    def test_delayed_order_persistence_and_duplicate(self):
        self.assertTrue(schedule_fame(self.db,8,'Astral','boss_1','Tytan',now=100))
        self.assertFalse(schedule_fame(self.db,8,'Astral','boss_1','Tytan',now=100))
        self.assertEqual(due_events(self.db,8,now=159),[])
        self.assertFalse(mark_exp_settled(self.db,8,'Astral','boss_1',now=159))
        self.assertEqual(len(due_events(self.db,8,now=401)),1)
        self.assertTrue(mark_exp_settled(self.db,8,'Astral','boss_1',now=401))
        self.assertFalse(mark_fame_settled(self.db,8,'Astral','boss_1',now=402))
        self.assertEqual(due_events(self.db,8,now=402),[])
        self.assertEqual(due_events(self.db,8,now=403)[0][3],'FAME_READY')
        self.assertTrue(mark_fame_settled(self.db,8,'Astral','boss_1',now=403))
        self.assertFalse(mark_fame_settled(self.db,8,'Astral','boss_1',now=404))
        self.assertEqual(due_events(self.db,8,now=9999),[])

    def test_transaction_restart(self):
        self.db.execute('BEGIN')
        schedule_fame(self.db,2,'Krypta','final','Straznik',now=5)
        self.db.commit()
        self.assertEqual(len(due_events(self.db,2,now=400)),1)

    def test_no_audio_dependency(self):
        from systems.v115 import fame_queue
        self.assertNotIn('sound_events',fame_queue.__dict__)

if __name__=='__main__': unittest.main()
