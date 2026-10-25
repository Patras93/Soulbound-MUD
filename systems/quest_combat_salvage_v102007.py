# -*- coding: utf-8 -*-
"""v102.00.7: explicit combat-loot exception for three exact-ID enemy-loot quests.

Does not reclassify quests, alter objectives, automatically award new EXP or
change their monetary rewards. Only deliberate Admin Live XP overrides pay out.
"""
# Restrict the exception to actual existing quest IDs, not a mutable display
# title or quest-list number ("53" is NOT a quest ID).
_ALLOWED_IDS = frozenset({
    'haldor_steel_recycling',
    'haldor_broken_blades_v0929',
    'haldor_armor_recycling_v0929',
})
_SALVAGE_KINDS = frozenset({'collect', 'collect_resource', 'collect_resource_set'})


def is_combat_salvage_quest(quest, quest_id=None):
    """Only these three actual combat-loot contracts can opt in to Soul/Class XP."""
    return (str(quest_id or '') in _ALLOWED_IDS
            and str((quest or {}).get('kind') or '') in _SALVAGE_KINDS)


def class_xp_at_turnin(quest, automatic_xp=0, quest_id=None):
    """A combat-salvage collection only pays mastery with an explicit override."""
    quest = quest or {}
    combat = str(quest.get('kind') or '') in ('kill', 'legendary_rare', 'world_boss', 'party_contract')
    if combat:
        return int(quest.get('olc_reward_class_xp', automatic_xp) or 0)
    if is_combat_salvage_quest(quest, quest_id):
        return int(quest.get('olc_reward_class_xp', 0) or 0)
    return 0


def soul_xp_at_turnin(quest, automatic_xp=0, quest_id=None):
    """Crafting quests retain zero Soul; three enemy-loot jobs need OLC opt-in."""
    from core.progression_resources import v0522_is_profession_quest
    quest = quest or {}
    if v0522_is_profession_quest(quest):
        if is_combat_salvage_quest(quest, quest_id):
            return int(quest.get('olc_reward_soul_xp', 0) or 0)
        return 0
    return int(quest.get('olc_reward_soul_xp', automatic_xp) or 0)
