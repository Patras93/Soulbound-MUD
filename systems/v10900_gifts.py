# -*- coding: utf-8 -*-
"""Stabilny publiczny interfejs v109; implementacja w niezaleznych modulach.

Nazwy eksportow zachowane dla serwera, instalatora i testow monkeypatch.
"""
from systems.gifts_v109.policy import enabled, gift_kind
from systems.gifts_v109.rewards import reward_plan
from systems.gifts_v109.legacy import _legacy_claimed, _update_daily_streak
from systems.gifts_v109.payout import claim_once
from systems.gifts_v109 import delivery as _delivery

DELAY_SECONDS = _delivery.DELAY_SECONDS
TABLE = 'v109_gift_claims'

async def announce_gift(session,result):
    return await _delivery.announce_gift(session,result)

async def award_after_delay(session,account_id,character,delay=DELAY_SECONDS):
    # Zachowuje podmiane claim_once w historycznej regresji.
    return await _delivery.award_after_delay(
        session,account_id,character,delay=delay,claim_function=claim_once)

def schedule_gift(session):
    return _delivery.schedule_gift(session,award_function=award_after_delay)

async def daily_on_enter(session):
    schedule_gift(session)

async def advent_status(session,args='',*,_today=None):
    return await _delivery.advent_status(session,args,_today=_today)

def install(session_mixin):
    """Attach without changing any AST-verified v108 historical methods."""
    async def delayed_daily(self):
        return await daily_on_enter(self)
    async def info_advent(self,args='',*,_today=None):
        return await advent_status(self,args,_today=_today)
    session_mixin.daily_login_v03051=delayed_daily
    session_mixin.advent_v108=info_advent
