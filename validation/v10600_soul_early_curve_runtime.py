# -*- coding: utf-8 -*-
"""Audyt wczesnej krzywej Soul XP v106, prawdziwego awansu oraz regresji v105.

Nie korzysta z bazy użytkownika ani z produkcyjnego serwera.\n"""
from __future__ import annotations
import os
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))


def run():
    if os.environ.get('SOULBOUND_V106_STAGING') != '1':
        raise RuntimeError('Ten test wymaga jawnego SOULBOUND_V106_STAGING=1.')
    from core import live_level_caps_v5200 as caps
    from core.balance_math import axis_gain
    from core.progression_resources import soul_xp_to_next
    from config.balance import SOUL_XP_REQUIREMENT_MULTIPLIER as multiplier
    from systems.soul_xp_early_v10600 import FIRST_LEVEL,LAST_LEVEL,requirement
    from systems.soul_xp_bridge_v10600 import requirement as bridge
    from systems.soul_xp_bands_v10402 import BANDS,current_percent,update_rates
    checks=0
    def ck(condition,description):
        nonlocal checks
        if not condition:
            raise AssertionError('SOUL EARLY V106: '+description)
        checks += 1

    ck((FIRST_LEVEL,LAST_LEVEL)==(1,800),'boundaries')
    ck(multiplier==3.0,'default multiplier')
    saved_caps=caps.current()
    saved_rates={k:current_percent(k) for k in BANDS}
    saved_staging=os.environ.get('SOULBOUND_V106_STAGING')
    try:
        caps._state['dusza']=60000
        caps._apply_to_runtime()
        # Precisely compare the v105 requirements outside staging and save
        # representative values: stage must NOT alter persistent XP or levels.
        os.environ.pop('SOULBOUND_V106_STAGING',None)
        original={level:soul_xp_to_next(level) for level in (1,2,10,100,500,501,700,799,800,1000)}
        ck(original[1]==47400,'actual production level 1')
        ck(original[799]>10**17,'historical saturation before lvl 800')
        os.environ['SOULBOUND_V106_STAGING']='1'

        # A full sweep proves every step through 1-800 is positive,
        # monotonic, capped by the planned boundary and exactly matches
        # the authored v105 normal-mob reward curve.
        anchor_gain=axis_gain('soul',800)
        anchor_req=bridge(800,multiplier)
        ck(anchor_req==2400000,'existing bridge preserved')
        previous=0
        for level in range(1,800):
            threshold=requirement(level,multiplier)
            ck(threshold>=previous and 0<threshold<anchor_req,f'monotonic XP {level}')
            ck(threshold==(anchor_req*axis_gain('soul',level)+anchor_gain//2)//anchor_gain,
                f'anchored authored reward {level}')
            ck(soul_xp_to_next(level)==threshold,f'actual progression {level}')
            previous=threshold
        ck(previous<bridge(800,multiplier),'continuous 799 to 800')
        ck(soul_xp_to_next(800)==anchor_req,'bridge 800 unchanged')
        ck(soul_xp_to_next(30000)==60000000,'endgame 30000 unchanged')
        ck(soul_xp_to_next(59999)==239994000,'endgame 59999 unchanged')
        for level in (1,2,10,100,500,700,799):
            ratio=requirement(level,multiplier)/axis_gain('soul',level)
            ck(7.0 <= ratio <= 8.0,f'expected 7-8 authored awards {level}: {ratio}')
        for wrong in (0,-1,800,30000,59999,60000,True,3.0,'100'):
            try:requirement(wrong,multiplier)
            except ValueError:checks += 1
            else:raise AssertionError('Accepted invalid Soul level: '+repr(wrong))
        for bad_mult in (-1,0,0.09,101,float('nan'),float('inf'),'3',True):
            try:requirement(20,bad_mult)
            except ValueError:checks += 1
            else:raise AssertionError('Accepted invalid multiplier: '+repr(bad_mult))
        for mult in (0.1,0.25,1,3,7,100):
            ck(0<requirement(1,mult)<requirement(799,mult)<bridge(800,mult),
               f'multiplier bounds: {mult}')

        # Existing Admin Live v104 bands are applied exactly once by the
        # production-facing soul_xp_to_next method.
        rates={name:100 for name in BANDS}
        rates['v10400_soul_501_1000']=175
        update_rates(rates)
        for level in (1,100,500,501,600,799,800):
            base=requirement(level,multiplier) if level<800 else bridge(800,multiplier)
            factor=175 if level>=501 else 100
            ck(soul_xp_to_next(level)==(base*factor+50)//100,
               f'Admin Live band {level}')
        update_rates({name:100 for name in BANDS})
        caps._state['dusza']=1
        ck(soul_xp_to_next(1)==0,'owner cap 1 respected')
        caps._state['dusza']=800
        ck(soul_xp_to_next(799)==requirement(799,multiplier),'cap 800 allows level 799')
        ck(soul_xp_to_next(800)==0,'owner cap 800 respected')
        caps._state['dusza']=60000
        caps._apply_to_runtime()
        # Real character awards may not skip Soul Tier 2 when EXP is plentiful.
        from player.character import Character
        test=object.__new__(Character)
        test.soul_level=19;test.soul_xp=0;test.soul_tier=1;test.race='Człowiek'
        test._race_bonus=lambda name:0.0
        needed=test.soul_xp_to_next()
        messages=test.add_soul_xp(needed+500)
        ck(test.soul_level==20 and test.soul_tier==1,'Soul Level 20 tier gate')
        ck(test.soul_xp==500,'Soul XP banked for pending trial')
        ck(test.soul_progress_is_tier_locked(),'tier locked')
        ck(any('Tieru 2' in msg for msg in messages),'Polish trial announcement')
        ck(test.add_soul_xp(200) and test.soul_xp==700,'XP deferred at locked tier')
        # Switching staging off must reconstruct *exactly* old thresholds.
        os.environ.pop('SOULBOUND_V106_STAGING',None)
        for level,value in original.items():
            ck(soul_xp_to_next(level)==value,f'production unchanged {level}')
        return checks
    finally:
        update_rates(saved_rates)
        caps._state.clear();caps._state.update(saved_caps)
        caps._apply_to_runtime()
        if saved_staging is None:os.environ.pop('SOULBOUND_V106_STAGING',None)
        else:os.environ['SOULBOUND_V106_STAGING']=saved_staging


if __name__=='__main__':
    print('V106 SOUL XP 1..799 + SOUL TIER REAL: '+str(run())+' PASS',flush=True)
