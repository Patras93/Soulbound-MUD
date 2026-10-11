# -*- coding: utf-8 -*-
"""v2.20.1: real, inventory-backed mastery recipes for all 14 professions.

Every craft consumes rare Ocean 5 resources in a single SQLite savepoint.
Requires first specialty of the matching profession, >= level 100.
"""
from __future__ import annotations
from systems.imperial_economy_v1320 import atomic, select_source, take, give
from systems.profession_mastery_v2200 import canonical, SPECIALTIES, TOOLS

# profession, specialty, output, inputs, sell_value, name
RECIPES = {
    'Wędkarstwo': ('Łowca Głębin', 'v2201_fishing_cache', {'v2200_leviathan_heart': 1, 'soul_shard': 2}, 180000, 'Zapasy Poławiacza'),
    'Górnictwo': ('Poszukiwacz Złóż', 'v2201_abyss_alloy', {'v2200_storm_core': 1, 'iron_ingot': 3}, 200000, 'Stop Otchłani'),
    'Drwalstwo': ('Strażnik Lasu', 'v2201_runic_mast', {'v2200_whisper_coral': 1, 'oak_plank': 4}, 180000, 'Runiczny Maszt'),
    'Kowalstwo': ('Płatnerz', 'v2201_naval_gun', {'v2200_leviathan_heart': 1, 'iron_ingot': 5}, 240000, 'Działo Lewiatana'),
    'Gotowanie': ('Kucharz Wypraw', 'v2201_deep_rations', {'v2200_whisper_coral': 1, 'sage': 3}, 165000, 'Racja Głębinowa'),
    'Zielarstwo': ('Odkrywca Roślin', 'v2201_reef_extract', {'v2200_whisper_coral': 1, 'mint': 5}, 170000, 'Ekstrakt Raf'),
    'Alchemia': ('Mistrz Eliksirów', 'v2201_storm_essence', {'v2200_storm_core': 1, 'ginseng': 3}, 210000, 'Esencja Burz'),
    'Jubilerstwo': ('Szlifierz Gwiazd', 'v2201_royal_gem', {'v2200_ancient_pearl': 1, 'gold_ingot': 2}, 190000, 'Klejnot Stolicy'),
    'Krawiectwo': ('Tkacz Run', 'v2201_pearl_cloth', {'v2200_ancient_pearl': 1, 'moonflower': 3}, 185000, 'Materiał Perłowy'),
    'Garbarstwo': ('Płatnerz Skór', 'v2201_abyss_hide', {'v2200_leviathan_heart': 1, 'wolf_fang': 4}, 195000, 'Skóra Strażnika Rowu'),
    'Stolarstwo': ('Budowniczy Statków', 'v2201_naval_hull', {'v2200_whisper_coral': 1, 'oak_plank': 6}, 235000, 'Pancerz Kadłuba Głębin'),
    'Zaklinanie': ('Mistrz Run', 'v2201_naval_ward', {'v2200_storm_core': 1, 'soul_shard': 8}, 250000, 'Bariera Okrętu Burz'),
    'Archeologia': ('Badacz Reliktów', 'v2201_royal_relic', {'v2200_ancient_pearl': 1, 'soul_shard': 5}, 195000, 'Relikt Zatopionego Tronu'),
    'Kartografia': ('Kartograf Oceanów', 'v2201_naval_chart', {'v2200_ancient_pearl': 1, 'oak_plank': 3}, 235000, 'Nawigator Głębin'),
}
# The historical TOOL_PROFESSION_MAP lists eight original tools. Include the
# six newer professions so every mastered craft grants its proper tool XP.
TOOL_TYPES = dict(TOOLS)
TOOL_TYPES.update({
    'Krawiectwo':'tailoring', 'Garbarstwo':'leatherworking',
    'Stolarstwo':'carpentry', 'Zaklinanie':'enchanting',
    'Archeologia':'archaeology', 'Kartografia':'cartography_profession',
})
OUTPUTS = {v[1] for v in RECIPES.values()}


def install(items):
    from data import catalog_mutations as cm
    for prof,(spec,item,inputs,price,name) in RECIPES.items():
        if item in items:
            raise ValueError('Kolizja receptury mistrzowskiej: '+item)
        for needed in inputs:
            if needed not in items:
                raise ValueError('Brak surowca mistrzowskiego: '+needed)
        cm.catalog_assign({'name':name, 'type':'resource','price':None,
                           'sell_silver':price,'desc':f'Mistrzowski wyrób: {prof}. Można handlować i sprzedawać.'},
                          'ITEMS',items,(item,))
    from systems.mastery_advancement_v2300 import install as _install_adv
    return len(RECIPES) + _install_adv(items)


def craft(conn, account, profession, level, tier=1):
    if int(tier) not in (1,2,3):
        raise ValueError('Wybierz recepturę 1, 2 lub 3.')
    if int(tier) > 1:
        from systems.mastery_advancement_v2300 import craft as _craft_adv
        return _craft_adv(conn, account, profession, level, tier)
    profession=canonical(profession)
    required,item,ingredients,price,name=RECIPES[profession]
    if int(level)<100: raise ValueError('Receptury mistrzowskie wymagają poziomu 100 profesji.')
    with atomic(conn):
        found=conn.execute('SELECT 1 FROM profession_specialties_v2200 WHERE account_id=? AND profession=? AND specialty=?',
                           (account,profession,required)).fetchone()
        if not found: raise ValueError('Odblokuj pierwszą specjalizację: '+required)
        sources=[]
        for material,quantity in ingredients.items():
            box=select_source(conn,account,material,quantity)
            if box is None: raise ValueError(f'Brakuje materiału {material}: {quantity} szt.')
            sources.append((material,quantity,box))
        for material,quantity,box in sources:
            take(conn,account,material,quantity,box)
        give(conn,account,item,1,'inventory')
    return item,name,2500+int(level)*35,500+int(level)*6
