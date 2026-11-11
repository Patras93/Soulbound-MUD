"""Zasady daty i zgody na automatyczne prezenty."""
from __future__ import annotations
import datetime as dt

def enabled():
    """v112 only: no historical staging flags or old activators can issue gifts."""
    from core.bootstrap_economy_professions import VERSION
    if VERSION != '112.00.0':
        return False
    from systems.v11200_activation import enabled as release_enabled
    return bool(release_enabled())

def gift_kind(day):
    if not isinstance(day, dt.date) or isinstance(day, dt.datetime):
        raise TypeError('gift_kind: expected date')
    return 'advent' if day.month == 12 else 'daily'
