# -*- coding: utf-8 -*-
"""Soul XP continuation after level 59999, with no authored gameplay cap.

The v106 30000..59999 curve is untouched. For 60000+ its linear
increase carries forward exactly, avoiding the old 9e18 fallback.
SQLite remains a signed-64-bit store and is protected by XP balance guards.
"""
from __future__ import annotations
from systems.soul_xp_curve_v10600 import BASE_XP, FIRST_LEVEL, XP_PER_LEVEL, SAFE_INT

FIRST_UNBOUNDED_LEVEL = 60_000


def requirement(level, multiplier):
    if type(level) is not int or level < FIRST_UNBOUNDED_LEVEL:
        raise ValueError('Krzywa v114 wymaga Soul Level >= 60000.')
    if type(multiplier) not in (int, float) or not 0.1 <= multiplier <= 100:
        raise ValueError('Nieprawidlowy mnoznik Soul XP.')
    total = max(1, int(round((BASE_XP + (level - FIRST_LEVEL) * XP_PER_LEVEL) * multiplier)))
    if total > SAFE_INT:
        raise OverflowError('Progi Soul XP przekraczaja techniczny zakres SQLite.')
    return total
