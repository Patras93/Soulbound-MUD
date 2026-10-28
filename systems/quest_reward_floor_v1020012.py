# -*- coding: utf-8 -*-
"""v102.00.12: meaningful quest XP, without modifying saved OLC or characters.

This calculates *base* rewards for display and payout. The existing content-
aware scaling, Multi Cap, Half CAP, Overcap and EXP Bank remain authoritative.
Only relevant XP tracks are awarded. Quest authoring/config is not mutated.
"""
from core.progression_resources import (
    v0270_quest_character_reward, v0190_quest_stat_reward,
    v0190_quest_soul_reward, v0522_combat_quest_class_reward,
)
from systems.quest_combat_salvage_v102007 import (
    class_xp_at_turnin, soul_xp_at_turnin,
)
from systems.live_quest_olc_v1209 import STAT_XP_FIELDS_V3900

BASE_QUEST_XP_MIN = 200_000


def _floor(value):
    return max(BASE_QUEST_XP_MIN, int(value or 0))


def quest_xp_plan(quest_id, quest):
    """Effective pre-scaling XP, stable for information screen and turn-in.

    Important: 0 mastery on a noncombat quest, 0 Soul on a profession quest,
    and absent profession/tool tracks stay 0. Three salvage combat-loot jobs
    still need explicit mastery/Soul authorization through Admin Live.
    Explicit OLC XP fields are not changed on disk; the runtime floor applies
    to relevant channels even when their older authored amount was 0.
    """
    q = quest or {}
    character = _floor(q.get('olc_reward_xp', v0270_quest_character_reward(q)))
    raw_stat = q.get('olc_reward_stat_xp', v0190_quest_stat_reward(q))
    stats = {
        name: _floor(q.get(field, raw_stat))
        for name, field in STAT_XP_FIELDS_V3900.items()
    }
    kind = str(q.get('kind') or '')
    combat = kind in ('kill', 'legendary_rare', 'world_boss', 'party_contract')
    original_class = class_xp_at_turnin(
        q, v0522_combat_quest_class_reward(q), quest_id)
    mastery = _floor(original_class) if combat or original_class > 0 else 0
    original_soul = soul_xp_at_turnin(q, v0190_quest_soul_reward(q), quest_id)
    # Preserve class/profession distinction; no free Soul for crafting.
    from core.progression_resources import v0522_is_profession_quest
    soul = _floor(original_soul) if original_soul > 0 or not v0522_is_profession_quest(q) else 0
    tool_type = q.get('reward_tool_type') or q.get('specialist_tool_type')
    profession_context = bool(q.get('reward_profession') or q.get('required_profession') or q.get('reward_profession_xp'))
    tool_context = bool(tool_type)
    # Profession reward function needs a concrete, valid tool type; callers
    # continue to validate it with the existing valid_tool_type guard.
    profession = _floor(q.get('reward_profession_xp')) if profession_context and tool_context else 0
    tool = _floor(q.get('reward_tool_xp')) if tool_context else 0
    return dict(character=character, stats=stats, class_xp=mastery,
                soul=soul, profession=profession, tool=tool)
