# -*- coding: utf-8 -*-
"""Actual boss phase state machine exercised for all 33 raid bosses.
Tests four thresholds and one-time phase transitions, not TCP fighting.
"""
from __future__ import annotations
from types import SimpleNamespace


def run():
    import server
    from systems.content_registry import MOB_TEMPLATES
    from systems.encounter_brain_v1230 import boss_tactics_phase_v1230
    from world.v10300_era_bez_granic import ERAS, install as era_install
    from world.v10300_era_raids import install as legacy_raid_install
    # v107 deleted these enemies from LIVE.  Preserve the original state-
    # machine regression on a synthetic pre-v107 content catalog, never by
    # resurrecting retired raid mobs on the running server.
    rooms={'v3000_eternal_6': {'exits': {}}}; mobs={}; spawns=[]
    npcs={}; quests={}; items={}; recipes={}; areas=[]
    era_install(rooms,mobs,spawns,npcs,quests,items,recipes,areas,{},{},{},{})
    legacy_raid_install(rooms,mobs,spawns,npcs,quests,items,recipes)
    checks=0
    for slug,*_ in ERAS:
        for j in (1,2,3):
            mid=f'v10300_{slug}_raid_boss_{j}'
            assert mid not in MOB_TEMPLATES, ('retired raid mob leaked into live world',mid)
            template=mobs[mid]
            maximum=int(template['max_hp'])
            mob=SimpleNamespace(alive=True,hp=maximum,adaptive_max_hp_v11330=0,v1230_boss_phase=0)
            for pct,phase in ((79,1),(59,2),(39,3),(19,4)):
                mob.hp=maximum*pct//100
                event=boss_tactics_phase_v1230(mob,template,now=111.0)
                assert f'FAZA {phase}/4' in str(event),(mid,phase,event)
                assert mob.v1230_boss_phase==phase,(mid,phase,mob.v1230_boss_phase)
                assert boss_tactics_phase_v1230(mob,template,now=111.0) is None,(mid,phase,'double phase')
                checks+=3
    assert checks==396,checks
    return checks

if __name__=='__main__':
    print(f'ERA 103 RAID BOSS AI: {run()} checks PASS',flush=True)
