# -*- coding: utf-8 -*-
"""v106 new-era Soul XP thresholds against original engine and quest rewards.

Isolated, no SQLite and no writes to Admin Live configuration.
Does not certify real player DPS, final exp multi-cap or prior v105 grinding.
"""
from __future__ import annotations
import os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))


def run():
    from core import live_level_caps_v5200 as caps
    from core.progression_resources import soul_xp_to_next
    from systems.soul_xp_curve_v10600 import requirement, FIRST_LEVEL,LAST_LEVEL
    from config.balance import SOUL_XP_REQUIREMENT_MULTIPLIER
    from world.v10600_krainy_30001_60000 import install, REGIONS
    checks=0
    def ck(flag,label):
        nonlocal checks
        if not flag:raise AssertionError('Soul XP v106: '+label)
        checks+=1
    ck(FIRST_LEVEL==30000 and LAST_LEVEL==60000,'era bounds')
    ck(SOUL_XP_REQUIREMENT_MULTIPLIER==3.0,'historical multiplier')
    for lvl in (30000,30001,30100,45000,59999):
        expected=int(round((20_000_000+(lvl-30000)*2_000)*SOUL_XP_REQUIREMENT_MULTIPLIER))
        ck(requirement(lvl,SOUL_XP_REQUIREMENT_MULTIPLIER)==expected,'authored value '+str(lvl))
    for value in (1,29999,60000,1000000):
        try:requirement(value,3.0)
        except ValueError:checks+=1
        else:raise AssertionError('invalid curve bound accepted: '+str(value))
    for mult in (-1,0,0.09,101,float('inf')):
        try:requirement(30000,mult)
        except ValueError:checks+=1
        else:raise AssertionError('invalid multiplier accepted: '+str(mult))
    before=caps.current()
    old_staging=os.environ.get('SOULBOUND_V106_STAGING')
    try:
        caps._state['dusza']=60000
        # Historical behaviour is preserved outside staging. Within staging,
        # early and middle curves are intentionally distinct from v105.
        os.environ.pop('SOULBOUND_V106_STAGING',None)
        original={lvl:soul_xp_to_next(lvl) for lvl in (1,100,700,799,800,999,1000,10000,29999,30000)}
        ck(original[30000]>=9_000_000_000_000_000_000,'prior saturation observed')
        os.environ['SOULBOUND_V106_STAGING']='1'
        from systems.soul_xp_early_v10600 import requirement as early_requirement
        for lvl in (1,100,700,799):
            ck(soul_xp_to_next(lvl)==early_requirement(lvl,SOUL_XP_REQUIREMENT_MULTIPLIER),'v106 early '+str(lvl))
        from systems.soul_xp_bridge_v10600 import requirement as mid_requirement
        for lvl in (800,999,1000,10000,29999):
            ck(soul_xp_to_next(lvl)==mid_requirement(lvl,SOUL_XP_REQUIREMENT_MULTIPLIER),
               'v106 bridge before new era '+str(lvl))
        ck(soul_xp_to_next(30000)==60_000_000,'start level 30000')
        ck(soul_xp_to_next(30100)==60_600_000,'Soul tier 3010')
        ck(soul_xp_to_next(59999)==239_994_000,'last level')
        ck(soul_xp_to_next(60000)==0,'cap reached returns zero')
        ck(all(soul_xp_to_next(i)<soul_xp_to_next(i+1000) for i in (30000,40000,50000)),
           'monotonic requirements through new era')
        # Existing v106 author templates provide actual numeric reference rewards.
        rooms={'v10500_przelom_14':{'exits':{}}};mobs={};spawns=[];npcs={};quests={};items={};recipes={}
        areas=[];zone_ids={};categories={};guides={};target_power={}
        install(rooms,mobs,spawns,npcs,quests,items,recipes,areas,zone_ids,categories,guides,target_power)
        first=mobs['v10600_przedmurze_mob_1']['soul_reward']
        last=mobs['v10600_serce_mob_10']['soul_reward']
        ck(first>0 and last>first,'actual authored mob reward growth')
        for level,reward in ((30000,first),(59999,last)):
            ratio=soul_xp_to_next(level)/reward
            ck(2.0<=ratio<=12.0,f'author-reference actions per Soul Level {level}: {ratio:.1f}')
        ck(quests['v10600_przedmurze_story_01']['olc_reward_soul_xp']>0,'real quest soul XP')
        ck(len(REGIONS)==30,'all 30 regions')
        # Default Admin Live cap blocks growth until owner explicitly changes it.
        caps._state['dusza']=800
        ck(soul_xp_to_next(800)==0,'owner cap 800 respected')
        caps._state['dusza']=None
        ck(soul_xp_to_next(59999)==239_994_000,'unlimited cap respected')
        ck(soul_xp_to_next(60000)>0,'unlimited Soul beyond final Tier cannot crash')
        return checks
    finally:
        caps._state.clear();caps._state.update(before)
        if old_staging is None:os.environ.pop('SOULBOUND_V106_STAGING',None)
        else:os.environ['SOULBOUND_V106_STAGING']=old_staging

if __name__=='__main__':
    print('V106 SOUL XP NEW ERA 30000..60000: '+str(run())+' PASS',flush=True)
