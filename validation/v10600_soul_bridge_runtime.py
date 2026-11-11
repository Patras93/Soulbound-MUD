# -*- coding: utf-8 -*-
"""Izolowany test rzeczywistej funkcji Soul XP w v106 i zgodności z v105.

Nie dotyka produkcyjnej SQLite, limitów trwałych ani kont graczy.
"""
from __future__ import annotations
import os, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))


def run():
    from core import live_level_caps_v5200 as caps
    from core.progression_resources import soul_xp_to_next
    from systems.soul_xp_bands_v10402 import BANDS, current_percent, update_rates
    from systems.soul_xp_bridge_v10600 import requirement, FIRST_LEVEL, LAST_LEVEL
    from systems.soul_xp_early_v10600 import requirement as early_requirement
    from config.balance import SOUL_XP_REQUIREMENT_MULTIPLIER as mult
    checks=0
    def ck(ok,message):
        nonlocal checks
        if not ok: raise AssertionError('Soul bridge: '+message)
        checks+=1
    ck(FIRST_LEVEL==800 and LAST_LEVEL==30000,'bounds')
    ck(mult==3.0,'historical multiplier')
    for level,expected in ((800,2400000),(1000,3000000),(5000,15000000),
                           (9999,29997000),(10000,30000000),
                           (20000,45000000),(29999,59998500)):
        ck(requirement(level,mult)==expected,f'bridge {level}')
    for value in (0,799,30000,60000,100000):
        try: requirement(value,mult)
        except ValueError: checks+=1
        else: raise AssertionError('invalid bridge level accepted')
    for bad in (-1,0,0.09,101,float('nan'),float('inf')):
        try: requirement(800,bad)
        except ValueError: checks+=1
        else: raise AssertionError('invalid multiplier accepted')
    old_staging=os.environ.get('SOULBOUND_V106_STAGING')
    old_caps=caps.current()
    old_rates={key:current_percent(key) for key in BANDS}
    try:
        caps._state['dusza']=60000
        os.environ.pop('SOULBOUND_V106_STAGING',None)
        historical={lvl:soul_xp_to_next(lvl) for lvl in (1,99,100,500,700,799,800,1000,5000,10000,20000,29999,30000)}
        ck(historical[1000]==9000000000000000000,'actual v105 saturation')
        os.environ['SOULBOUND_V106_STAGING']='1'
        for level in (1,99,100,500,700,799):
            ck(soul_xp_to_next(level)==early_requirement(level,mult),f'v106 early {level}')
        for level in (800,1000,5000,9999,10000,10001,20000,29999):
            ck(soul_xp_to_next(level)==requirement(level,mult),f'engine uses bridge {level}')
        ck(soul_xp_to_next(29999)==59998500,'before boundary')
        ck(soul_xp_to_next(30000)==60000000,'continuous at 30000')
        ck(all(soul_xp_to_next(v)<=soul_xp_to_next(v+1) for v in (800,900,9999,10000,10001,29999)),
           'continuous and monotonic edges')
        # Admin Live owner-defined percentages for historical bands must remain effective.
        test_rates={name:100 for name in BANDS}
        test_rates['v10400_soul_501_1000']=150
        test_rates['v10400_soul_1001_5000']=75
        test_rates['v10400_soul_5001_10000']=125
        update_rates(test_rates)
        for level,rate in ((800,150),(999,150),(1000,150),(1001,75),(5000,75),(5001,125),(10000,125),(10001,100)):
            base=requirement(level,mult)
            ck(soul_xp_to_next(level)==(base*rate+50)//100,f'Admin Live band {level}')
        ck(soul_xp_to_next(30000)==60000000,'new era not affected by v104 bands')
        update_rates({name:100 for name in BANDS})
        caps._state['dusza']=800
        ck(soul_xp_to_next(800)==0,'admin cap respected')
        caps._state['dusza']=None
        ck(soul_xp_to_next(800)==2400000,'no cap bridge')
        os.environ.pop('SOULBOUND_V106_STAGING',None)
        for level in (800,1000,10000,29999):
            ck(soul_xp_to_next(level)==historical[level],f'production unchanged {level}')
        return checks
    finally:
        update_rates(old_rates)
        caps._state.clear();caps._state.update(old_caps)
        if old_staging is None:os.environ.pop('SOULBOUND_V106_STAGING',None)
        else:os.environ['SOULBOUND_V106_STAGING']=old_staging

if __name__=='__main__':
    print(f'V106 SOUL XP POMOST 800..29999: {run()} PASS',flush=True)
