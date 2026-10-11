# -*- coding: utf-8 -*-
"""Route planning and honest quest NPC journey coverage (v2.32.0).

World graph reachability is NOT proof of a playable route: gates, teleport
requirements, combat and rewards are verified only by actual TCP scenarios.
"""
from __future__ import annotations
from collections import deque, Counter
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def shortest_route(rooms, origin, destination):
    if origin not in rooms or destination not in rooms:
        return None
    if origin == destination:
        return []
    queue = deque([origin])
    previous = {origin: None}
    while queue:
        room_id = queue.popleft()
        for direction, next_id in (rooms[room_id].get('exits') or {}).items():
            if not isinstance(next_id, str) or next_id not in rooms or next_id in previous:
                continue
            previous[next_id] = (room_id, direction)
            if next_id == destination:
                path = []
                node = destination
                while previous[node] is not None:
                    parent, step = previous[node]
                    path.append(step)
                    node = parent
                return list(reversed(path))
            queue.append(next_id)
    return None


def audit_world_npc_routes(rooms, npcs, quests):
    """Classify graph-only candidate journeys without claiming gameplay PASS."""
    if 'temple' not in rooms or 'temple_basement' not in rooms:
        raise AssertionError('Brak sciezki bazowej Swiatyni/Piwnicy')
    rat_route = shortest_route(rooms, 'temple', 'temple_basement')
    if not rat_route or rooms['temple']['exits'].get(rat_route[0]) != 'temple_basement':
        raise AssertionError('Autogracz nie moze odnalezc zejscia do Piwnicy')
    if 'priest_elor' not in npcs or npcs['priest_elor'].get('room') != 'temple':
        raise AssertionError('Kaplan Elor nie znajduje sie w Swiatyni')
    if 'temple_rats' not in quests or quests['temple_rats'].get('target') != 'temple_rat':
        raise AssertionError('Zadanie szczury ma nieznany cel')

    # Starter courier should always have a reachable giver AND receiver,
    # even if the historical private-NPC generator moves the NPC away from
    # its original location in data/npcs.py.
    archivist = npcs.get('archivist') or {}
    smith = npcs.get('doran') or {}
    sol_room = archivist.get('room')
    smith_room = smith.get('room')
    sol_route = shortest_route(rooms, 'temple', sol_room)
    smith_route = shortest_route(rooms, sol_room, smith_room)
    if sol_route is None or smith_route is None:
        raise AssertionError('Starter courier missing reachable NPC route: '
                             + repr((sol_room, smith_room)))
    if ('sol_starter_blacksmith_delivery' in quests
            and quests['sol_starter_blacksmith_delivery'].get('target_npc') != 'doran'):
        raise AssertionError('Starter courier target drifted away from Doran')

    # One BFS through the graph, rather than 1500 full scans.
    candidates = {}
    by_name = {}
    for npc_id, npc in npcs.items():
        room_id = npc.get('room')
        if isinstance(room_id, str) and room_id in rooms:
            candidates[npc_id] = room_id
            by_name.setdefault(str(npc.get('name', '')).casefold(), []).append(room_id)
    counts = Counter()
    missing = Counter()
    for qid, quest in quests.items():
        giver = str(quest.get('giver') or '').casefold()
        target_npc_id = str(quest.get('target_npc') or '')
        if not giver and not target_npc_id:
            missing['no_giver_or_target'] += 1
            continue
        if giver and giver in by_name:
            counts['giver_npc_mapped'] += 1
        else:
            missing['giver_npc_not_named'] += 1
        if target_npc_id:
            if target_npc_id in candidates:
                counts['target_npc_mapped'] += 1
            else:
                missing['target_npc_not_found'] += 1
    return {'checks': 5 + len(quests), 'quest_count': len(quests),
            'rat_route': rat_route, 'courier_to_sol': sol_route,
            'courier_to_doran': smith_route, 'mapped': dict(counts), 'unknown': dict(missing)}


def selftest():
    rooms = {'temple': {'exits': {'down': 'basement'}},
             'basement': {'exits': {'up': 'temple', 'north': 'cave'}},
             'cave': {'exits': {'south': 'basement'}},
             'island': {'exits': {}}}
    assert shortest_route(rooms, 'temple', 'cave') == ['down', 'north']
    assert shortest_route(rooms, 'cave', 'temple') == ['south', 'up']
    assert shortest_route(rooms, 'temple', 'island') is None
    assert shortest_route(rooms, 'temple', 'temple') == []
    assert shortest_route(rooms, 'fake', 'temple') is None
    # Graph cycle may not make route inaccessible or loop indefinitely.
    rooms['cave']['exits']['northeast'] = 'temple'
    assert shortest_route(rooms, 'basement', 'temple') == ['up']
    return 6


def main():
    checks = selftest()
    from data.rooms import ROOMS
    from data.npcs import NPCS
    from data.quests import QUESTS
    result = audit_world_npc_routes(ROOMS, NPCS, QUESTS)
    print('AUTOGRACZ v2.32.0 TRASY: '+str(checks)+' testow BFS PASS; '+
          f'{result["checks"]} kontroli katalogu statycznego PASS')
    print('AUTOGRACZ TRASA: Swiatynia -> Piwnica: '+', '.join(result['rat_route']))
    print('MAPOWANIE NPC: '+str(result['mapped']))
    print('NOT TESTED: przejscia przez blokady fabularne, caly katalog dynamiczny, '
          'walka i odbior nagrod — badane oddzielnie przez TCP.')

if __name__ == '__main__':
    main()
