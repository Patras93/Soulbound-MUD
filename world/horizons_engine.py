# -*- coding: utf-8 -*-
"""v109: 12 fizycznie grywalnych krain (288 pokoi, 360 questów).

Wszystkie definicje przed instalacją trafiają do osobnych rejestrów; kolizja,
brak odwrotnej drogi albo brak celu questa odrzuca cały moduł bez modyfikacji
starego świata. Brak rajdów, blokad poziomu i agresji przy wejściu.
"""
from __future__ import annotations
from config.balance import QUEST_REPEAT_COOLDOWN_SECONDS

from world.horizon_index import REGIONS
from world.v10700_region_index_chapters_2_6 import ALL_NEXT
from world.v10300_era_bez_granic import PROFESSION_SPECS
from world.legends_v3100 import OPPOSITE

PREFIX = 'v10900_horizon'
PARENT = 'v10700_chaos_' + ALL_NEXT[-1][0] + '_12'
PARENT_ZONE = ALL_NEXT[-1][1]
LABELS = (
    'Brama', 'Droga Wędrowców', 'Stacja Zwiadowców', 'Ścieżka Pod Skałą',
    'Sala Kronik', 'Cichy Trakt', 'Posterunek Poszukiwaczy', 'Rozstaje',
    'Kamienny Most', 'Dom Rzemieślników', 'Dziedziniec Warty',
    'Przejście Pradawnych', 'Sala Przysięgi', 'Tron Strażnika',
    'Odgałęzienie Wschodnie', 'Komnata Śladów', 'Galeria Tajemnic',
    'Korytarz Echa', 'Skarbiec Ścieżki', 'Wąwóz Północny',
    'Miejsce Pamięci', 'Ukryta Kaplica', 'Sala Odkrywców',
    'Tron Horyzontu',
)
NPC_ROLES = ('Kronikarz', 'Zwiadowczyni', 'Rzemieślnik', 'Strażniczka')
QUEST_COUNTS = {'story': 8, 'hunt': 12, 'collect': 6, 'prof': 4}
HUNTS = (1,2,3,4,5,6,7,8,9,10,13,14)
STORY = (('talk_npc',2), ('kill',1), ('collect',1), ('kill',6),
         ('talk_npc',3), ('collect',3), ('kill',13), ('kill',14))
assert len(LABELS) == 24 and len(REGIONS) == 12
assert sum(QUEST_COUNTS.values()) == 30


def prefix(slug):
    return f'{PREFIX}_{slug}'


def planned_ids():
    result = {kind:set() for kind in ('rooms','mobs','npcs','quests','items','recipes')}
    for slug,*_ in REGIONS:
        p = prefix(slug)
        result['rooms'].update(f'{p}_{i:02d}' for i in range(1,25))
        result['mobs'].update(f'{p}_mob_{i}' for i in range(1,13))
        result['mobs'].update(f'{p}_boss_{i}' for i in (1,2))
        result['npcs'].update(f'{p}_npc_{i}' for i in range(1,5))
        result['items'].update(f'{p}_material_{i}' for i in range(1,5))
        result['recipes'].add(f'{p}_alloy')
        result['items'].add(f'{p}_alloy')
        for kind,amount in QUEST_COUNTS.items():
            result['quests'].update(f'{p}_{kind}_{i:02d}' for i in range(1,amount+1))
    return result


def room_exits(p, i, previous, next_room):
    if i <= 14:
        doors = {'west':previous} if i == 1 else {'south':f'{p}_{i-1:02d}'}
        if i < 14:
            doors['north'] = f'{p}_{i+1:02d}'
        if i == 3:
            doors['east'] = f'{p}_15'
        if i == 10:
            doors['east'] = f'{p}_20'
        if i == 14 and next_room:
            doors['east'] = next_room
        return doors
    start = 15 if i <= 19 else 20
    origin = 3 if i <= 19 else 10
    doors = {'west':f'{p}_{i-1:02d}' if i != start else f'{p}_{origin:02d}'}
    if i < (19 if i <= 19 else 24):
        doors['east'] = f'{p}_{i+1:02d}'
    return doors


def _target(p, index):
    return f'{p}_mob_{index}' if index <= 12 else f'{p}_boss_{index-12}'


def install(rooms,mobs,spawns,npcs,quests,items,recipes,
            zone_ids,categories,guides,power):
    """Append new regional content after v107; no SQLite migration.

    Can be called twice; second call validates complete IDs and path without
    altering any catalog. Never removes or mutates old quests/EQ/rewards.
    """
    originals = {'rooms':rooms, 'mobs':mobs, 'npcs':npcs,
                 'quests':quests, 'items':items, 'recipes':recipes}
    required = planned_ids()
    first = prefix(REGIONS[0][0])+'_01'
    parent = rooms.get(PARENT)
    if parent is None or parent.get('zone') != PARENT_ZONE:
        raise RuntimeError('v109: nie znaleziono końcowej komnaty v107')
    if first in rooms:
        if any(not ids <= originals[k].keys() for k,ids in required.items()):
            raise RuntimeError('v109: wykryto częściową instalację krain')
        if parent.get('exits',{}).get('east') != first:
            raise RuntimeError('v109: uszkodzone wejście do nowych krain')
        for region_i, region in enumerate(REGIONS):
            p = prefix(region[0])
            prev = PARENT if region_i == 0 else prefix(REGIONS[region_i-1][0])+'_14'
            nxt = prefix(REGIONS[region_i+1][0])+'_01' if region_i<11 else None
            for i in range(1,25):
                if rooms[f'{p}_{i:02d}'].get('exits') != room_exits(p,i,prev,nxt):
                    raise RuntimeError('v109: zmieniona trasa w zainstalowanej krainie')
        return dict(already_installed=True, regions=0, rooms=0, mobs=0,
                    spawns=0,npcs=0,quests=0,items=0,recipes=0,areas=())
    if 'east' in parent.get('exits',{}):
        raise RuntimeError('v109: istniejące przejście v107 zajmuje planowaną drogę')
    if 'soul_shard' not in items:
        raise RuntimeError('v109: brak historycznej nagrody soul_shard')
    for kind, planned in required.items():
        conflict = planned.intersection(originals[kind])
        if conflict:
            raise RuntimeError('v109: kolizja '+kind+' '+min(conflict))
    for slug,name,*_ in REGIONS:
        if name in zone_ids or prefix(slug) in categories or name.casefold() in guides:
            raise RuntimeError('v109: konflikt nazwy krainy '+name)
    prospective = {name:{} for name in originals}
    new_spawns=[]
    new_zones={}
    new_categories={}
    new_guides={}
    new_power={}
    areas=[]
    for idx,(slug,name,description,boss1,boss2,normal_names,materials) in enumerate(REGIONS):
        p=prefix(slug)
        low=90001+1000*idx
        high=low+999
        previous=PARENT if idx==0 else prefix(REGIONS[idx-1][0])+'_14'
        following=prefix(REGIONS[idx+1][0])+'_01' if idx+1<len(REGIONS) else None
        for j,label in enumerate(LABELS,1):
            rid=f'{p}_{j:02d}'
            lvl=low+(high-low)*(j-1)//23
            prospective['rooms'][rid]={
                'name':f'{label} — {name}','zone':name,
                'desc':f'{description} {label}. Zalecane poziomy {low}–{high}; '
                       'nie ma wymaganego poziomu do wejścia.',
                'exits':room_exits(p,j,previous,following),
                'generator_level':lvl,'recommended_mastery':low,
                'v109_horizon':True,
            }
        material_ids=[]
        for j,item_name in enumerate(materials,1):
            item=f'{p}_material_{j}'
            material_ids.append(item)
            prospective['items'][item]={
                'name':item_name,'type':'craft_material', 'price':None,
                'sell_gold':2400+idx*170+j*120,
                'desc':f'Surowiec z krainy {name}.','v109_horizon':True,
            }
        alloy=f'{p}_alloy'
        prospective['items'][alloy]={
            'name':f'Stop {name}', 'type':'craft_material','price':None,
            'desc':f'Wytop z materiałów regionu {name}.','v109_horizon':True,
        }
        prospective['recipes'][alloy]={
            'name':f'Stop {name}','stations':('forge',),
            'ingredients':{material_ids[0]:2,material_ids[1]:2},
            'output':alloy,'quantity':1,'profession':'Kowalstwo',
            'min_profession_level':low,'generator_level':low,
            'profession_xp':low*4,'tool_xp':low*3,
            'desc':f'Regionalny stop: {name}.','v109_horizon':True,
        }
        for j,mob_name in enumerate(normal_names,1):
            mob_id=f'{p}_mob_{j}'
            level=low+(high-low)*j//14
            prospective['mobs'][mob_id]={
                'name':mob_name,'generator_level':level,
                'max_hp':level*1400,'damage':level*12,
                'damage_type':'magic' if j%3==0 else 'physical',
                'class_xp_reward':level*750,'soul_reward':level*620,
                'stat_reward':level*450,'silver':level*300,
                'gold':1000+idx*190+j*90,'mithril':8+idx,
                'drops':{material_ids[(j-1)%4]:.95,
                         material_ids[(j+1)%4]:.35,'soul_shard':.22},
                'quest_target':mob_id,'rank':'normal','stationary_mob':True,
                'auto_aggro':False,'v109_horizon':True,
            }
            for room_number in (2+(j-1)%12,15+(j-1)%10):
                new_spawns.append((f'{p}_{room_number:02d}',mob_id))
        for j,boss_name in enumerate((boss1,boss2),1):
            mob_id=f'{p}_boss_{j}'
            lvl=high-(250 if j==1 else 0)
            prospective['mobs'][mob_id]={
                'name':boss_name,'generator_level':lvl,
                'max_hp':lvl*12500*(j+1),'damage':lvl*18*(j+1),
                'damage_type':'magic' if j==2 else 'physical',
                'class_xp_reward':lvl*2400,'soul_reward':lvl*1750,
                'stat_reward':lvl*1350,'gold':4000+idx*850+j*450,
                'mithril':25+idx*2+j,'boss':True,'world_boss':False,
                'stationary_mob':True,'auto_aggro':False,
                'quest_target':mob_id,'leave_corpse':True,
                'drops':{material_ids[2]:1.0,material_ids[3]:1.0,'soul_shard':1.0},
                'v109_horizon':True,
            }
            new_spawns.append((f'{p}_{14 if j==1 else 24:02d}',mob_id))
        npcnames=[f'{title} {name}' for title in NPC_ROLES]
        offered=[[] for _ in range(4)]
        for j,(kind,n) in enumerate(STORY,1):
            who=min(3,(j-1)//2)
            qid=f'{p}_story_{j:02d}'
            extra={}
            if kind=='talk_npc':
                extra['target_npc']=f'{p}_npc_{n}'
                goal=f'Porozmawiaj z {npcnames[n-1]}.'
                needed=1
            elif kind=='kill':
                monster=_target(p,n)
                extra['target']=monster
                needed=1 if n>12 else 3
                goal=f'Pokonaj {needed} × {prospective["mobs"][monster]["name"]}.'
            else:
                item=material_ids[n-1]
                extra['target']=item
                needed=4
                goal=f'Zdobądź {needed} × {prospective["items"][item]["name"]}.'
            quest={
                'name':f'{name}: Kronika Horyzontu {j}/8',
                'giver':npcnames[who],'kind':kind,'needed':needed,
                'description':goal+f' Wróć do {npcnames[who]}.',
                'generator_level':low,'reward_stat_progress':low*1600,
                'olc_reward_xp':low*1900,'olc_reward_class_xp':low*1600,
                'olc_reward_soul_xp':low*1450,
                'reward_gold':2500+idx*410+j*180,
                'reward_mithril':6+idx,'reward_items':{material_ids[(j-1)%4]:1},
                'repeatable':False,'v109_horizon':True,**extra,
            }
            if j>1:
                quest['requires_quest']=f'{p}_story_{j-1:02d}'
            prospective['quests'][qid]=quest
            offered[who].append(qid)
        for j,n in enumerate(HUNTS,1):
            mob=_target(p,n)
            who=(j-1)%4
            needed=1 if n>12 else 4+j%4
            qid=f'{p}_hunt_{j:02d}'
            prospective['quests'][qid]={
                'name':f'{name}: Polowanie {j}','giver':npcnames[who],
                'kind':'kill','target':mob,'needed':needed,
                'description':f'Pokonaj {needed} × {prospective["mobs"][mob]["name"]}. Wróć do {npcnames[who]}.',
                'generator_level':low,'reward_stat_progress':low*1450,
                'olc_reward_xp':low*1800,'olc_reward_class_xp':low*1500,
                'olc_reward_soul_xp':low*1300,
                'reward_gold':1900+idx*330+j*120,'reward_mithril':4+idx,
                'reward_items':{material_ids[(j-1)%4]:1},
                'repeatable':n<=12,**({'repeat_cooldown':QUEST_REPEAT_COOLDOWN_SECONDS} if n<=12 else {}),'v109_horizon':True,
            }
            offered[who].append(qid)
        for j in range(1,7):
            who=(j+1)%4
            item=material_ids[(j-1)%4]
            count=4+j
            qid=f'{p}_collect_{j:02d}'
            prospective['quests'][qid]={
                'name':f'{name}: Materiały {j}','giver':npcnames[who],
                'kind':'collect','target':item,'needed':count,
                'description':f'Zbierz {count} × {prospective["items"][item]["name"]}.',
                'generator_level':low,'reward_stat_progress':low*1300,
                'olc_reward_xp':low*1700,'olc_reward_class_xp':low*1400,
                'olc_reward_soul_xp':low*1200,
                'reward_gold':1700+idx*300+j*120,'reward_mithril':4+idx,
                'reward_items':{material_ids[j%4]:1},
                'repeatable':True,'repeat_cooldown':QUEST_REPEAT_COOLDOWN_SECONDS,'v109_horizon':True,
            }
            offered[who].append(qid)
        for j in range(1,5):
            who=(j+2)%4
            profession,tool,action=PROFESSION_SPECS[(idx*4+j)%len(PROFESSION_SPECS)]
            count=6+j
            qid=f'{p}_prof_{j:02d}'
            prospective['quests'][qid]={
                'name':f'{name}: {profession} {j}','giver':npcnames[who],
                'kind':'profession_action','target':profession,'needed':count,
                'description':f'Wykonaj {count} czynności {profession}: {action}.',
                'required_profession':profession,'specialist_tool_type':tool,
                'reward_profession':profession,'reward_profession_xp':low*2300,
                'reward_tool_type':tool,'reward_tool_xp':low*2100,
                'generator_level':low,'reward_stat_progress':low*1450,
                'olc_reward_xp':low*1600,'olc_reward_class_xp':low*1400,
                'olc_reward_soul_xp':low*1300,
                'reward_gold':2000+idx*380+j*150,'reward_mithril':5+idx,
                'reward_items':{material_ids[(j-1)%4]:1},
                'repeatable':True,'repeat_cooldown':QUEST_REPEAT_COOLDOWN_SECONDS,'v109_horizon':True,
            }
            offered[who].append(qid)
        for j,room in enumerate((2,5,9,21),1):
            npc_id=f'{p}_npc_{j}'
            offered_ids=tuple(offered[j-1])
            prospective['npcs'][npc_id]={
                'name':npcnames[j-1],'room':f'{p}_{room:02d}',
                'dialogue':f'{npcnames[j-1]}: witaj w {name}. Wpisz quest list.',
                'specialist_quests':offered_ids,'quest_chain':offered_ids,
                'quest':offered_ids[0],'v700_story_npc':True,
                'v10300_era_npc':True,'v10400_era_npc':True,
                'v109_horizon':True,
            }
        new_zones[name]=p
        new_categories[p]='Endgame'
        new_guides[name.casefold()]=f'{p}_01'
        new_power[p]=low
        areas.append({
            'id':p,'name':name,'aliases':(name.casefold(),slug),
            'soul_min':low,'soul_max':high,
            'mastery_min':low,'mastery_max':high,
            'difficulty':f'era {low}-{high}', 'guide':name.casefold(),
            'enemies':', '.join(normal_names),
            'description':f'{description} 24 pokoje, 4 NPC, 30 questów, 12 potworów i 2 bossów.',
            'note':f'Zalecane poziomy {low}–{high}; solo lub grupa 2–6, bez rajdów.',
        })
    # Fail-closed: complete path, reachable NPC, quest targets and unique spawns.
    connection={PARENT:{'east':first}}
    connection.update({key:value['exits'] for key,value in prospective['rooms'].items()})
    for origin,doors in connection.items():
        for direction,target in doors.items():
            if direction not in OPPOSITE or target not in connection:
                raise RuntimeError('v109: brak korytarza '+origin)
            if connection[target].get(OPPOSITE[direction]) != origin:
                raise RuntimeError('v109: przejście bez powrotu '+origin+'/'+direction)
    if len(set(new_spawns))!=len(new_spawns):
        raise RuntimeError('v109: zdublowany spawn')
    for rid,mid in new_spawns:
        if rid not in prospective['rooms'] or mid not in prospective['mobs']:
            raise RuntimeError('v109: nieistniejący mob w spawnie')
    for qid,quest in prospective['quests'].items():
        kind=quest['kind']
        target=quest.get('target')
        if ((kind=='kill' and target not in prospective['mobs'])
            or (kind=='collect' and target not in prospective['items'])
            or (kind=='talk_npc' and quest.get('target_npc') not in prospective['npcs'])
            or (kind=='profession_action' and not quest.get('required_profession'))):
            raise RuntimeError('v109: niedostępny cel '+qid)
        if quest.get('requires_quest') and quest['requires_quest'] not in prospective['quests']:
            raise RuntimeError('v109: brak etapu fabuły '+qid)
    if any(len(offered)==0 for npc in prospective['npcs'].values()
           for offered in [npc['specialist_quests']]):
        raise RuntimeError('v109: NPC bez zadań')
    if {k:len(prospective[k]) for k in prospective} != {
            'rooms':288,'mobs':168,'npcs':48,'quests':360,'items':60,'recipes':12}:
        raise RuntimeError('v109: niekompletna zawartość świata')
    if len(new_spawns)!=312:
        raise RuntimeError('v109: niekompletne odrodzenia mobów')
    # Commit: after preflight, without any DB writes and without replacing old IDs.
    for kind,registry in originals.items():
        registry.update(prospective[kind])
    parent.setdefault('exits',{})['east']=first
    spawns.extend(new_spawns)
    zone_ids.update(new_zones)
    categories.update(new_categories)
    guides.update(new_guides)
    power.update(new_power)
    return dict(already_installed=False,regions=12,rooms=288,mobs=168,
                spawns=312,npcs=48,quests=360,items=60,recipes=12,
                areas=tuple(areas))
