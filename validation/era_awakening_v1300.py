# -*- coding: utf-8 -*-
"""Gameplay regression gates for the 1.30.0 authored expansion."""
from __future__ import annotations
from systems.era_awakening_v1300 import (
    REGIONS, ROOMS_SPEC, ORC_ROOMS_SPEC_V1301, region_room, market_factor_v1300,
    attach_expedition_v1300, SPECIAL_LOOT, active_kingdom_war_v1300, WAR_WINDOW_SECONDS_V1300,
)


def audit_awakening_v1300(rooms, npcs, shops, mobs, spawns, quests, items):
    errors=[]
    checks=0
    def check(ok, message):
        nonlocal checks
        checks+=1
        if not ok: errors.append(message)
    # Real directed graph, all rooms navigable and bidirectional.
    for slug, title, city, parent, inbound, outbound, faction, element, level, desc, guardian, monarch in REGIONS:
        root=region_room(slug,'border')
        check(rooms.get(parent,{}).get('exits',{}).get(inbound)==root,f'entrance {slug}')
        seen=set(); stack=[root]
        while stack:
            room_id=stack.pop()
            if room_id in seen: continue
            seen.add(room_id)
            room=rooms.get(room_id)
            check(isinstance(room,dict),f'missing room {room_id}')
            if room is None: continue
            for d,next_room in room.get('exits',{}).items():
                check(next_room in rooms,f'broken exit {room_id} {d}={next_room}')
                if str(next_room).startswith('v1300_'+slug+'_'):
                    rev={'east':'west','west':'east','north':'south','south':'north','up':'down','down':'up'}.get(d)
                    check(rooms.get(next_room,{}).get('exits',{}).get(rev)==room_id,
                          f'one-way exit {room_id} {d} {next_room}')
                    stack.append(next_room)
        check(len(seen)>=len(ORC_ROOMS_SPEC_V1301 if slug=='orc' else ROOMS_SPEC),f'{slug}: explored {len(seen)}')
        for role in ('market','tavern','hall','guild','archive','outpost','citadel','throne'):
            check(region_room(slug,role) in seen,f'{slug}:{role} not accessible')
        check(region_room(slug,'market') in shops,f'{slug} market missing')
        from systems.mercenary_taverns import tavern_here
        check(tavern_here(region_room(slug,'tavern')),f'{slug}: mercenary tavern not active')
        check(quests[f'v1300_{slug}_contract'].get('kind')=='collect_resource',
              f'{slug} contract must use storage-aware resource tracking')
        for key in ('defense','expedition','contract'):
            q=quests.get(f'v1300_{slug}_{key}')
            check(bool(q) and bool(q.get('repeatable')),f'quest {slug}/{key}')
        for key in ('citadel','throne'):
            mid=f'v1300_{slug}_{key}_boss'
            check(mid in mobs and (region_room(slug,key),mid) in spawns,f'{slug} {key} mob')
        for i in (1,2,3):
            check(f'v1300_{slug}_saga_{i}' in quests,f'{slug} saga {i}')
        t0=1728000000
        check(market_factor_v1300(slug,'ore',t0)==market_factor_v1300(slug,'ore',t0+100),
              f'{slug} market same window')
        check(.88 <= market_factor_v1300(slug,'ore',t0) <= 1.30,f'{slug} market bounds')
    for slot in range(9):
        war=active_kingdom_war_v1300(slot*WAR_WINDOW_SECONDS_V1300+120)
        check(war['template_id'] in mobs,f"missing live war boss {war['template_id']}")
        check(war['room_id'] in rooms,f"missing live war location {war['room_id']}")
        check(active_kingdom_war_v1300(slot*WAR_WINDOW_SECONDS_V1300+180)['region']==war['region'],
              f'war front instability {slot}')
    for item in SPECIAL_LOOT:
        check(item in items,f'item missing {item}')
    # Simulate dynamically appearing floor, with no static floor cap.
    for floor_id in ('crypt_floor_100','crypt_floor_400','crypt_floor_1200',
                     'mythic_crypt_floor_100','astral_floor_200',
                     'uoss_deep_dungeon_floor_100_v11331'):
        fake_rooms={floor_id:{'name':floor_id,'zone':'Krypta','exits':{'up':'outside','down':'next'}}}
        fake_mobs={}
        fake_spawns=[]
        check(attach_expedition_v1300(floor_id,fake_rooms,fake_mobs,fake_spawns),f'expedition {floor_id} not attached')
        check(len(fake_spawns)==1,f'expedition {floor_id} mob missing')
        if fake_spawns:
            loc,mid=fake_spawns[0]
            check(loc in fake_rooms and mid in fake_mobs,f'expedition {floor_id} invalid spawn')
            check(not attach_expedition_v1300(floor_id,fake_rooms,fake_mobs,fake_spawns) or len(fake_spawns)==1,
                  f'expedition {floor_id} duplicate')
    from config.balance import PROFESSION_XP_REQUIREMENT_MULTIPLIERS
    from core.profession_timing import TOOL_ACTION_MIN_SECONDS
    check(PROFESSION_XP_REQUIREMENT_MULTIPLIERS['Wędkarstwo']==4.0,'fishing profession XP')
    check(PROFESSION_XP_REQUIREMENT_MULTIPLIERS['Górnictwo']==2.0,'mining XP')
    # Existing actual fishing time is not changed by the profession requirement patch.
    check(TOOL_ACTION_MIN_SECONDS['fishing']==3,'active fishing minimum 3s changed')
    return {'checks':checks,'error_count':len(errors),'errors':errors,
            'authored_rooms':sum(len(ORC_ROOMS_SPEC_V1301 if reg[0]=='orc' else ROOMS_SPEC) for reg in REGIONS),'regions':len(REGIONS)}
