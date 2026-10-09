# -*- coding: utf-8 -*-
"""Mercenary 5.0: bounded per-session per-species tactical learning.

No commands, per-action SQLite writes or invented intelligence penalties. A
mercenary learns which of its three real abilities is effective against a species.
"""
from systems.mercenary_specialists_v1240 import SPECIALISTS
from core.large_number_math import safe_success_ratio

MAX_TARGETS = 200

def memory_choice_v1250(session, role, species, suggested, turn):
    abilities = SPECIALISTS[role][2:]
    key = (role, str(species))
    memory = getattr(session, '_mercenary_memory_v1250', None)
    if not isinstance(memory, dict):
        memory = {}
        session._mercenary_memory_v1250 = memory
    if key not in memory:
        db = getattr(getattr(session, 'server', None), 'db', None)
        saved = None
        if db is not None and getattr(session, 'account_id', None) is not None:
            reader = getattr(db, 'mercenary_memory_read_v1260', None)
            if callable(reader):
                saved = reader(session.account_id, role, species)
        memory[key] = saved or {'attempts': [0, 0, 0], 'success': [0., 0., 0.]}
    values = memory[key]
    # Bounded cache, no global sharing of character combat data.
    if len(memory) > MAX_TARGETS:
        memory.pop(next(iter(memory)))
    suggested_index = abilities.index(suggested) if suggested in abilities else 0
    # Initial exploration; move to best observed ability when there is evidence.
    attempts = values['attempts']
    if min(attempts) < 2:
        choice = min(range(3), key=lambda i: (attempts[i], (i - suggested_index) % 3))
    elif turn % 7 == 0:
        choice = min(range(3), key=lambda i: attempts[i])
    else:
        choice = max(range(3), key=lambda i: values['success'][i] / max(1, attempts[i]))
    return abilities[choice], choice, key


def memory_effect_v1250(role, technique_index, template):
    """Situational technique effectiveness (not an artificial damage cap)."""
    kind = str(template.get('creature_type') or template.get('name', '')).casefold()
    if technique_index == 0:
        return 1.05
    if technique_index == 1:
        return 1.18 if (template.get('elite') or 'armor' in kind or 'pancerz' in kind) else 1.09
    return 1.20 if (template.get('boss') or template.get('world_boss') or template.get('elite') or 'smok' in kind) else 1.04


def memory_learn_v1250(session, key, index, actual_damage, potential_damage, target_hp_before):
    record = session._mercenary_memory_v1250[key]
    record['attempts'][index] += 1
    # Avoid treating killing blows clipped by remaining HP as weak abilities.
    effective = safe_success_ratio(actual_damage, min(potential_damage, target_hp_before))
    record['success'][index] += effective
    # Persistent observations. Save the first strike immediately; thereafter
    # batch every third learned action to avoid hammering SQLite each hit.
    if sum(record['attempts']) == 1 or sum(record['attempts']) % 3 == 0:
        db = getattr(getattr(session, 'server', None), 'db', None)
        writer = getattr(db, 'mercenary_memory_save_v1260', None)
        if callable(writer) and getattr(session, 'account_id', None) is not None:
            writer(session.account_id, key[0], key[1], record)
