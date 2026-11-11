# -*- coding: utf-8 -*-
"""v107 insect realm addition: real dictionary catalog and topology contract."""
from __future__ import annotations

import copy
import os
import sys
from collections import deque

from world.v10700_insects_expansion import (install, INSECTS, MATERIALS, HABITATS,
                                           PREFIX, LEGACY, ZONE, planned_ids)
from world.legends_v3100 import OPPOSITE


def fixture():
    rooms = {}
    for index in range(12):
        exits = {}
        if index:
            exits['west'] = f'{LEGACY}_room_{index-1:02d}'
        if index < 11:
            exits['east'] = f'{LEGACY}_room_{index+1:02d}'
        rooms[f'{LEGACY}_room_{index:02d}'] = {
            'name': f'Stary pokój owadów {index}', 'zone': ZONE,
            'exits': exits, 'generator_level': 120, 'recommended_mastery': 120,
        }
    npcs = {'legacy_npc': {'name': 'Posłanka Myrra', 'room': f'{LEGACY}_room_00'}}
    mobs = {'legacy_mob': {'name': 'Wściekły Szerszeń', 'max_hp': 10000}}
    spawns = [(f'{LEGACY}_room_05', 'legacy_mob')]
    quests = {'legacy_quest': {'target': 'legacy_mob', 'kind': 'kill', 'reward_items': {}}}
    items = {'soul_shard': {'name': 'Odłamek Duszy'}, 'legacy_item': {'name': 'Jajo Królowej'}}
    return rooms, mobs, spawns, npcs, quests, items, {}, {}


def verify(rooms, mobs, spawns, npcs, quests, items, topics, aliases):
    count = 0
    def check(state, why):
        nonlocal count
        assert state, why
        count += 1
    ids = planned_ids()
    check(tuple(sorted(map(len, (ids['rooms'], ids['mobs'], ids['items'], ids['npcs'], ids['quests'])))) ==
          (2, 5, 8, 20, 26), 'expected exact counts')
    for kind, actual in [('rooms',rooms),('mobs',mobs),('items',items),('npcs',npcs),('quests',quests)]:
        check(ids[kind] <= actual.keys(), 'all registered: '+kind)
    check('legacy_mob' in mobs and 'legacy_quest' in quests and 'legacy_item' in items,
          'legacy IDs preserved')
    check('owady' in aliases and aliases['owady'] in topics, 'NVDA-friendly help')
    check(len([s for s in spawns if s[1] in ids['mobs']]) == 50, '50 new real spawns')
    check(not any(mobs[mid].get('auto_aggro') for mid in ids['mobs']), 'no forced combat')
    for slug, name, source, element, material, offset, rank in INSECTS:
        mid = f'{PREFIX}_{slug}'
        record = mobs[mid]
        check(record['name']==name and record['quest_target']==mid, 'unique active enemy')
        check(record['rank']==rank and record['max_hp']>0 and record['damage']>0,
              'actual combat statistics')
        check(record.get('attack_elements_v11339') == (() if element=='physical' else (element,)),
              'real engine elements')
        check(record['drops'].get(f'{PREFIX}_{material}', 0)>0, 'real collectible loot')
        check(record['world_boss'] is False and record['stationary_mob'] is True,
              'solo mob not a raid')
        places = [rid for rid, enemy in spawns if enemy==mid]
        check(len(places)==(1 if rank=='elite' else 2) and all(r in rooms for r in places),
              'spawns reachable places')
    queue = deque([f'{LEGACY}_room_00'])
    reached = set(queue)
    while queue:
        start = queue.popleft()
        for direction, target in rooms[start].get('exits', {}).items():
            check(target in rooms and rooms[target].get('exits',{}).get(OPPOSITE[direction]) == start,
                  'bidirectional exit '+start+':'+direction)
            if target not in reached:
                reached.add(target)
                queue.append(target)
    for rid in ids['rooms']:
        check(rid in reached, 'new room reachable from old insect entrance')
        check(rooms[rid].get('zone')==ZONE and rooms[rid].get('v107_insects'), 'same old realm')
    for i in range(1, 16):
        q=quests[f'{PREFIX}_hunt_{i:02d}']
        check(q['kind']=='kill' and q['target'] in mobs and
              any(mid==q['target'] for _,mid in spawns), 'hunt has a spawned target')
        check(q['needed'] > 0 and q.get('character_xp_reward',0)>0,
              'hunt objective and rewards')
    for i in range(1,6):
        q=quests[f'{PREFIX}_collect_{i:02d}']
        check(q['kind']=='collect' and q['target'] in items, 'collect item exists')
        check(any(mob.get('drops', {}).get(q['target'], 0)>0 for mob in mobs.values()),
              'real item drop from wildlife')
    offered = [qid for n in npcs.values() if n.get('v107_insects') for qid in n.get('specialist_quests', ())]
    check(len(offered)==20 and set(offered)==ids['quests'], 'all 20 quests offered by reachable NPCs')
    check(all(npcs[nid]['room'] in reached for nid in ids['npcs']), 'NPC rooms reachable')
    check(all(q['giver'] in [n['name'] for n in npcs.values()] for q in quests.values() if q.get('v107_insects')),
          'quest giver names resolve')
    check(not any('rajd' in q.get('name', '').lower() for q in quests.values()), 'no raids')
    return count


def main():
    if '--server' in sys.argv[1:]:
        os.environ['SOULBOUND_V107_STAGING'] = '1'
        os.environ['SOULBOUND_V106_STAGING'] = '0'
        import server
        w=server
        build=w.V107_INSECTS_BUILD
        assert build['rooms']==8 and build['mobs']==26 and build['quests']==20, build
        assert w.V107_MAGITEK_ADDED and w.V107_MAGITEK_GUILD_QUESTS
        assert w.V10700_RAIDS_RETIRED['retired_raids']==35
        count = 0
        for slug, *_ in INSECTS:
            mid=f'{PREFIX}_{slug}'
            assert mid in w.MOB_TEMPLATES and any(mid==enemy for _, enemy in w.MOB_SPAWNS)
            count+=1
        assert all(quest in w.QUESTS for quest in planned_ids()['quests'])
        assert all(w.ROOMS[room]['exits'] for room in planned_ids()['rooms'])
        from world.world_state import World
        state=World()
        actual=[m for m in state.mobs.values() if m.template_id.split('__',1)[0] in planned_ids()['mobs']]
        assert len(actual)==50, ('new living monsters not spawned', len(actual))
        assert all(m.alive and m.hp>0 and m.room_id in w.ROOMS for m in actual)
        print('V107 OWADY: PRAWDZIWY BOOTSTRAP',count+6,
              'kontroli PASS; realne 50 potworów w World()')
        return
    *registry, = fixture()
    rooms, mobs, spawns, npcs, quests, items, topics, aliases = registry
    legacy = copy.deepcopy((rooms,mobs,spawns,npcs,quests,items))
    result = install(*registry)
    assert result == {'already_installed': False, 'rooms':8, 'mobs':26,
                      'spawns':50, 'items':5, 'npcs':2, 'quests':20,
                      'elite_mobs':2, 'raids':0}, result
    checks = verify(*registry)
    for catalog, old in zip((rooms,mobs,spawns,npcs,quests,items), legacy):
        if isinstance(catalog,list):
            assert all(entry in catalog for entry in old)
        else:
            for key,val in old.items():
                if key in rooms and key.startswith(LEGACY+'_room_'):
                    new = copy.deepcopy(catalog[key])
                    new['exits'] = {d:v for d,v in new['exits'].items() if not v.startswith(PREFIX+'_')}
                    assert new == val, ('unexpected legacy room rewrite',key)
                else:assert catalog[key] == val, ('legacy entry modified',key)
        checks+=1
    before=copy.deepcopy(registry)
    again=install(*registry)
    assert again['already_installed'] and registry==before
    checks+=2
    # Guard every partial/foreign state and ensure no half-installation.
    for error in ('collision', 'no_realm', 'no_exits', 'occupied_npc', 'help'):
        value=fixture()
        rm,mb,sp,np,q,it,tp,al=value
        if error=='collision':rm[f'{PREFIX}_hornets']={'name':'foreign'}
        elif error=='no_realm':rm.pop(f'{LEGACY}_room_05')
        elif error=='no_exits':
            room=rm[f'{LEGACY}_room_05']
            room['exits'].update({d:'blocking_room' for d in OPPOSITE})
        elif error=='occupied_npc':np['foreign']={'name':'new NPC','room':f'{LEGACY}_room_03'}
        else:al['owady']='foreign_help'
        old=copy.deepcopy(value)
        try:install(*value)
        except RuntimeError:pass  # AUDIT_INTENTIONAL_PASS: expected preflight rejection
        else:raise AssertionError('expected refusal: '+error)
        assert old==value, ('changed data on refused install', error)
        checks+=2
    assert len(INSECTS)==26 and sum(m[-1]=='elite' for m in INSECTS)==2
    checks+=2
    print('V107 KRAINA OWADÓW:',checks,'kontroli PASS; 8 lokacji, 26 owadów, 20 zadań')

if __name__ == '__main__':
    main()
