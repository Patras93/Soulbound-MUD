# -*- coding: utf-8 -*-
"""Rozległe obrzeża 20 historycznych krain v105 — stabilna siatka 12x12.

Dawny łańcuch 14 pokoi każdej krainy, bossowie, questy, wyjścia
między krainami i ich ID pozostają nienaruszone. Wejście do siatki
od strony początku starej trasy, powrót z jej skrajnego pokoju.
"""
from __future__ import annotations

WIDTH = HEIGHT = 12
SLUGS = (
 'przesmyk','archipelag','pioruny','ogrody','korona','mgly','zwierciadla',
 'nekropolia','plomienie','obserwatorium','las','golemy','burze','bramy',
 'piesni','kometa','fale','przysiegi','tytani','przelom',
)
LANDMARKS = (
 'Daleki szlak', 'Rozległa dolina', 'Kamienny próg',
 'Zewnętrzny trakt', 'Zapomniany przesmyk', 'Ciche pogranicze',
 'Rozstaje wędrowców', 'Północna rubież',
)
OPPOSITE={'north':'south','south':'north','east':'west','west':'east'}

def room_id(slug: str, x: int, y: int) -> str:
    return f'v11621_region_{slug}_{x:02d}_{y:02d}'

def install_legacy_large_regions(rooms, mob_spawns, mob_templates):
    """Sprawdza prewarunki przed mutacją; tylko nowa siatka + wejście na brzegu.

    Jeden spawn na cztery pokoje, wyłącznie historyczne zwykłe moby,
    bez bossów, pułapek, blokad poziomu ani automatycznego aggro.
    """
    plans=[]; created={}; spawns=[]
    if not isinstance(mob_spawns,list):
        raise ValueError('Nieobsługiwany katalog spawnów')
    for slug in SLUGS:
        beginning=f'v10500_{slug}_01'
        finish=f'v10500_{slug}_14'
        first=rooms.get(beginning)
        last=rooms.get(finish)
        if not isinstance(first,dict) or not isinstance(last,dict):
            raise ValueError(f'Brak historycznej krainy {slug}')
        zone=first.get('zone')
        if (not zone or last.get('zone')!=zone
                or first.get('exits',{}).get('north')!=f'v10500_{slug}_02'
                or 'south' in first.get('exits',{})
                or last.get('exits',{}).get('south')!=f'v10500_{slug}_13'):
            raise ValueError(f'Nieprawidłowe historyczne granice {slug}')
        names=[f'v10500_{slug}_mob_{i}' for i in range(1,9)]
        if any(name not in mob_templates for name in names):
            raise ValueError(f'Brak historycznego zwykłego moba: {slug}')
        plans.append((beginning,slug))
        for y in range(HEIGHT):
            for x in range(WIDTH):
                rid=room_id(slug,x,y)
                if rid in rooms or rid in created:
                    raise ValueError(f'Kolizja nowego pokoju: {rid}')
                exits={}
                if x:exits['west']=room_id(slug,x-1,y)
                if x+1<WIDTH:exits['east']=room_id(slug,x+1,y)
                if y:exits['south']=room_id(slug,x,y-1)
                if y+1<HEIGHT:exits['north']=room_id(slug,x,y+1)
                if x==0 and y==HEIGHT-1:exits['north']=beginning
                created[rid]={
                    'zone':zone,
                    'name':f'{LANDMARKS[(x+2*y)%len(LANDMARKS)]} — {zone}',
                    'desc':f'{zone}. Obrzeże {x+1} z {WIDTH}, pas {y+1} z {HEIGHT}.',
                    'exits':exits,
                    'exploration_ep':0,
                    'v116_large_legacy':slug,
                }
                if (x+2*y)%4==0:
                    spawns.append((rid,names[(x+3*y)%len(names)]))
    if len(plans)!=20 or len(created)!=2880 or len(spawns)!=720:
        raise ValueError('Niepełne obrzeża starych krain')
    # Kontrola pełnej dwukierunkowości nowych dróg.
    for rid,room in created.items():
        for direction,target in room['exits'].items():
            if target in created:
                if created[target]['exits'].get(OPPOSITE[direction])!=rid:
                    raise ValueError(f'Brak drogi powrotnej {rid} -> {target}')
            elif target not in rooms or direction!='north':
                raise ValueError(f'Niepoprawny cel {rid} -> {target}')
    rooms.update(created)
    for beginning,slug in plans:
        rooms[beginning]['exits']['south']=room_id(slug,0,HEIGHT-1)
    mob_spawns.extend(spawns)
    return len(created),len(spawns)
