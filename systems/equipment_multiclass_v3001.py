# -*- coding: utf-8 -*-
"""Supplementary crossover bonuses for already owned and newly generated EQ.

Bonuses are computed from existing definitions at equip time: no catalog/SQLite
changes, no new item identifiers, and no replacement of authored stats.
"""
from __future__ import annotations

from core.classes_skills import CLASSES

_CLASS_TYPES_V3001 = {name: category for name, category, _weapon, _base in CLASSES}


def crossover_bonus_v3001(item):
    """Return ({stat: bonus}, {attack-channel: bonus}) for one equipable item.

    Crossover stats are 20% of the item's leading stat budget (per opposite
    stat), and the missing offensive channel is 30% of authored base power.
    Non-offensive armor uses defense as a modest baseline instead. Does not
    multiply original stats or properties and never modifies source records.
    """
    if not isinstance(item, dict) or item.get('type') != 'armor' or not item.get('slot'):
        return {}, {}
    stats = dict(item.get('stats') or {})
    for key, value in (item.get('soulbound_balance_stats') or {}).items():
        stats[key] = int(stats.get(key, 0) or 0) + int(value or 0)
    affix = str(item.get('affix') or '')
    if affix in ('strength','dexterity','intelligence','willpower'):
        stats[affix] = int(stats.get(affix,0) or 0) + max(0,int(item.get('affix_amount',0) or 0))
    phys = sum(max(0,int(stats.get(k,0) or 0)) for k in ('strength','dexterity'))
    magic = sum(max(0,int(stats.get(k,0) or 0)) for k in ('intelligence','willpower'))
    attack = max(0,int(item.get('attack',0) or 0))
    magic_attack = max(0,int(item.get('magic_attack',0) or 0))
    required_class = str(item.get('required_class') or '')
    if required_class:
        orientation = _CLASS_TYPES_V3001.get(required_class, "physical")
    elif phys > magic * 1.25:
        orientation = 'physical'
    elif magic > phys * 1.25:
        orientation = 'magic'
    elif phys == magic == 0:
        orientation = 'physical' if attack >= magic_attack else 'magic'
    elif phys == magic and attack != magic_attack:
        orientation = 'physical' if attack > magic_attack else 'magic'
    else:
        # Truly hybrid equipment already supports both styles.
        orientation = 'hybrid'
    defense = max(0,int(item.get('defense',0) or 0))
    if orientation == 'physical':
        budget = max(phys, attack, max(1, defense // 2))
        value = max(1, round(budget * 0.20))
        # Preserve authored INT/WILL bonuses; add only an explicit crossover.
        attack_value = max(1,round((attack or max(1,defense//2)) * 0.30))
        return {'intelligence':value,'willpower':value}, {'magic_attack':attack_value}
    if orientation == 'magic':
        budget = max(magic, magic_attack, max(1, defense // 2))
        value = max(1, round(budget * 0.20))
        attack_value = max(1,round((magic_attack or max(1,defense//2)) * 0.30))
        return {'strength':value,'dexterity':value}, {'attack':attack_value}
    return {}, {}


def crossover_text_v3001(item):
    """Text-only description usable by NVDA in 'eq info'."""
    stats, power = crossover_bonus_v3001(item)
    if not stats and not power:
        return ''
    labels = {'strength':'Siła','dexterity':'Zręczność','intelligence':'Inteligencja','willpower':'Siła Woli',
              'attack':'Attack','magic_attack':'Magic Attack'}
    entries = [f'{labels[k]} +{v}' for k,v in {**stats,**power}.items()]
    return 'MultiClass EQ: ' + ', '.join(entries) + '.'
