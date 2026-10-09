# -*- coding: utf-8 -*-
"""Authored v1.28.12 content: underground city routes, NPCs and one-time quest chain.

No Generator Core, procedural item names or save-schema changes. Travel uses
normal directions and the existing solo/party move rules.
"""
from __future__ import annotations
from data import catalog_mutations as mutations

CITIES = (
    ('basalt', 'Bazaltowy Azyl', 'crypt_floor_50', 50, 'Krypta Nieskończona'),
    ('echo', 'Miasto Echa', 'crypt_floor_100', 100, 'Krypta Nieskończona'),
    ('star', 'Gwiezdna Enklawa', 'crypt_floor_200', 200, 'Krypta Nieskończona'),
    ('myth', 'Mityczne Sanktuarium', 'mythic_crypt_floor_100', 100, 'Mityczna Krypta'),
)
CITY_ROLES = {
    'gate': ('Brama', 'Kamienne wrota i wartownia prowadzą z powrotem na to samo piętro krypty.'),
    'square': ('Plac', 'Podziemne lampy oświetlają plac, przez który przechodzą kupcy i podróżnicy.'),
    'market': ('Targ', 'Na stoiskach sprzedawane są mikstury i wyposażenie przydatne podczas wypraw.'),
    'tavern': ('Tawerna', 'Przy ognisku odpoczywają wędrowcy, najemnicy i poszukiwacze legend.'),
    'forge': ('Kuźnia', 'Pracownia mistrza słynącego z obróbki trudnych materiałów.'),
    'archive': ('Archiwum', 'Kroniki opisują wyprawy przez morza, kopalnie i odległe lochy.'),
    'arena': ('Arena', 'Groźny strażnik miasta czuwa nad zapieczętowanym dziedzictwem.'),
}

def city_room_id(slug, role):
    return f'v12812_city_{slug}_{role}'


def install_cities_v12812(rooms, npcs, shops, mobs, spawns, quests, items, shop_sellers):
    """Idempotent; register after the prebuilt crypt catalog exists."""
    for slug, title, parent, floor, zone in CITIES:
        # Dynamic crypt floors are instantiated lazily after entering them.
        # Reserve a route here, but attach the entrance when the floor appears.
        direction, reverse = 'east', 'west' 
        links = {
            'gate': {reverse: parent, 'north': 'square'},
            'square': {'south':'gate','east':'market','west':'tavern','north':'archive'},
            'market': {'west':'square','north':'forge'},
            'forge': {'south':'market'},
            'tavern': {'east':'square'},
            'archive': {'south':'square','north':'arena'},
            'arena': {'south':'archive'},
        }
        # Use a north->square entry for all four city gates, returning in reverse.
        for role, (label, desc) in CITY_ROLES.items():
            exits = {d: city_room_id(slug, r) for d,r in links[role].items() if d != reverse or role != 'gate'}
            if role == 'gate': exits[reverse] = parent
            room_id = city_room_id(slug, role)
            mutations.catalog_assign({
                'name': f'{label} — {title}', 'zone': title,
                'desc': f'{desc} {title}, połączone z piętrem {floor} {zone}. '
                        'Bez pułapek i teleportów omijających bossa.',
                'exits': exits, 'recommended_mastery': floor,
                'v12812_underground_city': slug,
            }, 'ROOMS', rooms, (room_id,))
        if parent in rooms: attach_city_v12812(parent, rooms)
        trader = f'v12812_merchant_{slug}'
        keeper = f'v12812_innkeeper_{slug}'
        smith = f'v12812_smith_{slug}'
        historian = f'v12812_historian_{slug}'
        for id, name, role, dialogue in (
            (trader, f'Kupiec {title}', 'market', 'Mój sklep ma wyposażenie na dalszą drogę. Wpisz sklep.'),
            (keeper, f'Karczmarka {title}', 'tavern', 'Opowiem ci o szlaku w głąb krypty i o jej strażnikach.'),
            (smith, f'Mistrz Kuźni {title}', 'forge', 'Im lepszy materiał, narzędzie i doświadczenie, tym większa szansa na arcydzieło.'),
            (historian, f'Archiwistka {title}', 'archive', 'Posłuchaj kroniki wypraw. Wpisz quest list, aby poznać wielki łańcuch.'),
        ):
            npc = {'name':name, 'room':city_room_id(slug,role), 'dialogue':dialogue}
            if role == 'market': npc['shopkeeper'] = True
            if role == 'forge':
                npc['rank_profession']='Kowalstwo'
                npc['teacher_class']={'basalt':'Wojownik', 'echo':'Mag',
                                      'star':'Inżynier', 'myth':'Nekromanta'}[slug]
            if role == 'archive':
                npc['quest'] = f'v12812_city_task_{slug}'
                if slug == 'basalt':
                    npc['quest_chain'] = tuple(f'v12812_saga_{i}' for i in range(1,7))
            mutations.catalog_assign(npc, 'NPCS', npcs, (id,))
        market_id = city_room_id(slug,'market')
        shops[market_id] = ['healing_potion','iron_guard','iron_helmet','lucky_charm']
        shop_sellers[market_id] = trader
        boss_id = f'v12812_city_guardian_{slug}'
        # These are real combat templates: kill, corpse, full party credit and drops.
        mutations.catalog_assign({
            'name':f'Strażnik Przysięgi {title}', 'boss':True, 'rank':'boss',
            'max_hp': max(3000,floor*130), 'damage':max(100,floor*11),
            'damage_type':'magic' if slug in ('echo','myth') else 'physical',
            'generator_level': floor, 'stat_reward': floor*110,
            'class_xp_reward':floor*2900, 'soul_reward':floor*950,
            'silver':floor*200 + max(1,floor//20)*100, 'gold':0, 'mithril':0,
            'quest_target':boss_id, 'quest_targets':(boss_id,),
            'drops': {'soul_shard':1.0, 'v12812_legendary_seal': .18},
            'boss_mechanic':'elemental_overdrive',
            'boss_mechanic_text':'Zmienia fazy i przyzywa pomocników bez limitu liczby żywych strażników.',
            'stationary_mob':True, 'auto_aggro':False,
            'v12812_city_boss':slug,
        }, 'MOB_TEMPLATES', mobs, (boss_id,))
        pair = (city_room_id(slug,'arena'), boss_id)
        if pair not in spawns: spawns.append(pair)
        # The archivist in EACH city gives its own genuine, repeatable
        # quest. The large inter-region saga starts in the Basalt archive.
        mutations.catalog_assign({
            'name':f'Warta Podziemi: {title}', 'giver': f'Archiwistka {title}',
            'kind':'kill', 'target':boss_id, 'needed':1,
            'description':f'Pokonaj strażnika areny miasta {title}. Klucz i skrzynia bossa działają niezależnie.',
            'reward_silver':floor*120, 'reward_gold':0,'reward_mithril':0,
            'repeatable':True, 'repeat_cooldown':7200,
        },'QUESTS',quests,(f'v12812_city_task_{slug}',))

    # Four genuine event bosses, each spawned only during its three-hour window.
    from systems.world_events_v12812 import EVENTS
    for slug, title, name, style, element in EVENTS:
        floor = next(f for cid, _name, _parent, f, _zone in CITIES if cid == slug)
        boss_id = f'v12812_event_{slug}'
        mutations.catalog_assign({
            'name':name, 'boss':True, 'world_boss':True, 'rank':'world_boss',
            'max_hp':max(9000, floor*800), 'damage':max(350,floor*38),
            'damage_type':style,'attack_elements_v11339':(element,),
            'generator_level':floor+80, 'silver':floor*900,'gold':0,'mithril':0,
            'stat_reward':floor*330, 'class_xp_reward':floor*5300,
            'soul_reward':floor*2500,'quest_target':boss_id,
            'quest_targets':(boss_id,), 'drops':{
                'soul_shard':1.0, 'v12812_legendary_seal':.28,
                'v12812_mythic_heart':.04},
            'boss_mechanic':'elemental_overdrive',
            'boss_mechanic_text':f'Rotujący boss wydarzenia {title}. Przywołuje strażników i atakuje żywiołem {element}.',
            'stationary_mob':True,'auto_aggro':False,'v12812_world_event':True,
        },'MOB_TEMPLATES',mobs,(boss_id,))

    # Single one-time 6-stage saga shared by all archivists; quests follow
    # real targets from crypt, archipelago, ocean, professions and mythic crypt.
    steps = (
      ('Pieczęć Podziemnego Miasta', 'kill','v12812_city_guardian_basalt',1,'Wygraj walkę na arenie Bazaltowego Azylu (Krypta, piętro 50).'),
      ('Wyprawa na Wyspy', 'kill','mist_pirate',1,'Pokonaj wroga Archipelagu. Jeśli nie ma tego gatunku, wybierz quest info i sprawdź lokację.'),
      ('Głębia Oceanu', 'kill','v1000_reef_guardian',2,'Dopłyń na Ocean 2.0 i pokonaj strażników podwodnych ruin Rafy.'),
      ('Dar Górnika', 'collect','iron_ore',8,'Wydobądź osiem jednostek rudy żelaza; policzy się rzeczywisty posiadany urobek.'),
      ('Krypta Setnego Piętra', 'kill','crypt_boss_100',1,'Pokonaj bossa Krypty na piętrze 100.'),
      ('Ostatnia Pieczęć Mityczna', 'kill','v12812_city_guardian_myth',1,'Pokonaj strażnika areny Mitycznego Sanktuarium.'),
    )
    for i,(name,kind,target,needed,desc) in enumerate(steps,1):
        quest = {
            'name': f'Kronika Podziemi {i}/6: {name}',
            'giver': 'Archiwistka Bazaltowy Azyl',
            'kind':kind,'target':target,'needed':needed,'description':desc,
            'reward_silver':2000*i,'reward_gold':0,'reward_mithril':0,
            'reward_items': {'v12812_chronicle_medallion':1} if i==6 else {'v12812_legendary_seal':1} if i==3 else {},
            'repeatable':False,
        }
        if i>1: quest['requires_quest'] = f'v12812_saga_{i-1}'
        mutations.catalog_assign(quest,'QUESTS', quests,(f'v12812_saga_{i}',))


def register_rewards_v12812(items):
    for key, data in {
        'v12812_legendary_seal': {'name':'Pieczęć Pradawnych Legend','type':'material',
            'rarity':'legendary','price':980000,'currency':'silver',
            'desc':'Bardzo rzadki materiał z legendarnych przeciwników i strażników miast. Można sprzedać lub zachować.'},
        'v12812_mythic_heart': {'name':'Serce Mitycznej Bestii','type':'material',
            'rarity':'mythic','price':3500000,'currency':'silver',
            'desc':'Unikatowe trofeum pochodzące z mitycznych odmian zwykłych potworów.'},
        'v12812_chronicle_medallion': {'name':'Medalion Strażnika Kroniki','type':'armor','slot':'necklace',
            'defense':260, 'stats':{'strength':320,'intelligence':320,'constitution':320,'willpower':260},
            'properties':{'all_damage_pct':5,'max_hp_pct':7},'rarity':'legendary','price':None,
            'desc':'Niepowtarzalna nagroda za sześć etapów Kroniki Podziemi. Wybór klasy nie blokuje użycia.'},
    }.items():
        mutations.catalog_assign(data,'ITEMS',items,(key,))


def attach_city_v12812(parent, rooms):
    """Attach an entrance when the canonical lazy crypt floor actually exists."""
    for slug, title, floor_room, floor, zone in CITIES:
        if parent != floor_room or parent not in rooms: continue
        exits=rooms[parent].setdefault('exits', {})
        if any(v == city_room_id(slug,'gate') for v in exits.values()): return True
        direction=next((d for d in ('east','west','north','south') if d not in exits), None)
        if direction is None: return False
        backwards={'east':'west','west':'east','north':'south','south':'north'}[direction]
        gate=rooms[city_room_id(slug,'gate')]
        # Gate north leads to square; don't overwrite it even if floor's only
        # free direction points south.
        if backwards == 'north': return False
        gate['exits'].pop('west', None)
        gate['exits'][backwards]=parent
        mutations.catalog_assign(city_room_id(slug,'gate'), 'ROOMS',rooms,(parent,'exits',direction))
        return True
    return False
