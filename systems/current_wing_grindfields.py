# -*- coding: utf-8 -*-
"""v116.00.26 — 60 regular dungeon wings expanded from 120 to 144 rooms.

All 120 previously authored rooms of each wing/gallery retain every exit;
exactly one new east edge from a previously unused OUTER border is added.
Cross-zone links remain at both original map borders.
"""
from __future__ import annotations
from systems.v115.high_level_world import REGIONS
from systems.v116_dungeon_border_wings import wing_id
from systems.v116_deep_galleries import gallery_id

WIDTH, HEIGHT = 6, 4
OPPOSITES = {'west':'east','east':'west','south':'north','north':'south'}
TYPES = (
    ('wing', wing_id, 'Rozległe Podziemia', 'v116_dungeon_wing'),
    ('gallery', gallery_id, 'Dalsze Podziemia', 'v116_deep_gallery'),
)
LANDMARKS = ('Szeroka komnata','Kręty trakt','Podziemny plac',
             'Kamienny chodnik','Otwarta galeria','Wielkie rozdroże')

def sector_id(kind, index, x, y):
    if kind not in ('wing','gallery') or not (0 <= x < WIDTH and 0 <= y < HEIGHT):
        raise ValueError('Niepoprawny sektor bocznych podziemi')
    return f'v11626_{kind}_{index:02d}_p_{x:02d}_{y:02d}'

def boundary_anchor(kind,index):
    return (wing_id if kind=='wing' else gallery_id)(index,11,8)

def build_rooms():
    result={}
    for kind,_oldid,zone_prefix,tag in TYPES:
        for index,reg in enumerate(REGIONS,1):
            anchor=boundary_anchor(kind,index)
            for y in range(HEIGHT):
                for x in range(WIDTH):
                    rid=sector_id(kind,index,x,y)
                    exits={}
                    if x:exits['west']=sector_id(kind,index,x-1,y)
                    if x+1<WIDTH:exits['east']=sector_id(kind,index,x+1,y)
                    if y:exits['south']=sector_id(kind,index,x,y-1)
                    if y+1<HEIGHT:exits['north']=sector_id(kind,index,x,y+1)
                    if (x,y)==(0,0):exits['west']=anchor
                    result[rid]={
                        'zone':f'{zone_prefix} — {reg.name}',
                        'name':f'{LANDMARKS[(index+2*x+3*y)%len(LANDMARKS)]} — {reg.name}',
                        'desc':f'Rozległa odnoga podziemi {reg.name}. Sektor {x+1}/{WIDTH}, pas {y+1}/{HEIGHT}.',
                        'generator_level':reg.suggested_level,
                        'v115_region_key':reg.key,
                        tag:reg.key,
                        'v11626_wing_grindfield':kind,
                        'exploration_ep':0,
                        'v1000_landmark':False,
                        'exits':exits,
                    }
    return result

def build_spawns():
    return [(sector_id(kind,index,x,y),f'v115_dungeon_{index:02d}_lurker')
            for kind,*_ in TYPES
            for index,_reg in enumerate(REGIONS,1)
            for y in range(HEIGHT) for x in range(WIDTH)
            if (x+y)%2==0]

def install_rooms(existing):
    planned=build_rooms()
    if set(existing).intersection(planned):
        raise ValueError('v116.00.26: powtórzony identyfikator nowego sektora')
    anchors=[]
    for kind,_oldid,zone_prefix,tag in TYPES:
        for index,reg in enumerate(REGIONS,1):
            anchor=boundary_anchor(kind,index)
            room=existing.get(anchor)
            if not isinstance(room,dict) or (room.get('zone')!=f'{zone_prefix} — {reg.name}'
               or room.get(tag)!=reg.key or room.get('v115_region_key')!=reg.key):
                raise ValueError(f'v116.00.26: brak właściwej granicy: {anchor}')
            if 'east' in room.get('exits',{}):
                raise ValueError(f'v116.00.26: zajęte przejście: {anchor}/east')
            entry=sector_id(kind,index,0,0)
            if planned[entry]['exits'].get('west')!=anchor:
                raise ValueError(f'v116.00.26: brak drogi powrotnej: {entry}')
            anchors.append((anchor,entry))
    allowed={(entry,'west',anchor) for anchor,entry in anchors}
    for rid,room in planned.items():
        for way,target in room['exits'].items():
            if target in planned:
                if planned[target]['exits'].get(OPPOSITES[way])!=rid:
                    raise ValueError(f'v116.00.26: jednostronny nowy sektor: {rid}')
            elif (rid,way,target) not in allowed:
                raise ValueError(f'v116.00.26: niedozwolone przejście: {rid}->{target}')
    # Commit only after all sixty anchors and all new edges have been validated.
    existing.update(planned)
    for anchor,entry in anchors:existing[anchor]['exits']['east']=entry
    return len(planned)
