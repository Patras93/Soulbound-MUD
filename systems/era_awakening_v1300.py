# -*- coding: utf-8 -*-
"""Soulbound 1.30.0. Ręcznie opisane krainy, wojny, kontrakty i ekspedycje.

Żadnego Generator Core ani zmian schematu bazy. Wszystkie nagrody korzystają
z istniejących systemów walki, profesji, questów i reputacji.
"""
from __future__ import annotations
import hashlib
import re
import time
from data import catalog_mutations as cm

REGIONS = (
    ('deep', 'Podziemne Królestwo', 'Kamienne Serce', 'v12812_city_basalt_forge', 'north', 'south', 'miners', 'dark', 160,
     'Podziemne kuźnie, ogromne hale górnicze i dawno zapomniane przysięgi krasnoludzkich strażników.',
     'Tytan Bazaltowego Tronu', 'Mroczny Władca Przepastnych Kuźni'),
    ('sky', 'Podniebny Archipelag', 'Aeria', 'v12812_city_star_archive', 'east', 'west', 'cartographers', 'lightning', 280,
     'Wyspy zawieszone ponad chmurami, skrzydlate karawany i obrońcy szlaków powietrznych.',
     'Smok Siedmiu Burz', 'Król Burzowej Cytadeli'),
    ('lost', 'Zaginiony Kontynent', 'Valdoria', 'v12812_city_echo_forge', 'east', 'west', 'green_path', 'fire', 360,
     'Starożytne królestwo lasów, ruin, gorących źródeł i żywych kamiennych pomników.',
     'Lewiatan Zapomnianego Lądu', 'Wieczny Cesarz Valdorii'),
    ('orc', 'Kraina Orków', 'Gor-Khaz', 'v1300_lost_hamlet', 'north', 'south', 'green_path', 'earth', 420,
     'Ziemie wolnych klanów, kamiennych warowni, zgromadzeń wodzów i pieśni przodków.',
     'Gromokrwawy Wódz Graakh', 'Kragh, Król Czterech Klanów'),
)

# W każdym regionie 16 konkretnych pokojów z połączeniami (48 łącznie).
ROOMS_SPEC = (
 ('border','Szlak graniczny', 'Szlak prowadzi ku nowemu królestwu.', {'north':'gate'}),
 ('gate','Wielka Brama', 'Warta strzeże bezpiecznej drogi do stolicy.', {'south':'border','north':'square'}),
 ('square','Plac Stolicy', 'Słychać kupców, rzemieślników i gońców wojennych.', {'south':'gate','east':'market','west':'tavern','north':'hall'}),
 ('market','Targ Kupiecki', 'Karawany wymieniają towary z trzech krain.', {'west':'square','north':'workshop'}),
 ('workshop','Warsztat Mistrzów', 'Tutaj najlepsi rzemieślnicy pracują nad arcydziełami.', {'south':'market','east':'forge'}),
 ('forge','Kuźnia Przysięgi', 'Kowale obrabiają stopy z najgłębszych żył.', {'west':'workshop'}),
 ('tavern','Tawerna Podróżników', 'Najemnicy odpoczywają przed niebezpieczną wyprawą.', {'east':'square','west':'inn'}),
 ('inn','Gospoda Wędrowców', 'Bezpieczne miejsce na opowieści o ekspedycjach.', {'east':'tavern'}),
 ('hall','Sala Rady', 'Przywódcy dyskutują o losach państwa.', {'south':'square','west':'guild','east':'archive','north':'outer'}),
 ('guild','Dom Frakcji', 'Wyprawy i kontrakty obronne wspierają reputację.', {'east':'hall'}),
 ('archive','Biblioteka Starożytnych', 'Opisy nieznanych ruin i zapomnianych miejsc.', {'west':'hall','east':'observatory'}),
 ('outer','Droga do Rubieży', 'Patrole pilnują szlaku do dzikich prowincji.', {'south':'hall','east':'fields','west':'outpost','north':'citadel'}),
 ('fields','Dolina Odkrywców', 'Niezwykłe rośliny i rzadkie surowce kryją się w dolinie.', {'west':'outer','east':'hamlet','north':'shrine'}),
 ('outpost','Obóz Ekspedycji', 'Kapitan szykuje wyprawy bez granicy głębokości.', {'east':'outer','north':'passage'}),
 ('citadel','Cytadela Obrony', 'Tu odbywa się najtrudniejsza obrona miasta.', {'south':'outer','north':'throne'}),
 ('throne','Sala Superbossów', 'Słychać odgłos nieznanej siły i zbliżającego się starcia.', {'south':'citadel'}),
 ('hamlet','Wioska Wędrowców', 'Mieszkańcy opowiadają o niezwykłych odkryciach.', {'west':'fields','east':'craftsmen'}),
 ('craftsmen','Osada Rzemieślników', 'Rzemieślnicy gromadzą rzadkie materiały.', {'west':'hamlet'}),
 ('shrine','Ścieżka Sanktuarium', 'Stare kamienie wskazują drogę odkrywców.', {'south':'fields','north':'grove'}),
 ('grove','Dziki Gaj', 'Niespotykane rośliny rosną pomiędzy kolumnami.', {'south':'shrine'}),
 ('passage','Tajny Przesmyk', 'Bezpieczne przejście prowadzi do ruin.', {'south':'outpost','east':'ruins'}),
 ('ruins','Ruiny Starej Twierdzy', 'Kamienne znaki kryją historię dawnych wojen.', {'west':'passage','north':'vault'}),
 ('vault','Komnata Zapomnianych', 'Dawny skarbiec przechowuje legendy królestwa.', {'south':'ruins'}),
 ('observatory','Wieża Obserwacyjna', 'Badacze zapisują odległe gwiazdy i szlaki.', {'west':'archive'}),
)

# Orczy region ma własne opisy wszystkich 24 pomieszczeń, a nie kopię stolicy.
ORC_ROOM_NAMES_V1301 = {
 'border':('Kamienny Szlak Klanów','Od Valdorii wiedzie tędy droga pod orczymi sztandarami.'),
 'gate':('Brama Żelaznych Kłów','Dwaj orczy strażnicy pilnują wstępu, ale nie żądają przepustek.'),
 'square':('Plac Czterech Klanów','Bębny oznajmiają zgromadzenie klanów i wolny targ.'),
 'market':('Targ Zębów i Stali','Handlarze wymieniają rudę, skóry i ostrza bez pobierania opłaty za przejście.'),
 'workshop':('Warsztat Kościanych Run','Rytownicy zakuwają runy w orcze ozdoby i narzędzia.'),
 'forge':('Kuźnia Czerwonego Żaru','Pod ogromnymi miechami kuje się legendarne topory.'),
 'tavern':('Tawerna Złamanego Rogu','Weterani i najemnicy opowiadają o wyprawach do kanionów.'),
 'inn':('Gospoda Nocnego Bębna','Miejsca wystarcza dla wszystkich podróżnych, także spoza klanów.'),
 'hall':('Rada Czterech Klanów','Wodzowie wspólnie podejmują decyzje w sprawach wojny.'),
 'guild':('Siedziba Żelaznej Przysięgi','Posłańcy przyjmują kontrakty na obronę krainy.'),
 'archive':('Izba Kronik Przodków','Starszyzna zachowuje historie dawnych królów.'),
 'outer':('Trakt Spękanej Ziemi','Ścieżka rozdziela się na dzikie ziemie i fortecę.'),
 'fields':('Step Żelaznych Traw','W suchych trawach wędrują patrole i łowcy.'),
 'outpost':('Obóz Tropicieli','Wyprawy wyruszają na kolejne głębokości.'),
 'citadel':('Forteca Czarnego Rogu','Tu czeka wojenny czempion klanów.'),
 'throne':('Tron Czterech Klanów','Sala Kragha jest miejscem wielkiej próby siły.'),
 'hamlet':('Osada Wilczego Kła','Zwykłe orcze rodziny handlują i wyprawiają skóry.'),
 'craftsmen':('Osada Mistrzów Topora','Rzemieślnicy przechowują najlepsze receptury.'),
 'shrine':('Droga Kamieni Przodków','Pamiątkowe obeliski opowiadają o poległych.'),
 'grove':('Gaj Krwistych Dębów','Niezwykłe drzewa rosną pośród kamiennych głazów.'),
 'passage':('Wąwóz Nocnych Echa','Echo wojennych rogów prowadzi ku ruinom.'),
 'ruins':('Ruiny Pierwszej Hordy','Odkrywasz miejsce sprzed zjednoczenia czterech klanów.'),
 'vault':('Skarbiec Przodków','Kamienne wrota chronią pamiątki i rzadkie znaleziska.'),
 'observatory':('Wieża Dymnych Sygnałów','Strażnicy obserwują ruch na odległych szlakach.'),
}
ORC_ROOMS_SPEC_V1301 = tuple(
    (role, *ORC_ROOM_NAMES_V1301[role], links)
    for role, _, _, links in ROOMS_SPEC
)

SPECIAL_LOOT = {
 'v1300_deep_ore':('Ruda Królewskiego Bazaltu', 'Legendarny minerał z pradawnych podziemnych kuźni.', 'ore'),
 'v1300_sky_scale':('Łuska Podniebnego Smoka', 'Odnaleziona podczas burzowej ekspedycji.', 'fish'),
 'v1300_lost_wood':('Serce Żywego Kontynentu', 'Niezwykłe drewno prastarych drzew.', 'wood'),
 'v1300_ocean_fish':('Srebrna Ryba Nieba', 'Ryba z legendarnego połowu.', 'fish'),
 'v1300_ancient_herb':('Kwiat Długowiecznej Przysięgi', 'Roślina o nadzwyczajnych właściwościach.', 'herb'),
 'v1300_mystery_gem':('Klejnot Zapomnianej Korony', 'Niezwykły kamień na arcydzieła.', 'ore'),
 'v1301_orc_iron':('Żelazo Czterech Klanów','Orcza ruda do legendarnych wyrobów.', 'ore'),
}

def region_room(slug, role):
    return f'v1300_{slug}_{role}'

def market_factor_v1300(region, category, now=None):
    """Deterministyczne zapotrzebowanie miasta, stabilne przez sześć godzin."""
    slot=int((time.time() if now is None else float(now)) // 21600)
    digest=hashlib.sha256(f'soulbound1300:{region}:{category}:{slot}'.encode('utf8')).digest()
    return round(.88 + (digest[0]/255)*.42, 3)

def install_awakening_v1300(rooms, npcs, shops, mobs, spawns, quests, items, shop_sellers):
    from data.crafting_recipes import CRAFT_RECIPES
    for key,(name,desc,kind) in SPECIAL_LOOT.items():
        cm.catalog_assign({'name':name,'type':'material','price':2500000,
            'rarity':'legendary','rarity_name':'Legendarny','v1300_commodity':kind,
            'desc':desc}, 'ITEMS', items,(key,))
    for slug, title, city, parent, inbound, outbound, faction, element, level, description, guardian, monarch in REGIONS:
        # Tworzymy pokoje i dwukierunkowe przejścia przez wskazaną bramę.
        for role, name, detail, links in (ORC_ROOMS_SPEC_V1301 if slug == 'orc' else ROOMS_SPEC):
            exits={direction:region_room(slug,target) for direction,target in links.items()}
            if role=='border': exits[outbound]=parent
            cm.catalog_assign({'name':f'{name} — {city}', 'zone':title,
                'desc': f'{detail} {description}', 'exits':exits,
                'recommended_mastery':level,'v1300_region':slug,'v1300_location_role':role},
                'ROOMS', rooms,(region_room(slug,role),))
        if parent not in rooms: raise RuntimeError(f'Brak istniejącego wejścia do krainy: {parent}')
        parent_exits=rooms[parent].setdefault('exits',{})
        if inbound in parent_exits and parent_exits[inbound] != region_room(slug,'border'):
            raise RuntimeError(f'Zajęty kierunek krainy {title}: {parent}/{inbound}')
        cm.catalog_assign(region_room(slug,'border'), 'ROOMS', rooms,(parent,'exits',inbound))
        npc_defs = (
            ('guard', 'Strażniczka Bramy', 'gate', 'Stolica przyjmuje podróżników. Wojna nie blokuje przejścia.'),
            ('merchant', 'Kupiec Karawanowy', 'market', 'Sprawdź sklep oraz ofertę kontraktów miejskich.'),
            ('innkeeper', 'Karczmarka Wypraw', 'tavern', 'Tutaj najemników można wynająć przed wyprawą.'),
            ('smith', 'Mistrz Arcydzieł', 'forge', 'Legendarne materiały wykorzystasz w nowych recepturach.'),
            ('council', 'Namiestniczka Królestwa', 'hall', 'Broń stolicy i zdobywaj reputację frakcji.'),
            ('faction', 'Przedstawiciel Frakcji', 'guild', 'Wojenne kontrakty są dostępne także solo.'),
            ('archivist', 'Kronikarka Starożytnych', 'archive', 'Odkrywaj historię i zdobywaj receptury.'),
            ('expedition', 'Kapitan Ekspedycji', 'outpost', 'Wyprawy nie mają ostatniego piętra.'),
        )
        if slug == 'orc':
            npc_defs = (
                ('guard', 'Wartowniczka Khara', 'gate','Wolne klany przyjmują wędrowców bez blokad.'),
                ('merchant','Kupiec Durgan','market','Ruda i wyroby z kanionów mają swoją cenę.'),
                ('innkeeper','Karczmarka Ursha','tavern','Najemnicy czterech klanów są gotowi do walki.'),
                ('smith','Kowal Brog','forge','Przynieś rzadkie materiały na arcydzieło.'),
                ('council','Wódz Ghar','hall','Obrona ojczyzny łączy nasze klany.'),
                ('faction','Posłanka Varka','guild','Zlecenia wojenne są otwarte również dla samotnych.'),
                ('archivist','Kronikarka Mogha','archive','Poznaj pradawną opowieść o zjednoczeniu klanów.'),
                ('expedition','Tropiciel Grum','outpost','Żadna głębokość nie jest ostatnia.'),
            )
        for key, role_name, role, dialogue in npc_defs:
            ident=f'v1300_{slug}_{key}'
            data={'name':f'{role_name} {city}', 'room':region_room(slug,role), 'dialogue':dialogue}
            if key=='merchant': data['shopkeeper']=True
            if key=='smith': data['rank_profession']='Kowalstwo'
            if key=='faction': data['quest']=f'v1300_{slug}_defense'
            if key=='expedition': data['quest']=f'v1300_{slug}_expedition'
            if key=='archivist': data['quest_chain']=tuple(f'v1300_{slug}_saga_{i}' for i in range(1,4))
            if key=='council': data['quest']=f'v1300_{slug}_defense'
            if key=='merchant': data['quest']=f'v1300_{slug}_contract'
            cm.catalog_assign(data, 'NPCS', npcs,(ident,))
        shops[region_room(slug,'market')]=['healing_potion','iron_guard','lucky_charm','soul_elixir']
        shop_sellers[region_room(slug,'market')]=f'v1300_{slug}_merchant'
        for role,boss_name,rank in [('citadel',guardian,'boss'),('throne',monarch,'world_boss')]:
            key=f'v1300_{slug}_{role}_boss'
            template={'name': boss_name, 'max_hp': max(120000,level*1800*(2 if role=='throne' else 1)),
                'damage':max(1500,level*50), 'damage_type':'magic' if slug=='sky' else 'physical',
                'attack_elements_v11339':(element,), 'generator_level':level,
                'boss':True, 'world_boss':rank=='world_boss','rank':rank,
                'boss_mechanic':'elemental_overdrive',
                'boss_mechanic_text':f'{boss_name}: wielofazowy przeciwnik. Zmienia styl ataków i przywołuje pomocników bez limitu.',
                'stat_reward':level*200,'class_xp_reward':level*4000,'soul_reward':level*1600,
                'silver':level*400,'gold':0,'mithril':0,
                'drops':{'soul_shard':1.0,{'deep':'v1300_deep_ore','sky':'v1300_sky_scale','lost':'v1300_lost_wood','orc':'v1301_orc_iron'}[slug]:.13,
                         'v12812_legendary_seal':.27},
                'stationary_mob':True, 'auto_aggro':False,'v1300_boss':True}
            cm.catalog_assign(template,'MOB_TEMPLATES',mobs,(key,))
            pair=(region_room(slug,role),key)
            if pair not in spawns:spawns.append(pair)
        war_key=f'v1300_{slug}_war_event'
        cm.catalog_assign({'name':f'Wódz Inwazji na {city}',
            'boss':True,'world_boss':True,'rank':'world_boss',
            'max_hp':max(100000,level*2800),'damage':max(1300,level*58),
            'damage_type':'magic' if slug=='sky' else 'physical',
            'attack_elements_v11339':(element,), 'generator_level':level+25,
            'stat_reward':level*340,'class_xp_reward':level*4200,
            'soul_reward':level*1900,'silver':level*460,'gold':0,'mithril':0,
            'drops':{'soul_shard':1.0,'v12812_legendary_seal':.2},
            'boss_mechanic':'elemental_overdrive',
            'boss_mechanic_text':'Wojna królestw: dowódca używa wielu faz i przywołuje pomocników.',
            'stationary_mob':True,'auto_aggro':False,'v1300_war_event':True},
            'MOB_TEMPLATES',mobs,(war_key,))
        defense=f'v1300_{slug}_citadel_boss' 
        superboss=f'v1300_{slug}_throne_boss'
        material={'deep':'iron_ore','sky':'salmon','lost':'oak_log','orc':'iron_ore'}[slug]
        profession={'deep':'Górnictwo','sky':'Wędkarstwo','lost':'Drwalstwo','orc':'Górnictwo'}[slug]
        tool={'deep':'mining','sky':'fishing','lost':'woodcutting','orc':'mining'}[slug]
        for kind,quest in {
          'defense':{'name':f'Wojna Królestw: Obrona {city}', 'giver':(f'Posłanka Varka {city}' if slug == 'orc' else f'Przedstawiciel Frakcji {city}'),
                     'kind':'kill','target':defense,'needed':1,'description':f'Obroń {city} przed legendarnym najeźdźcą.',
                     'reward_silver':level*320,'reward_gold':0,'reward_mithril':0,
                     'reward_faction_v016':faction,'reward_faction_amount_v016':12,
                     'reward_city_v0710':city,'reward_city_amount_v0710':8,
                     'repeatable':True,'repeat_cooldown':7200},
          'expedition':{'name':f'Ekspedycja bez granic: {city}', 'giver':(f'Tropiciel Grum {city}' if slug == 'orc' else f'Kapitan Ekspedycji {city}'),
                        'kind':'kill','target':superboss,'needed':1,
                        'description':f'Pokonaj {monarch} i ruszaj dalej w nieskończone lochy.',
                        'reward_silver':level*450,'reward_gold':0,'reward_mithril':0,
                        'reward_items':{'v12812_legendary_seal':1},'reward_faction_v016':faction,
                        'reward_faction_amount_v016':18,'repeatable':True,'repeat_cooldown':10800},
          'contract':{'name':f'Żywa Gospodarka: Kontrakt {city}', 'giver':(f'Kupiec Durgan {city}' if slug == 'orc' else f'Kupiec Karawanowy {city}'),
                       'kind':'collect_resource','target':material,'needed':8,
                       'description':f'Dostarcz 8 jednostek {material}. Zapotrzebowanie rynku zmienia cenę co 6 godzin.',
                       'reward_silver':level*160,'reward_gold':0,'reward_mithril':0,
                       'reward_profession':profession,'reward_profession_xp':level*180,
                       'reward_tool_type':tool,'reward_tool_xp':level*60,
                       'reward_faction_v016':faction,'reward_faction_amount_v016':5,
                       'v1300_market_contract':slug, 'v1300_market_category':{'deep':'ore','sky':'fish','lost':'wood','orc':'ore'}[slug],
                       'repeatable':True,'repeat_cooldown':21600},
        }.items(): cm.catalog_assign(quest,'QUESTS',quests,(f'v1300_{slug}_{kind}',))
        chain=((f'Poznaj granice {city}', 'kill',defense,1),
               (f'Skarby odległych krain {city}','collect_resource',material,5),
               (f'Powstrzymaj Przebudzenie {city}','kill',superboss,1))
        for i,(quest_name,kind,target,needed) in enumerate(chain,1):
            quest={'name':f'Era Przebudzenia {city} {i}/3: {quest_name}',
                   'giver':(f'Kronikarka Mogha {city}' if slug == 'orc' else f'Kronikarka Starożytnych {city}'), 'kind':kind,'target':target,'needed':needed,
                   'description':f'Wielka saga: {quest_name}. Wyprawa dostępna solo albo w drużynie.',
                   'reward_silver':level*220*i,'reward_gold':0,'reward_mithril':0,
                   'reward_faction_v016':faction,'reward_faction_amount_v016':10*i,
                   'repeatable':False,
                   'reward_items':{'v1300_awakened_emblem':1} if i==3 else {}}
            if i>1: quest['requires_quest']=f'v1300_{slug}_saga_{i-1}'
            cm.catalog_assign(quest,'QUESTS',quests,(f'v1300_{slug}_saga_{i}',))
    # Nieagresywne spotkania z orczymi patrolami i ważnymi przeciwnikami.
    for role, suffix, name, scale in (
      ('fields','scout','Zwiadowca Stepów Gor-Khaz',1),
      ('ruins','ancestor','Cień Pierwszej Hordy',2),
      ('grove','shaman','Szaman Krwistych Dębów',2),
      ('vault','keeper','Strażnik Skarbca Przodków',3),
    ):
        key=f'v1301_orc_{suffix}'
        cm.catalog_assign({'name':name,'max_hp':220000*scale,'damage':9500*scale,
           'damage_type':'magic' if suffix=='shaman' else 'physical',
           'generator_level':420,'stationary_mob':True,'auto_aggro':False,
           'boss':suffix=='keeper', 'rank':'boss' if suffix=='keeper' else 'elite',
           'silver':100000*scale,'gold':0,'mithril':0,
           'source_xp':300000*scale,'drops':{'v1301_orc_iron':.06*scale}},
           'MOB_TEMPLATES',mobs,(key,))
        spawns.append((region_room('orc',role),key))
    cm.catalog_assign({'name':'Emblemat Ery Przebudzenia','type':'armor','slot':'necklace',
      'defense':320,'stats':{'strength':450,'intelligence':450,'constitution':450,'willpower':400},
      'properties':{'all_damage_pct':6,'max_hp_pct':8},'rarity':'legendary', 'price':None,
      'desc':'Trofeum za serię prób z jednej z czterech nowych krain.'},'ITEMS',items,('v1300_awakened_emblem',))
    # Istniejąca kuźnia i narzędzia: nowe receptury wykorzystują autentyczne materiały.
    for slug, name, resource in (
      ('deep','Runiczna Korona Królestwa','v1300_deep_ore'),
      ('sky','Korona Siedmiu Burz','v1300_sky_scale'),
      ('lost','Korona Wiecznych Korzeni','v1300_lost_wood'),
      ('orc','Korona Czterech Klanów','v1301_orc_iron'),
    ):
        item_id=f'v1300_crown_{slug}'
        cm.catalog_assign({'name':name,'type':'armor','slot':'head','rarity':'legendary',
            'defense':180,'stats':{'strength':280,'intelligence':280,'constitution':280,'willpower':250},
            'properties':{'max_hp_pct':5},'price':None,'desc':'Ręcznie zaprojektowany legendarny przedmiot z materiałów krain.'},
            'ITEMS',items,(item_id,))
        cm.catalog_assign({'name':name,'stations':('forge',),
            'ingredients':{resource:2,'eternium_ingot':2,'v12812_legendary_seal':1},
            'output':item_id,'quantity':1,'min_profession_level':170,'min_tool_level':100,
            'profession_xp':6500,'tool_xp':3600,'desc':f'Wykonaj {name} z legendarnych materiałów.'},
            'CRAFT_RECIPES',CRAFT_RECIPES,(item_id,))

WAR_WINDOW_SECONDS_V1300 = 3 * 60 * 60

def active_kingdom_war_v1300(now=None):
    """Jeden aktywny front co 3 godziny; zwykłe miasta są zawsze dostępne."""
    moment=time.time() if now is None else float(now)
    slot=int(moment // WAR_WINDOW_SECONDS_V1300)
    slug,title,city,*_ = REGIONS[slot%len(REGIONS)]
    return {'slot':slot,'city':city,'region':slug,'room_id':region_room(slug,'gate'),
            'template_id':f'v1300_{slug}_war_event',
            'expires_at':float((slot+1)*WAR_WINDOW_SECONDS_V1300)}

# Ekspedycja przy każdej setnej głębokości jest dokładana LENIWIE podczas
# wejścia na piętro. Nie generuje milionów pokojów na starcie serwera.
EXPEDITION_FLOORS = re.compile(r'^(crypt_floor_|mythic_crypt_floor_|astral_floor_|mythic_astral_floor_|uoss_deep_dungeon_floor_)(\d+)(?:_v11331)?$')

def attach_expedition_v1300(parent, rooms, mobs, spawns):
    match=EXPEDITION_FLOORS.fullmatch(str(parent))
    if not match:return False
    floor=int(match.group(2))
    if floor<100 or floor%100:return False
    entrance=rooms.get(parent)
    if not entrance:return False
    direction=next((d for d in ('east','west','north','south') if d not in entrance.get('exits',{})),None)
    if direction is None:return False
    reverse={'east':'west','west':'east','north':'south','south':'north'}[direction]
    camp=f'v1300_camp_{match.group(1)}{floor}'
    arena=f'v1300_sanctum_{match.group(1)}{floor}'
    boss=f'v1300_expedition_{match.group(1)}{floor}'
    if camp in rooms:return True
    cm.catalog_assign({'name':f'Obóz Wyprawy — piętro {floor}','zone':'Ekspedycje bez końca',
       'desc':'Bezpieczny obóz badaczy z wejściem do sali dawnego strażnika. Bez pułapek.',
       'exits':{reverse:parent,'north':arena}, 'recommended_mastery':floor,
       'v1300_expedition_floor':floor},'ROOMS',rooms,(camp,))
    cm.catalog_assign({'name':f'Sanktuarium Głębin — piętro {floor}', 'zone':'Ekspedycje bez końca',
       'desc':'Ukryta sala z niezwykle potężnym przeciwnikiem i rzadką zdobyczą.',
       'exits':{'south':camp},'recommended_mastery':floor,'v1300_expedition_floor':floor},'ROOMS',rooms,(arena,))
    cm.catalog_assign(camp,'ROOMS',rooms,(parent,'exits',direction))
    cm.catalog_assign({'name':f'Strażnik Odkryć {floor}','max_hp':max(5000,floor*170),
        'damage':max(300,floor*15),'boss':True,'rank':'boss','generator_level':min(800,floor),
        'class_xp_reward':floor*100,'soul_reward':floor*80,'stat_reward':floor*10,
        'silver':floor*30,'gold':0,'mithril':0,
        'drops':{'soul_shard':1.0,'v12812_legendary_seal':.10},
        'boss_mechanic':'elemental_overdrive','stationary_mob':True,'auto_aggro':False,
        'v1300_expedition':True},'MOB_TEMPLATES',mobs,(boss,))
    spawns.append((arena,boss))
    return True
