
def validate_complete_resource_atlases():
    checks = (
        ("ryby", FISH_RESOURCE_IDS, FISH_ATLAS_ALL),
        ("rudy", ORE_RESOURCE_IDS, ORE_ATLAS_ALL),
        ("drewno", WOOD_RESOURCE_IDS, WOOD_ATLAS_ALL),
        ("zioła", HERB_RESOURCE_IDS, HERB_ATLAS_ALL),
    )
    for label, source_ids, atlas_ids in checks:
        missing = set(source_ids) - set(atlas_ids)
        if missing:
            raise RuntimeError(
                f"Atlas {label} nie zawiera: "
                + ", ".join(sorted(missing))
            )

validate_complete_resource_atlases()

ORE_ATLAS_LEVELS = {
    "stone_chunk": 1,
    "copper_ore": 1,
    "iron_ore": 10,
    "silver_ore": 25,
    "gold_ore": 50,
    "cobalt_ore": 100,
    "runestone_ore": 120,
    "dragonsteel_ore": 140,
    "astral_ore": 160,
    "void_ore": 180,
    "eternium_ore": 200,
}

ORE_MINE_FLOOR_MINIMUMS = {
    "stone_chunk": 1,
    "copper_ore": 1,
    "iron_ore": 10,
    "silver_ore": 25,
    "gold_ore": 50,
    "cobalt_ore": 100,
    "runestone_ore": 120,
    "dragonsteel_ore": 140,
    "astral_ore": 160,
    "void_ore": 180,
    "eternium_ore": 200,
}

for _level, _floor, _item_id, _name in WORLD_ORE_UNLOCKS:
    ORE_ATLAS_LEVELS[_item_id] = _level
    ORE_MINE_FLOOR_MINIMUMS[_item_id] = _floor

# v0.24.4: rudy progresji 220-400 wymagają równocześnie odpowiedniego
# Kilofa i głębokości Kopalni Głębinowej. Atlas ma pokazywać te same progi.
for _level, _item_id in ENDGAME_ORE_UNLOCKS:
    if int(_level) > 200:
        ORE_ATLAS_LEVELS[_item_id] = int(_level)
        ORE_MINE_FLOOR_MINIMUMS[_item_id] = int(_level)

# v0.8.22 - dokładne minimalne levele narzędzi według lokacji.
# Dane odpowiadają aktywnym pulom Drwalstwa i Zielarstwa v0.8.22.
WOOD_ATLAS_ROOM_MIN_LEVELS = {'deep_grove': {'ancient_heartwood': 80,
                'ash_log': 1,
                'astralwood_log': 140,
                'cedar_log': 1,
                'chestnut_log': 1,
                'dragonwood_log': 120,
                'ebony_log': 40,
                'eternal_worldwood_log': 200,
                'ironwood_log': 40,
                'mahogany_log': 40,
                'redwood_log': 60,
                'runewood_log': 100,
                'silverwood_log': 60,
                'spiritwood_log': 80,
                'starheart_log': 180,
                'teak_log': 40,
                'voidwood_log': 160,
                'walnut_log': 1,
                'world_agarwood': 144,
                'world_balsa': 165,
                'world_baobab': 172,
                'world_bubinga': 95,
                'world_greenheart': 123,
                'world_iroko': 74,
                'world_jarrah': 186,
                'world_jatoba': 109,
                'world_kauri': 179,
                'world_koa': 151,
                'world_lignum_vitae': 130,
                'world_merbau': 88,
                'world_padauk': 60,
                'world_paulownia': 158,
                'world_purpleheart': 116,
                'world_sandalwood': 137,
                'world_sapele': 81,
                'world_tasmanian_blackwood': 193,
                'world_wenge': 67,
                'world_zebrawood': 102,
                'worldtree_wood': 80,
                'yew_log': 40},
 'lumberjack_camp': {'alder_log': 1,
                     'beech_log': 35,
                     'birch_log': 1,
                     'fallen_branch': 1,
                     'linden_log': 15,
                     'maple_log': 35,
                     'oak_log': 35,
                     'pine_log': 1,
                     'poplar_log': 15,
                     'willow_log': 15,
                     'world_acacia_wood': 49,
                     'world_american_sycamore': 55,
                     'world_aspen_wood': 79,
                     'world_basswood': 73,
                     'world_black_locust': 43,
                     'world_cottonwood': 85,
                     'world_douglas_fir': 19,
                     'world_elm_wood': 61,
                     'world_european_larch': 13,
                     'world_hornbeam_wood': 67,
                     'world_juniper_wood': 37,
                     'world_mediterranean_cypress': 31,
                     'world_norway_spruce': 1,
                     'world_silver_fir': 7,
                     'world_western_hemlock': 25},
 'meadow': {'alder_log': 1,
            'beech_log': 35,
            'birch_log': 1,
            'fallen_branch': 1,
            'linden_log': 15,
            'maple_log': 35,
            'oak_log': 35,
            'pine_log': 1,
            'poplar_log': 15,
            'willow_log': 15,
            'world_acacia_wood': 49,
            'world_american_sycamore': 55,
            'world_aspen_wood': 79,
            'world_basswood': 73,
            'world_black_locust': 43,
            'world_cottonwood': 85,
            'world_douglas_fir': 19,
            'world_elm_wood': 61,
            'world_european_larch': 13,
            'world_hornbeam_wood': 67,
            'world_juniper_wood': 37,
            'world_mediterranean_cypress': 31,
            'world_norway_spruce': 1,
            'world_silver_fir': 7,
            'world_western_hemlock': 25},
 'old_road': {'ash_log': 25,
              'beech_log': 1,
              'cedar_log': 50,
              'chestnut_log': 25,
              'ironwood_log': 75,
              'linden_log': 1,
              'mahogany_log': 50,
              'maple_log': 1,
              'oak_log': 1,
              'redwood_log': 75,
              'teak_log': 75,
              'walnut_log': 25,
              'world_apple_wood': 26,
              'world_cherry_wood': 20,
              'world_cork_oak': 62,
              'world_eucalyptus_wood': 50,
              'world_hickory': 92,
              'world_olive_wood': 44,
              'world_pear_wood': 32,
              'world_pecan_wood': 98,
              'world_plum_wood': 38,
              'world_red_maple': 86,
              'world_red_oak': 74,
              'world_rosewood': 104,
              'world_rubberwood': 56,
              'world_sugar_maple': 80,
              'world_white_oak': 68,
              'yew_log': 50},
 'whisper_grove': {'ash_log': 25,
                   'beech_log': 1,
                   'cedar_log': 50,
                   'chestnut_log': 25,
                   'ironwood_log': 75,
                   'linden_log': 1,
                   'mahogany_log': 50,
                   'maple_log': 1,
                   'oak_log': 1,
                   'redwood_log': 75,
                   'teak_log': 75,
                   'walnut_log': 25,
                   'world_apple_wood': 26,
                   'world_cherry_wood': 20,
                   'world_cork_oak': 62,
                   'world_eucalyptus_wood': 50,
                   'world_hickory': 92,
                   'world_olive_wood': 44,
                   'world_pear_wood': 32,
                   'world_pecan_wood': 98,
                   'world_plum_wood': 38,
                   'world_red_maple': 86,
                   'world_red_oak': 74,
                   'world_rosewood': 104,
                   'world_rubberwood': 56,
                   'world_sugar_maple': 80,
                   'world_white_oak': 68,
                   'yew_log': 50}}

HERB_ATLAS_ROOM_MIN_LEVELS = {'chamomile_meadow': {'chamomile': 1},
 'deep_grove': {'astral_lotus': 90,
                'astral_orchid': 140,
                'dragon_sage': 120,
                'eternal_blossom': 200,
                'ginseng': 1,
                'mandrake': 1,
                'moonflower': 40,
                'nightshade': 1,
                'phoenix_crown': 180,
                'phoenix_leaf': 70,
                'soulroot': 40,
                'star_moss': 40,
                'sunfire_bloom': 100,
                'void_lotus': 160,
                'world_angelica': 130,
                'world_artichoke_leaf': 110,
                'world_ashwagandha': 10,
                'world_astragalus': 90,
                'world_bacopa': 50,
                'world_bay_leaf': 150,
                'world_eleuthero': 80,
                'world_eucalyptus_leaf': 170,
                'world_frankincense': 200,
                'world_gentian': 120,
                'world_gotu_kola': 40,
                'world_holy_basil': 1,
                'world_juniper_berry': 140,
                'world_milk_thistle': 100,
                'world_moringa': 20,
                'world_myrrh': 190,
                'world_neem': 30,
                'world_olive_leaf': 160,
                'world_rhodiola': 70,
                'world_shatavari': 60},
 'flower_meadow': {'chamomile': 1,
                   'lavender': 1,
                   'lemon_balm': 15,
                   'nettle': 1,
                   'sage': 35,
                   'valerian': 35,
                   'world_basil': 20,
                   'world_cardamom': 160,
                   'world_chives': 110,
                   'world_clove': 170,
                   'world_coriander': 60,
                   'world_dill': 50,
                   'world_fennel': 70,
                   'world_galangal': 150,
                   'world_garlic': 120,
                   'world_ginger': 130,
                   'world_marjoram': 90,
                   'world_oregano': 30,
                   'world_parsley': 40,
                   'world_rosemary': 1,
                   'world_saffron': 200,
                   'world_savory': 100,
                   'world_tarragon': 80,
                   'world_thyme': 10,
                   'world_turmeric': 140,
                   'world_vanilla': 190,
                   'yarrow': 15},
 'ginseng_meadow': {'ginseng': 1},
 'herbalist_hut': {'chamomile': 1,
                   'lavender': 15,
                   'lemon_balm': 15,
                   'mint': 1,
                   'nettle': 1,
                   'sage': 35,
                   'valerian': 35,
                   'world_basil': 20,
                   'world_cardamom': 160,
                   'world_chives': 110,
                   'world_clove': 170,
                   'world_coriander': 60,
                   'world_dill': 50,
                   'world_fennel': 70,
                   'world_galangal': 150,
                   'world_garlic': 120,
                   'world_ginger': 130,
                   'world_marjoram': 90,
                   'world_oregano': 30,
                   'world_parsley': 40,
                   'world_rosemary': 1,
                   'world_saffron': 200,
                   'world_savory': 100,
                   'world_tarragon': 80,
                   'world_thyme': 10,
                   'world_turmeric': 140,
                   'world_vanilla': 190,
                   'yarrow': 15},
 'lake_shore': {'chamomile': 1,
                'ginseng': 55,
                'lemon_balm': 1,
                'mint': 1,
                'moonflower': 55,
                'sage': 25,
                'star_moss': 25,
                'valerian': 55,
                'world_aloe_vera': 10,
                'world_arnica': 140,
                'world_burdock': 70,
                'world_calendula': 20,
                'world_comfrey': 150,
                'world_dandelion': 60,
                'world_echinacea': 30,
                'world_elderflower': 90,
                'world_hawthorn': 100,
                'world_hibiscus': 120,
                'world_horsetail': 80,
                'world_jasmine': 130,
                'world_lemongrass': 1,
                'world_mugwort': 160,
                'world_passionflower': 200,
                'world_ribwort_plantain': 50,
                'world_rosehip': 110,
                'world_skullcap': 190,
                'world_st_johns_wort': 40,
                'world_wormwood': 170,
                'yarrow': 25},
 'lakeside_meadow': {'chamomile': 1,
                     'lavender': 15,
                     'lemon_balm': 1,
                     'mint': 1,
                     'sage': 35,
                     'star_moss': 35,
                     'world_aloe_vera': 10,
                     'world_arnica': 140,
                     'world_burdock': 70,
                     'world_calendula': 20,
                     'world_comfrey': 150,
                     'world_dandelion': 60,
                     'world_echinacea': 30,
                     'world_elderflower': 90,
                     'world_hawthorn': 100,
                     'world_hibiscus': 120,
                     'world_horsetail': 80,
                     'world_jasmine': 130,
                     'world_lemongrass': 1,
                     'world_mugwort': 160,
                     'world_passionflower': 200,
                     'world_ribwort_plantain': 50,
                     'world_rosehip': 110,
                     'world_skullcap': 190,
                     'world_st_johns_wort': 40,
                     'world_wormwood': 170,
                     'yarrow': 15},
 'lavender_meadow': {'lavender': 1},
 'lemon_balm_meadow': {'lemon_balm': 1},
 'meadow': {'chamomile': 1,
            'lavender': 15,
            'lemon_balm': 15,
            'mint': 1,
            'nettle': 1,
            'sage': 35,
            'valerian': 35,
            'world_basil': 20,
            'world_cardamom': 160,
            'world_chives': 110,
            'world_clove': 170,
            'world_coriander': 60,
            'world_dill': 50,
            'world_fennel': 70,
            'world_galangal': 150,
            'world_garlic': 120,
            'world_ginger': 130,
            'world_marjoram': 90,
            'world_oregano': 30,
            'world_parsley': 40,
            'world_rosemary': 1,
            'world_saffron': 200,
            'world_savory': 100,
            'world_tarragon': 80,
            'world_thyme': 10,
            'world_turmeric': 140,
            'world_vanilla': 190,
            'yarrow': 15},
 'mint_meadow': {'mint': 1},
 'moonflower_meadow': {'moonflower': 1},
 'nettle_meadow': {'nettle': 1},
 'old_road': {'ginseng': 25,
              'lavender': 1,
              'mandrake': 50,
              'moonflower': 50,
              'nightshade': 25,
              'phoenix_leaf': 75,
              'sage': 1,
              'soulroot': 50,
              'star_moss': 75,
              'valerian': 1,
              'world_amaranth': 110,
              'world_anise': 50,
              'world_black_cumin': 70,
              'world_chia': 100,
              'world_cocoa_pod': 190,
              'world_coffee_berry': 170,
              'world_cumin': 40,
              'world_fenugreek': 30,
              'world_flax': 90,
              'world_guarana': 140,
              'world_hops': 1,
              'world_kola_nut': 200,
              'world_licorice_root': 10,
              'world_maca': 130,
              'world_marshmallow_root': 20,
              'world_quinoa': 120,
              'world_sesame': 80,
              'world_star_anise': 60,
              'world_tea_leaf': 160,
              'world_yerba_mate': 150},
 'riverbank': {'chamomile': 1,
               'ginseng': 55,
               'lemon_balm': 1,
               'mint': 1,
               'moonflower': 55,
               'sage': 25,
               'star_moss': 25,
               'valerian': 55,
               'world_aloe_vera': 10,
               'world_arnica': 140,
               'world_burdock': 70,
               'world_calendula': 20,
               'world_comfrey': 150,
               'world_dandelion': 60,
               'world_echinacea': 30,
               'world_elderflower': 90,
               'world_hawthorn': 100,
               'world_hibiscus': 120,
               'world_horsetail': 80,
               'world_jasmine': 130,
               'world_lemongrass': 1,
               'world_mugwort': 160,
               'world_passionflower': 200,
               'world_ribwort_plantain': 50,
               'world_rosehip': 110,
               'world_skullcap': 190,
               'world_st_johns_wort': 40,
               'world_wormwood': 170,
               'yarrow': 25},
 'sage_meadow': {'sage': 1},
 'valerian_meadow': {'valerian': 1},
 'whisper_grove': {'ginseng': 25,
                   'lavender': 1,
                   'mandrake': 50,
                   'moonflower': 50,
                   'nightshade': 25,
                   'phoenix_leaf': 75,
                   'sage': 1,
                   'soulroot': 50,
                   'star_moss': 75,
                   'valerian': 1,
                   'world_amaranth': 110,
                   'world_anise': 50,
                   'world_black_cumin': 70,
                   'world_chia': 100,
                   'world_cocoa_pod': 190,
                   'world_coffee_berry': 170,
                   'world_cumin': 40,
                   'world_fenugreek': 30,
                   'world_flax': 90,
                   'world_guarana': 140,
                   'world_hops': 1,
                   'world_kola_nut': 200,
                   'world_licorice_root': 10,
                   'world_maca': 130,
                   'world_marshmallow_root': 20,
                   'world_quinoa': 120,
                   'world_sesame': 80,
                   'world_star_anise': 60,
                   'world_tea_leaf': 160,
                   'world_yerba_mate': 150},
 'yarrow_meadow': {'yarrow': 1}}


# Profil bazowy v0.8.76 jest zachowany wyłącznie do bezpiecznej migracji
# istniejących postaci. Nie jest używany przy tworzeniu nowych postaci.
V0876_RACE_BASE_STATS = {
    "Człowiek": {"strength": 10, "dexterity": 10, "constitution": 10, "intelligence": 10, "willpower": 10},
    "Ogr": {"strength": 14, "dexterity": 8, "constitution": 14, "intelligence": 6, "willpower": 8},
    "Elf": {"strength": 8, "dexterity": 14, "constitution": 9, "intelligence": 13, "willpower": 11},
    "Krasnolud": {"strength": 12, "dexterity": 9, "constitution": 14, "intelligence": 9, "willpower": 12},
    "Ork": {"strength": 13, "dexterity": 10, "constitution": 13, "intelligence": 7, "willpower": 9},
    "Niziołek": {"strength": 7, "dexterity": 14, "constitution": 10, "intelligence": 10, "willpower": 11},
    "Mroczny Elf": {"strength": 9, "dexterity": 13, "constitution": 9, "intelligence": 14, "willpower": 10},
    "Gnom": {"strength": 7, "dexterity": 12, "constitution": 9, "intelligence": 14, "willpower": 13},
    "Smoczy": {"strength": 13, "dexterity": 9, "constitution": 13, "intelligence": 10, "willpower": 10},
    "Troll": {"strength": 15, "dexterity": 7, "constitution": 15, "intelligence": 5, "willpower": 8},
    "Diablę": {"strength": 9, "dexterity": 11, "constitution": 9, "intelligence": 13, "willpower": 13},
    "Aasimar": {"strength": 10, "dexterity": 10, "constitution": 11, "intelligence": 12, "willpower": 14},
    "Driada": {"strength": 7, "dexterity": 10, "constitution": 11, "intelligence": 15, "willpower": 15},
    "Cyborg": {"strength": 10, "dexterity": 11, "constitution": 12, "intelligence": 10, "willpower": 7},
}

# v0.9.0: każda rasa ma dokładnie ten sam budżet 50 bazowych punktów
# w pięciu głównych statystykach. Różni się WYŁĄCZNIE rozkładem oraz
# pasywem rasowym. Usuwa to dawną ukrytą przewagę 50-58 punktów.
RACES = [
    ("Człowiek",
     "Wszechstronny. Wszystkie pięć głównych statystyk startuje na równym poziomie. "
     "Pasyw rasowy: +10 procent do zdobywanego Postępu Rozwoju statystyk.",
     10, 10, 10, 10, 10),
    ("Ogr",
     "Bardzo silny i wytrzymały. Wysoka Siła i Kondycja wspierają walkę wręcz. "
     "Pasyw rasowy: +12 procent obrażeń fizycznych.",
     14, 8, 14, 6, 8),
    ("Elf",
     "Bardzo zręczny, z wyraźnym talentem magicznym. "
     "Pasyw rasowy: +5 punktów procentowych do szansy uniku.",
     8, 14, 8, 12, 8),
    ("Krasnolud",
     "Bardzo odporny. Wysoka Kondycja i Siła Woli wspierają przetrwanie. "
     "Pasyw rasowy: 10 procent redukcji wszystkich otrzymywanych obrażeń.",
     11, 7, 14, 6, 12),
    ("Ork",
     "Urodzony wojownik. Wysoka Siła i Kondycja dają mocne ciosy i dużo HP. "
     "Pasyw rasowy: +10 procent maksymalnego HP.",
     13, 9, 13, 7, 8),
    ("Niziołek",
     "Zręczny i szczęśliwy poszukiwacz. "
     "Pasyw rasowy: +3 punkty procentowe do szansy na bonusowy połów, dodatkową rudę lub dodatkowe drewno.",
     7, 14, 9, 10, 10),
    ("Mroczny Elf",
     "Zręczny i utalentowany magicznie. Dobrze łączy szybkość z ofensywną magią. "
     "Pasyw rasowy: +10 procent obrażeń magicznych.",
     8, 13, 8, 13, 8),
    ("Gnom",
     "Bardzo inteligentny, z dobrym zapasem Siły Woli. "
     "Pasyw rasowy: +15 procent maksymalnej Many.",
     7, 10, 8, 14, 11),
    ("Smoczy",
     "Silny, wytrzymały i wszechstronny w walce. "
     "Pasyw rasowy: +8 procent wszystkich zadawanych obrażeń, fizycznych i magicznych.",
     12, 9, 12, 9, 8),
    ("Troll",
     "Największa surowa Siła i Kondycja. Jest wolny i słaby magicznie, ale bardzo trudny do powalenia. "
     "Pasyw rasowy: 12 procent redukcji otrzymywanych obrażeń fizycznych.",
     15, 7, 15, 5, 8),
    ("Diablę",
     "Dobre predyspozycje magiczne i silna więź z energią dusz. "
     "Pasyw rasowy: +10 procent zdobywanego Soul XP Broni Duszy.",
     8, 10, 8, 13, 11),
    ("Aasimar",
     "Silna Siła Woli i dobre predyspozycje obronne. "
     "Pasyw rasowy: +12 procent obrony magicznej.",
     9, 9, 10, 10, 12),
    ("Driada",
     "Rasa natury nastawiona na życie, magię i odnowę. "
     "Pasyw rasowy: +15 procent mocy wszystkich klasowych umiejętności leczących. "
     "Szczególnie dobrze pasuje do Kapłana i Druida.",
     7, 9, 10, 12, 12),
    ("Cyborg",
     "Technologicznie zmodyfikowana rasa o wysokiej Kondycji i dobrej Zręczności. "
     "Pasyw rasowy: 10 procent redukcji wszystkich otrzymywanych obrażeń. "
     "Szczególnie dobrze współpracuje z klasami Mec i Inżynier.",
     10, 11, 12, 10, 7),
]

# v0.8.46: rekomendacje klas są wskazówką dla nowych graczy, nie ograniczeniem.
# Każda rasa nadal może wybrać każdą z 14 klas.
RACE_CLASS_RECOMMENDATIONS = {
    "Człowiek": {
        "classes": ["Wojownik", "Łotrzyk", "Mag", "Kapłan", "Druid", "Psionik"],
        "reason": "jest wszechstronny i rozwija statystyki szybciej, więc dobrze sprawdza się praktycznie w każdej roli",
    },
    "Ogr": {
        "classes": ["Wojownik", "Berserker", "Strażnik", "Mnich"],
        "reason": "bardzo wysoka Siła i Kondycja oraz bonus do obrażeń fizycznych najlepiej wspierają klasy walczące fizycznie",
    },
    "Elf": {
        "classes": ["Łotrzyk", "Łowca", "Mag", "Druid", "Psionik"],
        "reason": "wysoka Zręczność i Inteligencja łączą szybkie klasy fizyczne z klasami magicznymi",
    },
    "Krasnolud": {
        "classes": ["Strażnik", "Wojownik", "Kapłan", "Psionik"],
        "reason": "wysoka Kondycja i Siła Woli wzmacniają przetrwanie, gardy i odporność magiczną",
    },
    "Ork": {
        "classes": ["Wojownik", "Berserker", "Strażnik", "Mnich"],
        "reason": "wysoka Siła, Kondycja i dodatkowe maksymalne HP sprzyjają bezpośredniej walce",
    },
    "Niziołek": {
        "classes": ["Łotrzyk", "Łowca", "Mnich"],
        "reason": "bardzo wysoka Zręczność dobrze współpracuje z unikami, szybkością i precyzyjnymi atakami",
    },
    "Mroczny Elf": {
        "classes": ["Mag", "Czarownik", "Nekromanta", "Łotrzyk", "Psionik"],
        "reason": "wysoka Inteligencja i Zręczność oraz bonus do obrażeń magicznych wspierają ofensywną magię i szybkie buildy",
    },
    "Gnom": {
        "classes": ["Mag", "Psionik", "Nekromanta", "Kapłan", "Czarownik"],
        "reason": "najwyższa startowa Inteligencja wśród ras i większa maksymalna Mana mocno wspierają klasy magiczne",
    },
    "Smoczy": {
        "classes": ["Wojownik", "Berserker", "Strażnik", "Czarownik", "Mag"],
        "reason": "bonus do wszystkich obrażeń pozwala skutecznie grać zarówno fizycznie, jak i magicznie",
    },
    "Troll": {
        "classes": ["Berserker", "Strażnik", "Wojownik", "Mnich"],
        "reason": "najwyższa Siła i Kondycja oraz redukcja obrażeń fizycznych czynią go bardzo mocnym wojownikiem wręcz",
    },
    "Diablę": {
        "classes": ["Czarownik", "Nekromanta", "Mag", "Psionik"],
        "reason": "dobra Inteligencja i Siła Woli sprzyjają magii, a bonus Soul XP wspiera szybki rozwój Broni Duszy",
    },
    "Aasimar": {
        "classes": ["Kapłan", "Psionik", "Druid", "Strażnik"],
        "reason": "wysoka Siła Woli i rasowa obrona magiczna wspierają leczenie, obronę magiczną i klasy defensywne",
    },
    "Driada": {
        "classes": ["Druid", "Kapłan", "Psionik", "Mag"],
        "reason": "profil Inteligencji i Siły Woli oraz rasowy bonus do leczenia szczególnie wspierają klasy magiczne i lecznicze",
    },
    "Cyborg": {
        "classes": ["Mec", "Inżynier", "Strażnik", "Łowca"],
        "reason": "wysoka Kondycja, dobra Zręczność i redukcja obrażeń wspierają technologiczne oraz defensywne style walki",
    },
}

def race_class_recommendation_text(race_name):
    data = RACE_CLASS_RECOMMENDATIONS.get(race_name)
    if not data:
        return ""
    return f"Polecane klasy: {', '.join(data['classes'])}. Dlaczego: {data['reason']}."

# v0.9.0: bazowa Moc Broni Duszy ma wąski zakres 7-8 zamiast 6-9.
# Różnice klas nadal wynikają ze skilli, pasywów i specjalizacji Soul Tier,
# ale żaden archetyp nie zaczyna z ukrytą karą/bonusem 50% w weapon_base.
CLASSES = [
    ("Wojownik", "physical", "Miecz Przysięgi", 7),
    ("Berserker", "physical", "Topór Krwi", 8),
    ("Łotrzyk", "physical", "Sztylety Cienia", 7),
    ("Łowca", "physical", "Łuk Echa", 7),
    ("Mnich", "physical", "Rękawice Ducha", 7),
    ("Strażnik", "physical", "Młot Bastionu", 7),
    ("Mag", "magic", "Kostur Arkanów", 7),
    ("Nekromanta", "magic", "Kosa Dusz", 8),
    ("Kapłan", "magic", "Młot Światła", 7),
    ("Czarownik", "magic", "Ostrze Otchłani", 8),
    ("Druid", "magic", "Kostur Korzeni", 7),
    ("Psionik", "magic", "Kryształ Umysłu", 7),
    ("Mec", "physical", "Rdzeń Meca", 8),
    ("Inżynier", "physical", "Omni-Narzędzie", 7),
]

# v0.30.17: Broń Duszy jest aktywną bronią autoataku, nie tylko ukrytym bonusem.
SOUL_WEAPON_ATTACK_TECHNIQUES = {
    "Wojownik": "Cięcie Przysięgi",
    "Berserker": "Rąbnięcie Krwi",
    "Łotrzyk": "Podwójne Ukłucie Cienia",
    "Łowca": "Strzał Echa",
    "Mnich": "Cios Ducha",
    "Strażnik": "Uderzenie Bastionu",
    "Mag": "Impuls Arkanów",
    "Nekromanta": "Żniwo Dusz",
    "Kapłan": "Uderzenie Światła",
    "Czarownik": "Cięcie Otchłani",
    "Druid": "Cios Korzeni",
    "Psionik": "Impuls Umysłu",
    "Mec": "Impuls Rdzenia",
    "Inżynier": "Strzał Omni-Narzędzia",
}

# v0.8.51: klasa nadaje własny profil startowych statystyk.
# Maksymalne HP i Mana nie są wpisane na sztywno dla klasy: wynikają potem
# bezpośrednio z Kondycji i Inteligencji oraz bonusów rasy/ekwipunku.
# Profil klasowy v0.8.76 pozostaje dostępny tylko dla migracji starych save'ów.
V0876_CLASS_STARTING_STAT_BONUSES = {
    "Wojownik":   {"strength": 3, "dexterity": 1, "constitution": 3, "intelligence": 0, "willpower": 1, "charisma": 0},
    "Berserker":  {"strength": 4, "dexterity": 1, "constitution": 3, "intelligence": 0, "willpower": 0, "charisma": 0},
    "Łotrzyk":    {"strength": 1, "dexterity": 4, "constitution": 1, "intelligence": 1, "willpower": 0, "charisma": 1},
    "Łowca":      {"strength": 2, "dexterity": 4, "constitution": 2, "intelligence": 0, "willpower": 0, "charisma": 0},
    "Mnich":      {"strength": 1, "dexterity": 3, "constitution": 2, "intelligence": 1, "willpower": 2, "charisma": 0},
    "Strażnik":   {"strength": 2, "dexterity": 0, "constitution": 4, "intelligence": 0, "willpower": 2, "charisma": 0},
    "Mag":        {"strength": 0, "dexterity": 2, "constitution": 1, "intelligence": 4, "willpower": 2, "charisma": 0},
    "Nekromanta": {"strength": 0, "dexterity": 1, "constitution": 2, "intelligence": 3, "willpower": 3, "charisma": 0},
    "Kapłan":     {"strength": 0, "dexterity": 0, "constitution": 3, "intelligence": 2, "willpower": 4, "charisma": 0},
    "Czarownik":  {"strength": 1, "dexterity": 2, "constitution": 1, "intelligence": 4, "willpower": 1, "charisma": 0},
    "Druid":      {"strength": 0, "dexterity": 1, "constitution": 3, "intelligence": 3, "willpower": 3, "charisma": 0},
    "Psionik":    {"strength": 0, "dexterity": 2, "constitution": 1, "intelligence": 3, "willpower": 4, "charisma": 0},    "Mec":       {"strength": 3, "dexterity": 2, "constitution": 3, "intelligence": 1, "willpower": 0, "charisma": 0},
    "Inżynier":  {"strength": 1, "dexterity": 4, "constitution": 2, "intelligence": 2, "willpower": 0, "charisma": 0},
}

# v0.9.0: każda klasa dokłada dokładnie 9 punktów startowych.
# Dzięki temu o sile startu nie decyduje ukryty budżet 8-10, tylko profil
# klasy, pasyw, skille i Broń Duszy.
CLASS_STARTING_STAT_BONUSES = {
    "Wojownik":   {"strength": 4, "dexterity": 1, "constitution": 3, "intelligence": 0, "willpower": 1, "charisma": 0},
    "Berserker":  {"strength": 4, "dexterity": 2, "constitution": 3, "intelligence": 0, "willpower": 0, "charisma": 0},
    "Łotrzyk":    {"strength": 1, "dexterity": 4, "constitution": 1, "intelligence": 1, "willpower": 1, "charisma": 1},
    "Łowca":      {"strength": 2, "dexterity": 4, "constitution": 2, "intelligence": 0, "willpower": 1, "charisma": 0},
    "Mnich":      {"strength": 1, "dexterity": 4, "constitution": 2, "intelligence": 1, "willpower": 1, "charisma": 0},
    "Strażnik":   {"strength": 2, "dexterity": 0, "constitution": 4, "intelligence": 0, "willpower": 3, "charisma": 0},
    "Mag":        {"strength": 0, "dexterity": 2, "constitution": 1, "intelligence": 4, "willpower": 2, "charisma": 0},
    "Nekromanta": {"strength": 0, "dexterity": 1, "constitution": 2, "intelligence": 4, "willpower": 2, "charisma": 0},
    "Kapłan":     {"strength": 0, "dexterity": 0, "constitution": 3, "intelligence": 2, "willpower": 4, "charisma": 0},
    "Czarownik":  {"strength": 1, "dexterity": 2, "constitution": 1, "intelligence": 4, "willpower": 1, "charisma": 0},
    "Druid":      {"strength": 0, "dexterity": 1, "constitution": 2, "intelligence": 4, "willpower": 2, "charisma": 0},
    "Psionik":    {"strength": 0, "dexterity": 1, "constitution": 1, "intelligence": 3, "willpower": 4, "charisma": 0},    "Mec":       {"strength": 3, "dexterity": 2, "constitution": 3, "intelligence": 1, "willpower": 0, "charisma": 0},
    "Inżynier":  {"strength": 1, "dexterity": 4, "constitution": 2, "intelligence": 2, "willpower": 0, "charisma": 0},
}

def class_starting_stat_bonus(class_name, stat_name):
    return int(CLASS_STARTING_STAT_BONUSES.get(class_name, {}).get(stat_name, 0))

def class_starting_stats_for(race, cls):
    rname, _desc, strength, dexterity, constitution, intelligence, willpower = race
    cname = cls[0]
    b = CLASS_STARTING_STAT_BONUSES.get(cname, {})
    return {
        "strength": int(strength) + int(b.get("strength", 0)),
        "dexterity": int(dexterity) + int(b.get("dexterity", 0)),
        "constitution": int(constitution) + int(b.get("constitution", 0)),
        "intelligence": int(intelligence) + int(b.get("intelligence", 0)),
        "willpower": int(willpower) + int(b.get("willpower", 0)),
        "charisma": 10 + int(b.get("charisma", 0)),
    }

def starting_hp_mana_for(race, cls):
    stats = class_starting_stats_for(race, cls)
    hp = 40 + stats["constitution"] * 5
    mana = int(round(20 + stats["intelligence"] * 2.5 + stats["willpower"] * 2.5))
    race_name = race[0]
    if race_name == "Ork":
        hp = int(round(hp * 1.10))
    if race_name == "Gnom":
        mana = int(round(mana * 1.15))
    return max(1, hp), max(0, mana)


CLASS_DESCRIPTIONS = {
    "Wojownik": (
        "Klasa fizyczna. Stabilny wojownik do walki wręcz. "
        "Każda z sześciu statystyk ma własny automatyczny EXP. "
        "Dobra dla graczy chcących mocnych ciosów, szybkości i dużej ilości HP."
        "Pasyw klasowy: +10 procent obrażeń fizycznych."
    ),
    "Berserker": (
        "Klasa fizyczna nastawiona na bardzo wysokie obrażenia. "
        "Każda z sześciu statystyk ma własny automatyczny EXP. "
        "Broń Duszy ma wysoki bazowy potencjał ofensywny."
        "Pasyw klasowy: +12 procent obrażeń fizycznych."
    ),
    "Łotrzyk": (
        "Klasa fizyczna nastawiona na szybkość i zwinność. "
        "Każda z sześciu statystyk ma własny automatyczny EXP. "
        "Dobrze korzysta z wysokiej Zręczności i uników."
        "Pasyw klasowy: +5 punktów procentowych do szansy uniku."
    ),
    "Łowca": (
        "Klasa fizyczna walcząca z dystansu. "
        "Każda z sześciu statystyk ma własny automatyczny EXP. "
        "Najlepiej współpracuje z rasami o wysokiej Zręczności."
        "Pasyw klasowy: +8 procent obrażeń fizycznych."
    ),
    "Mnich": (
        "Klasa fizyczna oparta na szybkości i kontroli ciała. "
        "Każda z sześciu statystyk ma własny automatyczny EXP. "
        "Dobrze skaluje się ze Zręcznością oraz Kondycją."
        "Pasyw klasowy: +8 procent mocy klasowych umiejętności leczących."
    ),
    "Strażnik": (
        "Klasa fizyczna nastawiona na przetrwanie. "
        "Każda z sześciu statystyk ma własny automatyczny EXP. "
        "Dobrze wykorzystuje wysoką Kondycję i cięższy pancerz."
        "Pasyw klasowy: 10 procent redukcji wszystkich otrzymywanych obrażeń."
    ),
    "Mag": (
        "Klasa magiczna. Inteligencja zwiększa moc czarów i ataków Bronią Duszy, a Inteligencja razem z Siłą Woli zwiększają Manę, "
        "Zręczność daje szybkość, unik i krytyki, Kondycja zwiększa HP, a Siła Woli obronę magiczną. "
        "Każda z sześciu statystyk ma własny automatyczny EXP."
        "Pasyw klasowy: +10 procent obrażeń magicznych."
    ),
    "Nekromanta": (
        "Klasa magiczna oparta na mrocznej energii i silnych czarach. "
        "Każda z sześciu statystyk ma własny automatyczny EXP. "
        "Dobrze korzysta z wysokiej Inteligencji."
        "Pasyw klasowy: +15 procent leczenia z umiejętności wysysających życie."
    ),
    "Kapłan": (
        "Klasa magiczna o defensywnym charakterze. "
        "Każda z sześciu statystyk ma własny automatyczny EXP. "
        "Wysoka Siła Woli wzmacnia obronę magiczną."
        "Pasyw klasowy: +10 procent mocy klasowych umiejętności leczących."
    ),
    "Czarownik": (
        "Ofensywna klasa magiczna z mocną Bronią Duszy. "
        "Każda z sześciu statystyk ma własny automatyczny EXP. "
        "Dobrze skaluje się z Inteligencją i dużą pulą Many."
        "Pasyw klasowy: +12 procent obrażeń magicznych."
    ),
    "Druid": (
        "Wszechstronna klasa magiczna związana z naturą. "
        "Każda z sześciu statystyk ma własny automatyczny EXP. "
        "Łączy dobrą moc czarów z obroną magiczną."
        "Pasyw klasowy: +10 procent mocy klasowych umiejętności leczących."
    ),
    "Psionik": (
        "Klasa magiczna oparta na mocy umysłu. "
        "Każda z sześciu statystyk ma własny automatyczny EXP. "
        "Najlepiej wykorzystuje wysoką Inteligencję i Siłę Woli."
        "Pasyw klasowy: +10 procent obrony magicznej."
    ),    "Mec": (
        "Technologiczna klasa bojowa oparta na ciężkim pancerzu, rdzeniu energetycznym i uzbrojeniu pokładowym. "
        "Inspiruje się ideą jobu Mec oraz technologicznych jobów UOSSMUD, ale działa według zasad Soulbound. "
        "Pasyw klasowy: 10 procent redukcji wszystkich otrzymywanych obrażeń."
    ),
    "Inżynier": (
        "Zręcznościowa klasa technologiczna korzystająca z narzędzi, działek, skanera, materiałów wybuchowych i urządzeń. "
        "Część nazw i pomysłów na narzędzia inspirowana jest Engineerem UOSSMUD. "
        "Pasyw klasowy: +10 procent obrażeń fizycznych."
    ),
}


CLASS_SKILLS = {'Wojownik': [{'id': 'warrior_power_slash',
               'name': 'Potężne Cięcie',
               'aliases': ['potezne ciecie', 'potężne cięcie', 'power slash'],
               'unlock': 1,
               'kind': 'damage',
               'cooldown': 4,
               'mana': 0,
               'desc': 'Mocny fizyczny cios skalowany Siłą.',
               'scale': 'strength',
               'mult': 1.35},
              {'id': 'warrior_war_cry',
               'name': 'Okrzyk Wojenny',
               'aliases': ['okrzyk wojenny', 'war cry'],
               'unlock': 20,
               'kind': 'boost',
               'cooldown': 12,
               'mana': 0,
               'desc': 'Przez 12 sekund wzmacnia wszystkie skille i spelle o 35 procent.',
               'boost': 1.35,
               'duration': 12},
              {'id': 'warrior_unbreakable',
               'name': 'Niezłomność',
               'aliases': ['niezlomnosc', 'niezłomność', 'unbreakable'],
               'unlock': 60,
               'kind': 'guard',
               'cooldown': 15,
               'mana': 0,
               'desc': 'Zmniejsza obrażenia następnego trafienia o dodatkowe 18.',
               'guard': 18}],
 'Berserker': [{'id': 'berserker_blood_swing',
                'name': 'Krwawy Zamach',
                'aliases': ['krwawy zamach', 'blood swing'],
                'unlock': 1,
                'kind': 'damage',
                'cooldown': 5,
                'mana': 0,
                'desc': 'Bardzo mocny cios Siłą, ale kosztuje 4 HP.',
                'scale': 'strength',
                'mult': 1.5,
                'self_damage': 4},
               {'id': 'berserker_blood_fury',
                'name': 'Szał Krwi',
                'aliases': ['szal krwi', 'szał krwi', 'blood fury'],
                'unlock': 20,
                'kind': 'boost',
                'cooldown': 13,
                'mana': 0,
                'desc': 'Czasowo wzmacnia wszystkie skille i spelle o 55 procent.',
                'boost': 1.55},
               {'id': 'berserker_execution',
                'name': 'Egzekucja',
                'aliases': ['egzekucja', 'execution'],
                'unlock': 60,
                'kind': 'execute',
                'cooldown': 10,
                'mana': 0,
                'desc': 'Silny cios, wyjątkowo mocny poniżej 35 procent HP celu.',
                'scale': 'strength',
                'mult': 1.45,
                'execute_mult': 1.9}],
 'Łotrzyk': [{'id': 'rogue_shadow_strike',
              'name': 'Cios z Cienia',
              'aliases': ['cios z cienia', 'shadow strike'],
              'unlock': 1,
              'kind': 'damage',
              'cooldown': 4,
              'mana': 0,
              'desc': 'Szybki atak skalowany Zręcznością.',
              'scale': 'dexterity',
              'mult': 1.38},
             {'id': 'rogue_double_blade',
              'name': 'Podwójne Ostrze',
              'aliases': ['podwojne ostrze', 'podwójne ostrze', 'double blade'],
              'unlock': 20,
              'kind': 'damage',
              'cooldown': 8,
              'mana': 0,
              'desc': 'Seria dwóch cięć jako jeden silny atak.',
              'scale': 'dexterity',
              'mult': 1.68},
             {'id': 'rogue_vanish',
              'name': 'Zniknięcie',
              'aliases': ['znikniecie', 'zniknięcie', 'vanish'],
              'unlock': 60,
              'kind': 'evade',
              'cooldown': 12,
              'mana': 0,
              'desc': 'Gwarantuje unik następnego ataku przeciwnika.'}],
 'Łowca': [{'id': 'hunter_precise_shot',
            'name': 'Celny Strzał',
            'aliases': ['celny strzal', 'celny strzał', 'precise shot'],
            'unlock': 1,
            'kind': 'damage',
            'cooldown': 4,
            'mana': 0,
            'desc': 'Precyzyjny atak dystansowy skalowany Zręcznością.',
            'scale': 'dexterity',
            'mult': 1.42},
           {'id': 'hunter_echo_volley',
            'name': 'Salwa Echa',
            'aliases': ['salwa echa', 'echo volley'],
            'unlock': 20,
            'kind': 'damage',
            'cooldown': 8,
            'mana': 0,
            'desc': 'Potężna salwa z Łuku Echa.',
            'scale': 'dexterity',
            'mult': 1.72},
           {'id': 'hunter_instinct',
            'name': 'Instynkt Łowcy',
            'aliases': ['instynkt lowcy', 'instynkt łowcy', 'hunter instinct'],
            'unlock': 60,
            'kind': 'evade',
            'cooldown': 10,
            'mana': 0,
            'desc': 'Gwarantuje unik następnego ataku przeciwnika.'}],
 'Mnich': [{'id': 'monk_spirit_punch',
            'name': 'Uderzenie Ducha',
            'aliases': ['uderzenie ducha', 'spirit punch'],
            'unlock': 1,
            'kind': 'damage',
            'cooldown': 3,
            'mana': 0,
            'desc': 'Szybkie uderzenie skalowane Zręcznością.',
            'scale': 'dexterity',
            'mult': 1.32},
           {'id': 'monk_combo',
            'name': 'Seria Ciosów',
            'aliases': ['seria ciosow', 'seria ciosów', 'combo'],
            'unlock': 20,
            'kind': 'damage',
            'cooldown': 7,
            'mana': 0,
            'desc': 'Szybka kombinacja kilku uderzeń.',
            'scale': 'dexterity',
            'mult': 1.65},
           {'id': 'monk_meditation',
            'name': 'Medytacja',
            'aliases': ['medytacja', 'meditation'],
            'unlock': 60,
            'kind': 'heal',
            'cooldown': 16,
            'mana': 0,
            'desc': 'Przywraca 28 procent maksymalnego HP.',
            'heal_pct': 0.28}],
 'Strażnik': [{'id': 'guardian_crushing_blow',
               'name': 'Miażdżący Cios',
               'aliases': ['miazdzacy cios', 'miażdżący cios', 'crushing blow'],
               'unlock': 1,
               'kind': 'damage',
               'cooldown': 4,
               'mana': 0,
               'desc': 'Ciężki fizyczny cios Młotem Bastionu.',
               'scale': 'strength',
               'mult': 1.28},
              {'id': 'guardian_bastion',
               'name': 'Bastion',
               'aliases': ['bastion'],
               'unlock': 20,
               'kind': 'guard',
               'cooldown': 11,
               'mana': 0,
               'desc': 'Zmniejsza obrażenia następnego trafienia o dodatkowe 22.',
               'guard': 22},
              {'id': 'guardian_soul_wall',
               'name': 'Mur Duszy',
               'aliases': ['mur duszy', 'soul wall'],
               'unlock': 60,
               'kind': 'guard',
               'cooldown': 18,
               'mana': 0,
               'desc': 'Potężna osłona redukująca następne trafienie o 35.',
               'guard': 35}],
 'Mag': [{'id': 'mage_arcane_bolt',
          'name': 'Pocisk Arkanów',
          'aliases': ['pocisk arkanow', 'pocisk arkanów', 'arcane bolt'],
          'unlock': 1,
          'kind': 'damage',
          'cooldown': 3,
          'mana': 6,
          'desc': 'Podstawowy czar ofensywny skalowany Inteligencją.',
          'scale': 'intelligence',
          'mult': 1.42},
         {'id': 'mage_chain_energy',
          'name': 'Łańcuch Energii',
          'aliases': ['lancuch energii', 'łańcuch energii', 'chain energy'],
          'unlock': 20,
          'kind': 'damage',
          'cooldown': 7,
          'mana': 12,
          'desc': 'Silny impuls energii magicznej.',
          'scale': 'intelligence',
          'mult': 1.78},
         {'id': 'mage_arcane_barrier',
          'name': 'Bariera Arkanów',
          'aliases': ['bariera arkanow', 'bariera arkanów', 'arcane barrier'],
          'unlock': 60,
          'kind': 'guard',
          'cooldown': 13,
          'mana': 10,
          'desc': 'Magiczna bariera redukująca następne trafienie o 24.',
          'guard': 24}],
 'Nekromanta': [{'id': 'necro_death_touch',
                 'name': 'Dotyk Śmierci',
                 'aliases': ['dotyk smierci', 'dotyk śmierci', 'death touch'],
                 'unlock': 1,
                 'kind': 'damage',
                 'cooldown': 4,
                 'mana': 6,
                 'desc': 'Mroczny atak magiczny skalowany Inteligencją.',
                 'scale': 'intelligence',
                 'mult': 1.38},
                {'id': 'necro_soul_drain',
                 'name': 'Wysysanie Duszy',
                 'aliases': ['wysysanie duszy', 'soul drain'],
                 'unlock': 20,
                 'kind': 'drain',
                 'cooldown': 8,
                 'mana': 10,
                 'desc': 'Zadaje obrażenia i leczy za 45 procent zadanych obrażeń.',
                 'scale': 'intelligence',
                 'mult': 1.45,
                 'drain_pct': 0.45},
                {'id': 'necro_soul_reaping',
                 'name': 'Żniwo Dusz',
                 'aliases': ['zniwo dusz', 'żniwo dusz', 'soul reaping'],
                 'unlock': 60,
                 'kind': 'execute',
                 'cooldown': 11,
                 'mana': 16,
                 'desc': 'Potężny czar silniejszy poniżej 35 procent HP celu.',
                 'scale': 'intelligence',
                 'mult': 1.65,
                 'execute_mult': 1.75}],
 'Kapłan': [{'id': 'priest_small_heal',
             'name': 'Małe Leczenie',
             'aliases': ['male leczenie', 'małe leczenie', 'small heal'],
             'unlock': 1,
             'kind': 'heal',
             'cooldown': 6,
             'mana': 3,
             'desc': 'Podstawowe leczenie dla początkujących Kapłanów. Przywraca 12 procent maksymalnego HP i rośnie wraz ze Skill Level.',
             'heal_pct': 0.12},
            {'id': 'priest_holy_hammer',
             'name': 'Święty Młot',
             'aliases': ['swiety mlot', 'święty młot', 'holy hammer'],
             'unlock': 1,
             'kind': 'damage',
             'cooldown': 4,
             'mana': 5,
             'desc': 'Święty atak magiczny skalowany Inteligencją.',
             'scale': 'intelligence',
             'mult': 1.28},
            {'id': 'priest_great_heal',
             'name': 'Wielkie Leczenie',
             'aliases': ['wielkie leczenie', 'great heal'],
             'unlock': 20,
             'kind': 'heal',
             'cooldown': 14,
             'mana': 10,
             'desc': 'Przywraca 38 procent maksymalnego HP.',
             'heal_pct': 0.38},
            {'id': 'priest_divine_shield',
             'name': 'Boska Tarcza',
             'aliases': ['boska tarcza', 'divine shield'],
             'unlock': 60,
             'kind': 'guard',
             'cooldown': 17,
             'mana': 12,
             'desc': 'Silna tarcza redukująca następne trafienie o 32.',
             'guard': 32}],
 'Czarownik': [{'id': 'warlock_void_blade',
                'name': 'Ostrze Otchłani',
                'aliases': ['ostrze otchlani', 'ostrze otchłani', 'void blade'],
                'unlock': 1,
                'kind': 'damage',
                'cooldown': 4,
                'mana': 7,
                'desc': 'Ofensywny czar Ostrza Otchłani.',
                'scale': 'intelligence',
                'mult': 1.48},
               {'id': 'warlock_void_flame',
                'name': 'Płomień Otchłani',
                'aliases': ['plomien otchlani', 'płomień otchłani', 'void flame'],
                'unlock': 20,
                'kind': 'damage',
                'cooldown': 8,
                'mana': 13,
                'desc': 'Bardzo mocny magiczny atak.',
                'scale': 'intelligence',
                'mult': 1.85},
               {'id': 'warlock_blood_pact',
                'name': 'Pakt Krwi',
                'aliases': ['pakt krwi', 'blood pact'],
                'unlock': 60,
                'kind': 'damage',
                'cooldown': 12,
                'mana': 8,
                'desc': 'Ekstremalnie silny czar kosztujący dodatkowo 10 procent maksymalnego HP.',
                'scale': 'intelligence',
                'mult': 2.15,
                'self_damage_pct': 0.1}],
 'Druid': [{'id': 'druid_thorns',
            'name': 'Ciernie',
            'aliases': ['ciernie', 'thorns'],
            'unlock': 1,
            'kind': 'damage',
            'cooldown': 4,
            'mana': 5,
            'desc': 'Magiczny atak natury skalowany Inteligencją.',
            'scale': 'intelligence',
            'mult': 1.32},
           {'id': 'druid_nature_heal',
            'name': 'Uzdrowienie Natury',
            'aliases': ['uzdrowienie natury', 'nature heal'],
            'unlock': 20,
            'kind': 'heal',
            'cooldown': 13,
            'mana': 9,
            'desc': 'Przywraca 32 procent maksymalnego HP.',
            'heal_pct': 0.32},
           {'id': 'druid_storm_wrath',
            'name': 'Gniew Burzy',
            'aliases': ['gniew burzy', 'storm wrath'],
            'unlock': 60,
            'kind': 'damage',
            'cooldown': 10,
            'mana': 15,
            'desc': 'Potężny czar burzy.',
            'scale': 'intelligence',
            'mult': 1.92}],
 'Psionik': [{'id': 'psion_mind_pulse',
              'name': 'Impuls Umysłu',
              'aliases': ['impuls umyslu', 'impuls umysłu', 'mind pulse'],
              'unlock': 1,
              'kind': 'damage',
              'cooldown': 3,
              'mana': 5,
              'desc': 'Szybki psioniczny atak skalowany Inteligencją.',
              'scale': 'intelligence',
              'mult': 1.38},
             {'id': 'psion_psionic_wave',
              'name': 'Fala Psioniczna',
              'aliases': ['fala psioniczna', 'psionic wave'],
              'unlock': 20,
              'kind': 'damage',
              'cooldown': 7,
              'mana': 11,
              'desc': 'Silna fala energii umysłu.',
              'scale': 'intelligence',
              'mult': 1.75},
             {'id': 'psion_mind_barrier',
              'name': 'Bariera Umysłu',
              'aliases': ['bariera umyslu', 'bariera umysłu', 'mind barrier'],
              'unlock': 60,
              'kind': 'guard',
              'cooldown': 14,
              'mana': 10,
              'desc': 'Psioniczna bariera redukująca następne obrażenia o 28.',
              'guard': 28}]}


ENDGAME_CLASS_SKILLS = {
    "Wojownik": [
        {
            "id": "warrior_soul_rend",
            "name": "Rozcięcie Duszy Bohatera",
            "aliases": ["rozciecie duszy bohatera", "rozcięcie duszy bohatera", "hero soul slash"],
            "natural_tags": ["ciecie", "slash", "dusza"],
            "unlock": 100, "kind": "damage", "cooldown": 8, "mana": 0,
            "desc": "Silne cięcie końcowego etapu Wojownika.",
            "scale": "strength", "mult": 2.10,
        },
        {
            "id": "warrior_iron_wall",
            "name": "Żelazny Mur",
            "aliases": ["zelazny mur", "żelazny mur", "iron wall"],
            "natural_tags": ["tarcza", "oslona", "guard", "obrona"],
            "unlock": 140, "kind": "guard", "cooldown": 13, "mana": 0,
            "desc": "Potężna osłona Wojownika redukująca następne trafienie.",
            "guard": 58,
        },
        {
            "id": "warrior_hero_charge",
            "name": "Szarża Bohatera",
            "aliases": ["szarza bohatera", "szarża bohatera", "hero charge"],
            "natural_tags": ["szarza", "charge", "atak"],
            "unlock": 180, "kind": "damage", "cooldown": 11, "mana": 0,
            "desc": "Mocna szarża skalowana Siłą.",
            "scale": "strength", "mult": 2.55,
        },
        {
            "id": "warrior_final_slash",
            "name": "Ostateczne Cięcie",
            "aliases": ["ostateczne ciecie", "ostateczne cięcie", "final slash"],
            "natural_tags": ["ciecie", "slash", "dobij", "egzekucja"],
            "unlock": 200, "kind": "execute", "cooldown": 16, "mana": 0,
            "desc": "Najsilniejsze cięcie Wojownika, szczególnie groźne na osłabionym celu.",
            "scale": "strength", "mult": 2.55, "execute_mult": 1.90,
        },
    ],
    "Berserker": [
        {
            "id": "berserker_butcher_swing",
            "name": "Rzeźniczy Zamach",
            "aliases": ["rzezniczy zamach", "rzeźniczy zamach", "butcher swing"],
            "natural_tags": ["zamach", "ciecie", "atak"],
            "unlock": 100, "kind": "damage", "cooldown": 8, "mana": 0,
            "desc": "Brutalny zamach Berserkera skalowany Siłą.",
            "scale": "strength", "mult": 2.20,
        },
        {
            "id": "berserker_titan_rage",
            "name": "Szał Tytana",
            "aliases": ["szal tytana", "szał tytana", "titan rage"],
            "natural_tags": ["szal", "rage", "buff", "wzmocnienie"],
            "unlock": 140, "kind": "boost", "cooldown": 15, "mana": 0,
            "desc": "Czasowo wzmacnia wszystkie skille i spelle.",
            "boost": 1.65,
        },
        {
            "id": "berserker_blood_whirl",
            "name": "Krwawy Wir",
            "aliases": ["krwawy wir", "blood whirl"],
            "natural_tags": ["krew", "wir", "drain", "wysysanie"],
            "unlock": 180, "kind": "drain", "cooldown": 12, "mana": 0,
            "desc": "Krwawy atak, który przywraca część zadanych obrażeń jako HP.",
            "scale": "strength", "mult": 2.45, "drain_pct": 0.35,
        },
        {
            "id": "berserker_blood_apocalypse",
            "name": "Apokalipsa Krwi",
            "aliases": ["apokalipsa krwi", "blood apocalypse"],
            "natural_tags": ["krew", "apokalipsa", "dobij", "egzekucja"],
            "unlock": 200, "kind": "execute", "cooldown": 17, "mana": 0,
            "desc": "Ostateczny atak Berserkera, jeszcze silniejszy na osłabionym przeciwniku.",
            "scale": "strength", "mult": 2.65, "execute_mult": 1.95,
        },
    ],
    "Łotrzyk": [
        {
            "id": "rogue_spectral_cut",
            "name": "Cięcie Widma",
            "aliases": ["ciecie widma", "cięcie widma", "spectral cut"],
            "natural_tags": ["ciecie", "slash", "widmo"],
            "unlock": 100, "kind": "damage", "cooldown": 6, "mana": 0,
            "desc": "Błyskawiczne cięcie skalowane Zręcznością.",
            "scale": "dexterity", "mult": 2.05,
        },
        {
            "id": "rogue_shadow_step",
            "name": "Krok Cienia",
            "aliases": ["krok cienia", "shadow step"],
            "natural_tags": ["unik", "evade", "cien"],
            "unlock": 140, "kind": "evade", "cooldown": 11, "mana": 0,
            "desc": "Gwarantuje unik następnego ataku przeciwnika.",
        },
        {
            "id": "rogue_blade_dance",
            "name": "Taniec Ostrzy",
            "aliases": ["taniec ostrzy", "blade dance"],
            "natural_tags": ["ostrza", "taniec", "atak"],
            "unlock": 180, "kind": "damage", "cooldown": 10, "mana": 0,
            "desc": "Seria szybkich cięć skalowana Zręcznością.",
            "scale": "dexterity", "mult": 2.55,
        },
        {
            "id": "rogue_shadow_execution",
            "name": "Egzekucja Cienia",
            "aliases": ["egzekucja cienia", "shadow execution"],
            "natural_tags": ["egzekucja", "execute", "dobij", "cien"],
            "unlock": 200, "kind": "execute", "cooldown": 15, "mana": 0,
            "desc": "Kończący cios Łotrzyka na osłabionego przeciwnika.",
            "scale": "dexterity", "mult": 2.50, "execute_mult": 2.00,
        },
    ],
    "Łowca": [
        {
            "id": "hunter_soul_arrow",
            "name": "Strzała Duszy",
            "aliases": ["strzala duszy", "strzała duszy", "soul arrow"],
            "natural_tags": ["strzala", "arrow", "strzal"],
            "unlock": 100, "kind": "damage", "cooldown": 7, "mana": 0,
            "desc": "Silny strzał skalowany Zręcznością.",
            "scale": "dexterity", "mult": 2.10,
        },
        {
            "id": "hunter_predator_camouflage",
            "name": "Kamuflaż Drapieżcy",
            "aliases": ["kamuflaz drapieznika", "kamuflaż drapieżcy", "predator camouflage"],
            "natural_tags": ["unik", "evade", "kamuflaz"],
            "unlock": 140, "kind": "evade", "cooldown": 12, "mana": 0,
            "desc": "Pozwala uniknąć następnego ataku przeciwnika.",
        },
        {
            "id": "hunter_echo_rain",
            "name": "Deszcz Echa",
            "aliases": ["deszcz echa", "echo rain"],
            "natural_tags": ["deszcz", "strzaly", "arrow", "atak"],
            "unlock": 180, "kind": "damage", "cooldown": 11, "mana": 0,
            "desc": "Potężna salwa skalowana Zręcznością.",
            "scale": "dexterity", "mult": 2.60,
        },
        {
            "id": "hunter_final_shot",
            "name": "Strzał Końca",
            "aliases": ["strzal konca", "strzał końca", "final shot"],
            "natural_tags": ["strzal", "shot", "dobij", "egzekucja"],
            "unlock": 200, "kind": "execute", "cooldown": 16, "mana": 0,
            "desc": "Ostateczny strzał Łowcy, wyjątkowo mocny na osłabionym celu.",
            "scale": "dexterity", "mult": 2.55, "execute_mult": 1.90,
        },
    ],
    "Mnich": [
        {
            "id": "monk_soul_fist",
            "name": "Pięść Duszy",
            "aliases": ["piesc duszy", "pięść duszy", "soul fist"],
            "natural_tags": ["piesc", "fist", "atak"],
            "unlock": 100, "kind": "damage", "cooldown": 6, "mana": 0,
            "desc": "Skoncentrowane uderzenie skalowane Siłą.",
            "scale": "strength", "mult": 2.05,
        },
        {
            "id": "monk_master_meditation",
            "name": "Medytacja Mistrza",
            "aliases": ["medytacja mistrza", "master meditation"],
            "natural_tags": ["heal", "leczenie", "medytacja", "odnowa"],
            "unlock": 140, "kind": "heal", "cooldown": 12, "mana": 0,
            "desc": "Zaawansowana medytacja przywracająca dużą część HP.",
            "heal_pct": 0.38,
        },
        {
            "id": "monk_dragon_combo",
            "name": "Smocza Seria",
            "aliases": ["smocza seria", "dragon combo"],
            "natural_tags": ["seria", "combo", "smok", "atak"],
            "unlock": 180, "kind": "damage", "cooldown": 10, "mana": 0,
            "desc": "Szybka seria ciosów o wysokiej sile.",
            "scale": "strength", "mult": 2.50,
        },
        {
            "id": "monk_enlightened_strike",
            "name": "Cios Oświecenia",
            "aliases": ["cios oswiecenia", "cios oświecenia", "enlightened strike"],
            "natural_tags": ["cios", "oswiecenie", "dobij", "egzekucja"],
            "unlock": 200, "kind": "execute", "cooldown": 15, "mana": 0,
            "desc": "Ostateczny cios Mnicha, silniejszy na osłabionym przeciwniku.",
            "scale": "strength", "mult": 2.45, "execute_mult": 1.90,
        },
    ],
    "Strażnik": [
        {
            "id": "guardian_fortress_strike",
            "name": "Uderzenie Fortecy",
            "aliases": ["uderzenie fortecy", "fortress strike"],
            "natural_tags": ["uderzenie", "mlot", "hammer", "atak"],
            "unlock": 100, "kind": "damage", "cooldown": 7, "mana": 0,
            "desc": "Ciężkie uderzenie skalowane Siłą.",
            "scale": "strength", "mult": 2.00,
        },
        {
            "id": "guardian_eternal_bastion",
            "name": "Wieczny Bastion",
            "aliases": ["wieczny bastion", "eternal bastion"],
            "natural_tags": ["tarcza", "bastion", "guard", "obrona"],
            "unlock": 140, "kind": "guard", "cooldown": 14, "mana": 0,
            "desc": "Najpotężniejsza osłona Strażnika.",
            "guard": 72,
        },
        {
            "id": "guardian_bastion_wrath",
            "name": "Gniew Bastionu",
            "aliases": ["gniew bastionu", "bastion wrath"],
            "natural_tags": ["gniew", "mlot", "hammer", "atak"],
            "unlock": 180, "kind": "damage", "cooldown": 11, "mana": 0,
            "desc": "Potężny atak Strażnika.",
            "scale": "strength", "mult": 2.45,
        },
        {
            "id": "guardian_final_hammer",
            "name": "Młot Końca",
            "aliases": ["mlot konca", "młot końca", "final hammer"],
            "natural_tags": ["mlot", "hammer", "dobij", "egzekucja"],
            "unlock": 200, "kind": "execute", "cooldown": 17, "mana": 0,
            "desc": "Ostateczne uderzenie Strażnika.",
            "scale": "strength", "mult": 2.60, "execute_mult": 1.85,
        },
    ],
    "Mag": [
        {
            "id": "mage_arcane_lance",
            "name": "Lanca Arkanów",
            "aliases": ["lanca arkanow", "lanca arkanów", "arcane lance"],
            "natural_tags": ["pocisk", "bolt", "lanca", "arkany"],
            "unlock": 100, "kind": "damage", "cooldown": 6, "mana": 18,
            "desc": "Skoncentrowany czar ofensywny skalowany Inteligencją.",
            "scale": "intelligence", "mult": 2.20,
        },
        {
            "id": "mage_arcane_aegis",
            "name": "Aegis Arkanów",
            "aliases": ["aegis arkanow", "aegis arkanów", "arcane aegis"],
            "natural_tags": ["tarcza", "oslona", "guard", "arkany"],
            "unlock": 140, "kind": "guard", "cooldown": 13, "mana": 16,
            "desc": "Silna magiczna osłona.",
            "guard": 62,
        },
        {
            "id": "mage_mana_tempest",
            "name": "Burza Many",
            "aliases": ["burza many", "mana tempest"],
            "natural_tags": ["burza", "storm", "mana", "atak"],
            "unlock": 180, "kind": "damage", "cooldown": 10, "mana": 26,
            "desc": "Potężny wybuch Many skalowany Inteligencją.",
            "scale": "intelligence", "mult": 2.75,
        },
        {
            "id": "mage_arcane_cataclysm",
            "name": "Kataklizm Arkanów",
            "aliases": ["kataklizm arkanow", "kataklizm arkanów", "arcane cataclysm"],
            "natural_tags": ["kataklizm", "arkany", "czar", "atak"],
            "unlock": 200, "kind": "damage", "cooldown": 16, "mana": 35,
            "desc": "Najsilniejszy czar Maga.",
            "scale": "intelligence", "mult": 3.25,
        },
    ],
    "Nekromanta": [
        {
            "id": "necromancer_bone_curse",
            "name": "Klątwa Kości",
            "aliases": ["klatwa kosci", "klątwa kości", "bone curse"],
            "natural_tags": ["klatwa", "kosci", "czar", "atak"],
            "unlock": 100, "kind": "damage", "cooldown": 7, "mana": 17,
            "desc": "Nekromantyczna klątwa skalowana Inteligencją.",
            "scale": "intelligence", "mult": 2.15,
        },
        {
            "id": "necromancer_greater_drain",
            "name": "Wielkie Wysysanie",
            "aliases": ["wielkie wysysanie", "greater drain"],
            "natural_tags": ["drain", "wysysanie", "leech"],
            "unlock": 140, "kind": "drain", "cooldown": 10, "mana": 20,
            "desc": "Silny drenaż życia.",
            "scale": "intelligence", "mult": 2.25, "drain_pct": 0.50,
        },
        {
            "id": "necromancer_dead_reaping",
            "name": "Żniwo Umarłych",
            "aliases": ["zniwo umarlych", "żniwo umarłych", "reaping of the dead"],
            "natural_tags": ["zniwo", "drain", "wysysanie"],
            "unlock": 180, "kind": "drain", "cooldown": 12, "mana": 28,
            "desc": "Potężne żniwo dusz przywracające część HP.",
            "scale": "intelligence", "mult": 2.70, "drain_pct": 0.55,
        },
        {
            "id": "necromancer_death_sentence",
            "name": "Wyrok Śmierci",
            "aliases": ["wyrok smierci", "wyrok śmierci", "death sentence"],
            "natural_tags": ["smierc", "wyrok", "dobij", "egzekucja"],
            "unlock": 200, "kind": "execute", "cooldown": 17, "mana": 34,
            "desc": "Ostateczny nekromantyczny wyrok na osłabionym celu.",
            "scale": "intelligence", "mult": 2.80, "execute_mult": 2.00,
        },
    ],
    "Kapłan": [
        {
            "id": "priest_light_beam",
            "name": "Promień Światła",
            "aliases": ["promien swiatla", "promień światła", "light beam"],
            "natural_tags": ["swiatlo", "promien", "czar", "atak"],
            "unlock": 100, "kind": "damage", "cooldown": 6, "mana": 17,
            "desc": "Silny święty atak skalowany Inteligencją.",
            "scale": "intelligence", "mult": 2.10,
        },
        {
            "id": "priest_greater_restoration",
            "name": "Wielkie Uzdrowienie",
            "aliases": ["wielkie uzdrowienie", "greater restoration"],
            "natural_tags": ["heal", "leczenie", "uzdrowienie", "odnowa"],
            "unlock": 140, "kind": "heal", "cooldown": 10, "mana": 20,
            "desc": "Potężne leczenie Kapłana.",
            "heal_pct": 0.48,
        },
        {
            "id": "priest_aegis_of_light",
            "name": "Aegis Światła",
            "aliases": ["aegis swiatla", "aegis światła", "aegis of light"],
            "natural_tags": ["tarcza", "oslona", "guard", "swiatlo"],
            "unlock": 180, "kind": "guard", "cooldown": 13, "mana": 24,
            "desc": "Święta osłona redukująca następne trafienie.",
            "guard": 68,
        },
        {
            "id": "priest_miracle_rebirth",
            "name": "Cud Odrodzenia",
            "aliases": ["cud odrodzenia", "miracle of rebirth"],
            "natural_tags": ["heal", "leczenie", "cud", "odrodzenie"],
            "unlock": 200, "kind": "heal", "cooldown": 17, "mana": 32,
            "desc": "Najsilniejsze leczenie Kapłana.",
            "heal_pct": 0.68,
        },
    ],
    "Czarownik": [
        {
            "id": "warlock_void_fire",
            "name": "Ogień Pustki",
            "aliases": ["ogien pustki", "ogień pustki", "void fire"],
            "natural_tags": ["ogien", "plomien", "fire", "pustka"],
            "unlock": 100, "kind": "damage", "cooldown": 7, "mana": 18,
            "desc": "Silny ognisty czar Otchłani.",
            "scale": "intelligence", "mult": 2.25,
        },
        {
            "id": "warlock_void_shield",
            "name": "Tarcza Otchłani",
            "aliases": ["tarcza otchlani", "tarcza otchłani", "void shield"],
            "natural_tags": ["tarcza", "oslona", "guard", "pustka"],
            "unlock": 140, "kind": "guard", "cooldown": 13, "mana": 18,
            "desc": "Mroczna osłona Czarownika.",
            "guard": 58,
        },
        {
            "id": "warlock_abyss_inferno",
            "name": "Inferno Otchłani",
            "aliases": ["inferno otchlani", "inferno otchłani", "abyss inferno"],
            "natural_tags": ["ogien", "plomien", "fire", "inferno"],
            "unlock": 180, "kind": "damage", "cooldown": 11, "mana": 29,
            "desc": "Potężne inferno skalowane Inteligencją.",
            "scale": "intelligence", "mult": 2.85,
        },
        {
            "id": "warlock_hell_judgment",
            "name": "Piekielny Wyrok",
            "aliases": ["piekielny wyrok", "hell judgment"],
            "natural_tags": ["ogien", "wyrok", "dobij", "egzekucja"],
            "unlock": 200, "kind": "execute", "cooldown": 17, "mana": 35,
            "desc": "Ostateczny czar Czarownika, szczególnie silny na osłabionym celu.",
            "scale": "intelligence", "mult": 2.80, "execute_mult": 1.95,
        },
    ],
    "Druid": [
        {
            "id": "druid_ancient_roots",
            "name": "Pradawne Korzenie",
            "aliases": ["pradawne korzenie", "ancient roots"],
            "natural_tags": ["korzenie", "natura", "atak"],
            "unlock": 100, "kind": "damage", "cooldown": 7, "mana": 17,
            "desc": "Pradawna magia natury skalowana Inteligencją.",
            "scale": "intelligence", "mult": 2.10,
        },
        {
            "id": "druid_grove_restoration",
            "name": "Odnowa Gaju",
            "aliases": ["odnowa gaju", "grove restoration"],
            "natural_tags": ["heal", "leczenie", "odnowa", "natura"],
            "unlock": 140, "kind": "heal", "cooldown": 11, "mana": 18,
            "desc": "Silna regeneracja Druida.",
            "heal_pct": 0.42,
        },
        {
            "id": "druid_elemental_storm",
            "name": "Burza Żywiołów",
            "aliases": ["burza zywiolow", "burza żywiołów", "elemental storm"],
            "natural_tags": ["burza", "storm", "zywioly", "atak"],
            "unlock": 180, "kind": "damage", "cooldown": 11, "mana": 28,
            "desc": "Potężna burza żywiołów.",
            "scale": "intelligence", "mult": 2.70,
        },
        {
            "id": "druid_worldtree_wrath",
            "name": "Gniew Drzewa Świata",
            "aliases": ["gniew drzewa swiata", "gniew drzewa świata", "worldtree wrath"],
            "natural_tags": ["gniew", "drzewo", "natura", "atak"],
            "unlock": 200, "kind": "damage", "cooldown": 16, "mana": 34,
            "desc": "Najsilniejszy ofensywny czar Druida.",
            "scale": "intelligence", "mult": 3.10,
        },
    ],
    "Psionik": [
        {
            "id": "psion_mind_blade",
            "name": "Ostrze Umysłu",
            "aliases": ["ostrze umyslu", "ostrze umysłu", "mind blade"],
            "natural_tags": ["ostrze", "umysl", "atak"],
            "unlock": 100, "kind": "damage", "cooldown": 6, "mana": 17,
            "desc": "Psioniczne ostrze skalowane Inteligencją.",
            "scale": "intelligence", "mult": 2.20,
        },
        {
            "id": "psion_mind_fortress",
            "name": "Forteca Umysłu",
            "aliases": ["forteca umyslu", "forteca umysłu", "mind fortress"],
            "natural_tags": ["tarcza", "oslona", "guard", "umysl"],
            "unlock": 140, "kind": "guard", "cooldown": 13, "mana": 18,
            "desc": "Potężna psioniczna osłona.",
            "guard": 64,
        },
        {
            "id": "psion_psyche_rend",
            "name": "Rozdarcie Jaźni",
            "aliases": ["rozdarcie jazni", "rozdarcie jaźni", "psyche rend"],
            "natural_tags": ["rozdarcie", "umysl", "atak"],
            "unlock": 180, "kind": "damage", "cooldown": 10, "mana": 28,
            "desc": "Potężny atak psioniczny.",
            "scale": "intelligence", "mult": 2.75,
        },
        {
            "id": "psion_end_of_thought",
            "name": "Koniec Myśli",
            "aliases": ["koniec mysli", "koniec myśli", "end of thought"],
            "natural_tags": ["mysl", "umysl", "dobij", "egzekucja"],
            "unlock": 200, "kind": "execute", "cooldown": 17, "mana": 35,
            "desc": "Ostateczny psioniczny cios na osłabionego przeciwnika.",
            "scale": "intelligence", "mult": 2.75, "execute_mult": 1.95,
        },
    ],
}

for _class_name, _skills in ENDGAME_CLASS_SKILLS.items():
    CLASS_SKILLS.setdefault(_class_name, []).extend(_skills)


AREA_MAGIC_AND_GROUP_HEALING_SKILLS = {
    "Mag": [
        {"id":"mage_arcane_explosion","name":"Eksplozja Arkanów","aliases":["eksplozja arkanow","eksplozja arkanów","arcane explosion"],"natural_tags":["aoe","obszar","arkany"],"unlock":40,"kind":"aoe_damage","cooldown":10,"mana":18,"desc":"Obszarowy czar Maga trafiający wszystkich dostępnych przeciwników w lokacji.","scale":"intelligence","mult":1.35},
        {"id":"mage_meteor_storm","name":"Burza Meteorów","aliases":["burza meteorow","burza meteorów","meteor storm"],"natural_tags":["aoe","obszar","meteor"],"unlock":160,"kind":"aoe_damage","cooldown":18,"mana":36,"desc":"Potężny obszarowy czar Maga na wszystkich przeciwników w lokacji.","scale":"intelligence","mult":2.20},
    ],
    "Nekromanta": [
        {"id":"necro_soul_plague","name":"Plaga Dusz","aliases":["plaga dusz","soul plague"],"natural_tags":["aoe","obszar","plaga"],"unlock":40,"kind":"aoe_damage","cooldown":11,"mana":18,"desc":"Plaga nekromantyczna uderzająca wszystkich przeciwników w lokacji.","scale":"intelligence","mult":1.30},
        {"id":"necro_grave_tempest","name":"Nawałnica Grobów","aliases":["nawalnica grobow","nawałnica grobów","grave tempest"],"natural_tags":["aoe","obszar","grob"],"unlock":160,"kind":"aoe_damage","cooldown":19,"mana":35,"desc":"Potężna fala śmierci obejmująca wszystkich przeciwników w lokacji.","scale":"intelligence","mult":2.10},
    ],
    "Czarownik": [
        {"id":"warlock_void_nova","name":"Nova Otchłani","aliases":["nova otchlani","nova otchłani","void nova"],"natural_tags":["aoe","obszar","nova","pustka"],"unlock":40,"kind":"aoe_damage","cooldown":11,"mana":20,"desc":"Eksplozja Otchłani zadająca obrażenia wszystkim przeciwnikom w lokacji.","scale":"intelligence","mult":1.42},
        {"id":"warlock_void_rain","name":"Deszcz Pustki","aliases":["deszcz pustki","void rain"],"natural_tags":["aoe","obszar","pustka"],"unlock":160,"kind":"aoe_damage","cooldown":18,"mana":38,"desc":"Endgameowy czar obszarowy Czarownika na wszystkich przeciwników w lokacji.","scale":"intelligence","mult":2.30},
    ],
    "Druid": [
        {"id":"druid_hurricane","name":"Huragan","aliases":["huragan","hurricane"],"natural_tags":["aoe","obszar","burza"],"unlock":40,"kind":"aoe_damage","cooldown":11,"mana":17,"desc":"Obszarowy huragan natury uderzający wszystkich przeciwników w lokacji.","scale":"intelligence","mult":1.28},
        {"id":"druid_starfall","name":"Deszcz Gwiazd","aliases":["deszcz gwiazd","starfall"],"natural_tags":["aoe","obszar","gwiazdy"],"unlock":160,"kind":"aoe_damage","cooldown":18,"mana":34,"desc":"Silny obszarowy czar Druida trafiający wszystkich przeciwników w lokacji.","scale":"intelligence","mult":2.00},
    ],
    "Psionik": [
        {"id":"psion_mind_storm","name":"Burza Umysłów","aliases":["burza umyslow","burza umysłów","mind storm"],"natural_tags":["aoe","obszar","umysl"],"unlock":40,"kind":"aoe_damage","cooldown":10,"mana":18,"desc":"Psioniczna fala obszarowa uderzająca wszystkie dostępne cele w lokacji.","scale":"intelligence","mult":1.34},
        {"id":"psion_psychic_collapse","name":"Psychiczne Załamanie","aliases":["psychiczne zalamanie","psychiczne załamanie","psychic collapse"],"natural_tags":["aoe","obszar","psychic"],"unlock":160,"kind":"aoe_damage","cooldown":18,"mana":35,"desc":"Potężne obszarowe uderzenie psioniczne na wszystkich przeciwników w lokacji.","scale":"intelligence","mult":2.12},
    ],
    "Kapłan": [
        {"id":"priest_prayer_of_renewal","name":"Modlitwa Odnowy","aliases":["modlitwa odnowy","prayer of renewal","group heal"],"natural_tags":["heal","leczenie","grupa","druzyna"],"unlock":40,"kind":"group_heal","cooldown":13,"mana":16,"desc":"Obszarowe leczenie Kapłana dla całej drużyny w tej samej lokacji.","heal_pct":0.24},
        {"id":"priest_mass_restoration","name":"Masowe Uzdrowienie","aliases":["masowe uzdrowienie","mass restoration","mass heal"],"natural_tags":["heal","leczenie","grupa","druzyna"],"unlock":160,"kind":"group_heal","cooldown":20,"mana":34,"desc":"Potężne obszarowe leczenie całej drużyny Kapłana w tej samej lokacji.","heal_pct":0.46},
    ],
}
for _class_name, _skills in AREA_MAGIC_AND_GROUP_HEALING_SKILLS.items():
    CLASS_SKILLS.setdefault(_class_name, []).extend(_skills)


# v0.8.25 utworzyło pełną siatkę skilli w dawnych progach Soul 1-200.
# v0.8.41 przeniosło odblokowanie na Biegłość klasy.
# v0.8.42 rozszerza Biegłość każdej klasy do 200 i zachowuje progi 1-200
# bez dzielenia ich przez dwa. Postać nadal NIE ma levelu postaci.
SOUL_SKILL_UNLOCK_LEVELS = tuple([1] + list(range(10, SOUL_MAX_LEVEL + 1, 10)))

_SOUL_GRID_CLASS_PROFILES = {
    "Wojownik":   {"prefix":"warrior_grid",   "scale":"strength",     "magic":False},
    "Berserker":  {"prefix":"berserker_grid", "scale":"strength",     "magic":False},
    "Łotrzyk":    {"prefix":"rogue_grid",     "scale":"dexterity",    "magic":False},
    "Łowca":      {"prefix":"hunter_grid",    "scale":"dexterity",    "magic":False},
    "Mnich":      {"prefix":"monk_grid",      "scale":"dexterity",    "magic":False},
    "Strażnik":   {"prefix":"guardian_grid",  "scale":"strength",     "magic":False},
    "Mag":        {"prefix":"mage_grid",      "scale":"intelligence", "magic":True},
    "Nekromanta": {"prefix":"necro_grid",     "scale":"intelligence", "magic":True},
    "Kapłan":     {"prefix":"priest_grid",    "scale":"intelligence", "magic":True},
    "Czarownik":  {"prefix":"warlock_grid",   "scale":"intelligence", "magic":True},
    "Druid":      {"prefix":"druid_grid",     "scale":"intelligence", "magic":True},
    "Psionik":    {"prefix":"psion_grid",     "scale":"intelligence", "magic":True},
}

# Tylko brakujące progi. Istniejące umiejętności z wcześniejszych wersji
# zostają zachowane i dalej mają te same ID, Skill Level oraz Skill XP.
SOUL_LEVEL_SKILL_EXPANSION = {
    "Wojownik": [
        (10,"Cięcie Straży","damage"),(30,"Żelazny Impet","boost"),
        (40,"Wir Ostrza","damage"),(50,"Przełamanie Gardy","damage"),
        (70,"Marsz Wojenny","guard"),(80,"Cięcie Weterana","damage"),
        (90,"Szturm Duszy","execute"),(110,"Ostrze Bohatera","damage"),
        (120,"Stalowa Postawa","guard"),(130,"Rozszczepienie Pancerza","damage"),
        (150,"Gniew Czempiona","boost"),(160,"Wir Bohatera","damage"),
        (170,"Natarcie Legendy","damage"),(190,"Wyrok Wojownika","execute"),
    ],
    "Berserker": [
        (10,"Krwawy Cios","damage"),(30,"Wściekły Ryk","boost"),
        (40,"Rzeźniczy Wir","damage"),(50,"Rozłupanie","damage"),
        (70,"Skóra Furii","guard"),(80,"Łamacz Kości","damage"),
        (90,"Krwawa Egzekucja","execute"),(110,"Szał Rzezi","damage"),
        (120,"Niepowstrzymany","boost"),(130,"Rozdarcie Ciała","damage"),
        (150,"Furia Przodków","boost"),(160,"Wir Rzezi","damage"),
        (170,"Gniew Kolosa","drain"),(190,"Ostatnia Rzeź","execute"),
    ],
    "Łotrzyk": [
        (10,"Szybkie Ostrze","damage"),(30,"Cienisty Impet","boost"),
        (40,"Wir Sztyletów","damage"),(50,"Pchnięcie w Lukę","damage"),
        (70,"Unik Widma","evade"),(80,"Potrójne Cięcie","damage"),
        (90,"Cichy Wyrok","execute"),(110,"Ostrze Nocy","damage"),
        (120,"Zasłona Cienia","evade"),(130,"Rozprucie","damage"),
        (150,"Zabójczy Rytm","boost"),(160,"Taniec Sztyletów","damage"),
        (170,"Skok Zabójcy","damage"),(190,"Ostatni Cień","execute"),
    ],
    "Łowca": [
        (10,"Szybki Strzał","damage"),(30,"Sokoli Wzrok","boost"),
        (40,"Deszcz Strzał","damage"),(50,"Strzał Przebijający","damage"),
        (70,"Unik Tropiciela","evade"),(80,"Potrójna Salwa","damage"),
        (90,"Strzał Łowcy","execute"),(110,"Strzała Widma","damage"),
        (120,"Zasadzka","evade"),(130,"Strzał w Słaby Punkt","damage"),
        (150,"Sokole Skupienie Mistrza","boost"),(160,"Nawałnica Strzał","damage"),
        (170,"Polowanie Legendy","damage"),(190,"Ostatnia Strzała","execute"),
    ],
    "Mnich": [
        (10,"Szybka Pięść","damage"),(30,"Oddech Wojownika","heal"),
        (40,"Wirujący Kop","damage"),(50,"Uderzenie Meridianu","damage"),
        (70,"Krok Wiatru","evade"),(80,"Seria Tygrysa","damage"),
        (90,"Cios Smoka","execute"),(110,"Pięść Harmonii","damage"),
        (120,"Wewnętrzny Spokój","heal"),(130,"Fala Ki","damage"),
        (150,"Skupienie Mistrza Ki","boost"),(160,"Taniec Smoka","damage"),
        (170,"Pięść Legendy","damage"),(190,"Wyrok Oświeconego","execute"),
    ],
    "Strażnik": [
        (10,"Uderzenie Tarczy","damage"),(30,"Postawa Bastionu","guard"),
        (40,"Krąg Młota","damage"),(50,"Przełamanie","damage"),
        (70,"Kamienna Skóra","guard"),(80,"Cios Strażnika","damage"),
        (90,"Wyrok Twierdzy","execute"),(110,"Młot Duszy","damage"),
        (120,"Mur Fortecy","guard"),(130,"Roztrzaskanie","damage"),
        (150,"Przysięga Obrońcy","boost"),(160,"Burza Młota","damage"),
        (170,"Natarcie Bastionu","damage"),(190,"Ostatnia Obrona","guard"),
    ],
    "Mag": [
        (10,"Iskra Arkanów","damage"),(30,"Skupienie Many","boost"),
        (50,"Lanca Many","damage"),(70,"Odbicie Arkanów","guard"),
        (80,"Kula Mocy","damage"),(90,"Rozdarcie Eteru","execute"),
        (110,"Pocisk Astralny","damage"),(120,"Bariera Mistrza","guard"),
        (130,"Fala Arkanów","damage"),(150,"Przeciążenie Many","boost"),
        (170,"Promień Próżni","damage"),(190,"Wyrok Arkanów","execute"),
    ],
    "Nekromanta": [
        (10,"Kolec Kości","damage"),(30,"Mroczny Szept","boost"),
        (50,"Widmowy Pocisk","damage"),(70,"Zasłona Grobu","guard"),
        (80,"Uścisk Kości","damage"),(90,"Kradzież Życia","drain"),
        (110,"Włócznia Śmierci","damage"),(120,"Pancerz Kości","guard"),
        (130,"Mroczne Żniwo","damage"),(150,"Przymierze Grobu","boost"),
        (170,"Rozdarcie Duszy Grobu","damage"),(190,"Ostatni Oddech","execute"),
    ],
    "Kapłan": [
        (10,"Błysk Światła","damage"),(30,"Modlitwa Skupienia","boost"),
        (50,"Uzdrowienie Wiary","heal"),(70,"Tarcza Wiary","guard"),
        (80,"Promień Łaski","damage"),(90,"Wielka Modlitwa","heal"),
        (110,"Ostrze Światła","damage"),(120,"Sanktuarium","guard"),
        (130,"Łaska Arcykapłana","heal"),(150,"Hymn Mocy","boost"),
        (170,"Sąd Światła","damage"),(190,"Ostateczne Błogosławieństwo","heal"),
    ],
    "Czarownik": [
        (10,"Iskra Pustki","damage"),(30,"Szept Otchłani","boost"),
        (50,"Cierń Pustki","damage"),(70,"Zasłona Otchłani","guard"),
        (80,"Krwawy Płomień","damage"),(90,"Wysysanie Pustki","drain"),
        (110,"Lanca Otchłani","damage"),(120,"Pakt Cienia","boost"),
        (130,"Rozdarcie Pustki","damage"),(150,"Mroczne Przeładowanie","boost"),
        (170,"Gniew Piekieł","damage"),(190,"Ostateczny Pakt","execute"),
    ],
    "Druid": [
        (10,"Pnącze Cierni","damage"),(30,"Pieśń Gaju","heal"),
        (50,"Pazur Natury","damage"),(70,"Kora Życia","guard"),
        (80,"Piorun Natury","damage"),(90,"Oddech Lasu","heal"),
        (110,"Korzeń Duszy","damage"),(120,"Ochrona Pradawnych","guard"),
        (130,"Gniew Dziczy","damage"),(150,"Pieśń Burzy","boost"),
        (170,"Wściekłość Natury","damage"),(190,"Wyrok Pradawnego Dębu","execute"),
    ],
    "Psionik": [
        (10,"Kolec Umysłu","damage"),(30,"Skupienie Psioniczne","boost"),
        (50,"Wstrząs Jaźni","damage"),(70,"Tarcza Myśli","guard"),
        (80,"Impuls Dominacji","damage"),(90,"Wysysanie Woli","drain"),
        (110,"Ostrze Jaźni","damage"),(120,"Forteca Jaźni","guard"),
        (130,"Kruszenie Umysłu","damage"),(150,"Trans Psioniczny","boost"),
        (170,"Burza Jaźni","damage"),(190,"Zerwanie Świadomości","execute"),
    ],
}


def _make_soul_grid_skill(class_name, soul_level, name, kind):
    profile = _SOUL_GRID_CLASS_PROFILES[class_name]
    magic = bool(profile["magic"])
    skill = {
        "id": f"{profile['prefix']}_{int(soul_level)}",
        "name": name,
        "aliases": [name.lower()],
        "natural_tags": [word.lower() for word in name.split()],
        "unlock": int(soul_level),
        "kind": kind,
        "cooldown": 4,
        "mana": 0,
        "desc": (
            f"Umiejętność klasy {class_name} odblokowywana przez "
            f"Soul Level {int(soul_level)} Broni Duszy."
        ),
    }

    # Mana rośnie wraz z siłą czaru, ale fizyczne klasy pozostają bez many.
    if magic:
        skill["mana"] = max(4, 5 + int(soul_level) // 7)

    if kind == "damage":
        skill["scale"] = profile["scale"]
        skill["mult"] = round(1.18 + int(soul_level) * 0.0082, 2)
        skill["cooldown"] = min(12, 4 + int(soul_level) // 35)
    elif kind == "execute":
        skill["scale"] = profile["scale"]
        skill["mult"] = round(1.22 + int(soul_level) * 0.0078, 2)
        skill["execute_mult"] = round(min(2.0, 1.45 + int(soul_level) / 400.0), 2)
        skill["cooldown"] = min(17, 9 + int(soul_level) // 30)
    elif kind == "drain":
        skill["scale"] = profile["scale"]
        skill["mult"] = round(1.16 + int(soul_level) * 0.0074, 2)
        skill["drain_pct"] = round(min(0.48, 0.24 + int(soul_level) / 800.0), 2)
        skill["cooldown"] = min(15, 8 + int(soul_level) // 35)
    elif kind == "boost":
        skill["boost"] = round(min(1.70, 1.20 + int(soul_level) / 400.0), 2)
        skill["cooldown"] = min(16, 10 + int(soul_level) // 45)
        skill["duration"] = skill["cooldown"]
        skill["desc"] = (
            f"Czasowo wzmacnia wszystkie skille i spelle. Wymaga Biegłości klasy {int(soul_level)}."
        )
    elif kind == "guard":
        skill["guard"] = 10 + int(soul_level) // 3
        skill["cooldown"] = min(18, 10 + int(soul_level) // 35)
    elif kind == "evade":
        skill["cooldown"] = min(16, 9 + int(soul_level) // 40)
    elif kind == "heal":
        skill["heal_pct"] = round(min(0.52, 0.14 + int(soul_level) / 520.0), 3)
        skill["cooldown"] = min(18, 9 + int(soul_level) // 35)
    else:
        raise ValueError(f"Nieobsługiwany typ skilla progresji Soul: {kind}")

    return skill


for _class_name, _specs in SOUL_LEVEL_SKILL_EXPANSION.items():
    _existing_levels = {
        int(skill.get("unlock", 1))
        for skill in CLASS_SKILLS.get(_class_name, [])
    }
    for _soul_level, _name, _kind in _specs:
        if int(_soul_level) in _existing_levels:
            continue
        CLASS_SKILLS.setdefault(_class_name, []).append(
            _make_soul_grid_skill(_class_name, _soul_level, _name, _kind)
        )
        _existing_levels.add(int(_soul_level))


# v0.9.12: nowe umiejętności Biegłości 220-400. Stare progi 1-200
# pozostają bez zmian; nowe skille mają malejący przyrost mocy.
_POST200_SKILL_STAGES = (
    (220, "Przebudzenie"), (240, "Transcendencja"), (260, "Horyzont"),
    (280, "Otchłań"), (300, "Gwiezdny Rdzeń"), (320, "Pierwotność"),
    (340, "Nieskończoność"), (360, "Korona Świata"),
    (380, "Ponadczasowość"), (400, "Absolut"),
)
_POST200_CLASS_NOUN = {
    "Wojownik":"Wojownika", "Berserker":"Berserkera", "Łotrzyk":"Łotrzyka",
    "Łowca":"Łowcy", "Mnich":"Mnicha", "Strażnik":"Strażnika",
    "Mag":"Maga", "Nekromanta":"Nekromanty", "Kapłan":"Kapłana",
    "Czarownik":"Czarownika", "Druid":"Druida", "Psionik":"Psionika",
}
_POST200_ROLE_KINDS = {
    "Wojownik":("damage","guard","damage","boost","execute"),
    "Berserker":("damage","boost","drain","damage","execute"),
    "Łotrzyk":("damage","evade","damage","boost","execute"),
    "Łowca":("damage","evade","damage","boost","execute"),
    "Mnich":("damage","heal","damage","boost","execute"),
    "Strażnik":("damage","guard","guard","boost","damage"),
    "Mag":("damage","guard","damage","boost","execute"),
    "Nekromanta":("damage","guard","drain","boost","execute"),
    "Kapłan":("damage","heal","guard","boost","heal"),
    "Czarownik":("damage","guard","drain","boost","execute"),
    "Druid":("damage","heal","guard","boost","execute"),
    "Psionik":("damage","guard","drain","boost","execute"),
}

def _make_post200_mastery_skill(class_name, level, stage, kind):
    profile = _SOUL_GRID_CLASS_PROFILES[class_name]
    magic = bool(profile["magic"])
    noun = _POST200_CLASS_NOUN[class_name]
    name = f"{stage} {noun}"
    skill = {
        "id": f"{profile['prefix']}_mastery_{level}", "name": name,
        "aliases": [name.lower()], "natural_tags": [stage.lower(), "biegłość"],
        "unlock": level, "kind": kind, "cooldown": 10,
        "mana": (18 + level // 18) if magic else 0,
        "desc": f"Umiejętność Biegłości {level} klasy {class_name}.",
    }
    progress = (level - 200) / 200.0
    if kind in ("damage", "execute", "drain"):
        skill["scale"] = profile["scale"]
        skill["mult"] = round(2.65 + progress * 0.55, 2)
        skill["cooldown"] = 10 if kind == "damage" else 15
    if kind == "execute":
        skill["execute_mult"] = round(1.75 + progress * 0.15, 2)
    elif kind == "drain":
        skill["drain_pct"] = round(0.28 + progress * 0.08, 2)
    elif kind == "guard":
        skill["guard"] = 70 + (level - 200) // 8
        skill["cooldown"] = 15
    elif kind == "evade":
        skill["cooldown"] = 13
    elif kind == "boost":
        skill["boost"] = round(1.50 + progress * 0.15, 2)
        skill["duration"] = 14
        skill["cooldown"] = 16
    elif kind == "heal":
        skill["heal_pct"] = round(min(0.60, 0.42 + progress * 0.12), 3)
        skill["cooldown"] = 15
    return skill

for _class_name in _SOUL_GRID_CLASS_PROFILES:
    _existing = {int(x.get("unlock", 1)) for x in CLASS_SKILLS.get(_class_name, [])}
    _pattern = _POST200_ROLE_KINDS[_class_name]
    for _index, (_level, _stage) in enumerate(_POST200_SKILL_STAGES):
        if _level in _existing:
            continue
        _kind = _pattern[_index % len(_pattern)]
        CLASS_SKILLS.setdefault(_class_name, []).append(
            _make_post200_mastery_skill(_class_name, _level, _stage, _kind)
        )

# v0.9.22: każdy próg Biegłości ma kilka realnych umiejętności do nauki.
# Docelowo dokładnie 3 skille/spelle na próg 1, 10, 20...200 oraz 220...400.
# Dodatkowe umiejętności są alternatywami tego samego progu i korzystają ze
# wspólnego cooldownu mastery_choice_group, żeby zwiększyć wybór bez potrajania DPS.
_V0922_MASTERY_LEVELS = tuple(sorted(set(SOUL_SKILL_UNLOCK_LEVELS) | {
    level for level, _stage in _POST200_SKILL_STAGES
}))
_V0922_CLASS_ALT_PROFILES = {
    "Wojownik":   (("Kontratak Wojownika", "damage"), ("Mur Wojownika", "guard"), ("Rozkaz Wojownika", "boost")),
    "Berserker":  (("Rozdarcie Berserkera", "drain"), ("Furia Berserkera", "damage"), ("Ryk Berserkera", "boost")),
    "Łotrzyk":    (("Riposta Łotrzyka", "damage"), ("Krok Łotrzyka", "evade"), ("Impuls Cienia", "boost")),
    "Łowca":      (("Strzał Tropiciela", "damage"), ("Odskok Łowcy", "evade"), ("Skupienie Tropiciela", "boost")),
    "Mnich":      (("Fala Ki", "damage"), ("Oddech Harmonii", "heal"), ("Krok Harmonii", "evade")),
    "Strażnik":   (("Cios Bastionu", "damage"), ("Tarcza Strażnika", "guard"), ("Przysięga Bastionu", "boost")),
    "Mag":        (("Lanca Arkanów", "damage"), ("Krąg Arkanów", "aoe_damage"), ("Bariera Eteru", "guard")),
    "Nekromanta": (("Żniwo Nekromanty", "drain"), ("Fala Grobów", "aoe_damage"), ("Pancerz Grobu", "guard")),
    "Kapłan":     (("Promień Kapłana", "damage"), ("Łaska Kapłana", "heal"), ("Modlitwa Drużyny", "group_heal")),
    "Czarownik":  (("Pocisk Otchłani", "damage"), ("Krąg Pustki", "aoe_damage"), ("Pakt Otchłani", "drain")),
    "Druid":      (("Cierń Druida", "damage"), ("Odnowa Natury", "heal"), ("Krąg Dziczy", "aoe_damage")),
    "Psionik":    (("Impuls Psionika", "damage"), ("Fala Umysłu", "aoe_damage"), ("Forteca Myśli", "guard")),
}

# v0.24.4: stary generator tworzył dziesiątki nazw typu
# "Kontratak Wojownika 10", "Kontratak Wojownika 20" itd. ID i mechanika
# pozostają bez zmian, ale nazwy alternatywnych skilli Wojownika są teraz
# faktycznie różne i czytelne dla NVDA.
_V0244_WARRIOR_LEVEL_TITLES = {
    level: title for level, title in zip(
        _V0922_MASTERY_LEVELS,
        (
            "Pierwszej Warty", "Żelaznego Świtu", "Stalowej Straży",
            "Miecza Północy", "Tarczy Miasta", "Krwawego Frontu",
            "Srebrnej Gwardii", "Nieugiętej Linii", "Płonącego Bastionu",
            "Weterana", "Kamiennej Bramy", "Wojennego Sztandaru",
            "Hartowanego Ostrza", "Czerwonej Warty", "Złamanego Muru",
            "Niezłomnego Legionu", "Ostatniej Straży", "Ducha Bohatera",
            "Korony Wojny", "Mistrza Oręża", "Legendy Pola Bitwy",
            "Przekroczonej Granicy", "Przebudzonej Stali", "Wyższej Warty",
            "Transcendentnej Gwardii", "Dalekiego Horyzontu",
            "Horyzontu Bitew", "Głębokiej Otchłani", "Otchłannego Ostrza",
            "Gwiezdnej Kuźni", "Gwiezdnego Bastionu", "Pierwotnego Szańca",
            "Pierwotnego Legionu", "Wiecznej Warty", "Nieskończonej Straży",
            "Korony Zwycięstwa", "Korony Świata", "Czasu Bohaterów",
            "Ponadczasowej Wojny", "Ostatniej Granicy", "Absolutnej Stali",
        ),
    )
}
_V0244_WARRIOR_ACTION_PREFIXES = {
    "damage": (
        "Riposta", "Odwet", "Przechwyt", "Cięcie Odpowiedzi",
        "Pchnięcie Zwrotne", "Uderzenie po Bloku", "Natarcie Zwrotne",
        "Zamach Odpowiedzi", "Przecięcie Gardy",
    ),
    "guard": (
        "Żelazna Zasłona", "Bastion", "Tarcza", "Garda",
        "Forteca", "Warta", "Szańcowanie", "Mur",
    ),
    "boost": (
        "Rozkaz", "Zew", "Komenda", "Sygnał Natarcia",
        "Marsz", "Przysięga", "Mobilizacja", "Sztandar",
    ),
}

def _v0244_warrior_alt_name(level, kind):
    title = _V0244_WARRIOR_LEVEL_TITLES.get(int(level), f"Biegłości {int(level)}")
    prefixes = _V0244_WARRIOR_ACTION_PREFIXES.get(kind)
    if not prefixes:
        return None
    idx = _V0922_MASTERY_LEVELS.index(int(level))
    return f"{prefixes[idx % len(prefixes)]} {title}"


def _v0922_alt_skill(class_name, level, variant_index, base_name, kind):
    profile = _SOUL_GRID_CLASS_PROFILES[class_name]
    magic = bool(profile["magic"])
    level = int(level)
    # Nazwa ma być jednoznaczna dla NVDA i komendy learn, ale nie może
    # udawać nowego skilla przez samo dopisanie numeru poziomu.
    name = None
    if class_name == "Wojownik":
        name = _v0244_warrior_alt_name(level, kind)
    if not name:
        name = f"{base_name} {level}"
    skill = {
        "id": f"v0922_{profile['prefix']}_{level}_{variant_index}",
        "name": name,
        "aliases": [name.lower()],
        "natural_tags": [w.lower() for w in base_name.split()],
        "unlock": level,
        "kind": kind,
        "cooldown": 10,
        "mana": (max(4, 5 + level // 12) if magic else 0),
        "desc": (
            f"Alternatywna umiejętność progu Biegłości {level} klasy {class_name}. "
            "Umiejętności z tego samego progu współdzielą cooldown wyboru."
        ),
        "mastery_choice_group": f"{class_name}:{level}",
    }
    progress = min(1.0, max(0.0, (level - 1) / 399.0))
    if kind in ("damage", "aoe_damage", "execute", "drain"):
        skill["scale"] = profile["scale"]
        # Alternatywy są trochę słabsze od najmocniejszego głównego skilla progu;
        # ich wartością jest inny typ działania, nie power creep.
        skill["mult"] = round(1.16 + progress * 1.75, 2)
        skill["cooldown"] = 8 if kind == "damage" else 12
    if kind == "aoe_damage":
        skill["mult"] = round(1.02 + progress * 1.40, 2)
        skill["cooldown"] = 14
    elif kind == "execute":
        skill["execute_mult"] = round(1.45 + progress * 0.35, 2)
        skill["cooldown"] = 15
    elif kind == "drain":
        skill["drain_pct"] = round(0.24 + progress * 0.14, 2)
        skill["cooldown"] = 13
    elif kind == "guard":
        skill["guard"] = 10 + int(round(progress * 110))
        skill["cooldown"] = 13
    elif kind == "evade":
        skill["cooldown"] = 13
    elif kind == "boost":
        skill["boost"] = round(1.18 + progress * 0.42, 2)
        skill["duration"] = 12
        skill["cooldown"] = 15
    elif kind == "heal":
        skill["heal_pct"] = round(0.14 + progress * 0.36, 3)
        skill["cooldown"] = 13
    elif kind == "group_heal":
        skill["heal_pct"] = round(0.10 + progress * 0.28, 3)
        skill["cooldown"] = 16
    return skill


for _class_name in _SOUL_GRID_CLASS_PROFILES:
    _skills = CLASS_SKILLS.setdefault(_class_name, [])
    for _level in _V0922_MASTERY_LEVELS:
        _at_level = [s for s in _skills if int(s.get("unlock", 1)) == int(_level)]
        # Każdy już istniejący skill także należy do wspólnej grupy tego progu.
        for _skill in _at_level:
            _skill["mastery_choice_group"] = f"{_class_name}:{int(_level)}"
        _profile_alts = _V0922_CLASS_ALT_PROFILES[_class_name]
        _alt_index = 0
        while len(_at_level) < 3:
            _base_name, _kind = _profile_alts[_alt_index % len(_profile_alts)]
            _candidate = _v0922_alt_skill(
                _class_name, int(_level), len(_at_level) + 1, _base_name, _kind
            )
            if all(s.get("id") != _candidate["id"] for s in _skills):
                _skills.append(_candidate)
                _at_level.append(_candidate)
            _alt_index += 1
        for _skill in _at_level:
            _skill["mastery_choice_group"] = f"{_class_name}:{int(_level)}"

# ============================================================
# v0.30.14 - FULL CLASS SKILL/SPELL NAME AUDIT
# ============================================================
# v0.9.22 intentionally created three real choices per mastery threshold, but
# eleven classes still displayed large numbered families such as
# "Furia Berserkera 10" or "Fala Umysłu 80".  IDs/mechanics stay untouched;
# only the user-facing names are replaced.  Old names remain aliases so saved
# macros and learned-skill workflows keep working.
_V03014_SKILL_TITLES = (
    "Pierwszy Świt", "Żelazny Próg", "Stalowy Szlak", "Północny Zew",
    "Kamienna Brama", "Srebrny Front", "Czerwony Horyzont", "Nieugięta Linia",
    "Płonący Bastion", "Szlak Weterana", "Brama Duszy", "Wojenny Sztandar",
    "Hartowany Rdzeń", "Krwawy Księżyc", "Złamany Mur", "Niezłomny Legion",
    "Ostatnia Warta", "Duch Bohatera", "Korona Burzy", "Mistrzowski Krąg",
    "Legenda Pola", "Przekroczona Granica", "Przebudzony Rdzeń", "Wyższa Warta",
    "Transcendentny Krąg", "Daleki Horyzont", "Horyzont Mocy", "Głęboka Otchłań",
    "Otchłanny Znak", "Gwiezdna Kuźnia", "Gwiezdny Bastion", "Pierwotne Serce",
    "Pierwotny Tron", "Wieczny Zew", "Nieskończona Droga", "Korona Zwycięstwa",
    "Korona Świata", "Czas Bohaterów", "Ponadczasowy Znak", "Ostatnia Granica",
    "Absolutny Szczyt",
)

_V03014_SKILL_FAMILIES = {
    "Berserker": {
        "damage": ("Szkarłatna Furia", "Rzeźniczy Zamach", "Gniew Rozłamu"),
        "drain": ("Krwiożercze Rozdarcie", "Żniwo Krwi", "Rozdarcie Żył"),
        "boost": ("Ryk Rzezi", "Zew Furii", "Szał Bez Kajdan"),
        "execute": ("Wyrok Topora", "Ostatnie Rozdarcie", "Kres Krwi"),
    },
    "Łotrzyk": {
        "damage": ("Riposta Czarnego Ostrza", "Cięcie Nocnego Widma", "Sztych Bez Śladu"),
        "evade": ("Krok Widma", "Unik Cichego Cienia", "Przejście Bez Śladu"),
        "boost": ("Impuls Nocnego Cienia", "Skupienie Zabójcy", "Zew Czarnej Maski"),
        "execute": ("Cichy Wyrok", "Ostatni Sztych", "Wyrok Bez Świadków"),
    },
    "Łowca": {
        "damage": ("Strzał Sokolego Tropu", "Strzała Dalekiego Łuku", "Pocisk Leśnego Widma"),
        "evade": ("Odskok Tropiciela", "Krok Leśnego Cienia", "Unik Sokoła"),
        "boost": ("Skupienie Szarego Tropiciela", "Sokoli Zew", "Instynkt Dalekiego Łuku"),
        "execute": ("Strzał Ostatniego Tropu", "Wyrok Sokoła", "Ostatnia Strzała"),
    },
    "Mnich": {
        "damage": ("Fala Smoczego Ki", "Pięść Cichego Ducha", "Uderzenie Lotosu"),
        "heal": ("Oddech Białego Lotosu", "Harmonia Życia", "Medytacja Odnowy"),
        "evade": ("Krok Cichej Harmonii", "Taniec Wiatru", "Przejście Lotosu"),
        "boost": ("Skupienie Ki", "Pieśń Harmonii", "Przebudzenie Ducha"),
        "execute": ("Dotyk Końca", "Pięść Ostatniego Oddechu", "Wyrok Meridianu"),
    },
    "Strażnik": {
        "damage": ("Cios Kamiennego Bastionu", "Uderzenie Żelaznej Warty", "Taranująca Tarcza"),
        "guard": ("Tarcza Żelaznej Przysięgi", "Mur Niezłomnej Straży", "Bastion Kamiennego Serca"),
        "boost": ("Przysięga Niezłomnej Straży", "Rozkaz Bastionu", "Zew Ostatniej Warty"),
        "execute": ("Wyrok Bastionu", "Ostatni Cios Warty", "Kres Oblężenia"),
    },
    "Mag": {
        "damage": ("Lanca Gwiezdnych Arkanów", "Pocisk Kryształowego Eteru", "Ostrze Runicznego Ognia"),
        "aoe_damage": ("Krąg Eterycznej Burzy", "Nova Gwiezdnych Run", "Wir Arkanicznego Nieba"),
        "guard": ("Bariera Kryształowego Eteru", "Pieczęć Astralnej Tarczy", "Mur Runicznego Światła"),
        "boost": ("Skupienie Arkanów", "Przebudzenie Eteru", "Zew Gwiezdnej Many"),
        "execute": ("Wyrok Arkanów", "Ostatnia Lanca", "Kres Gwiezdnej Iskry"),
    },
    "Nekromanta": {
        "damage": ("Kościany Pocisk", "Włócznia Czarnego Grobu", "Cios Umarłego Tronu"),
        "aoe_damage": ("Fala Umarłych", "Krąg Cmentarnej Burzy", "Marsz Kościanego Legionu"),
        "drain": ("Żniwo Czarnego Grobu", "Wysysanie Zgasłej Duszy", "Pocałunek Kostuchy"),
        "guard": ("Pancerz Kościanego Tronu", "Zasłona Czarnego Grobu", "Mur Umarłych"),
        "boost": ("Szept Nekropolii", "Przysięga Kostuchy", "Zew Umarłego Legionu"),
        "execute": ("Wyrok Kostuchy", "Ostatnie Żniwo", "Kres Duszy"),
    },
    "Kapłan": {
        "damage": ("Promień Świętego Sądu", "Młot Złotego Światła", "Iskra Boskiej Pieczęci"),
        "heal": ("Łaska Złotego Światła", "Dotyk Miłosierdzia", "Uzdrowienie Świętej Pieczęci"),
        "group_heal": ("Modlitwa Wspólnoty", "Pieśń Zbiorowej Łaski", "Krąg Wspólnego Światła"),
        "guard": ("Tarcza Wiary", "Boska Zasłona", "Pieczęć Sanktuarium"),
        "boost": ("Modlitwa Skupienia", "Zew Świętej Łaski", "Błogosławieństwo Światła"),
        "execute": ("Wyrok Światła", "Ostatni Sąd", "Pieczęć Końca"),
    },
    "Czarownik": {
        "damage": ("Pocisk Głębokiej Otchłani", "Ostrze Bezgwiezdnej Pustki", "Płomień Czarnego Paktu"),
        "aoe_damage": ("Krąg Bezgwiezdnej Pustki", "Nova Otchłannego Mroku", "Wir Czarnego Horyzontu"),
        "drain": ("Pakt Krwawej Otchłani", "Wysysanie Pustki", "Danina Czarnego Paktu"),
        "guard": ("Zasłona Otchłani", "Bariera Pustki", "Pieczęć Czarnego Kręgu"),
        "boost": ("Szept Otchłani", "Przebudzenie Paktu", "Zew Bezgwiezdnej Pustki"),
        "execute": ("Wyrok Otchłani", "Kres Paktu", "Ostatni Pocisk Pustki"),
    },
    "Druid": {
        "damage": ("Cierń Pradawnego Gaju", "Pazur Zielonego Serca", "Korzeń Dzikiej Burzy"),
        "aoe_damage": ("Krąg Pierwotnej Dziczy", "Burza Starego Lasu", "Taniec Rozszalałych Korzeni"),
        "heal": ("Odnowa Zielonego Serca", "Szept Leczącego Gaju", "Pieśń Żywej Kory"),
        "guard": ("Kora Pradawnych", "Mur Żywego Dębu", "Osłona Zielonego Serca"),
        "boost": ("Zew Dzikiej Natury", "Przebudzenie Gaju", "Pieśń Pierwotnego Lasu"),
        "execute": ("Wyrok Pradawnego Dębu", "Ostatni Cierń", "Kres Dzikiego Korzenia"),
    },
    "Psionik": {
        "damage": ("Impuls Kryształowej Jaźni", "Kolec Astralnej Myśli", "Ostrze Cichego Umysłu"),
        "aoe_damage": ("Fala Astralnego Umysłu", "Burza Wspólnej Jaźni", "Krąg Psionicznego Echa"),
        "drain": ("Wysysanie Woli", "Pęknięcie Jaźni", "Wysysanie Astralnej Myśli"),
        "guard": ("Forteca Niezłomnej Myśli", "Bariera Kryształowej Jaźni", "Mur Psionicznej Woli"),
        "boost": ("Skupienie Psioniczne", "Przebudzenie Jaźni", "Zew Astralnej Woli"),
        "execute": ("Wyrok Umysłu", "Ostatni Impuls", "Kres Jaźni"),
    },
}



# v0.31.2: kompletne siatki skilli nowych klas technologicznych.
def _v0310_tech_skill(class_name, prefix, level, index, name, kind):
    sid = f"v0310_{prefix}_{level}_{index}"
    base = {
        "id": sid, "name": name, "aliases": [name.casefold()], "unlock": level,
        "kind": kind, "cooldown": 4 + ((level // 10 + index) % 7), "mana": 0,
        "desc": f"Umiejętność klasy {class_name} odblokowywana przez Biegłość {level}.",
    }
    scale = "dexterity" if class_name == "Inżynier" else "strength"
    if kind in ("damage","aoe_damage","execute","drain"):
        base["scale"] = scale
        base["mult"] = round(1.20 + min(1.10, level / 400.0) + index * 0.08, 2)
    if kind == "aoe_damage": base["aoe"] = True
    if kind == "execute": base["execute_mult"] = 1.65
    if kind == "drain": base["drain_pct"] = 0.18
    if kind == "boost": base.update({"boost": 1.25 + min(.30, level/1400.0), "duration": 30})
    if kind == "guard": base["guard"] = 12 + level // 20
    if kind == "evade": base["evade"] = True
    if kind == "heal": base["heal_pct"] = min(.40, .16 + level/1800.0)
    if kind == "group_heal": base["heal_pct"] = min(.30, .12 + level/2200.0)
    return base

def _v0310_build_tech_class_skills():
    levels = (1, *range(10, 401, 10))
    mec_special = {
        1: [("Fire Beam", "damage"), ("TekShield", "guard"), ("Vent Heat", "heal")],
        10: [("Ice Beam", "damage"), ("Bolt Beam", "damage"), ("Target Lock", "boost")],
        20: [("Gravity Bomb", "aoe_damage"), ("TekBarrier", "guard"), ("Overdrive", "boost")],
        30: [("Bio Blast", "aoe_damage"), ("TekMissile", "execute"), ("Heal Force", "heal")],
        40: [("Diffuser", "aoe_damage"), ("Runic Weapon", "boost"), ("Core Meltdown", "execute")],
    }
    eng_special = {
        1: [("Auto Crossbow", "aoe_damage"), ("Mako Gun", "damage"), ("Scanner", "boost")],
        10: [("Bio Blaster", "aoe_damage"), ("Flash", "aoe_damage"), ("Debilitator", "boost")],
        20: [("Drill", "damage"), ("Napalm", "aoe_damage"), ("Launcher", "execute")],
        30: [("Noise Blaster", "aoe_damage"), ("Chainsaw", "execute"), ("Mega Bomb", "aoe_damage")],
        40: [("Air Anchor", "damage"), ("Field Repair", "heal"), ("Tool Upgrade", "boost")],
    }
    generic_mec = (("Salwa Rdzenia", "damage"), ("Pancerz Reaktywny", "guard"), ("Przeciążenie Systemów", "boost"))
    generic_eng = (("Wieżyczka Szturmowa", "damage"), ("Ładunek Taktyczny", "aoe_damage"), ("Kalibracja", "boost"))
    # v0.33.1: nie używamy już sztucznych nazw Mk-13A, Mk-14A itd.
    # Każdy próg technologiczny dostaje własny, czytelny tytuł bez cyfr.
    tech_stage_titles = (
        "Pierwszy Zapłon", "Miedziany Impuls", "Żelazny Obwód", "Stalowy Rezonans",
        "Kobaltowy Sygnał", "Srebrna Matryca", "Złoty Przekaźnik", "Runiczny Układ",
        "Kryształowy Rdzeń", "Astralna Iskra", "Próżniowy Napęd", "Eteryczna Sieć",
        "Reaktywny Pancerz", "Puls Plazmowy", "Jonowy Horyzont", "Kwantowa Brama",
        "Neuralny Splot", "Magitekowy Węzeł", "Tytanowy Obwód", "Gwiezdny Reaktor",
        "Fazowy Przekaźnik", "Chronalny Impuls", "Burzowy Kondensator", "Słoneczny Rdzeń",
        "Lunarny Moduł", "Grawitonowa Matryca", "Widmowy Układ", "Harmoniczny Napęd",
        "Pustkowy Rezonator", "Kosmiczny Obwód", "Niebiański Reaktor", "Pierwotny Węzeł",
        "Wieczny Przekaźnik", "Nieskończona Matryca", "Transcendentny Rdzeń", "Korona Maszyny",
        "Horyzont Absolutu", "Ponadczasowy Układ", "Ostateczny Rezonans", "Szczyt Techniki",
        "Absolutny Rdzeń",
    )
    stage_title_by_level = {level: tech_stage_titles[idx] for idx, level in enumerate(levels)}
    for cname,prefix,special,generic in (("Mec","mec",mec_special,generic_mec),("Inżynier","engineer",eng_special,generic_eng)):
        rows=[]
        for level in levels:
            specs=special.get(level)
            if specs is None:
                title = stage_title_by_level[level]
                specs=[(f"{n}: {title}", k) for n,k in generic]
            for idx,(name,kind) in enumerate(specs,1):
                rows.append(_v0310_tech_skill(cname,prefix,level,idx,name,kind))
        CLASS_SKILLS[cname]=rows

_v0310_build_tech_class_skills()

# v0.31.5: UOSSMUD-inspired Mec abilities. Cosmic Rave keeps the supplied
# UOSS behavior adapted to Soulbound: base power 2000, requirement 110, all enemies normally,
# five random hits while V-MAX is active.
def _v0315_install_cosmic_rave():
    rows = CLASS_SKILLS.get("Mec", [])
    by_level = {}
    for row in rows:
        by_level.setdefault(int(row.get("unlock", 0) or 0), []).append(row)
    if by_level.get(100):
        row = by_level[100][0]
        row.clear(); row.update({
            "id":"v0315_mec_vmax", "name":"V-MAX", "aliases":["v-max","vmax","v max"],
            "unlock":100, "kind":"boost", "cooldown":45, "mana":0,
            "boost":1.0, "duration":30,
            "desc":"Aktywuje V-MAX na 30 sekund. Cosmic Rave wykonuje wtedy 5 losowych trafień zamiast jednego trafienia we wszystkich przeciwników."
        })
    if by_level.get(110):
        row = by_level[110][0]
        row.clear(); row.update({
            "id":"v0315_mec_cosmic_rave", "name":"Cosmic Rave", "aliases":["cosmic rave","kosmiczny rave"],
            "unlock":110, "kind":"aoe_damage", "cooldown":8, "mana":0,
            "base_power":2000, "scale":"strength", "mult":1.0,
            "desc":"Moc bazowa 2000. Normalnie trafia wszystkich przeciwników salwą meteorycznych ładunków. Pod V-MAX wykonuje 5 losowych trafień. Soulbound nie używa AP."
        })
_v0315_install_cosmic_rave()


# v0.31.9: Full authored Mec kit based on the user-provided UOSSMUD ability list.
# Soulbound does NOT use AP. Source Base AP is stored only as internal base_power.
def _v0319_install_full_mec_kit():
    rows = CLASS_SKILLS.get("Mec", [])
    specs = [
        # Melee
        ("Hammer Crush",1,"damage",200,"melee","hammer_crush","Smashes one enemy with a powerful melee attack."),
        ("Shock Soldier",14,"aoe_damage",600,"melee","shock_soldier","Miniature weapon-wielding clones attack all enemies."),
        ("Plural Slash",32,"damage",900,"melee","plural_slash","Multiple slashes on one enemy. Scales especially with Dexterity."),
        ("Pop Knight",46,"aoe_damage",1500,"melee","pop_knight","Flying clones attack all enemies."),
        ("Tiger Rampage",80,"damage",1800,"melee","tiger_rampage","Powerful single-target attack that lowers Defense."),
        ("Cosmic Rave",110,"aoe_damage",2000,"melee","cosmic_rave","Hits all enemies; during V-MAX performs 5 random hits instead."),
        # Ranged
        ("Crosshair",1,"damage",200,"ranged","crosshair","Precise shot; benefits strongly from critical chance."),
        ("Range Fire",8,"aoe_damage",500,"ranged","range_fire","Bullets hit all enemies; non-diminishing area attack."),
        ("Dispose",32,"aoe_damage",1200,"ranged","dispose","Lasers hit all enemies at a cost of some HP."),
        ("Satellite Linker",44,"damage",1000,"ranged","satellite_linker","Attack drones repeatedly damage one enemy over time; scales with Will."),
        ("Magnify",90,"damage",1500,"ranged","magnify","Very strong overload attack; may Lock the user."),
        ("Shoot-All",110,"aoe_damage",2000,"ranged","shoot_all","Fires all ammunition at all enemies; V-MAX increases damage and crit."),
        # Feedback
        ("Destroy",1,"damage",200,"feedback","destroy","Single-target smash at a cost of HP."),
        ("Robo Tackle",20,"damage",500,"feedback","robo_tackle","Body/shield charge at a cost of HP."),
        ("Compress",30,"damage",600,"feedback","compress","Gravity percentile damage at a cost of HP."),
        ("Crush",46,"damage",1000,"feedback","crush","Damage increases with HP already lost; costs HP."),
        ("Uzi Punch",95,"aoe_damage",1400,"feedback","uzi_punch","Random fist/shield attacks across enemies at a cost of HP."),
        ("Kamikaze Crush",110,"damage",2000,"feedback","kamikaze_crush","Lethal dive bomb; more HP sacrificed means more damage. V-MAX raises the sacrifice limit."),
        # Magic
        ("Laser Spin",1,"aoe_damage",200,"magic","laser_spin","Dark lasers hit all enemies."),
        ("Area Bomb",8,"aoe_damage",300,"magic","area_bomb","Fire bomb burns engaged targets."),
        ("Mec Sonata",20,"damage",1000,"magic","mec_sonata","Holy gospel attacks one enemy and may reduce its level-equivalent power."),
        ("Maelstrom",44,"aoe_damage",1500,"magic","maelstrom","Water vortex floods all enemies."),
        ("Shock",95,"aoe_damage",1800,"magic","shock","Dark + Lightning attack on all enemies."),
        ("Starlight Shower",110,"damage",2000,"magic","starlight_shower","Focused laser barrage; in V-MAX becomes non-diminishing and hits all enemies."),
        # Support
        ("Cure Beam",10,"heal",100,"support","cure_beam","Single-target heal; support effect improves healing and clears Poison/Blind."),
        ("Hypno Flash",16,"damage",300,"support","hypno_flash","Attempts to put one enemy to Sleep; support effect improves chance."),
        ("Jammer",32,"damage",750,"support","jammer","Disables one enemy, stronger on Machine; support effect attempts all enemies."),
        ("Heal Beam",54,"heal",1000,"support","heal_beam","Large single-target heal; support effect heals entire party."),
        ("Logic Bomb",95,"damage",1200,"support","logic_bomb","Attempts Silence/Don't Act/Slow; support effect can add Curse/Don't Move/Blind."),
        ("V-MAX",130,"boost",2000,"support","vmax","Core overdrive: Protect, Shell, Haste, Regen, Preach, Praise, Permanence; changes several Mec skills. Overheats when it ends unless Support Effect suppresses it."),
        # Counter
        ("Intercept System",75,"passive",1000,"counter","intercept_system","Counters enemy melee using the user's highest combat stat."),
        # Inherent
        ("Self-Repair",1,"passive",1000,"inherent","self_repair","Auto-Regen and delayed recovery of Feedback self-damage."),
        ("Combat Mastery",30,"passive",1000,"inherent","combat_mastery","Increases purely Strength-based weapon/Mec melee damage."),
        ("Maxwell Program",30,"passive",2000,"inherent","maxwell_program","Auto-Mana Regen and increased magic damage."),
        ("Shooting Mastery",30,"passive",1000,"inherent","shooting_mastery","Increases purely Dexterity-based ranged damage."),
        # Passive protocols
        ("Strength Protocol",1,"passive",2000,"passive","strength_protocol","Increases Mec melee potency."),
        ("Ranged Protocol",1,"passive",2000,"passive","ranged_protocol","Increases Mec ranged potency."),
        ("Feedback Protocol",1,"passive",2000,"passive","feedback_protocol","Increases Mec feedback potency."),
        ("Magic Protocol",1,"passive",2000,"passive","magic_protocol","Increases Mec magic potency."),
    ]
    if len(rows) < len(specs):
        return
    for idx,(name,unlock,kind,power,branch,special,desc) in enumerate(specs):
        row=rows[idx]
        row.clear()
        row.update({
            "id":f"v0319_mec_{special}", "name":name, "aliases":[name.casefold()],
            "unlock":unlock, "kind":kind, "cooldown":5, "mana":0,
            "base_power":power, "mec_authored":True, "mec_branch":branch,
            "mec_special":special, "desc":desc,
        })
        if kind in ("damage","aoe_damage"):
            row["scale"] = "intelligence" if branch=="magic" else ("dexterity" if branch=="ranged" else "strength")
            row["mult"] = 1.0
            if kind=="aoe_damage": row["aoe"]=True
        if kind=="heal": row["heal_pct"] = .22 if special=="cure_beam" else .48
        if special in ("destroy","robo_tackle"): row["self_damage_pct"]=.04
        if special=="compress": row["self_damage_pct"]=.06
        if special=="crush": row["self_damage_pct"]=.08
        if special=="uzi_punch": row["self_damage_pct"]=.10
        if special=="kamikaze_crush": row["self_damage_pct"]=.18
        if special=="dispose": row["self_damage_pct"]=.08
        if special=="vmax": row.update({"boost":1.0,"duration":30,"cooldown":60})
    CLASS_SKILLS["Mec"] = rows

_v0319_install_full_mec_kit()


# v0.31.7: authored Engineer tool kit based on the user-provided UOSSMUD list.
# Soulbound has no AP. The original Base AP values are represented only as
# internal base_power values for relative skill strength.
def _v0317_install_engineer_toolkit():
    rows = CLASS_SKILLS.get("Inżynier", [])
    if len(rows) < 19:
        return
    specs = [
      # name, unlock, kind, base_power, special, category, description
      ("Auto Crossbow",1,"aoe_damage",100,"auto_crossbow","area","Automatyczna kusza ostrzeliwuje wszystkich przeciwników. Ulepszenie zwiększa obrażenia."),
      ("Mako Gun",1,"damage",100,"mako_gun","single","Losowy atak żywiołowy. Ulepszenie zwiększa obrażenia i dobiera skuteczniejszy element."),
      ("Bio Blaster",1,"aoe_damage",200,"bio_blaster","area","Fala toksycznego gazu na wszystkich przeciwników. Ulepszenie zwiększa obrażenia i siłę efektu biologicznego."),
      ("Scanner",1,"damage",500,"scanner","utility","Skanuje cel i podaje HP, rangę, typ, odporności oraz słabości. Nie podlega Upgrade."),
      ("Flash",8,"aoe_damage",800,"flash","area","Święte światło uderza wszystkich przeciwników. Ulepszenie zwiększa obrażenia i wzmacnia efekt oślepienia/Guard Break."),
      ("Debilitator",8,"damage",1000,"debilitator","utility","Nadaje celowi losową słabość żywiołową. Ulepszenie nadaje trzy słabości jednocześnie."),
      ("Hypercharge",8,"passive",500,"hypercharge","passive","Pasywnie wzmacnia pojedyncze ofensywne narzędzia Inżyniera, w tym Mega Bomb."),
      ("Lindblum Assembly",8,"passive",500,"lindblum","passive","Pasywnie wzmacnia obszarowe narzędzia Inżyniera."),
      ("Improved Kinematics",8,"passive",500,"kinematics","passive","Pasywnie wydłuża efekty statusowe narzędzi Inżyniera."),
      ("Drill",12,"damage",1500,"drill","single","Wiertło przebija ochronę celu. Ulepszenie zwiększa obrażenia i wzmacnia przebicie ochrony."),
      ("Napalm",12,"aoe_damage",1500,"napalm","area","Ognista bomba uderza wszystkich przeciwników. Ulepszenie zwiększa obrażenia i pokrywa cele łatwopalnym olejem."),
      ("Launcher",14,"aoe_damage",2500,"launcher","area","Do czterech pocisków trafia losowe cele, każdy redukuje bieżące HP celu o połowę. Ulepszenie: do sześciu pocisków."),
      ("Upgrade",16,"boost",15000,"upgrade","utility","Ulepsza wybrane narzędzie Inżyniera. Bazowo 1 slot; Silver Gear i Gold Battery zwiększają limit."),
      ("Noise Blaster",18,"aoe_damage",2500,"noise_blaster","area","Fala dźwięku uderza i ucisza przeciwników. Ulepszenie zwiększa obrażenia i efekt kontroli."),
      ("Chainsaw",20,"damage",5000,"chainsaw","single","Piła łańcuchowa zadaje ciężkie obrażenia albo efekt Demi. Ulepszenie wzmacnia Demi do Quarter."),
      ("Mega Bomb",21,"aoe_damage",5000,"mega_bomb","single","Potężna eksplozja: główny cel otrzymuje pełne obrażenia, pozostali mniejsze. Ulepszenie zwiększa obrażenia wszystkim celom."),
      ("Silver Gear",21,"passive",15000,"silver_gear","passive","Pasywnie dodaje drugi slot systemu Upgrade."),
      ("Air Anchor",23,"damage",7500,"air_anchor","single","Kotwica wbija się w cel i zadaje obrażenia. Ulepszenie zwiększa moc efektu."),
      ("Gold Battery",23,"passive",15000,"gold_battery","passive","Pasywnie dodaje trzeci slot systemu Upgrade."),
    ]
    # Replace only 19 generated entries so total class skill count remains 123.
    for index, spec in enumerate(specs):
        name,unlock,kind,power,special,category,desc = spec
        row=rows[index]
        row.clear()
        row.update({
          "id":f"v0317_engineer_{special}","name":name,
          "aliases":[name.casefold()],"unlock":unlock,"kind":kind,"cooldown":4,"mana":0,
          "base_power":power,"engineer_tool":True,"engineer_special":special,
          "engineer_category":category,"desc":desc,
        })
        if kind in ("damage","aoe_damage"):
            row.update({"scale":"dexterity","mult":1.0})
            if kind=="aoe_damage": row["aoe"]=True
        if special=="upgrade": row.update({"boost":1.0,"duration":1})
    CLASS_SKILLS["Inżynier"] = rows

_v0317_install_engineer_toolkit()

def _v03014_unique_generated_skill_names():
    renamed = 0
    old_aliases_added = 0
    level_to_title = {
        int(level): _V03014_SKILL_TITLES[idx]
        for idx, level in enumerate(_V0922_MASTERY_LEVELS)
    }
    for class_name, skills in CLASS_SKILLS.items():
        if class_name == "Wojownik":
            # v0.24.4 already gave the Warrior authored, non-numbered names.
            continue
        families = _V03014_SKILL_FAMILIES.get(class_name, {})
        for skill in skills:
            sid = str(skill.get("id", ""))
            if not sid.startswith("v0922_"):
                continue
            match = re.search(r"_(\d+)_(\d+)$", sid)
            if not match:
                continue
            original_level = int(match.group(1))
            variant_index = int(match.group(2))
            title = level_to_title.get(original_level, f"Próg {original_level}")
            kind = str(skill.get("kind", "damage"))
            family_options = families.get(kind) or families.get("damage") or (class_name,)
            family = family_options[(variant_index + original_level) % len(family_options)]
            old_name = str(skill.get("name", "")).strip()
            new_name = f"{family}: {title}"
            aliases = [str(a).strip() for a in (skill.get("aliases") or []) if str(a).strip()]
            if old_name and old_name.casefold() not in {a.casefold() for a in aliases}:
                aliases.append(old_name)
                old_aliases_added += 1
            if new_name.casefold() not in {a.casefold() for a in aliases}:
                aliases.append(new_name)
            skill["legacy_display_name_v03013"] = old_name
            skill["name"] = new_name
            skill["aliases"] = aliases
            skill["natural_tags"] = list(dict.fromkeys(
                list(skill.get("natural_tags") or []) +
                [w.lower().strip(":,—") for w in (family + " " + title).split() if w.strip(":,—")]
            ))
            renamed += 1
    return renamed, old_aliases_added


V03014_SKILLS_RENAMED, V03014_OLD_NAME_ALIASES = _v03014_unique_generated_skill_names()


def _v03014_skill_name_audit():
    errors = []
    warnings = []
    seen_names = {}
    seen_ids = {}
    valid_kinds = {
        "damage", "aoe_damage", "execute", "drain", "boost", "guard", "evade",
        "heal", "group_heal", "passive",
    }
    per_class = {}
    numeric_names = []
    for class_name, skills in CLASS_SKILLS.items():
        per_class[class_name] = len(skills)
        for skill in skills:
            sid = str(skill.get("id", "")).strip()
            name = str(skill.get("name", "")).strip()
            kind = str(skill.get("kind", "")).strip()
            if not sid or not name:
                errors.append(f"{class_name}: skill bez id/nazwy")
                continue
            id_key = sid.casefold()
            if id_key in seen_ids:
                errors.append(f"Powtórzone ID {sid}: {seen_ids[id_key]} / {class_name}")
            else:
                seen_ids[id_key] = class_name
            name_key = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode("ascii").casefold()
            name_key = re.sub(r"[^a-z0-9]+", " ", name_key).strip()
            if name_key in seen_names:
                errors.append(f"Powtórzona nazwa {name}: {seen_names[name_key]} / {class_name}")
            else:
                seen_names[name_key] = class_name
            # v0.33.1: cyfry w nazwie wyświetlanej skilla/spella są zabronione.
            # Progi i warianty należą do pól unlock/id, nie do nazwy dla gracza.
            if re.search(r"\d", name):
                numeric_names.append((class_name, name))
            if kind not in valid_kinds:
                warnings.append(f"{class_name}/{name}: nieznany kind={kind}")
            unlock = int(skill.get("unlock", 1) or 1)
            if not (1 <= unlock <= CLASS_MASTERY_MAX_LEVEL):
                errors.append(f"{class_name}/{name}: unlock poza zakresem: {unlock}")
    if numeric_names:
        errors.append(f"Pozostały numerowane nazwy: {len(numeric_names)}")
    return {
        "version": "0.34.4",
        "classes": len(CLASS_SKILLS),
        "skills": sum(per_class.values()),
        "renamed": V03014_SKILLS_RENAMED,
        "legacy_aliases_added": V03014_OLD_NAME_ALIASES,
        "legacy_aliases_preserved": sum(
            1 for _skills in CLASS_SKILLS.values() for _skill in _skills
            if _skill.get("legacy_display_name_v03013") and
            str(_skill.get("legacy_display_name_v03013")).casefold() in
            {str(_a).casefold() for _a in (_skill.get("aliases") or [])}
        ),
        "per_class": per_class,
        "error_count": len(errors),
        "warning_count": len(warnings),
        "errors": errors,
        "warnings": warnings,
    }


# The generator later redistributes unlock numbers, but it does not change names.
# A second final audit is executed near the bottom of the file after Generator Core.
V03014_SKILL_NAME_AUDIT_PREGEN = _v03014_skill_name_audit()
if V03014_SKILL_NAME_AUDIT_PREGEN.get("error_count"):
    raise RuntimeError(
        "Skill/Spell Name Audit v0.30.14 failed before Generator Core: " +
        "; ".join(V03014_SKILL_NAME_AUDIT_PREGEN.get("errors", [])[:20])
    )

# v0.8.42: progi dostępu do skilli są progami Biegłości klasy 1-200.
# Zachowujemy numer dawnego progu Soul jako identyczny próg Biegłości,
# np. dawny 100 -> Biegłość 100, dawny 200 -> Biegłość 200.
def _legacy_skill_unlock_to_mastery(value):
    value = max(1, int(value or 1))
    return min(CLASS_MASTERY_MAX_LEVEL, value)


for _class_name, _skills in CLASS_SKILLS.items():
    for _skill in _skills:
        _legacy_unlock = max(1, int(_skill.get("unlock", 1)))
        _skill["legacy_soul_unlock"] = _legacy_unlock
        _skill["unlock"] = _legacy_skill_unlock_to_mastery(_legacy_unlock)
        _desc = str(_skill.get("desc", ""))
        if "Soul Level" in _desc and "Broni Duszy" in _desc:
            _skill["desc"] = (
                f"Umiejętność klasy {_class_name} odblokowywana przez "
                f"Biegłość klasy {_skill['unlock']}."
            )

# Czytelna kolejność dla skills, nauczycieli i Kodeksu Klasowego.
for _class_name in CLASS_SKILLS:
    CLASS_SKILLS[_class_name].sort(
        key=lambda skill: (int(skill.get("unlock", 1)), skill.get("name", ""))
    )


NATURAL_SKILL_INTENTS = {
    "heal": {"kinds": {"heal"}},
    "healing": {"kinds": {"heal"}},
    "lecz": {"kinds": {"heal"}},
    "leczenie": {"kinds": {"heal"}},
    "uzdrow": {"kinds": {"heal"}},
    "uzdrowienie": {"kinds": {"heal"}},
    "tarcza": {"kinds": {"guard"}},
    "oslona": {"kinds": {"guard"}},
    "guard": {"kinds": {"guard"}},
    "obrona": {"kinds": {"guard"}},
    "unik": {"kinds": {"evade"}},
    "evade": {"kinds": {"evade"}},
    "buff": {"kinds": {"boost"}},
    "boost": {"kinds": {"boost"}},
    "wzmocnij": {"kinds": {"boost"}},
    "wzmocnienie": {"kinds": {"boost"}},
    "drain": {"kinds": {"drain"}},
    "wysysanie": {"kinds": {"drain"}},
    "wysysaj": {"kinds": {"drain"}},
    "egzekucja": {"kinds": {"execute"}},
    "execute": {"kinds": {"execute"}},
    "dobij": {"kinds": {"execute"}},
    "ciecie": {"tags": {"ciecie", "slash"}},
    "slash": {"tags": {"ciecie", "slash"}},
    "pocisk": {"tags": {"pocisk", "bolt", "lanca"}},
    "bolt": {"tags": {"pocisk", "bolt", "lanca"}},
    "ogien": {"tags": {"ogien", "plomien", "fire", "inferno"}},
    "plomien": {"tags": {"ogien", "plomien", "fire", "inferno"}},
    "fire": {"tags": {"ogien", "plomien", "fire", "inferno"}},
    "burza": {"tags": {"burza", "storm"}},
    "storm": {"tags": {"burza", "storm"}},
    "mlot": {"tags": {"mlot", "hammer"}},
    "hammer": {"tags": {"mlot", "hammer"}},
    "strzal": {"tags": {"strzal", "strzala", "shot", "arrow"}},
    "strzala": {"tags": {"strzal", "strzala", "shot", "arrow"}},
    "arrow": {"tags": {"strzal", "strzala", "shot", "arrow"}},
}


# 28 trwałych lokacji. Opisy są krótkie i przyjazne czytnikom ekranu.
ROOMS = {
    "square": {
        "zone": "Miasto Dusz", "name": "Plac Dusz",
        "desc": "Centralny plac osady. Nad kamienną fontanną płonie błękitny ogień.",
        "exits": {"north": "north_street", "south": "south_street", "east": "market", "west": "temple"},
    },
    "temple": {
        "zone": "Miasto Dusz", "name": "Świątynia Odrodzenia",
        "desc": "Spokojna świątynia. Polegli bohaterowie odzyskują tutaj świadomość.",
        "exits": {"east": "square", "north": "library", "down": "temple_basement"},
    },
    "temple_basement": {
        "zone": "Podziemia", "name": "Piwnica Świątyni",
        "desc": "Wilgotna piwnica pod Świątynią Odrodzenia. Między skrzyniami słychać piski szczurów.",
        "exits": {"up": "temple"},
    },
    "library": {
        "zone": "Miasto Dusz", "name": "Biblioteka Kronik",
        "desc": "Kamienne regały przechowują kroniki o duszach, rasach i dawnych wojnach.",
        "exits": {"south": "temple", "east": "guild_hall"},
    },
    "guild_hall": {
        "zone": "Gildia Dusz", "name": "Sala Główna Gildii",
        "desc": "Centralny hol Gildii Dusz. Korytarze prowadzą do wyspecjalizowanych sal nauczycieli.",
        "exits": {
            "west": "library",
            "south": "north_street",
            "north": "guild_martial_hall",
            "east": "guild_arcane_chamber",
            "up": "guild_shadow_gallery",
            "down": "guild_sanctuary",
        },
    },
    "guild_martial_hall": {
        "zone": "Gildia Dusz", "name": "Sala Oręża Gildii",
        "desc": "Ciężkie manekiny i stojaki treningowe służą Wojownikom i Berserkerom.",
        "exits": {"south": "guild_hall", "east": "guild_body_hall"},
    },
    "guild_body_hall": {
        "zone": "Gildia Dusz", "name": "Sala Dyscypliny Gildii",
        "desc": "Spokojna sala ćwiczeń ciała i obrony przeznaczona dla Mnichów i Strażników.",
        "exits": {"west": "guild_martial_hall"},
    },
    "guild_arcane_chamber": {
        "zone": "Gildia Dusz", "name": "Komnata Arkanów Gildii",
        "desc": "Runy świecą na ścianach. Tutaj Magowie i Psionicy ćwiczą kontrolę energii.",
        "exits": {"west": "guild_hall", "east": "guild_dark_chamber"},
    },
    "guild_dark_chamber": {
        "zone": "Gildia Dusz", "name": "Komnata Mrocznych Sztuk",
        "desc": "Zabezpieczona sala do nauki Nekromantów i Czarowników.",
        "exits": {"west": "guild_arcane_chamber"},
    },
    "guild_shadow_gallery": {
        "zone": "Gildia Dusz", "name": "Galeria Cieni Gildii",
        "desc": "Wąskie przejścia i cele treningowe służą Łotrzykom i Łowcom.",
        "exits": {"down": "guild_hall"},
    },
    "guild_sanctuary": {
        "zone": "Gildia Dusz", "name": "Sanktuarium Gildii",
        "desc": "Cicha sala natury i światła, w której szkolą się Kapłani i Druidzi.",
        "exits": {"up": "guild_hall"},
    },
    "north_street": {
        "zone": "Miasto Dusz", "name": "Ulica Północna",
        "desc": "Szeroka ulica prowadząca ku dziedzińcowi i północnej bramie.",
        "exits": {"south": "square", "north": "training", "east": "guard_hall", "west": "guild_hall"},
    },
    "guard_hall": {
        "zone": "Miasto Dusz", "name": "Strażnica Główna",
        "desc": (
            "Główna sala miejskiej straży. Na ścianach wiszą mapy szlaków, "
            "tablice patroli i meldunki z obu bram. Stąd można przejść do koszar, "
            "zbrojowni, komnaty dowódcy, wieży obserwacyjnej i cel strażnicy."
        ),
        "exits": {
            "west": "north_street", "east": "guard_barracks",
            "south": "guard_armory", "north": "guard_command",
            "up": "guard_watchtower", "down": "guard_cells",
        },
    },
    "guard_barracks": {
        "zone": "Miasto Dusz", "name": "Koszary Straży",
        "desc": (
            "Rzędy prycz, stojaki na płaszcze i tablice zmian wypełniają koszary. "
            "Strażnicy odpoczywają tutaj między patrolami północnej i południowej bramy."
        ),
        "exits": {"west": "guard_hall", "east": "guard_mess"},
    },
    "guard_mess": {
        "zone": "Miasto Dusz", "name": "Jadalnia Straży",
        "desc": (
            "Długi stół, kocioł i beczki z wodą zajmują niewielką jadalnię. "
            "Na ścianie wisi plan godzinnych zmian patroli miejskich."
        ),
        "exits": {"west": "guard_barracks"},
    },
    "guard_armory": {
        "zone": "Miasto Dusz", "name": "Zbrojownia Straży",
        "desc": (
            "Zamknięte stojaki przechowują włócznie, tarcze, kusze i zapasowe pancerze. "
            "Kwatermistrz prowadzi tu ewidencję wyposażenia miejskiej straży."
        ),
        "exits": {"north": "guard_hall"},
    },
    "guard_command": {
        "zone": "Miasto Dusz", "name": "Komnata Dowódcy Straży",
        "desc": (
            "Duży stół mapowy pokazuje Miasto Dusz, Stary Trakt, Gaj Szeptów i pogranicze. "
            "Tutaj planowane są patrole i akcje przeciw goblinom oraz bandytom."
        ),
        "exits": {"south": "guard_hall", "east": "guard_archive"},
    },
    "guard_archive": {
        "zone": "Miasto Dusz", "name": "Archiwum Straży",
        "desc": (
            "Regały są pełne raportów z patroli, listów gończych i starych map. "
            "Archiwistka straży porządkuje meldunki z obu bram."
        ),
        "exits": {"west": "guard_command"},
    },
    "guard_watchtower": {
        "zone": "Miasto Dusz", "name": "Wieża Obserwacyjna Straży",
        "desc": (
            "Z kamiennej wieży widać północną bramę, Stary Trakt i dachy miasta. "
            "Wartownicy przekazują stąd sygnały do posterunków przy bramach."
        ),
        "exits": {"down": "guard_hall"},
    },
    "guard_cells": {
        "zone": "Miasto Dusz", "name": "Cele Strażnicy",
        "desc": (
            "Kilka żelaznych cel służy do przetrzymywania schwytanych bandytów i szabrowników. "
            "Korytarz prowadzi do małego pokoju przesłuchań."
        ),
        "exits": {"up": "guard_hall", "east": "guard_interrogation"},
    },
    "guard_interrogation": {
        "zone": "Miasto Dusz", "name": "Pokój Przesłuchań",
        "desc": (
            "Surowy stół, dwa krzesła i półka z raportami tworzą niewielki pokój przesłuchań. "
            "Straż zbiera tu informacje o napadach, goblinach i ruchach bandytów."
        ),
        "exits": {"west": "guard_cells"},
    },
    "training": {
        "zone": "Miasto Dusz", "name": "Plac Treningowy",
        "desc": "Plac do ćwiczeń. Drewniane manekiny stoją obok północnej bramy.",
        "exits": {"south": "north_street", "north": "north_gate"},
    },
    "north_gate": {
        "zone": "Miasto Dusz", "name": "Północna Brama",
        "desc": (
            "Ciężka brama otwiera się na Stary Trakt. Dwóch miejskich strażników "
            "pełni tu stałą wartę i kontroluje podróżnych wracających z pogranicza."
        ),
        "exits": {"south": "training", "north": "old_road"},
    },
    "market": {
        "zone": "Miasto Dusz", "name": "Rynek",
        "desc": (
            "Kupcy sprzedają prowiant i podstawowe wyposażenie. Mikstury kupisz w Aptece Pod Srebrnym Liściem. "
            "Przy kamiennym kantorze działa Bank Dusz Bankiera Aldrena. "
            "Handlarz Skupu Radan kupuje łupy, trofea i niezałożone EQ, "
            "ale nie skupuje ryb, rud, drewna, ziół ani innych materiałów rzemieślniczych."
        ),
        "exits": {"west": "square", "east": "forge", "south": "inn", "north": "fish_market"},
    },
    "fish_market": {
        "zone": "Miasto Dusz", "name": "Targ Rybny",
        "desc": "Stragany pachną świeżą rybą i mokrymi sieciami. Tutaj sprzedaje się sprzęt wędkarski.",
        "exits": {"south": "market", "east": "harbor"},
    },
    "harbor": {
        "zone": "Miasto Dusz", "name": "Port Dusz",
        "desc": "Drewniane pomosty, kutry i skrzynie rybackie wypełniają miejski port.",
        "exits": {"west": "fish_market", "east": "sea_pier"},
    },
    "sea_pier": {
        "zone": "Wybrzeże", "name": "Morskie Molo",
        "desc": "Długie molo wychodzi nad morze. To łowisko typowych ryb morskich.",
        "exits": {"west": "harbor", "east": "ocean_platform"},
    },
    "ocean_platform": {
        "zone": "Wybrzeże", "name": "Oceaniczna Platforma",
        "desc": "Daleka platforma nad otwartym oceanem. Trafiają się tu wielkie ryby oceaniczne i rekiny.",
        "exits": {"west": "sea_pier"},
    },
    "forge": {
        "zone": "Miasto Dusz", "name": "Kuźnia Dusz",
        "desc": "Młoty uderzają o metal, a Broń Duszy odpowiada cichym rezonansem.",
        "exits": {"west": "market"},
    },
    "inn": {
        "zone": "Miasto Dusz", "name": "Karczma Pod Błękitnym Płomieniem",
        "desc": "Ciepła karczma pełna rozmów podróżników.",
        "exits": {"north": "market", "west": "south_street"},
    },
    "south_street": {
        "zone": "Miasto Dusz", "name": "Ulica Południowa",
        "desc": "Cichsza część miasta prowadząca do południowej bramy.",
        "exits": {"north": "square", "east": "inn", "south": "south_gate"},
    },
    "south_gate": {
        "zone": "Miasto Dusz", "name": "Południowa Brama",
        "desc": (
            "Brama otwiera się na łąki i Gaj Szeptów. Miejska straż utrzymuje tu "
            "stały posterunek i ostrzega podróżnych o wilkach oraz zagrożeniach w dziczy."
        ),
        "exits": {"north": "south_street", "south": "meadow"},
    },
    "meadow": {
        "zone": "Łąki", "name": "Srebrna Łąka",
        "desc": (
            "Centralna część rozległych łąk. W trawie rosną Pokrzywa, "
            "Rumianek, Mięta, Krwawnik, Melisa i Lawenda. "
            "Na zachodzie leży Łąka Kwiatów, na wschodzie Łąka Mięty, "
            "a na południu Łąka Nadjeziorna."
        ),
        "exits": {
            "north": "south_gate",
            "west": "flower_meadow",
            "east": "mint_meadow",
            "south": "lakeside_meadow",
        },
    },
    "mint_meadow": {
        "zone": "Łąki", "name": "Łąka Mięty",
        "desc": (
            "Wilgotniejsza łąka pachnąca Miętą i Melisą. "
            "To dobre miejsce do Zielarstwa, szczególnie dla początkujących."
        ),
        "exits": {"west": "meadow", "east": "riverbank"},
    },
    "flower_meadow": {
        "zone": "Łąki", "name": "Łąka Kwiatów",
        "desc": (
            "Kolorowa łąka pełna Rumianku, Lawendy i Krwawnika. "
            "Dalej na zachodzie zaczyna się Gaj Szeptów."
        ),
        "exits": {"east": "meadow", "west": "whisper_grove"},
    },
    "lakeside_meadow": {
        "zone": "Łąki", "name": "Łąka Nadjeziorna",
        "desc": (
            "Łąka schodząca ku Srebrnemu Jezioru. "
            "Rosną tu Mięta, Melisa, Rumianek i inne zioła lubiące wilgoć."
        ),
        "exits": {"north": "meadow", "south": "lake_shore"},
    },
    "lake_shore": {
        "zone": "Dzicz", "name": "Brzeg Srebrnego Jeziora",
        "desc": "Spokojne jezioro jest osobnym łowiskiem dla ryb jeziorowych.",
        "exits": {"north": "lakeside_meadow"},
    },
    "whisper_grove": {
        "zone": "Dzicz", "name": "Gaj Szeptów",
        "desc": "Stare drzewa szepczą pod wpływem magicznego wiatru.",
        "exits": {"east": "flower_meadow", "south": "deep_grove", "west": "lumberjack_camp", "north": "herbalist_hut"},
    },
    "herbalist_hut": {
        "zone": "Dzicz", "name": "Chata Zielarki",
        "desc": "Półki są pełne suszonych ziół, fiolek i alchemicznych naczyń.",
        "exits": {"south": "whisper_grove"},
    },
    "lumberjack_camp": {
        "zone": "Dzicz", "name": "Obóz Drwala",
        "desc": "Przy stosach drewna stoi warsztat Drwala Brana. Tutaj kupuje się Piłę.",
        "exits": {"east": "whisper_grove"},
    },
    "deep_grove": {
        "zone": "Dzicz", "name": "Głębia Gaju",
        "desc": "Światło prawie nie dociera między gęste konary.",
        "exits": {"north": "whisper_grove", "east": "hill"},
    },
    "hill": {
        "zone": "Dzicz", "name": "Wzgórze Kamiennych Znaków",
        "desc": "Na szczycie stoją stare kamienie pokryte nieczytelnymi runami.",
        "exits": {"west": "deep_grove", "north": "shrine"},
    },
    "shrine": {
        "zone": "Dzicz", "name": "Zapomniana Kapliczka",
        "desc": "Mała kapliczka poświęcona dawnym strażnikom dusz.",
        "exits": {"south": "hill"},
    },
    "riverbank": {
        "zone": "Dzicz", "name": "Brzeg Rzeki",
        "desc": "Szybka rzeka oddziela łąki od ruin starego pogranicza.",
        "exits": {"west": "mint_meadow", "east": "stone_bridge"},
    },
    "stone_bridge": {
        "zone": "Dzicz", "name": "Kamienny Most",
        "desc": "Popękany most prowadzi na wschodni brzeg.",
        "exits": {"west": "riverbank", "east": "ruined_watchtower"},
    },
    "ruined_watchtower": {
        "zone": "Ruiny Strażnicy", "name": "Ruiny Strażnicy",
        "desc": (
            "Zawalona wieża obserwacyjna góruje nad starym pograniczem. "
            "Gobliny plądrują wejście, lecz spod gruzów prowadzą schody do zachowanych części dawnego garnizonu."
        ),
        "exits": {
            "west": "stone_bridge", "south": "goblin_camp", "east": "graveyard",
            "down": "ruin_gatehouse",
        },
    },
    "ruin_gatehouse": {
        "zone": "Ruiny Strażnicy", "name": "Zawalona Brama Strażnicy",
        "desc": (
            "Kamienny korytarz pod wieżą wciąż nosi ślady dawnej obrony. "
            "Połamane kraty i tarcze tworzą wąskie przejście do wnętrza ruin."
        ),
        "exits": {"up": "ruined_watchtower", "east": "ruin_courtyard"},
    },
    "ruin_courtyard": {
        "zone": "Ruiny Strażnicy", "name": "Wewnętrzny Dziedziniec",
        "desc": (
            "Popękane płyty dziedzińca otaczają resztki studni. "
            "Wokół zachowały się wejścia do koszar, murów i piwnic dawnej straży."
        ),
        "exits": {
            "west": "ruin_gatehouse", "north": "ruin_barracks",
            "east": "ruin_wall_walk", "south": "ruin_cellar",
        },
    },
    "ruin_barracks": {
        "zone": "Ruiny Strażnicy", "name": "Opuszczone Koszary",
        "desc": (
            "Spróchniałe prycze stoją między zardzewiałymi stojakami na broń. "
            "Niektórzy dawni strażnicy najwyraźniej nigdy nie opuścili posterunku."
        ),
        "exits": {"south": "ruin_courtyard", "east": "ruin_armory"},
    },
    "ruin_armory": {
        "zone": "Ruiny Strażnicy", "name": "Zbrojownia Starej Straży",
        "desc": (
            "Ciężkie szafy i skrzynie z resztkami uzbrojenia wypełniają kamienną salę. "
            "Na ścianach wiszą pęknięte herby dawnego garnizonu."
        ),
        "exits": {"west": "ruin_barracks", "east": "ruin_command_chamber"},
    },
    "ruin_wall_walk": {
        "zone": "Ruiny Strażnicy", "name": "Chodnik na Murze",
        "desc": (
            "Wąski chodnik biegnie po ocalałym fragmencie muru. "
            "Dawne stanowiska kuszników nadal spoglądają na drogę i dolinę."
        ),
        "exits": {"west": "ruin_courtyard", "north": "ruin_archive"},
    },
    "ruin_archive": {
        "zone": "Ruiny Strażnicy", "name": "Archiwum Runiczne",
        "desc": (
            "Kamienne tablice i metalowe pieczęcie pokrywają resztki archiwum. "
            "W powietrzu utrzymuje się słaba, lecz wciąż aktywna magia ochronna."
        ),
        "exits": {"south": "ruin_wall_walk", "down": "ruin_undercroft"},
    },
    "ruin_cellar": {
        "zone": "Ruiny Strażnicy", "name": "Piwnice Strażnicy",
        "desc": (
            "Wilgotne piwnice pełne są rozbitych beczek, kości i śladów szabrowników. "
            "Niżej prowadzi stary tunel służbowy."
        ),
        "exits": {"north": "ruin_courtyard", "down": "ruin_undercroft"},
    },
    "ruin_undercroft": {
        "zone": "Ruiny Strażnicy", "name": "Podziemia Garnizonu",
        "desc": (
            "Niskie sklepienia podtrzymują filary pokryte znakami wartowników. "
            "Stąd prowadzi droga do zapieczętowanej sali wewnętrznej."
        ),
        "exits": {
            "up": "ruin_cellar", "west": "ruin_archive", "east": "ruin_sealed_hall",
        },
    },
    "ruin_sealed_hall": {
        "zone": "Ruiny Strażnicy", "name": "Sala Pieczęci",
        "desc": (
            "Pęknięte pieczęcie na posadzce wciąż pulsują bladym światłem. "
            "Za nimi znajduje się dawna komnata dowódcy strażnicy."
        ),
        "exits": {"west": "ruin_undercroft", "north": "ruin_command_chamber"},
    },
    "ruin_command_chamber": {
        "zone": "Ruiny Strażnicy", "name": "Komnata Dowódcy Strażnicy",
        "desc": (
            "Ocalały stół dowódcy stoi pod poszarpanym sztandarem. "
            "Najpotężniejszy z dawnych obrońców strzeże tej komnaty nawet po upadku garnizonu."
        ),
        "exits": {"south": "ruin_sealed_hall", "west": "ruin_armory"},
    },
    "goblin_camp": {
        "zone": "Dzicz", "name": "Obóz Goblinów",
        "desc": (
            "Prymitywne namioty stoją wokół dymiącego ogniska. "
            "Na wschodzie w skale zieje wejście do rozległych Jaskiń Goblinów."
        ),
        "exits": {"north": "ruined_watchtower", "south": "cave_entrance", "east": "goblin_cave_mouth"},
    },
    "goblin_cave_mouth": {
        "zone": "Jaskinie Goblinów", "name": "Wejście do Jaskiń Goblinów",
        "desc": "Niski skalny otwór jest obwieszony kośćmi, sznurkami i prymitywnymi dzwonkami alarmowymi.",
        "exits": {"west": "goblin_camp", "east": "goblin_fungus_gallery"},
    },
    "goblin_fungus_gallery": {
        "zone": "Jaskinie Goblinów", "name": "Galeria Grzybów",
        "desc": "Wilgotny korytarz porastają świecące grzyby. W bocznych niszach widać ślady goblińskich wartowników.",
        "exits": {"west": "goblin_cave_mouth", "east": "goblin_scrap_tunnels", "south": "goblin_shaman_hollow"},
    },
    "goblin_scrap_tunnels": {
        "zone": "Jaskinie Goblinów", "name": "Tunele Złomu",
        "desc": "Gobliny zatarasowały ściany resztkami pancerzy, kół i połamanych narzędzi.",
        "exits": {"west": "goblin_fungus_gallery", "east": "goblin_guard_post", "south": "goblin_bomb_workshop"},
    },
    "goblin_shaman_hollow": {
        "zone": "Jaskinie Goblinów", "name": "Kotlina Szamanów",
        "desc": "Dym z gorzkich ziół miesza się tu z zielonkawą poświatą prostych goblińskich rytuałów.",
        "exits": {"north": "goblin_fungus_gallery", "east": "goblin_war_den"},
    },
    "goblin_bomb_workshop": {
        "zone": "Jaskinie Goblinów", "name": "Warsztat Bombiarzy",
        "desc": "Na chwiejnych stołach leżą gliniane kule, proch i wiązki lontów. Powietrze pachnie siarką.",
        "exits": {"north": "goblin_scrap_tunnels", "east": "goblin_war_den"},
    },
    "goblin_guard_post": {
        "zone": "Jaskinie Goblinów", "name": "Podziemny Posterunek",
        "desc": "Drewniane barykady i ostre pale tworzą pierwszy prawdziwy punkt obrony głębszej części jaskiń.",
        "exits": {"west": "goblin_scrap_tunnels", "east": "goblin_war_den"},
    },
    "goblin_war_den": {
        "zone": "Jaskinie Goblinów", "name": "Nora Wojenna",
        "desc": "Kamienne stoły pokrywają mapy szlaków, skradzione chorągwie i stosy broni gotowej do użycia.",
        "exits": {"west": "goblin_guard_post", "north": "goblin_shaman_hollow", "south": "goblin_bomb_workshop", "east": "goblin_treasure_burrow"},
    },
    "goblin_treasure_burrow": {
        "zone": "Jaskinie Goblinów", "name": "Nora Łupów",
        "desc": "Skrzynie, worki i chaotyczne stosy skradzionych przedmiotów wypełniają prawie całe pomieszczenie.",
        "exits": {"west": "goblin_war_den", "east": "goblin_throne_cave"},
    },
    "goblin_throne_cave": {
        "zone": "Jaskinie Goblinów", "name": "Grota Króla Goblinów",
        "desc": "Najgłębsza komora została zamieniona w prymitywną salę tronową. Tu rządzi Król Goblinów.",
        "exits": {"west": "goblin_treasure_burrow"},
    },
    "cave_entrance": {
        "zone": "Podziemia", "name": "Wejście do Kopalni Głębinowej",
        "desc": "Główne wejście do jedynej kopalni świata. Niżej zaczynają się kolejne poziomy Kopalni Głębinowej.",
        "exits": {"north": "goblin_camp", "down": "cave_tunnel"},
    },
    "cave_tunnel": {
        "zone": "Podziemia", "name": "Tunel Wejściowy Kopalni Głębinowej",
        "desc": "Tunel prowadzi z wejścia do komnaty zejściowej Kopalni Głębinowej.",
        "exits": {"up": "cave_entrance", "east": "crystal_chamber"},
    },
    "crystal_chamber": {
        "zone": "Podziemia", "name": "Komnata Zejściowa Kopalni Głębinowej",
        "desc": "Ostatnia komnata wejściowa. Stąd schodzi się na poziom 1 jedynej Kopalni Głębinowej.",
        "exits": {"west": "cave_tunnel"},
    },
    "graveyard": {
        "zone": "Dzicz", "name": "Stary Cmentarz",
        "desc": "Pęknięte nagrobki otaczają zejście do zapomnianej krypty.",
        "exits": {"west": "ruined_watchtower", "down": "crypt_entrance"},
    },
    "crypt_entrance": {
        "zone": "Podziemia", "name": "Przedsionek Krypty",
        "desc": "Kamienne schody prowadzą w ciemność.",
        "exits": {"up": "graveyard", "south": "crypt_hall"},
    },
    "crypt_hall": {
        "zone": "Podziemia", "name": "Sala Krypty",
        "desc": "W ścianach znajdują się stare nisze grobowe.",
        "exits": {"north": "crypt_entrance", "down": "crypt_depths"},
    },
    "crypt_depths": {
        "zone": "Podziemia", "name": "Głębia Krypty",
        "desc": "Najstarsza część podziemi. Powietrze drży od niespokojnej energii.",
        "exits": {"up": "crypt_hall"},
    },
    "old_road": {
        "zone": "Dzicz", "name": "Stary Trakt",
        "desc": "Kamienny trakt prowadzi między zarośniętymi słupami granicznymi. Na wschodzie widać wartownię straży.",
        "exits": {"south": "north_gate", "north": "crossroads", "east": "north_watchpost"},
    },
    "north_watchpost": {
        "zone": "Dzicz", "name": "Wartownia Północna",
        "desc": "Drewniana wartownia pilnuje północnego szlaku. Strażnicy obserwują ruch na Starym Trakcie.",
        "exits": {"west": "old_road", "east": "frontier_watchpost"},
    },
    "frontier_watchpost": {
        "zone": "Dzicz", "name": "Wartownia Pogranicza",
        "desc": "Kamienno-drewniany posterunek stoi na granicy bezpiecznych ziem. Dalej zaczyna się teren bandytów.",
        "exits": {"west": "north_watchpost", "east": "bandit_camp"},
    },
    "bandit_camp": {
        "zone": "Obozowiska Bandytów", "name": "Skraj Obozowiska Bandytów",
        "desc": (
            "Pierwsze brudne namioty i wygasające ogniska stoją tuż za granicą straży. "
            "Dalej obozowisko rozdziela się na kilka pilnowanych części."
        ),
        "exits": {"west": "frontier_watchpost", "east": "bandit_outer_ring", "north": "bandit_supply_tents", "south": "bandit_training_yard"},
    },
    "bandit_outer_ring": {
        "zone": "Obozowiska Bandytów", "name": "Zewnętrzny Pierścień Obozu",
        "desc": "Niskie barykady, ogniska i prowizoryczne strażnice tworzą zewnętrzny pas obrony bandytów.",
        "exits": {"west": "bandit_camp", "east": "bandit_barricade"},
    },
    "bandit_supply_tents": {
        "zone": "Obozowiska Bandytów", "name": "Namioty Zaopatrzenia",
        "desc": "Pod płachtami leżą worki z jedzeniem, beczki i towary zabrane kupieckim karawanom.",
        "exits": {"south": "bandit_camp", "east": "bandit_loot_depot"},
    },
    "bandit_training_yard": {
        "zone": "Obozowiska Bandytów", "name": "Plac Ćwiczeń Bandytów",
        "desc": "Zużyte manekiny, tarcze i prowizoryczna arena służą bandytom do brutalnych ćwiczeń.",
        "exits": {"north": "bandit_camp", "east": "bandit_arena"},
    },
    "bandit_barricade": {
        "zone": "Obozowiska Bandytów", "name": "Wewnętrzna Barykada",
        "desc": "Wysoka palisada oddziela zwykłych rabusiów od lepiej uzbrojonej części obozu.",
        "exits": {"west": "bandit_outer_ring", "east": "bandit_inner_camp"},
    },
    "bandit_loot_depot": {
        "zone": "Obozowiska Bandytów", "name": "Magazyn Łupów",
        "desc": "Skrzynie z monetami, bronią i skradzionymi zapasami stoją pod silną strażą.",
        "exits": {"west": "bandit_supply_tents", "south": "bandit_inner_camp"},
    },
    "bandit_arena": {
        "zone": "Obozowiska Bandytów", "name": "Krąg Walk",
        "desc": "Ubita ziemia jest otoczona palami. Najsilniejsi bandyci ćwiczą tu walkę bez zasad.",
        "exits": {"west": "bandit_training_yard", "north": "bandit_inner_camp"},
    },
    "bandit_inner_camp": {
        "zone": "Obozowiska Bandytów", "name": "Wewnętrzne Obozowisko",
        "desc": "Tu stoją najlepsze namioty, stoły dowódców i straże pilnujące drogi do kwatery Herszta.",
        "exits": {"west": "bandit_barricade", "north": "bandit_loot_depot", "south": "bandit_arena", "east": "bandit_command_tent"},
    },
    "bandit_command_tent": {
        "zone": "Obozowiska Bandytów", "name": "Namiot Herszta",
        "desc": "Duży namiot pełen map, rozkazów i trofeów. To tutaj przebywa Herszt Bandytów.",
        "exits": {"west": "bandit_inner_camp"},
    },
    "crossroads": {
        "zone": "Dzicz", "name": "Rozdroże",
        "desc": "Stary drogowskaz wskazuje zachód ku lasom i wschód ku ruinom.",
        "exits": {"south": "old_road", "west": "deep_grove", "east": "ruined_watchtower"},
    },
}
