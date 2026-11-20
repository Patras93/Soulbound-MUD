# -*- coding: utf-8 -*-
"""Long regular grinding fields in all 30 original Horyzonty dungeons.

Each original 6x4 dungeon keeps every room and boss. An extra 12x10 grid
extends from its east BORDER (5,0); this is part of the same dungeon zone.
The v115 boss-clear contract and the other two v116 wings are unaffected.
"""
from __future__ import annotations
from systems.v115.high_level_world import REGIONS
from systems.v115.regional_dungeons import room_id as old_id

WIDTH, HEIGHT = 12, 10
OPPOSITE = {'east':'west','west':'east','north':'south','south':'north'}
LANDMARKS = ('Kamienny trakt', 'Szeroka galeria', 'Podziemne rozdroże',
             'Pasaż echa', 'Skalna komnata', 'Zawalony krużganek',
             'Głęboka sztolnia', 'Zimny korytarz')

def sector_id(index, x, y):
    return f'v11625_main_dungeon_{index:02d}_p_{x:02d}_{y:02d}'

def build_rooms():
    created = {}
    for index, reg in enumerate(REGIONS, 1):
        anchor = old_id(reg.key, 5, 0)
        for y in range(HEIGHT):
            for x in range(WIDTH):
                rid = sector_id(index, x, y)
                exits = {}
                if x: exits['west'] = sector_id(index,x-1,y)
                if x < WIDTH - 1: exits['east'] = sector_id(index,x+1,y)
                if y: exits['south'] = sector_id(index,x,y-1)
                if y < HEIGHT - 1: exits['north'] = sector_id(index,x,y+1)
                if (x,y) == (0,0): exits['west'] = anchor
                created[rid] = {
                    'zone':f'Podziemia — {reg.name}',
                    'name':f'{LANDMARKS[(index+3*x+5*y)%len(LANDMARKS)]} — {reg.name}',
                    'desc':(f'Podziemia {reg.name}, szeroki sektor {x+1}/{WIDTH}, '
                            f'pas {y+1}/{HEIGHT}. Ścieżki prowadzą w wiele stron.'),
                    'v115_region_key':reg.key,
                    'v11625_main_dungeon_expanse':reg.key,
                    # Do not mark as v115_dungeon_key. Boss completion requires
                    # an authenticated kill at the original (5,3) chamber.
                    'generator_level':reg.suggested_level,
                    'exploration_ep':0,
                    'exits':exits,
                }
    return created

def build_spawns():
    return [(sector_id(index,x,y),f'v115_dungeon_{index:02d}_lurker')
            for index,_reg in enumerate(REGIONS,1)
            for y in range(HEIGHT) for x in range(WIDTH) if (x+y)%2==0]

def install_rooms(existing):
    """Validate every anchor and reciprocal edge before modifying catalog."""
    planned=build_rooms()
    if set(planned).intersection(existing):
        raise ValueError('v116.00.25: kolizja identyfikatorów nowych sektorów')
    anchors=[]
    for index,reg in enumerate(REGIONS,1):
        anchor=old_id(reg.key,5,0)
        room=existing.get(anchor)
        if (not isinstance(room,dict)
                or room.get('v115_dungeon_key')!=reg.key
                or room.get('v115_region_key')!=reg.key
                or room.get('zone')!=f'Podziemia — {reg.name}'):
            raise ValueError(f'v116.00.25: brak poprawnego krańca: {anchor}')
        if 'east' in room.get('exits',{}):
            raise ValueError(f'v116.00.25: zajęty wschodni kraniec: {anchor}')
        entry=sector_id(index,0,0)
        if planned[entry]['exits'].get('west')!=anchor:
            raise ValueError(f'v116.00.25: brak powrotu z {entry}')
        anchors.append((anchor,entry))
    allowed={(entry,'west',anchor) for anchor,entry in anchors}
    for rid,room in planned.items():
        for way,target in room['exits'].items():
            if target in planned:
                if planned[target]['exits'].get(OPPOSITE[way])!=rid:
                    raise ValueError(f'v116.00.25: nieodwracalne przejście {rid}')
            elif (rid,way,target) not in allowed:
                raise ValueError(f'v116.00.25: nielegalne przejście {rid}->{target}')
    existing.update(planned)
    for anchor,entry in anchors:
        existing[anchor]['exits']['east']=entry
    return len(planned)
