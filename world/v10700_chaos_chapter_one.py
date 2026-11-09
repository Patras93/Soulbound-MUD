# -*- coding: utf-8 -*-
"""v107 staging – pięć pełnych krain rozdziału pierwszego i 200 questów.

Instalacja deklaratywna. Bez zapisów SQLite, bez rajdów, bez przymusowej drużyny.
Wszystkie ID historyczne zachowane; żadnych zmian na produkcji bez świadomego
włączenia całego trybu roboczego SOULBOUND_V107_STAGING=1.
"""
from __future__ import annotations
from config.balance import QUEST_REPEAT_COOLDOWN_SECONDS

from world.v10700_region_index import CHAPTER_ONE
from world.v10300_era_bez_granic import PROFESSION_SPECS
from world.legends_v3100 import OPPOSITE

PREFIX = 'v10700_chaos'
PARENT = 'v10600_serce_14'

ROOMS_LABELS = (
    'Brama Niepokoju', 'Posterunek Odkrywców', 'Ślad Burzy', 'Kamienny Trakt',
    'Dom Pamięci', 'Rozstaje Szeptów', 'Trakt Rozbitego Światła', 'Warsztat Wędrowców',
    'Strażnica Przedpola', 'Korytarz Stróżów', 'Schody Chaosu', 'Tron Pierwszego Strażnika',
    'Odgałęzienie Krystaliczne', 'Galeria Skrybów', 'Ukryta Kaplica', 'Komora Relikwii',
    'Wąwóz Odbić', 'Schody Wieczności', 'Sala Wymarłych Imion', 'Tron Głębi',
)
NPC_ROLES = ('Kronikarz', 'Zwiadowca', 'Rzemieślniczka', 'Strażniczka')
QUEST_PARTS = {'story': 10, 'hunt': 16, 'collect': 8, 'prof': 6}
# 14 normal hunts, 2 boss hunts; all targets spawn in authored rooms.
HUNT_TARGETS = (1,2,3,4,5,6,7,8,9,10,2,4,6,8,11,12)
# 10 story quests use native kinds with a real available NPC/mob/drop.
STORY_STEPS = (
    ('talk_npc', 2), ('kill', 1), ('collect', 1), ('kill', 4),
    ('talk_npc', 3), ('kill', 6), ('collect', 2), ('talk_npc', 4),
    ('kill', 11), ('kill', 12),
)
assert sum(QUEST_PARTS.values()) == 40


def prefix(slug):
    return f'{PREFIX}_{slug}'


def planned_ids(chapter=CHAPTER_ONE):
    result={key:set() for key in ('rooms','mobs','npcs','quests','items','recipes')}
    for slug,*_ in chapter:
        p=prefix(slug)
        result['rooms'].update(f'{p}_{j:02d}' for j in range(1,21))
        result['mobs'].update(f'{p}_mob_{j}' for j in range(1,11))
        result['mobs'].update(f'{p}_boss_{j}' for j in (1,2))
        result['npcs'].update(f'{p}_npc_{j}' for j in range(1,5))
        result['items'].update(f'{p}_material_{j}' for j in range(1,5))
        result['items'].add(f'{p}_alloy')
        result['recipes'].add(f'{p}_alloy')
        for kind,amount in QUEST_PARTS.items():
            result['quests'].update(f'{p}_{kind}_{j:02d}' for j in range(1,amount+1))
    return result


def _room_exits(p, index, previous):
    # Central 01–12, dwie dwukierunkowe odnogi 13–16 i 17–20.
    if index <= 12:
        exits = {'west': previous} if index == 1 else {'south':f'{p}_{index-1:02d}'}
        if index < 12:
            exits['north'] = f'{p}_{index+1:02d}'
        if index in (2,8):
            exits['east'] = f'{p}_{13 if index == 2 else 17:02d}'
        return exits
    if 13 <= index <= 16:
        exits={'west':f'{p}_{index-1:02d}' if index > 13 else f'{p}_02'}
        if index < 16:
            exits['east'] = f'{p}_{index+1:02d}'
        return exits
    exits={'west':f'{p}_{index-1:02d}' if index > 17 else f'{p}_08'}
    if index < 20:
        exits['east'] = f'{p}_{index+1:02d}'
    return exits


def install(rooms,mobs,spawns,npcs,quests,items,recipes,
            zone_ids,categories,guides,power, *, chapter=CHAPTER_ONE,
            parent=PARENT, start_level=60001, parent_zone=None,
            chapter_number=1):
    """Wykonaj pełny preflight przed dopięciem pierwszej krainy.

    Return: 5 regionów, 100 pokojów, 60 mobów, 20 NPC, 200 questów.
    """
    if parent_zone is None:
        parent_zone=CHAPTER_ONE_PARENT_ZONE()
    flag=f'v107_chapter_{chapter_number}'
    planned=planned_ids(chapter)
    catalogs={'rooms':rooms,'mobs':mobs,'npcs':npcs,'quests':quests,
              'items':items,'recipes':recipes}
    first=f'{prefix(chapter[0][0])}_01'
    if first in rooms:
        if any(not required <= catalogs[kind].keys() for kind,required in planned.items()):
            raise RuntimeError('v107 rozdział I: niekompletny katalog przy ponownej instalacji')
        if rooms.get(parent,{}).get('exits',{}).get('east') != first:
            raise RuntimeError('v107 rozdział I: uszkodzone historyczne wejście')
        for i,(slug,*_) in enumerate(chapter):
            p=prefix(slug)
            previous=parent if i==0 else f'{prefix(chapter[i-1][0])}_12'
            for j in range(1,21):
                expected=_room_exits(p,j,previous)
                if j==12 and i+1<len(chapter):
                    expected['east']=f'{prefix(chapter[i+1][0])}_01'
                actual=rooms[f'{p}_{j:02d}'].get('exits')
                if actual!=expected:
                    # Once a later chapter has been connected, the final boss room
                    # gains one correctly reversed east exit. Do not reject it.
                    if i==len(chapter)-1 and j==12 and isinstance(actual,dict):
                        extra={k:v for k,v in actual.items() if k not in expected}
                        ok=(all(actual.get(k)==v for k,v in expected.items())
                            and set(extra)=={'east'}
                            and rooms.get(extra['east'],{}).get('exits',{}).get('west')==f'{p}_{j:02d}')
                        if ok:
                            continue
                    raise RuntimeError(f'v107 rozdział {chapter_number}: uszkodzony szlak {p}_{j:02d}')
        return {'already_installed':True,'regions':0,'rooms':0,'mobs':0,
                'spawns':0,'npcs':0,'quests':0,'items':0,'recipes':0,'areas':()}
    if parent not in rooms or rooms[parent].get('zone') != parent_zone:
        raise RuntimeError('v107 rozdział I: brakuje ostatniej krainy v106')
    if 'east' in rooms[parent].get('exits',{}):
        raise RuntimeError('v107 rozdział I: zajęte wyjście z ostatniej krainy v106')
    for kind,required in planned.items():
        overlap=required & catalogs[kind].keys()
        if overlap:
            raise RuntimeError(f'v107 rozdział I: kolizja {kind}: {sorted(overlap)[0]}')
    if 'soul_shard' not in items:
        raise RuntimeError('v107 rozdział I: brakuje podstawowej nagrody duszy')
    for slug,name,*_ in chapter:
        p=prefix(slug)
        if name in zone_ids or p in categories or name.casefold() in guides:
            raise RuntimeError(f'v107 rozdział I: kolizja nazwy {name}')
    # Compute all edges up front: no one-way, unknown exit or region overlap.
    prospective={}
    prev=parent
    for slug,*_ in chapter:
        p=prefix(slug)
        for j in range(1,21):
            prospective[f'{p}_{j:02d}']=_room_exits(p,j,prev)
        prev=f'{p}_12'
    for i,(slug,*_) in enumerate(chapter[:-1]):
        prospective[f'{prefix(slug)}_12']['east']=f'{prefix(chapter[i+1][0])}_01'
    # Source room is v106, and has only one future exit.
    edges={parent:{'east':first},**prospective}
    for origin,exits in prospective.items():
        for direction,target in exits.items():
            if direction not in OPPOSITE:
                raise RuntimeError(f'v107 rozdział I: nieznany kierunek {direction}')
            reverse=(edges[target] if target in edges else rooms.get(target,{}).get('exits',{}))
            if reverse.get(OPPOSITE[direction])!=origin:
                raise RuntimeError(f'v107 rozdział I: przejście bez powrotu {origin}/{direction}')
    # Commit only after all validations succeed. Data stored in native registries.
    rooms[parent].setdefault('exits',{})['east']=first
    areas=[]
    for i,(slug,name,description,boss1,boss2,normal_names,materials) in enumerate(chapter):
        p=prefix(slug)
        low=start_level+i*1000
        high=low+999
        for j,label in enumerate(ROOMS_LABELS,1):
            rid=f'{p}_{j:02d}'
            level=low+(high-low)*(j-1)//19
            rooms[rid]={
                'name':f'{label} — {name}', 'zone':name,
                'desc':f'{description} {label}. Zalecane poziomy {low}–{high}; '
                       'brak twardej blokady wejścia.',
                'exits':prospective[rid], 'generator_level':level,
                'recommended_mastery':low, flag:True,
            }
        material_keys=[]
        for j,material_name in enumerate(materials,1):
            mid=f'{p}_material_{j}'
            material_keys.append(mid)
            items[mid]={
                'name':material_name, 'type':'craft_material','price':None,
                'sell_gold':(i+1)*140+j*120,
                'desc':f'{material_name} pozyskiwany w krainie {name}.',
                flag:True,
            }
        items[f'{p}_alloy']={
            'name':f'Stop {name}', 'type':'craft_material', 'price':None,
            'desc':f'Wytapiany z regionalnych surowców {name}.',
            flag:True,
        }
        recipes[f'{p}_alloy']={
            'name':f'Stop {name}', 'stations':('forge',),
            'ingredients':{material_keys[0]:2,material_keys[1]:2},
            'output':f'{p}_alloy','quantity':1,'profession':'Kowalstwo',
            'min_profession_level':low,'generator_level':low,
            'profession_xp':low*4,'tool_xp':low*3,
            'desc':f'Wytop stopu krainy {name}.', flag:True,
        }
        for j,mob_name in enumerate(normal_names,1):
            mid=f'{p}_mob_{j}'
            level=low+(high-low)*j//12
            mobs[mid]={
                'name':mob_name,'generator_level':level,
                'max_hp':int(level*1400), 'damage':int(level*12),
                'damage_type':'magic' if j%3==0 else 'physical',
                'class_xp_reward':level*750, 'soul_reward':level*620,
                'stat_reward':level*450, 'silver':level*300,
                'gold':600+(i*200)+j*65,'mithril':5+i,
                'drops':{material_keys[(j-1)%4]:.95,
                         material_keys[(j+1)%4]:.35,'soul_shard':.22},
                'quest_target':mid,'rank':'normal','stationary_mob':True,
                'auto_aggro':False,flag:True,
            }
            for room_index in (2+(j-1)%10,13+(j-1)%8):
                spawns.append((f'{p}_{room_index:02d}',mid))
        for j,boss_name in enumerate((boss1,boss2),1):
            mid=f'{p}_boss_{j}'
            level=high-(300 if j==1 else 0)
            mobs[mid]={
                'name':boss_name,'generator_level':level,
                'max_hp':int(level*12500*(j+1)),
                'damage':int(level*18*(j+1)),
                'damage_type':'magic' if j==2 else 'physical',
                'class_xp_reward':level*2400,'soul_reward':level*1750,
                'stat_reward':level*1350,'gold':2900+i*750+j*350,
                'mithril':18+i*2+j,'boss':True,'world_boss':False,
                'stationary_mob':True,'auto_aggro':False,
                'quest_target':mid,'leave_corpse':True,
                'drops':{material_keys[2]:1.0,material_keys[3]:1.0,'soul_shard':1.0},
                flag:True,
            }
            spawns.append((f'{p}_{12 if j==1 else 20:02d}',mid))
        npc_names=[f'{role} {name}' for role in NPC_ROLES]
        by_npc=[[] for _ in range(4)]
        for j,(kind,target_index) in enumerate(STORY_STEPS,1):
            nid=0 if j<=3 else 1 if j<=5 else 2 if j<=8 else 3
            giver=npc_names[nid]
            qid=f'{p}_story_{j:02d}'
            if kind=='talk_npc':
                target=f'{p}_npc_{target_index}'
                details={'target_npc':target}
                desc=f'Porozmawiaj z {npc_names[target_index-1]} w krainie {name}.'
                needed=1
            elif kind=='kill':
                target=(f'{p}_mob_{target_index}' if target_index<=10
                        else f'{p}_boss_{target_index-10}')
                details={'target':target}
                needed=1 if target_index>10 else 4
                desc=f'Pokonaj {needed} × {mobs[target]["name"]}. Wróć do {giver}.'
            else:
                target=material_keys[target_index-1]
                details={'target':target}
                needed=3
                desc=f'Zdobądź {needed} × {items[target]["name"]}. Wróć do {giver}.'
            quest={
                'name':f'{name}: Kronika Chaosu {j}/10',
                'giver':giver,'kind':kind,'needed':needed,
                'description':desc, 'generator_level':low,
                'reward_stat_progress':low*1550,
                'olc_reward_xp':low*1700,'olc_reward_class_xp':low*1500,
                'olc_reward_soul_xp':low*1350,
                'reward_gold':1000+i*400+j*150,
                'reward_mithril':i+3,
                'reward_items':{material_keys[(j-1)%4]:1},
                'repeatable':False,flag:True,
                **details,
            }
            if j>1:
                quest['requires_quest']=f'{p}_story_{j-1:02d}'
            quests[qid]=quest
            by_npc[nid].append(qid)
        for j,monster_index in enumerate(HUNT_TARGETS,1):
            target=(f'{p}_mob_{monster_index}' if monster_index<=10
                    else f'{p}_boss_{monster_index-10}')
            elite=monster_index>10
            needed=1 if elite else 4+(j%4)
            who=(j-1)%4
            qid=f'{p}_hunt_{j:02d}'
            quests[qid]={
                'name':f'{name}: Polowanie {j}',
                'giver':npc_names[who],'kind':'kill',
                'target':target,'needed':needed,
                'description':f'Pokonaj {needed} × {mobs[target]["name"]} i wróć do {npc_names[who]}.',
                'generator_level':low,'reward_stat_progress':low*1400,
                'olc_reward_xp':low*1650,'olc_reward_class_xp':low*1400,
                'olc_reward_soul_xp':low*1200,'reward_gold':900+i*350+j*90,
                'reward_mithril':i+2,'reward_items':{material_keys[(j-1)%4]:1},
                'repeatable':not elite,**({'repeat_cooldown': QUEST_REPEAT_COOLDOWN_SECONDS} if not elite else {}),flag:True,
            }
            by_npc[who].append(qid)
        for j in range(1,9):
            target=material_keys[(j-1)%4]
            needed=3+(j%5)
            who=(j+1)%4
            qid=f'{p}_collect_{j:02d}'
            quests[qid]={
                'name':f'{name}: Zbiór surowców {j}',
                'giver':npc_names[who],'kind':'collect',
                'target':target,'needed':needed,
                'description':f'Zdobądź {needed} × {items[target]["name"]}. Wróć do {npc_names[who]}.',
                'generator_level':low,'reward_stat_progress':low*1250,
                'olc_reward_xp':low*1500,'olc_reward_class_xp':low*1300,
                'olc_reward_soul_xp':low*1100,'reward_gold':900+i*340+j*90,
                'reward_mithril':i+2,'reward_items':{material_keys[j%4]:1},
                'repeatable':True,'repeat_cooldown':QUEST_REPEAT_COOLDOWN_SECONDS,flag:True,
            }
            by_npc[who].append(qid)
        for j in range(1,7):
            profession,tool,activity=PROFESSION_SPECS[(i*6+j)%len(PROFESSION_SPECS)]
            needed=5+j
            who=(j+2)%4
            qid=f'{p}_prof_{j:02d}'
            quests[qid]={
                'name':f'{name}: {profession} {j}',
                'giver':npc_names[who],'kind':'profession_action',
                'target':profession,'needed':needed,
                'description':f'Wykonaj {needed} czynności profesji {profession}: {activity}. '
                              f'Wróć do {npc_names[who]}.',
                'required_profession':profession,'specialist_tool_type':tool,
                'reward_profession':profession,'reward_profession_xp':low*2100,
                'reward_tool_type':tool,'reward_tool_xp':low*1900,
                'generator_level':low,'reward_stat_progress':low*1400,
                'olc_reward_xp':low*1500,'olc_reward_class_xp':low*1300,
                'olc_reward_soul_xp':low*1200,'reward_gold':1000+i*420+j*110,
                'reward_mithril':i+2,'reward_items':{material_keys[(j-1)%4]:1},
                'repeatable':True,'repeat_cooldown':QUEST_REPEAT_COOLDOWN_SECONDS,flag:True,
            }
            by_npc[who].append(qid)
        for j,roomno in enumerate((2,5,9,15),1):
            offered=tuple(by_npc[j-1])
            npc_id=f'{p}_npc_{j}'
            npcs[npc_id]={
                'name':npc_names[j-1],'room':f'{p}_{roomno:02d}',
                'dialogue':f'{npc_names[j-1]}: witaj w {name}. Wpisz quest list.',
                'specialist_quests':offered,'quest_chain':offered,
                'quest':offered[0], 'v700_story_npc':True,
                'v10300_era_npc':True,'v10400_era_npc':True,
                flag:True,
            }
        zone_ids[name]=p
        categories[p]='Endgame'
        guides[name.casefold()]=f'{p}_01'
        power[p]=low
        areas.append({
            'id':p,'name':name,'aliases':(name.casefold(),slug),
            'soul_min':low,'soul_max':high,
            'mastery_min':low,'mastery_max':high,
            'difficulty':f'era {low}-{high}', 'guide':name.casefold(),
            'enemies':', '.join(normal_names),
            'description':f'{description} 20 pokoi, 4 NPC, 40 questów, 10 potworów i 2 bossów.',
            'note':f'Zalecane poziomy {low}–{high}. Każdy boss dostępny solo; bez rajdów.',
        })
    return {'already_installed':False,'regions':len(chapter),'rooms':20*len(chapter),'mobs':12*len(chapter),
            'spawns':22*len(chapter),'npcs':4*len(chapter),'quests':40*len(chapter),'items':5*len(chapter),
            'recipes':len(chapter),'areas':tuple(areas)}


def CHAPTER_ONE_PARENT_ZONE():
    from world.v10600_region_index import REGIONS
    return REGIONS[-1][1]
