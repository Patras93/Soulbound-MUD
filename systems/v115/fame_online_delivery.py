# -*- coding: utf-8 -*-
"""v115: serialized, reconnect-safe ONLINE delivery driver.

This is an opt-in host adapter, not an automatic combat/login hook. A host
scheduler must call tick(session), and must not invoke it inside an already
open gameplay transaction. Messages are emitted only after durable settlement.
No audio or soundpack imports.
"""
from __future__ import annotations

import asyncio
import weakref
from systems.v115.fame_snapshot_delivery import deliver_stored_for_online_player


class FameOnlineDelivery:
    def __init__(self, *, settle=deliver_stored_for_online_player):
        self._settle = settle
        self._locks = weakref.WeakKeyDictionary()

    async def tick(self, session, *, now=None, limit=20):
        """Process due rewards for one authenticated, live session.

        Use the live character object under a session-specific asyncio.Lock.
        All durable writes are performed by the injected settlement callback.
        A failure propagates: no premature success message is sent.
        """
        if session is None or getattr(session, 'character', None) is None:
            raise ValueError('Online character required')
        if getattr(session, 'account_id', None) != getattr(session.character, 'account_id', None):
            raise ValueError('Online account and character mismatch')
        if not callable(getattr(session, 'send', None)):
            raise TypeError('Authenticated session must support send')
        if not 1 <= limit <= 100:
            raise ValueError('Invalid batch limit')
        lock = self._locks.setdefault(session, asyncio.Lock())
        async with lock:
            # Session may have logged out while awaiting the lock.
            if getattr(session, 'character', None) is None or (
                session.account_id != session.character.account_id
            ):
                return []
            events = self._settle(session.server.db, session.character,
                                  session.account_id, now=now, limit=limit)
            # The settlement method returns ONLY after committing successfully.
            # Never claim a payout before this point.
            for event in events:
                phase, region, boss_id, boss_name, amount = event
                if phase == 'exp':
                    await session.send('FAME MOB: zaległy EXP za ' + str(boss_name)
                                       + ' został rozliczony.')
                elif phase == 'fame':
                    await session.send('FAMA: +1 za ' + str(boss_name)
                                       + ' (' + str(region) + ').')
                else:
                    raise ValueError('Unexpected Fame delivery phase')
            return events
