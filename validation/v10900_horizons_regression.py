# -*- coding: utf-8 -*-
"""v109: actual runtime registries, full map, quests and collision guards."""
from __future__ import annotations
import copy
from collections import deque
from world.v10900_horizons import (install,planned_ids,REGIONS,PARENT,PARENT_ZONE,
                                   prefix,QUEST_COUNTS)
from world.legends_v3100 import OPPOSITE


def fixture():
    return ({PARENT:{'name':'Koniec v107','zone':PARENT_ZONE,'exits':{'south':'old_room'}},
             'old_room':{'name':'Ostatnia droga','zone':PARENT_ZONE,'exits':{'north':PARENT}}},
            {'old_mob':{'name':'Historia'}},[],{}, {},
            {'soul_shard':{'name':'Odłamek Duszy'}},{},{},{},{},{})


def run():
    count=0
    def check(condition,label):
        nonlocal count
        assert condition,label
        count+=1
    initial=fixture()
    old=copy.deepcopy(initial)
    status=install(*initial)
    rooms,mobs,spawns,npcs,quests,items,recipes,zones,categories,guides,power=initial
    check(status['regions']==12 and status['rooms']==288 and status['quests']==360,'12 realms 288 rooms 360 quests')
    check(status['mobs']==168 and status['npcs']==48 and status['items']==60 and status['recipes']==12,'all original assets')
    check(len(status['areas'])==12 and len(spawns)==312,'area catalogue & all real mob spawns')
    check(rooms['old_room']==old[0]['old_room'] and mobs['old_mob']==old[1]['old_mob']
          and items['soul_shard']==old[5]['soul_shard'],'historic game content untouched')
    req=planned_ids()
    for kind,store in [('rooms',rooms),('mobs',mobs),('npcs',npcs),('quests',quests),('items',items),('recipes',recipes)]:
        check(req[kind]<=store.keys(),'complete ID surface: '+kind)
    check(rooms[PARENT]['exits']['east']==prefix(REGIONS[0][0])+'_01','real v107 connection')
    visited=set()
    queue=deque(['old_room'])
    while queue:
        room=queue.popleft()
        if room in visited:continue
        visited.add(room)
        for direction,target in rooms[room]['exits'].items():
            check(target in rooms and rooms[target]['exits'].get(OPPOSITE[direction])==room,
                  'two-way '+room+'/'+direction)
            if target not in visited:queue.append(target)
    check(req['rooms']<=visited and len(visited)==290,'all 288 rooms reachable from old world')
    for i,(slug,name,description,boss1,boss2,enemies,materials) in enumerate(REGIONS):
        p=prefix(slug)
        check(zones[name]==p and categories[p]=='Endgame' and guides[name.casefold()]==p+'_01','zone indexes')
        check(power[p]==90001+i*1000,'power level')
        check(len([x for x in quests if x.startswith(p+'_')])==30,'30 quests')
        check(len([x for x in mobs if x.startswith(p+'_')])==14,'12 creatures + 2 bosses')
        check(len([x for x in spawns if x[1].startswith(p+'_')])==26,'26 real spawns')
        offered=set()
        for j in range(1,5):
            npc=npcs[f'{p}_npc_{j}']
            check(npc['room'] in visited,'npc accessible')
            offered.update(npc['specialist_quests'])
        check(offered=={x for x in quests if x.startswith(p+'_')},'every quest linked to NPC')
        for kind,amount in QUEST_COUNTS.items():
            check(len([x for x in offered if x.startswith(f'{p}_{kind}_')])==amount,'correct type count')
        for j in range(1,15):
            mid=f'{p}_mob_{j}' if j<=12 else f'{p}_boss_{j-12}'
            creature=mobs[mid]
            check(creature['max_hp']>0 and creature['damage']>0 and creature['class_xp_reward']>0,'combat stats')
            check(creature['auto_aggro'] is False and not creature.get('raid'),'solo friendly')
            check(all(x in items for x in creature['drops']),'legitimate drop')
            check(any(key==mid and room in visited for room,key in spawns),'real spawn')
        for qid in offered:
            q=quests[qid]
            check(q['needed']>0 and q['reward_gold']>0 and q['olc_reward_xp']>0,'real progress')
            check(not q.get('raid') and not q.get('party_required'),'no forced group')
            check(all(x in items for x in q.get('reward_items',{})),'real reward item')
            kind=q['kind']
            if kind=='kill':check(q['target'] in mobs and any(x==q['target'] for _,x in spawns),'kill target exists')
            elif kind=='collect':
                check(q['target'] in items and any(q['target'] in mobs[x]['drops'] for _,x in spawns),'collect drop exists')
            elif kind=='talk_npc':check(q['target_npc'] in npcs,'talk npc exists')
            elif kind=='profession_action':check(bool(q['required_profession'] and q['specialist_tool_type']),'profession exists')
            else:raise AssertionError('unsupported quest kind '+kind)
            if q.get('requires_quest'):check(q['requires_quest'] in quests,'story requires existing quest')
    frozen=copy.deepcopy(initial)
    check(install(*initial)['already_installed'] and initial==frozen,'idempotent installation')
    for kind,index,new in [('rooms',0,next(iter(req['rooms']))),('mobs',1,next(iter(req['mobs']))),
                           ('npcs',3,next(iter(req['npcs']))),('quests',4,next(iter(req['quests']))),
                           ('items',5,next(iter(req['items']))),('recipes',6,next(iter(req['recipes'])) )]:
        broken=list(copy.deepcopy(old))
        broken[index][new]={}
        snap=copy.deepcopy(broken)
        try:install(*broken)
        except RuntimeError:pass  # AUDIT_INTENTIONAL_PASS: injected failure expected in negative test
        else:raise AssertionError('collision not rejected: '+kind)
        check(broken==snap,'atomic collision rejection: '+kind)
    broken=list(copy.deepcopy(old))
    broken[0][PARENT]['exits']['east']='already_occupied'
    before=copy.deepcopy(broken)
    try:install(*broken)
    except RuntimeError:pass  # AUDIT_INTENTIONAL_PASS: injected failure expected in negative test
    else:raise AssertionError('parent exit conflict ignored')
    check(broken==before,'existing v107 exit never overwritten')
    print(f'V109 HORIZONS: {count} kontrol PASS, 12 krain, 288 lokacji, 360 questów, 312 spawnów')
    return count

if __name__=='__main__':run()
