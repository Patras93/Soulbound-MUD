# -*- coding: utf-8 -*-
"""Static Soulbound catalog. Data only; gameplay logic lives elsewhere."""
from data.catalogs_v109.items_01 import build_catalog as _items_part_01
from data.catalogs_v109.items_02 import build_catalog as _items_part_02
from data.catalogs_v109.items_03 import build_catalog as _items_part_03
from data.catalogs_v109.items_04 import build_catalog as _items_part_04
from data.catalogs_v109.items_05 import build_catalog as _items_part_05
from data.catalogs_v109.items_06 import build_catalog as _items_part_06
from data.catalogs_v109.items_07 import build_catalog as _items_part_07

ITEMS = {}
ITEMS.update(_items_part_01())
ITEMS.update(_items_part_02())
ITEMS.update(_items_part_03())
ITEMS.update(_items_part_04())
ITEMS.update(_items_part_05())
ITEMS.update(_items_part_06())
ITEMS.update(_items_part_07())

# v1.28.11: rare, tradeable discoveries (normal inventory; not bound tools).
ITEMS.update({
    "v12811_leviathan_pearl": {"name": "Perła Lewiatana", "type": "loot", "price": None,
        "sell_gold": 150000, "desc": "Niezwykle rzadki skarb z połowu. Cenny towar na sprzedaż i składnik legendarnych receptur."},
    "v12811_worldheart_core": {"name": "Serce Pierwotnej Rudy", "type": "loot", "price": None,
        "sell_gold": 180000, "desc": "Legendarny minerał znaleziony podczas wydobycia. Składnik mistrzowskiego rzemiosła."},
    "v12811_eternal_timber": {"name": "Żywe Drewno Pradawnych", "type": "loot", "price": None,
        "sell_gold": 160000, "desc": "Bezcenne drewno ze starych lasów. Składnik mistrzowskiego rzemiosła."},
    "v12811_phoenix_bloom": {"name": "Pierwotny Kwiat Feniksa", "type": "loot", "price": None,
        "sell_gold": 160000, "desc": "Wyjątkowy okaz znaleziony wśród ziół. Składnik mistrzowskiego rzemiosła."},
    "v12811_ancient_blueprint": {"name": "Zapis Zapomnianej Receptury", "type": "loot", "price": None,
        "sell_gold": 200000, "desc": "Rzadki schemat z legendarnego skarbca. Zużywany do wykonania Reliktu Odkrywcy."},
    "v12811_explorer_relic": {"name": "Relikt Odkrywcy", "type": "armor", "slot": "charm",
        "defense": 140, "price": None, "rarity": "legendary", "rarity_name": "Legendarny",
        "stats": {"strength": 120, "dexterity": 120, "constitution": 120,
                  "intelligence": 120, "willpower": 120},
        "desc": "Legendarny talizman wykonany z czterech wyjątkowych odkryć i zapomnianej receptury."},
})

__all__ = ['ITEMS']

# v6.00.0: narzędzia i towary nowych profesji.
ITEMS.update({
    'hunting_knife': {"name":'Nóż Łowiecki',"type":"tool","tool_type":'hunting',"price":1200,"currency":"silver","desc":"Narzędzie profesji Łowiectwo, poziomy 1-800; tylko jedno na postać."},
    'farming_hoe': {"name":'Motyka Rolnicza',"type":"tool","tool_type":'farming',"price":1200,"currency":"silver","desc":"Narzędzie profesji Rolnictwo, poziomy 1-800; tylko jedno na postać."},
    'husbandry_kit': {"name":'Przybory Hodowlane',"type":"tool","tool_type":'animal_husbandry',"price":1200,"currency":"silver","desc":"Narzędzie profesji Hodowla zwierząt, poziomy 1-800; tylko jedno na postać."},
    'shipwright_hammer': {"name":'Młot Okrętowy',"type":"tool","tool_type":'shipbuilding',"price":1200,"currency":"silver","desc":"Narzędzie profesji Okrętownictwo, poziomy 1-800; tylko jedno na postać."},
    'mason_trowel': {"name":'Kielnia Murarska',"type":"tool","tool_type":'masonry',"price":1200,"currency":"silver","desc":"Narzędzie profesji Murarstwo, poziomy 1-800; tylko jedno na postać."},
    'engineer_kit': {"name":'Zestaw Inżynierski',"type":"tool","tool_type":'engineering',"price":1200,"currency":"silver","desc":"Narzędzie profesji Inżynieria, poziomy 1-800; tylko jedno na postać."},
    'merchant_scale': {"name":'Waga Kupiecka',"type":"tool","tool_type":'trading',"price":1200,"currency":"silver","desc":"Narzędzie profesji Kupiectwo, poziomy 1-800; tylko jedno na postać."},
    'navigation_sextant': {"name":'Sekstant Nawigacyjny',"type":"tool","tool_type":'sailing',"price":1200,"currency":"silver","desc":"Narzędzie profesji Żeglarstwo, poziomy 1-800; tylko jedno na postać."},
    'hunt_meat': {"name":'Mięso Łowne',"type":"resource","price":None,"sell_silver":30,"desc":"Surowiec profesji v6.00.0."},
    'field_grain': {"name":'Zboże z Pola',"type":"resource","price":None,"sell_silver":30,"desc":"Surowiec profesji v6.00.0."},
    'farm_wool': {"name":'Wełna Hodowlana',"type":"resource","price":None,"sell_silver":30,"desc":"Surowiec profesji v6.00.0."},
    'ship_parts': {"name":'Elementy Okrętu',"type":"resource","price":None,"sell_silver":30,"desc":"Surowiec profesji v6.00.0."},
    'stone_blocks': {"name":'Bloki Kamienne',"type":"resource","price":None,"sell_silver":30,"desc":"Surowiec profesji v6.00.0."},
    'machine_gears': {"name":'Mechanizm Zębaty',"type":"resource","price":None,"sell_silver":30,"desc":"Surowiec profesji v6.00.0."},
    'trade_crate': {"name":'Skrzynia Kupiecka',"type":"resource","price":None,"sell_silver":30,"desc":"Surowiec profesji v6.00.0."},
    'navigation_chart': {"name":'Mapa Żeglarska',"type":"resource","price":None,"sell_silver":30,"desc":"Surowiec profesji v6.00.0."},
})

# v6.00: no duplicated tools, all new activities registered in professions_v600.
from systems.new_professions import ITEMS_NEW as _V600_ITEMS, PROFESSIONS as _V600_PROFESSIONS
for _id, (_name, _type) in _V600_ITEMS.items():
    ITEMS[_id] = {"name":_name,"type":_type,"price":None,"sell_silver":5,"desc":"Produkt nowej profesji (v6.00.0)."}
# Items are not purchasable through generic shop; their single purchase is
# recorded against character id by the profession command.

# v12.00.0: 22 distinct, player-craftable masterworks; no new tool item.
from systems.profession_projects_v1200 import crafted_items as _v1200_masterwork_items
for _id, _spec in _v1200_masterwork_items().items():
    if _id in ITEMS:
        raise RuntimeError('Duplicate masterwork item: '+_id)
    ITEMS[_id] = _spec

# v110: isolated content catalog; no session, database or mutable legacy import.
from systems.v11000_activation import enabled as _v110_items_enabled
if _v110_items_enabled():
    from data.items_v110.professions import tools as _v110_profession_catalog
    _extra_v110 = _v110_profession_catalog()
    if set(_extra_v110).intersection(ITEMS):
        raise RuntimeError('v110: kolizja ID narzędzia lub wyrobu profesji')
    ITEMS.update(_extra_v110)
