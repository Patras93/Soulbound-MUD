# -*- coding: utf-8 -*-
"""v114 deployed post-100 XP continuation for character and class mastery.

The historical curve is retained for bootstrap and 1..100. Beyond 100 it
used to reach the SQLite maximum around level 2000, yielding a permanent
9e18 XP plateau. This continuation follows same-level *authored* awards,
not the old exponential curve. It never rewrites saved XP or stored levels.

Actual kills/skill use may pay different amounts, so the 500-action anchor
is a balancing target, not a claim of an exact number of kills per level.
"""
from __future__ import annotations

from core.balance_math import axis_gain

START_LEVEL = 100
ADDITIONAL_AWARD_UNITS = 500
SQLITE_SAFE_XP = 9_000_000_000_000_000_000


def requirement(kind: str, level: int, historic_at_100: int) -> int:
    if kind not in ('character', 'class'):
        raise ValueError('Only character and class mastery use this curve')
    if type(level) is not int or level <= START_LEVEL:
        raise ValueError('Continuation starts at level 101')
    if type(historic_at_100) is not int or historic_at_100 <= 0:
        raise ValueError('Missing authored requirement at level 100')
    awarded_at_start = axis_gain(kind, START_LEVEL)
    awarded_now = axis_gain(kind, level)
    if awarded_now < awarded_at_start:
        raise ArithmeticError('Award curve must be monotonic')
    result = historic_at_100 + ADDITIONAL_AWARD_UNITS * (awarded_now - awarded_at_start)
    # Never silently saturate to 9e18, because that creates an impossible
    # de facto cap without informing players or protecting stored XP.
    if result >= SQLITE_SAFE_XP:
        raise OverflowError('Progression exceeds supported SQLite XP storage range')
    return result
