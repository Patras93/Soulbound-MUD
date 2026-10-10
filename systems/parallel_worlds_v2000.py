# -*- coding: utf-8 -*-
"""v2.00.0: authored parallel worlds, ocean islands, real PvE arenas.

Only additive authored IDs. Old room graph and player saves remain untouched.
All entry and return routes are reciprocal and have text labels for NVDA.
"""
from __future__ import annotations
from data import catalog_mutations as cm

REALMS = (
    ('sny', 'Kraina Snów', 'arcane', 360,
     ('Próg Śnienia','Aleja Srebrnych Zegarów','Jezioro Odbić','Krużganek Szeptów','Most Bez Cienia','Plac Zagubionych Imion','Ogród Motyli','Korytarz Luster','Biblioteka Snów','Wieża Północy','Komnata Przewidzeń','Taras Mgły','Studnia Wspomnień','Krypta Srebrnych Run','Sala Zasłon','Pałac Uśpionych','Schody Przebudzenia','Tron Tkaczki Snów'),
     ('Lustrzany Wilk','Srebrny Tkacz','Strażnik Zegarów','Mim Zaginionego Dworu','Duch Wspomnień','Pająk Sennych Nici','Rycerz Iluzji','Ćma Prorocza','Koszmarny Łowca','Zegarmistrz Zmierzchu'),'Oneira, Tkaczka Koszmarów'),
    ('smoki', 'Królestwo Smoków', 'fire', 500,
     ('Smocza Przełęcz','Czerwony Kanion','Pieczara Srebrnych Łusek','Most Smoczego Oddechu','Plac Smoczych Heraldów','Wylęgarnia Ognia','Stary Wulkan','Studnia Wyroczni','Strażnica Szkarłatu','Skalne Gniazdo','Kryształowe Żebra','Kuźnia Smoczych Łez','Wrota Arcykróla','Sala Smoków Burzowych','Most Czterech Skrzydeł','Galeria Ancjentów','Próg Pieczęci','Tron Pradawnego Smoka'),
     ('Młody Smok Rubinowy','Smoczy Łucznik','Strażnik Wyklucia','Jaszczur Magmowy','Ognisty Drakonid','Żelaznołuski Smok','Strażnik Łusek','Wyrocznia Burz','Smok Zepsutej Korony','Smoczy Czempion'),'Valdrath, Król Pierwszego Płomienia'),
    ('duchy', 'Świat Duchów', 'dark', 610,
     ('Bramy Ciszy','Cmentarz Świec','Aleja Dusz','Prom Widmowy','Dom Żałobników','Krypta Przymierza','Krąg Echa','Kanał Zapomnienia','Biblioteka Pożegnań','Wzgórze Strażników','Most Wspomnień','Kaplica Widm','Komnata Żalu','Kamienne Tablice','Dziedziniec Przodków','Sala Zmierzchu','Wrota Ukojenia','Tron Strażniczki Dusz'),
     ('Zagubiona Dusza','Strażnik Przeprawy','Widmowy Mnich','Szept Nieboszczyka','Cmentarny Opiekun','Duch Kamiennego Króla','Rycerz Żałoby','Krzyk Starej Kaplicy','Strażnik Pieczęci','Wędrowny Żniwiarz'),'Morvessa, Strażniczka Granicy'),
    ('pustka', 'Pustka', 'void', 740,
     ('Próg Niebytu','Tunel Ciemnych Gwiazd','Puste Obserwatorium','Brama Bez Światła','Pęknięta Komnata','Most Końca Czasu','Sala Wygasłych Słońc','Wąwóz Pustych Głosów','Złamana Orbita','Świątynia Ciszy','Pajęczyna Otchłani','Krużganek Zapomnienia','Wrota Nieskończoności','Galeria Nieważkości','Czarny Rezonator','Pałac Nocy','Próg Końca','Tron Władcy Pustki'),
     ('Sługa Niebytu','Czarnogwiezdny Wąż','Golem Pustych Serc','Strażnik Pęknięcia','Łowca Światła','Szept Otchłani','Widmo Czarnej Orbity','Wygnany Mag','Prorok Nieważkości','Egzekutor Końca'),'Xerathun, Władca Pustki'),
)
ISLANDS = (
    ('perly','Archipelag Perłowych Sztormów','water',390,
     ('Pomost Żeglarzy','Plaża Bursztynowa','Koralowe Przejście','Latarnia Północy','Zatopiony Targ','Płytka Laguna','Ruiny Kapitana','Gniazdo Królowej Fal'),
     ('Koralowy Strażnik','Korsarz Perłowej Burzy','Syrena Zaginionych Łodzi','Golem Koralowy','Wąż Błękitnej Laguny'),'Thalira, Królowa Perłowej Burzy'),
    ('otchlan','Archipelag Czarnej Głębi','dark',570,
     ('Ciemna Przystań','Most Wraków','Brzeg Milczących Żagli','Grota Pływów','Podwodna Świątynia','Komnata Czarnych Pereł','Skarbiec Rozbitków','Tron Głębin'),
     ('Wodny Cień','Piracki Widmowy Kapitan','Głębinowy Skorpion','Morświn Otchłani','Strażnik Czarnej Rafy'),'Uldra, Matka Głębin'),
    ('burze','Archipelag Błyskawicznych Wysp','lightning',690,
     ('Port Sztormowy','Pole Piorunów','Wąski Falochron','Wyspa Milczących Masztów','Wieża Burz','Świątynia Gromu','Most Rozbłysków','Ołtarz Władcy Burz'),
     ('Sztormowy Korsarz','Rażąca Meduza','Żywiołak Morskiej Burzy','Pancerna Ośmiornica','Wicher z Zatoki'),'Azrakon, Władca Błyskawic'),
)
ARENAS = (
    ('zelazna','Próba Żelaznego Serca',280,'Żelazny Behemot'),
    ('zywiolow','Próba Czterech Żywiołów',430,'Arcymistrz Czterech Żywiołów'),
    ('dusz','Próba Dusz Pradawnych',610,'Pradawny Sędzia Dusz'),
    ('legend','Próba Żywej Legendy',760,'Egzekutor Wiecznej Legendy'),
)


def _add(typ, table, key, value):
    if key in table:
        raise ValueError('Duplicate authored v2.00.0 ID: '+key)
    cm.catalog_assign(value,typ,table,(key,))


def install_parallel_worlds_v2000(rooms,npcs,shops,mobs,spawns,quests,items,shop_sellers):
    portal='v1900_dim_hub'
    if portal not in rooms or 'up' in rooms[portal].get('exits',{}):
        raise ValueError('v2.00.0 requires v1.90 dimension hub and a free up exit')
    cm.catalog_assign('v2000_nexus','ROOMS',rooms,(portal,'exits','up'))
    _add('ROOMS',rooms,'v2000_nexus',{
        'name':'Węzeł Równoległych Światów','zone':'Węzeł Wymiarów',
        'desc':'Cztery opisane portale: sny na północy, smoki na wschodzie, duchy na południu, pustka na zachodzie. W dół powrót do Wymiarów Chaosu; w górę nowe porty Oceanu 5.0.',
        'exits':{'down':portal,'north':'v2000_sny_0','east':'v2000_smoki_0','south':'v2000_duchy_0','west':'v2000_pustka_0','up':'v2000_ocean_hub'}})
    counter=1; boss_ids=[]
    opposite={'north':'south','east':'west','south':'north','west':'east'}
    for k,(slug,zone,element,level,names,enemies,boss) in enumerate(REALMS):
        entrance=('north','east','south','west')[k]
        for i,label in enumerate(names):
            exits={'west':f'v2000_{slug}_{i-1}'} if i else {opposite[entrance]:'v2000_nexus'}
            if slug=='pustka' and i==0:
                exits['south']=f'v2000_{slug}_1'
            elif slug=='pustka' and i==1:
                exits.pop('west',None)
                exits['north']=f'v2000_{slug}_0'
            if i<len(names)-1 and not (slug=='pustka' and i==0):exits['east']=f'v2000_{slug}_{i+1}'
            _add('ROOMS',rooms,f'v2000_{slug}_{i}',{
                'name':f'{label} — {zone}','zone':zone,
                'generator_level':min(800,level+i*7),
                'recommended_mastery':min(800,level+i*7),
                'desc':f'{label}. {zone}. Korytarz {i+1} z {len(names)}. Przejścia są dwukierunkowe. Wszelkie wyzwania są walkami PvE, bez pułapek.',
                'exits':exits,'v2000_realm':slug})
            counter+=1
        for j,name in enumerate(enemies):
            mid=f'v2000_{slug}_mob_{j}'
            power=min(800,level+j*12)
            _add('MOB_TEMPLATES',mobs,mid,{
                'name':name,'max_hp':power*(520+j*85),'damage':power*(32+j*4),
                'generator_level':power,'damage_type':'magic' if j%2 else 'physical',
                'attack_elements_v11339':(element,), 'rank':'elite' if j>=7 else 'normal',
                'fame_target':True,'stat_reward':power*245,'class_xp_reward':power*3100,
                'soul_reward':power*1200,'silver':power*650,'gold':0,'mithril':0,
                'drops':{'soul_shard':.3},'quest_target':mid,'stationary_mob':True,'auto_aggro':False})
            spawns.append((f'v2000_{slug}_{1+(j%8)*2}',mid))
        bid=f'v2000_{slug}_boss';boss_ids.append(bid)
        power=min(800,level+130)
        _add('MOB_TEMPLATES',mobs,bid,{
            'name':boss,'max_hp':power*8900,'damage':power*160,
            'generator_level':power,'rank':'world_boss','boss':True,'world_boss':True,
            'v1900_ancient_god':True,'boss_mechanic':'elemental_overdrive','damage_type':'magic',
            'attack_elements_v11339':(element,), 'fame_target':True,
            'stat_reward':power*660,'class_xp_reward':power*9400,
            'soul_reward':power*4200,'silver':power*5200,'gold':0,'mithril':0,
            'drops':{'soul_shard':1.0},'quest_target':bid,'stationary_mob':True,'auto_aggro':False})
        spawns.append((f'v2000_{slug}_17',bid))
        for j,mid in enumerate((f'v2000_{slug}_mob_8',f'v2000_{slug}_mob_9',bid)):
            _add('QUESTS',quests,f'v2000_{slug}_quest_{j}',{
                'name':f'Kronika {zone}: {mobs[mid]["name"]}',
                'giver':f'Kronikarz {zone}', 'kind':'kill','target':mid,'needed':1,
                'description':f'Pokonaj {mobs[mid]["name"]} w krainie {zone}.',
                'reward_silver':power*(1400+j*800),'reward_gold':0,'reward_mithril':0,
                'reward_items':{'soul_shard':j+1},'repeatable':True,'repeat_cooldown':7200})
        _add('NPCS',npcs,f'v2000_{slug}_chronicler',{
            'name':f'Kronikarz {zone}','room':f'v2000_{slug}_0',
            'dialogue':f'{zone} skrywa dziesięć gatunków Fame i pradawnego władcę.',
            'quest_chain':tuple(f'v2000_{slug}_quest_{j}' for j in range(3))})
    # Ocean islands are real traversable areas, reached through an openly labelled ship route.
    _add('ROOMS',rooms,'v2000_ocean_hub',{
        'name':'Port Nieznanych Mórz','zone':'Ocean 5.0 — Port',
        'desc':'Floty Ocean 4.0 pozostają aktywne. Północ: Perłowe Sztormy, wschód: Czarna Głębia, zachód: Błyskawiczne Wyspy. W dół Węzeł Światów.',
        'exits':{'down':'v2000_nexus','north':'v2000_sea_perly_0','east':'v2000_sea_otchlan_0','west':'v2000_sea_burze_0'},'v2000_port':True})
    counter+=1
    for k,(slug,zone,element,level,names,enemies,boss) in enumerate(ISLANDS):
        entrance=('north','east','west')[k]
        for i,label in enumerate(names):
            exits={'west':f'v2000_sea_{slug}_{i-1}'} if i else {opposite[entrance]:'v2000_ocean_hub'}
            if slug=='burze' and i==0:
                exits['south']=f'v2000_sea_{slug}_1'
            elif slug=='burze' and i==1:
                exits.pop('west',None)
                exits['north']=f'v2000_sea_{slug}_0'
            if i<len(names)-1 and not (slug=='burze' and i==0):exits['east']=f'v2000_sea_{slug}_{i+1}'
            _add('ROOMS',rooms,f'v2000_sea_{slug}_{i}',{
                'name':f'{label} — {zone}','zone':zone,
                'recommended_mastery':min(800,level+i*14), 'generator_level':min(800,level+i*14),
                'desc':f'{zone}: {label}. Trasa wysp {i+1}/{len(names)}. Powrót oznaczony kierunkami; bez losowych pułapek.',
                'exits':exits, 'v2000_ocean':slug})
            counter+=1
        for j,name in enumerate(enemies):
            mid=f'v2000_sea_{slug}_mob_{j}';power=min(800,level+j*17)
            _add('MOB_TEMPLATES',mobs,mid,{
                'name':name,'max_hp':power*(620+j*80),'damage':power*(38+j*4),
                'generator_level':power,'rank':'elite' if j>=3 else 'normal',
                'damage_type':'magic','attack_elements_v11339':(element,), 'fame_target':True,
                'stat_reward':power*245,'class_xp_reward':power*3400,
                'soul_reward':power*1300,'silver':power*750,'gold':0,'mithril':0,
                'drops':{'soul_shard':.4},'quest_target':mid,'stationary_mob':True,'auto_aggro':False})
            spawns.append((f'v2000_sea_{slug}_{1+j}',mid))
        bid=f'v2000_sea_{slug}_boss';power=min(800,level+150)
        _add('MOB_TEMPLATES',mobs,bid,{
            'name':boss,'max_hp':power*9200,'damage':power*175,
            'generator_level':power,'rank':'world_boss','boss':True,'world_boss':True,
            'v1900_ancient_god':True,'boss_mechanic':'elemental_overdrive',
            'damage_type':'magic','attack_elements_v11339':(element,), 'fame_target':True,
            'stat_reward':power*610,'class_xp_reward':power*9400,'soul_reward':power*4500,
            'silver':power*5600,'gold':0,'mithril':0,'drops':{'soul_shard':1.0},
            'quest_target':bid,'stationary_mob':True,'auto_aggro':False})
        spawns.append((f'v2000_sea_{slug}_7',bid))
        _add('QUESTS',quests,f'v2000_sea_{slug}_quest',{
            'name':f'Łowy oceaniczne: {boss}','giver':f'Kartograf {zone}',
            'kind':'kill','target':bid,'needed':1,'description':f'Pokonaj {boss}.',
            'reward_silver':power*3500,'reward_gold':0,'reward_mithril':0,
            'reward_items':{'soul_shard':3},'repeatable':True,'repeat_cooldown':7200})
        _add('NPCS',npcs,f'v2000_sea_{slug}_cartographer',{
            'name':f'Kartograf {zone}','room':f'v2000_sea_{slug}_0',
            'dialogue':'Rejs i dojście do bossa są dwukierunkowe. Fame zdobywasz za pierwsze pokonanie.',
            'quest_chain':(f'v2000_sea_{slug}_quest',)})
    # Arena stages: actual mobs, real combat and credited kills, not a simulated instant win.
    _add('ROOMS',rooms,'v2000_arena_hall',{
        'name':'Hala Areny Legend','zone':'Arena Legend 3.0',
        'desc':'Wpisz arena lista, arena podejmij <kod>, arena status, arena odbierz. Z hali wschód: Żelazna, północ: Żywiołów, zachód: Dusz, południe: Legend.',
        'exits':{'down':'v2000_ocean_hub','east':'v2000_arena_zelazna',
                 'north':'v2000_arena_zywiolow','west':'v2000_arena_dusz','south':'v2000_arena_legend'}})
    cm.catalog_assign('v2000_arena_hall','ROOMS',rooms,('v2000_ocean_hub','exits','up'))
    counter+=1
    for j,(slug,title,level,boss) in enumerate(ARENAS):
        direction=('west','south','east','north')[j]
        _add('ROOMS',rooms,f'v2000_arena_{slug}',{
            'name':title,'zone':'Arena Legend 3.0',
            'generator_level':level,'recommended_mastery':level,
            'desc':f'{title}. Prawdziwy pojedynek PvE z {boss}. Możesz walczyć solo lub w drużynie, wyjście prowadzi do hali. Nie ma pułapek.',
            'exits':{direction:'v2000_arena_hall'},'v2000_arena':slug})
        mid=f'v2000_arena_boss_{slug}'
        _add('MOB_TEMPLATES',mobs,mid,{
            'name':boss,'max_hp':level*8300,'damage':level*125,
            'generator_level':level,'rank':'boss','boss':True,'damage_type':'magic',
            'attack_elements_v11339':(('fire','ice','lightning','dark')[j],),
            'fame_target':True,'stat_reward':level*560,'class_xp_reward':level*7300,
            'soul_reward':level*3300,'silver':level*3300,'gold':0,'mithril':0,
            'drops':{'soul_shard':1.0},'quest_target':mid,'stationary_mob':True,'auto_aggro':False})
        spawns.append((f'v2000_arena_{slug}',mid))
        for wave in range(3):
            wid=f'v2000_arena_wave_{slug}_{wave}'
            _add('MOB_TEMPLATES',mobs,wid,{
                'name':f'{("Strażnik Pierwszej Fali", "Strażnik Drugiej Fali", "Strażnik Trzeciej Fali")[wave]} — {title}',
                'max_hp':level*(430+wave*140),'damage':level*(36+wave*9),
                'generator_level':level,'rank':'elite','damage_type':'physical' if wave==0 else 'magic',
                'fame_target':True,'stat_reward':level*260,'class_xp_reward':level*3000,
                'soul_reward':level*1200,'silver':level*620,'gold':0,'mithril':0,
                'drops':{'soul_shard':.35},'quest_target':wid,'stationary_mob':True,'auto_aggro':False})
            spawns.append((f'v2000_arena_{slug}',wid))
        counter+=1
    for slug,zone,_element,_level,*_ in (*REALMS,*ISLANDS):
        for rank in (1,2,3):
            power=(110,350,740)[rank-1]
            _add('ITEMS',items,f'v2000_faction_{slug}_rank_{rank}',{
                'name':f'Odznaka {zone} — Ranga {rank}',
                'type':'armor','slot':'necklace','rarity':'legendary','price':None,
                'defense':power//2,
                'stats':{'strength':power,'intelligence':power,'constitution':power,
                         'dexterity':power,'wisdom':power,'willpower':power},
                'properties':{'max_hp_pct':rank*2,'all_damage_pct':rank*3},
                'desc':'Trwała nagroda za reputację frakcji. Nie wymaga poświęcania EXP.'})
    return {'realms':len(REALMS),'ocean_archipelagos':len(ISLANDS),
            'arena_stages':len(ARENAS),'rooms':counter,'realm_bosses':len(boss_ids)}
