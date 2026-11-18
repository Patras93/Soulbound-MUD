# -*- coding: utf-8 -*-
import asyncio
import sqlite3
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from systems.v115.fame_online_scheduler import pending_online_accounts, fame_online_scheduler_v115

class FameSchedulerV115Tests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.db=sqlite3.connect(':memory:')
    def tearDown(self):
        self.db.close()

    async def test_no_schema_on_fresh_database(self):
        self.assertEqual(pending_online_accounts(self.db),set())
        self.assertEqual(self.db.execute("SELECT count(*) FROM sqlite_master WHERE name='v115_fame_delivery'").fetchone()[0],0)

    async def test_filters_done(self):
        from systems.v115.fame_queue import ensure_schema
        ensure_schema(self.db)
        self.db.execute("INSERT INTO v115_fame_delivery(account_id,region,boss_id,boss_name,due_at,created_at,status) VALUES(1,'a','b','boss',0,0,'WAITING'),(2,'a','b','boss',0,0,'DONE')")
        self.assertEqual(pending_online_accounts(self.db),{1})

    async def test_not_due_future_first_fame_and_fame_gap(self):
        from systems.v115.fame_queue import ensure_schema
        ensure_schema(self.db)
        self.db.execute("""INSERT INTO v115_fame_delivery
            (account_id,region,boss_id,boss_name,due_at,created_at,status)
            VALUES(1,'r','first','Fame',300,0,'WAITING')""")
        self.db.execute("""INSERT INTO v115_fame_delivery
            (account_id,region,boss_id,boss_name,due_at,fame_due_at,created_at,status)
            VALUES(2,'r','second','Fame',100,302,0,'FAME_READY')""")
        self.assertEqual(pending_online_accounts(self.db,now=299),set())
        self.assertEqual(pending_online_accounts(self.db,now=300),{1})
        self.assertEqual(pending_online_accounts(self.db,now=301),{1})
        self.assertEqual(pending_online_accounts(self.db,now=302),{1,2})

    async def test_repeat_due_filter_and_done_exclusion(self):
        from systems.v115.fame_repeat_rewards import ensure_schema
        ensure_schema(self.db)
        for token, aid, due, status in (
                ('a',3,301,'PENDING'), ('b',4,300,'PENDING'),
                ('c',5,10,'DONE')):
            self.db.execute("""INSERT INTO v115_fame_repeat_exp
                (kill_token,account_id,character_name,region,boss_id,
                 boss_name,snapshot,due_at,created_at,status)
                VALUES (?,?,?,?,?,?,?,?,?,?)""",
                (token,aid,'Test','r','b','Boss','{}',due,0,status))
        self.assertEqual(pending_online_accounts(self.db,now=299),set())
        self.assertEqual(pending_online_accounts(self.db,now=300),{4})
        self.assertEqual(pending_online_accounts(self.db,now=301),{3,4})

    async def test_online_only_and_deduplicates_accounts(self):
        from systems.v115.fame_queue import ensure_schema
        ensure_schema(self.db)
        self.db.execute("INSERT INTO v115_fame_delivery(account_id,region,boss_id,boss_name,due_at,created_at,status) VALUES(1,'a','b','boss',0,0,'WAITING')")
        class FakeDelivery:
            def __init__(self): self.calls=[]
            async def tick(self,s,limit=20): self.calls.append(s.account_id)
        delivery=FakeDelivery()
        s1=SimpleNamespace(account_id=1,character=SimpleNamespace(account_id=1),closed=False)
        s2=SimpleNamespace(account_id=2,character=SimpleNamespace(account_id=2),closed=False)
        server=SimpleNamespace(db=SimpleNamespace(conn=self.db),sessions=[s1,s1,s2])
        real_sleep=asyncio.sleep
        calls=0
        async def one_tick(seconds):
            nonlocal calls
            calls+=1
            if calls>1: raise asyncio.CancelledError()
            await real_sleep(0)
        with patch('systems.v115.fame_online_scheduler.asyncio.sleep',side_effect=one_tick):
            with self.assertRaises(asyncio.CancelledError):
                await fame_online_scheduler_v115(server, interval=1,delivery=delivery)
        self.assertEqual(delivery.calls,[1])

    async def test_reject_invalid_interval(self):
        with self.assertRaises(ValueError):
            await fame_online_scheduler_v115(None,interval=0)

if __name__=='__main__': unittest.main()
