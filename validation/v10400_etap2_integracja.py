# -*- coding: utf-8 -*-
"""Test realnych rejestrow po bootstrapie, bez uruchamiania TCP i bez DB."""
from __future__ import annotations


def run():
    from world import dynamic_content as world
    from systems.quest_reward_floor_v1020012 import quest_xp_plan
    from core.classes_skills import CLASSES
    counts=world.V10400_REGIONS_BUILD
    expected={'regions':10,'rooms':140,'mobs':100,'npcs':30,'quests':480,
              'story_quests':120,'profession_quests':140,'class_quests':10*len(CLASSES),
              'items':50,'recipes':20}
    checks=0
    def ok(value,msg):
        nonlocal checks
        if not value:raise AssertionError(msg)
        checks+=1
    for k,v in expected.items():ok(counts[k]==v,f'bootstrap count {k}')
    ok(world.ROOMS['v10300_tron_12']['exits']['east']=='v10400_sztorm_01','world linked v103')
    ok(world.ROOMS['v10400_sztorm_01']['exits']['west']=='v10300_tron_12','world return v103')
    ok(world.ROOMS['v10400_tron_14']['name'].startswith('Tron Władcy'),'last room')
    for qid,q in world.QUESTS.items():
        if not qid.startswith('v10400_'):continue
        rewards=quest_xp_plan(qid,q)
        ok(rewards['character']>=200_000,f'character XP {qid}')
        ok(rewards['stats'] and min(rewards['stats'].values())>=200_000,f'stat XP {qid}')
        if '_prof_' in qid:
            ok(rewards['profession']>=200_000 and rewards['tool']>=200_000,
               f'profession and tool XP {qid}')
            ok(rewards['class_xp']==0,f'no profession fight XP {qid}')
        elif '_class_' in qid:
            ok(rewards['class_xp']>=200_000,f'class mastery XP {qid}')
    for region in counts['areas']:
        ok(region['id'] in world.EXP_AREA_BASE_CATEGORY, f'area missing {region["id"]}')
        ok(region in world.EXP_AREAS, f'exp areas missing {region["id"]}')
        ok(region['name'] in world.EXP_ZONE_AREA_ID,f'zone map missing {region["id"]}')
    return checks, expected


if __name__=='__main__':
    n,summary=run()
    print(f'V104 ETAP 2 BOOTSTRAP: {n} sprawdzeń PASS, '
          f'{summary["regions"]} krain, {summary["quests"]} questów',flush=True)
