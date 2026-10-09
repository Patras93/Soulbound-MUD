# -*- coding: utf-8 -*-
"""Soulbound v1.31.0: six connected authored campaigns.

Builds only static, navigable rooms and catalog entries. Quest completion,
party rewards, economy, boss AI and permanent storage remain native systems.
No Generator Core, no schema migration, no procedural equipment IDs.
"""
from __future__ import annotations
from data import catalog_mutations as cm

# Each authored chapter has its own source, NPC, fights and long-term reward.
# Anchors intentionally preserve the old world's established entrances.
CAMPAIGNS = (
    ('emp_deep','Era Imperiów: Bastion Bazaltu','v1300_deep_guild','north','earth',180,
     'Marszałek Żelaznych Bram','Hetman Twardoskórych','miners','Żołnierska Pieczęć Bazaltu','empire'),
    ('emp_sky','Era Imperiów: Twierdza Chmur','v1300_sky_guild','north','lightning',300,
     'Marszałek Podniebnej Warty','Burzowy Hetman','cartographers','Żołnierska Pieczęć Chmur','empire'),
    ('emp_lost','Era Imperiów: Warownia Valdorii','v1300_lost_guild','north','fire',370,
     'Marszałek Starego Cesarstwa','Cesarz Popiołu','green_path','Pieczęć Odnowionej Korony','empire'),
    ('emp_orc','Era Imperiów: Warownia Czterech Klanów','v1300_orc_guild','north','earth',440,
     'Wódz Żelaznej Przysięgi','Generał Rozbitego Rogu','green_path','Pieczęć Czterech Klanów','empire'),
    ('dim_shadow','Wojna Wymiarów: Kraina Cienia','v1300_deep_observatory','north','dark',500,
     'Przewodniczka Cienistych Bram','Arcywładca Rozdarcia','miners','Okruch Cienistej Pieczęci','dimension'),
    ('dim_element','Wojna Wymiarów: Tron Żywiołów','v1300_sky_observatory','north','fire',540,
     'Strażnik Równowagi Żywiołów','Monarcha Czterech Żywiołów','cartographers','Okruch Pierwotnej Iskry','dimension'),
    ('dim_astral','Wojna Wymiarów: Astralna Pustka','v1300_lost_observatory','north','arcane',590,
     'Mistrzyni Rozdarć Astralnych','Władca Bezgłosu','green_path','Okruch Astralnej Przysięgi','dimension'),
    ('players','Świat Graczy: Wolna Dzielnica','v1300_lost_inn','north','physical',130,
     'Zarządczyni Wolnego Targu','Złodziejski Baron Karawan','green_path','Certyfikat Wolnego Handlu','players'),
    ('soul','Dziedzictwo Dusz: Świątynia Echa','v1300_sky_grove','north','light',600,
     'Mistrzyni Pamięci Dusz','Strażnik Nieskończonej Pamięci','cartographers','Fragment Wiecznej Pamięci','soul'),
)
# The third ocean chapter uses a shared departure hub and three fully described islands.
OCEAN_ISLANDS = (
    ('sea_coral','Rafa Żywego Kryształu','east','water',360,'Latarniczka Rafy','Kraken Kryształowych Głębin','Perła Wielkiego Rejsu'),
    ('sea_fog','Wyspa Mgły Przodków','west','dark',430,'Kartografka Mgły','Admirał Widmowej Floty','Kompas Dawnej Floty'),
    ('sea_abyss','Wyspa Bezkresnej Toni','north','water',520,'Kapitan Głębin','Lewiatan Ostatniej Otchłani','Łuska Wielkiego Lewiatana'),
)
ANCIENTS = (
    ('anc_deep','Olbrzym Pierwszych Kuźni','v1300_deep_throne','north','earth',640),
    ('anc_sky','Smok Korony Burz','v1300_sky_throne','north','lightning',670),
    ('anc_lost','Tytan Utraconego Czasu','v1300_lost_throne','north','arcane',720),
    ('anc_orc','Duch Pradawnego Wodza','v1300_orc_throne','north','dark',750),
)
ROLE_NAMES = (
    ('border','Próg Wyprawy','Stary trakt prowadzi do nowej części świata.'),
    ('gate','Brama Straży','Słychać nawoływania straży i kroki podróżnych.'),
    ('square','Plac Przymierza','Tutaj podróżnicy odpoczywają między wyprawami.'),
    ('market','Targ Znalezisk','Kupcy wymieniają materiały, lekarstwa i narzędzia.'),
    ('tavern','Tawerna Odkrywców','Najemnicy spotykają się przy wspólnym stole.'),
    ('archive','Archiwum Kronikarza','Zapisy wypraw, wojennych czynów i dawnej historii.'),
    ('outpost','Posterunek Graniczny','Dowódcy czekają na meldunki o napadach.'),
    ('shrine','Świątynia Przysięgi','Stare symbole nie skrywają losowych pułapek.'),
    ('arena','Sala Próby','W tej sali czeka nazwany legendarny przeciwnik.'),
)
OCEAN_NAMES = (
    ('shore','Przystań Rejsu','Pomosty prowadzą na odległą wyspę.'),
    ('market','Targ Wyspiarski','Kupcy handlują z wyprawami dalekomorskimi.'),
    ('camp','Obóz Marynarzy','Wędrowcy snują opowieści o głębinach.'),
    ('lagoon','Laguna Odkryć','Żywioły i nieznane okazy czekają na badaczy.'),
    ('lighthouse','Stara Latarnia','Ognisko latarni wskazuje drogę powrotną.'),
    ('ruins','Zatopione Ruiny','W kamieniu tkwią pradawne znaki.'),
    ('cave','Jaskinia Prądów','Dźwięk wody odbija się echem.'),
    ('boss','Sanktuarium Morskiego Władcy','W głębi wyspy kryje się legendarny przeciwnik.'),
)

def _room(slug, role):
    return f'v1310_{slug}_{role}'


def _assign(catalog_name, catalog, key, value):
    cm.catalog_assign(value, catalog_name, catalog, (key,))


def _connect(rooms, parent, direction, first, reverse):
    if parent not in rooms:
        raise RuntimeError(f'Nie znaleziono istniejącej lokacji: {parent}')
    existing=rooms[parent].setdefault('exits',{}).get(direction)
    if existing not in (None, first):
        raise RuntimeError(f'Zajęty kierunek {parent}/{direction}: {existing}')
    cm.catalog_assign(first, 'ROOMS', rooms, (parent,'exits',direction))
    cm.catalog_assign(parent, 'ROOMS', rooms, (first,'exits',reverse))


def _boss(mobs, spawns, room_id, key, name, level, element, loot, *, extra=()):
    _assign('MOB_TEMPLATES',mobs,key,{
       'name':name,'max_hp':max(120000, level*2500),'damage':max(2600, level*64),
       'damage_type':'magic' if element not in ('earth','physical') else 'physical',
       'attack_elements_v11339':(element,*extra), 'boss':True,'world_boss':True,
       'rank':'world_boss','generator_level':min(800,level),
       'stat_reward':level*270,'class_xp_reward':level*4100,
       'soul_reward':level*1500,'silver':level*390,'gold':0,'mithril':0,
       'drops':{'soul_shard':1.0,'v12812_legendary_seal':.18,loot:.12},
       'boss_mechanic':'elemental_overdrive',
       'boss_mechanic_text':f'{name} walczy fazami i przywołuje kolejne fale strażników.',
       'quest_target':key, 'quest_targets':(key,),
       'stationary_mob':True, 'auto_aggro':False,'v1310_ancient':True,
    })
    pair=(room_id,key)
    if pair not in spawns: spawns.append(pair)


def _quest(quests,key,name,giver,target,level,*,repeat=False,prereq=None,items=None,faction=None):
    spec={'name':name,'giver':giver,'kind':'kill','target':target,'needed':1,
          'description':f'Pokonaj przeciwnika {name} i wróć po nagrodę. Możesz walczyć solo albo z drużyną.',
          'reward_silver':level*330,'reward_gold':0,'reward_mithril':0,
          'reward_items':items or {},'repeatable':repeat}
    if repeat: spec['repeat_cooldown']=10800
    if prereq:spec['requires_quest']=prereq
    if faction:
        spec['reward_faction_v016']=faction
        spec['reward_faction_amount_v016']=12
    _assign('QUESTS',quests,key,spec)


def install_six_eras_v1310(rooms,npcs,shops,mobs,spawns,quests,items,shop_sellers):
    """Register content after native runtime and the v1.30.1 authored network."""
    for slug,title,parent,direction,element,level,giver,boss_name,faction,loot,kind in CAMPAIGNS:
        first=_room(slug,'border')
        for index,(role,name,desc) in enumerate(ROLE_NAMES):
            exits={}
            if index:exits['south']=_room(slug,ROLE_NAMES[index-1][0])
            if index+1<len(ROLE_NAMES):exits['north']=_room(slug,ROLE_NAMES[index+1][0])
            _assign('ROOMS',rooms,_room(slug,role),{
                'name':f'{name} — {title}','zone':title,'desc':f'{desc} {title}.',
                'exits':exits,'recommended_mastery':level,'v1310_campaign':kind})
        _connect(rooms,parent,direction,first,'south')
        _assign('ITEMS',items,f'v1310_{slug}_token',{
            'name':loot,'type':'material','rarity':'legendary','price':450000,
            'desc':f'Rzadki materiał ekspedycji {title}. Nadaje się do wymiany i rzemiosła.'})
        trader_id=f'v1310_{slug}_trader'
        _assign('NPCS',npcs,trader_id,{'name':f'Kupiec {title}','room':_room(slug,'market'),
            'shopkeeper':True,'dialogue':'Wpisz sklep. Handlujemy także z samotnymi odkrywcami.'})
        shops[_room(slug,'market')]=['healing_potion','iron_guard','lucky_charm','soul_elixir']
        shop_sellers[_room(slug,'market')]=trader_id
        _assign('NPCS',npcs,f'v1310_{slug}_keeper',{
            'name':giver,'room':_room(slug,'archive'),
            'dialogue':'Zapraszam na wyprawę. Wpisz quest list i quest przyjmij.'})
        _assign('NPCS',npcs,f'v1310_{slug}_captain',{
            'name':f'Kapitan Straży {title}','room':_room(slug,'outpost'),
            'dialogue':'Nasi obrońcy nigdy nie zamykają bram podróżnikom.'})
        mob_id=f'v1310_{slug}_lord'
        _boss(mobs,spawns,_room(slug,'arena'),mob_id,boss_name,level,element,
            f'v1310_{slug}_token',extra=('fire','ice') if kind=='dimension' else ())
        _quest(quests,f'v1310_{slug}_quest',f'Próba {title}',giver,mob_id,level,
            repeat=True,faction=faction)
        npcs[f'v1310_{slug}_keeper']['quest']=f'v1310_{slug}_quest'
        if kind=='empire':
            for role,label,scale in (
                ('gate','Zbrojny Obrońca',1),('outpost','Łucznik Warowni',2)):
                guard_key=f'v1310_{slug}_{role}_guard'
                _assign('MOB_TEMPLATES',mobs,guard_key,{
                    'name':f'{label} {title}', 'max_hp':level*1000*scale,
                    'damage':level*38*scale,'damage_type':'physical',
                    'rank':'elite','generator_level':level,'silver':level*80,
                    'gold':0,'mithril':0,'drops':{'v12812_legendary_seal':.02},
                    'stationary_mob':True,'auto_aggro':False})
                spawns.append((_room(slug,role),guard_key))
        # Unique non-repeatable conquest record persists through native quest journal.
        _quest(quests,f'v1310_{slug}_triumph',f'Korona {title}',giver,mob_id,level,
            items={f'v1310_{slug}_token':1},faction=faction)
        npcs[f'v1310_{slug}_keeper']['quest_chain']=(f'v1310_{slug}_triumph',)
    # Morska wyprawa: normalne kierunki z istniejącej oceanicznej platformy.
    ocean_hub='v1310_ocean_departure'
    _assign('ROOMS',rooms,ocean_hub,{
        'name':'Port Trzech Rejsów','zone':'Wielka Era Odkrywców',
        'desc':'Trzy oznaczone kierunki prowadzą do oddalonych wysp. Wróć na południe, by zejść z portu.',
        'exits':{'down':'ocean_platform'},'v1310_campaign':'ocean'})
    _connect(rooms,'ocean_platform','up',ocean_hub,'down')
    for slug,title,direction,element,level,giver,boss_name,loot in OCEAN_ISLANDS:
        for index,(role,name,desc) in enumerate(OCEAN_NAMES):
            exits={}
            if index: exits['south']=_room(slug,OCEAN_NAMES[index-1][0])
            if index+1<len(OCEAN_NAMES):exits['north']=_room(slug,OCEAN_NAMES[index+1][0])
            _assign('ROOMS',rooms,_room(slug,role),{
                'name':f'{name} — {title}','zone':title,'desc':desc+' Szlak morski bez losowych pułapek.',
                'exits':exits,'recommended_mastery':level,'v1310_campaign':'ocean'})
        _connect(rooms,ocean_hub,direction,_room(slug,'shore'),{'east':'west','west':'east','north':'south'}[direction])
        loot_id=f'v1310_{slug}_relic'
        _assign('ITEMS',items,loot_id,{'name':loot,'type':'material','rarity':'legendary',
            'price':550000,'desc':'Unikalny materiał dalekomorskiej ekspedycji.'})
        trader_id=f'v1310_{slug}_trader'
        _assign('NPCS',npcs,trader_id,{'name':f'Kupiec {title}','room':_room(slug,'market'),
            'shopkeeper':True,'dialogue':'Dostarczamy lekarstwa i wyposażenie dla dalekich rejsów.'})
        shops[_room(slug,'market')]=['healing_potion','soul_elixir','lucky_charm']
        shop_sellers[_room(slug,'market')]=trader_id
        _assign('NPCS',npcs,f'v1310_{slug}_questgiver',{'name':giver,
            'room':_room(slug,'camp'),'dialogue':'Zacznij od zadania na miejscowego władcę.'})
        mob_id=f'v1310_{slug}_boss'
        _boss(mobs,spawns,_room(slug,'boss'),mob_id,boss_name,level,element,loot_id)
        _quest(quests,f'v1310_{slug}_quest',f'Wyprawa {title}',giver,mob_id,level,
            repeat=True,items={loot_id:1})
        npcs[f'v1310_{slug}_questgiver']['quest']=f'v1310_{slug}_quest'
    # Starsi bogowie: osobne areny do odkrycia, niezależne od UOSS.
    for slug,name,parent,direction,element,level in ANCIENTS:
        room=_room(slug,'sanctum'); loot=f'v1310_{slug}_heart'
        _assign('ROOMS',rooms,room,{'name':f'Sanktuarium — {name}',
            'desc':'Starożytna arena o kilku fazach. Kierunek południe prowadzi z powrotem. Bez pułapek.',
            'zone':'Przebudzenie Starożytnych','exits':{'south':parent},
            'recommended_mastery':level,'v1310_campaign':'ancients'})
        _connect(rooms,parent,direction,room,'south')
        _assign('ITEMS',items,loot,{'name':f'Serce: {name}', 'type':'material','rarity':'mythic',
            'price':850000,'desc':'Bardzo rzadkie trofeum ze starożytnego superbossa.'})
        _boss(mobs,spawns,room,f'v1310_{slug}_boss',name,level,element,loot,
              extra=('dark','fire','lightning'))
        mobs[f'v1310_{slug}_boss']['ancient_avatar_v1330'] = True
        mobs[f'v1310_{slug}_boss']['boss_mechanic_text'] = (
            'Cztery fazy, rotacja żywiołów i ataki Echa Pradawnych; przywołania bez limitu.')
        giver=f'Kronikarz Starożytnych {slug}'
        _assign('NPCS',npcs,f'v1310_{slug}_keeper',{'name':giver,'room':room,
            'dialogue':'Wpisz quest list, aby spróbować pokonać pradawnego władcę.'})
        _quest(quests,f'v1310_{slug}_quest',f'Starożytny {name}',giver,
               f'v1310_{slug}_boss',level,repeat=True)
        npcs[f'v1310_{slug}_keeper']['quest']=f'v1310_{slug}_quest'
    # v1.33.2: real shared arena for two different Ancients, not a fake description.
    # The existing individual sanctuaries and their original loot remain intact.
    council_entry='v1332_ancients_council_entry'
    council_room='v1332_ancients_council_arena'
    _assign('ROOMS',rooms,council_entry,{
       'name':'Przedsionek Rady Starożytnych',
       'zone':'Przebudzenie Starożytnych',
       'desc':'Dwa dawne trony przemawiają jednocześnie. Droga na północ prowadzi na wspólną arenę. Nie ma pułapek.',
       'exits':{'west':'v1310_anc_sky_sanctum','north':council_room},'recommended_mastery':750,
       'v1310_campaign':'ancients'})
    _connect(rooms,'v1310_anc_sky_sanctum','east',council_entry,'west')
    _assign('ROOMS',rooms,council_room,{
       'name':'Arena Rady Starożytnych',
       'zone':'Przebudzenie Starożytnych',
       'desc':'Olbrzym Pierwszych Kuźni i Smok Korony Burz wspólnie bronią tego miejsca. Leczą sojuszników i koordynują ciosy. Południe: wyjście.',
       'exits':{'south':council_entry},'recommended_mastery':750,
       'v1310_campaign':'ancients','ancient_council_v1332':True})
    spawns.extend(((council_room,'v1310_anc_deep_boss'),(council_room,'v1310_anc_sky_boss')))
    # Dziedzictwo Dusz: pięć etapów zapamiętywanych jako standardowe questy,
    # bez resetu poziomu 800 i bez nowego schematu SQLite.
    giver='Mistrzyni Pamięci Dusz'
    soul_chain=(('dim_shadow','v1310_dim_shadow_lord'),('dim_element','v1310_dim_element_lord'),
                ('sea_abyss','v1310_sea_abyss_boss'),('anc_sky','v1310_anc_sky_boss'),
                ('soul','v1310_soul_lord'))
    _assign('ITEMS',items,'v1310_soul_legacy',{'name':'Relikt Dziedzictwa Dusz',
        'type':'armor','slot':'necklace','rarity':'legendary','price':None,
        'defense':550,'stats':{'strength':660,'intelligence':660,'constitution':660,'willpower':660},
        'properties':{'max_hp_pct':8,'all_damage_pct':7},
        'desc':'Nagroda za pięć prób Dziedzictwa Dusz. Nie resetuje poziomów ani Biegłości.'})
    for i,(region,target) in enumerate(soul_chain,1):
        _quest(quests,f'v1310_legacy_{i}',f'Dziedzictwo Dusz {i}/5: {region}',giver,
            target,500+i*50,prereq=f'v1310_legacy_{i-1}' if i>1 else None,
            items={'v1310_soul_legacy':1} if i==5 else {})
    npcs['v1310_soul_keeper']['quest_chain']=tuple(f'v1310_legacy_{i}' for i in range(1,6))
    # Lokalny rzemieślnik może sprzedać cenne wyroby innym graczom przez
    # istniejący handel. Nie mnożymy cen ani EXP przy zakupie/sprzedaży.
    from data.crafting_recipes import CRAFT_RECIPES
    craft_catalog=(
      ('v1310_empire_medal','Medalion Obrońcy Czterech Twierdz','necklace',
       {'v1310_emp_deep_token':1,'v1310_emp_orc_token':1,'eternium_ingot':2}),
      ('v1310_dimension_circlet','Diadem Równowagi Wymiarów','head',
       {'v1310_dim_shadow_token':1,'v1310_dim_element_token':1,'v1310_dim_astral_token':1,'eternium_ingot':2}),
      ('v1310_ocean_circlet','Korona Trzech Rejsów','head',
       {'v1310_sea_coral_relic':1,'v1310_sea_fog_relic':1,'v1310_sea_abyss_relic':1,'eternium_ingot':2}),
      ('v1310_ancient_circlet','Korona Czterech Starożytnych','head',
       {'v1310_anc_deep_heart':1,'v1310_anc_sky_heart':1,'v1310_anc_lost_heart':1,
        'v1310_anc_orc_heart':1,'eternium_ingot':3}),
    )
    for item_id,name,slot,ingredients in craft_catalog:
        _assign('ITEMS',items,item_id,{
           'name':name,'type':'armor','slot':slot,'rarity':'legendary',
           'defense':290,'stats':{'strength':440,'intelligence':440,
               'constitution':480,'willpower':430},
           'properties':{'max_hp_pct':7,'all_damage_pct':5},
           'price':None,'desc':'Rzadki ręcznie zaprojektowany wyrób z materiałów sześciu er.'})
        _assign('CRAFT_RECIPES',CRAFT_RECIPES,item_id,{
            'name':name,'stations':('forge',),'ingredients':ingredients,
            'output':item_id,'quantity':1,'min_profession_level':180,
            'min_tool_level':120,'profession_xp':4200,'tool_xp':2500,
            'desc':'Rzemiosło: materiały z nowych krain, bez sztucznego limitu statystyk.'})
    # Dostawy karawan: prawdziwe surowce z siatki, sakwy oraz magazynów
    # profesji, a nie puste przedmioty tworzone przy przyjęciu zadania.
    caravan_giver='Mistrzyni Kontraktów Karawanowych'
    caravan_quests=(
      ('ore','iron_ore','Górnictwo','mining'),
      ('fish','salmon','Wędkarstwo','fishing'),
      ('wood','oak_log','Drwalstwo','woodcutting'),
      ('herbs','chamomile','Zielarstwo','herbalism'),
    )
    for kind,resource,profession,tool in caravan_quests:
        _assign('QUESTS',quests,f'v1310_caravan_{kind}',{
           'name':f'Karawany Wolnego Targu: {profession}',
           'giver':caravan_giver,'kind':'collect_resource',
           'target':resource,'needed':8,
           'description':f'Dostarcz osiem sztuk {resource} z własnych zasobów.',
           'reward_silver':44000,'reward_gold':0,'reward_mithril':0,
           'reward_profession':profession,'reward_profession_xp':8500,
           'reward_tool_type':tool,'reward_tool_xp':2200,
           'repeatable':True,'repeat_cooldown':21600})
    # The permanent house/guild economy is *already live*; add a real exchange
    # quarter with vendors and quests, not a duplicate wallet/storage system.
    _assign('NPCS',npcs,'v1310_players_steward',{
        'name':'Zarządczyni Domów i Gildii','room':_room('players','square'),
        'dialogue':'Własny dom: dom / house. Rozbudowa gildii: gildia siedziba. Handel graczy: handel.'})
    _assign('NPCS',npcs,'v1310_players_caravan',{
        'name':'Mistrzyni Kontraktów Karawanowych','room':_room('players','outpost'),
        'dialogue':'Najpierw pokonaj Barona Karawan, potem odbierz kontrakt.'})
    npcs['v1310_players_caravan']['quest_chain']=tuple(
       f'v1310_caravan_{kind}' for kind,_,_,_ in caravan_quests)
    # Set the source and quest support without overriding existing content.
    return {'campaigns':len(CAMPAIGNS),'islands':len(OCEAN_ISLANDS),
            'ancients':len(ANCIENTS), 'heritage_stages':len(soul_chain)}
