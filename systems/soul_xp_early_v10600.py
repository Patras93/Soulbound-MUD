# -*- coding: utf-8 -*-
"""Staging v106: wczesny Soul EXP 1..799 dopasowany do realnej krzywej nagród.

Oś nagród ``balance_math.axis_gain('soul', level)`` pochodzi z v105 i
nie jest zmieniana. Wymaganie Soul Level 800 pochodzi z istniejącego
pomostu v106. Wyłącznie progi XP w jawnie włączonym trybie v106 są inne.
Nie dotyka Soul Tier, tabel SQLite, limitów Admin Live ani historii graczy.
"""
from __future__ import annotations

from core.balance_math import axis_gain
from systems.soul_xp_bridge_v10600 import requirement as _bridge_requirement

FIRST_LEVEL = 1
LAST_LEVEL = 800  # granica wyłączna
REFERENCE_LEVEL = 800


def requirement(level: int, multiplier: float) -> int:
    if type(level) is not int or not FIRST_LEVEL <= level < LAST_LEVEL:
        raise ValueError('Krzywa wczesnej Duszy v106 obejmuje poziomy 1..799.')
    # _bridge_requirement sprawdza również typ, finitość i zakres mnożnika.
    anchor = _bridge_requirement(REFERENCE_LEVEL, multiplier)
    current_reward = axis_gain('soul', level)
    anchor_reward = axis_gain('soul', REFERENCE_LEVEL)
    if not 0 < current_reward <= anchor_reward:
        raise ValueError('Niespójna krzywa nagród Soul XP.')
    # Cel: ~7,4 zwykłych nagród przypisanych do danego poziomu na awans.
    # Dzielenie całkowitoliczbowe wyklucza błąd float dla 64-bitowego XP.
    result = max(1, (anchor * current_reward + anchor_reward // 2) // anchor_reward)
    return result
