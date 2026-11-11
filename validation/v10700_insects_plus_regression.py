# -*- coding: utf-8 -*-
"""Phase 7 insect species, true registry and path regression, no live DB."""
from __future__ import annotations

import copy
import os
import sys
from collections import deque
from world.legends_v3100 import OPPOSITE
from world.v10700_insects_expansion import install as stage6_install, planned_ids as stage6_ids, PREFIX as PREV, ZONE
from world.v10700_insects_wildlife_plus import install, planned_ids, PREFIX, HABITATS, INSECTS, MATERIALS
from validation.v10700_insects_expansion_regression import fixture


def run():
    catalog=fixture()
    stage6_install(*catalog)
    rooms, mobs, spawns, npcs, quests, items, topics, aliases=catalog
    previous=copy.deepcopy(catalog)
    result=install(*catalog)
    assert result=={'already_installed':False,'rooms':8,'mobs':24,
                    'spawns':45,'items':4,'npcs':2,'quests':20,
                    'elite_mobs':3,'raids':0}, result
    checks=1
    def check(ok,msg):
        nonlocal checks
        assert ok,msg
        checks+=1
    ids=planned_ids()
    for key, collection in zip(('rooms','mobs','items','npcs','quests'),
                               (rooms,mobs,items,npcs,quests)):
        check(ids[key] <= collection.keys(), 'IDs registered '+key)
    check(stage6_ids()['mobs'].isdisjoint(ids['mobs']), 'no stage6 duplicates')
    check(len([sp for sp in spawns if sp[1] in ids['mobs']])==45,'45 new living spawns')
    check(len([sp for sp in spawns if sp[1] in stage6_ids()['mobs']])==50, 'all stage6 monsters stay')
    check(len({m[0] for m in INSECTS})==24 and sum(m[-1]=='elite' for m in INSECTS)==3,'24 distinct types')
    for slug,name,habitat,element,material,stage,rank in INSECTS:
        mid=f'{PREFIX}_{slug}'
        mob=mobs[mid]
        check(mob['name']==name and mob['generator_level']==stage and mob['quest_target']==mid,
              'actual monster stat entry '+slug)
        check(mob['attack_elements_v11339']==(() if element=='physical' else (element,)), 'native element '+slug)
        check(mob['drops'].get(f'{PREFIX}_{material}',0)>0,'native drop '+slug)
        check(mob['max_hp']>0 and mob['damage']>0 and mob['class_xp_reward']>0 and mob['soul_reward']>0,
              'kill reward '+slug)
        check(not mob.get('auto_aggro') and not mob.get('world_boss'),'solo and not raid '+slug)
        actual=[room for room,m in spawns if m==mid]
        check(len(actual)==(1 if rank=='elite' else 2) and all(r in rooms for r in actual),
              'spawn point '+slug)
    # Every new room reachable from old entrance with reciprocal exits.
    queue=deque([f'v3100_insects_room_00'])
    seen=set(queue)
    while queue:
        rid=queue.popleft()
        for direction,target in rooms[rid].get('exits',{}).items():
            check(target in rooms and rooms[target].get('exits',{}).get(OPPOSITE[direction])==rid,
                  'no one-way or ghost exit '+rid+' '+direction)
            if target not in seen:
                seen.add(target)
                queue.append(target)
    for slug,parent,name,_ in HABITATS:
        rid=f'{PREFIX}_{slug}'
        check(rid in seen and rooms[rid]['zone']==ZONE and rooms[rid]['name']==name,
              'reachable active room '+slug)
        check(f'{PREV}_{parent}' in rooms[rid]['exits'].values(),'returns to stage6 habitat '+slug)
    for i in range(1,17):
        q=quests[f'{PREFIX}_hunt_{i:02d}']
        check(q['target'] in mobs and any(mid==q['target'] for _,mid in spawns), 'quest target spawned')
        check(q['kind']=='kill' and q['needed'] in (1,4) and q['character_xp_reward']>0,
              'hunt has objective and rewards')
    for i in range(1,5):
        q=quests[f'{PREFIX}_collect_{i:02d}']
        check(q['target'] in items and q['kind']=='collect' and q['needed']==3,'material quest exists')
        check(any(m.get('drops',{}).get(q['target'],0)>0 for m in mobs.values()),'collect source drops')
    offered=[qid for npc in npcs.values() if npc.get('v107_insects_plus')
             for qid in npc.get('specialist_quests',())]
    check(len(offered)==20 and set(offered)==ids['quests'],'every quest reachable through new NPCs')
    check(all(npcs[nid]['room'] in seen for nid in ids['npcs']), 'new NPCs accessible')
    check(all(quests[qid]['giver'] in {npcs[nid]['name'] for nid in ids['npcs']} for qid in ids['quests']),
          'giver matches NPC')
    check(aliases['szerszenie']==f'{PREFIX}_region' and aliases['owady_plus'] in topics,
          'additional Polish help')
    check(not any('raid' in q.lower() or 'rajd' in q.lower() for q in ids['quests']),
          'no raid content')
    # Preserve all previous entities byte-for-byte except extra exits in stage6 rooms.
    old_rooms,old_mobs,old_spawns,old_npcs,old_quests,old_items,old_topics,old_aliases=previous
    for oldid,oldrecord in old_rooms.items():
        new=copy.deepcopy(rooms[oldid])
        new['exits']={d:t for d,t in new['exits'].items() if not t.startswith(PREFIX+'_')}
        check(new==oldrecord,'unchanged old room '+oldid)
    for old,cur,label in ((old_mobs,mobs,'mob'),(old_npcs,npcs,'NPC'),
                          (old_quests,quests,'quest'),(old_items,items,'item'),
                          (old_topics,topics,'help'),(old_aliases,aliases,'alias')):
        for oldid,oldrecord in old.items():
            check(cur[oldid]==oldrecord,'unchanged '+label+' '+oldid)
    check(spawns[:len(old_spawns)]==old_spawns,'all old spawns preserved and order stable')
    before=copy.deepcopy(catalog)
    again=install(*catalog)
    check(again['already_installed'] and before==catalog,'idempotence')
    for error in ('collide','missing','blocked','help'):
        candidate=fixture(); stage6_install(*candidate)
        rr,mm,ss,nn,qq,ii,tt,aa=candidate
        if error=='collide': mm[f'{PREFIX}_hornet_royal']={'name':'foreign'}
        elif error=='missing': rr.pop(f'{PREV}_hornets')
        elif error=='blocked': rr[f'{PREV}_hornets']['exits'].update({d:'foreign' for d in OPPOSITE})
        elif error=='help': aa['szerszenie']='foreign'
        prior=copy.deepcopy(candidate)
        try:install(*candidate)
        except RuntimeError:pass  # AUDIT_INTENTIONAL_PASS: expected preflight rejection
        else:raise AssertionError('must block '+error)
        check(candidate==prior,'no half-install on '+error)
    print('V107 OWADY PLUS:', checks,'PASS; 24 potwory, 8 lokacji, 20 questów, 45 spawnów')
    return checks


def real_server():
    os.environ['SOULBOUND_V107_STAGING']='1'
    os.environ['SOULBOUND_V106_STAGING']='0'
    import server
    from world.world_state import World
    assert server.V107_INSECTS_PLUS_BUILD['mobs']==24
    assert server.V107_INSECTS_BUILD['mobs']==26
    assert server.V10700_RAIDS_RETIRED['retired_raids']==35
    for qid in planned_ids()['quests']:
        assert qid in server.QUESTS
    world=World()
    new=[mob for mob in world.mobs.values() if mob.template_id.startswith(PREFIX+'_')]
    old=[mob for mob in world.mobs.values() if mob.template_id.split('__',1)[0] in stage6_ids()['mobs']]
    assert len(new)==45, ('new runtime spawns',len(new))
    assert len(old)==50, ('old runtime spawns',len(old))
    assert all(mob.alive and mob.hp>0 and mob.room_id in server.ROOMS for mob in new+old)
    print('V107 OWADY PLUS: SERVER BOOT PASS, 95 owadzich przeciwników w World()')


if __name__=='__main__':
    if '--server' in sys.argv[1:]:real_server()
    else:run()
