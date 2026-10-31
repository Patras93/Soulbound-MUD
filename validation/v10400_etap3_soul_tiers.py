# -*- coding: utf-8 -*-
"""v104 etap 3 — testy realnego katalogu i awansu Soul Tier 501–1000.
Bez dostępu do prawdziwej bazy danych i bez zmiany limitów Admin Live.
"""
from __future__ import annotations

import asyncio
import types
from collections import Counter


def run():
    from core import progression_600 as p
    from core.bootstrap_economy_professions import SOUL_TRIAL_QUEST_IDS, soul_trial_difficulty_band
    from core.classes_skills import CLASSES
    from systems.content_registry import QUESTS
    from world import dynamic_content as world
    from systems.quest_reward_floor_v1020012 import quest_xp_plan
    from systems.dungeons_regions import is_crypt_boss_floor
    from systems.admin_live_era_v10300 import report
    from player.character import Character

    n=0
    def ck(check, description):
        nonlocal n
        if not check: raise AssertionError(description)
        n+=1

    ck(p.SOUL_MAX_TIER == 1000, 'max tier')
    arrays=('SOUL_TIER_THRESHOLDS','SOUL_TIER_POWER_BONUSES',
            'SOUL_TIER_CLASS_BONUS_PERCENT','SOUL_TIER_DODGE_BONUS',
            'SOUL_TIER_GUARDIAN_REDUCTION')
    for name in arrays:
        ck(len(getattr(p,name))==1000,'len '+name)
    ck(p.SOUL_TIER_THRESHOLDS[499]==5000,'legacy Tier 500 threshold')
    ck(p.SOUL_TIER_THRESHOLDS[500]==5010,'new Tier 501 threshold')
    ck(p.SOUL_TIER_THRESHOLDS[999]==10000,'Tier 1000 threshold')
    for tier in range(501,1001):
        lvl=tier*10
        key=f'soul_tier_{tier:02d}_trial'
        ck(p.SOUL_TIER_THRESHOLDS[tier-1]==lvl,f'level {tier}')
        ck(SOUL_TRIAL_QUEST_IDS.get(tier)==key,f'trial key {tier}')
        q=QUESTS.get(key)
        ck(q is not None,f'trial missing {tier}')
        ck(q['target']==f'crypt_boss_{lvl}',f'trial target {tier}')
        ck(q['required_soul_level']==lvl,f'level req {tier}')
        ck(q['required_soul_tier']==tier-1,f'tier req {tier}')
        ck(q['unlocks_soul_tier']==tier,f'unlock {tier}')
        ck(q['giver']=='Kapłan Elor',f'Elor {tier}')
        ck(is_crypt_boss_floor(lvl),f'crypt boss {lvl}')
        ck(soul_trial_difficulty_band(tier)==('Kosmiczna' if tier<=750 else 'Transcendentna'),f'band {tier}')
        plan=quest_xp_plan(key,q)
        ck(plan['character']>=2_000_000,f'character reward {tier}')
        ck(plan['class_xp']>=1_500_000,f'class reward {tier}')
        ck(plan['soul']>=2_000_000,f'soul reward {tier}')
        ck(all(v>=1_000_000 for v in plan['stats'].values()),f'stats reward {tier}')
        ck(q['reward_silver']>0,f'normalizowana nagroda w srebrze {tier}')
        ck(p.SOUL_TIER_GUARDIAN_REDUCTION[tier-1]<=65,f'guard reduction {tier}')
        ck(p.SOUL_TIER_DODGE_BONUS[tier-1]<=.05,f'dodge reduction {tier}')
    # All real classes, every tier; no overwrite of previous traits.
    for class_name,*_ in CLASSES:
        titles=set()
        for tier in range(501,1001):
            trait=p.soul_weapon_trait_for_tier_v11193(tier,class_name)
            ck(bool(trait and trait['name'] and trait['description']),f'trait {class_name} {tier}')
            ck(trait['name'] not in titles,f'nonunique trait {class_name} {tier}')
            titles.add(trait['name'])
        ck(len(titles)==500,f'500 titles for {class_name}')
    # Generowanie głębokiej Krypty: naprawdę dostępny cel questa, nie tylko ID.
    from world.economy_quests import create_infinite_crypt_floor_definition
    for floor in (5010, 7500, 10000):
        room, spawns = create_infinite_crypt_floor_definition(floor)
        boss_id=f'crypt_boss_{floor}'
        ck(room==f'crypt_floor_{floor}',f'dynamic room {floor}')
        ck(boss_id in world.MOB_TEMPLATES,f'boss template {floor}')
        ck(world.MOB_TEMPLATES[boss_id]['quest_target']==boss_id,f'quest kill credit {floor}')
        ck((room,boss_id) in spawns,f'boss spawn {floor}')
        ck(world.MOB_TEMPLATES[boss_id]['max_hp']>0,f'boss HP {floor}')
    ck('Soul Tier 1000/1000:' in report('soul 1000',QUESTS,world.ROOMS,world.NPCS,world.MOB_TEMPLATES),'admin live inspect tier1000')
    ck('Soul: dopuszczalne Tiery' in report('soul 1001',QUESTS,world.ROOMS,world.NPCS,world.MOB_TEMPLATES),'admin live out of range')

    # Test actual native Character unlock threshold, using object with only
    # the attributes needed for can_unlock (no DB initialization).
    for tier,level,expected in ((500,5000,None),(500,5010,501),(999,9999,None),(999,10000,1000),(1000,20000,None)):
        c=types.SimpleNamespace(soul_tier=tier,soul_level=level)
        ck(Character.can_unlock(c)==expected,f'character can_unlock {tier}/{level}')

    # Exercise actual unlock method, with an isolated fake server, no SQLite,
    # no global monkeypatch of an already running session.
    from player.session_methods_v4200.skilllearning_part01 import unlock as native_unlock
    g=dict(native_unlock.__globals__)
    g.update(SOUL_MAX_TIER=p.SOUL_MAX_TIER, SOUL_TIER_THRESHOLDS=p.SOUL_TIER_THRESHOLDS,
             SOUL_TRIAL_QUEST_IDS=SOUL_TRIAL_QUEST_IDS, QUESTS=QUESTS,
             soul_tier_title_for_class=p.soul_tier_title_for_class,
             soul_weapon_trait_for_tier_v11193=p.soul_weapon_trait_for_tier_v11193,
             SOUL_MILESTONE_TIERS=())
    method=types.FunctionType(native_unlock.__code__,g,'unlock')
    class DummyDB:
        def __init__(self):self.saved=[]
        def save_character(self,c):self.saved.append(c.soul_tier)
    class DummyServer:
        def __init__(self):self.db=DummyDB();self.messages=[]
        async def broadcast_room(self,*a,**kw):self.messages.append((a,kw))
    class DummySession:
        def __init__(self,old,level,passed):
            self.character=types.SimpleNamespace(soul_tier=old,soul_level=level,
                class_name='Wojownik',name='Tester',room_id='room',
                soul_power=lambda:9000,
                soul_weapon_class_bonus_text=lambda:'bonus')
            self.server=DummyServer();self.messages=[];self.passed=passed
        async def send(self,x):self.messages.append(x)
        def soul_tier_quest_completed(self,tier):return self.passed
        def soul_next_goal_text(self):return 'Następna Próba'
    async def validate_unlock():
        for old,level,passed,should_advance in ((500,5010,False,False),
                (500,5000,True,False),(500,5010,True,True),
                (999,10000,True,True),(1000,20000,True,False)):
            s=DummySession(old,level,passed)
            await method(s)
            ck((s.character.soul_tier==old+1)==should_advance,
               f'advance check {old}/{level}/{passed}')
            ck(s.server.db.saved==([old+1] if should_advance else []),
               f'no accidental save {old}/{level}/{passed}')
            ck(bool(s.messages),f'nvda feedback {old}/{level}')
            if should_advance:
                ck(len(s.server.messages)==1,f'broadcast {old}/{level}')
    asyncio.run(validate_unlock())
    return n

if __name__=='__main__':
    result=run()
    print(f'V104 ETAP 3 SOUL TIER 501–1000: {result} PASS',flush=True)
