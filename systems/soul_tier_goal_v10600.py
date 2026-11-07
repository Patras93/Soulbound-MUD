# -*- coding: utf-8 -*-
"""v106: odczytowy komunikat o realnym limicie Duszy.

Nie podnosi limitów i nie zapisuje konfiguracji Admin Live. Działa tylko po
jawnej aktywacji testowego v106, z zachowaniem ustawień właściciela.
"""
from __future__ import annotations


def readiness(soul_tier, soul_level, configured_cap, thresholds):
    """Zwraca problem następnego Tieru albo None; bez side effects."""
    tier = int(soul_tier)
    level = int(soul_level)
    if tier < 1 or tier > len(thresholds):
        raise ValueError('Nieprawidłowy Soul Tier.')
    if tier == len(thresholds):
        return None
    next_tier = tier + 1
    required = int(thresholds[tier])
    if required <= level:
        return None  # trzeba ukończyć próbę / unlock, nie zmieniać limitu
    if configured_cap is None or int(configured_cap) >= required:
        return None
    maximum = int(configured_cap)
    return {
        'tier': next_tier,
        'required': required,
        'configured': maximum,
        'message': (
            f'Uwaga: limit Soul Level {maximum} jest niższy niż próg {required} '
            f'dla Tieru {next_tier}. Soul XP pozostaje odłożony. '
            f'Administrator może ustawić: admin live limity ustaw dusza {required} POTWIERDZAM '
            f'lub bezlimitu. Ustawienia nie zostały zmienione.'
        ),
    }


def current_warning(character, thresholds):
    """Odczytuje bieżące limity Admin Live, nie zmienia plików ani sesji."""
    from core.live_level_caps_v5200 import cap
    result = readiness(character.soul_tier, character.soul_level, cap('dusza'), thresholds)
    return result['message'] if result else ''
