# -*- coding: utf-8 -*-
"""Kod rozwojowy v106: 30 obszarów, 720 pokoi, 1800 zadań i 60 bossów.

Podłączony jedynie pod flagą SOULBOUND_V106_STAGING=1. Przed produkcją
wymaga audytu TCP, migracji i balansu na normalnym HP.
"""
from __future__ import annotations
from world.v10600_region_index import REGIONS
from world.v10300_era_bez_granic import PROFESSION_SPECS

ROOM_LABELS = (
    'Brama Astralna', 'Przyczółek Zwiadowców', 'Rozstaje Gwiazd',
    'Kamienny Szlak', 'Dom Kronikarza', 'Ogród Kamiennych Głosów',
    'Pradawny Trakt', 'Komnata Mistrza', 'Dziedziniec Znaków',
    'Przejście Przysięgi', 'Cień Starego Tronu', 'Główna Galeria',
    'Sanktuarium Odkrywców', 'Tron Strażnika', 'Wschodnia Strażnica',
    'Przejście Run', 'Wąwóz Echa', 'Zachodni Most', 'Sekretne Archiwum',
    'Zapomniany Korytarz', 'Sala Znaków', 'Ukryta Kuźnia',
    'Szept Przodków', 'Sanktuarium Drugiego Bossa',
)
MOB_LABELS = (
    'Zwiadowca', 'Łowca', 'Weteran', 'Runiczny Mag', 'Widmo',
    'Obrońca', 'Herold', 'Golem', 'Wędrowiec', 'Strażnik',
)
NPC_LABELS = ('Kronikarz','Mistrz','Wysłannik','Badacz')
KINDS = {'story':15, 'prof':15, 'hunt':15, 'explore':10, 'event':5}


def prefix(slug):
    return f'v10600_{slug}'


def planned_ids():
    ids = {'rooms':set(),'mobs':set(),'npcs':set(),'quests':set(),
           'items':set(),'recipes':set()}
    for slug,*_ in REGIONS:
        p=prefix(slug)
        ids['rooms'].update(f'{p}_{j:02d}' for j in range(1,25))
        ids['mobs'].update(f'{p}_mob_{j}' for j in range(1,11))
        ids['mobs'].update(f'{p}_boss_{j}' for j in range(1,3))
        ids['npcs'].update(f'{p}_npc_{j}' for j in range(1,5))
        for kind,amount in KINDS.items():
            ids['quests'].update(f'{p}_{kind}_{j:02d}' for j in range(1,amount+1))
        ids['items'].update(f'{p}_material_{j}' for j in range(1,4))
        ids['items'].add(f'{p}_alloy')
        ids['recipes'].add(f'{p}_alloy')
    return ids


def room_exits(p,j,previous):
    # Główny szlak 1–14, osobna pętla 4–15–18–10 oraz sekretna odnoga 19–24.
    # Bez blokady poziomem i bez wyjść do nieistniejących pokoi.
    if j<=14:
        exits={'west':previous} if j==1 else {'south':f'{p}_{j-1:02d}'}
        if j<14:exits['north']=f'{p}_{j+1:02d}'
        if j==4:exits['east']=f'{p}_15'
        if j==10:exits['west']=f'{p}_18'
        if j==12:exits['east']=f'{p}_19'
        return exits
    if 15<=j<=18:
        exits={'west':f'{p}_{j-1:02d}' if j>15 else f'{p}_04',
               'east':f'{p}_{j+1:02d}' if j<18 else f'{p}_10'}
        return exits
    if j==19:return {'west':f'{p}_12','north':f'{p}_20'}
    if j==20:return {'south':f'{p}_19','north':f'{p}_21'}
    if j==21:return {'south':f'{p}_20','east':f'{p}_22'}
    if j==22:return {'west':f'{p}_21','east':f'{p}_23'}
    if j==23:return {'west':f'{p}_22','north':f'{p}_24'}
    return {'south':f'{p}_23'}


def _story_objective(part,p):
    # Celów nie oznaczamy tylko nazwą. Silnik obsługuje te typy natywnie.
    layout=(('talk_npc',2),('collect',1),('kill',1),('explore_frontier',0),
            ('talk_npc',3),('kill',5),('collect',2),('talk_npc',4),
            ('kill',11),('collect',3),('talk_npc',2),('kill',8),
            ('explore_frontier',0),('collect',3),('kill',12))
    kind,index=layout[part-1]
    if kind=='talk_npc':return kind,{'target_npc':f'{p}_npc_{index}'},1
    if kind=='collect':return kind,{'target':f'{p}_material_{index}'},2
    if kind=='kill':
        target=f'{p}_mob_{index}' if index<=10 else f'{p}_boss_{index-10}'
        return kind,{'target':target},1 if index>10 else 3
    return kind,{'target':'any'},4


def install(rooms,mobs,spawns,npcs,quests,items,recipes,areas,zone_ids,categories,guides,target_power):
    """Wymaga wszystkich historycznych rejestrów v105; bez bazy postaci.

    Sprawdza ID i nazwy przed zmianą, a kolejne wywołanie kontroluje kompletność.
    """
    ids=planned_ids()
    registries={'rooms':rooms,'mobs':mobs,'npcs':npcs,'quests':quests,
                'items':items,'recipes':recipes}
    first=f'{prefix(REGIONS[0][0])}_01'
    parent='v10500_przelom_14'
    if first in rooms:
        for kind,required in ids.items():
            if not required.issubset(registries[kind]):
                raise RuntimeError(f'v106: niekompletny katalog {kind}')
        if rooms.get(parent,{}).get('exits',{}).get('east')!=first:
            raise RuntimeError('v106: przerwane wejście z v105')
        return dict(regions=0,rooms=0,mobs=0,npcs=0,quests=0,areas=(),reason='already installed')
    if parent not in rooms or 'east' in rooms[parent].get('exits',{}):
        raise RuntimeError('v106: brak niezajętego wyjścia z v105')
    for kind,required in ids.items():
        overlap=required.intersection(registries[kind])
        if overlap:raise RuntimeError(f'v106: kolizja {kind}: {sorted(overlap)[0]}')
    for slug,name,*_ in REGIONS:
        p=prefix(slug)
        if name in zone_ids or p in categories or name.casefold() in guides:
            raise RuntimeError('v106: kolizja nazwy '+name)
    for _,_,_,_,boss1,boss2 in REGIONS:
        if not boss1 or not boss2:raise RuntimeError('v106: brak nazwy bossa')
    previous=parent;new_areas=[]
    for i,(slug,name,low,high,boss1,boss2) in enumerate(REGIONS,1):
        p=prefix(slug)
        rooms[previous].setdefault('exits',{})['east']=f'{p}_01'
        for j,label in enumerate(ROOM_LABELS,1):
            rid=f'{p}_{j:02d}';lvl=low+(high-low)*(j-1)//23
            rooms[rid]={'zone':name,'name':f'{label} — {name}',
                        'desc':f'{label}, kraina {name}. Zalecane poziomy {low}–{high}; '
                               'brak sztywnej blokady poziomu; ochrona nowicjusza może wymagać newbieprotect off. Ukryte ścieżki i pętla obejścia.',
                        'generator_level':lvl,'recommended_mastery':low,
                        'exits':room_exits(p,j,previous)}
        previous=f'{p}_14'
        for j,label in enumerate(('Odłamek','Rdzeń','Pieczęć'),1):
            items[f'{p}_material_{j}']={'name':f'{label} {name}',
                  'type':'craft_material','price':None,'sell_gold':200*i*j,
                  'desc':f'Materiał wydobyty podczas ekspedycji do {name}.'}
        items[f'{p}_alloy']={'name':f'Stop {name}','type':'craft_material',
                             'price':None,'desc':f'Stop do kuźni {name}.'}
        recipes[f'{p}_alloy']={'name':f'Stop {name}','stations':('forge',),
               'ingredients':{f'{p}_material_1':2,f'{p}_material_2':2},
               'output':f'{p}_alloy','quantity':1,'profession':'Kowalstwo',
               'generator_level':800,'min_profession_level':low,
               'profession_xp':low*4,'tool_xp':low*3,
               'desc':f'Regionalny stop z {name}.'}
        for j,label in enumerate(MOB_LABELS,1):
            mid=f'{p}_mob_{j}';lvl=low+(high-low)*j//12
            mobs[mid]={'name':f'{label} {name}','generator_level':lvl,
              'v106_authored_mob_stage':lvl,
              'max_hp':450000+lvl*1400,'damage':6000+lvl*12,
              'damage_type':'magic' if j%2==0 else 'physical',
              'class_xp_reward':lvl*650,'soul_reward':lvl*540,'stat_reward':lvl*450,
              'gold':600+i*160+j*50,'mithril':5+i,
              'drops':{f'{p}_material_1':0.85,f'{p}_material_2':0.50,
                       f'{p}_material_3':0.15,'soul_shard':0.2},
              'quest_target':mid}
            for roomno in (2+(j-1)%10,15+(j-1)%10):
                spawns.append((f'{p}_{roomno:02d}',mid))
        for j,(boss,roomno) in enumerate(((boss1,14),(boss2,24)),1):
            mid=f'{p}_boss_{j}';lvl=high-300 if j==1 else high
            mobs[mid]={'name':boss,'boss':True,'world_boss':True,
             'generator_level':lvl,'v106_authored_boss_stage':lvl,
             'max_hp':(6_000_000+lvl*22000)*(j+1),
             'damage':(4000+lvl*17)*(j+1),'damage_type':'magic',
             'class_xp_reward':lvl*2400,'soul_reward':lvl*1700,
             'stat_reward':lvl*1300,'gold':2400+i*700,'mithril':16+i*2,
             'drops':{f'{p}_material_3':1.0,'soul_shard':1.0},
             'quest_target':mid,'leave_corpse':True}
            spawns.append((f'{p}_{roomno:02d}',mid))
        quest_by_npc=[[] for _ in range(4)]
        npc_names=[f'{role} {name}' for role in NPC_LABELS]
        for kind,amount in KINDS.items():
            for j in range(1,amount+1):
                qid=f'{p}_{kind}_{j:02d}'
                if kind=='story':
                    nature,details,needed=_story_objective(j,p)
                    who=0 if j<=5 else 1 if j<=9 else 2 if j<=12 else 3
                    topic=('Pierwszy ślad','Wspomnienie','Zagrożenie','Rozpoznanie','Zapis Przysięgi',
                           'Warta','Relikwie','Świadek','Pierwszy Strażnik','Rytuał',
                           'Ostatnia wiadomość','Obrona','Ukryta ścieżka','Pieczęć','Finał') [j-1]
                elif kind=='prof':
                    who=2;nature='profession_action';profession,tool,activity=PROFESSION_SPECS[(i*15+j-1)%len(PROFESSION_SPECS)]
                    details={'target':profession};needed=8+i;topic=f'Zlecenie {profession}'
                elif kind=='hunt':
                    who=1;nature='kill';mid=f'{p}_mob_{1+(j-1)%10}' if j<=13 else f'{p}_boss_{j-13}'
                    details={'target':mid};needed=4 if j<=13 else 1;topic='Polowanie'
                elif kind=='explore':
                    who=3;nature='explore_frontier';details={'target':'any'}
                    needed=3+j;topic='Ekspedycja'
                else:
                    who=0;nature='kill';details={'target':f'{p}_boss_{(j-1)%2+1}'}
                    needed=1;topic='Wspólna obrona'
                giver=npc_names[who]
                # Opis celu odzwierciedla faktycznie obsługiwany typ progresu.
                if nature=='talk_npc':
                    destination=npc_names[int(details['target_npc'][-1])-1]
                    desc=f'Porozmawiaj z {destination} w {name}. Zadanie kończy się i wypłaca nagrodę podczas tej rozmowy.'
                elif nature=='collect':
                    desc=f'Zdobądź {needed} × {items[details["target"]]["name"]} i wróć do {giver}.'
                elif nature=='kill':
                    desc=f'Pokonaj {needed} × {mobs[details["target"]]["name"]} i wróć do {giver}.'
                elif nature=='profession_action':
                    desc=f'Wykonaj {needed} czynności profesji {profession} i wróć do {giver}.'
                else:
                    desc=f'Zbadaj {needed} nowych sektorów rubieży i wróć do {giver}.'
                q={'name':f'{name}: {topic} {j}', 'giver':giver,
                   'kind':nature,'needed':needed,'description':desc,
                   'generator_level':low,'reward_stat_progress':low*1400,
                   'olc_reward_xp':low*1600,'olc_reward_class_xp':low*1500,
                   'olc_reward_soul_xp':low*1300,'reward_gold':700+i*500+j*24,
                   'reward_mithril':i+2,
                   'reward_items':{f'{p}_material_1':1},**details}
                if kind=='story' and j>1:q['requires_quest']=f'{p}_story_{j-1:02d}'
                if kind=='prof':
                    q.update(required_profession=profession,specialist_tool_type=tool,
                       reward_profession=profession,reward_profession_xp=low*2000,
                       reward_tool_type=tool,reward_tool_xp=low*1800)
                if kind=='event':q['v106_party_contract']=True
                quests[qid]=q;quest_by_npc[who].append(qid)
        for j,(roomno,person) in enumerate(zip((5,8,13,20),npc_names),1):
            offered=tuple(quest_by_npc[j-1]);npcs[f'{p}_npc_{j}']={
               'name':person,'room':f'{p}_{roomno:02d}',
               'dialogue':f'{person}: jesteśmy w {name}. Dostępne zadania: quest list.',
               'specialist_quests':offered,'quest_chain':offered,'quest':offered[0],
               'v700_story_npc':True,'v10300_era_npc':True,'v10400_era_npc':True}
        zone_ids[name]=p;categories[p]='Endgame';guides[name.casefold()]=f'{p}_01'
        target_power[p]=low
        new_areas.append({'id':p,'name':name,'aliases':(name.casefold(),slug),
             'soul_min':low,'soul_max':high,'mastery_min':low,'mastery_max':high,
             'difficulty':f'era {low}-{high}', 'guide':name.casefold(),
             'enemies':', '.join(mobs[f'{p}_mob_{j}']['name'] for j in range(1,11)),
             'description':f'{name}: 24 pokoje, 4 NPC, 60 questów, 10 mobów i 2 bossów.',
             'note':f'Poziomy {low}–{high} zalecane; newbieprotect off dla świadomego wejścia początkującego.'})
    return {'regions':len(REGIONS),'rooms':len(ids['rooms']),'mobs':len(ids['mobs']),
       'npcs':len(ids['npcs']),'quests':len(ids['quests']),'items':len(ids['items']),
       'recipes':len(ids['recipes']),'areas':tuple(new_areas)}
