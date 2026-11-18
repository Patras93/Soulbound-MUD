# -*- coding: utf-8 -*-
"""v115: modest, durable Fame payouts on an already-running server.

The loop never creates a queue, never pays old v114 credits and does not
require a soundpack. Actual kill interception is deliberately separate.
"""
from __future__ import annotations
import asyncio
import logging
import time
from systems.v115.fame_online_delivery import FameOnlineDelivery
from systems.v115.fame_repeat_rewards import pending_online_accounts as pending_repeat_accounts

LOGGER = logging.getLogger(__name__)


def pending_online_accounts(conn, *, now=None):
    """Only accounts with an ACTUALLY due phase; never create a schema.

    Prevents a pending reward from taking the combat SQLite lock every three
    seconds for the entire 60-300 second wait. After a restart, already-due
    rows are still eligible. The EXP/Fame phases remain separately gated.
    """
    now = time.time() if now is None else float(now)
    exists = conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='v115_fame_delivery'").fetchone()
    accounts = set() if not exists else {int(row[0]) for row in conn.execute(
        """SELECT DISTINCT account_id FROM v115_fame_delivery WHERE
          ((status IN ('WAITING','EXP_READY') AND due_at<=?) OR
           (status='FAME_READY' AND fame_due_at<=?))""", (now, now)
    )}
    return accounts | pending_repeat_accounts(conn, now=now)


async def fame_online_scheduler_v115(server, *, interval=3.0, delivery=None):
    """Poll due entries while sessions are online, without locking world ticks.

    Exceptions are reported; pending SQLite rows remain available for retry.
    A single delivery instance serializes the same session's ticks.
    """
    if not 1 <= interval <= 60:
        raise ValueError('Invalid scheduler interval')
    delivery = delivery or FameOnlineDelivery()
    while True:
        await asyncio.sleep(interval)
        try:
            waiting = pending_online_accounts(server.db.conn)
            if not waiting:
                continue
        except asyncio.CancelledError:
            raise
        except Exception:
            LOGGER.exception('v115 Fame scheduler could not read queue')
            continue
        seen = set()
        for session in tuple(server.sessions):
            if (getattr(session, 'closed', False)
                    or getattr(session, 'character', None) is None):
                continue
            account_id = getattr(session, 'account_id', None)
            _key = (account_id, getattr(session.character, "name", None))
            if account_id not in waiting or _key in seen:
                continue
            if getattr(session.character, 'account_id', None) != account_id:
                continue
            seen.add(_key)
            try:
                # Serialize ALL SQLite fame payouts with the same database-wide
                # v104 combat kill coordinator. A kill can be paused in an
                # `await send()` while its outer SAVEPOINT is still active.
                lock = getattr(server.db, '_v104_kill_settlement_lock', None)
                if lock is None:
                    lock = asyncio.Lock()
                    server.db._v104_kill_settlement_lock = lock
                async with lock:
                    await delivery.tick(session, limit=20)
            except asyncio.CancelledError:
                raise
            except Exception:
                LOGGER.exception('v115 Fame payout failed for account %s', account_id)
