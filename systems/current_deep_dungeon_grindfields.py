# -*- coding: utf-8 -*-
"""v116.00.28: large optional UOSS Deep Dungeon floors.

The canonical landing, personal Apanda checkpoint and elevators are untouched.
Only regular mobs copied from the current floor can spawn in the new maze.
"""
from __future__ import annotations

WIDTH = 12
HEIGHT = 12
OPPOSITES = {"east":"west", "west":"east", "north":"south", "south":"north"}


def _room_id(canonical, offset):
    return f"{canonical}_v11628_{offset:03d}"


def expand_deep_dungeon(canonical, pairs, runtime=False):
    from data.rooms import ROOMS
    from data.mobs import MOB_TEMPLATES
    from systems.content_registry import MOB_SPAWNS
    from world.uoss_superboss_world import (
        uoss_deep_dungeon_floor_id_v11331,
        uoss_deep_dungeon_floor_number_v11331,
    )
    from data import catalog_mutations as catalog

    floor = uoss_deep_dungeon_floor_number_v11331(canonical)
    if floor is None or canonical != uoss_deep_dungeon_floor_id_v11331(floor):
        return list(pairs)
    if canonical not in ROOMS:
        return list(pairs)
    first = _room_id(canonical, 0)
    if first in ROOMS:  # idempotency; keep original pairs on repeated calls
        return list(pairs)

    # The landing is the START/border of the floor. Preserve both vertical
    # exits: the old Apanda boss and deepelevator rules depend on those IDs.
    base = ROOMS[canonical]
    exits = base.get('exits', {})
    side = next((d for d in ('east','west','north','south') if d not in exits), None)
    if side is None:
        raise RuntimeError(f'Brak bocznego wyjścia na piętrze Deep Dungeon {floor}')
    back = OPPOSITES[side]
    # If side=east, enter at the WEST edge of the grid; similarly for other directions.
    start_xy = {'east': (0,0), 'west': (WIDTH-1,0),
                'north': (0,HEIGHT-1), 'south': (0,0)}[side]
    ids = {(x,y):_room_id(canonical,y*WIDTH+x)
           for y in range(HEIGHT) for x in range(WIDTH)}
    if any(rid in ROOMS for rid in ids.values()):
        raise RuntimeError('Kolizja identyfikatorów galerii Deep Dungeon')

    for (x,y),rid in ids.items():
        catalog.catalog_assign({
            'zone': base['zone'],
            'name': f'Deep Dungeon {floor} — rozległy sektor {x+1}/{y+1}',
            'desc': 'Duży sektor piętra Deep Dungeon. Korytarze łączą się w pętle.',
            'exits': {},
            'procedural_dynamic': True,
            'generated_on_demand': True,
            'uoss_deep_dungeon': True,
            'uoss_deep_dungeon_floor': floor,
            'recommended_level': base.get('recommended_level',95+floor),
            'generator_level': base.get('generator_level',95+floor),
            'exploration_ep': 0,
            'v11628_grindfield': True,
        }, 'ROOMS', ROOMS, (rid,))
    for (x,y),rid in ids.items():
        if x+1 < WIDTH:
            other=ids[(x+1,y)]
            catalog.catalog_assign(other,'ROOMS',ROOMS,(rid,'exits','east'))
            catalog.catalog_assign(rid,'ROOMS',ROOMS,(other,'exits','west'))
        if y+1 < HEIGHT:
            other=ids[(x,y+1)]
            catalog.catalog_assign(other,'ROOMS',ROOMS,(rid,'exits','south'))
            catalog.catalog_assign(rid,'ROOMS',ROOMS,(other,'exits','north'))
    start = ids[start_xy]
    if back in ROOMS[start]['exits']:
        raise RuntimeError('Zajęte wejście do nowego sektora Deep Dungeon')
    catalog.catalog_assign(start,'ROOMS',ROOMS,(canonical,'exits',side))
    catalog.catalog_assign(canonical,'ROOMS',ROOMS,(start,'exits',back))

    regular=[]
    for rid,tid in pairs:
        if rid != canonical or tid not in MOB_TEMPLATES:
            continue
        template=MOB_TEMPLATES[tid]
        if any(template.get(k) for k in ('boss','mini_boss','boss_mechanic',
                  'uoss_deep_dungeon_apanda_floor','uoss_superboss','stationary_mob')):
            continue
        if tid not in regular:
            regular.append(tid)
    extras=[]
    if regular:
        for i in range(0,WIDTH*HEIGHT,2):
            extras.append((_room_id(canonical,i),regular[(i//2)%len(regular)]))
    if runtime:
        return list(pairs)+extras
    MOB_SPAWNS.extend(extras)
    return list(pairs)


def deep_dungeon_saved_side_parent(room_id):
    """Recognize only genuine 12x12 side-room IDs from a saved position.

    Does not expand or grant access to a floor; personal unlock/boss checks
    still belong to the existing movement and checkpoint code.
    """
    room_id = str(room_id or "")
    # Normal room movement is a hot path. Do not import/regex for it.
    if not room_id.startswith("uoss_deep_dungeon_floor_") or "_v11628_" not in room_id:
        return None
    import re
    from world.uoss_superboss_world import uoss_deep_dungeon_floor_id_v11331

    found = re.fullmatch(
        r"uoss_deep_dungeon_floor_([1-9][0-9]*)_v11331_v11628_([0-9]{3})",
        room_id,
    )
    if found is None or int(found.group(2)) >= WIDTH * HEIGHT:
        return None
    return uoss_deep_dungeon_floor_id_v11331(int(found.group(1)))
