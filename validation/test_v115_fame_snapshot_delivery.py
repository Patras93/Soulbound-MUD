# -*- coding: utf-8 -*-
import sqlite3
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from systems.v115 import fame_queue, fame_exp_progression
from systems.v115.fame_reward_snapshot import RewardSnapshot
from systems.v115.fame_snapshot_delivery import stage_first_clear, deliver_stored_for_online_player

class Connection:
    def __init__(self): self.raw = sqlite3.connect(':memory:')
    def __getattr__(self, name): return getattr(self.raw, name)
    def deferred_commits(self):
        conn = self.raw
        class Tx:
            def __enter__(self): return conn
            def __exit__(self, t,v,tb):
                if t: conn.rollback()
                else: conn.commit()
        return Tx()

class Tests(unittest.TestCase):
    def setUp(self):
        self.conn = Connection()
        self.db = SimpleNamespace(conn=self.conn)
        self.character = SimpleNamespace(account_id=17)
        self.snap = RewardSnapshot(150, 240, 330, 80, (('Mage', 810),), 100000, False)

    def tearDown(self):
        self.conn.raw.close()

    def stage(self):
        self.assertTrue(stage_first_clear(self.conn, 17, 'Region', 'boss', 'Boss', self.snap, now=100))
        self.conn.commit()
        return self.conn.execute('SELECT due_at FROM v115_fame_delivery').fetchone()[0]

    def test_old_fame_is_preserved(self):
        self.conn.execute('CREATE TABLE fame_bosses_v1702(account_id INTEGER, region TEXT, boss_id TEXT)')
        self.conn.execute('INSERT INTO fame_bosses_v1702 VALUES(17,?,?)', ('Region','boss'))
        self.assertFalse(stage_first_clear(self.conn, 17, 'Region', 'boss', 'Boss', self.snap))
        self.assertFalse(self.conn.execute("SELECT 1 FROM sqlite_master WHERE name='v115_fame_delivery'").fetchone())

    def test_frozen_value_and_order_and_dedup(self):
        due = self.stage()
        payments=[]
        def atomic_fake(db, char, aid, region, boss_id, **kw):
            def pay(conn, _):
                conn.execute('CREATE TABLE IF NOT EXISTS test_paid(xp INTEGER)')
                conn.execute('INSERT INTO test_paid VALUES(?)', (kw['character_xp'],))
            ok=fame_queue.settle_exp(db.conn,aid,region,boss_id,pay,now=kw['now'])
            db.conn.commit()
            if ok: payments.append((kw['character_xp'],kw['soul_xp'],kw['class_xp'],kw['stat_xp']))
            return {'character':kw['character_xp']} if ok else None
        with patch.object(fame_exp_progression, 'settle_fame_exp_progression', atomic_fake):
            self.assertEqual(deliver_stored_for_online_player(self.db,self.character,17,now=due-1),[])
            self.assertEqual([v[0] for v in deliver_stored_for_online_player(self.db,self.character,17,now=due)],['exp'])
            self.assertEqual(deliver_stored_for_online_player(self.db,self.character,17,now=due+1),[])
            self.assertEqual([v[0] for v in deliver_stored_for_online_player(self.db,self.character,17,now=due+2)],['fame'])
            self.assertEqual(deliver_stored_for_online_player(self.db,self.character,17,now=due+100),[])
        self.assertEqual(payments,[(150,240,330,80)])
        self.assertEqual(self.conn.execute('SELECT COUNT(*) FROM fame_bosses_v1702').fetchone()[0],1)

    def test_orphan_queue_refuses_snapshot_replay(self):
        fame_queue.schedule_fame(self.conn,17,'Region','boss','Boss',now=100)
        with self.assertRaises(ValueError):
            stage_first_clear(self.conn,17,'Region','boss','Boss',self.snap,now=100)

    def test_missing_snapshot_refuses_payment(self):
        fame_queue.schedule_fame(self.conn,17,'Region','boss','Boss',now=100)
        due=self.conn.execute('SELECT due_at FROM v115_fame_delivery').fetchone()[0]
        with self.assertRaises(RuntimeError): deliver_stored_for_online_player(self.db,self.character,17,now=due)
        self.assertEqual(self.conn.execute('SELECT status FROM v115_fame_delivery').fetchone()[0],'WAITING')

    def test_ownership(self):
        with self.assertRaises(ValueError): deliver_stored_for_online_player(self.db,self.character,18,now=999)

    def test_retry_conflict(self):
        self.stage()
        changed=RewardSnapshot(151,240,330,80,(('Mage',810),),100000,False)
        with self.assertRaises(ValueError): stage_first_clear(self.conn,17,'Region','boss','Boss',changed,now=101)

    def test_no_soundpack(self):
        import inspect
        from systems.v115 import fame_snapshot_delivery
        self.assertNotIn('sound_events',inspect.getsource(fame_snapshot_delivery))

if __name__=='__main__': unittest.main()
