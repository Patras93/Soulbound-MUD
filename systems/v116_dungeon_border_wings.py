# -*- coding: utf-8 -*-
"""Optional border wings for the thirty fixed dungeons. Never move their bosses.

All original dungeon identifiers, boss locations, 24-room shapes and objective
contracts remain untouched. Wings attach at an existing BORDER chamber (0,3).
"""
from __future__ import annotations
from systems.v115.high_level_world import REGIONS
from systems.v115.regional_dungeons import room_id as original_room_id

WIDTH, HEIGHT = 12, 10  # 120 new rooms per existing 24-room dungeon
ENTRANCE_X, ENTRANCE_Y = WIDTH-1, 0
OPPOSITE = {'north':'south', 'south':'north', 'east':'west', 'west':'east'}
ROOM_NAMES = ('Stara Galeria','Głęboki Korytarz','Zawalony Trakt','Kamienna Sala',
              'Podziemne Rozstaje','Wąski Przesmyk','Skalny Most','Zapomniana Komora')

def wing_id(index:int,x:int,y:int)->str:
    return f'v116_dungeon_wing_{index:02d}_p_{x:02d}_{y:02d}'

def build_rooms():
    result={}
    for index,reg in enumerate(REGIONS,1):
        for y in range(HEIGHT):
            for x in range(WIDTH):
                exits={}
                if x: exits['west']=wing_id(index,x-1,y)
                if x<WIDTH-1: exits['east']=wing_id(index,x+1,y)
                if y: exits['south']=wing_id(index,x,y-1)
                if y<HEIGHT-1: exits['north']=wing_id(index,x,y+1)
                if (x,y)==(ENTRANCE_X,ENTRANCE_Y):
                    exits['east']=original_room_id(reg.key,0,3)
                result[wing_id(index,x,y)]={
                    'zone':f'Rozległe Podziemia — {reg.name}',
                    'name':f'{ROOM_NAMES[(x+3*y+index)%len(ROOM_NAMES)]} — {reg.name}',
                    'desc':(f'Boczne podziemia {reg.name}. Sektor {x+1}/{WIDTH}, '
                            f'pas {y+1}/{HEIGHT}. Połączenia z sąsiednimi komnatami.'),
                    'generator_level':reg.suggested_level,
                    'v115_region_key':reg.key,
                    # IMPORTANT: do not mark a wing as a historical v115 dungeon
                    # boss chamber. Old dungeon completion stays at (5,3).
                    'v116_dungeon_wing':reg.key,
                    'v1000_landmark':(x+y)%2==0,
                    'exploration_ep':(8+min(12,(x+y)//3)) if (x+y)%2==0 else 0,
                    'exits':exits,
                }
    return result

def install_rooms(existing):
    planned=build_rooms()
    if set(existing)&set(planned):
        raise ValueError('v116: konflikt identyfikatorów nowych podziemi')
    anchors=[]
    for index,reg in enumerate(REGIONS,1):
        anchor=original_room_id(reg.key,0,3)
        src=existing.get(anchor)
        if (not isinstance(src,dict) or src.get('v115_dungeon_key')!=reg.key
                or src.get('v115_region_key')!=reg.key):
            raise ValueError(f'v116: niezgodny punkt wejścia podziemi {anchor}')
        if 'west' in src.get('exits',{}):
            raise ValueError(f'v116: kierunek west zajęty {anchor}')
        dst=wing_id(index,ENTRANCE_X,ENTRANCE_Y)
        if planned[dst]['exits'].get('east')!=anchor:
            raise ValueError(f'v116: brak powrotu z {dst}')
        anchors.append((anchor,dst))
    for rid,room in planned.items():
        for dest in room['exits'].values():
            if dest not in planned and dest not in existing:
                raise ValueError(f'v116: brak celu {rid}->{dest}')
    existing.update(planned)
    for anchor,dst in anchors:
        existing[anchor]['exits']['west']=dst
    return len(planned)

def build_spawns():
    return [(wing_id(index,x,y),f'v115_dungeon_{index:02d}_lurker')
            for index,_reg in enumerate(REGIONS,1)
            for y in range(HEIGHT) for x in range(WIDTH) if (x+y)%2==0]
