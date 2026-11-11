# -*- coding: utf-8 -*-
"""v111 DRAFT: twelve separate XP zones, each with hunt quests and a boss.
Only in-memory registry expansion; never migrates or writes player data.
"""
from __future__ import annotations
from systems.holiday.calendar import MONTHS

PREFIX = 'v11100_holiday'


def install(rooms,mobs,spawns,npcs,quests,items,recipes,zones,categories,guides,power):
    from world.v11000_realms import prefix as old_prefix
    from world.v11000_realm_index import REGIONS
    from config.balance import QUEST_REPEAT_COOLDOWN_SECONDS
    anchor=old_prefix(REGIONS[-1][0])+'_14'
    first=PREFIX+'_01_01'
    if anchor not in rooms:raise RuntimeError('v111: brak wymaganej bramy v110')
    if first in rooms:raise RuntimeError('v111: ponowna instalacja katalogu')
    if rooms[anchor].get('exits',{}).get('east'):
        raise RuntimeError('v111: wyjście v110 jest już zajęte')
    planned={'rooms':{},'mobs':{},'npcs':{},'quests':{},'items':{}}
    added_spawns=[];areas=[];new_zones={};new_cats={};new_guides={};new_power={}
    for idx,(zone,festival,boss_name) in enumerate(MONTHS,1):
        p=f'{PREFIX}_{idx:02d}';low=100+idx*350;high=low+499
        prev=anchor if idx==1 else f'{PREFIX}_{idx-1:02d}_08'
        nxt=f'{PREFIX}_{idx+1:02d}_01' if idx<12 else None
        for step in range(1,9):
            rid=f'{p}_{step:02d}';exits={}
            if step==1:exits['west']=prev
            else:exits['south']=f'{p}_{step-1:02d}'
            if step<8:exits['north']=f'{p}_{step+1:02d}'
            if step==8 and nxt:exits['east']=nxt
            planned['rooms'][rid]={'name':f'{zone} — sektor {step}',
                'zone':zone,'desc':f'{festival}. Świąteczne expowisko dla 1–6 graczy; '
                                     'wejście bez wymaganego poziomu.',
                'exits':exits,'generator_level':low+step*50,'recommended_mastery':low,
                'v11100':True}
        for n in range(1,5):
            mid=f'{p}_mob_{n}';level=low+n*70
            planned['mobs'][mid]={'name':f'{festival} — przeciwnik {n}',
                'generator_level':level,'max_hp':level*250,'damage':level*9,
                'damage_type':'magic' if n%2==0 else 'physical',
                'class_xp_reward':level*280,'soul_reward':level*240,
                'stat_reward':level*120,'gold':150+n*40,
                'drops':{'soul_shard':.12},'quest_target':mid,
                'rank':'normal','stationary_mob':True,'auto_aggro':False,'v11100':True}
            for roomnum in (n+1,n+3):added_spawns.append((f'{p}_{roomnum:02d}',mid))
        souvenir=f'{p}_souvenir'
        planned['items'][souvenir]={'name':'Pamiątka — '+festival,
            'type':'craft_material','price':None,
            'desc':'Trofeum sezonowego expowiska '+zone+'.','v11100':True}
        boss=f'{p}_boss';level=high
        planned['mobs'][boss]={'name':boss_name,'generator_level':level,
            'max_hp':level*5500,'damage':level*17,'damage_type':'magic',
            'class_xp_reward':level*900,'soul_reward':level*750,
            'stat_reward':level*400,'gold':2400,'mithril':4,
            'drops':{'soul_shard':1.0,souvenir:1.0},'quest_target':boss,
            'boss':True,'world_boss':False,'stationary_mob':True,
            'auto_aggro':False,'leave_corpse':True,'v11100':True}
        added_spawns.append((f'{p}_08',boss))
        npc=f'{p}_npc';planned['npcs'][npc]={'name':'Opiekun '+zone,
            'room':f'{p}_01','dialogue':f'Witaj w {festival}.',
            'specialist_quests':(f'{p}_quest_{n}' for n in (1,2,3)),
            'v700_story_npc':True,'v10300_era_npc':True,'v11100':True}
        qids=[]
        for q in range(1,4):
            target=f'{p}_mob_{q}' if q<3 else boss
            qid=f'{p}_quest_{q}';qids.append(qid)
            planned['quests'][qid]={'name':f'{festival} — próba {q}',
                'giver':planned['npcs'][npc]['name'],'kind':'kill',
                'target':target,'needed':(5 if q<3 else 1),
                'description':f'Pokonaj cel wydarzenia {festival} i wróć do opiekuna.',
                'generator_level':low,'reward_stat_progress':low*120,
                'olc_reward_xp':low*450,'olc_reward_class_xp':low*400,
                'olc_reward_soul_xp':low*350,'reward_gold':500+q*150,
                'repeatable':True,'repeat_cooldown':QUEST_REPEAT_COOLDOWN_SECONDS,
                'v11100':True}
        planned['npcs'][npc]['specialist_quests']=tuple(qids)
        planned['npcs'][npc]['quest_chain']=()
        planned['npcs'][npc]['quest']=qids[0]
        new_zones[zone]=p;new_cats[p]='Sezonowe expowiska';new_guides[zone.casefold()]=f'{p}_01';new_power[p]=low
        areas.append({'id':p,'name':zone,'aliases':(zone.casefold(),f'swieto{idx}'),
            'soul_min':low,'soul_max':high,'mastery_min':low,'mastery_max':high,
            'difficulty':f'poziom {low}-{high}','guide':zone.casefold(),
            'enemies':f'4 rodzaje przeciwników i {boss_name}',
            'description':f'{festival}: 8 lokacji, 3 questy, 1 boss.',
            'note':'Obszar dostępny cały rok; święto wyróżniane w kalendarzu.'})
    for key,catalog in (('rooms',rooms),('mobs',mobs),('npcs',npcs),('quests',quests),('items',items)):
        collision=set(planned[key])&set(catalog)
        if collision:raise RuntimeError(f'v111: kolizja {key}: {min(collision)}')
    if any(x in zones or x.casefold() in guides for x,_,_ in MONTHS):
        raise RuntimeError('v111: kolizja nazwy expowiska')
    # All-or-nothing catalog validation; every edge has a return path.
    graph={anchor:{**rooms[anchor].get('exits',{}),'east':first}}
    graph.update({key:row['exits'] for key,row in planned['rooms'].items()})
    opposite={'north':'south','south':'north','east':'west','west':'east'}
    for origin,doors in graph.items():
        for direction,dest in doors.items():
            if origin==anchor and direction!='east':continue
            if dest not in graph or graph[dest].get(opposite[direction])!=origin:
                raise RuntimeError(f'v111: brak przejścia powrotnego {origin}/{direction}')
    if not set(m for _,m in added_spawns)==set(planned['mobs']):
        raise RuntimeError('v111: brak spawnu')
    if not all(q['target'] in planned['mobs'] for q in planned['quests'].values()):
        raise RuntimeError('v111: quest bez celu')
    for key,catalog in (('rooms',rooms),('mobs',mobs),('npcs',npcs),('quests',quests),('items',items)):
        catalog.update(planned[key])
    rooms[anchor].setdefault('exits',{})['east']=first
    spawns.extend(added_spawns);zones.update(new_zones);categories.update(new_cats)
    guides.update(new_guides);power.update(new_power)
    return {'regions':12,'rooms':96,'mobs':60,'quests':36,'items':12,
            'npcs':12,'spawns':len(added_spawns),'areas':tuple(areas)}
