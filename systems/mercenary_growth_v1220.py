# -*- coding: utf-8 -*-
"""Persistent role progression for independently hired tavern mercenaries."""
from math import isqrt

SPECIALIZATIONS = {
    "szturm": "Szturm: silniejsze uderzenia oraz seria ciosów na wyższych poziomach",
    "obrona": "Obrona: dodatkowa osłona członka drużyny",
    "wsparcie": "Wsparcie: pomoc w leczeniu rannego członka drużyny",
}
MILESTONES = (10, 25, 50)


def mercenary_level(xp):
    """Long-term, non-capped growth, with increasingly expensive levels."""
    return 1 + isqrt(max(0, int(xp)) // 180)


def mercenary_xp_for_level(level):
    return 180 * max(0, int(level) - 1) ** 2


def mercenary_action_xp(owner_level, foe_level, boss=False):
    """The enemy and owner both matter; never a flat reward per combat action."""
    enemy = max(1, int(foe_level))
    owner = max(1, int(owner_level))
    return min(2500, 18 + enemy // 3 + min(owner, enemy) // 6 + (enemy // 4 if boss else 0))


def mercenary_attack_multiplier(level, specialization):
    bonus = min(0.20, max(0, int(level) - 1) * 0.002)
    if specialization == "szturm" and level >= 10:
        bonus += 0.08 if level < 25 else 0.13 if level < 50 else 0.18
    return 1.0 + bonus


def mercenary_unlocked(level, specialization):
    level = int(level)
    if level < 10:
        return "Umiejętność podstawowa"
    if not specialization:
        return "Dostępna specjalizacja: najemnik specjalizacja <imię> <szturm|obrona|wsparcie>"
    return ("Talent specjalizacji" if level < 25 else
            "Mistrzowska technika" if level < 50 else "Legendarna technika")
