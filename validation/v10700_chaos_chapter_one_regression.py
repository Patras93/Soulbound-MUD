# -*- coding: utf-8 -*-
"""Testy pięciu krain v107: realne struktury, dwukierunkowe trasy i cele."""
from __future__ import annotations

import copy
import os
import sys
from collections import deque

from world.legends_v3100 import OPPOSITE
from world.v10700_chaos_chapter_one import (
    install, planned_ids, CHAPTER_ONE, CHAPTER_ONE_PARENT_ZONE, PARENT,
    QUEST_PARTS, PREFIX,
)


def fixture():
    return (
        {PARENT:{'name':'Historyczny tron v106','zone':CHAPTER_ONE_PARENT_ZONE(),
                 'exits':{},'generator_level':60000}},
        {}, [], {}, {}, {'soul_shard':{'name':'Odłamek Duszy'}}, {}, {}, {}, {}, {},
    )


def run():
    values=fixture()
    original=copy.deepcopy(values)
    result=install(*values)
    rooms,mobs,spawns,npcs,quests,items,recipes,zone_ids,categories,guides,power=values
    expected=planned_ids()
    checks=0
    def check(ok,why):
        nonlocal checks
        assert ok,why
        checks+=1
    check(result['regions']==5 and result['rooms']==100 and result['mobs']==60,
          '5 regions, 100 rooms, 60 unique mob templates')
    check(result['quests']==200 and result['spawns']==110 and result['npcs']==20,
          '200 quests and 110 real spawns, 20 NPC')
    for key,reg in (('rooms',rooms),('mobs',mobs),('npcs',npcs),('quests',quests),
                    ('items',items),('recipes',recipes)):
        check(expected[key] <= reg.keys(), f'all {key} IDs created')
    check(original[0][PARENT]['name']==rooms[PARENT]['name'], 'old room fields preserved')
    check(original[5]['soul_shard']==items['soul_shard'], 'old shard untouched')
    check(rooms[PARENT]['exits']['east']==f'{PREFIX}_{CHAPTER_ONE[0][0]}_01',
          'real v106 -> v107 gateway')
    reached={PARENT}
    queue=deque([PARENT])
    while queue:
        rid=queue.popleft()
        for direction,other in rooms[rid].get('exits',{}).items():
            check(other in rooms and rooms[other].get('exits',{}).get(OPPOSITE[direction])==rid,
                  f'no one-way or missing route {rid}/{direction}')
            if other not in reached:
                reached.add(other)
                queue.append(other)
    check(expected['rooms']<=reached and len(reached)==101, 'all 100 rooms reachable from v106')
    for i,(slug,region,description,boss1,boss2,names,materials) in enumerate(CHAPTER_ONE):
        p=f'{PREFIX}_{slug}'
        check(zone_ids.get(region)==p and categories.get(p)=='Endgame' and
              guides.get(region.casefold())==f'{p}_01', 'native zone indexes '+slug)
        check(power.get(p)==60001+i*1000,'region level power index '+slug)
        check(len([q for q in quests if q.startswith(p+'_')])==40,
              'exactly 40 authored quests '+slug)
        check(len([m for m in mobs if m.startswith(p+'_')])==12,
              '10 mobs and 2 bosses '+slug)
        check(len([s for s in spawns if s[1].startswith(p+'_')])==22,
              'all mobs really placed '+slug)
        check(rooms[f'{p}_12']['zone']==region and rooms[f'{p}_20']['zone']==region,
              'two distinct boss arenas '+slug)
        for no in range(1,13):
            mid=f'{p}_mob_{no}' if no<=10 else f'{p}_boss_{no-10}'
            mob=mobs[mid]
            check(mob.get('auto_aggro')==False and not mob.get('raid'),
                  'no autoaggression or raid '+mid)
            check(mob.get('max_hp',0)>0 and mob.get('damage',0)>0 and mob.get('class_xp_reward',0)>0,
                  'combat and rewards '+mid)
            check(any(target==mid and rid in reached for rid,target in spawns),
                  'reachable actual monster spawn '+mid)
            check(all(item in items for item in mob.get('drops',{})),
                  'existing material loot '+mid)
        npc_names={npcs[f'{p}_npc_{j}']['name'] for j in range(1,5)}
        offered=set()
        for j in range(1,5):
            npc=npcs[f'{p}_npc_{j}']
            check(npc['room'] in reached and npc['room'] in rooms,
                  'living NPC accessible '+str(j)+slug)
            offered.update(npc['specialist_quests'])
        check(offered=={qid for qid in expected['quests'] if qid.startswith(p+'_')},
              'all 40 quests assigned NPCs '+slug)
        for kind,amount in QUEST_PARTS.items():
            check(len([q for q in offered if q.startswith(f'{p}_{kind}_')])==amount,
                  'quest type count '+kind+slug)
        for qid in offered:
            quest=quests[qid]
            check(quest.get('giver') in npc_names and quest['needed']>0,
                  'real giver and count '+qid)
            check(quest.get('reward_gold',0)>0 and quest.get('olc_reward_xp',0)>0 and
                  quest.get('reward_mithril',0)>0,'nonzero native rewards '+qid)
            check(all(k in items for k in quest.get('reward_items',{})),
                  'reward item exists '+qid)
            check(not quest.get('party_required') and not quest.get('raid'),
                  'solo possible '+qid)
            kind=quest['kind']
            if kind=='kill':
                check(quest['target'] in mobs and any(m==quest['target'] for _,m in spawns),
                      'kill goal is physically spawned '+qid)
            elif kind=='collect':
                check(quest['target'] in items and
                      any(m.get('drops',{}).get(quest['target'],0)>0 for m in mobs.values()),
                      'collect goal is dropped by real monster '+qid)
            elif kind=='talk_npc':
                check(quest['target_npc'] in npcs and
                      npcs[quest['target_npc']]['room'] in reached,
                      'talk target exists in real room '+qid)
            elif kind=='profession_action':
                check(bool(quest.get('required_profession')) and
                      bool(quest.get('specialist_tool_type')),
                      'real profession action '+qid)
            else:
                raise AssertionError('unsupported fake quest kind: '+kind)
            if 'requires_quest' in quest:
                check(quest['requires_quest'] in quests and
                      quest['requires_quest'] != qid, 'real story prerequisite '+qid)
    check(len(expected['quests'])==200,'first 200 of projected 1200 regional tasks')
    snapshot=copy.deepcopy(values)
    again=install(*values)
    check(again['already_installed'] and values==snapshot,'complete idempotent repeat')
    # A broken existing corridor must NOT be silently accepted as already built.
    broken=copy.deepcopy(values)
    broken[0][f'{PREFIX}_popiol_08']['exits'].pop('east')
    old_broken=copy.deepcopy(broken)
    try:
        install(*broken)
    except RuntimeError:  # AUDIT_INTENTIONAL_PASS: must reject damaged world layout
        pass
    else:
        raise AssertionError('damaged installed chapter must be rejected')
    check(broken==old_broken,'damaged installed route rejected without mutations')
    for label,change in (
        ('bad parent',lambda a:a[0][PARENT].update(zone='wrong')),
        ('occupied gate',lambda a:a[0][PARENT]['exits'].update(east='foreign')),
        ('no shard',lambda a:a[5].pop('soul_shard')),
        ('existing quest ID',lambda a:a[4].update({next(iter(expected['quests'])):{}})),
        ('existing mob ID',lambda a:a[1].update({next(iter(expected['mobs'])):{}})),
        ('existing room ID',lambda a:a[0].update({f'{PREFIX}_odlamki_11':{}})),
        ('duplicate region name',lambda a:a[7].update({CHAPTER_ONE[0][1]:'foreign'})),
    ):
        candidate=fixture()
        change(candidate)
        old=copy.deepcopy(candidate)
        try:
            install(*candidate)
        except RuntimeError:  # AUDIT_INTENTIONAL_PASS: must reject damaged world layout
            pass
        else:
            raise AssertionError('should reject: '+label)
        check(candidate==old,'failed preflight causes no mutations: '+label)
    print(f'V107 ROZDZIAL I KATALOG: {checks} PASS; 5 krain, 100 lokacji, 60 potworów, 200 questów')
    return checks


def real_server():
    os.environ['SOULBOUND_V107_STAGING']='1'
    os.environ['SOULBOUND_V106_STAGING']='0'
    import server
    from world.world_state import World
    from world.v10700_chaos_chapter_one import planned_ids
    ids=planned_ids()
    build=server.V10700_CHAOS_CHAPTER_ONE_BUILD
    assert build['regions']==5 and build['quests']==200,build
    assert server.V10700_RAIDS_RETIRED['retired_raids']==35
    assert server.V107_INSECTS_BUILD['mobs']==26 and server.V107_INSECTS_PLUS_BUILD['mobs']==24
    assert ids['rooms']<=server.ROOMS.keys()
    assert ids['quests']<=server.QUESTS.keys()
    world=World()
    spawned=[m for m in world.mobs.values() if m.template_id.split('__',1)[0] in ids['mobs']]
    assert len(spawned)==110,('expected 110 actual monsters',len(spawned))
    assert len({m.template_id.split('__',1)[0] for m in spawned})==60
    assert all(m.alive and m.hp>0 and m.room_id in ids['rooms'] for m in spawned)
    from world.v10700_insects_expansion import planned_ids as old_insects_ids
    from world.v10700_insects_wildlife_plus import planned_ids as plus_insects_ids
    for species, count in ((old_insects_ids()['mobs'],50),(plus_insects_ids()['mobs'],45)):
        assert sum(m.template_id.split('__',1)[0] in species for m in world.mobs.values())==count
    assert not any('raid_' in m.template_id for m in world.mobs.values() if m.template_id.startswith(('v10300_','v10400_','v10600_')))
    print('V107 ROZDZIAL I SERWER: PASS, World() 110 nowych i 95 owadzich potworów; 0 rajdów')

if __name__=='__main__':
    real_server() if '--server' in sys.argv[1:] else run()
