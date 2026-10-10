# -*- coding: utf-8 -*-
"""Authored sky expansion for Soulbound 1.70.0; additive content only."""
from __future__ import annotations
from data import catalog_mutations as cm
from systems.forgotten_world_v1500 import PROFESSIONS

SKY_REGIONS=(
 ('burza','Wyspy Gromowych Chmur','lightning',590,('Brama Gromowładcy','Arcygryf Błyskawic','Smok Burzowego Tronu')),
 ('zorza','Ogrody Wiecznej Zorzy','holy',650,('Strażnik Słonecznych Korzeni','Feniks Niebiańskiej Straży','Serafin Korony Zorzy')),
 ('otchlan','Archipelag Czarnej Otchłani','dark',720,('Prorok Cienia','Żniwiarz Gwiezdnego Pyłu','Lewiatan Niebios')),
)


def put(label, catalog, key, value):
    if key in catalog: raise RuntimeError('v1.70.0 duplicate '+str(key))
    cm.catalog_assign(value,label,catalog,(key,))


def install_sky_era_v1700(rooms,npcs,shops,mobs,spawns,quests,items,shop_sellers):
    from data.crafting_recipes import CRAFT_RECIPES
    anchor='v1600_road_2'
    assert anchor in rooms and 'up' not in rooms[anchor]['exits'], 'No free sky portal exit'
    cm.catalog_assign('v1700_sky_harbor','ROOMS',rooms,(anchor,'exits','up'))
    put('ROOMS',rooms,'v1700_sky_harbor',{
       'name':'Przystań Sterowców Czterech Wiatrów','zone':'Podniebne Królestwa',
       'desc':'Zabezpieczone sterowce łączą trzy krainy chmur. Brak losowych pułapek; dostępne solo i w drużynie.',
       'exits':{'down':anchor,'north':'v1700_burza_0','east':'v1700_zorza_0','south':'v1700_otchlan_0','west':'v1700_city_gate'}})
    put('ROOMS',rooms,'v1700_city_gate',{'name':'Brama Osad Założycieli','zone':'Miasta Graczy',
        'desc':'Wspólna przystań założycieli. Rozwój osobistego miasta: miasto zaloz; miasto buduj; miasto status.',
        'exits':{'east':'v1700_sky_harbor','west':'v1700_city_market'}})
    put('ROOMS',rooms,'v1700_city_market',{'name':'Targ Osad Założycieli','zone':'Miasta Graczy',
        'desc':'Giełda materiałów i rzemieślniczych projektów arcymistrzów; każde konto zarządza własną osadą.',
        'exits':{'east':'v1700_city_gate'}})
    for key,name,price in [('v1700_common_tooth','Zwykły ząb',1500),('v1700_dragon_tooth','Smoczy ząb',350000),
                           ('v1700_soul_stone','Czerwony Kamień Duszy',200000),('v1700_nature_seed','Nasiono Pradawnego Gaju',120000),('v1702_pinecone','Szyszka Pradawnego Gaju',50000),
                           ('v1700_bond_token','Pieczęć Chowańca',120000)]:
        put('ITEMS',items,key,{'name':name,'type':'material','rarity':'rare','price':price,
                             'desc':'Szyszka używana do przywoływania drzew za manę.' if key=='v1702_pinecone' else 'Materiał przywołań Soulbound.'})
    # Nine colored grades, keeping v1.70.0 soulstone ID as red for old characters.
    from systems.soulstones_v1701 import SOULSTONE_TIERS
    for rank, (key,name,item_id,bonus,threshold) in enumerate(SOULSTONE_TIERS[1:],start=1):
        put('ITEMS',items,item_id,{'name':name,'type':'material',
            'rarity':'legendary' if rank>=5 else 'rare',
            'price':int(200000*(3**rank)),'desc':
            f'Kamień Duszy poziomu {rank+1}/9. Ulepsza szkielet wojownika lub maga; rezonans x{bonus:.2f}.'})
    for n,(slug,region,element,level,bosses) in enumerate(SKY_REGIONS):
        resource=f'v1700_{slug}_essence'
        put('ITEMS',items,resource,{'name':'Esencja '+region,'type':'material','rarity':'legendary',
                'price':2900000+level*3600,'desc':'Surowiec rzemiosła 6.0 z podniebnych krain.'})
        start={'burza':'south','zorza':'west','otchlan':'north'}[slug]
        back={'burza':'north','zorza':'east','otchlan':'south'}[slug]
        forward={'burza':'north','zorza':'east','otchlan':'south'}[slug]
        reverse={'burza':'south','zorza':'west','otchlan':'north'}[slug]
        for i in range(18):
            exits={}
            if i: exits[reverse]=f'v1700_{slug}_{i-1}'
            if i<17: exits[forward]=f'v1700_{slug}_{i+1}'
            if not i: exits[start]='v1700_sky_harbor'
            if i==17: exits[forward]=f'v1700_{slug}_throne'
            landmarks=('Podniebny Most','Galeria Wiatrów','Strażnica Sokołów','Niebiańska Polana','Stara Zbrojownia','Zatoka Chmur')
            put('ROOMS',rooms,f'v1700_{slug}_{i}',{
              'name':f'{landmarks[i%len(landmarks)]} — {region}, odcinek {i+1}',
              'zone':region,'desc':f'Ręcznie opisany szlak do władców {region}. Kierunki są jawne. '
                 'Powietrzne patrole, relikty, warsztaty i widoczne zejścia.',
              'exits':exits,'recommended_mastery':min(800,level+i*7),'sky_v1700':True})
        put('ROOMS',rooms,f'v1700_{slug}_throne',{'name':'Tron '+region,'zone':region,
             'desc':'Arena superbossa; nie ma pułapek. Wojna Legend rozgrywa się w normalnym systemie walki.',
             'exits':{reverse:f'v1700_{slug}_17'},'recommended_mastery':min(800,level+170)})
        for j,label in enumerate(('Podniebny Zwiadowca','Rycerz Podmuchów','Smok Szlaku','Tajemniczy Bestiariusz')):
            mid=f'v1700_{slug}_patrol_{j}'
            drop={'v1700_common_tooth':.26,'v1700_bond_token':.11,resource:.19}
            if j==2: drop={'v1700_dragon_tooth':.55,'v1700_soul_stone':.15, 'v1701_soul_green':.10, resource:.27}
            put('MOB_TEMPLATES',mobs,mid,{'name':f'{label} {region}',
                'max_hp':(level+j*25)*910,'damage':(level+j*25)*49,
                'damage_type':'magic' if j%2 else 'physical','attack_elements_v11339':(element,),
                'generator_level':min(800,level+j*25),'rank':'elite',
                'stat_reward':level*180,'class_xp_reward':level*2350,'soul_reward':level*780,
                'silver':level*490,'gold':0,'mithril':0,'drops':drop,
                'quest_target':mid,'stationary_mob':True,'auto_aggro':False})
            for r in (1+j*4, 2+j*4, 3+j*4):spawns.append((f'v1700_{slug}_{r}',mid))
        for j,title in enumerate(bosses):
            mid=f'v1700_{slug}_boss_{j}'
            strength=level+70*j
            is_super=j==2
            put('MOB_TEMPLATES',mobs,mid,{'name':title,'max_hp':strength*(6500 if is_super else 3000),
                'damage':strength*(140 if is_super else 78),'damage_type':'magic',
                'attack_elements_v11339':(element,'dark' if j==1 else 'fire'),
                'generator_level':min(800,strength),'boss':True,'world_boss':is_super,
                'rank':'world_boss' if is_super else 'boss',
                'boss_mechanic':'elemental_overdrive','boss_mechanic_text':'Zmienne fazy i żywioły Wojny Legend.',
                'stat_reward':strength*460,'class_xp_reward':strength*6400,
                'soul_reward':strength*3000,'silver':strength*2900,'gold':0,'mithril':0,
                'drops':{resource:1.0,'v1700_dragon_tooth':1.0,('v1701_soul_clear' if level<670 else 'v1701_soul_white'):1.0,
                         'soul_shard':1.0},'quest_target':mid,
                'stationary_mob':True,'auto_aggro':False})
            spawns.append((f'v1700_{slug}_throne' if is_super else f'v1700_{slug}_{7+j*6}',mid))
        hunter=f'Strażniczka Wojny Legend {region}'
        quest_ids=[]
        for j,title in enumerate(bosses):
            qid=f'v1700_hunt_{slug}_{j}'
            put('QUESTS',quests,qid,{'name':f'Wojna Legend: {title}',
                'giver':hunter,'kind':'kill','target':f'v1700_{slug}_boss_{j}',
                'needed':1,'description':f'Pokonaj {title} i zdobądź nagrodę. Solo i drużyna.',
                'reward_silver':(level+j*70)*4800,'reward_gold':0,'reward_mithril':0,
                'reward_items':{resource:2+j},'repeatable':True,'repeat_cooldown':7200})
            quest_ids.append(qid)
        put('NPCS',npcs,f'v1700_hunter_{slug}',{'name':hunter,'room':f'v1700_{slug}_0',
            'dialogue':'Trzy wielkie polowania. Wpisz quest list.','quest_chain':tuple(quest_ids)})
    # Each of 14 professions gets 2 permanent new authentic action quests.
    for k,(name,tool,action) in enumerate(PROFESSIONS):
        slug,region,*_=SKY_REGIONS[k%3]
        giver=f'Arcymistrz {name} z Niebios'
        ids=[]
        for stage in (1,2):
            qid=f'v1700_prof_{k}_{stage}'; count=25*stage
            put('QUESTS',quests,qid,{
                'name':f'Rzemiosło 6.0: {name}, próba {stage}',
                'giver':giver,'kind':'profession_action','target':name,'needed':count,
                'description':f'Wykonaj {count} nowych czynności {name} po przyjęciu. {action}.',
                'required_profession':name,'specialist_tool_type':tool,
                'reward_profession':name,'reward_profession_xp':50000*stage,
                'reward_tool_type':tool,'reward_tool_xp':25000*stage,
                'reward_silver':2500000*stage,'reward_gold':0,'reward_mithril':0,
                'repeatable':True,'repeat_cooldown':7200})
            ids.append(qid)
        put('NPCS',npcs,f'v1700_crafter_{k}',{'name':giver,'room':f'v1700_{slug}_{k%6}',
            'dialogue':f'Nowe realne zadania {name}, odnowienie co dwie godziny.',
            'strict_profession_quests':name,'specialist_quests':tuple(ids)})
    # Authored forge gear, no numbered generator overlays; crafts use old strict inventory system.
    names=('Korona Podniebnego Władcy','Zbroja Wichrowego Strażnika','Rękawice Burzowego Łowcy',
           'Buty Szkarłatnego Feniksa','Płaszcz Północnej Zorzy','Amulet Otchłani')
    slots=('head','body','hands','feet','cloak','necklace')
    for i,(name,slot) in enumerate(zip(names,slots)):
        slug,region,*_=SKY_REGIONS[i%3]
        resource=f'v1700_{slug}_essence'; iid=f'v1700_relic_{i}'
        put('ITEMS',items,iid,{'name':name,'type':'armor','slot':slot,'rarity':'legendary',
            'defense':280+i*47,'stats':{'constitution':520+i*100,'strength':450+i*80,
               'dexterity':450+i*80,'intelligence':450+i*80,'willpower':450+i*80},
            'properties':{'all_damage_pct':5+i,'max_hp_pct':7+i},'price':None,
            'desc':f'Autorskie arcydzieło rzemiosła z krainy {region}. Można mieszać zestawy.'})
        put('CRAFT_RECIPES',CRAFT_RECIPES,iid,{'name':name,'stations':('forge',),
            'ingredients':{resource:4+i,'eternium_ingot':3+i,'v12812_legendary_seal':2},
            'output':iid,'quantity':1,'min_profession_level':350+i*45,
            'profession_xp':26000+i*8000,'tool_xp':10000+i*2500,
            'desc':'Rzemiosło 6.0: realne wymagania i materiały, bez sztucznego generatora.'})
    return {'sky_rooms':60,'sky_bosses':9,'profession_quests':28,'craft_recipes':6,
            'crafting_professions':len(PROFESSIONS)}
