# -*- coding: utf-8 -*-
"""Duże zwykłe expowiska v116.00.22, 27 stref + siatki po 144 pokoi.

Żaden boss, quest, istniejący spawn ani wyjście nie jest zastępowany.
Preflight sprawdza całość przed zapisaniem; strefy bez automatycznego aggro.
"""
from __future__ import annotations

WIDTH = HEIGHT = 12
V103_SLUGS = ('swit','kuznie','gwiazdy','echa','runy','smoki','materia','dusza','ogrody','czas','tron')
V104_SLUGS = ('sztorm','zelazo','cienie','runy','ogrody','pustynia','wrota','smok','labirynt','tron')
V3000_SLUGS = ('scarlet','crystal','abyss','eternal')
LANDMARKS = ('Rozległy szlak','Pograniczne pola','Dalsze ostępy','Zewnętrzny trakt',
             'Węzeł dróg','Cicha dolina','Północny skraj','Dalekie rubieże')
OPPOSITE = {'north':'south','south':'north','east':'west','west':'east'}

# Zawiera tylko zweryfikowane historyczne zwykłe szablony mobów.
def region_specs():
    for slug in V103_SLUGS:
        yield ('v103_'+slug, f'v10300_{slug}_01', 'south',
               tuple(f'v10300_{slug}_mob_{i}' for i in range(1,9)))
    for slug in V104_SLUGS:
        yield ('v104_'+slug, f'v10400_{slug}_01', 'south',
               tuple(f'v10400_{slug}_mob_{i}' for i in range(1,9)))
    for slug in V3000_SLUGS:
        yield ('v3000_'+slug, f'v3000_{slug}_1', 'south',
               tuple(f'v3000_{slug}_mob_{i}' for i in range(1,5))+
               tuple(f'v3100_{slug}_mob_{i}' for i in range(1,5)))
    yield ('outskirts', 'outer_wall_path', 'east',
           ('outskirts_wolf','outskirts_thief','outskirts_boar','outskirts_wasp'))
    yield ('temple_basement', 'temple_basement_deep_nest', 'east', ('temple_rat',))


def room_id(slug, x, y):
    return f'v11622_exp_{slug}_{x:02d}_{y:02d}'


def install_large_experience_zones(rooms, mob_spawns, mob_templates):
    """Atomic preflight and then add dense, connected, safe grinding grounds."""
    if not isinstance(mob_spawns,list):
        raise ValueError('Nieobsługiwany katalog mobów')
    created, spawns, plans = {}, [], []
    for slug, anchor, direction, monsters in region_specs():
        original = rooms.get(anchor)
        if not isinstance(original,dict) or not isinstance(original.get('exits'),dict):
            raise ValueError(f'Brak poprawnego początku expowiska: {slug}')
        if direction in original['exits']:
            raise ValueError(f'Zajęte wejście na obrzeże expowiska: {anchor}, {direction}')
        zone=original.get('zone')
        if not zone or any(mob not in mob_templates for mob in monsters):
            raise ValueError(f'Brak strefy lub istniejących potworów: {slug}')
        # Warianty A: od początku w kierunku południowym, nowa siatka kończy się od północy.
        # Warianty B: od krańca wschodniego wchodzimy na zachodnią granicę siatki.
        attach=(0,HEIGHT-1) if direction=='south' else (0,HEIGHT//2)
        if direction not in ('south','east'):
            raise ValueError('Nieznany kierunek wejścia')
        plans.append((anchor,direction,attach,slug))
        for y in range(HEIGHT):
            for x in range(WIDTH):
                rid=room_id(slug,x,y)
                if rid in rooms or rid in created:
                    raise ValueError(f'Kolizja lokacji {rid}')
                exits={}
                if x:exits['west']=room_id(slug,x-1,y)
                if x+1<WIDTH:exits['east']=room_id(slug,x+1,y)
                if y:exits['south']=room_id(slug,x,y-1)
                if y+1<HEIGHT:exits['north']=room_id(slug,x,y+1)
                if (x,y)==attach:exits[OPPOSITE[direction]]=anchor
                created[rid]={
                  'zone':zone,
                  'name':f'{LANDMARKS[(x+3*y)%len(LANDMARKS)]} — {zone}',
                  'desc':f'{zone}. Sektor {x+1} z {WIDTH}, pas {y+1} z {HEIGHT}.',
                  'exits':exits,
                  'exploration_ep':0,
                  'v116_large_exp':slug,
                }
                if (x+y)%2==0:
                    spawns.append((rid,monsters[(x+3*y)%len(monsters)]))
    if len(plans)!=27 or len(created)!=3888 or len(spawns)!=1944:
        raise ValueError('Niekompletne nowe expowiska')
    for rid,r in created.items():
        for direction,target in r['exits'].items():
            if target in created:
                if created[target]['exits'].get(OPPOSITE[direction])!=rid:
                    raise ValueError(f'Brak powrotu {rid} do {target}')
            elif target not in rooms:
                raise ValueError(f'Nieznany koniec drogi {target}')
    # Zmiany wyłącznie po pełnym sprawdzeniu planu.
    rooms.update(created)
    for anchor,direction,attach,slug in plans:
        rooms[anchor]['exits'][direction]=room_id(slug,*attach)
    mob_spawns.extend(spawns)
    return len(plans),len(created),len(spawns)
