# -*- coding: utf-8 -*-
"""v2.00.8: 12 elemental ranks receive meaningful non-nerf magic damage."""
from systems.mage_elementals_v1702 import ELEMENTALS
from systems.elemental_damage_v2008 import (ELEMENTAL_STRIKE_SHARE,
    effective_elemental_strike_v2008 as strike)


def run_regression():
    count=0
    assert len(ELEMENTALS)==12;count+=1
    assert set(ELEMENTAL_STRIKE_SHARE)=={'ogien','blyskawice','lod','krysztal'};count+=1
    for name,spec in ELEMENTALS.items():
        raw=73
        owner_hit=3200
        # Every rank, including lesser elemental, scales from the owner.
        result=strike(raw,spec,owner_hit)
        assert result>=raw and result>=int(owner_hit*ELEMENTAL_STRIKE_SHARE[spec['element']][spec['rank']])-1,(name,result)
        count+=2
        # No nerf for existing high level minions, 800+ levels and unusual gear.
        assert strike(1000000000,spec,owner_hit)==1000000000;count+=1
        # Protection/support stances reduce the added hit, not other mechanics.
        assert strike(1,spec,owner_hit,stance_factor=.7)<=strike(1,spec,owner_hit,stance_factor=.8)<=result;count+=1
        # Actual city/tactic bonus continues to improve the hit.
        assert strike(1,spec,owner_hit,formation_bonus=1.15,team_bonus=1.06,workshop_bonus=1.2)>result;count+=1
        # No soft cap as the owner's magic hit scales indefinitely.
        assert strike(1,spec,owner_hit*100)>result*90;count+=1
    for rank in range(3):
        for element in ('ogien','blyskawice','lod','krysztal'):
            key=f'zywiolak_{element}_{("mniejszy","zwykly","potezny")[rank]}'
            lo=strike(1,ELEMENTALS[key],3200)
            assert lo > 0;count+=1
        assert (strike(1,ELEMENTALS[f'zywiolak_blyskawice_{("mniejszy","zwykly","potezny")[rank]}'],3200) >
                strike(1,ELEMENTALS[f'zywiolak_ogien_{("mniejszy","zwykly","potezny")[rank]}'],3200) >
                strike(1,ELEMENTALS[f'zywiolak_lod_{("mniejszy","zwykly","potezny")[rank]}'],3200))
        count+=1
    # Unknown/other classes unchanged; bad rank is inert.
    assert strike(200,None,3200)==200;count+=1
    assert strike(200,{'element':'unknown','rank':2},3200)==200;count+=1
    assert strike(200,{'element':'ogien','rank':77},3200)==200;count+=1
    return count

if __name__=='__main__':
    print('MAGE ELEMENTAL DAMAGE v2.00.8:',run_regression(),'checks PASS')
