# -*- coding: utf-8 -*-
"""v115: rozlegle, stale krainy; bez wymagania soundpacka.

Kazda kraina ma siatke 12 x 12 (144 pokoje) z wieloma petlami i odnogami.
Stale nazwy i ID umozliwiaja zapisy i latwa nawigacje NVDA.
"""
from .high_level_world import REGIONS
from .profession_sites import site_for_sector

HUB = 'v115_horyzonty_wezel'
WIDTH, HEIGHT = 12, 12
FEATURES = ('Skraj', 'Trakt', 'Wąwóz', 'Polana', 'Kamienny krąg', 'Ruiny',
            'Przesmyk', 'Dziedziniec', 'Rozstaje', 'Obozowisko', 'Taras', 'Wzgórze',
            'Przepaść', 'Punkt obserwacyjny', 'Pustkowie', 'Sanktuarium')

def room_id(region_key, x, y):
    return f'{region_key}_p_{x:02d}_{y:02d}'

def build_rooms():
    rooms = {HUB: {'zone':'Szlak Horyzontów',
                   'name':'Węzeł Nieskończonych Horyzontów',
                   'desc':'Początek trzydziestu rozległych krain.',
                   'exits':{'down':'crossroads'}}}
    for index, region in enumerate(REGIONS,1):
        node = HUB if index == 1 else f'v115_wezel_{index:02d}'
        if index > 1:
            previous = HUB if index == 2 else f'v115_wezel_{index-1:02d}'
            rooms[node] = {'zone':'Szlak Horyzontów','name':f'Węzeł Horyzontów {index}',
                           'desc':f'Droga do krainy {region.name}.',
                           'exits':{'south':previous}}
            rooms[previous]['exits']['north'] = node
        rooms[node]['exits']['east'] = room_id(region.key,0,0)
        for y in range(HEIGHT):
            for x in range(WIDTH):
                room = room_id(region.key,x,y)
                exits = {}
                if x: exits['west'] = room_id(region.key,x-1,y)
                if x < WIDTH-1: exits['east'] = room_id(region.key,x+1,y)
                if y: exits['south'] = room_id(region.key,x,y-1)
                if y < HEIGHT-1: exits['north'] = room_id(region.key,x,y+1)
                if x==0 and y==0: exits['west'] = node
                name = f'{FEATURES[(x*7+y*11+index)%len(FEATURES)]} — {region.name}'
                desc = (f'Rozległy obszar {region.name}; teren {region.biome}. '
                        f'Sektor {x+1}/{WIDTH}, pas {y+1}/{HEIGHT}. '
                        'Połączone ścieżki pozwalają wybrać różne trasy wyprawy.')
                site = site_for_sector(region.key, x, y)
                if site:
                    # Short, NVDA-friendly hint; only one action is available
                    # in this sector and it still requires the existing tool.
                    command = {'fishing':'low', 'mining':'kop',
                               'woodcutting':'tnij', 'herbalism':'zbieraj'}[site['kind']]
                    desc += f" {site['name']}. Komenda: {command}."
                rooms[room] = {'zone':region.name,'name':name,'desc':desc,
                               'generator_level':region.suggested_level,
                               'v115_region_key':region.key,
                               **({'v115_profession_site': site} if site else {}),
                               'v1000_landmark':(x+y)%2==0,
                               'exploration_ep':(10 + min(14, (x+y)//2)) if (x+y)%2==0 else 0,
                               'exits':exits}
    return rooms

def build_mobs():
    mobs = {}
    for region in REGIONS:
        base = max(1,region.suggested_level)
        for kind,scale in (('scout',6),('patrol',10),('guardian',40)):
            boss = kind == 'guardian'
            name = {'scout':'Zwiadowca','patrol':'Wojownik','guardian':'Strażnik'}[kind]
            mobs[f'{region.key}_{kind}'] = {
                'name':f'{name} — {region.name}', 'max_hp':base*scale,
                'damage':max(1,base//(3 if boss else 12 if kind=='patrol' else 20)),
                'damage_type':'magic' if boss else 'physical',
                'silver':min(10000,base//4),'gold':min(1000,base//150),'mithril':0,
                'stat_reward':base*(4 if boss else 2),
                'class_xp_reward':base*(14 if boss else 8),
                'soul_reward':base*(7 if boss else 4),
                'drops':{},'quest_target':None,'generator_level':base,
                'v115_region_key':region.key,
                **({'world_boss':True,'boss':True} if boss else {})}
    return mobs

def build_spawns():
    spawns = []
    for region in REGIONS:
        for y in range(HEIGHT):
            for x in range(WIDTH):
                # Nie blokujemy pokojow. 50% pokojow jest stale zasiedlone.
                if (x+y)%2 == 0:
                    kind='scout' if (x+2*y)%3==0 else 'patrol'
                    spawns.append((room_id(region.key,x,y),f'{region.key}_{kind}'))
        spawns.append((room_id(region.key,7,5),f'{region.key}_guardian'))
    return spawns

def validate_world(existing_rooms,existing_mobs,existing_spawns):
    rooms=build_rooms(); mobs=build_mobs(); spawns=build_spawns()
    if set(rooms)&set(existing_rooms): raise ValueError('v115: kolizja lokacji')
    if set(mobs)&set(existing_mobs): raise ValueError('v115: kolizja potwora')
    for rid, room in rooms.items():
        for dest in room['exits'].values():
            if dest not in rooms and dest not in existing_rooms:
                raise ValueError(f'v115: zle przejscie {rid}->{dest}')
    for rid,tid in spawns:
        if rid not in rooms or tid not in mobs: raise ValueError('v115: zly spawn')
    expected_rooms=len(REGIONS)*(WIDTH*HEIGHT+1)
    expected_spawns=len(REGIONS)*(WIDTH*HEIGHT//2+1)
    if (len(rooms),len(mobs),len(spawns))!=(expected_rooms,3*len(REGIONS),expected_spawns):
        raise ValueError('v115: niekompletne katalogi')
    return True
