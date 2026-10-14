# -*- coding: utf-8 -*-
"""EXP awards for EP and Fame, independent of next-level EXP requirements.

Only the origin/difficulty and permanent level can influence a payout.
Increasing the EXP required for leveling NEVER increases these rewards.
No XP earned before this change is altered or deleted.
"""


def exploration_point_xp_v2103(character):
    """Legacy helper: same fixed low-stage value, no character-level scaling."""
    return explorer_award_per_point_v4211(1)['character']


def explorer_award_per_point_v4211(room_stage=1):
    """Reward PER earned EP, modestly higher in objectively harder regions.

    Stage 1: 120 XP, stage 800: 220 XP per track and per stat. A room
    retains its exact EP count; no dependency on player XP or requirements.
    """
    stage = min(800, max(1, int(room_stage or 1)))
    base = 120 + min(100, (stage-1)//8)
    return {'character': base, 'soul': base, 'class_total': base, 'stat': base}


def _fame_award_for_level_v4211(level):
    """Fixed achievement-reward curve, not a percentage of next-level XP."""
    level = min(800, max(1, int(level or 1)))
    return 2500 + 30 * level * level


def fame_cap_awards_v2103(session):
    """Fame rewards for each axis; historical name kept for compatibility.

    Fame credits remain one-time per significant enemy in SQLite. The boss's
    ordinary combat XP is separate, unaffected and can be enormous.
    """
    char = session.character
    active = tuple(session.active_class_names())
    class_rewards = tuple(_fame_award_for_level_v4211(session.class_mastery_level(name)) for name in active)
    return {
        'character': _fame_award_for_level_v4211(char.character_level),
        'soul': _fame_award_for_level_v4211(char.soul_level),
        'stat': _fame_award_for_level_v4211(char.character_level),
        'class_total': max(class_rewards) if class_rewards else 0,
    }
