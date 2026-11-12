"""Zasady daty i zgody na automatyczne prezenty."""
from __future__ import annotations
import datetime as dt

def enabled():
    """Approved current release only; no historical activation code."""
    from core.bootstrap_economy_professions import VERSION
    if tuple(map(int,VERSION.split('.'))) < (112,0,0):
        return False
    from systems.runtime_activation import enabled as release_enabled
    return bool(release_enabled())

def gift_kind(day):
    if not isinstance(day, dt.date) or isinstance(day, dt.datetime):
        raise TypeError('gift_kind: expected date')
    return 'advent' if day.month == 12 else 'daily'
