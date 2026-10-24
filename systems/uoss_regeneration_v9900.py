# -*- coding: utf-8 -*-
"""v99: bounded declarative HP-regeneration phases for scripted UOSS bosses.

No user code execution, item/EXP rewards, spawns or player writes. Bosses retain
all source abilities. Called once per authoritative enemy action, before attacks.
"""
from __future__ import annotations
import copy
from world.uoss_superbosses import UOSS_SUPERBOSS_ENCOUNTERS_V11134

ACTIVE = {}

def validate(profiles):
    if type(profiles) is not dict or len(profiles) > len(UOSS_SUPERBOSS_ENCOUNTERS_V11134):
        raise ValueError('UOSS ODNOWA: wymagany slownik istniejacych superbossow.')
    for boss, profile in profiles.items():
        if boss not in UOSS_SUPERBOSS_ENCOUNTERS_V11134:
            raise ValueError('UOSS ODNOWA: nieznany boss.')
        if type(profile) is not dict or set(profile) != {'phases'}:
            raise ValueError('UOSS ODNOWA: wymagane phases.')
        phases = profile['phases']
        if type(phases) is not list or not 1 <= len(phases) <= 5:
            raise ValueError('UOSS ODNOWA: wymagane 1-5 faz.')
        previous = 101
        for phase in phases:
            if type(phase) is not dict or set(phase) != {'below_hp', 'every', 'heal_percent', 'label'}:
                raise ValueError('Faza odnowy: below_hp, every, heal_percent, label.')
            below, every, heal = phase['below_hp'], phase['every'], phase['heal_percent']
            if type(below) is not int or not 1 <= below <= 100 or below >= previous:
                raise ValueError('Progi HP 1-100 musza malec.')
            if type(every) is not int or not 1 <= every <= 30:
                raise ValueError('Odnowa: rytm 1-30.')
            if type(heal) is not int or not 1 <= heal <= 10:
                raise ValueError('Odnowa: 1-10% maksymalnego HP.')
            label = phase['label']
            if type(label) is not str or not 1 <= len(label.strip()) <= 70 or any(ord(c) < 32 or ord(c) == 127 for c in label):
                raise ValueError('Odnowa: nazwa 1-70 znakow bez sterowania.')
            previous = below
    return True

def sync(profiles):
    validate(profiles)
    ACTIVE.clear()
    ACTIVE.update(copy.deepcopy(profiles))

def apply_regen(mob, template):
    """Return (healed:int,label:str) or (0,''). Boss-state only, one action.

    Requires a monotonic combat_turn from the authoritative combat loop.
    A guard on the mob prevents double healing if the loop is reentered.
    """
    key = template.get('uoss_unique_superboss_key', '')
    profile = ACTIVE.get(key)
    if not profile or not getattr(mob, 'alive', False):
        return (0, '')
    maximum = max(1, int(getattr(mob, 'adaptive_max_hp_v11330', 0) or getattr(mob, 'max_hp', 0) or template.get('max_hp', 1)))
    hp = int(getattr(mob, 'hp', 0) or 0)
    turn = int(getattr(mob, 'combat_turn', 0) or 0)
    if hp <= 0 or turn <= 0 or turn == getattr(mob, '_v99_regen_turn', None):
        return (0, '')
    phase = next((p for p in reversed(profile['phases']) if hp * 100 <= maximum * p['below_hp']), None)
    if not phase or turn % phase['every']:
        return (0, '')
    mob._v99_regen_turn = turn
    value = min(maximum - hp, max(1, maximum * phase['heal_percent'] // 100))
    if value <= 0:
        return (0, '')
    mob.hp = hp + value
    return (value, phase['label'])
