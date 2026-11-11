# -*- coding: utf-8 -*-
"""v1.20.0 world-extension smoke tests against real server catalogs."""
from __future__ import annotations

import asyncio
from collections import deque
from types import SimpleNamespace


def audit_great_world_v1200():
    import server
    from data.catalogs import ROOMS, NPCS, QUESTS, ITEMS, MOB_TEMPLATES
    from player.session_mixins.command_registry import resolve_session_command
    from systems.content_registry import MOB_SPAWNS
    from world.expansions import TREASURE_CHESTS
    from world.great_world import V1200_GATE, V1200_REGIONAL_INDEX, V1200_REGIONS, v1200_rotating_events
    from world.world_state import v0290_event_for_room

    errors = []
    checks = 0

    def check(condition, label):
        nonlocal checks
        checks += 1
        if not condition:
            errors.append(label)

    # The world extension remains installed in later compatible hotfixes.
    check(tuple(int(part) for part in server.VERSION.split('.')[:3]) >= (1, 20, 0), 'release version')
    check(resolve_session_command('krainy')=='greatworld', 'krainy registered')
    check(callable(getattr(server.Session,'great_world_v1200',None)), 'session handler')
    check(len(V1200_REGIONAL_INDEX)==4, 'four authored regions')
    check(V1200_GATE in ROOMS, 'gateway exists')

    # Reachability from the original starting square, respecting directed exits.
    reachable = {'square'}
    queue=deque(['square'])
    while queue:
        rid=queue.popleft()
        for other in ROOMS[rid].get('exits',{}).values():
            if other in ROOMS and other not in reachable:
                reachable.add(other)
                queue.append(other)
    check(V1200_GATE in reachable, 'gateway reachable on foot')
    new_rooms = {V1200_GATE}
    for key, name, theme, element, stage, boss, archivist in V1200_REGIONS:
        spec = V1200_REGIONAL_INDEX[key]
        rooms=set(spec['rooms']) | {spec['town'],spec['archive'],spec['arena']}
        new_rooms.update(rooms)
        check(len(rooms)==19 and len(spec['rooms'])==16, key+' authored topology')
        check(all(r in reachable for r in rooms), key+' walkable from square')
        check(len({ROOMS[r]['name'] for r in spec['rooms']})==16, key+' unique names')
        check(all(ROOMS[r].get('v1200_region')==key for r in rooms), key+' metadata')
        check(all(other in ROOMS for r in rooms for other in ROOMS[r].get('exits',{}).values()), key+' no missing exits')
        check(all(ROOMS[r]['exits'].get(direction)!=r for r in rooms for direction in ROOMS[r].get('exits',{})), key+' no self loops')
        check(spec['relic'] in ITEMS and ITEMS[spec['relic']].get('type')=='armor', key+' relic equips')
        check(spec['resource'] in ITEMS and (ITEMS[spec['resource']].get('sell_silver',0)>0 or ITEMS[spec['resource']].get('sell_gold',0)>0 or ITEMS[spec['resource']].get('sell_mithril',0)>0), key+' resource sells')
        check(spec['arena'] in TREASURE_CHESTS and spec['relic'] in TREASURE_CHESTS[spec['arena']]['set_pool'], key+' boss chest')
        check(all(r not in TREASURE_CHESTS for r in spec['rooms']),key+' no normal floor chests')
        check((spec['arena'], spec['boss']) in MOB_SPAWNS and MOB_TEMPLATES[spec['boss']]['world_boss'],key+' boss fights')
        check(spec['relic'] in MOB_TEMPLATES[spec['boss']]['drops'],key+' boss unique loot')
        check(sum(1 for r,m in MOB_SPAWNS if r in spec['rooms'])>=16,key+' mob density')
        check(sum(1 for n in NPCS.values() if n.get('room') in (spec['town'],spec['archive']))==2,key+' two NPCs')
        gids=tuple(f'v1200_{key}_q{i}' for i in range(1,4))
        check(all(q in QUESTS for q in gids), key+' 3 story quests')
        check(QUESTS[gids[0]]['target']==f'v1200_{key}_hunt' and QUESTS[gids[2]]['target']==spec['boss'],key+' quest targets')
        check(QUESTS[gids[2]]['reward_items'].get(spec['relic'])==1,key+' story relic')
        check(all(QUESTS[gids[i]]['requires_quest']==gids[i-1] for i in (1,2)),key+' quest gates')
    check(len(new_rooms)==77, 'exact 77 new rooms')
    opposite={'north':'south', 'south':'north', 'east':'west', 'west':'east',
              'up':'down', 'down':'up', 'northeast':'southwest', 'southwest':'northeast'}
    check(all(ROOMS[other].get('exits',{}).get(opposite[direction])==rid
              for rid in new_rooms for direction,other in ROOMS[rid].get('exits',{}).items()
              if direction in opposite), 'all new exits reciprocal')
    check(all(QUESTS[qid].get('reward_gold',0)==0 and QUESTS[qid].get('reward_mithril',0)==0
              for key in V1200_REGIONAL_INDEX for qid in (f'v1200_{key}_q{i}' for i in range(1,4))),
          'quests unified currency')


    clock=1760000000.0
    events=v1200_rotating_events(clock)
    check(len(events)==4,'4 real hourly events')
    check(events==v1200_rotating_events(clock), 'fixed event slot deterministic')
    check({e['room_id'].split('_')[1] for e in events}==set(V1200_REGIONAL_INDEX),'one event per region')
    check(all(e['expires_at']==(int(clock//3600)+1)*3600 for e in events),'next hour expiry')
    check(events!=v1200_rotating_events(clock+3600),'rotating each hour')
    check(all(any(e['token']==c['token'] for c in v0290_event_for_room(e['room_id'],clock)) for e in events), 'World event resolver integrated')

    # Actual World encounter path: two reads of one event cannot duplicate its enemy.
    fake = object.__new__(server.World)
    fake.mobs = {}
    fake._last_refresh_at = 0.0
    event = events[0]
    created=fake._ensure_v0290_event_spawns(event['room_id'],now=clock)
    check(len(created)>=1, 'event actual spawn')
    check(any(getattr(m,'v029_event_key','').startswith('v029:v1200:') for m in created),'event tagged and ephemeral')
    count=len(fake.mobs)
    fake._ensure_v0290_event_spawns(event['room_id'],now=clock)
    check(len(fake.mobs)==count,'event not duplicated on re-entry')

    # NVDA command on an actual Session class, without sockets/database writes.
    session = object.__new__(server.Session)
    session.character=SimpleNamespace(room_id='square')
    out=[]
    async def send(line):
        out.append(str(line))
    session.send = send
    async def exercise():
        await session.great_world_v1200('')
        await session.great_world_v1200('Ogrody Zorzy')
        await session.great_world_v1200('wydarzenia')
    asyncio.run(exercise())
    check(any('WIELKI ŚWIAT' in line for line in out),'NVDA short list')
    check(any('Trasa:' in line for line in out),'NVDA step')
    check(any('WYDARZENIA WIELKIEGO ŚWIATA' in line for line in out),'NVDA events')

    return {'checks':checks,'error_count':len(errors),'errors':errors,
            'regions':len(V1200_REGIONAL_INDEX),'new_rooms':len(new_rooms),
            'events':len(events)}


if __name__=='__main__':
    result=audit_great_world_v1200()
    print(result)
    if result['error_count']:
        raise SystemExit(1)
