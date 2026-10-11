# -*- coding: utf-8 -*-
"""Alter Aeon inspired EXP cap per individual award (not level requirement).

Cap grows with the recipient's own progression. A significant boss challenge
can award up to 2x the normal cap. This does not alter level requirements or
already earned experience. Stat caps refer to character level (stats uncapped).
"""
from core.progression_resources import (
    character_xp_to_next, class_mastery_xp_to_next, soul_xp_to_next,
    v0190_requirement,
)

KINDS = ('character', 'soul', 'class', 'stat', 'profession', 'tool', 'skill')


def experience_cap_v2009(kind, level):
    kind = str(kind).lower()
    if kind not in KINDS:
        raise ValueError('Unknown experience kind: ' + kind)
    level = min(800, max(1, int(level or 1)))
    lookup_level = min(799, level)
    if kind == 'character':
        required = character_xp_to_next(lookup_level)
    elif kind == 'soul':
        required = soul_xp_to_next(lookup_level)
    elif kind == 'class':
        required = class_mastery_xp_to_next(lookup_level)
    else:
        required = v0190_requirement(kind, lookup_level)
    return max(100, int(required) // 3)


def capped_experience_v2009(amount, kind, level, overcap=False):
    amount = max(0, int(amount or 0))
    multiplier = 2 if overcap else 1
    return min(amount, experience_cap_v2009(kind, level) * multiplier)


def combat_overcap_v2009(template, player_level):
    """Doublecap reserved for genuinely challenging elite/boss enemies."""
    from core.progression_resources import v0190_mob_stage
    if not (template.get('boss') or template.get('world_boss') or
            template.get('crypt_boss') or template.get('astral_boss') or
            template.get('mythic_crypt_boss') or template.get('mythic_astral_boss') or
            template.get('giant_fortress_boss') or template.get('uoss_superboss')):
        return False
    return v0190_mob_stage(template) >= min(800, max(1, int(player_level or 1)))
