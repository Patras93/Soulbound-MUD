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


def historical_continuation_v11403(level, historic_level_800):
    """Keep v113's Soul-XP difficulty after 800 without a 9e18 flatline.

    A slow linear extension avoids reward/requirement jumps and remains O(1).
    Technical overflow is reported instead of corrupting a SQLite int64.
    """
    if type(level) is not int or level <= 800:
        raise ValueError('Kontynuacja v114.00.3 wymaga Soul Level > 800.')
    if type(historic_level_800) is not int or historic_level_800 <= 0:
        raise ValueError('Nieprawidlowy historyczny prog Soul XP 800.')
    # One million levels of growth fit within the supported integer range at
    # the current authored baseline; do not round via float at high levels.
    step = max(1, historic_level_800 // 100_000)
    required = historic_level_800 + (level - 800) * step
    if required > SAFE_INT:
        raise OverflowError('Progi Soul XP przekraczaja techniczny zakres SQLite.')
    return required
