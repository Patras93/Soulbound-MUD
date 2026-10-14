# -*- coding: utf-8 -*-
"""Fallback cap of a single award, never an XP reward or level requirement.

In real play, account-wide Multi Cap is authoritative. Legacy isolated
SQLite fixtures without character progression use this stable level-only
fallback instead of a fraction of the ever-changing next-level XP threshold.
"""
from systems.multi_cap_v23215 import multi_cap_level_value_v23217

KINDS = ('character', 'soul', 'class', 'stat', 'profession', 'tool', 'skill')


def experience_cap_v2009(kind, level):
    kind = str(kind).lower()
    if kind not in KINDS:
        raise ValueError('Unknown experience kind: ' + kind)
    level = min(800, max(1, int(level or 1)))
    return max(100, multi_cap_level_value_v23217(level))


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
