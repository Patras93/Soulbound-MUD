# -*- coding: utf-8 -*-
import sqlite3,tempfile,os,unittest
from systems.v115 import objective_progress as p
from systems.v115.content_catalog import quest_catalog,achievement_catalog

class ProgressTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.path=os.path.join(self.temp.name,'v115.sqlite')
        self.db=sqlite3.connect(self.path)
        p.ensure_schema(self.db)
        self.q=quest_catalog()[0]
        self.a=next(a for a in achievement_catalog() if a.region==self.q.region and a.objective==self.q.objective)
    def tearDown(self):
        self.db.close();self.temp.cleanup()
    def test_duplicate_event(self):
        self.assertTrue(p.record_event(self.db,1,'kill:1',self.q.region,self.q.objective,10))
        self.assertFalse(p.record_event(self.db,1,'kill:1',self.q.region,self.q.objective,10))
        self.assertEqual(p.total(self.db,1,self.q.region,self.q.objective),10)
    def test_accounts_separated(self):
        p.record_event(self.db,1,'e',self.q.region,self.q.objective,10)
        self.assertEqual(p.total(self.db,2,self.q.region,self.q.objective),0)
    def test_restart(self):
        p.record_event(self.db,1,'e',self.q.region,self.q.objective,10)
        self.db.commit(); self.db.close(); self.db=sqlite3.connect(self.path)
        self.assertEqual(p.total(self.db,1,self.q.region,self.q.objective),10)
    def test_rollback(self):
        self.db.execute('BEGIN')
        p.record_event(self.db,1,'e',self.q.region,self.q.objective,10)
        self.db.rollback()
        self.assertEqual(p.total(self.db,1,self.q.region,self.q.objective),0)
    def test_claim_once_and_rollback(self):
        p.record_event(self.db,1,'e',self.q.region,self.q.objective,100)
        self.db.commit()
        self.db.execute('BEGIN')
        self.assertTrue(p.mark_claimed(self.db,1,self.q.key,0))
        self.db.rollback()
        self.assertTrue(p.mark_claimed(self.db,1,self.q.key,0))
        self.assertFalse(p.mark_claimed(self.db,1,self.q.key,0))
    def test_not_early(self):
        self.assertFalse(p.mark_claimed(self.db,1,self.q.key,0))
    def test_achievement_cycles(self):
        p.record_event(self.db,1,'e',self.a.region,self.a.objective,self.a.threshold*3)
        self.assertTrue(p.mark_claimed(self.db,1,self.a.key,0))
        self.assertTrue(p.mark_claimed(self.db,1,self.a.key,1))
        self.assertTrue(p.mark_claimed(self.db,1,self.a.key,2))
        self.assertFalse(p.mark_claimed(self.db,1,self.a.key,3))
    def test_reject_invalid(self):
        with self.assertRaises(ValueError):p.record_event(self.db,1,'fake','bad','bad')
        with self.assertRaises(ValueError):p.record_event(self.db,1,'a',self.q.region,self.q.objective,-1)
    def test_no_audio(self):
        import inspect
        self.assertNotIn('sound_events',inspect.getsource(p))
    def test_catalog_sizes(self):
        self.assertEqual(len(p.QUESTS),5000)
        self.assertEqual(len(p.ACHIEVEMENTS),2000)
if __name__=='__main__':unittest.main()
