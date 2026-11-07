# -*- coding: utf-8 -*-
"""Calendar-based v104 repeatable quests. UTC boundaries, no new quest ledger.

A completion stays blocked only within its UTC day/week. This intentionally
keeps older completed_at timestamps and completion_count exactly as recorded.
"""
from __future__ import annotations
from datetime import datetime, timedelta, timezone


def remaining_seconds(completed_at: int, cadence: str, now: int | None = None) -> int:
    """Seconds until the NEXT UTC calendar boundary after completion.

    Weekly windows begin Monday 00:00 UTC. No advantage from moving host clock
    backwards: a completion whose timestamp is in the future stays locked.
    """
    import time
    if cadence not in ("day_utc", "week_utc"):
        raise ValueError("Nieznany kalendarz odnowienia.")
    now = int(time.time()) if now is None else int(now)
    completed_at = int(completed_at)
    if completed_at <= 0:
        return 0
    completed = datetime.fromtimestamp(completed_at, timezone.utc)
    at_midnight = completed.replace(hour=0, minute=0, second=0, microsecond=0)
    if cadence == "day_utc":
        renew_at = at_midnight + timedelta(days=1)
    else:
        renew_at = at_midnight + timedelta(days=7-completed.weekday())
    return max(0, int(renew_at.timestamp()) - now)


def cadence_for_quest(quest_id: str, definition: dict) -> str | None:
    """Restrict UTC calendar to authored v104/v106 contracts, not older quests.

    Live OLC modifications to other quest fields keep their old behaviour.
    """
    # v106 rozszerza tę samą politykę UTC bez drugiego licznika nagród.
    # Inne zadania (również stare powtarzalne) zachowują stary cooldown.
    if not str(quest_id).startswith(('v10400_contract_', 'v10600_contract_')) or not definition.get('repeatable'):
        return None
    cadence = definition.get('repeat_calendar_v104')
    return cadence if cadence in ('day_utc', 'week_utc') else None
