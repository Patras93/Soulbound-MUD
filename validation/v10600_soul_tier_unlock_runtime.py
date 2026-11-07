# -*- coding: utf-8 -*-
"""Real unlock function (same Python code) + 300 v106 milestone trials.

Run only under SOULBOUND_V106_STAGING=1, no production db/TCP.
Does not certify actual Soul Level 60000 gain rate or combat balance.
"""
from __future__ import annotations
import asyncio
import os
import sys
import types
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))


def run():
    if os.environ.get('SOULBOUND_V106_STAGING')!='1':
        raise RuntimeError('V106 Soul Tier audit requires isolated SOULBOUND_V106_STAGING=1')
    from core import progression_600 as p
    from world.dynamic_content import MOB_TEMPLATES, QUESTS, NPCS
    from world import equipment_help  # ensures trial metadata was authored
    from player.session_methods_v4200.skilllearning_part01 import unlock as unlock_source
    checks=0
    def ck(condition,label):
        nonlocal checks
        if not condition:raise AssertionError('TIER 6000: '+label)
        checks+=1

    ck(p.SOUL_MAX_TIER==6000,'max tier')
    ck(all(len(getattr(p,k))==6000 for k in (
        'SOUL_TIER_THRESHOLDS','SOUL_TIER_POWER_BONUSES',
        'SOUL_TIER_CLASS_BONUS_PERCENT','SOUL_TIER_DODGE_BONUS',
        'SOUL_TIER_GUARDIAN_REDUCTION')),'five curves')
    ck(all(p.SOUL_TIER_THRESHOLDS[t-1]==t*10 for t in range(2,6001)),'historical & new thresholds')
    ck(len({p.SOUL_TRIAL_QUEST_IDS[t] for t in range(3010,6001,10)})==300,'300 unique trial ids')
    ck(all(p.SOUL_TRIAL_QUEST_IDS[t] in QUESTS for t in range(3010,6001,10)),'300 actual quests')
    ck(all(QUESTS[p.SOUL_TRIAL_QUEST_IDS[t]]['target'] in MOB_TEMPLATES for t in range(3010,6001,10)),'300 physical boss targets')
    ck(all(QUESTS[p.SOUL_TRIAL_QUEST_IDS[t]]['required_soul_level']==t*10 for t in range(3010,6001,10)),'300 real Soul Level gates')
    ck(all(QUESTS[p.SOUL_TRIAL_QUEST_IDS[t]]['required_soul_tier']==t-1 for t in range(3010,6001,10)),'300 prior-tier gates')
    ck(QUESTS[p.SOUL_TRIAL_QUEST_IDS[3010]]['target'].startswith('v10600_'),'first v106 boss')
    ck(QUESTS[p.SOUL_TRIAL_QUEST_IDS[6000]]['target']=='v10600_serce_boss_2','last v106 boss')
    ck(p.SOUL_TRIAL_QUEST_IDS[3000] in QUESTS,'v105 last milestone preserved')

    glob=unlock_source.__globals__.copy()
    glob.update(SOUL_MAX_TIER=p.SOUL_MAX_TIER,
                SOUL_TIER_THRESHOLDS=p.SOUL_TIER_THRESHOLDS,
                SOUL_TRIAL_QUEST_IDS=p.SOUL_TRIAL_QUEST_IDS,
                QUESTS=QUESTS,
                SOUL_MILESTONE_TIERS=(),
                soul_tier_title_for_class=p.soul_tier_title_for_class,
                soul_weapon_trait_for_tier_v11193=p.soul_weapon_trait_for_tier_v11193)
    unlock=types.FunctionType(unlock_source.__code__,glob,'unlock')

    class Fake:
        def __init__(self,old,level,passed=()):
            self.character=SimpleNamespace(soul_tier=old,soul_level=level,
                class_name='Wojownik',name='Tester',room_id='temple',
                soul_power=lambda:42,
                soul_weapon_class_bonus_text=lambda:'potwierdzony')
            self.passed=set(passed)
            self.messages=[]
            self.saved=[]
            self.events=[]
            self.server=SimpleNamespace(db=SimpleNamespace(save_character=self.saved_char),
                                        broadcast_room=self.broadcast)
        def saved_char(self,c):self.saved.append(c.soul_tier)
        async def broadcast(self,*args,**kwargs):self.events.append((args,kwargs))
        async def send(self,msg):self.messages.append(msg)
        def soul_tier_quest_completed(self,t):return t in self.passed
        def soul_next_goal_text(self):return 'Następny cel'
        def soul_milestone_text(self,t):return 'milestone'
    def trial(f,multi=True):asyncio.run(unlock(f,multi=multi))

    test=Fake(3009,30100)
    trial(test)
    ck(test.character.soul_tier==3009 and not test.saved,'T3010 cannot bypass trial')
    ck(any('Próba Tieru 3010' in m for m in test.messages),'NVDA block points to Elor')
    test.passed.add(3010)
    trial(test)
    ck(test.character.soul_tier==3010 and test.saved==[3010],'T3010 after quest')

    test=Fake(3010,30200,passed=(3010,))
    trial(test)
    ck(test.character.soul_tier==3019,'T3020 cannot bypass second trial')
    test.passed.add(3020)
    trial(test)
    ck(test.character.soul_tier==3020 and test.saved==[3019,3020],'T3020 after quest')

    last=Fake(5999,60000)
    trial(last)
    ck(last.character.soul_tier==5999,'T6000 cannot bypass final trial')
    last.passed.add(6000)
    trial(last)
    ck(last.character.soul_tier==6000 and last.saved==[6000],'T6000 unlocks')
    trial(last)
    ck(last.character.soul_tier==6000 and last.saved==[6000],'T6001 not possible')
    ck(any('maksymalny Tier' in x for x in last.messages),'max tier message Polish')
    ck(all(f.events for f in (test,last)),'one event on successful unlock')
    return checks

if __name__=='__main__':
    print(f'V106 SOUL TIER 6000 / REAL UNLOCK: {run()} PASS',flush=True)
