# -*- coding: utf-8 -*-
"""Fallback per-award cap that grows above level 800, never an XP reward or requirement.

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
    # An unlimited level axis must not freeze the fallback per-award cap at 800.
    # The authoritative real-player Multi Cap is still calculated from the
    # player's owned levels; EXP Bank and Half CAP/Overcap are unchanged.
    level = max(1, int(level or 1))
    return max(100, 2 * multi_cap_level_value_v23217(level))


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
    # A lvl-950 boss is no longer "hard enough" for an uncapped lvl-1000
    # character merely because the old eligibility check stopped at 800.
    # The historical stage helper clamps combat stages to the old authored
    # level ceiling (800). Do not apply that ceiling to an explicitly
    # generated boss above level 800: unlimited players must still have an
    # eligible high-level opponent. Other legacy mob staging is unchanged.
    try:
        stage = v0190_mob_stage(template)
    except (TypeError, ValueError, OverflowError):
        # Malformed boss metadata cannot elevate an enemy to Over Cap.
        # Reject the bonus explicitly; never crash the reward path.
        return False
    if template.get('generator_level') is not None:
        try:
            stage = max(stage, max(1, int(template['generator_level'])))
        except (TypeError, ValueError, OverflowError):
            # An invalid optional generator_level is not evidence of a stronger
            # boss. Use the normal authored stage rather than granting bonus
            # EXP based on malformed metadata. This is an intentional,
            # conservative fallback, not a silently ignored exception.
            return stage >= max(1, int(player_level or 1))
    return stage >= max(1, int(player_level or 1))
