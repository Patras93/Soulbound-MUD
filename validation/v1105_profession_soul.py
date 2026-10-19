# -*- coding: utf-8 -*-
"""v11.00.5: profession-only activity/quests NEVER grant Soul XP.

Covers the assembled 22-profession quest catalog, displayed NPC rewards,
and real quest-completion gateway with isolated fake reward sinks.
"""
import asyncio
from types import SimpleNamespace

import server  # Install additive catalogs before inspecting all quests.
from core.progression_resources import v0522_is_profession_quest
from player.session_mixins.quest_offers import SessionQuestOffersMixin
from player.session_mixins.quest_commands import SessionQuestCommandsMixin
from player.session_mixins.professions import SessionProfessionsV03053Mixin
from player.session_mixins.profesje6 import SessionProfesje6Mixin
from systems.content_registry import QUESTS
from systems.new_professions import PROFESSIONS


class _DB:
    def quest(self, *args): return None
    def complete_quest(self, *args): pass
    def add_lifetime_stat(self, *args): pass
    def record_activity_v0560(self, *args): pass
    def save_character(self, *args): pass


class _Session(SessionQuestOffersMixin, SessionQuestCommandsMixin):
    account_id = 1
    def __init__(self, quest_id):
        self.quest_id = quest_id
        self.server = SimpleNamespace(db=_DB(), events=SimpleNamespace(publish=self._publish))
        self.character = SimpleNamespace(silver=1000, character_level=20)
        self.messages = []
        self.soul = []
        self.character_rewards = []
    async def send(self, value, **kwargs): self.messages.append(str(value))
    def quest_from_context(self, number): return self.quest_id, None
    def quest_offer_state(self, qid): return 'Dostępne'
    def validate_quest_rewards_v1106(self, quest_id, quest): return []
    def cleanup_quest_map_artifacts_v0243(self, *args, **kwargs): pass
    def quest_turnin_npc_name_v098(self, quest): return 'Mistrz'
    def quest_turnin_reaction_v098(self, quest, name): return 'Nagroda'
    async def grant_combat_quest_stat_xp(self, amount, repeatable, **kwargs): return [amount]*6
    async def grant_class_xp(self, amount, **kwargs): pass
    async def grant_profession_reward_xp(self, *args, **kwargs): pass
    async def grant_tool_reward_xp(self, *args, **kwargs): pass
    async def grant_soul_xp(self, amount, **kwargs): self.soul.append(amount)
    def add_character_xp_with_event(self, amount, **kwargs):
        self.character_rewards.append(amount)
        return []
    async def _publish(self, event): pass


def run_regression():
    checks=0
    def ck(condition, reason):
        nonlocal checks
        checks += 1
        if not condition: raise AssertionError('PROFESSIONS WITHOUT SOUL v11.00.5: '+reason)

    ck(server.VERSION in ('11.00.5','11.00.6','11.00.7','11.00.8','11.00.9','11.00.10','11.00.11','11.00.12','11.00.13','11.00.14','11.00.15','11.00.16','11.00.17','11.00.18',), 'candidate version')
    ck(len(PROFESSIONS) == 8, 'new 8 professions unchanged')
    ck(len(QUESTS) >= 6745, 'full quest catalog is loaded')
    examples = [
        ({'kind':'profession_action', 'generator_level':75, 'reward_silver':500}, True),
        ({'kind':'craft_set', 'generator_level':75}, True),
        ({'kind':'collect', 'required_profession':'Kupiectwo'}, True),
        ({'kind':'collect', 'track_craft_progress':True}, True),
        ({'kind':'collect', 'reward_tool_type':'mining'}, True),
        ({'kind':'collect', 'reward_profession_xp':10}, True),
        ({'kind':'kill', 'generator_level':75}, False),
        ({'kind':'world_boss', 'generator_level':75}, False),
        ({'kind':'explore_frontier', 'generator_level':75}, False),
    ]
    for quest, expected in examples:
        ck(bool(v0522_is_profession_quest(quest)) == expected, 'quest classifier: '+repr(quest))

    profession_ids=[]
    for qid, quest in QUESTS.items():
        if quest.get('kind') in ('profession_action','craft_set'):
            ck(v0522_is_profession_quest(quest), 'profession-action payout: '+qid)
        if v0522_is_profession_quest(quest):
            profession_ids.append(qid)
    ck(len(profession_ids) > 1500, 'all profession quests accounted for')
    ck(any(QUESTS[qid]['kind']=='profession_action' and not QUESTS[qid].get('reward_profession_xp') for qid in profession_ids),
       'silver-only profession actions included')

    # Real command offer and completion, including v11 silver-only contracts.
    silver_only = next(qid for qid in profession_ids if QUESTS[qid]['kind']=='profession_action' and not QUESTS[qid].get('reward_profession_xp') and not QUESTS[qid].get('reward_tool_xp') and not QUESTS[qid].get('reward_items'))
    for qid in (silver_only, next(qid for qid in profession_ids if qid.startswith('v601_path_'))):
        s = _Session(qid)
        asyncio.run(s.quest_info_from_context('1'))
        ck(not any('Soul XP' in msg for msg in s.messages), qid+' does not advertise Soul XP')
        ck(any('Nagrody:' in msg for msg in s.messages), qid+' retains legitimate rewards')
        s.messages.clear()
        asyncio.run(s.complete_quest(qid))
        ck(not s.soul, qid+' zero Soul XP actually granted')
        ck(bool(s.character_rewards), qid+' regular character EXP intact')
    # Gameplay battle quest rewards are intentionally not suppressed.
    battle = next(qid for qid,q in QUESTS.items() if q.get('kind') == 'kill' and not v0522_is_profession_quest(q) and not q.get('reward_items') and not q.get('reward_profession_xp'))
    s = _Session(battle)
    asyncio.run(s.quest_info_from_context('1'))
    ck(any('Soul XP' in msg for msg in s.messages), 'non-profession quest still advertises Soul XP')
    asyncio.run(s.complete_quest(battle))
    ck(bool(s.soul), 'non-profession quest still pays Soul XP')
    ck(not hasattr(SessionProfesje6Mixin, 'grant_soul_xp'), 'new profession mechanic has no soul grant override')
    ck(not hasattr(SessionProfessionsV03053Mixin, 'grant_soul_xp'), 'legacy profession mechanic has no soul grant override')
    print(f'PROFESJE BEZ SOUL XP v11.00.5: {checks} checks PASS ({len(profession_ids)} profession quests)')
    return checks


if __name__ == '__main__': run_regression()
