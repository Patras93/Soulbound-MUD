# -*- coding: utf-8 -*-
"""Two parallel kill callbacks must never overlap SQLite SAVEPOINT scopes."""
from __future__ import annotations
import asyncio
import sqlite3
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from systems.kill_transaction_coordinator_v10400 import run_serialized_kill_v10400
from storage.database import _DeferredCommitConnection


class ConcurrentKillSettlement(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='sb104_kill_lock_')
        self.path = str(Path(self.temp.name) / 'case.sqlite')
        self.raw = sqlite3.connect(self.path)
        self.conn = _DeferredCommitConnection(self.raw)
        self.conn.execute('CREATE TABLE payout (recipient INTEGER NOT NULL, amount INTEGER NOT NULL)')
        self.conn.commit()
        self.db = SimpleNamespace(conn=self.conn)
        self.session = SimpleNamespace(server=SimpleNamespace(db=self.db))

    def tearDown(self):
        self.raw.close()
        self.temp.cleanup()

    def persisted(self):
        with sqlite3.connect(self.path) as check:
            return check.execute('SELECT recipient,amount FROM payout ORDER BY recipient').fetchall()

    async def test_concurrent_kills_are_serialised(self):
        first_started = asyncio.Event()
        release_first = asyncio.Event()
        second_entered = asyncio.Event()

        async def first(_):
            self.conn.execute('INSERT INTO payout VALUES (1,100)')
            self.conn.commit()
            first_started.set()
            await release_first.wait()

        async def second(_):
            second_entered.set()
            self.conn.execute('INSERT INTO payout VALUES (2,200)')
            self.conn.commit()

        a = asyncio.create_task(run_serialized_kill_v10400(self.session, first))
        await asyncio.wait_for(first_started.wait(), 2)
        b = asyncio.create_task(run_serialized_kill_v10400(self.session, second))
        await asyncio.sleep(0)
        self.assertFalse(second_entered.is_set(), 'Other kill entered while first holds SAVEPOINT')
        self.assertEqual(self.persisted(), [])
        release_first.set()
        await asyncio.wait_for(asyncio.gather(a,b), 2)
        self.assertTrue(second_entered.is_set())
        self.assertEqual(self.persisted(), [(1,100),(2,200)])
        self.assertEqual(self.conn._defer_depth, 0)

    async def test_failed_first_kill_cannot_rollback_other_kill(self):
        first_started=asyncio.Event()
        release_first=asyncio.Event()
        async def first(_):
            self.conn.execute('INSERT INTO payout VALUES (1,100)')
            self.conn.commit()
            first_started.set()
            await release_first.wait()
            raise RuntimeError('forced kill failure')
        async def second(_):
            self.conn.execute('INSERT INTO payout VALUES (2,200)')
            self.conn.commit()
        a=asyncio.create_task(run_serialized_kill_v10400(self.session, first))
        await asyncio.wait_for(first_started.wait(),2)
        b=asyncio.create_task(run_serialized_kill_v10400(self.session, second))
        await asyncio.sleep(0)
        release_first.set()
        with self.assertRaisesRegex(RuntimeError, 'forced kill failure'):
            await asyncio.wait_for(a,2)
        await asyncio.wait_for(b,2)
        self.assertEqual(self.persisted(),[(2,200)])
        self.assertEqual(self.conn._defer_depth,0)

    async def test_nested_kill_on_same_task_does_not_deadlock(self):
        async def inner(_):
            self.conn.execute('INSERT INTO payout VALUES (2,200)')
            self.conn.commit()
        async def outer(_):
            self.conn.execute('INSERT INTO payout VALUES (1,100)')
            await run_serialized_kill_v10400(self.session, inner)
            self.conn.commit()
        await asyncio.wait_for(run_serialized_kill_v10400(self.session, outer), 2)
        self.assertEqual(self.persisted(), [(1,100),(2,200)])
        self.assertEqual(self.conn._defer_depth,0)
        self.assertIsNone(getattr(self.db,'_v104_kill_settlement_owner',None))

    async def test_nested_failure_only_rolls_back_inner_scope(self):
        async def inner(_):
            self.conn.execute('INSERT INTO payout VALUES (2,200)')
            self.conn.commit()
            raise ValueError('inner failure')
        async def outer(_):
            self.conn.execute('INSERT INTO payout VALUES (1,100)')
            try:
                await run_serialized_kill_v10400(self.session, inner)
            except ValueError:  # AUDIT_INTENTIONAL_PASS: test verifies rolled-back inner failure
                pass
            self.conn.commit()
        await asyncio.wait_for(run_serialized_kill_v10400(self.session, outer), 2)
        self.assertEqual(self.persisted(),[(1,100)])
        self.assertEqual(self.conn._defer_depth,0)

    async def test_cancellation_does_not_leave_open_savepoint(self):
        entered=asyncio.Event()
        async def blocked(_):
            self.conn.execute('INSERT INTO payout VALUES (1,100)')
            self.conn.commit()
            entered.set()
            await asyncio.Event().wait()
        task=asyncio.create_task(run_serialized_kill_v10400(self.session, blocked))
        await asyncio.wait_for(entered.wait(),2)
        task.cancel()
        with self.assertRaises(asyncio.CancelledError):
            await task
        self.assertEqual(self.persisted(),[])
        self.assertEqual(self.conn._defer_depth,0)
        async def after(_):
            self.conn.execute('INSERT INTO payout VALUES (3,300)')
            self.conn.commit()
        await asyncio.wait_for(run_serialized_kill_v10400(self.session, after),2)
        self.assertEqual(self.persisted(),[(3,300)])


if __name__=='__main__':
    unittest.main()
