# -*- coding: utf-8 -*-
"""Thirty navigable galleries beyond the NORTH border of earlier dungeon wings.

No existing room ID, boss chamber, dungeon-clear condition or quest changes.
A single reversible edge links the old northwest border to the new southern
border for every region; all other edges remain within each new 12x10 gallery.
"""
from __future__ import annotations

from systems.v115.high_level_world import REGIONS
from systems.v116_dungeon_border_wings import HEIGHT as OLD_HEIGHT, wing_id

WIDTH, HEIGHT = 12, 10
ENTRY = (0, 0)
OPPOSITE = {'north':'south', 'south':'north', 'west':'east', 'east':'west'}
LANDMARKS = (
    'Głęboka galeria', 'Kamienny pasaż', 'Opuszczony korytarz',
    'Podziemny most', 'Korytarz echa', 'Cicha komora',
    'Skrzyżowanie sztolni', 'Zapomniany trakt',
)


def gallery_id(index: int, x: int, y: int) -> str:
    return f'v116_deep_gallery_{index:02d}_p_{x:02d}_{y:02d}'


def build_rooms():
    rooms = {}
    for index, reg in enumerate(REGIONS, 1):
        old_border = wing_id(index, 0, OLD_HEIGHT-1)
        for y in range(HEIGHT):
            for x in range(WIDTH):
                rid = gallery_id(index, x, y)
                exits = {}
                if x: exits['west'] = gallery_id(index, x-1, y)
                if x < WIDTH-1: exits['east'] = gallery_id(index, x+1, y)
                if y: exits['south'] = gallery_id(index, x, y-1)
                if y < HEIGHT-1: exits['north'] = gallery_id(index, x, y+1)
                if (x, y) == ENTRY:
                    exits['south'] = old_border
                rooms[rid] = {
                    'zone': f'Dalsze Podziemia — {reg.name}',
                    'name': f'{LANDMARKS[(x + 3*y + index)%len(LANDMARKS)]} — {reg.name}',
                    'desc': (f'Dalsze podziemia {reg.name}. Sektor {x+1}/{WIDTH}, '
                             f'pas {y+1}/{HEIGHT}. Sąsiednie galerie są połączone.'),
                    'generator_level': reg.suggested_level,
                    'v115_region_key': reg.key,
                    'v116_deep_gallery': reg.key,
                    'v1000_landmark': (x+y)%2==0,
                    'exploration_ep': (8+min(12,(x+y)//3)) if (x+y)%2==0 else 0,
                    'exits': exits,
                }
    return rooms


def install_rooms(existing):
    planned = build_rooms()
    if set(planned).intersection(existing):
        raise ValueError('v116: kolizja ID dalszych podziemi')
    anchors=[]
    for index, reg in enumerate(REGIONS,1):
        anchor=wing_id(index,0,OLD_HEIGHT-1)
        old=existing.get(anchor)
        if (not isinstance(old,dict) or old.get('v116_dungeon_wing')!=reg.key
                or old.get('v115_region_key')!=reg.key):
            raise ValueError(f'v116: brak autoryzowanej granicy galerii {anchor}')
        if 'north' in old.get('exits',{}):
            raise ValueError(f'v116: zajęty północny kierunek {anchor}')
        dest=gallery_id(index,*ENTRY)
        if planned[dest]['exits'].get('south')!=anchor:
            raise ValueError(f'v116: brak drogi powrotnej {dest}')
        anchors.append((anchor,dest))
    for rid,room in planned.items():
        for dest in room['exits'].values():
            if dest not in planned and dest not in existing:
                raise ValueError(f'v116: uszkodzona droga {rid}->{dest}')
    existing.update(planned)
    for anchor,dest in anchors:
        existing[anchor]['exits']['north']=dest
    return len(planned)


def build_spawns():
    return [(gallery_id(index,x,y),f'v115_dungeon_{index:02d}_lurker')
            for index,_reg in enumerate(REGIONS,1)
            for y in range(HEIGHT) for x in range(WIDTH) if (x+y)%2==0]
