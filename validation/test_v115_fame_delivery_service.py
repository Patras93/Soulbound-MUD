# -*- coding: utf-8 -*-
import sqlite3
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from systems.v115 import fame_queue
from systems.v115.fame_delivery_service import AwardPlan, deliver_due_for_online_player

class Conn:
    def __init__(self):
        self.c=sqlite3.connect(':memory:')
    def __getattr__(self,key): return getattr(self.c,key)
    def deferred_commits(self):
        class Context:
            def __enter__(self_): return self.c
            def __exit__(self_, t,v,tb):
                if t: self.c.rollback()
                else: self.c.commit()
        return Context()

class Tests(unittest.TestCase):
    def setUp(self):
        self.conn=Conn(); self.db=SimpleNamespace(conn=self.conn)
        self.character=SimpleNamespace(account_id=11)
        self.assertTrue(fame_queue.schedule_fame(self.conn,11,'R','B','Boss',now=100))
        self.due=self.conn.execute('SELECT due_at FROM v115_fame_delivery').fetchone()[0]
    def test_no_award_before_due(self):
        called=[]
        self.assertEqual(deliver_due_for_online_player(self.db,self.character,11,
            lambda *a: called.append(a),now=100),[])
        self.assertEqual(called,[])
    def test_reject_missing_plan_and_zero_exp(self):
        with self.assertRaises(TypeError):
            deliver_due_for_online_player(self.db,self.character,11,lambda *a: None,now=self.due)
        with self.assertRaises(ValueError):
            deliver_due_for_online_player(self.db,self.character,11,
                lambda *a: AwardPlan(0,0,0,0),now=self.due)
        self.assertEqual(self.conn.execute('SELECT status FROM v115_fame_delivery').fetchone()[0],'WAITING')
    def test_owner_guard(self):
        with self.assertRaises(ValueError):
            deliver_due_for_online_player(self.db,self.character,12,lambda *a: None,now=self.due)
    def test_order_and_exact_once_with_injected_atomic_exp(self):
        # Exercise real queue/legacy Fame adapter; mock the full Multi Cap engine
        # because it requires a character-backed production DB.
        from systems.v115 import fame_exp_progression
        def fake_settle(db, character, account_id,region,boss_id,**kw):
            def pay(conn,amount):
                conn.execute('CREATE TABLE IF NOT EXISTS credited (xp INTEGER)')
                conn.execute('INSERT INTO credited VALUES (?)',(kw['character_xp'],))
            granted=fame_queue.settle_exp(db.conn,account_id,region,boss_id,pay,now=kw['now'])
            db.conn.commit()
            return {'character':kw['character_xp']} if granted else None
        plan=lambda *_: AwardPlan(125,5,0,3)
        with patch.object(fame_exp_progression,'settle_fame_exp_progression',fake_settle):
            e=deliver_due_for_online_player(self.db,self.character,11,plan,now=self.due)
            self.assertEqual([r[0] for r in e],['exp'])
            self.assertEqual(deliver_due_for_online_player(self.db,self.character,11,plan,now=self.due+1),[])
            e=deliver_due_for_online_player(self.db,self.character,11,plan,now=self.due+2)
            self.assertEqual([r[0] for r in e],['fame'])
            self.assertEqual(deliver_due_for_online_player(self.db,self.character,11,plan,now=self.due+3),[])
        self.assertEqual(self.conn.execute('SELECT count(*) FROM credited').fetchone()[0],1)
        self.assertEqual(self.conn.execute('SELECT count(*) FROM fame_bosses_v1702').fetchone()[0],1)
    def test_missing_calculator_does_not_pay(self):
        with self.assertRaises(TypeError):
            deliver_due_for_online_player(self.db,self.character,11,None,now=self.due)
    def test_no_audio_import(self):
        import inspect
        from systems.v115 import fame_delivery_service
        self.assertNotIn('sound_events',inspect.getsource(fame_delivery_service))

if __name__=='__main__': unittest.main()
