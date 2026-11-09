# -*- coding: utf-8 -*-
"""v104 / etap 2: rzeczywiste regiony 5001-10000 w rejestrach silnika.

Dodatek statyczny, deterministyczny. Nie zapisuje i nie migruje bazy kont.
Limity w opisach to ZALECENIA, nie bramki lokacji.
"""
from __future__ import annotations

from core.classes_skills import CLASSES
from world.v10300_era_bez_granic import PROFESSION_SPECS

# Unikalne miejsca, fabuły i bossowie. Przedziały są ciągłe.
from world.v10400_region_index import REGIONS
ROOM_PARTS = (
    'Brama', 'Punkt Strażniczy', 'Droga Pielgrzymów', 'Warsztat Rzemieślników',
    'Dom Kronikarza', 'Targ Wędrowców', 'Przejście Żołnierzy', 'Kwatera Mistrza',
    'Ścieżka Prób', 'Arena Strażnika', 'Zapomniana Galeria', 'Pracownia Alchemiczna',
    'Sanktuarium', 'Tron Władcy',
)
ENEMY_PARTS = ('Zwiadowca', 'Łowca', 'Żołnierz', 'Runiczny Mag', 'Zjawisko',
               'Weteran', 'Stróż', 'Tytan')
OPPOSITE = {'north': 'south', 'south': 'north', 'east': 'west', 'west': 'east'}


def _planned_ids(class_rows=None):
    classes = tuple(row[0] for row in (CLASSES if class_rows is None else class_rows))
    ids = {
        'rooms': {f'v10400_{slug}_{n:02d}' for slug, *_ in REGIONS for n in range(1,15)},
        'mobs': {f'v10400_{slug}_{kind}_{n}' for slug, *_ in REGIONS
                 for kind,indices in (('mob',range(1,9)),('boss',range(1,3))) for n in indices},
        'npcs': {f'v10400_{slug}_npc_{n}' for slug,*_ in REGIONS for n in range(1,4)},
        'items': {f'v10400_{slug}_{kind}' for slug,*_ in REGIONS
                  for kind in ('material_1','material_2','material_3','alloy','charm')},
        'recipes': {f'v10400_{slug}_{kind}' for slug,*_ in REGIONS for kind in ('alloy','charm')},
        'quests': {f'v10400_{slug}_story_{n:02d}' for slug,*_ in REGIONS for n in range(1,13)} |
                  {f'v10400_{slug}_prof_{n:02d}' for slug,*_ in REGIONS for n in range(1,len(PROFESSION_SPECS)+1)} |
                  {f'v10400_{slug}_class_{n:02d}' for slug,*_ in REGIONS for n in range(1,len(classes)+1)},
    }
    return ids


def install(rooms, mobs, spawns, npcs, quests, items, recipes,
            areas, zone_ids, categories, guides, target_power, *, class_rows=None):
    """Podłącza 10 krain do ostatniej sali v103 atomowo po prewalidacji ID.

    Wywoływany raz podczas bootstrapu świata. Przy ponownym wywołaniu no-op.
    Nie dotyka baz graczy, zapisów questów ani polityki limitów.
    """
    # v110 historical audits may supply the 22 original classes explicitly.
    # Regular runtime callers always retain the existing registry behavior.
    active_classes = tuple(CLASSES if class_rows is None else class_rows)
    first = 'v10400_sztorm_01'
    if first in rooms:
        # Odmowa cichego zaakceptowania niekompletnej/kolizyjnej instalacji.
        ids = _planned_ids(active_classes)
        for key,registry in (('rooms',rooms),('mobs',mobs),('npcs',npcs),
                             ('quests',quests),('items',items),('recipes',recipes)):
            if not ids[key].issubset(registry):
                raise RuntimeError(f'v104 etap2: niekompletny ponowny import {key}')
        if rooms.get('v10300_tron_12',{}).get('exits',{}).get('east') != first:
            raise RuntimeError('v104 etap2: utracone przejście z v103')
        return {'regions':0,'rooms':0,'mobs':0,'npcs':0,'quests':0,
                'items':0,'recipes':0,'areas':(), 'reason':'already installed'}
    parent='v10300_tron_12'
    if parent not in rooms:
        raise RuntimeError('v104 etap2: brak Tronu Tysiąca Epok z v103')
    if 'east' in rooms[parent].get('exits',{}):
        raise RuntimeError('v104 etap2: wschodnie przejście z v103 zajęte')
    ids = _planned_ids(active_classes)
    for name,registry in (('rooms',rooms),('mobs',mobs),('npcs',npcs),
                          ('quests',quests),('items',items),('recipes',recipes)):
        collisions=ids[name].intersection(registry)
        if collisions:
            raise RuntimeError(f'v104 etap2: kolizja {name}: {sorted(collisions)[0]}')
    for slug,zone,*_ in REGIONS:
        if zone in zone_ids or f'v10400_{slug}' in categories or zone.casefold() in guides:
            raise RuntimeError(f'v104 etap2: kolizja regionu: {zone}')
    if len({row[0] for row in active_classes}) != len(active_classes):
        raise RuntimeError('v104 etap2: powtórzona nazwa klasy')
    if len({row[0] for row in PROFESSION_SPECS}) != len(PROFESSION_SPECS):
        raise RuntimeError('v104 etap2: powtórzona profesja')

    new_areas=[]
    previous=parent
    class_names=tuple(row[0] for row in active_classes)
    for stage,(slug,zone,low,high,theme,boss1,boss2) in enumerate(REGIONS,1):
        prefix=f'v10400_{slug}'
        entrance=f'{prefix}_01'
        rooms[previous].setdefault('exits',{})['east']=entrance
        for index,part in enumerate(ROOM_PARTS,1):
            rid=f'{prefix}_{index:02d}'
            recommended=low + ((high-low)*(index-1))//13
            exits={'west':previous} if index==1 else {'south':f'{prefix}_{index-1:02d}'}
            if index<14:
                exits['north']=f'{prefix}_{index+1:02d}'
            rooms[rid]={
                'zone':zone, 'name':f'{part} — {zone}',
                'desc':f'{theme}. {part} w krainie {zone}, poziomy {low}–{high} '
                       'są zalecane, ale nie blokują wejścia. Można wrócić.',
                'generator_level':recommended,'recommended_mastery':recommended,
                'exits':exits,
            }
        previous=f'{prefix}_14'
        m1,m2,m3=(f'{prefix}_material_{i}' for i in (1,2,3))
        alloy=f'{prefix}_alloy'; charm=f'{prefix}_charm'
        for item_id,label,sell in ((m1,'Odłamek',60),(m2,'Rdzeń',100),(m3,'Pieczęć',150),(alloy,'Stop',210)):
            items[item_id]={'name':f'{label} {zone}','type':'craft_material',
                            'price':None,'sell_gold':sell*stage,
                            'desc':f'Materiał z krainy {zone}.'}
        items[charm]={'name':f'Talizman {zone}','type':'armor','slot':'charm',
                      'defense':low*3,'price':None,'rarity':'epic',
                      'desc':f'Ochronny talizman {zone} dla wypraw na poziomach {low}–{high}.'}
        recipes[alloy]={'name':f'Stop {zone}','stations':('forge',),
                        'ingredients':{m1:2,m2:2},'output':alloy,'quantity':1,
                        'profession':'Kowalstwo','generator_level':800,'min_profession_level':low,
                          'profession_xp':max(200,low*4),'tool_xp':max(150,low*3),
                        'desc':f'Stop z dwóch odłamków i dwóch rdzeni krainy {zone}.'}
        recipes[charm]={'name':f'Talizman {zone}','stations':('forge',),
                        'ingredients':{alloy:2,m3:1,'steel_ingot':1},'output':charm,'quantity':1,
                        'profession':'Kowalstwo','generator_level':800,'min_profession_level':low,
                          'profession_xp':max(200,low*4),'tool_xp':max(150,low*3),
                        'desc':f'Rytualny talizman ze stopów i pieczęci krainy {zone}.'}
        for n,kind in enumerate(ENEMY_PARTS,1):
            mid=f'{prefix}_mob_{n}'
            level=low+((high-low)*n)//10
            mobs[mid]={
                'name':f'{kind} {zone}','generator_level':level,
                'max_hp':160000 + level*1100 + stage*50000,
                'damage':1500 + level*7 + stage*600,
                'damage_type':'magic' if n%2==0 else 'physical',
                'class_xp_reward':1_000_000+stage*900_000+n*150_000,
                'soul_reward':800_000+stage*600_000+n*100_000,
                'stat_reward':500_000+stage*350_000+n*100_000,
                'gold':250+stage*90+n*30,'silver':2000+stage*600,
                'mithril':3+stage,
                'drops':{m1:0.9,m2:0.5,'soul_shard':0.2},
                'quest_target':mid,'endgame_region_mastery':level,
            }
            for room_no in (2+((n-1)%8), 3+((n-1)%8)):
                spawns.append((f'{prefix}_{room_no:02d}',mid))
        for n,name,room_no in ((1,boss1,10),(2,boss2,14)):
            mid=f'{prefix}_boss_{n}'
            level=low if n==1 else high
            mobs[mid]={
                'name':name,'boss':True,'world_boss':True,
                'generator_level':level,
                'max_hp':(5_000_000+level*20_000)*(n+1),
                'damage':(2_500+level*15)*(n+1),
                'damage_type':'magic',
                'class_xp_reward':2_000_000+stage*1_500_000*n,
                'soul_reward':1_500_000+stage*900_000*n,
                'stat_reward':1_000_000+stage*600_000*n,
                'gold':1200+stage*450,'silver':16000+stage*1800,
                'mithril':10+stage*2,
                'drops':{m3:1.0,'soul_shard':1.0},
                'quest_target':mid,'endgame_region_mastery':level,
                'leave_corpse':True,
            }
            spawns.append((f'{prefix}_{room_no:02d}',mid))
        story=[]
        goals=([('kill',f'{prefix}_mob_{i}',2+i%3) for i in range(1,9)] +
               [('collect',m1,5),('collect',m2,4),
                ('kill',f'{prefix}_boss_1',1),('kill',f'{prefix}_boss_2',1)])
        for n,(kind,target,needed) in enumerate(goals,1):
            qid=f'{prefix}_story_{n:02d}'
            giver=(f'Kronikarz {zone}' if n<=4 else
                   f'Mistrz {zone}' if n<=8 else f'Strażniczka {zone}')
            obj_name=mobs[target]['name'] if kind=='kill' else items[target]['name']
            quests[qid]={
                'name':f'{zone}: kronika {n} z 12', 'giver':giver,
                'kind':kind,'target':target,'needed':needed,
                'description':f'{"Pokonaj" if kind=="kill" else "Zdobądź"} {needed} × {obj_name}. '
                              f'Wróć do NPC {giver}.',
                'generator_level':low+((high-low)*(n-1))//11,
                'reward_stat_progress':500_000+stage*1_000_000+n*180_000,
                'reward_gold':400+stage*350+n*100,
                'reward_mithril':stage+n//4,
                'reward_items':{m1:1},
                **({'requires_quest':f'{prefix}_story_{n-1:02d}'} if n>1 else {}),
            }
            story.append(qid)
        prof=[]
        for n,(profession,tool_type,activity) in enumerate(PROFESSION_SPECS,1):
            qid=f'{prefix}_prof_{n:02d}'
            quests[qid]={
                'name':f'{zone}: kontrakt {profession}',
                'giver':f'Strażniczka {zone}',
                'kind':'profession_action','target':profession,'needed':10+2*stage,
                'description':f'Wykonaj {10+2*stage} czynności profesji {profession}: {activity}. '
                              f'Wróć do Strażniczki {zone}.',
                'required_profession':profession,
                'recommended_profession_level':low,
                'generator_level':low,
                'specialist_tool_type':tool_type,
                'reward_profession':profession,
                'reward_profession_xp':low*2700+stage*150_000,
                'reward_tool_type':tool_type,
                'reward_tool_xp':low*2700+stage*150_000,
                'reward_gold':800+stage*350,
                'reward_mithril':stage,
                'reward_items':{m2:1},
            }
            prof.append(qid)
        class_q=[]
        for n,klass in enumerate(class_names,1):
            qid=f'{prefix}_class_{n:02d}'
            target=f'{prefix}_mob_{(n-1)%8+1}' if n%3 else f'{prefix}_boss_1'
            quests[qid]={
                'name':f'{klass}: próba w {zone}',
                'giver':f'Mistrz {zone}', 'kind':'kill','target':target,
                'needed':1 if n%3==0 else 3,
                'required_class':klass,
                'description':f'Jako {klass} pokonaj {1 if n%3==0 else 3} × '
                              f'{mobs[target]["name"]} w krainie {zone}.',
                'generator_level':low,
                'reward_stat_progress':low*2200+stage*230_000,
                'reward_gold':450+stage*350,'reward_mithril':stage,
                'reward_items':{m1:1},
            }
            class_q.append(qid)
        for n,room_no,person,offered in (
            (1,5,f'Kronikarz {zone}',story[:4]),
            (2,8,f'Mistrz {zone}',tuple(story[4:8])+tuple(class_q)),
            (3,13,f'Strażniczka {zone}',tuple(story[8:])+tuple(prof)),
        ):
            nid=f'{prefix}_npc_{n}'
            npcs[nid]={
                'name':person,'room':f'{prefix}_{room_no:02d}',
                'dialogue':f'{person}: {theme}. Wybierz quest numerem; przyjmij 1.',
                'specialist_quests':tuple(offered),'quest_chain':tuple(offered),
                'quest':offered[0],
                'v700_story_npc':True,'v10300_era_npc':True,'v10400_era_npc':True,
            }
        zone_ids[zone]=prefix
        categories[prefix]='Endgame'
        guides[zone.casefold()]=entrance
        target_power[prefix]=low
        new_areas.append({
            'id':prefix,'name':zone,'aliases':(zone.casefold(),slug),
            'soul_min':low,'soul_max':high,'mastery_min':low,'mastery_max':high,
            'difficulty':f'era {low}-{high}','guide':zone.casefold(),
            'enemies':', '.join(mobs[f'{prefix}_mob_{n}']['name'] for n in range(1,9)),
            'description':f'{zone}: 14 komnat, 3 NPC, 8 zwykłych przeciwników, 2 bossów. {theme}.',
            'note':f'Połączenie z poprzednią krainą; poziomy {low}–{high} zalecane, nie wymagane.',
        })
    return {'regions':len(REGIONS), 'rooms':len(ids['rooms']), 'mobs':len(ids['mobs']),
            'npcs':len(ids['npcs']),'quests':len(ids['quests']),
            'story_quests':12*len(REGIONS),'profession_quests':len(PROFESSION_SPECS)*len(REGIONS),
            'class_quests':len(active_classes)*len(REGIONS),
            'items':len(ids['items']),'recipes':len(ids['recipes']),
            'areas':tuple(new_areas)}
