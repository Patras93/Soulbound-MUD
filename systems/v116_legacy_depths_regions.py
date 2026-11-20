# -*- coding: utf-8 -*-
"""v116: optional, wide side passages for three untouched early dungeons.

Entry from a START or END room only. No legacy ID, quest, boss,
existing exit or procedural-floor mechanic is moved. No auto-aggro or traps.
"""
from __future__ import annotations

WIDTH, HEIGHT = 20, 12
# key, source zone, START/END anchor, direction to new terrain,
# reverse direction, entry (always a perimeter cell), new zone, level,
# already registered ordinary creatures
AREAS = (
    ('swiatynia', 'Piwnica Świątyni', 'temple_basement_deep_nest',
     'north', 'south', (0, 0), 'Rozległe Podziemia Świątyni', 1,
     ('temple_rat',)),
    ('kopalnia', 'Podziemia', 'cave_entrance',
     'west', 'east', (WIDTH-1, 0), 'Rozległa Kopalnia Głębinowa', 23,
     ('goblin_cave_guard', 'crystal_guardian')),
    ('krypta', 'Podziemia', 'crypt_entrance',
     'west', 'east', (WIDTH-1, 0), 'Rozległe Krypty Pogranicza', 30,
     ('skeleton', 'crypt_wraith')),
)
LANDMARKS = {
    'swiatynia': ('Szczurzy tunel', 'Zawilgocona galeria', 'Piwniczny trakt',
                  'Stara śluza', 'Kamienny korytarz', 'Opuszczony magazyn'),
    'kopalnia': ('Szyb górniczy', 'Kryształowa grota', 'Kamienny most',
                 'Wąski przekop', 'Podziemny trakt', 'Zapomniana sztolnia'),
    'krypta': ('Stary krużganek', 'Kościana aleja', 'Zimna komnata',
               'Zamknięte podziemie', 'Kamienny korytarz', 'Pusta krypta'),
}
OPPOSITE = {'north':'south', 'south':'north', 'west':'east', 'east':'west'}

def room_id(key: str, x: int, y: int) -> str:
    return f'v116_depths_{key}_{x:02d}_{y:02d}'

def build_rooms():
    planned = {}
    for key, _source, anchor, _direction, reverse, entry, zone, level, _mobs in AREAS:
        for y in range(HEIGHT):
            for x in range(WIDTH):
                rid=room_id(key,x,y)
                exits={}
                if x: exits['west']=room_id(key,x-1,y)
                if x+1<WIDTH: exits['east']=room_id(key,x+1,y)
                if y: exits['south']=room_id(key,x,y-1)
                if y+1<HEIGHT: exits['north']=room_id(key,x,y+1)
                if (x,y)==entry:
                    exits[reverse]=anchor
                planned[rid]={
                    'zone':zone,
                    'name':f'{LANDMARKS[key][(x+3*y)%len(LANDMARKS[key])]} — {zone}',
                    'desc':f'{zone}. Odcinek {x+1}/{WIDTH}, pas {y+1}/{HEIGHT}. Drogi prowadzą do sąsiednich sektorów.',
                    'generator_level':level,
                    'exploration_ep':(5+(x+y)//4) if (x+y)%2==0 else 0,
                    'v116_legacy_depths':key,
                    'exits':exits,
                }
    return planned

def install_rooms(existing):
    planned=build_rooms()
    if set(planned).intersection(existing):
        raise ValueError('v116: kolizja identyfikatorów podziemnych traktów')
    for key, source, anchor, direction, reverse, entry, _zone, _level, _mobs in AREAS:
        old=existing.get(anchor)
        if not isinstance(old,dict) or old.get('zone')!=source:
            raise ValueError(f'v116: brak właściwego początku/końca trasy {anchor}')
        if direction in old.get('exits',{}):
            raise ValueError(f'v116: kierunek już zajęty {anchor}/{direction}')
        if not (entry[0] in (0,WIDTH-1) or entry[1] in (0,HEIGHT-1)):
            raise ValueError(f'v116: wejście poza krańcem {key}')
        if planned[room_id(key,*entry)]['exits'].get(reverse)!=anchor:
            raise ValueError(f'v116: brak drogi powrotnej {key}')
    for rid,room in planned.items():
        for dest in room['exits'].values():
            if dest not in planned and dest not in existing:
                raise ValueError(f'v116: brak pomieszczenia {rid}->{dest}')
    existing.update(planned)
    for key, _source, anchor, direction, _reverse, entry, _zone, _level, _mobs in AREAS:
        existing[anchor]['exits'][direction]=room_id(key,*entry)
    return len(planned)

def build_spawns():
    return [(room_id(key,x,y), mobs[(x+2*y)%len(mobs)])
            for key,_source,_anchor,_direction,_reverse,_entry,_zone,_level,mobs in AREAS
            for y in range(HEIGHT) for x in range(WIDTH) if (x+y)%2==0]
