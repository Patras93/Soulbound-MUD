# -*- coding: utf-8 -*-
"""PvE companion tactical responses without a new command, XP bar or DB table.

Only positive modifiers to the previous 100%-owner-damage mercenary algorithm.
No global world scan; caller supplies the active target and current turn.
"""
from __future__ import annotations

FINISHERS = frozenset(('lotrzyk','berserker','lucznik','nekromanta','wojownik',
                         'samuraj','gladiator'))
BREAKERS = frozenset(('mag','czarownik','psionik','inzynier','mec',
                         'korsarz','chronomanta','iluzjonista'))
GUARDIANS = frozenset(('straznik','paladyn','kaplan','druid','mnich',
                          'bard','szaman'))


def tactical_response(role, boss, hp, hp_max, sequence):
    """Return additive multiplier + tactic label at significant enemy phases."""
    ratio = max(0.0,min(1.0,float(hp)/max(1.0,float(hp_max))))
    if boss and ratio <= .25:
        if role in FINISHERS:
            return 1.12, 'Wyczute osłabienie bossa'
        if role in BREAKERS:
            return 1.10, 'Przełamanie ostatniej fazy'
        return 1.07, 'Osłona drużyny w finale'
    if boss and ratio <= .50:
        return (1.08 if role in BREAKERS else 1.05), 'Reakcja na zmianę fazy'
    if boss and ratio <= .75:
        return 1.04, 'Rozpoznanie fazy'
    if not boss and ratio <= .25 and role in FINISHERS:
        return 1.035, 'Cel osłabiony'
    return 1.0, ''
