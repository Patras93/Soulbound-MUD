# -*- coding: utf-8 -*-
"""v105: end-to-end static reachability and spawn validation of 1000 quests.

All checks operate on the final physical world registers, not a generated plan.
No character SQLite or production server writes.
"""
from __future__ import annotations
from collections import deque,Counter
from world.dynamic_content import ROOMS,NPCS,QUESTS,MOB_SPAWNS,MOB_TEMPLATES
from world.v10500_region_index import REGIONS


def run():
    assert 'temple' in ROOMS, 'missing historic entrance'
    seen={'temple'};queue=deque(['temple']);checks=0
    while queue:
        rid=queue.popleft()
        for dst in ROOMS[rid].get('exits',{}).values():
            # Older infinite dungeons generate their destinations lazily.
            # Inspect static v105 rooms; skip unrelated generated destinations.
            if dst not in ROOMS:
                assert not str(dst).startswith('v10500_'),(rid,dst)
                continue
            if dst not in seen:
                seen.add(dst);queue.append(dst)
    spawn_rooms={}
    for room,template in MOB_SPAWNS:
        spawn_rooms.setdefault(template,set()).add(room)
    totals=Counter()
    for slug,_,low,high,_,_ in REGIONS:
        prefix=f'v10500_{slug}'
        region_rooms={f'{prefix}_{i:02d}' for i in range(1,15)}
        assert region_rooms<=seen,('region disconnected',slug,sorted(region_rooms-seen))
        checks+=14
        for ni in range(1,4):
            npc=NPCS[f'{prefix}_npc_{ni}']
            assert npc['room'] in seen,(slug,ni,'npc disconnected')
            checks+=1
        for i in range(1,51):
            if i<=20: kind='story';number=i
            elif i<=35:kind='prof';number=i-20
            elif i<=45:kind='hunt';number=i-35
            else:kind='explore';number=i-45
            qid=f'{prefix}_{kind}_{number:02d}'
            quest=QUESTS[qid]
            possible=[n for n in (NPCS[f'{prefix}_npc_{k}'] for k in (1,2,3)) if qid in n.get('specialist_quests',())]
            assert len(possible)==1 and possible[0]['name']==quest['giver'],(qid,'missing NPC')
            assert possible[0]['room'] in seen,(qid,'unreachable NPC')
            if quest['kind']=='kill':
                target=quest['target']
                assert target in MOB_TEMPLATES,(qid,'missing mob')
                in_region=spawn_rooms.get(target,set()) & region_rooms
                assert in_region and in_region<=seen,(qid,'target has no reachable spawn')
                assert MOB_TEMPLATES[target].get('quest_target')==target,(qid,'kill credit mismatch')
                totals['kill']+=1;checks+=4
            elif quest['kind']=='profession_action':
                assert quest.get('required_profession')==quest['target'],(qid,'profession mismatch')
                assert quest.get('reward_profession')==quest['target'],(qid,'reward mismatch')
                totals['profession_action']+=1;checks+=2
            elif quest['kind']=='explore_frontier':
                assert quest['target']=='any' and quest['needed']>0,(qid,'explore objective')
                totals['explore_frontier']+=1;checks+=1
            else:raise AssertionError((qid,'unknown quest objective',quest['kind']))
            if kind=='story' and number>1:
                assert quest.get('requires_quest')==f'{prefix}_story_{number-1:02d}',(qid,'story chain')
                checks+=1
            assert quest['reward_gold']>0 and quest['reward_items'],(qid,'no guaranteed reward')
            checks+=3
    assert totals=={'kill':600,'profession_action':300,'explore_frontier':100},totals
    assert all(f'v10500_{slug}_boss_{i}' in spawn_rooms for slug,*_ in REGIONS for i in (1,2))
    checks+=41
    return checks,len(seen),totals

if __name__=='__main__':
    checks,reached,totals=run()
    print(f'V105 PHYSICAL QUEST REACHABILITY: {checks} PASS; {reached} reachable rooms; types {dict(totals)}',flush=True)
