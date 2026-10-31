# -*- coding: utf-8 -*-
"""Exclusive async kill settlements on the same SQLite connection.

Only serialises victory callbacks, not unrelated game commands. It does not
claim full database-wide isolation or complete BigNumber migration.
"""
from __future__ import annotations
import asyncio


async def run_serialized_kill_v10400(session, callback, *args, **kwargs):
    """Keep concurrent kill callbacks from overlapping SAVEPOINT stacks.

    Network sends inside a kill callback may yield while a SAVEPOINT remains
    open. This lock is stored on the database instance so different player
    sessions referencing the same DB cannot release one another's savepoints.
    Exceptions, including asyncio cancellation, release the lock and roll back
    the pending kill's savepoint.
    """
    db = session.server.db
    lock = getattr(db, '_v104_kill_settlement_lock', None)
    if lock is None:
        # No await before publishing the lock on the shared DB object.
        lock = asyncio.Lock()
        db._v104_kill_settlement_lock = lock
    task = asyncio.current_task()
    if getattr(db, '_v104_kill_settlement_owner', None) is task:
        # A single attack may synchronously settle a summoned/additional mob.
        # Re-enter the DB SAVEPOINT, not the non-reentrant asyncio.Lock.
        with db.conn.deferred_commits():
            return await callback(session, *args, **kwargs)
    async with lock:
        db._v104_kill_settlement_owner = task
        try:
            with db.conn.deferred_commits():
                return await callback(session, *args, **kwargs)
        finally:
            db._v104_kill_settlement_owner = None
