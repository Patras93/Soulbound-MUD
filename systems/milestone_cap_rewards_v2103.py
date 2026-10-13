# -*- coding: utf-8 -*-
"""Guaranteed full, ordinary one-award EXP cap for one-time Fame/EP events.

EXP Bank handles any event/guild overflow using existing per-axis ledgers.
Never grant extra levels, change requirements, or reduce saved XP.
"""
from systems.experience_cap_v2009 import experience_cap_v2009


def exploration_point_xp_v2103(character):
    return experience_cap_v2009('character', character.character_level)


def fame_cap_awards_v2103(session):
    char = session.character
    active = tuple(session.active_class_names())
    class_caps = tuple(experience_cap_v2009('class', session.class_mastery_level(name)) for name in active)
    return {
        'character': experience_cap_v2009('character', char.character_level),
        'soul': experience_cap_v2009('soul', char.soul_level),
        'stat': experience_cap_v2009('stat', char.character_level),
        # v2.32.18: grant_class_xp gives this amount to EACH active class.
        # Do not multiply by class count; Fame cannot mint enormous rewards.
        'class_total': max(class_caps) if class_caps else 0,
    }
