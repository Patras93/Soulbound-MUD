# -*- coding: utf-8 -*-
"""v116.00.64: LIVE source balance after retiring hirelings and EXP CAP.

No per-award CAP, no bank, no hard entry gate. The source reward is
computed by the recipient's real progress and the authored encounter stage.
Legacy isolated test fixtures retain their previous payout model.
"""
from __future__ import annotations

import math

SAFE_XP = 9_000_000_000_000_000_000
RANK_TENTHS = {'normal': 10, 'elite': 18, 'rare': 27,
               'mini': 42, 'boss': 75, 'world_boss': 110}


def _fraction_of_requirement(needed, basis_points, *, factor=1.0):
    """Base XP formula, NOT a cap on an arbitrarily large incoming award."""
    needed=max(1,int(needed or 1))
    return min(SAFE_XP,max(1,int(round(needed*max(1,int(basis_points))*factor/10000.0))))


def content_relevance_v11664(content_stage, recipient_level):
    """Discourage trivial old zones without rewarding risky power-level skips."""
    level=max(1,int(recipient_level))
    stage=max(1,int(content_stage or level))
    ratio=(stage+12)/(level+12)
    if ratio<1:
        return max(.06,ratio**1.4)
    return min(1.30,1.0+min(100,stage-level)*.003)


def kills_per_level_target_v11664(character_level):
    """~130 low-level, ~200 at lv92, ~400 at high levels, before boosts."""
    level=max(1,int(character_level))
    basis_points=max(24,88-(min(level,180)*42)//100-(max(0,level-180)//80))
    return 10000/basis_points


def live_kill_reward_v11664(session, template, *, stage, combat_multiplier=1.0,
                             double_factor=1.0, guild_percent=0,
                             mentor_percent=0, class_levels=()):
    """Source-balance ordinary mob awards before durable kill settlement.

    Handles all four XP axes. Fame and quest XP use separate source curves.
    Includes old source_xp_exact UOSS/boss templates so an uncapped
    low-level kill cannot award hundreds of character levels. Never
    creates a per-reward/bank cap. Existing kill multipliers remain meaningful.
    """
    char=session.character
    lvl=max(1,int(char.character_level))
    from core.progression_resources import (character_xp_to_next,
        soul_xp_to_next, class_mastery_xp_to_next)
    from systems.adaptive_combat import adaptive_combat_rank_v11330
    if template.get('training_dummy') or float(combat_multiplier or 0.0) <= 0:
        return {'character':0,'soul':0,'class':0,'stat':0}
    rank=adaptive_combat_rank_v11330(template)
    factor=RANK_TENTHS[rank]/10.0
    # The fight's meaningful party/area bonuses stay, but cannot recreate the
    # old runaway event multiplier through helper-generated mob HP.
    try:
        combat=max(.20,min(2.80,float(combat_multiplier)))
        doubled=max(1.,min(3.,float(double_factor)))
    except (ValueError,OverflowError,TypeError):
        combat,doubled=1.,1.
    basis=max(24,88-(min(lvl,180)*42)//100-(max(0,lvl-180)//80))
    def payout(requirement, recipient_level, extra=1.0):
        return _fraction_of_requirement(requirement,basis,
            factor=factor*combat*doubled*extra*content_relevance_v11664(stage,recipient_level))
    result={'character':payout(character_xp_to_next(lvl),lvl),
            'soul':payout(soul_xp_to_next(max(1,int(char.soul_level))),
                          max(1,int(char.soul_level)),1+max(0,int(mentor_percent))/100.0)}
    pairs=tuple(class_levels or ())
    if pairs:
        clv=max(1,min(int(level) for _,level in pairs))
        class_extra=(1+max(0,int(guild_percent))/100.0)*(1+max(0,int(mentor_percent))/100.0)
        result['class']=payout(class_mastery_xp_to_next(clv),clv,class_extra)
    else:
        result['class']=0
    fields=getattr(char,'STAT_PROGRESS_FIELDS',{})
    thresholds=[int(char.stat_growth_threshold_for(n)) for n in fields] if fields else []
    stat_need=sum(thresholds)//len(thresholds) if thresholds else 1000
    stat_level=max(1,int(round(sum(int(getattr(char,k,1)) for k in fields)/len(fields)))) if fields else lvl
    result['stat']=payout(stat_need,stat_level)
    return result


def _quest_bps(quest):
    kind=str(quest.get('kind') or '').casefold()
    if kind in ('world_boss','legendary_rare'):
        bp=700
    elif kind in ('kill','party_contract','mini_dungeon'):
        bp=550
    elif kind in ('profession_action','craft_set'):
        bp=350
    else:
        bp=450
    if quest.get('repeatable') or quest.get('hourly') or quest.get('v10700_event_rotation'):
        bp=max(100,bp*45//100)
    return bp


def rebalanced_quest_plan_v11664(session, quest_id, quest, legacy_plan):
    """Generate a quest's BASE rewards without the historic 200k XP floor.

    This is a new SOURCE formula, not an after-the-fact cap on paid EXP.
    Explicit 0 XP axes remain absent, and no OLC data are mutated.
    """
    from core.progression_resources import (v0190_quest_stage,character_xp_to_next,
        soul_xp_to_next,class_mastery_xp_to_next)
    from core.balance_math import axis_requirement
    q=quest or {};old=legacy_plan or {};char=session.character
    if char is None:return old
    stage=v0190_quest_stage(q)
    lvl=max(1,int(char.character_level))
    bp=_quest_bps(q)
    def award(needed,level,bp_override=None):
        return _fraction_of_requirement(needed, bp if bp_override is None else bp_override,
                    factor=content_relevance_v11664(stage,level))
    plan=dict(old)
    plan['character']=award(character_xp_to_next(lvl),lvl)
    slv=max(1,int(char.soul_level))
    plan['soul']=award(soul_xp_to_next(slv),slv) if old.get('soul') else 0
    pairs=tuple(session.active_class_names() or ())
    if old.get('class_xp') and pairs:
        levels=[session.class_mastery_level(name) for name in pairs]
        low=max(1,min(levels))
        plan['class_xp']=award(class_mastery_xp_to_next(low),low)
    elif not old.get('class_xp'):
        plan['class_xp']=0
    vals={}
    for stat in (old.get('stats') or {}):
        value=max(1,int(getattr(char,stat,1)))
        vals[stat]=award(char.stat_growth_threshold_for(stat),value)
    plan['stats']=vals
    tool_type=str(q.get('reward_tool_type') or q.get('specialist_tool_type') or '')
    if old.get('profession') and tool_type:
        profession=str(q.get('reward_profession') or q.get('required_profession') or '')
        if not profession:
            from player.session_mixins.gathering import profession_for_tool_type
            profession=profession_for_tool_type(tool_type) or ''
        row=session.server.db.profession(session.account_id,profession) if profession else None
        prof_level=max(1,int(row['level'])) if row else 1
        prof_need=session.profession_xp_to_next(prof_level,profession) or axis_requirement('profession',prof_level)
        plan['profession']=award(prof_need,prof_level)
    elif not old.get('profession'):
        plan['profession']=0
    if old.get('tool') and tool_type:
        row=session.server.db.tool(session.account_id,tool_type)
        tool_level=max(1,int(row['level'])) if row else 1
        tool_need=session.tool_xp_to_next(tool_level,tool_type) or axis_requirement('tool',tool_level)
        plan['tool']=award(tool_need,tool_level)
    elif not old.get('tool'):
        plan['tool']=0
    return plan
