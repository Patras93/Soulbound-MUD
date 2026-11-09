# -*- coding: utf-8 -*-
"""11 playable raid descriptions for NVDA, no mutations and no real DB."""
from __future__ import annotations

def run():
    from systems import admin_live_era_v10300 as admin
    report = admin.report
    from world.v10300_era_bez_granic import install as era_install, ERAS
    from world.v10300_era_raids import install as raids_install
    rooms={'v3000_eternal_6': {'exits': {}}}
    mobs={}; spawns=[]; npcs={}; quests={}; items={}; recipes={}; areas=[]
    era_install(rooms,mobs,spawns,npcs,quests,items,recipes,areas,{},{},{},{})
    raids_install(rooms,mobs,spawns,npcs,quests,items,recipes)
    checks=0
    # v107: the real game must deny former raid admin commands, even if a
    # complete pre-v107 fixture exists for preserving historical NVDA limits.
    assert 'wycofane' in report('rajdy',quests,rooms,npcs,mobs)
    assert 'wycofane' in report('rajd swit',quests,rooms,npcs,mobs)
    original_gate=admin._sb107_runtime_enabled
    admin._sb107_runtime_enabled=lambda:False
    try:
        return _run_legacy_catalogue_checks(report,quests,rooms,npcs,mobs,ERAS)
    finally:
        admin._sb107_runtime_enabled=original_gate


def _run_legacy_catalogue_checks(report,quests,rooms,npcs,mobs,ERAS):
    checks=0
    listing=report('rajdy',quests,rooms,npcs,mobs)
    assert 0<len(listing)<1600 and listing.count(': ')>=11
    checks+=2
    for slug,zone,low,high,*_ in ERAS:
        answer=report('rajd '+slug,quests,rooms,npcs,mobs)
        assert zone in answer and str(low) in answer and str(high) in answer
        assert f'v10300_{slug}_04' in answer and f'v10300_{slug}_09' in answer
        assert all(f'{j}/3:' in answer for j in (1,2,3))
        assert all(mobs[f'v10300_{slug}_raid_boss_{j}']['name'] in answer for j in (1,2,3))
        assert len(answer)<1100,('NVDA verbosity',slug,len(answer))
        checks+=5
    for bad in ('rajd','rajd cos_nieistniejacego','rajd xyz','rajd 123'):
        text=report(bad,quests,rooms,npcs,mobs)
        assert isinstance(text,str) and text and len(text)<1100
        checks+=1
    assert checks==61,checks
    return checks

if __name__ == '__main__':
    print(f'ERA 103 RAID NVDA STATUS: {run()} checks PASS',flush=True)
