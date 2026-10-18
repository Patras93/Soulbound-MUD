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



def explorer_award_per_point_v1001(multi_cap):
    """One earned EP rewards 100% of the *current* full Multi Cap per existing EXP axis.

    Separate character, Soul, class and stat gateways preserve the previous
    reward destinations. Professions/tools are never rewarded by exploration.
    EXP Bank remains responsible for per-axis overflow. No EXP is multiplied
    by the number of level-bearing domains contributing to Multi Cap.
    """
    reward = max(1, int(multi_cap))
    return {'character': reward, 'soul': reward, 'class_total': reward, 'stat': reward}

def _fame_award_for_level_v4211(level):
    """Fixed achievement-reward curve, not a percentage of next-level XP."""
    level = min(800, max(1, int(level or 1)))
    return 2500 + 30 * level * level


def fame_cap_awards_v2103(session):
    """v11 candidate: each UNIQUE Fame is 100% of the current Multi Cap.

    Fame is durable per canonical target and region. Professions/tools do
    not receive battle milestone XP. All awards use existing EXP Bank gates.
    """
    multi_cap = session.server.db.multi_cap_v23215(session.account_id)
    if multi_cap is None:
        raise RuntimeError('FAME: brak Multi Cap postaci')
    reward = max(1, int(multi_cap))
    # Explicitly classless historical/test sessions have no class mastery
    # axis to credit; real characters retain their full class allocation.
    classes = getattr(session, 'active_class_names', None)
    has_class = bool(classes()) if callable(classes) else True
    return {'character': reward, 'soul': reward,
            'stat': reward, 'class_total': reward if has_class else 0}
