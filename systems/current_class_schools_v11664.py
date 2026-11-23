# -*- coding: utf-8 -*-
"""v116.00.64: schools for every playable class; new characters only.

Old guild teachers, world rooms, saves, quests and existing characters stay intact.
The only link to Miasto Dusz is a confirmed portal at the OUTER school boundary.
"""
from __future__ import annotations
import re
import unicodedata

WIDTH = 5
HEIGHT = 5


def class_slug(name):
    folded = unicodedata.normalize('NFKD', str(name).replace('ł','l').replace('Ł','L'))
    ascii_text = ''.join(ch for ch in folded if not unicodedata.combining(ch))
    slug = re.sub(r'[^a-z0-9]+','_',ascii_text.casefold()).strip('_')
    if not slug:
        raise ValueError('Szkoła bez identyfikatora klasy')
    return slug


def school_room(name, x=0, y=0):
    return f'v11664_class_school_{class_slug(name)}_{x:02d}_{y:02d}'


def school_teacher(name):
    return f'v11664_school_teacher_{class_slug(name)}'


NAMES = ('Sala Przyjęć', 'Sala Nauk', 'Pracownia Ciosów', 'Sala Obrony',
         'Sala Celności', 'Sala Taktyki', 'Sala Manewrów', 'Sala Umiejętności',
         'Dziedziniec Treningowy', 'Sala Wsparcia', 'Sala Prób', 'Sala Ćwiczeń')


def build_class_schools(class_names):
    """Build 25 real rooms, 1 teacher and multiple mob-filled halls per class."""
    class_names = tuple(str(name) for name in class_names)
    if len(class_names) != len(set(class_names)):
        raise ValueError('Powtórzona klasa w szkołach')
    slugs = [class_slug(name) for name in class_names]
    if len(slugs) != len(set(slugs)):
        raise ValueError('Powtórzony identyfikator szkoły')
    rooms, npcs, spawns = {}, {}, []
    for name in class_names:
        zone = f'Szkoła klasy {name}'
        for y in range(HEIGHT):
            for x in range(WIDTH):
                rid = school_room(name,x,y)
                exits = {}
                if x: exits['west'] = school_room(name,x-1,y)
                if x+1 < WIDTH: exits['east'] = school_room(name,x+1,y)
                if y: exits['south'] = school_room(name,x,y-1)
                if y+1 < HEIGHT: exits['north'] = school_room(name,x,y+1)
                if (x,y) == (WIDTH-1,HEIGHT-1):
                    exits['up'] = 'square'   # deliberate one-way portal at a boundary
                if (x,y) == (0,0):
                    title='Sala Nauczyciela'
                    desc=(f'Szkoła {name}. Tutaj nauczyciel prowadzi pierwsze lekcje. '
                          'Wpisz talk <imię nauczyciela> albo learn. Ćwicz w sąsiednich salach. '
                          'Wyjście do Miasta Dusz jest na dalekim północno-wschodnim krańcu szkoły.')
                elif (x,y) == (WIDTH-1,HEIGHT-1):
                    title='Portal do Miasta Dusz'
                    desc=('Koniec szkolnego szlaku. Portal prowadzi do Miasta Dusz. '
                          'Zalecany poziom postaci: 10. Wyjście wymaga potwierdzenia; '
                          'można wyjść wcześniej, nie ma sztucznej blokady poziomu.')
                else:
                    title=NAMES[(x+2*y)%len(NAMES)]
                    desc=(f'{zone}. {title}, ćwiczenia etap {min(10,1+x+y)}. '
                          'Kilka odrębnych sal służy do walki, obrony i praktyki umiejętności.')
                stage=min(10,1+x+y)
                rooms[rid]={
                    'zone':zone,'name':f'{title} — {name} ({x+1}/{WIDTH}, {y+1}/{HEIGHT})',
                    'desc':desc,'exits':exits,'generator_level':stage,
                    'region_difficulty_v2006':'poczatkujace',
                    'region_stage_v2006':stage,
                    'v11664_school_class':name,
                    'v11664_school_city_portal':(x,y)==(WIDTH-1,HEIGHT-1),
                }
                # Beyond a single dummy: many separately respawning training mobs.
                # No automatic aggression; regular game combat and rewards apply.
                if (x,y) not in ((0,0),(WIDTH-1,HEIGHT-1)) and (x+y)%2==0:
                    enemy=('training_dummy','temple_rat','goblin')[(x+y//2)%3]
                    spawns.append((rid,enemy))
        npcs[school_teacher(name)]={
            'name':f'Nauczyciel {name}',
            'room':school_room(name),
            'teacher_class':name,
            'dialogue':(f'Witaj w szkole klasy {name}. '
                        'Uczę twoich klasowych umiejętności. Wpisz learn, '
                        'aby sprawdzić aktualne lekcje, oraz talk, by zobaczyć wymagania. '
                        'Trenuj w salach dalej od wejścia. '
                        'Portal na krańcu szkoły prowadzi do Miasta Dusz, '
                        'zalecany poziom 10.'),
            'quest':None,
        }
    return rooms,npcs,spawns


def install_class_schools(rooms,npcs,spawns,mob_templates,class_rows):
    classes=tuple(str(row[0]) for row in class_rows)
    if len(classes)!=38 or len(set(classes))!=38:
        raise RuntimeError('Szkoły v116.64 wymagają dokładnie 38 aktywnych klas')
    built, teachers, enemies=build_class_schools(classes)
    if set(rooms)&set(built) or set(npcs)&set(teachers):
        raise RuntimeError('Kolizja identyfikatorów szkół/nauczycieli')
    if any(mob not in mob_templates for _,mob in enemies):
        raise RuntimeError('Brak prawdziwego szablonu początkującego przeciwnika')
    if any(dst not in built and dst not in rooms
           for room in built.values() for dst in room['exits'].values()):
        raise RuntimeError('Szkoły: niedostępna lokacja portalu')
    if sum(1 for room in built.values() if room['v11664_school_city_portal'])!=len(classes):
        raise RuntimeError('Każda szkoła musi mieć dokładnie jeden portal')
    rooms.update(built)
    npcs.update(teachers)
    spawns.extend(enemies)
    return {'schools':len(classes),'rooms':len(built),'teachers':len(teachers),'spawns':len(enemies)}
