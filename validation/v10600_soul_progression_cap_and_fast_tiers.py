# -*- coding: utf-8 -*-
"""v106 staging: live cap versus Soul Tier 6000 plus real Soul XP boundary.

No LIVE_CONTENT writes. Runs in a fresh process on a test source copy.
"""
from __future__ import annotations
import os,sys
from pathlib import Path
from types import SimpleNamespace
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))


def run():
    if os.environ.get('SOULBOUND_V106_STAGING')!='1':
        raise RuntimeError('Tylko v106 staging na odizolowanej kopii.')
    from core.progression_600 import SOUL_MAX_TIER,SOUL_TIER_THRESHOLDS
    from systems.soul_tier_goal_v10600 import readiness,current_warning
    from core import live_level_caps_v5200 as caps
    from player.character import Character,_SOUL_TIER_AT_EXACT_LEVEL
    from player.session_mixins.character_profile import SessionCharacterProfileMixin
    checks=0
    def ck(flag,msg):
        nonlocal checks
        if not flag:raise AssertionError('SOUL CAP: '+msg)
        checks+=1

    ck(SOUL_MAX_TIER==6000,'cap tiers')
    ck(SOUL_TIER_THRESHOLDS[2999]==30000 and SOUL_TIER_THRESHOLDS[5999]==60000,'upper level threshold')
    ck(len(_SOUL_TIER_AT_EXACT_LEVEL)==6000,'indexed milestones')
    for tier in (1,2,30,80,3000,3010,3020,5999,6000):
        lvl=int(SOUL_TIER_THRESHOLDS[tier-1]);ck(_SOUL_TIER_AT_EXACT_LEVEL[lvl]==tier,f'tier index {tier}')
    for lvl in (19,21,30001,30101,59999):
        ck(_SOUL_TIER_AT_EXACT_LEVEL.get(lvl) is None,f'not milestone {lvl}')
    ck(readiness(3009,30090,800,SOUL_TIER_THRESHOLDS)['required']==30100,'readiness 3010')
    ck(readiness(5999,59999,800,SOUL_TIER_THRESHOLDS)['required']==60000,'readiness 6000')
    ck(readiness(3009,30100,800,SOUL_TIER_THRESHOLDS) is None,'trial, not cap')
    ck(readiness(3009,30090,60000,SOUL_TIER_THRESHOLDS) is None,'sufficient cap')
    ck(readiness(3009,30090,None,SOUL_TIER_THRESHOLDS) is None,'unlimited cap')
    ck(readiness(6000,60000,800,SOUL_TIER_THRESHOLDS) is None,'already final')
    try:readiness(6001,60000,800,SOUL_TIER_THRESHOLDS)
    except ValueError:ck(True,'tier range guarded')
    else:ck(False,'tier range guarded')
    previous=caps.current()
    previous_staging=os.environ.get('SOULBOUND_V106_STAGING')
    try:
        caps._state['dusza']=800
        person=SimpleNamespace(soul_tier=3009,soul_level=30090,class_name='Wojownik')
        ck('limit Soul Level 800' in current_warning(person,SOUL_TIER_THRESHOLDS),'current cap warning')
        source=SimpleNamespace(character=person)
        goal=SessionCharacterProfileMixin.soul_next_goal_text(source)
        ck('Tieru 3010' in goal and 'admin live limity ustaw dusza 30100 POTWIERDZAM' in goal,'player goal real source')
        # Disabling v106 must keep the old goal unchanged, even in this process.
        os.environ.pop('SOULBOUND_V106_STAGING',None)
        old=SessionCharacterProfileMixin.soul_next_goal_text(source)
        ck('Następny cel: Soul 30100' in old and 'admin live limity' not in old,'old UI unchanged')
        os.environ['SOULBOUND_V106_STAGING']='1'
        caps._state['dusza']=60000
        ck(current_warning(person,SOUL_TIER_THRESHOLDS)=='','no warning when cap is ready')
        goal=SessionCharacterProfileMixin.soul_next_goal_text(source)
        ck('admin live limity' not in goal,'ready UI')
        # The real server refreshes imported numeric caps after loading saved
        # settings. Replicate that without touching any player's database.
        caps._apply_to_runtime()
        ck(__import__('player.character',fromlist=['SOUL_MAX_LEVEL']).SOUL_MAX_LEVEL==60000,'live imported cap')
        c=object.__new__(Character)
        c.soul_level=30099;c.soul_tier=3009;c.soul_xp=0;c.race='Człowiek'
        c._race_bonus=lambda key:0.0
        needed=c.soul_xp_to_next()
        ck(0<needed<=9_223_372_036_854_775_807,'nonzero Soul XP threshold')
        messages=c.add_soul_xp(needed)
        ck(c.soul_level==30100 and c.soul_tier==3009,'real Soul 30100 tier gate')
        ck(any('próg Tieru 3010' in t for t in messages),'real milestone spoken')
        ck(c.soul_progress_is_tier_locked(),'real tier lock after milestone')
        ck(c.add_soul_xp(123) and c.soul_xp==123,'Soul XP banked at trial')
        ck(_SOUL_TIER_AT_EXACT_LEVEL[60000]==6000,'max staged milestone indexed')
        c.soul_level=59999;c.soul_tier=5999;c.soul_xp=0
        needed=c.soul_xp_to_next()
        ck(needed==239_994_000,'final v106 level has finite attainable threshold')
        final_msgs=c.add_soul_xp(needed)
        ck(c.soul_level==60000 and c.soul_tier==5999,'final Soul level requires Tier quest')
        ck(c.can_unlock()==6000,'max Tier 6000 can unlock after trial')
        ck(any('Tieru 6000' in line for line in final_msgs),'final Tier goal announced')
        return checks
    finally:
        caps._state.clear();caps._state.update(previous)
        caps._apply_to_runtime()
        if previous_staging is None:os.environ.pop('SOULBOUND_V106_STAGING',None)
        else:os.environ['SOULBOUND_V106_STAGING']=previous_staging

if __name__=='__main__':
    print('V106 SOUL LEVEL 60000 READINESS + FAST TIERS: '+str(run())+' PASS',flush=True)
