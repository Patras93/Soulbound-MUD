# -*- coding: utf-8 -*-
"""Soulbound 1.50.0 — ręcznie zaprojektowany kontynent, 25 bossów, 40-etapowa saga,
    14 profesji w trzech etapach, 24 rzemieślnicze receptury.
    Katalogi używają istniejących questów i persystencji, bez nowej tabeli SQLite.
"""
from data import catalog_mutations as cm

REGIONS = (
 ('szron', 'Korona Północnego Szronu','Kraina Kryształowych Burz','ice', 320,
  ('Przełęcz Białych Wilków','Śnieżna Strażnica','Most Nad Przepaścią','Plac Zorzy','Jaskinia Mroźnego Wiatru','Kamienne Schody','Zamarznięty Akwedukt','Krypta Lodowego Żaru','Wąwóz Szeptów','Ołtarz Zimowego Słońca'),
  ('Warden Arktos','Czarodziejka Lodowych Róż','Gromowładny Jarl','Wilczy Herold Północy','Król Bezsennej Zamieci'),
  ('Tysiącletnia Strażniczka Zorzy','Lodowa Korona Przodków'), 'Szafirowy Odłamek Północy'),
 ('zar', 'Pustkowia Wiecznego Żaru','Kraina Popiołu i Ognistych Kuźni','fire', 390,
  ('Wrota Czarnego Żużlu','Trakt Pękniętej Ziemi','Obóz Wędrownych Kowali','Most Lawowej Rzeki','Kuźnia Czerwonego Nieba','Plac Żelaznych Dzwonów','Komora Wyrzutów','Przeprawa Bazaltowa','Galeria Siedmiu Pieców','Sanktuarium Starego Płomienia'),
  ('Strażnik Krwawego Węgla','Smoczy Płatnerz','Kapłan Trzech Pieców','Władczyni Lawowych Rzek','Imperator Wypalonej Korony'),
  ('Pradawny Feniks Wiecznego Żaru','Szept Pierwszego Płomienia'), 'Serce Pradawnej Kuźni'),
 ('korzen', 'Las Zatopionych Korzeni','Kraina Druidów i Utraconych Ogrodów','poison', 460,
  ('Ścieżka Tysiąca Liści','Most Korzeni','Wioska Zielonych Latarni','Kapliczka Nasiennego Serca','Mokradła Pamięci','Polana Śpiewającej Rosy','Koronna Gałąź','Targ Ziół','Jaskinia Grzybnych Kolumn','Święty Krąg Drzewa'),
  ('Strażnik Ciernistych Wrót','Matka Błotnych Duchów','Łowczyni Zielonych Cieni','Książę Gnijących Pnączy','Monarcha Czarnego Drzewa'),
  ('Pramatka Odrodzenia','Korona Żywych Korzeni'), 'Żywa Łza Starego Lasu'),
 ('gwiazda', 'Astralne Morze Gwiazd','Kraina Spadających Konstelacji','arcane', 550,
  ('Przystań Niebiańskich Łodzi','Most Bezgrawitacji','Obserwatorium Komety','Galeria Srebrnych Orbit','Świątynia Pulsara','Korytarz Starych Gwiazd','Plac Tęczowego Zaćmienia','Wieża Czasu','Ogród Astralnej Mgły','Tron Horyzontu'),
  ('Łowca Zgasłych Gwiazd','Pani Złamanego Księżyca','Strażnik Czarnej Komety','Mistrz Bezwładnego Czasu','Cesarz Pustego Nieba'),
  ('Przedwieczny Architekt Konstelacji','Pieczęć Ostatniej Gwiazdy'), 'Łza Kosmicznego Horyzontu'),
)
CHAPTERS = ('Przejście Granicy','Głos Dawnego Królestwa','Sekret Zapomnianych Dróg','Próba Władców')
STORY_STAGES = (
  ('Zaginiony meldunek', 'Na granicy odnaleziono list o śladach zdrady sprzed stu lat.'),
  ('Przysięga dawnej straży', 'Strażnik dawnych wrót pilnuje prawdy o upadku pierwszych miast.'),
  ('Wyprawa kartografów', 'Ostatni świadek wyprawy zostawił fragment mapy zapisany na zbroi zwiadowcy.'),
  ('Pierwszy upadły władca', 'Odzyskaj pierwszy znak przysięgi. Niegdyś chronił mieszkańców przed mrokiem.'),
  ('Milczenie kupców', 'Karawany zaginęły pośród ruin. Znajdź trop w obozie wrogich poszukiwaczy.'),
  ('Korona rozdarcia', 'Drugi z dawnych władców chroni część zapieczętowanej korony.'),
  ('Słowa z zatartych tablic', 'Runiczne zapiski wyjawiają, dlaczego przodkowie ukryli pamięć czterech krain.'),
  ('Pamięć w popiołach', 'Trzeci i czwarty znak otwierają drogę do prawdy o utraconym królestwie.'),
  ('Głos ostatniego świadka', 'Weteran dawnej korony zna prawdziwe imię zdrajcy; zdobądź jego świadectwo.'),
  ('Ostatnia pieczęć', 'Ostatni władca strzeże pieczęci. Zwycięstwo kończy historię krainy, ale nie przygodę.'),
)
ROOM_DETAILS = (
 'W powietrzu słychać dźwięk dawnych szlaków; każdy podróżnik może odnaleźć oznaczenia drogi.',
 'Na murach pozostawiono opowieści o zaginionych wyprawach; szlak pozostaje otwarty.',
 'Kupcy opowiadają o nowych materiałach, które prawdziwie warto zbierać i obrabiać.',
 'Pod kamieniami zachowano znaki Przebudzenia. Nic tutaj nie wywołuje losowych pułapek.',
 'Ślady przeciwników prowadzą do sąsiednich przejść, a echo zdradza kierunki.',
 'Wyryte w skale imiona przypominają pokonanych mistrzów dawnych czasów.',
 'Pośród ruin widać bezpieczne miejsce odpoczynku i drogę do dalszej wyprawy.',
 'Tutejsze mapy rozdzielają kolejne komnaty, nie prowadząc gracza w ślepy labirynt.',
 'Za zniszczonymi kolumnami majaczy światło nowego odkrycia i przygody.',
 'Stare inskrypcje wskazują starą trasę bohaterów, prowadzącą do najwyższej próby.',
)
PROFESSIONS = (
 ('Górnictwo','mining','Wydobycie rudy z dawnych żył'),
 ('Wędkarstwo','fishing','Połów rzadkich okazów'),
 ('Drwalstwo','woodcutting','Pozyskanie bezcennego drewna'),
 ('Zielarstwo','herbalism','Zbieranie ziół nowych krain'),
 ('Kowalstwo','crafting','Kucie legendarnych stopów'),
 ('Gotowanie','cooking','Przygotowanie posiłków na wyprawę'),
 ('Alchemia','alchemy','Destylacja nowych esencji'),
 ('Jubilerstwo','jewelcrafting','Oprawa starych klejnotów'),
 ('Krawiectwo','tailoring','Tkanie płaszczy odkrywców'),
 ('Garbarstwo','leatherworking','Obróbka skór bestii'),
 ('Stolarstwo','carpentry','Budowa sprzętu ekspedycji'),
 ('Zaklinanie','enchanting','Związanie run żywiołów'),
 ('Archeologia','archaeology','Badanie pozostałości cywilizacji'),
 ('Kartografia','cartography_profession','Mapowanie nieopisanych szlaków'),
)
# Przypisanie konkretnych, różniących się tematem czynności do specjalistów.
BOSS_EFFECTS = (
 ('ice','Lodowa blokada: spowalniające pociski i fala mrozu.'),
 ('lightning','Wyładowanie: ataki piorunem i chwilowe porażenie.'),
 ('fire','Ognisty przełom: okresowe podpalenia podczas walki.'),
 ('dark','Ciemność: przekleństwo zwiększające otrzymywane obrażenia.'),
 ('void','Pustka: uderzenia wysysające manę i rozrywające osłony.'),
)


def rid(slug, row, col):
    return f'v1500_{slug}_{row}_{col}'


def put(catalog_name, catalog, key, value):
    if key in catalog:
        raise RuntimeError(f'v1.50.0: zajęty identyfikator {catalog_name}/{key}')
    cm.catalog_assign(value, catalog_name, catalog, (key,))


def boss_template(name, level, element, treasure, *, superboss=False, ordinal=0):
    effect = BOSS_EFFECTS[ordinal % len(BOSS_EFFECTS)]
    elements = (element, effect[0], 'poison' if ordinal % 2 else 'holy')
    return {
        'name': name, 'max_hp': level * (5200 if superboss else 2300),
        'damage': level * (115 if superboss else 61),
        'damage_type': 'magic', 'attack_elements_v11339':elements,
        'boss':True,'world_boss':True,'rank':'world_boss',
        'generator_level':min(800,level),'stat_reward':level*(380 if superboss else 200),
        'class_xp_reward':level*(5800 if superboss else 2600),
        'soul_reward':level*(2100 if superboss else 900),
        'silver':level*(1200 if superboss else 570),'gold':0,'mithril':0,
        'drops':{treasure:1.0 if superboss else .65, 'soul_shard':1.0,
                 'v12812_legendary_seal':.55 if superboss else .18},
        'boss_mechanic':'elemental_overdrive',
        'boss_mechanic_text':('Superboss. ' if superboss else 'Boss. ') + effect[1] +
          ' Zmienna faza i ataki kilku żywiołów w istniejącym silniku walki.',
        'quest_target':None, 'stationary_mob':True,'auto_aggro':False,
        'v1500_forgotten_boss':True,
    }


def install_forgotten_world_v1500(rooms,npcs,shops,mobs,spawns,quests,items,shop_sellers):
    """Wpisy tylko przez kontrolowane API; żadnych nowych danych osobowych ani migracji."""
    from data.crafting_recipes import CRAFT_RECIPES
    anchor='v1310_emp_lost_arena'
    if anchor not in rooms or rooms[anchor].get('exits',{}).get('east'):
        raise RuntimeError('v1.50.0: historyczna brama Valdorii niedostępna')
    put('ROOMS',rooms,'v1500_gate',{
        'name':'Brama Zapomnianych Światów','zone':'Zapomniane Światy',
        'desc':'Cztery szlaki wiodą do Szronu, Żaru, Lasu i Gwiazd. Wejście do nowej sagi bez blokady poziomu. '
               'Wpisz kontynent, by poznać drogę; nie ma losowych pułapek.',
        'exits':{'west':anchor,'north':rid('szron',0,0),
                 'east':rid('zar',0,0),'south':rid('korzen',4,0),
                 'up':'v1500_super_council'},
        'recommended_mastery':300,'v1500_gateway':True,
    })
    cm.catalog_assign('v1500_gate','ROOMS',rooms,(anchor,'exits','east'))
    # Czwarty szlak wychodzi z astralnego obserwatorium, bo główna brama ma tylko 4 kierunki.
    put('ROOMS',rooms,'v1500_starlight_gate',{
       'name':'Wrota Piątej Konstelacji','zone':'Zapomniane Światy',
       'desc':'Przejście do Astralnego Morza Gwiazd. Stare gwiezdne mapy wskazują bezpieczną trasę.',
       'exits':{'west':'v1500_gate','east':rid('gwiazda',0,0)},
       'recommended_mastery':550})
    # Piąty kierunek prowadzi do osobnych wrót konstelacji po wyjściu z bramy.
    cm.catalog_assign('v1500_starlight_gate','ROOMS',rooms,('v1500_gate','exits','down'))
    for zone_index,(slug,title,theme,element,level,places,boss_names,super_tuple,material_name) in enumerate(REGIONS):
        super_name,super_loot=super_tuple
        material_id=f'v1500_{slug}_material'
        trophy_id=f'v1500_{slug}_relic'
        put('ITEMS',items,material_id,{'name':material_name,'type':'craft_material','rarity':'legendary',
             'price':1300000+zone_index*300000,'desc':f'Rzadki materiał z krainy {title}; pełnowartościowy surowiec rzemieślniczy.'})
        put('ITEMS',items,trophy_id,{'name':super_loot,'type':'material','rarity':'legendary',
             'price':4500000+zone_index*800000,'desc':f'Pamiątka zwycięstwa w {title}. Wykorzystaj w kowalstwie.'})
        for row in range(5):
            for col in range(8):
                key=rid(slug,row,col)
                loc_number=(row*8+col)
                # unikalne nazwy i konkretne opisy opracowane na podstawie dziesięciu motywów krainy
                local=places[loc_number%10]
                chapter=CHAPTERS[loc_number//10]
                exits={}
                if row: exits['north']=rid(slug,row-1,col)
                if row<4: exits['south']=rid(slug,row+1,col)
                if col: exits['west']=rid(slug,row,col-1)
                if col<7: exits['east']=rid(slug,row,col+1)
                if slug=='szron' and (row,col)==(0,0): exits['north']='v1500_gate'
                if slug=='zar' and (row,col)==(0,0): exits['west']='v1500_gate'
                if slug=='korzen' and (row,col)==(4,0): exits['south']='v1500_gate'
                if slug=='gwiazda' and (row,col)==(0,0): exits['west']='v1500_starlight_gate'
                if row==4 and col==7:
                    exits['south']=f'v1500_{slug}_super_room'
                put('ROOMS',rooms,key,{
                    'name':f'{local} — {chapter} ({title})', 'zone':title,
                    'desc':f'{theme}. {ROOM_DETAILS[loc_number%10]} Rozdział: {chapter}. Odkrycie {loc_number+1}/40.',
                    'exits':exits,'recommended_mastery':min(800,level+loc_number*3),
                    'v1500_region':slug, 'v1500_chapter':1+loc_number//10,
                })
        # Konsekwentne wrota sąsiadują tylko z krawędzią, nie nadpisują siatki.
        saga_npc=f'v1500_{slug}_chronicler'
        saga_giver=f'Kronikarka {title}'
        put('NPCS',npcs,saga_npc,{
            'name':saga_giver, 'room':rid(slug,0,0),
            'dialogue':'Odkryj dziesięć rozdziałów naszej opowieści. Wpisz quest list i quest przyjmij.',
            'quest_chain':tuple(f'v1500_{slug}_saga_{i}' for i in range(1,11))})
        vendor=f'v1500_{slug}_merchant'
        put('NPCS',npcs,vendor,{'name':f'Kupiec Odkrywców {title}',
            'room':rid(slug,0,1),'shopkeeper':True,
            'dialogue':'Sprzedaj łupy i uzupełnij zapasy. Nie handluję przedmiotami za darmo.'})
        cm.catalog_assign(['healing_potion','mana_potion','soul_elixir','iron_guard'],'SHOPS',shops,(rid(slug,0,1),))
        shop_sellers[rid(slug,0,1)]=vendor
        encounter_ids=[]
        for index, boss_name in enumerate(boss_names):
            location=((index+1)%5, (2+index)%7+1)
            mob_id=f'v1500_{slug}_boss_{index+1}'
            template=boss_template(boss_name,level+index*38,element,material_id,ordinal=index+zone_index)
            template['quest_target']=mob_id
            put('MOB_TEMPLATES',mobs,mob_id,template)
            spawns.append((rid(slug,*location),mob_id))
            encounter_ids.append(mob_id)
        # 5 regularnych wrogów na krainę, z własnymi nazwami i nagrodami.
        for index, name in enumerate(('Zwiadowca Pogranicza','Strażnik Zapomnianego Traktu','Poszukiwacz Run',
                                    'Łowca Reliktów','Weteran Zaginionej Korony')):
            mob_id=f'v1500_{slug}_elite_{index+1}'
            put('MOB_TEMPLATES',mobs,mob_id,{
                'name':f'{name} — {title}', 'max_hp':(level+index*20)*850,
                'damage':(level+index*20)*36,'rank':'elite','damage_type':'magic' if index%2 else 'physical',
                'attack_elements_v11339':(element,), 'generator_level':min(800,level+index*22),
                'stat_reward':level*100,'class_xp_reward':level*1200,'soul_reward':level*430,
                'silver':level*260,'gold':0,'mithril':0,
                'drops':{material_id:.24,'soul_shard':.08},
                'stationary_mob':True,'auto_aggro':False,'v1500_forgotten_mob':True,
                'quest_target':mob_id,
            })
            spawns.append((rid(slug,0 if index%2==0 else 2,(index*2+1)%8),mob_id))
        for stage in range(1,11):
            index=(stage-1)//2
            is_boss=stage%2==0
            target=(encounter_ids[index] if is_boss else f'v1500_{slug}_elite_{index+1}')
            quest_id=f'v1500_{slug}_saga_{stage}'
            reward={material_id:1} if stage in (4,8) else ({trophy_id:1} if stage==10 else {})
            put('QUESTS',quests,quest_id,{
                'name':f'Saga Zapomnianych Światów — {title}, akt {stage}/10: {STORY_STAGES[stage-1][0]}',
                'giver':saga_giver,'kind':'kill','target':target,'needed':1,
                'description':f'{STORY_STAGES[stage-1][1]} {"Pokonaj władcę" if is_boss else "Pokonaj świadka"} '
                              f'{mobs[target]["name"]}. Wróć do kronikarki po nagrodę. Drużyna lub solo.',
                'reward_silver':(level*1800)+(stage*level*180),
                'reward_gold':0,'reward_mithril':0,'reward_items':reward,
                'repeatable':False,
                **({'requires_quest':f'v1500_{slug}_saga_{stage-1}'} if stage>1 else {}),
            })
        super_room=f'v1500_{slug}_super_room'
        put('ROOMS',rooms,super_room,{'name':f'Sanktuarium {super_name}',
          'zone':title,'desc':f'Ostatnia próba {title}. Przeciwnik zna wiele żywiołów, atakuje mocniej i pozostawia relikt.',
          'exits':{'north':rid(slug,4,7)},'recommended_mastery':min(800,level+180)})
        super_mob=f'v1500_{slug}_superboss'
        template=boss_template(super_name,level+220,element,trophy_id,superboss=True,ordinal=zone_index+1)
        template['quest_target']=super_mob
        put('MOB_TEMPLATES',mobs,super_mob,template)
        spawns.append((super_room,super_mob))
        put('QUESTS',quests,f'v1500_{slug}_legend',{
           'name':f'Legenda Zapomnianych Światów: {super_name}', 'giver':saga_giver,
           'kind':'kill','target':super_mob,'needed':1,
           'description':f'Pokonaj legendarnego władcę sanktuarium: {super_name}.',
           'reward_silver':level*9000, 'reward_gold':0,'reward_mithril':0,
           'reward_items':{trophy_id:1},'repeatable':True,'repeat_cooldown':10800,
           'requires_quest':f'v1500_{slug}_saga_10'})
        cm.catalog_assign(f'v1500_{slug}_legend','NPCS',npcs,(saga_npc,'quest'))
        for index in range(5):
            put('QUESTS',quests,f'v1500_{slug}_hunt_{index+1}',{
               'name':f'Kontrakt mistrzowski {title}: {boss_names[index]}',
               'giver':f'Łowczy {title}','kind':'kill', 'target':encounter_ids[index],
               'needed':1,'description':f'Pokonaj {boss_names[index]} i odbierz godną nagrodę.',
               'reward_silver':level*(450+index*90),'reward_gold':0,'reward_mithril':0,
               'repeatable':True,'repeat_cooldown':7200})
        put('NPCS',npcs,f'v1500_{slug}_hunter',{
          'name':f'Łowczy {title}','room':rid(slug,1,0),
          'dialogue':'Polowania mistrzowskie dla gracza solo i drużyny.',
          'quest_chain':tuple(f'v1500_{slug}_hunt_{i}' for i in range(1,6))})
    # Piąty superboss nie zależy od wcześniejszego ukończenia sagi.
    council='v1500_super_council'
    put('ROOMS',rooms,council,{
       'name':'Tron Czterech Wymiarów','zone':'Zapomniane Światy',
       'desc':'Na środku wielkiego kręgu spotykają się wszystkie żywioły. Nie ma losowych pułapek.',
       'exits':{'down':'v1500_gate'},'recommended_mastery':790})
    put('ITEMS',items,'v1500_council_heart',{'name':'Serce Czterech Wymiarów',
       'type':'material','rarity':'legendary','price':8000000,
       'desc':'Nagroda za pokonanie Strażnika Czterech Wymiarów.'})
    super_id='v1500_council_superboss'
    boss=boss_template('Strażnik Czterech Wymiarów',790,'arcane',
                       'v1500_council_heart',superboss=True,ordinal=4)
    boss['quest_target']=super_id
    put('MOB_TEMPLATES',mobs,super_id,boss)
    spawns.append((council,super_id))
    put('NPCS',npcs,'v1500_council_witness',{'name':'Świadek Czterech Światów','room':'v1500_gate',
        'dialogue':'Wspólny tron leży na górze. Wpisz quest list, aby przyjąć wyzwanie.',
        'quest':'v1500_council_quest'})
    put('QUESTS',quests,'v1500_council_quest',{'name':'Władca Czterech Światów',
       'giver':'Świadek Czterech Światów','kind':'kill','target':super_id,'needed':1,
       'description':'Zwycięż Strażnika Czterech Wymiarów na Tronie.',
       'reward_silver':12000000,'reward_gold':0,'reward_mithril':0,
       'reward_items':{'v1500_council_heart':1},'repeatable':True,'repeat_cooldown':14400})
    # Profesje 5.0. Wykorzystujemy liczniki prawdziwych akcji po przyjęciu zadania,
    # istniejącą persystencję i system EXP — żadnych stałych, fikcyjnych ukończeń.
    for index,(profession,tool,action) in enumerate(PROFESSIONS):
        slug,title,*_=REGIONS[index%4]
        npc_id=f'v1500_prof_npc_{index}'
        npc_name=f'Mistrz Ekspedycji {profession}'
        npc_room=rid(slug,1+(index//4),0)
        chain=[]
        for phase,(needed,xp,tool_xp,silver) in enumerate(((12,12000,6000,480000),
                                                            (24,30000,15500,1100000),
                                                            (40,65000,35000,2400000)),1):
            qid=f'v1500_prof_{index}_{phase}'
            put('QUESTS',quests,qid,{
              'name':f'Profesje 5.0 — {profession}: rozdział {phase}/3',
              'giver':npc_name,'kind':'profession_action','target':profession,'needed':needed,
              'description':f'Po przyjęciu wykonaj {needed} rzeczywistych akcji {profession}. {action}. '
                            'Nie liczą się wcześniejsze czynności.',
              'required_profession':profession,'specialist_tool_type':tool,
              'reward_profession':profession,'reward_profession_xp':xp,
              'reward_tool_type':tool,'reward_tool_xp':tool_xp,
              'reward_silver':silver,'reward_gold':0,'reward_mithril':0,
              'repeatable':True,'repeat_cooldown':7200,
            })
            chain.append(qid)
        put('NPCS',npcs,npc_id,{'name':npc_name,'room':npc_room,
            'dialogue':f'Trzy nowe próby {profession}, odnawialne co 2 godziny. '
                       'Wpisz quest list, aby przyjąć kontrakt.',
            'strict_profession_quests':profession,'specialist_quests':tuple(chain)})
    # Wyposażenie: autorskie 4 przedmioty craftowane po 2 razy w krainie; wysoka realna cena materiałów.
    # Tylko receptury obsługiwane przez wspólny silnik kuźni; bez syntetycznych itemów o losowych numerach.
    slots=('head','body','hands','necklace','feet','cloak')
    for region_index,(slug,title,*_) in enumerate(REGIONS):
        for form in range(6):
            item_id=f'v1500_{slug}_crafted_{form}'
            item_name=(f'{("Korona","Pancerz","Rękawice","Naszyjnik","Buty","Płaszcz")[form]} '
                       f'{title}')
            slot=slots[form]
            material=f'v1500_{slug}_material'
            put('ITEMS',items,item_id,{
              'name':item_name,'type':'armor','slot':slot,'rarity':'legendary',
              'defense':155+region_index*42+form*17,
              'stats':{'strength':240+region_index*70,'dexterity':240+region_index*70,
                      'intelligence':240+region_index*70,'willpower':240+region_index*70,
                      'constitution':275+region_index*80},
              'properties':{'max_hp_pct':4+region_index,'all_damage_pct':2+region_index},
              'price':None,'desc':f'Realne rzemiosło z materiałów {title}; można mieszać z innymi zestawami.'})
            put('CRAFT_RECIPES',CRAFT_RECIPES,item_id,{
              'name':item_name,'stations':('forge',),
              'ingredients':{material:2+(form%3), 'eternium_ingot':1+form%2,
                             'v12812_legendary_seal':1},
              'output':item_id,'quantity':1,'min_profession_level':180+region_index*30,
              'profession_xp':6000+region_index*2400,
              'tool_xp':3000+region_index*1000,
              'desc':f'Legendarny projekt z kontynentu {title}. Wszystkie składniki są zużywane.'})
    return {'rooms':167,'regional_bosses':20,'superbosses':5,
            'saga_quests':40,'profession_quests':42,'contracts':20,
            'craft_recipes':24,'professions':14}
