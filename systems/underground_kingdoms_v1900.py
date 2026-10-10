# -*- coding: utf-8 -*-
"""Soulbound v1.90.0: authored underground kingdoms and Chaos dimension routes.

Only additive catalog IDs and normal room/mob/quest/loot paths: old saves and
world IDs remain valid. No traps, random names, procedural loot or level gates.
"""
from __future__ import annotations
from data import catalog_mutations as cm

KINGDOMS = (
    ('miedz', 'Królestwo Miedzianych Ech', 'fire', 390,
     ('Wrota Starych Kuźni', 'Most nad Lawą', 'Sala Kopaczy', 'Rdzawa Galeria',
      'Ogród Miedzianych Grzybów', 'Korytarz Dzwonów', 'Komnata Żużlu',
      'Archiwum Górników', 'Zawalona Sala', 'Bastion Ognia', 'Kamienny Balkon',
      'Czerwony Rezerwuar', 'Krypta Kowali', 'Aleja Śladów', 'Podziemny Akwedukt',
      'Sala Żelaznych Bram', 'Komnata Mistrzów', 'Kopalnia Szeptów',
      'Łuk Starego Tronu', 'Głębokie Podkuźnie', 'Wąwóz Miedzianych Strun', 'Tron Kuźni'),
     ('Kret Rozpalonych Skał', 'Miedziany Golem', 'Ognisty Nietoperz',
      'Kowal Bez Twarzy', 'Żelazny Strażnik', 'Salamandra Rdzawych Żył',
      'Duch Wypalonego Młota', 'Wilk Jaskiniowych Iskier',
      'Kolos Żużlowy', 'Górnik Widmo', 'Miedziany Bazyliszek', 'Strażnik Pieca'),
     ('Hargun, Pan Żarzącej Kuźni','Rozżarzony Prorok','Bogini Miedzianego Jądra')),
    ('zarodniki', 'Dwór Zarodnikowych Królów', 'poison', 480,
     ('Brama Korzeni', 'Lśniące Gniazda', 'Królewska Grzybnia', 'Sieć Podziemnych Strumieni',
      'Łuk Zarodników', 'Podziemna Polana', 'Sala Błękitnych Kapeluszy', 'Korzenna Strażnica',
      'Gaj Cichych Zarodników', 'Kryształowy Staw', 'Most Białych Korzeni', 'Świątynia Porostów',
      'Komnata Roju', 'Dolina Wiecznych Liści', 'Galeria Zarośli', 'Szlak Uśpionych Drzew',
      'Sala Zielonych Trujących Kwiatów', 'Ciche Źródło', 'Skarbiec Porostów',
      'Złota Grzybnia', 'Schronienie Starego Dębu', 'Tron Zarodników'),
     ('Strażnik Zarodników', 'Pająk Szmaragdowych Korzeni', 'Grzybowy Rycerz',
      'Jadowity Chrząszcz', 'Wąż Podziemnych Rzek', 'Leśny Cień',
      'Zakażony Druid', 'Kryształowy Ślimak', 'Trująca Kobra Głębin',
      'Rój Zielonych Skrzydeł', 'Prastary Porost', 'Wilk Grzybni'),
     ('Velyra, Matka Grzybni','Arcykapłan Zarodników','Bogini Korzennego Serca')),
    ('obsydian', 'Imperium Obsydianowego Szeptu', 'dark', 580,
     ('Obsydianowe Wrota', 'Sala Nocnych Piór', 'Czarny Wiadukt', 'Księga Zapomnienia',
      'Galeria Rozbitych Gwiazd', 'Zapadnięte Archiwum', 'Most Czarnego Kryształu',
      'Strażnica Pustki', 'Krypta Szeptów', 'Labirynt Cieni', 'Sala Mrocznych Lusterek',
      'Przedsionek Cesarza', 'Schody Nieskończoności', 'Komnata Run', 'Wąwóz Nocy',
      'Ciemne Obserwatorium', 'Podziemna Biblioteka', 'Ogród Czarnych Róż',
      'Panteon Milczenia', 'Skarbiec Wiecznej Nocy', 'Próg Obsydianu', 'Tron Szeptu'),
     ('Obsydianowy Mściciel', 'Strażnik Czarnego Lustra', 'Widmo Korony',
      'Pustkowy Rycerz', 'Nocny Nietoperz', 'Runiczny Kruk',
      'Duch Zapomnianej Cesarzowej', 'Kryształowy Pająk', 'Arcynekromanta Szeptów',
      'Golem Czarnego Marmuru', 'Szepczący Wąż', 'Cienisty Egzekutor'),
     ('Ishrak, Strażnik Czarnego Tronu','Sędzia Obsydianu','Pan Zapomnianych Królestw')),
)

DIMENSIONS = (
    ('plomienie', 'Wymiar Płomiennego Echa', 'fire', 650),
    ('szron', 'Wymiar Wiecznego Szronu', 'ice', 690),
    ('otchlan', 'Wymiar Bezkresnej Otchłani', 'void', 740),
)


def _put(catalog_type, catalog, key, value):
    if key in catalog:
        raise ValueError(f'Duplicate v1.90.0 authored ID: {key}')
    cm.catalog_assign(value, catalog_type, catalog, (key,))


def install_underground_kingdoms_v1900(rooms, npcs, shops, mobs, spawns, quests,
                                        items, shop_sellers, recipes):
    """Add 3 explorable kingdoms, 2 city hubs and 3 dimensional challenge routes."""
    anchor = 'v1800_portal'
    if anchor not in rooms or 'down' in rooms[anchor]['exits']:
        raise ValueError('v1.90.0 portal requires free downward exit')
    cm.catalog_assign('v1900_nexus', 'ROOMS', rooms, (anchor, 'exits', 'down'))
    _put('ROOMS', rooms, 'v1900_nexus', {
        'name': 'Brama Podziemnych Królestw', 'zone': 'Pradawne Podziemia',
        'desc': 'Na górze Rozdroże Bogów Chaosu. Na północ Miedziane Echo, na wschód Dwór Zarodników, '
                'na południe Obsydian. Na zachodzie wyraźnie oznaczone Wymiary Chaosu. Bez pułapek.',
        'exits': {'up':anchor, 'north':'v1900_miedz_0', 'east':'v1900_zarodniki_0',
                  'south':'v1900_obsydian_0', 'west':'v1900_dim_hub'},
        'recommended_mastery':390,
    })
    gateways = ('south','west','north')
    inward = ('north','east','south')
    room_count=1
    for k,(slug, zone, element, level, names, enemies, bosses) in enumerate(KINGDOMS):
        material=f'v1900_{slug}_relic_ore'
        _put('ITEMS',items,material,{'name':('Ruda Starych Kuźni','Zarodnik Królewskiego Dworu',
                                                'Odłamek Obsydianowej Korony')[k],
            'type':'material','rarity':'legendary','price':700000+level*4200,
            'desc':'Autentyczny surowiec Podziemnych Królestw, wykorzystywany w recepturach artefaktów.'})
        for i,label in enumerate(names):
            exits={}
            if i:exits['west']=f'v1900_{slug}_{i-1}'
            else:exits[gateways[k]]='v1900_nexus'
            if i<len(names)-1:exits['east']=f'v1900_{slug}_{i+1}'
            if i==2 and k<2:exits['north']=f'v1900_city_{slug}_gate'
            _put('ROOMS',rooms,f'v1900_{slug}_{i}',{
                'name':f'{label} — {zone}','zone':zone,'generator_level':min(800,level+(i//4)*12),
                'recommended_mastery':min(800,level+(i//4)*12),
                'desc':f'{label}. Podziemny szlak {zone}, odcinek {i+1} z {len(names)}. '
                       'Droga jest dwukierunkowa; zagrożenia i potwory są opisane tekstowo. '
                       'Eksploracja możliwa solo lub w drużynie.',
                'exits':exits,'v1900_underground':slug})
            room_count+=1
        for j,label in enumerate(enemies):
            mid=f'v1900_{slug}_mob_{j}'
            power=level+j*8
            _put('MOB_TEMPLATES',mobs,mid,{
                'name':label,'max_hp':power*(380+j*45),'damage':power*(26+j*3),
                'generator_level':min(800,power),'damage_type':'magic' if j%3==0 else 'physical',
                'attack_elements_v11339':(element,), 'rank':'elite' if j>=9 else 'normal',
                'fame_target':True, 'stat_reward':power*200, 'class_xp_reward':power*2400,
                'soul_reward':power*830,'silver':power*520,'gold':0,'mithril':0,
                'drops':{material:.18 if j<9 else .38,'soul_shard':.3},
                'quest_target':mid,'stationary_mob':True,'auto_aggro':False})
            # Two physically accessible locations per species; no fake Fame objectives.
            for idx in (1+(j*2)%18,2+(j*2)%19):
                spawns.append((f'v1900_{slug}_{idx}',mid))
        hunter=f'Kronikarz {zone}'
        chain=[]
        for j,boss_name in enumerate(bosses):
            mid=f'v1900_{slug}_god_{j}'
            power=min(800,level+70+j*60)
            is_god=j==2
            _put('MOB_TEMPLATES',mobs,mid,{
                'name':boss_name, 'max_hp':power*(6800 if is_god else 3500),
                'damage':power*(170 if is_god else 90), 'damage_type':'magic',
                'attack_elements_v11339':(element,'dark'),
                'generator_level':power,'rank':'world_boss' if is_god else 'boss',
                'boss':True,'world_boss':is_god,'v1900_ancient_god':True,
                'boss_mechanic':'elemental_overdrive',
                'boss_mechanic_text':'Fazy 70%, 40%, 15% HP. Zmiana ochrony i ataków przywołań.',
                'stat_reward':power*550,'class_xp_reward':power*8200,
                'soul_reward':power*3800,'silver':power*3500,'gold':0,'mithril':0,
                'drops':{material:1.0,'soul_shard':1.0},
                'quest_target':mid,'stationary_mob':True,'auto_aggro':False})
            spawns.append((f'v1900_{slug}_{(8,16,21)[j]}',mid))
            qid=f'v1900_god_quest_{slug}_{j}'
            _put('QUESTS',quests,qid,{
                'name':f'Kronika: {boss_name}','giver':hunter,'kind':'kill','target':mid,
                'needed':1, 'description':f'Pokonaj {boss_name} w krainie {zone}.',
                'reward_silver':power*4200,'reward_gold':0,'reward_mithril':0,
                'reward_items':{material:2+j},'repeatable':True,'repeat_cooldown':7200})
            chain.append(qid)
        _put('NPCS',npcs,f'v1900_chronicler_{slug}',{
            'name':hunter,'room':f'v1900_{slug}_0',
            'dialogue':'Bogowie przemawiają przez trzy fazy walki. Można walczyć w drużynie i solo.',
            'quest_chain':tuple(chain)})
    # Two navigable settlements, not shortcuts past the region's bosses.
    for slug, town in (('miedz','Miasto Płonących Kuźni'),
                       ('zarodniki','Osada Białej Grzybni')):
        names={'gate':'Brama','square':'Plac','market':'Targ','forge':'Kuźnia',
               'archive':'Archiwum','inn':'Karczma'}
        exits={
            'gate':{'south':f'v1900_{slug}_2','north':f'v1900_city_{slug}_square'},
            'square':{'south':f'v1900_city_{slug}_gate','east':f'v1900_city_{slug}_market',
                      'west':f'v1900_city_{slug}_inn','north':f'v1900_city_{slug}_archive'},
            'market':{'west':f'v1900_city_{slug}_square','north':f'v1900_city_{slug}_forge'},
            'forge':{'south':f'v1900_city_{slug}_market'},
            'archive':{'south':f'v1900_city_{slug}_square'},
            'inn':{'east':f'v1900_city_{slug}_square'},
        }
        for role,name in names.items():
            _put('ROOMS',rooms,f'v1900_city_{slug}_{role}',{
                'name':f'{name} — {town}','zone':town,'recommended_mastery':400,
                'desc':f'{town}: {name.lower()}. Mieszkańcy handlują, opowiadają historie i wskazują wyjścia. '
                       'Wszystkie przejścia prowadzą w obie strony.',
                'exits':exits[role], 'v1900_city':True})
            room_count+=1
        npc_id=f'v1900_vendor_{slug}'
        _put('NPCS',npcs,npc_id,{'name':f'Kupiec {town}',
            'room':f'v1900_city_{slug}_market','shopkeeper':True,
            'dialogue':'Kupisz mikstury i zapasy. Legendarne artefakty wymagają realnych surowców.'})
        market=f'v1900_city_{slug}_market'
        cm.catalog_assign(['healing_potion','greater_healing_potion','mana_potion','lucky_charm'],
                          'SHOPS',shops,(market,))
        shop_sellers[market]=npc_id
    # Real renewable profession-action contracts for all fourteen professions.
    # They build on the same quest progress/reward handlers as Sky v1.70.0.
    from systems.sky_era_v1700 import PROFESSIONS
    for i, (profession,tool,action) in enumerate(PROFESSIONS):
        town_slug='miedz' if i%2==0 else 'zarodniki'
        master=f'Mistrz Podziemi: {profession}'
        qid=f'v1900_profession_{i}'
        _put('QUESTS',quests,qid,{
            'name':f'Podziemna Próba: {profession}',
            'giver':master,'kind':'profession_action','target':profession,'needed':45,
            'description':f'Wykonaj 45 nowych czynności {profession} po przyjęciu. {action}.',
            'required_profession':profession,'specialist_tool_type':tool,
            'reward_profession':profession,'reward_profession_xp':90000,
            'reward_tool_type':tool,'reward_tool_xp':45000,
            'reward_silver':4800000,'reward_gold':0,'reward_mithril':0,
            'repeatable':True,'repeat_cooldown':7200})
        _put('NPCS',npcs,f'v1900_prof_master_{i}',{
            'name':master,
            'room':f'v1900_city_{town_slug}_{"forge" if i%3==0 else "archive"}',
            'dialogue':f'Podziemna Próba {profession}: {action}. '
                       'Wykonane czynności liczą się dopiero od przyjęcia zadania.',
            'strict_profession_quests':profession,'specialist_quests':(qid,)})
    # Authored repeatable dimensions expand exploration around EXISTING unlimited dungeons;
    # they do not claim to replace the infinite floor/elevator engine.
    _put('ROOMS',rooms,'v1900_dim_hub',{
        'name':'Rozstaje Wymiarów Chaosu','zone':'Wymiary Chaosu',
        'desc':'Na wschodzie Brama Królestw. Północ, południe i zachód prowadzą do '
               'trzech odmiennych prób. Istniejące nieskończone lochy pozostają bez limitu pięter.',
        'exits':{'east':'v1900_nexus','north':'v1900_dim_plomienie_0',
                 'south':'v1900_dim_szron_0','west':'v1900_dim_otchlan_0'}})
    room_count+=1
    for slug,zone,element,level in DIMENSIONS:
        return_dir={'plomienie':'south','szron':'north','otchlan':'east'}[slug]
        for i in range(12):
            exits={return_dir:'v1900_dim_hub'} if i==0 else {'west':f'v1900_dim_{slug}_{i-1}'}
            if i<11:exits['east']=f'v1900_dim_{slug}_{i+1}'
            _put('ROOMS',rooms,f'v1900_dim_{slug}_{i}',{
                'name':f'{("Przedsionek", "Most Echa", "Rozbita Sala", "Komnata Magii", "Próg Run", "Dolina Kryształów", "Łuk Strażnika", "Krypta Wiatru", "Galeria Dusz", "Świątynia Żywiołu", "Wrota Próby", "Arena Wymiaru")[i]} — {zone}',
                'zone':zone,'generator_level':min(800,level+i*10),
                'recommended_mastery':min(800,level+i*10),
                'desc':f'Wyzwanie wymiaru {zone}. Odcinek {i+1}/12. Przejścia są czytelne, '
                       'powrót jest możliwy; nie ma ukrytych pułapek.',
                'exits':exits,'v1900_dimension':slug})
            room_count+=1
        for j in range(6):
            mid=f'v1900_dim_{slug}_mob_{j}'
            power=min(800,level+j*15)
            _put('MOB_TEMPLATES',mobs,mid,{
                'name':f'{("Strażnik", "Zwiadowca", "Golem", "Rycerz", "Duch", "Egzekutor")[j]} {zone}',
                'max_hp':power*(850+j*110),'damage':power*(58+j*10),
                'generator_level':power,'rank':'elite','damage_type':'magic',
                'attack_elements_v11339':(element,), 'fame_target':True,
                'stat_reward':power*290,'class_xp_reward':power*3800,
                'soul_reward':power*1250,'silver':power*1050,'gold':0,'mithril':0,
                'drops':{'soul_shard':.4},'quest_target':mid,
                'stationary_mob':True,'auto_aggro':False})
            for i in (1+j,6+j):spawns.append((f'v1900_dim_{slug}_{i}',mid))
        boss_id=f'v1900_dim_{slug}_keeper'
        _put('MOB_TEMPLATES',mobs,boss_id,{
            'name':f'Władca {zone}','max_hp':level*8200,'damage':level*185,
            'generator_level':min(800,level+110),'rank':'world_boss','boss':True,
            'world_boss':True,'v1900_ancient_god':True,'damage_type':'magic',
            'attack_elements_v11339':(element,),
            'boss_mechanic':'elemental_overdrive',
            'stat_reward':level*580,'class_xp_reward':level*8900,
            'soul_reward':level*3950,'silver':level*4050,'gold':0,'mithril':0,
            'drops':{'soul_shard':1.0},'quest_target':boss_id,
            'stationary_mob':True,'auto_aggro':False})
        spawns.append((f'v1900_dim_{slug}_11',boss_id))
    # 6 craftable legendary items, each with distinct role and valid source materials.
    gear=(
        ('korona','Korona Głębokiego Żaru','head', 'miedz',650,'strength', 'fire'),
        ('tarcza','Tarcza Miedzianych Pieczęci','shield','miedz',700,'constitution','fire'),
        ('plaszcz','Płaszcz Żywej Grzybni','cloak','zarodniki',680,'willpower','poison'),
        ('buty','Buty Bezgłośnych Korzeni','feet','zarodniki',660,'dexterity','poison'),
        ('amulet','Amulet Obsydianowego Szeptu','necklace','obsydian',760,'intelligence','dark'),
        ('zbroja','Zbroja Strażnika Nocy','body','obsydian',780,'constitution','dark'),
    )
    for slug,label,slot,kingdom,level,stat,ward in gear:
        iid=f'v1900_artifact_{slug}';mat=f'v1900_{kingdom}_relic_ore'
        _put('ITEMS',items,iid,{
            'name':label,'type':'armor','slot':slot,'rarity':'legendary','price':None,
            'defense':int(level*1.8) if slot!='shield' else int(level*2.5),
            'stats':{stat:level*2,'constitution':level//2} if stat!='constitution'
                    else {'constitution':level*2,'strength':level//2},
            'properties':{'max_hp_pct':6 if slot=='body' else 3,
                          'all_damage_pct':5 if slot in ('head','necklace') else 2},
            'element_wards':{ward:0.12},
            'desc':'Legendarna rzecz z realnych materiałów podziemi. Można mieszać części EQ.'})
        _put('CRAFT_RECIPES',recipes,iid,{
            'name':label,'stations':('forge',),
            'ingredients':{mat:6, 'soul_shard':12, 'dragonsteel_ingot':3},
            'output':iid,'quantity':1,'min_profession_level':max(1,level-200),
            'tool_xp':150,'desc':f'Artefakt poziomu {level}; rzadkie łupy {kingdom}.'})
    return {'kingdoms':len(KINGDOMS),'settlements':2,'dimensions':len(DIMENSIONS),
            'rooms':room_count,'new_mob_templates':3*(12+3)+3*7,
            'legendary_recipes':len(gear),'profession_trials':14}
