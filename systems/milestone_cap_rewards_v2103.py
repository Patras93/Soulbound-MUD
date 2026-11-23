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



# v116.00.53: Multi Cap is the maximum allowed PER AWARD, never the default
# value of every milestone. Full-cap EP/Fame created a feedback loop: stronger
# stats raised the cap, and each EP then granted the whole larger cap to all
# stats, class, character and Soul. Use bounded FRACTIONS for future awards.
# Do not change the legacy Multi Cap curve, EXP Bank or any earned XP.
V11653_EP_CAP_PERCENT = 5
V11653_FAME_CAP_PERCENT = 10


def milestone_payout_from_cap_v11653(multi_cap, percent):
    cap = max(1, int(multi_cap))
    fraction = max(1, min(100, int(percent)))
    return min(cap, max(1, (cap * fraction + 99) // 100))


def explorer_award_per_point_v1001(multi_cap):
    """One earned EP pays 5% of Multi Cap independently to existing axes.

    No duplicate profession/tool EXP, no account data migration or bank erase.
    """
    reward = milestone_payout_from_cap_v11653(multi_cap, V11653_EP_CAP_PERCENT)
    return {'character': reward, 'soul': reward, 'class_total': reward, 'stat': reward}

def _fame_award_for_level_v4211(level):
    """Fixed achievement-reward curve, not a percentage of next-level XP."""
    level = min(800, max(1, int(level or 1)))
    return 2500 + 30 * level * level


def fame_cap_awards_v2103(session):
    """Each UNIQUE Fame pays a bounded 10% of the current Multi Cap.

    Fame remains durable per canonical target/region; this changes ONLY
    FUTURE unissued awards, never completed Fame or existing EXP balances.
    """
    if getattr(session.server.db, '_uncapped_awards_v11664', False):
        # Provisional Fame-by-level reward, no CAP dependency.
        from systems.independent_milestone_xp_v11664 import fame_xp_per_first_v11664
        level = max(1, int(session.character.character_level))
        reward = fame_xp_per_first_v11664(level)
        classes = getattr(session, 'active_class_names', None)
        has_class = bool(classes()) if callable(classes) else True
        return {'character': reward, 'soul': reward, 'stat': reward,
                'class_total': reward if has_class else 0}
    multi_cap = session.server.db.multi_cap_v23215(session.account_id)
    if multi_cap is None:
        raise RuntimeError('FAME: brak Multi Cap postaci')
    reward = milestone_payout_from_cap_v11653(multi_cap, V11653_FAME_CAP_PERCENT)
    # Explicitly classless historical/test sessions have no class mastery
    # axis to credit; real characters retain their full class allocation.
    classes = getattr(session, 'active_class_names', None)
    has_class = bool(classes()) if callable(classes) else True
    return {'character': reward, 'soul': reward,
            'stat': reward, 'class_total': reward if has_class else 0}
