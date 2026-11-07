# -*- coding: utf-8 -*-
"""v107 – 25 nowych krain, 500 pomieszczeń, 300 mobów, 1000 zadań.

Pięć rozdziałów świata, każdy z dwukierunkową siecią 100 pokojów. Wszyscy
bossowie solo, brak rajdów, brak auto-agro. Rejestry mutowane TYLKO w staging.
Przed instalacją sprawdzane są wszystkie docelowe identyfikatory i nazwy.
"""
from __future__ import annotations
from world.v10700_chaos_chapter_one import install as install_five
from world.v10700_chaos_chapter_one import planned_ids, prefix
from world.v10700_region_index import CHAPTER_ONE
from world.v10700_region_index_chapters_2_6 import CHAPTERS, ALL_NEXT


def all_planned_ids():
    return planned_ids(ALL_NEXT)


def _parent(chapter_number):
    if chapter_number==2:
        return prefix(CHAPTER_ONE[-1][0])+'_12', CHAPTER_ONE[-1][1]
    previous=CHAPTERS[chapter_number-3][-1]
    return prefix(previous[0])+'_12', previous[1]


def install(rooms,mobs,spawns,npcs,quests,items,recipes,
            zone_ids,categories,guides,power):
    """Dodaje 25 regionów za rozdziałem I bez ruszania starego świata.

    Używa tej samej fizycznej rejestracji questów, bossów, nagród i NPC,
    którą przetestowano w rozdziale I; bez osobnego niegrywalnego katalogu.
    """
    planned=all_planned_ids()
    catalogs={'rooms':rooms,'mobs':mobs,'npcs':npcs,'quests':quests,
              'items':items,'recipes':recipes}
    first=prefix(CHAPTERS[0][0][0])+'_01'
    last_parent,last_zone=_parent(2)
    if first in rooms:
        for kind,ids in planned.items():
            if not ids<=catalogs[kind].keys():
                raise RuntimeError('v107 rozdziały II–VI: niekompletna poprzednia instalacja '+kind)
        if rooms.get(last_parent,{}).get('exits',{}).get('east')!=first:
            raise RuntimeError('v107 rozdziały II–VI: uszkodzone wejście')
        # Real check of each whole chapter; idempotency with next linked chapter.
        known=planned['mobs']
        observed=[(rid,mid) for rid,mid in spawns if mid in known]
        if len(observed)!=550 or len(set(observed))!=550:
            raise RuntimeError('v107 rozdziały II–VI: brak jednego z 550 odrodzeń')
        for number, chapter in enumerate(CHAPTERS,2):
            parent,zone=_parent(number)
            again=install_five(rooms,mobs,spawns,npcs,quests,items,recipes,
                zone_ids,categories,guides,power,chapter=chapter,parent=parent,
                parent_zone=zone,start_level=60001+(number-1)*5000,
                chapter_number=number)
            if not again['already_installed']:
                raise RuntimeError('v107: niespodziewana modyfikacja przy ponownej instalacji')
        return {'already_installed':True,'chapters':0,'regions':0,
                'rooms':0,'mobs':0,'spawns':0,'npcs':0,'quests':0,
                'items':0,'recipes':0,'areas':()}
    # Global preflight: collisions detected before ANY chapter is created.
    if (last_parent not in rooms or rooms[last_parent].get('zone')!=last_zone or
            rooms[last_parent].get('exits',{}).get('east') is not None):
        raise RuntimeError('v107: rozdział I nie jest gotowy do połączenia')
    for kind,ids in planned.items():
        overlap=ids & catalogs[kind].keys()
        if overlap:
            raise RuntimeError('v107: kolizja '+kind+' '+sorted(overlap)[0])
    if 'soul_shard' not in items:
        raise RuntimeError('v107: brak nagrody soul_shard')
    for slug,name,*_ in ALL_NEXT:
        if name in zone_ids or prefix(slug) in categories or name.casefold() in guides:
            raise RuntimeError('v107: istnieje już kraina '+name)
    if len({row[0] for row in (*CHAPTER_ONE,*ALL_NEXT)})!=30:
        raise RuntimeError('v107: nieunikalne ID 30 krain')
    if len({row[1] for row in (*CHAPTER_ONE,*ALL_NEXT)})!=30:
        raise RuntimeError('v107: nieunikalne nazwy 30 krain')
    results=[]
    for number,chapter in enumerate(CHAPTERS,2):
        parent,zone=_parent(number)
        result=install_five(rooms,mobs,spawns,npcs,quests,items,recipes,
            zone_ids,categories,guides,power,chapter=chapter,parent=parent,
            parent_zone=zone,start_level=60001+(number-1)*5000,
            chapter_number=number)
        if (result['already_installed'] or result['regions']!=5 or
                result['quests']!=200):
            raise RuntimeError('v107: rozdział nie został prawidłowo zainstalowany')
        results.append(result)
    keys=('regions','rooms','mobs','spawns','npcs','quests','items','recipes')
    totals={k:sum(r[k] for r in results) for k in keys}
    totals.update({'already_installed':False,'chapters':5,
        'areas':tuple(a for r in results for a in r['areas'])})
    return totals
