# -*- coding: utf-8 -*-
"""v7.00.0 living empire: additive authored materials, stories and cross-craft economy.

No historical quest, map, NPC, shop or character row is overwritten. All rewards
are independent of XP-to-next-level formulas. No new profession or tool is added.
"""
from __future__ import annotations
from dataclasses import dataclass
from systems.new_professions import PROFESSIONS, TIERS
from systems.profession_paths_v601 import SPEC as V601_MENTORS
from systems.npc_single_room_v3101 import OPPOSITE
from data.catalog_mutations import catalog_assign

# Old and v6 profession outputs are consumed rather than replaced by a parallel
# gathering engine. Extra goods are earned only by executing actual jobs.
NEW_GOODS = {
    'v700_harvest_seal': ('Pieczęć Zbiorów', 'Potwierdzenie dostaw żywności do wspólnoty.'),
    'v700_herd_seal': ('Pieczęć Hodowcy', 'Dokument jakości hodowli.'),
    'v700_building_seal': ('Pieczęć Budowniczego', 'Potwierdzenie wkładu w budowle.'),
    'v700_engineering_seal': ('Pieczęć Konstruktorów', 'Certyfikat działania urządzenia.'),
    'v700_ocean_seal': ('Pieczęć Wyprawy', 'Dokument dostarczonej ekspedycji.'),
    'v700_hunt_seal': ('Trofeum Legendarnych Tropicieli', 'Trofeum z pracochłonnego polowania.'),
    'v700_trade_seal': ('List Przewozowy Imperium', 'Dowód zrealizowanego kontraktu handlowego.'),
    'v700_story_seal': ('Pieczęć Kroniki Imperium', 'Nagroda za służbę opisaną w kronice.'),
}

# Upgrade levels persist per character. Each level takes additional genuine
# products of existing professions; no free item generators or random timers.
UPGRADES = {
    'pole': ('Rolnictwo', 'field', (('field_grain', 3), ('stone_blocks', 1)), 'v700_harvest_seal'),
    'stado': ('Hodowla zwierząt', 'pasture', (('field_grain', 4), ('farm_wool', 2)), 'v700_herd_seal'),
    'warsztat': ('Inżynieria', 'workshop', (('machine_gears', 3), ('iron_ingot', 2)), 'v700_engineering_seal'),
    'magazyn': ('Murarstwo', 'construction', (('stone_blocks', 4), ('oak_plank', 2)), 'v700_building_seal'),
    'stocznia': ('Okrętownictwo', 'harbor', (('ship_parts', 4), ('v600_ship_gear', 1)), 'v700_building_seal'),
    'mury': ('Murarstwo', 'construction', (('stone_blocks', 5), ('v600_foundation', 1)), 'v700_building_seal'),
    'latarnia': ('Inżynieria', 'harbor', (('v600_nav_kit', 2), ('v600_mechanism', 1)), 'v700_engineering_seal'),
    'twierdza': ('Murarstwo', 'construction', (('stone_blocks', 6), ('v600_masonry_support', 2)), 'v700_building_seal'),
}

# Tiers are required BOTH for profession and instrument. Costs rise by stage,
# and the direct action XP grows separately from the level-requirement curve.
MISSION_TYPES = {
    'inżynieria': ('Inżynieria','workshop',(('machine_gears',3),('v600_masonry_support',1)),
                  'v700_engineering_seal',145),
    'rolnictwo': ('Rolnictwo','field',(('field_grain',4),('v600_flour',1)),
                  'v700_harvest_seal',90),
    'hodowla': ('Hodowla zwierząt','pasture',(('farm_wool',3),('v600_milk',1)),
                  'v700_herd_seal',105),
}
VOYAGES = {
    'rafa': (1, 'Rafy Szeptów', 180, (('navigation_chart',2),('v600_hull_repair',1))),
    'stolica': (75, 'Zatopiona Stolica', 240, (('navigation_chart',3),('v600_ship_gear',1))),
    'burze': (300, 'Archipelag Wiecznych Burz', 300, (('navigation_chart',4),('v600_nav_kit',2))),
    'row': (500, 'Rów Lewiatana', 360, (('navigation_chart',5),('v600_mechanism',2))),
}
CARAVANS = {
    'rynek': (1, 'Rynek Dusz', 'market', (('trade_crate',2),('field_grain',3)), 150),
    'port': (75, 'Port Nieznanych Mórz', 'harbor', (('trade_crate',3),('ship_parts',2)), 210),
    'kuźnia': (150, 'Kuźnia Pradawnych', 'forge', (('trade_crate',3),('iron_ingot',3)), 250),
    'targ': (300, 'Targ Rybny', 'fish_market', (('trade_crate',4),('farm_wool',3)), 290),
}

# Mastery contracts for all 22, using original profession outputs; not a 23rd
# profession or specialisation which could overwrite previous level 1-800.
MASTER_INPUT = {
    'Wędkarstwo':'navigation_chart', 'Górnictwo':'iron_ore',
    'Drwalstwo':'oak_plank', 'Zielarstwo':'mint',
    'Gotowanie':'v600_field_bread', 'Alchemia':'mint',
    'Kowalstwo':'iron_ingot', 'Jubilerstwo':'silver_ingot',
    'Krawiectwo':'v600_yarn', 'Garbarstwo':'v600_hunting_hide',
    'Stolarstwo':'oak_plank', 'Zaklinanie':'v600_mechanism',
    'Archeologia':'stone_chunk', 'Kartografia':'navigation_chart',
    'Łowiectwo':'v600_hunting_hide','Rolnictwo':'field_grain',
    'Hodowla zwierząt':'farm_wool','Okrętownictwo':'ship_parts',
    'Murarstwo':'stone_blocks','Inżynieria':'machine_gears',
    'Kupiectwo':'trade_crate','Żeglarstwo':'navigation_chart',
}

# Great story 2.0: real native, sequential, profession-action quests in eight
# existing regions, offered by eight NEW NPCs in private accessible side rooms.
STORY = (
    ('Łowiectwo','meadow','Szept Kniei','Włóczniczka Kronik Neria', 'Ocalenie szlaków łowieckich'),
    ('Rolnictwo','mint_meadow','Głosy Ziemi','Kronikarz Pól Ravel', 'Przebudzenie pól'),
    ('Hodowla zwierząt','lakeside_meadow','Przysięga Stad','Hodowczyni Kronik Brena','Ochrona stad'),
    ('Murarstwo','forge','Kamień Przymierza','Mistrz Kronik Malvor','Odbudowa murów'),
    ('Inżynieria','market','Serce Maszyn','Konstruktorka Kronik Vessa','Naprawa mechanizmów'),
    ('Okrętownictwo','harbor','Przysięga Żagli','Szkutniczka Kronik Irsa','Przygotowanie armady'),
    ('Żeglarstwo','sea_pier','Pieśń Oceanów','Kapitan Kronik Relven','Wyprawy ku głębinom'),
    ('Kupiectwo','fish_market','Pokój Miast','Kupczyni Kronik Elana','Dostawy między krainami'),
)
STORY_IDS = []


def _add(catalog, title, key, value):
    if key in catalog:
        raise RuntimeError('v7.00.0 catalog collision '+title+': '+key)
    catalog_assign(value,title,catalog,(key,))


def _attach(rooms, start, dest):
    if start not in rooms:
        raise RuntimeError('Unknown story anchor '+start)
    for way in ('north','south','east','west','northeast','northwest','southeast','southwest','up','down'):
        back=OPPOSITE[way]
        if way not in rooms[start]['exits'] and back not in rooms[dest]['exits']:
            catalog_assign(dest,'ROOMS',rooms,(start,'exits',way))
            catalog_assign(start,'ROOMS',rooms,(dest,'exits',back))
            return
    raise RuntimeError('No safe link to '+start)


def install(rooms, npcs, quests, items, help_topics):
    """Install without modifying ANY old quest or character data."""
    from systems.new_professions import BASE_ACTIONS, AREAS
    if STORY_IDS:
        raise RuntimeError('v7.00.0 installed twice')
    for key,(name,desc) in NEW_GOODS.items():
        _add(items,'ITEMS',key,{'name':name,'type':'resource','price':None,
                                'sell_silver':10,'desc':desc})
    # Each story chapter has eight native quests. Across the chapters, the
    # same linear prerequisite chain guides the player through the world.
    previous=None
    for chapter,(prof,anchor,title,npc_name,subject) in enumerate(STORY):
        ttype=PROFESSIONS[prof][0]
        actions=[a for a in BASE_ACTIONS if a.prof==prof]
        rid=f'v700_chronicle_room_{chapter+1}'
        nid=f'v700_chronicle_npc_{chapter+1}'
        _add(rooms,'ROOMS',rid,{
            'name':'Archiwum Kroniki — '+title,
            'zone':rooms[anchor]['zone'],
            'desc':f'{npc_name} prowadzi część Wielkiej Fabuły: {subject}. '
                   'Zadania opierają się na rzeczywistych czynnościach profesji. '
                   'Komendy: quest list, przyjmij 1.',
            'exits':{},'generator_level':1,'v700_story_room':True,
        })
        _attach(rooms,anchor,rid)
        own=[]
        for stage in range(8):
            tier=TIERS[min(stage,6)]
            level=(1,25,75,150,300,500,700,800)[stage]
            action=actions[(chapter+stage)%len(actions)]
            qid=f'v700_saga_{chapter+1:02d}_{stage+1:02d}'
            q={
                'name':f'Kronika Imperium: {title} — część {stage+1}',
                'giver':npc_name,'kind':'profession_action','target':prof,
                'needed':2+stage*2,
                'description':f'{subject}. Wykonaj {2+stage*2} razy profesje6 praca '
                              f'{prof} {action.code} {tier}. Wymagane materiały i narzędzie. '
                              f'Próg profesji przynajmniej {tier}.',
                'required_profession':prof,'min_profession_level':tier,
                'generator_level':level,'specialist_tool_type':ttype,
                'required_action_code':action.code,'min_action_tier':tier,
                'reward_profession':prof,'reward_profession_xp':2300+level*62,
                'reward_tool_type':ttype,'reward_tool_xp':1500+level*40,
                'reward_silver':6500+level*430,
                'reward_gold':0,'reward_mithril':0,
                'reward_items':{'v700_story_seal':1+stage//3},
                'repeatable':False,'v700_story':True,
            }
            if previous: q['requires_quest']=previous
            _add(quests,'QUESTS',qid,q)
            STORY_IDS.append(qid)
            own.append(qid)
            previous=qid
        _add(npcs,'NPCS',nid,{
            'name':npc_name,'room':rid,'rank_profession':prof,
            'dialogue':f'{npc_name}: {subject}. Poprowadzę cię przez 8 etapów. '
                       'Wpisz quest list i przyjmij 1. Kronika łączy osiem krain.',
            'specialist_tool_type':ttype,'specialist_topic':'imperium7',
            'specialist_quests':tuple(own),'v700_story_npc':True,
        })
    if len(STORY_IDS)!=64:
        raise RuntimeError('Incomplete v7 story')
    help_topics['imperium7']=[
        'Era Żyjącego Imperium: imperium7 pomoc, status, koszt <projekt> — sprawdź wymagania przed budową.',
        'imperium7 ulepsz pole/stado/magazyn/warsztat/stocznia/mury/latarnia/twierdza — trwałe projekty.',
        'imperium7 praca rolnictwo/hodowla/inżynieria; imperium7 lowy lista/start/odbierz — realne zabicia elit i bossów.',
        'imperium7 wyprawa lista/start <rafa|stolica|burze|row>/odbierz — realne zapasy i rejs.',
        'imperium7 karawana lista/start <rynek|port|kuźnia|targ>/odbierz — towary i trasy.',
        'imperium7 mistrzostwo lista/<profesja> — dodatkowe kontrakty wszystkich 22 profesji.',
        'imperium7 fabula — przewodnik po 64 zadaniach Kroniki Imperium u ośmiu nowych NPC.',
        'imperium7 nvda zwięźle/pełne — trwałe ustawienie komunikatów tej komendy.',
    ]
    return {'quests':64,'npcs':8,'rooms':8,'items':len(NEW_GOODS),'professions':22}
