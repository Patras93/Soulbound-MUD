# -*- coding: utf-8 -*-
"""Testowe wymagania Soul XP dla krain 800–29999.

Od Soul Level 800 do 9999 mnożnik 1000 * level, następnie łagodniejsze
przejście 10000–29999 do istniejącej krzywej v106 dla 30000.

Nie zmienia nagród, zapisów postaci ani ustawień Admin Live. Na poziomach
800–10000 zachowuje istniejące procenty pasm Soul Level z v104.
Wartości 1–799 są obsługiwane w soul_xp_early_v10600.
To nie jest dowód rzeczywistego tempa progresji po Multi Cap.
"""
from __future__ import annotations

FIRST_LEVEL = 800
LAST_LEVEL = 30_000
SAFE_INT = 9_000_000_000_000_000_000


def requirement(level: int, multiplier: float) -> int:
    """Progi v106 przed nową erą, bez float-owego błędu na całych liczbach."""
    if type(level) is not int or not FIRST_LEVEL <= level < LAST_LEVEL:
        raise ValueError('Krzywa pomostowa v106 dotyczy Soul Level 800..29999.')
    if type(multiplier) not in (int, float) or not 0.1 <= multiplier <= 100:
        raise ValueError('Nieprawidłowy mnożnik wymagań Soul XP.')
    base = level * 1000 if level < 10_000 else 10_000_000 + (level - 10_000) * 500
    result = max(1, int(round(base * multiplier)))
    if result > SAFE_INT:
        raise OverflowError('Przekroczony bezpieczny limit Soul XP.')
    return result
