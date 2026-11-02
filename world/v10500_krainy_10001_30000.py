# -*- coding: utf-8 -*-
"""v105: physical regions, NPC offers, 1000 real quest definitions.

Preserves existing IDs and account SQLite, requires actual v104 world topology.
All recommended levels are informational (no hard region gates).
"""
from __future__ import annotations
from world.v10500_region_index import REGIONS
from world.v10400_krainy_5001_10000 import ROOM_PARTS, ENEMY_PARTS
from world.v10300_era_bez_granic import PROFESSION_SPECS


def install(rooms,mobs,spawns,npcs,quests,items,recipes,areas,zone_ids,categories,guides,target_power):
    head='v10500_przesmyk_01'; parent='v10400_tron_14'
    ids={'rooms':set(), 'mobs':set(), 'npcs':set(), 'quests':set(), 'items':set(), 'recipes':set()}
    for slug,*_ in REGIONS:
        p='v10500_'+slug
        ids['rooms'].update(f'{p}_{j:02d}' for j in range(1,15))
        ids['mobs'].update(f'{p}_{kind}_{j}' for kind,n in (('mob',8),('boss',2)) for j in range(1,n+1))
        ids['npcs'].update(f'{p}_npc_{j}' for j in range(1,4))
        ids['quests'].update(f'{p}_{kind}_{j:02d}' for kind,n in (('story',20),('prof',15),('hunt',10),('explore',5)) for j in range(1,n+1))
        ids['items'].update(f'{p}_{kind}' for kind in ('material_1','material_2','material_3','alloy'))
        ids['recipes'].add(p+'_alloy')
    registries={'rooms':rooms,'mobs':mobs,'npcs':npcs,'quests':quests,'items':items,'recipes':recipes}
    if head in rooms:
        if any(not ids[key].issubset(registries[key]) for key in ids):
            raise RuntimeError('v105: niekompletny ponowny import krain')
        return {'regions':0,'quests':0,'reason':'already installed','areas':()}
    if parent not in rooms or 'east' in rooms[parent].get('exits',{}):
        raise RuntimeError('v105: brak wolnego wyjścia z Tronu v104')
    for key, planned in ids.items():
        if planned.intersection(registries[key]):
            raise RuntimeError(f'v105: kolizja katalogu {key}')
    for slug,name,*_ in REGIONS:
        p='v10500_'+slug
        if name in zone_ids or p in categories or name.casefold() in guides:
            raise RuntimeError('v105: kolizja nazwy regionu '+name)
    new_areas=[];previous=parent
    for i,(slug,name,low,high,boss_a,boss_b) in enumerate(REGIONS,1):
        p='v10500_'+slug
        rooms[previous].setdefault('exits',{})['east']=p+'_01'
        for j,part in enumerate(ROOM_PARTS,1):
            rid=f'{p}_{j:02d}'; exits={'west':previous} if j==1 else {'south':f'{p}_{j-1:02d}'}
            if j<14: exits['north']=f'{p}_{j+1:02d}'
            rooms[rid]={'zone':name,'name':f'{part} — {name}',
                        'desc':f'{part}. {name}. Zalecany zakres {low}–{high}; wejście bez blokady. Kierunki są w exits.',
                        'generator_level':low+(high-low)*(j-1)//13,
                        'recommended_mastery':low, 'exits':exits}
        previous=f'{p}_14'
        for j,word in enumerate(('Odłamek','Rdzeń','Pieczęć'),1):
            iid=f'{p}_material_{j}'
            items[iid]={'name':f'{word} {name}','type':'craft_material','price':None,
                        'sell_gold':i*120*j,'desc':f'{word} z {name}; materiał dla ekwipunku v105.'}
        alloy=f'{p}_alloy'
        items[alloy]={'name':f'Stop {name}','type':'craft_material','price':None,'desc':f'Stop z {name}.'}
        recipes[alloy]={'name':f'Stop {name}','stations':('forge',),
                        'ingredients':{f'{p}_material_1':2,f'{p}_material_2':2},
                        'output':alloy,'quantity':1,'profession':'Kowalstwo',
                        'generator_level':800,'min_profession_level':low,'profession_xp':low*4,
                        'tool_xp':low*3,'desc':'Regionalny stop.'}
        for j,kind in enumerate(ENEMY_PARTS,1):
            mid=f'{p}_mob_{j}';lvl=low+(high-low)*j//10
            mobs[mid]={'name':f'{kind} {name}','generator_level':lvl,
                       'max_hp':300000+lvl*1250,'damage':5000+lvl*11,
                       'damage_type':'magic' if j%2==0 else 'physical',
                       'class_xp_reward':lvl*600,'soul_reward':lvl*500,
                       'stat_reward':lvl*400,'gold':400+i*120+j*30,'mithril':3+i,
                       'drops':{f'{p}_material_1':0.9,f'{p}_material_2':0.55,'soul_shard':0.2},
                       'quest_target':mid}
            for roomno in (2+(j-1)%8,3+(j-1)%8):spawns.append((f'{p}_{roomno:02d}',mid))
        for j,(boss,roomno) in enumerate(((boss_a,10),(boss_b,14)),1):
            mid=f'{p}_boss_{j}';lvl=low if j==1 else high
            mobs[mid]={'name':boss,'boss':True,'world_boss':True,'generator_level':lvl,
                       'max_hp':(5_000_000+lvl*20_000)*(j+1),
                       'damage':(3000+lvl*15)*(j+1),'damage_type':'magic',
                       'class_xp_reward':lvl*2000,'soul_reward':lvl*1500,
                       'stat_reward':lvl*1000,'gold':1800+i*600,'mithril':12+i*2,
                       'drops':{f'{p}_material_3':1.,'soul_shard':1.},
                       'quest_target':mid,'leave_corpse':True}
            spawns.append((f'{p}_{roomno:02d}',mid))
        by_npc=[[],[],[]]
        for j in range(1,51):
            if j<=20:
                kind='story';part=j;target=f'{p}_mob_{(j-1)%8+1}' if j%5 else f'{p}_boss_{1+(j//10)%2}'
                nature='kill';needed=2+j%3 if j%5 else 1;who=0 if j<=8 else 1 if j<=14 else 2
            elif j<=35:
                kind='prof';part=j-20;who=2
                profession,tool,activity=PROFESSION_SPECS[(j-21)%len(PROFESSION_SPECS)]
                nature='profession_action';target=profession;needed=8+i
            elif j<=45:
                kind='hunt';part=j-35;who=1
                nature='kill';target=f'{p}_mob_{(part-1)%8+1}' if part<=8 else f'{p}_boss_{part-8}'
                needed=3 if part<=8 else 1
            else:
                kind='explore';part=j-45;who=0;nature='explore_frontier';target='any';needed=part+2
            qid=f'{p}_{kind}_{part:02d}';giver=(f'Kronikarz {name}',f'Mistrz {name}',f'Strażniczka {name}')[who]
            namepart={'story':'Kronika','prof':'Profesja','hunt':'Polowanie','explore':'Odkrycia'}[kind]
            quest={'name':f'{name}: {namepart} {part}', 'giver':giver,
                   'kind':nature,'target':target,'needed':needed,
                   'description':(f'Wykonaj {needed} działań profesji {target} i wróć do {giver}.' if kind=='prof' else
                                  f'Zbadaj {needed} nowych sektorów proceduralnych rubieży, wróć do {giver}.' if kind=='explore' else
                                  f'Pokonaj {needed} × {mobs[target]["name"]} w krainie {name} i wróć do {giver}.'),
                   'generator_level':low, 'reward_stat_progress':low*1300,
                   'olc_reward_xp':low*1500,'olc_reward_class_xp':low*1400,
                   'olc_reward_soul_xp':low*1200,'reward_gold':400+i*450+j*20,
                   'reward_mithril':i+1,'reward_items':{f'{p}_material_1':1}}
            if kind=='story' and part>1:quest['requires_quest']=f'{p}_story_{part-1:02d}'
            if kind=='prof':
                quest.update({'required_profession':profession,'specialist_tool_type':tool,
                              'reward_profession':profession,'reward_profession_xp':low*2000,
                              'reward_tool_type':tool,'reward_tool_xp':low*1800})
            quests[qid]=quest;by_npc[who].append(qid)
        for j,(roomno,person) in enumerate(((5,f'Kronikarz {name}'),(8,f'Mistrz {name}'),(13,f'Strażniczka {name}'))):
            offered=tuple(by_npc[j]);npcs[f'{p}_npc_{j+1}']={
                'name':person,'room':f'{p}_{roomno:02d}',
                'dialogue':f'{person}: {name}. Wybierz zadania komendą quest list.',
                'specialist_quests':offered,'quest_chain':offered,'quest':offered[0],
                'v700_story_npc':True,'v10300_era_npc':True,'v10400_era_npc':True}
        zone_ids[name]=p;categories[p]='Endgame';guides[name.casefold()]=p+'_01'
        target_power[p]=low
        new_areas.append({'id':p,'name':name,'aliases':(name.casefold(),slug),
                         'soul_min':low,'soul_max':high,'mastery_min':low,'mastery_max':high,
                         'difficulty':f'era {low}-{high}', 'guide':name.casefold(),
                         'enemies':', '.join(mobs[f'{p}_mob_{j}']['name'] for j in range(1,9)),
                         'description':f'{name}: 14 komnat, 3 NPC, 50 zadań, 8 mobów i 2 bossów.',
                         'note':f'Zakres {low}–{high} zalecany, wejście nie wymaga poziomu.'})
    return {'regions':len(REGIONS),'rooms':len(ids['rooms']),'mobs':len(ids['mobs']),
            'npcs':len(ids['npcs']),'quests':len(ids['quests']),
            'items':len(ids['items']),'recipes':len(ids['recipes']),
            'areas':tuple(new_areas)}
