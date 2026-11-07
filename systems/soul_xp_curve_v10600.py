# -*- coding: utf-8 -*-
"""v106: osobne wymagania Soul XP wyłącznie dla poziomów nowej ery 30000+.

W v106 wartości 1..799 reguluje pomost wczesny, 800..29999 pomost środkowy.
Bez SOULBOUND_V106_STAGING wszystkie poziomy pozostają historyczne.
Staging-only; korzysta z istniejącego SOUL_XP_REQUIREMENT_MULTIPLIER.
Nie zmienia żadnej postaci, progu Soul Tier ani bazy SQLite.
"""
from __future__ import annotations

FIRST_LEVEL = 30_000
LAST_LEVEL = 60_000
BASE_XP = 20_000_000
XP_PER_LEVEL = 2_000
SAFE_INT = 9_000_000_000_000_000_000


def requirement(level, multiplier):
    """Nowy liniowy próg: ~3-8 zwykłych mobów na poziom wg szablonów.

    Nie jest to dowód czasu walk ani realnych wypłat po Multi Cap.
    """
    if type(level) is not int or not FIRST_LEVEL <= level < LAST_LEVEL:
        raise ValueError('Krzywa v106 dotyczy Soul Level 30000..59999.')
    if type(multiplier) not in (int,float) or not 0.1 <= multiplier <= 100:
        raise ValueError('Nieprawidłowy mnożnik wymagań Soul XP.')
    amount=(BASE_XP + (level-FIRST_LEVEL)*XP_PER_LEVEL) * multiplier
    result=max(1,int(round(amount)))
    if result > SAFE_INT:raise OverflowError('Techniczny limit XP dla v106.')
    return result
