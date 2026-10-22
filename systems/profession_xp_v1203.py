# -*- coding: utf-8 -*-
"""v12.00.3: fair rewards for 22 professions and all 22 tools.

Only successful, level-tagged activities get a progression-aware reward.
Real content level and real item/action identity determine payout: the
player's skill level is NEVER used to fake a higher material tier.
All old rewards are retained as lower bounds; no item loss, RNG, new tools,
or database writes. Old EXP Bank/Multi Cap and all existing modifiers apply.
"""
from __future__ import annotations
import hashlib


def material_factor(key):
    """Deterministic distinction within a content tier, never a random jackpot.

    The small tie-breaker recognizes different materials of the same level.
    It is based on a stable identity, not on per-use random sampling.
    """
    if not key:
        return 1.0
    code = str(key).encode('utf-8', 'replace')
    token = int.from_bytes(hashlib.blake2b(code, digest_size=8).digest(), 'big')
    return 1.01 + (token % 15001) / 100000.0  # +1% to +16%


def reward_xp_v1203(previous, required, level, content_level, *, tool=False, content_key=None):
    """A meaningful fraction of a level for a *suitable* real material.

    Up to 800; ~75..155 successful challenging profession actions / level,
    ~85..165 tool actions. Using low-level copper or common fish at level 799
    gets much less, so progression still rewards unlocking harder work.
    """
    old=max(0,int(previous or 0))
    if old==0 or content_level is None:
        return old
    skill=max(1,min(800,int(level or 1)))
    stage=max(1,min(800,int(content_level or 1)))
    if skill>=800:return old
    needed=max(0,int(required or 0))
    if not needed:return old
    # No free high-tier rewards for trivial gathering. The maximum effective
    # tier is level-appropriate, even if an invalid caller passes stage 999.
    ratio=(stage+18.0)/(skill+18.0)
    # Advanced material remains more rewarding at every higher tier, even
    # when its level is above the current skill; no flat plateau after 100.
    # Limit exceptional jumps to avoid unbounded accidental rewards.
    difficulty=ratio**1.7 if ratio<=1.0 else 1.0+0.45*(min(5.0,ratio)-1.0)
    steps=(88 + skill//11) if tool else (72 + skill//12)
    # Distinct real materials within same tier yield slightly different EXP.
    # Diminishing returns maintain the original long-term Soulbound grind.
    target=int(needed*difficulty*material_factor(content_key)/steps)
    # v12.00.7: item-specific OLC EXP on the actual material ID. Preserves
    # the previously calculated reward as a floor and never creates XP from 0.
    from systems.live_progression_v1206 import resource_rule_xp
    return resource_rule_xp(max(old,target), content_key, tool=tool)


def quest_reward_floor_v1203(previous, required, level, quest, *, tool=False):
    """Extra master/quest award from actual effort and authentic quest tier.

    Repeatable paths are capped lower than one-time journeys; trivial quests
    never become a source of free level-799 progress. Old payout is a floor.
    Quest completion stays a separate award from the quest's activity XP.
    """
    old=max(0,int(previous or 0))
    if old==0 or not isinstance(quest,dict):
        return old
    level=max(1,min(800,int(level or 1)))
    if level>=800:
        return old
    needed=max(0,int(required or 0))
    if not needed:return old
    stage=max(1,min(800,int(quest.get('min_profession_level')
                                  or quest.get('generator_level') or 1)))
    # Some legacy quest levels are only recommendations, not an access lock.
    # A fresh apprentice must not gain artificially large EXP by accepting an
    # unlevelled endgame quest through an unlocked NPC dialogue.
    if stage>level+30:
        return old
    difficulty=min(1.0,(stage+18.0)/(level+18.0))**1.7
    actions=max(1,int(quest.get('needed') or 1))
    workload=min(1.65,0.65+0.03*actions)
    factor=(0.055 if quest.get('repeatable') else 0.105)
    if tool: factor*=0.95
    return max(old,int(needed*difficulty*workload*factor))
