# -*- coding: utf-8 -*-
"""v110: atomowa instalacja 12 nowych krain i 700 grywalnych questów.

Dane poszczególnych krain żyją w world.realms.*. Konstruktor pracuje na
prywatnych rejestrach, nie zapisuje bazy SQLite i nie usuwa dawnych nagród.
"""
from __future__ import annotations
from config.balance import QUEST_REPEAT_COOLDOWN_SECONDS
from world.v11000_realm_index import REGIONS
from world.horizon_index import REGIONS as OLD_REGIONS
from world.v10300_era_bez_granic import PROFESSION_SPECS as OLD_PROFS
from core.archetypes.expansion import (CLASS_SPECS, RACE_SPECS, PROFESSION_SPECS)
from world.legends_v3100 import OPPOSITE

PREFIX='v11000_realm'
PARENT='v10900_horizon_'+OLD_REGIONS[-1][0]+'_14'
ROOM_LABELS=(
    'Brama Nowej Ery','Sala Przybyszów','Kronika Początków','Dawny Trakt',
    'Plac Strażników','Wąwóz Osobliwości','Komnata Badaczy','Ścieżka Przygód',
    'Obóz Wędrowców','Studnia Historii','Most Wschodni','Posterunek Osadników',
    'Wrota Mistrzów','Tron Pierwszego Strażnika','Pierwszy Zakręt',
    'Oddech Odkrywcy','Korytarz Echa','Komora Wypraw','Sekretna Galeria',
    'Przedsionek Odbić','Zapomniana Płyta','Skarbiec Drugiego Strażnika',
    'Boczne Wejście','Krypta Podróżników','Ścieżka Zmierzchu',
    'Sala Długich Cieni','Kręte Schody','Skarbiec Wiecznej Pamięci',
    'Wrota Ostatniej Próby','Tron Trzeciego Strażnika')
NPC_ROLES=('Kronikarz','Zwiadowca','Mistrz Rzemiosł','Strażniczka')
EVENTS=(('kontynent','Przebudzenie Kontynentu',2),
        ('prady','Zanik Prądów',5),
        ('echa','Echo Zapomnianych Imion',8),
        ('migracja','Wielka Migracja',11))
COUNTS=dict(story=10,hunt=20,collect=10,prof=10)
assert len(ROOM_LABELS)==30 and sum(COUNTS.values())==50


def prefix(slug):return PREFIX+'_'+slug


def exits(p,j,previous,following):
    if j<=14:
        doors={'west':previous} if j==1 else {'south':f'{p}_{j-1:02d}'}
        if j<14:doors['north']=f'{p}_{j+1:02d}'
        if j==3:doors['east']=p+'_15'
        if j==10:doors['east']=p+'_23'
        if j==14 and following:doors['east']=following
        return doors
    anchor=15 if j<=22 else 23
    origin=3 if j<=22 else 10
    doors={'west':p+f'_{j-1:02d}' if j>anchor else p+f'_{origin:02d}'}
    if j<(22 if j<=22 else 30):doors['east']=p+f'_{j+1:02d}'
    return doors


def planned_ids():
    result={name:set() for name in ('rooms','mobs','npcs','quests','items','recipes')}
    for slug,*_ in REGIONS:
        p=prefix(slug)
        result['rooms'].update(p+f'_{i:02d}' for i in range(1,31))
        result['mobs'].update(p+f'_mob_{i}' for i in range(1,13))
        result['mobs'].update(p+f'_boss_{i}' for i in range(1,4))
        result['npcs'].update(p+f'_npc_{i}' for i in range(1,5))
        result['items'].update(p+f'_material_{i}' for i in range(1,5))
        result['items'].add(p+'_alloy');result['recipes'].add(p+'_alloy')
        for kind,amount in COUNTS.items():
            result['quests'].update(p+f'_{kind}_{j:02d}' for j in range(1,amount+1))
    for slug,*_ in EVENTS:
        result['mobs'].add('v11000_event_'+slug+'_boss')
        result['items'].add('v11000_event_'+slug+'_seal')
        result['quests'].update('v11000_event_'+slug+f'_quest_{j:02d}' for j in range(1,10))
    result['items'].update('v11000_prof_product_'+str(i) for i in range(1,9))
    for cl,*_ in CLASS_SPECS:
        result['quests'].update('v11000_class_'+cl.casefold().replace(' ','_')+f'_{j:02d}' for j in range(1,6))
    for ra,*_ in RACE_SPECS:
        result['quests'].update('v11000_race_'+ra.casefold().replace(' ','_')+f'_{j:02d}' for j in range(1,4))
    return result


def _quest(p, name, giver, kind, target, needed, low, serial, *,repeat=True,**other):
    row=dict(name=name,giver=giver,kind=kind,needed=needed,
             description=name+'. '+('Pokonaj' if kind=='kill' else 'Zdobądź' if kind=='collect' else 'Wykonaj')+
             ' wymagany cel i wróć do NPC.',
             generator_level=low,reward_stat_progress=low*1300,
             olc_reward_xp=low*1700,olc_reward_class_xp=low*1400,
             olc_reward_soul_xp=low*1200,reward_gold=2000+serial*35,
             reward_mithril=5+serial//120,repeatable=repeat,
             **({'repeat_cooldown':QUEST_REPEAT_COOLDOWN_SECONDS} if repeat else {}),v11000=True)
    row['target_npc' if kind=='talk_npc' else 'target']=target
    row.update(other)
    return row


def _build_quest(p,qid,npc_id,entry,prospective,offer):
    quest=entry;quest['giver']=prospective['npcs'][npc_id]['name']
    if qid in prospective['quests']:raise RuntimeError('v110: zdublowany quest '+qid)
    prospective['quests'][qid]=quest
    offer.setdefault(npc_id,[]).append(qid)


def _extra_quests(prospective,offer):
    """Separate authors/unique names; all targets are physically spawned."""
    from world.quests.classes import rows as class_rows
    from world.quests.races import rows as race_rows
    from world.quests.events import rows as event_rows
    for produce in (class_rows,race_rows,event_rows):
        for nid,qid,quest in produce(REGIONS,prefix,prospective['mobs'],prospective['npcs']):
            _build_quest('',qid,nid,quest,prospective,offer)


def install(rooms,mobs,spawns,npcs,quests,items,recipes,zones,categories,guides,power):
    originals=dict(rooms=rooms,mobs=mobs,npcs=npcs,quests=quests,items=items,recipes=recipes)
    ids=planned_ids()
    source=rooms.get(PARENT)
    if not source or not source.get('v109_horizon'):
        raise RuntimeError('v110: brak połączonej końcowej krainy v109')
    first=prefix(REGIONS[0][0])+'_01'
    if first in rooms:
        if any(not ids[k] <= set(originals[k]) for k in ids) or source.get('exits',{}).get('east')!=first:
            raise RuntimeError('v110: wykryto niepełny wcześniejszy katalog')
        for idx,(slug,*_) in enumerate(REGIONS):
            p=prefix(slug)
            prev=PARENT if idx==0 else prefix(REGIONS[idx-1][0])+'_14'
            nxt=prefix(REGIONS[idx+1][0])+'_01' if idx+1<len(REGIONS) else None
            for j in range(1,31):
                if rooms[p+f'_{j:02d}'].get('exits') != exits(p,j,prev,nxt):
                    raise RuntimeError('v110: zmieniono przejścia w istniejącej krainie')
        return dict(already_installed=True,regions=0,rooms=0,mobs=0,bosses=0,
                    spawns=0,npcs=0,quests=0,items=0,recipes=0,areas=())
    if 'east' in source.get('exits',{}):
        raise RuntimeError('v110: istniejące przejście zajmuje miejsce połączenia')
    if 'soul_shard' not in items:raise RuntimeError('v110: brak historycznej nagrody')
    for kind,planned in ids.items():
        conflicts=planned.intersection(originals[kind])
        if conflicts:raise RuntimeError('v110: kolizja '+kind+': '+min(conflicts))
    new_names={region[1] for region in REGIONS}
    if any(name in zones or name.casefold() in guides or prefix(reg[0]) in categories
           for reg in REGIONS for name in (reg[1],)):
        raise RuntimeError('v110: kolizja indeksu krain')
    if len(new_names)!=12:raise RuntimeError('v110: nieunikalne krainy')
    prospective={key:{} for key in originals}
    new_spawns=[]; new_zones={};new_categories={};new_guides={};new_power={}; areas=[];offer={}
    for idx,(slug,name,story,bosses,enemies,materials) in enumerate(REGIONS):
        p=prefix(slug);low=102001+idx*1000;high=low+999
        previous=PARENT if idx==0 else prefix(REGIONS[idx-1][0])+'_14'
        following=prefix(REGIONS[idx+1][0])+'_01' if idx+1<len(REGIONS) else None
        for j,label in enumerate(ROOM_LABELS,1):
            level=low+999*(j-1)//29
            prospective['rooms'][p+f'_{j:02d}']={
                'name':label+' — '+name,'zone':name,
                'desc':story+' '+label+'. Zalecane poziomy '+str(low)+'–'+str(high)+
                       '. Wejście bez twardej blokady poziomu.',
                'exits':exits(p,j,previous,following),'generator_level':level,
                'recommended_mastery':low,'v11000':True}
        itemids=[]
        for j,item in enumerate(materials,1):
            key=p+f'_material_{j}';itemids.append(key)
            prospective['items'][key]={'name':item,'type':'craft_material','price':None,
                'sell_gold':3000+idx*145+j*85,'desc':'Surowiec: '+name+'.','v11000':True}
        product=p+'_alloy'
        prospective['items'][product]={'name':'Stop — '+name,'type':'craft_material',
            'price':None,'v11000':True}
        prospective['recipes'][product]={'name':'Stop — '+name,'stations':('forge',),
            'desc':'Przetop dwa rodzaje surowców z krainy '+name+' w kuźni.',
            'ingredients':{itemids[0]:2,itemids[1]:2},'output':product,'quantity':1,
            'profession':'Kowalstwo','min_profession_level':low,'generator_level':low,
            'profession_xp':low*4,'tool_xp':low*3,'v11000':True}
        for j,monster in enumerate(enemies,1):
            mid=p+f'_mob_{j}';lvl=low+999*j//15
            prospective['mobs'][mid]={'name':monster,'generator_level':lvl,
                'max_hp':lvl*1500,'damage':lvl*12,'damage_type':'magic' if j%3==0 else 'physical',
                'class_xp_reward':lvl*850,'soul_reward':lvl*680,'stat_reward':lvl*460,
                'silver':lvl*200,'gold':1300+idx*180+j*85,'mithril':8+idx,
                'drops':{itemids[(j-1)%4]:.90,itemids[(j+1)%4]:.35,'soul_shard':.18},
                'quest_target':mid,'rank':'normal','stationary_mob':True,
                'auto_aggro':False,'v11000':True}
            for n in (2+(j-1)%12,15+(j-1)):
                new_spawns.append((p+f'_{n:02d}',mid))
        for j,boss in enumerate(bosses,1):
            mid=p+f'_boss_{j}';lvl=high-300+(j-1)*150
            prospective['mobs'][mid]={'name':boss,'generator_level':lvl,
                'max_hp':lvl*19000*j,'damage':lvl*19*j,
                'damage_type':'magic' if j%2==0 else 'physical',
                'class_xp_reward':lvl*2300,'soul_reward':lvl*1800,
                'stat_reward':lvl*1300,'gold':5600+idx*820+j*460,
                'mithril':24+idx*2+j,'boss':True,'world_boss':False,
                'stationary_mob':True,'auto_aggro':False,'quest_target':mid,
                'leave_corpse':True,'drops':{itemids[(j-1)%4]:1.0,'soul_shard':1.0},
                'v11000':True}
            new_spawns.append((p+f'_{(14,22,30)[j-1]:02d}',mid))
        for j,roomnum in enumerate((2,5,9,25),1):
            nid=p+f'_npc_{j}'
            prospective['npcs'][nid]={'name':NPC_ROLES[j-1]+' '+name,
                'room':p+f'_{roomnum:02d}',
                'dialogue':'Witaj w '+name+'. Wpisz quest list.',
                'specialist_quests':(),'quest_chain':(),
                'v700_story_npc':True,'v10300_era_npc':True,'v10400_era_npc':True,
                'v11000':True}
        from world.quests.regional import produce_regional
        for nid,qid,quest in produce_regional(idx,slug,name,low,p,enemies,bosses,itemids,prospective['npcs']):
            _build_quest(p,qid,nid,quest,prospective,offer)
        new_zones[name]=p;new_categories[p]='Endgame';new_guides[name.casefold()]=p+'_01';new_power[p]=low
        areas.append({'id':p,'name':name,'aliases':(name.casefold(),slug),
          'soul_min':low,'soul_max':high,'mastery_min':low,'mastery_max':high,
          'difficulty':f'era {low}-{high}','guide':name.casefold(),
          'enemies':', '.join(enemies),'description':story+' 30 lokacji i 50 questów.',
          'note':'Solo i drużyna do sześciu osób. Bez rajdów i progów wejścia.'})
    # Four distinct event bosses (12*3 + 4 = 40).
    from world.events.registry import BOSSES
    for slug,title,region_i in EVENTS:
        p=prefix(REGIONS[region_i][0]);mid='v11000_event_'+slug+'_boss'
        spec=BOSSES[slug];lvl=102001+region_i*1000+950
        prospective['items']['v11000_event_'+slug+'_seal']={'name':'Pieczęć: '+title,
            'type':'craft_material','price':None,'desc':'Nagroda za globalne wydarzenie v110.',
            'v11000':True,'v11000_event':slug}
        prospective['mobs'][mid]={
           'name':spec['name'],'generator_level':lvl,
           'max_hp':lvl*34000,'damage':lvl*39,'damage_type':spec['damage_type'],
           'class_xp_reward':lvl*3100,'soul_reward':lvl*2400,
           'stat_reward':lvl*1850,'gold':8000+region_i*600,'mithril':45+region_i,
           'boss':True,'world_boss':False,'stationary_mob':True,
           'auto_aggro':False,'leave_corpse':True,'quest_target':mid,
           'drops':{p+'_material_4':1.0,'soul_shard':1.0},
           'v11000':True,'v11000_event':slug}
        new_spawns.append((p+'_30',mid))
    _extra_quests(prospective,offer)
    from world.teachers_v110 import assign_teachers
    if assign_teachers(prospective['npcs'], prospective['rooms'], prefix) != 8:
        raise RuntimeError('v110: brakuje nauczycieli nowych klas')
    from data.items_v110.professions import products
    prospective['items'].update(products())
    for nid,qids in offer.items():
        npc=prospective['npcs'][nid]
        if not qids or len(qids)!=len(set(qids)):raise RuntimeError('v110: błędne oferty NPC '+nid)
        npc['specialist_quests']=tuple(qids)
        # Quest chain includes only the primary storyline to avoid class/race locks.
        npc['quest_chain']=tuple(q for q in qids if '_story_' in q)
        npc['quest']=qids[0]
    # Graph validation: every edge reversible and every target physically present.
    graph={PARENT:{'east':first}}
    graph.update({rid:room['exits'] for rid,room in prospective['rooms'].items()})
    for rid,doors in graph.items():
        for direction,destination in doors.items():
            if direction not in OPPOSITE or destination not in graph or graph[destination].get(OPPOSITE[direction])!=rid:
                raise RuntimeError('v110: brak powrotu '+rid+'/'+direction)
    all_spawns={mob for room,mob in new_spawns if room in prospective['rooms']}
    if len(set(new_spawns))!=len(new_spawns) or not all_spawns==set(prospective['mobs']):
        raise RuntimeError('v110: brak fizycznego spawnu lub duplikat')
    for qid,q in prospective['quests'].items():
        if (q['kind']=='kill' and q.get('target') not in all_spawns
            or q['kind']=='collect' and q.get('target') not in prospective['items']
            or q['kind']=='talk_npc' and q.get('target_npc') not in prospective['npcs']
            or q['kind']=='profession_action' and q.get('target') not in
                {row[0] for row in PROFESSION_SPECS}|{row[0] for row in OLD_PROFS}):
            raise RuntimeError('v110: nieosiągalny cel zadania '+qid)
        if q.get('requires_quest') and q['requires_quest'] not in prospective['quests']:
            raise RuntimeError('v110: brak poprzedniego zadania '+qid)
    expected=dict(rooms=360,mobs=184,npcs=48,quests=700,items=72,recipes=12)
    sizes={k:len(v) for k,v in prospective.items()}
    if sizes!=expected or len(new_spawns)!=328:
        raise RuntimeError('v110: niezgodne liczby '+str(sizes)+'; spawns='+str(len(new_spawns)))
    # Atomic on validation: only now commit generated content. Historical
    # quest IDs, physical equipment and SQLite are never modified or migrated.
    for kind,catalog in originals.items():catalog.update(prospective[kind])
    source.setdefault('exits',{})['east']=first
    spawns.extend(new_spawns)
    zones.update(new_zones);categories.update(new_categories)
    guides.update(new_guides);power.update(new_power)
    return dict(already_installed=False,regions=12,rooms=360,mobs=184,bosses=40,
                spawns=328,npcs=48,quests=700,items=72,recipes=12,areas=tuple(areas))
