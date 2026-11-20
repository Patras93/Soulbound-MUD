# -*- coding: utf-8 -*-
"""Sprawdzalne nowe obrzeża trzech dawnych krain: bez zmiany starej mapy.

Każde wejście jest na POCZĄTKU starego traktu i na BRZEGU nowej siatki.
Nie dopisujemy bossów, bramek, questów, pułapek ani auto-aggro.
"""
from __future__ import annotations

WIDTH, HEIGHT = 20, 12
# klucz, dawna strefa, stary punkt początku, wyjście do nowego świata,
# powrót do starego świata, trudność, wyłącznie istniejące zwykłe moby.
AREAS = (
    ('gobliny', 'Jaskinie Goblinów', 'goblin_cave_mouth', 'north', 'south', 23,
     ('goblin_scout', 'goblin_spearman', 'goblin_cave_guard', 'goblin_archer')),
    ('bandyci', 'Obozowiska Bandytów', 'bandit_camp', 'up', 'down', 22,
     ('bandit_scout', 'bandit_crossbowman', 'bandit_cutthroat', 'bandit_marauder')),
    ('straznica', 'Ruiny Strażnicy', 'ruin_gatehouse', 'north', 'south', 25,
     ('ruin_watchman', 'ruin_spearman', 'ruin_shieldbearer', 'ruin_goblin_looter')),
)
NEW_ZONES = {
    'gobliny': 'Rozległe Jaskinie Goblinów',
    'bandyci': 'Rozległe Pogranicze Bandytów',
    'straznica': 'Rozległe Ruiny Strażnicy',
}
NAMES = {
    'gobliny': ('Skalne rozstaje', 'Grzybowe korytarze', 'Szczelina w skale',
                'Podziemny most', 'Wietrzny tunel', 'Kamienna galeria'),
    'bandyci': ('Wysunięty szaniec', 'Płaskowyż łupieżców', 'Stary szlak',
                'Obozowy przesmyk', 'Pusta strażnica', 'Zarośnięty trakt'),
    'straznica': ('Kamienny krużganek', 'Zawalone mury', 'Dziedziniec wieży',
                  'Głucha galeria', 'Ruiny koszar', 'Strażniczy trakt'),
}
OPPOSITE = {'north':'south','south':'north','east':'west','west':'east','up':'down','down':'up'}

def room_id(key: str, x: int, y: int) -> str:
    return f'v116_historic_{key}_{x:02d}_{y:02d}'

def build_rooms():
    result={}
    for key, _zone, anchor, _forward, back, level, _mobs in AREAS:
        for y in range(HEIGHT):
            for x in range(WIDTH):
                rid=room_id(key,x,y)
                exits={}
                if x: exits['west']=room_id(key,x-1,y)
                if x+1<WIDTH: exits['east']=room_id(key,x+1,y)
                if y: exits['south']=room_id(key,x,y-1)
                if y+1<HEIGHT: exits['north']=room_id(key,x,y+1)
                if x==0 and y==0: exits[back]=anchor
                result[rid]={
                    'zone':NEW_ZONES[key],
                    'name':f'{NAMES[key][(x+3*y)%len(NAMES[key])]} — {NEW_ZONES[key]}',
                    'desc':f'{NEW_ZONES[key]}. Odcinek {x+1}/{WIDTH}, pas {y+1}/{HEIGHT}. Drogi łączą sąsiednie sektory.',
                    'generator_level':level,
                    'exploration_ep':(5+(x+y)//4) if (x+y)%2==0 else 0,
                    'v116_historic_expansion':key,
                    'exits':exits,
                }
    return result

def install_rooms(existing):
    planned=build_rooms()
    if set(existing).intersection(planned):
        raise ValueError('v116: kolizja identyfikatorów historycznych obrzeży')
    # Pełna walidacja przed jakąkolwiek modyfikacją starego świata.
    for key, zone, anchor, direction, back, _level, _mobs in AREAS:
        room=existing.get(anchor)
        if not isinstance(room,dict) or room.get('zone')!=zone:
            raise ValueError(f'v116: niezgodny historyczny początek: {anchor}')
        if direction in room.get('exits',{}):
            raise ValueError(f'v116: stary kierunek zajęty: {anchor}/{direction}')
        if planned[room_id(key,0,0)]['exits'].get(back)!=anchor:
            raise ValueError(f'v116: brak powrotu z nowej krainy: {key}')
    for rid,room in planned.items():
        for dest in room['exits'].values():
            if dest not in planned and dest not in existing:
                raise ValueError(f'v116: przejście do brakującego pokoju: {rid} -> {dest}')
    existing.update(planned)
    for key, _zone, anchor, direction, _back, _level, _mobs in AREAS:
        existing[anchor]['exits'][direction]=room_id(key,0,0)
    return len(planned)

def build_spawns():
    # Zwykłe wrogie postaci z katalogu, żadnych nowych szablonów bossów.
    return [(room_id(key,x,y),mobs[(x+2*y)%len(mobs)])
            for key,_zone,_anchor,_direction,_back,_level,mobs in AREAS
            for y in range(HEIGHT) for x in range(WIDTH) if (x+y)%2==0]
