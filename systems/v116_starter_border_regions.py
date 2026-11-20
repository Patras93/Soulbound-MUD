# -*- coding: utf-8 -*-
"""v116: three long, border-only extensions of the original starter world.

The authored old locations and their exits never get replaced. A single
new exit at a verified end-of-route leads into each 20x12 traversable area.
All IDs are stable; no additional bosses, quests, level gates or traps.
"""
from __future__ import annotations

WIDTH, HEIGHT = 20, 12
# (key, old zone, old endpoint, direction from old endpoint,
#  direction back to old endpoint, entry coordinates, level, native mob IDs)
AREAS = (
    ('laki', 'Łąki', 'flower_meadow', 'south', 'north', (0, HEIGHT - 1), 5,
     ('meadow_giant_wasp', 'meadow_field_wolf', 'meadow_wild_boar')),
    ('dzicz', 'Dzicz', 'shrine', 'north', 'south', (0, 0), 12,
     ('shadow_wolf', 'goblin_scout', 'bandit_scout')),
    ('wybrzeze', 'Wybrzeże', 'sea_pier', 'north', 'south', (0, 0), 16,
     ('coast_rock_crab', 'coast_sea_raider')),
)
EXTENSION_ZONES = {
    'laki': 'Rozległe Łąki',
    'dzicz': 'Dzicz Pogranicza',
    'wybrzeze': 'Wybrzeże Wysp',
}

LANDSCAPES = {
    'laki': ('Łąkowy trakt', 'Trawiasta dolina', 'Rozległa polana',
             'Srebrzysta równina', 'Ziołowy zakątek', 'Brzeg strumienia'),
    'dzicz': ('Prastary bór', 'Gęste zarośla', 'Wzgórza pogranicza',
              'Leśny przesmyk', 'Zwierzęcy szlak', 'Kamienne rozstaje'),
    'wybrzeze': ('Skalisty brzeg', 'Łańcuch wysepek', 'Morski przesmyk',
                 'Nadmorski szlak', 'Zatoka', 'Kamienista plaża'),
}
OPPOSITE = {'north':'south','south':'north','east':'west','west':'east'}

def room_id(key: str, x: int, y: int) -> str:
    return f'v116_border_{key}_{x:02d}_{y:02d}'

def build_rooms():
    rooms = {}
    for key, zone, _anchor, _forward, back, start, level, _enemies in AREAS:
        names = LANDSCAPES[key]
        for y in range(HEIGHT):
            for x in range(WIDTH):
                rid = room_id(key,x,y)
                exits = {}
                if x: exits['west'] = room_id(key,x-1,y)
                if x+1 < WIDTH: exits['east'] = room_id(key,x+1,y)
                if y: exits['south'] = room_id(key,x,y-1)
                if y+1 < HEIGHT: exits['north'] = room_id(key,x,y+1)
                if (x,y) == start: exits[back] = _anchor
                # Do not rename the 12x12 sectors already released in v116.00.8.
                # Newly appended sectors use the extended coordinate range.
                shown_width = 12 if x < 12 else WIDTH
                rooms[rid] = {
                    'zone':EXTENSION_ZONES[key],
                    'name':f'{names[(x+3*y)%len(names)]} — {EXTENSION_ZONES[key]} ({x+1}/{shown_width}, {y+1}/{HEIGHT})',
                    'desc':f'{EXTENSION_ZONES[key]}. Sektor {x+1}/{shown_width}, pas {y+1}/{HEIGHT}. Ścieżki prowadzą w kilku kierunkach.',
                    'exits':exits,
                    'generator_level':level,
                    'exploration_ep':(5+(x+y)//4) if (x+y)%2==0 else 0,
                    'v116_border_expansion':key,
                }
    return rooms

def install_rooms(existing):
    new = build_rooms()
    # Validate ALL anchors and collisions before mutating any room/exits.
    for key, zone, anchor, forward, back, start, _level, _enemies in AREAS:
        original = existing.get(anchor)
        if not isinstance(original,dict) or original.get('zone') != zone:
            raise ValueError(f'Brak końcowej lokacji starego terenu: {anchor}')
        if forward in original.get('exits',{}):
            raise ValueError(f'Zajęte wyjście na granicy: {anchor} {forward}')
        if (start[0] not in (0,WIDTH-1) and start[1] not in (0,HEIGHT-1)):
            raise ValueError(f'Wejście nie leży na krańcu: {key}')
        if new[room_id(key,*start)]['exits'].get(back) != anchor:
            raise ValueError(f'Brak drogi powrotnej: {key}')
    if set(existing).intersection(new):
        raise ValueError('Kolizja identyfikatorów nowych lokacji v116')
    for rid, room in new.items():
        for dst in room['exits'].values():
            if dst not in new and dst not in existing:
                raise ValueError(f'Nieistniejące przejście: {rid}->{dst}')
    existing.update(new)
    for key, _zone, anchor, forward, _back, start, _level, _enemies in AREAS:
        existing[anchor]['exits'][forward] = room_id(key,*start)
    return len(new)

def build_spawns():
    return [(room_id(key,x,y), enemies[(x+2*y)%len(enemies)])
            for key, _zone, _anchor, _forward, _back, _start, _level, enemies in AREAS
            for y in range(HEIGHT) for x in range(WIDTH) if (x+y)%2 == 0]
