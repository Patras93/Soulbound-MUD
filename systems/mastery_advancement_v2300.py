# -*- coding: utf-8 -*-
"""v2.30: second/third authored profession recipes, transactional materials.

Legacy v2.20.1 recipes remain unchanged; advancement uses their outputs as
inputs so each mastery tier builds on the previous, not a free item generator.
"""
from systems.profession_mastery_v2200 import canonical, SPECIALTIES
from systems.imperial_economy_v1320 import atomic, select_source, take, give

# Two named artifacts, with distinct extra basic materials at tiers 250 and 450.
ADVANCED = {
 'Wędkarstwo': ('Skrzynia Łowcy Prądów', 'Dziedzictwo Władcy Głębin', 'soul_shard', 'v2200_leviathan_heart'),
 'Górnictwo': ('Rafinowana Stal Rowu', 'Rdzeń Kowadła Otchłani', 'iron_ingot', 'v2200_storm_core'),
 'Drwalstwo': ('Maszt Żelaznego Wiatru', 'Serce Pradawnego Okrętu', 'oak_plank', 'v2200_whisper_coral'),
 'Kowalstwo': ('Działo Gromowej Salwy', 'Artyleria Zatopionego Cesarza', 'iron_ingot', 'v2200_storm_core'),
 'Gotowanie': ('Uczta Rafowych Wędrowców', 'Uczta Mistrza Lewiatanów', 'sage', 'v2200_whisper_coral'),
 'Zielarstwo': ('Eliksir Rafinowanych Raf', 'Żywa Esencja Głębin', 'mint', 'v2200_whisper_coral'),
 'Alchemia': ('Destylat Burzowy', 'Pradawny Kondensat Piorunów', 'ginseng', 'v2200_storm_core'),
 'Jubilerstwo': ('Korona Perłowych Głębin', 'Korona Królów Stolicy', 'gold_ingot', 'v2200_ancient_pearl'),
 'Krawiectwo': ('Płaszcz Zatopionych Run', 'Szata Nieśmiertelnego Wędrowca', 'moonflower', 'v2200_ancient_pearl'),
 'Garbarstwo': ('Pancerz Skóry Otchłani', 'Płaszcz Strażnika Rowu', 'wolf_fang', 'v2200_leviathan_heart'),
 'Stolarstwo': ('Wzmocniona Burta Lewiatana', 'Szkielet Okrętu Pradawnych', 'oak_plank', 'v2200_whisper_coral'),
 'Zaklinanie': ('Pieczęć Błękitnych Sztormów', 'Wieczna Bariera Władcy Mórz', 'soul_shard', 'v2200_storm_core'),
 'Archeologia': ('Insygnia Zatopionego Dworu', 'Berło Zapomnianego Cesarza', 'soul_shard', 'v2200_ancient_pearl'),
 'Kartografia': ('Atlas Podmorskich Dróg', 'Mapa Zapomnianych Imperiów', 'oak_plank', 'v2200_ancient_pearl'),
}

def recipe(profession, tier):
    from systems.mastery_crafting_v2201 import RECIPES
    profession = canonical(profession)
    tier = int(tier)
    if tier not in (2, 3):
        raise ValueError('Wybierz poziom receptury 2 lub 3.')
    first = RECIPES[profession]
    names = ADVANCED[profession]
    item_id = 'v2300_master_' + str(list(SPECIALTIES).index(profession)+1) + '_' + str(tier)
    prev_id = first[1] if tier==2 else 'v2300_master_'+str(list(SPECIALTIES).index(profession)+1)+'_2'
    extra = names[2] if tier==2 else names[3]
    return (SPECIALTIES[profession][tier-1], item_id,
            {prev_id:1,extra:2 if tier==2 else 3}, first[3]*(2 if tier==2 else 4),names[tier-2])

def install(items):
    from data import catalog_mutations as cm
    for prof in SPECIALTIES:
        for tier in (2,3):
            spec,item,inputs,price,name=recipe(prof,tier)
            if item in items:
                raise ValueError('Kolizja mistrzowskiego przedmiotu: '+item)
            if any(material not in items for material in inputs):
                raise ValueError('Brak składnika dla '+name)
            cm.catalog_assign({'name':name,'type':'resource','price':None,
                              'sell_silver':price,
                              'desc':f'Mistrzowski wyrób poziomu {tier} profesji {prof}. Można nim handlować.'},
                              'ITEMS',items,(item,))
    return len(ADVANCED)*2

def craft(conn,account,profession,level,tier):
    profession=canonical(profession)
    tier=int(tier)
    spec,item,ingredients,price,name=recipe(profession,tier)
    minimum=(100,250,450)[tier-1]
    if int(level)<minimum:
        raise ValueError(f'Wymagany poziom profesji {minimum}.')
    with atomic(conn):
        found=conn.execute('SELECT 1 FROM profession_specialties_v2200 WHERE account_id=? AND profession=? AND specialty=?',
                           (account,profession,spec)).fetchone()
        if not found:raise ValueError('Odblokuj specjalizację: '+spec)
        sources=[]
        for material,amount in ingredients.items():
            box=select_source(conn,account,material,amount)
            if box is None:raise ValueError(f'Brakuje materiału {material}: {amount} szt.')
            sources.append((material,amount,box))
        for material,amount,box in sources:take(conn,account,material,amount,box)
        give(conn,account,item,1,'inventory')
    return item,name,2500+int(level)*35*tier,500+int(level)*6*tier
