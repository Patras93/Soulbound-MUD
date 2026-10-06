# v0.45.0: explicit imports; no compatibility-runtime injection.
import re
import unicodedata
from core.character_resources import (
    character_hp_base as authored_character_hp_base,
    character_mana_base as authored_character_mana_base,
    race_passive_profile as authored_race_passive_profile,
)
from core.progression_600 import CLASS_MASTERY_MAX_LEVEL, ENDGAME_ORE_UNLOCKS, SOUL_MAX_LEVEL
from core.progression_resources import (
    FISH_ATLAS_ALL,
    FISH_RESOURCE_IDS,
    HERB_ATLAS_ALL,
    HERB_RESOURCE_IDS,
    ORE_ATLAS_ALL,
    ORE_RESOURCE_IDS,
    WOOD_ATLAS_ALL,
    WOOD_RESOURCE_IDS,
    WORLD_ORE_UNLOCKS,
)


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

# v0.24.4: rudy progresji 220-600 wymagają równocześnie odpowiedniego
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
    ("Smok",
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
    "Smok": {
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

PHYSICAL_MANA_FREE_CLASSES = frozenset(
    class_name for class_name, class_type, _weapon, _power in CLASSES
    if class_type == "physical"
)

def effective_skill_mana_cost(skill, class_name):
    """Return the gameplay MP cost without discarding source-authored magic costs.

    Physical classes remain mana-free by default, but an authored ability may
    carry an exact source MP cost (for example the Mec magic/support branches).
    """
    row = skill or {}
    for field in ("uoss_mp_cost", "source_mp_cost"):
        if row.get(field) is not None:
            try:
                return max(0, int(row.get(field) or 0))
            except (TypeError, ValueError):
                return 0
    if str(class_name) in PHYSICAL_MANA_FREE_CLASSES:
        return 0
    try:
        return max(0, int(row.get("mana", 0) or 0))
    except (TypeError, ValueError):
        return 0

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
    """Character-creation preview uses the same authored runtime resource model."""
    stats = class_starting_stats_for(race, cls)
    hp = authored_character_hp_base(1, stats["constitution"])
    mana = authored_character_mana_base(
        1, stats["intelligence"], stats["willpower"]
    )
    race_profile = authored_race_passive_profile(race[0])
    if race_profile["kind"] == "max_hp":
        hp = int(round(hp * (1.0 + race_profile["value"])))
    if race_profile["kind"] == "max_mana":
        mana = int(round(mana * (1.0 + race_profile["value"])))
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
            "desc": "Skoncentrowane uderzenie skalowane Zręcznością.",
            "scale": "dexterity", "mult": 2.05,
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
            "desc": "Szybka seria ciosów skalowana Zręcznością.",
            "scale": "dexterity", "mult": 2.50,
        },
        {
            "id": "monk_enlightened_strike",
            "name": "Cios Oświecenia",
            "aliases": ["cios oswiecenia", "cios oświecenia", "enlightened strike"],
            "natural_tags": ["cios", "oswiecenie", "dobij", "egzekucja"],
            "unlock": 200, "kind": "execute", "cooldown": 15, "mana": 0,
            "desc": "Ostateczny cios Mnicha skalowany Zręcznością, silniejszy na osłabionym przeciwniku.",
            "scale": "dexterity", "mult": 2.45, "execute_mult": 1.90,
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
            "id": "priest_regen",
            "name": "Regen",
            "aliases": ["regen", "white magic regen", "whitemagic regen"],
            "natural_tags": ["heal", "leczenie", "regen", "odnowa"],
            "unlock": 1, "kind": "regen", "cooldown": 0, "mana": 8,
            "desc": "Regeneracja Kapłana. Cel: siebie albo jeden sojusznik. Leczy małą liczbę HP co kilka rund i znika po krótkim czasie. Siła Woli wpływa na efekt, a poziom umiejętności zwiększa czas działania.",
            "source_ap_cost": 300,
            "source_ap_semantics": "learning_points",
            "source_ap_is_damage_power": False,
            "source_requirements": [],
            "source_requires_none": True,
            "source_target_mode": ["self", "one_ally"],
            "source_stat_influence": ["will"],
            "source_properties": ["dispelable", "extendable", "reflectable", "silenceable"],
            "level_effect": "increases_duration",
            "scale": "willpower",
            "source_extendable": True, "source_dispellable": True,
            "source_reflectable": True, "source_silenceable": True,
            "source_duration_scales_with_level": True,
            "source_periodic_heal": True,
            "source_tick_cadence_defined": False,
            "source_heal_amount_defined": False,
            "source_base_duration_defined": False,
            "soulbound_tick_every_rounds": 3,
            "soulbound_duration_model": "30_to_90_seconds_by_skill_level",
            "soulbound_heal_model": "small_will_scaled_periodic_heal",
        },
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


# v1.11.96: canonical UOSS status contract supplied from Temple Knight.
# Temple Knight is not one of Soulbound's 14 playable classes, so this does not
# install a fifteenth class. It defines the sourced meaning of Silence for
# existing/future effects that apply that status.
UOSS_STATUS_SOURCE_CONTRACTS_V11196 = {
    "silence": {
        "source_job": "Temple Knight",
        "source_ability": "Silence",
        "source_ap_cost": 270,
        "source_ap_semantics": "learning_points",
        "source_ap_is_damage_power": False,
        "source_requirements": [],
        "source_requires_none": True,
        "source_usage": "use magicsword silence [at target]",
        "source_target_mode": "one_enemy",
        "soulbound_target_scope": "enemy_only",
        "source_mp_cost": 32,
        "source_stat_influence": ["will"],
        "source_properties": ["cleanseable", "extendable"],
        "level_effect": "increases_accuracy_and_duration",
        "source_effect": "prevents_magic_casting",
        "source_weapon_requirement": ["sword", "greatsword"],
        "accuracy_numeric_source_defined": False,
        "duration_numeric_source_defined": False,
    },
}


def _uoss_status_source_contract_audit_v11196():
    errors=[]
    silence=UOSS_STATUS_SOURCE_CONTRACTS_V11196.get("silence",{})
    if int(silence.get("source_ap_cost",0) or 0)!=270:
        errors.append("silence: Base AP 270 must remain learning points")
    if str(silence.get("source_ap_semantics",""))!="learning_points":
        errors.append("silence: AP semantics must be learning_points")
    if list(silence.get("source_requirements") or [])!=[] or not bool(silence.get("source_requires_none")):
        errors.append("silence: Reqs must remain None")
    if str(silence.get("source_target_mode",""))!="one_enemy":
        errors.append("silence: target must remain One Enemy")
    if str(silence.get("soulbound_target_scope",""))!="enemy_only":
        errors.append("silence: Soulbound scope must remain enemy_only")
    if int(silence.get("source_mp_cost",0) or 0)!=32:
        errors.append("silence: MP cost must remain 32")
    if list(silence.get("source_stat_influence") or [])!=["will"]:
        errors.append("silence: Stat Influence must remain Will")
    if list(silence.get("source_properties") or [])!=["cleanseable","extendable"]:
        errors.append("silence: source Properties mismatch")
    if str(silence.get("level_effect",""))!="increases_accuracy_and_duration":
        errors.append("silence: Level Effect must increase Accuracy and Duration")
    if str(silence.get("source_effect",""))!="prevents_magic_casting":
        errors.append("silence: effect must prevent magic casting")
    return {"version":"1.11.96","error_count":len(errors),"errors":errors}


UOSS_STATUS_SOURCE_CONTRACT_AUDIT_V11196=_uoss_status_source_contract_audit_v11196()
if UOSS_STATUS_SOURCE_CONTRACT_AUDIT_V11196["error_count"]:
    raise RuntimeError(
        "UOSS Status Source Contract Audit v1.11.96 failed: "
        + "; ".join(UOSS_STATUS_SOURCE_CONTRACT_AUDIT_V11196["errors"])
    )


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
        {"id":"priest_healing_wind","name":"Healing Wind","aliases":["healing wind","leczacy wiatr","leczący wiatr"],"natural_tags":["heal","leczenie","grupa","druzyna"],"unlock":1,"kind":"group_heal","cooldown":0,"mana":60,"scale":"willpower","source_ap_cost":1500,"source_ap_semantics":"learning_points","source_ap_is_damage_power":False,"source_requirements":[],"source_requires_none":True,"source_target_mode":"all_allies","source_stat_influence":["will"],"source_properties":["multicastable","silenceable"],"level_effect":"increases_healing_power","healing_numeric_source_defined":False,"desc":"Leczy wszystkich żywych członków drużyny w tej samej lokacji. Will i Skill Level zwiększają moc leczenia."},
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
        skill["execute_mult"] = round(min(2.0, 1.45 + int(soul_level) / float(SOUL_MAX_LEVEL)), 2)
        skill["cooldown"] = min(17, 9 + int(soul_level) // 30)
    elif kind == "drain":
        skill["scale"] = profile["scale"]
        skill["mult"] = round(1.16 + int(soul_level) * 0.0074, 2)
        skill["drain_pct"] = round(min(0.48, 0.24 + int(soul_level) / 800.0), 2)
        skill["cooldown"] = min(15, 8 + int(soul_level) // 35)
    elif kind == "boost":
        skill["boost"] = round(min(1.70, 1.20 + int(soul_level) / float(SOUL_MAX_LEVEL)), 2)
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


# v0.9.12: nowe umiejętności Biegłości 220-600. Stare progi 1-200
# pozostają bez zmian; nowe skille mają malejący przyrost mocy.
_POST200_SKILL_STAGES = (
    (220, "Przebudzenie"), (240, "Transcendencja"), (260, "Horyzont"),
    (280, "Otchłań"), (300, "Gwiezdny Rdzeń"), (320, "Pierwotność"),
    (340, "Nieskończoność"), (360, "Korona Świata"),
    (380, "Ponadczasowość"), (400, "Absolut"),
    (420, "Przekroczenie"), (440, "Gwiezdny Tron"),
    (460, "Wieczne Echo"), (480, "Serce Otchłani"),
    (500, "Korona Gwiazd"), (520, "Sąd Horyzontu"),
    (540, "Kosmiczny Szlak"), (560, "Wieczność"),
    (580, "Apogeum"), (600, "Absolut Duszy"),
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
    progress = (level - 200) / float(max(1, CLASS_MASTERY_MAX_LEVEL - 200))
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
            "Przekroczenia Granic", "Gwiezdnego Tronu", "Wiecznego Echa",
            "Serca Otchłani", "Korony Gwiazd", "Sądu Horyzontu",
            "Nieskończonego Pulsu", "Kosmicznej Pieczęci", "Pradawnego Rezonansu",
            "Świtu Absolutu", "Drogi Przeznaczenia", "Oka Wszechświata",
            "Wiecznej Iskry", "Transcendentnego Znaku", "Głosu Nieskończoności",
            "Ostatecznego Horyzontu", "Duszy Kosmosu", "Korony Wieczności",
            "Apogeum Wojny", "Absolutu Duszy",
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
    progress = min(1.0, max(0.0, (level - 1) / float(max(1, CLASS_MASTERY_MAX_LEVEL - 1))))
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
    "Przekroczenie Granic", "Gwiezdny Tron", "Wieczne Echo", "Serce Otchłani",
    "Korona Gwiazd", "Sąd Horyzontu", "Nieskończony Puls", "Kosmiczna Pieczęć",
    "Pradawny Rezonans", "Świt Absolutu", "Droga Przeznaczenia", "Oko Wszechświata",
    "Wieczna Iskra", "Transcendentny Znak", "Głos Nieskończoności",
    "Ostateczny Horyzont", "Dusza Kosmosu", "Korona Wieczności", "Apogeum", "Absolut Duszy",
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
        base["mult"] = round(1.20 + min(1.10, level / float(CLASS_MASTERY_MAX_LEVEL)) + index * 0.08, 2)
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
    levels = (1, *range(10, CLASS_MASTERY_MAX_LEVEL + 1, 10))
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
        "Absolutny Rdzeń", "Przekroczenie Obwodu", "Gwiezdny Tron Maszyny",
        "Wieczne Echo Rdzenia", "Serce Otchłani Techniki", "Korona Gwiezdnej Maszyny",
        "Sąd Horyzontu Techniki", "Nieskończony Puls Systemu", "Kosmiczna Matryca",
        "Pradawny Rezonator", "Świt Absolutnego Rdzenia", "Moduł Przeznaczenia",
        "Oko Wszechsystemu", "Wieczna Iskra Maszyny", "Transcendentny Obwód",
        "Głos Nieskończonej Sieci", "Ostateczny Horyzont Techniki", "Dusza Kosmicznej Maszyny",
        "Korona Wiecznego Rdzenia", "Apogeum Techniki", "Absolut Maszyny",
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

# v0.31.9: Full authored Mec kit based on the user-provided UOSSMUD ability list.
# Source Base AP is an AP/learning cost from UOSS, NOT an attack-power value.
# Soulbound stores it only as source_ap_cost metadata; combat power comes from
# Soul Power, effective stats/EQ, Skill Level, protocols and authored mechanics.
def _v0319_install_full_mec_kit():
    rows = CLASS_SKILLS.get("Mec", [])
    specs = [
        # Melee
        ("Hammer Crush",1,"damage",200,"melee","hammer_crush","Attack-based heavy smash against one enemy. Carries the active Soul Weapon element and uses the Mec melee Soul Weapon role."),
        ("Shock Soldier",14,"aoe_damage",600,"melee","shock_soldier","Attack-based melee barrage against all enemies with diminishing damage. Carries the active Soul Weapon element and uses the Mec melee Soul Weapon role."),
        ("Plural Slash",32,"damage",900,"melee","plural_slash","Attack-led multi-slash against one enemy. Agility/DEX adds a smaller damage contribution to every slash even for strength-oriented melee builds. Carries the active Soul Weapon element."),
        ("Pop Knight",46,"aoe_damage",1500,"melee","pop_knight","Attack-based non-diminishing melee attack on all enemies. Carries the active Soul Weapon element and deals extra damage to enemies explicitly marked Flying."),
        ("Tiger Rampage",80,"damage",1800,"melee","tiger_rampage","Attack-based two-hit melee assault against one enemy. Carries the active Soul Weapon element and can lower both physical and magical defenses; the defense break is Extendable."),
        ("Cosmic Rave",110,"aoe_damage",2000,"melee","cosmic_rave","Hits all enemies with diminishing damage; during V-MAX targets random enemies instead. Attack is the primary influence and Agility provides a lesser secondary damage contribution."),
        # Ranged
        ("Crosshair",1,"damage",200,"ranged","crosshair","One-enemy ranged attack influenced by Attack and Critical Hit Chance. It attempts to deliver a critical hit and carries the active Soul Weapon element."),
        ("Range Fire",8,"aoe_damage",500,"ranged","range_fire","Attack-based ranged barrage against all enemies at full non-diminishing power. Carries the active Soul Weapon element."),
        ("Dispose",32,"aoe_damage",1000,"ranged","dispose","Attack-based heavy-duty laser barrage against all enemies at full non-diminishing power. Carries the active Soul Weapon element and inflicts Feedback damage on the Mec after the attack."),
        ("Satellite Linker",44,"damage",1200,"ranged","satellite_linker","Laser bits hover around one enemy and repeatedly deal minor damage for a short period. Attack and Wisdom influence damage; higher Skill Level makes the bits operate longer."),
        ("Magnify",90,"damage",1500,"ranged","magnify","One-enemy weapon-overload attack influenced by Attack and Wisdom. Wisdom magnifies damage; Skill Level and Wisdom reduce the chance of systems failure. Failure causes weapon Overheat/reboot. Requires the Mec ranged Soul Weapon role."),
        ("Shoot-All",110,"aoe_damage",2000,"ranged","shoot_all","Fires all ammunition at all enemies; V-MAX increases damage and crit."),
        # Feedback
        ("Destroy",1,"damage",200,"feedback","destroy","One-enemy Feedback attack influenced by HP, Vitality and Attack. A shield improves damage and the attack becomes stronger as HP decreases."),
        ("Robo Tackle",20,"damage",500,"feedback","robo_tackle","One-enemy tackle influenced by HP before use, Vitality and Attack. Damage falls as current HP falls; a shield improves damage. V-MAX increases both attack power and Feedback damage."),
        ("Compress",30,"damage",600,"feedback","compress","One-enemy compression attempt influenced by Vitality and HP. On success it deals a percentage of the target current HP; full HP and an equipped shield increase compression power. Skill Level increases accuracy and the attack causes Feedback."),
        ("Crush",46,"damage",1000,"feedback","crush","One-enemy Feedback attack based on the difference between maximum and current HP. Character Level limits the damage capacity, Skill Level raises the maximum possible damage, and an equipped shield increases that capacity."),
        ("Uzi Punch",95,"aoe_damage",1400,"feedback","uzi_punch","Random-enemy machinegun punch influenced by HP, Vitality and Attack. Feedback damages the Mec, a shield improves damage, and the attack becomes stronger as HP decreases."),
        ("Kamikaze Crush",110,"damage",2000,"feedback","kamikaze_crush","One-enemy lethal divebomb influenced by HP before use, Vitality and Attack. Damage falls as current HP falls; an equipped shield improves damage. V-MAX increases both attack power and Feedback damage."),
        # Magic
        ("Laser Spin",1,"aoe_damage",200,"magic","laser_spin","Magic Attack-based Dark laser assault against all enemies with diminishing damage. Source requirements: none; Properties: none."),
        ("Area Bomb",8,"aoe_damage",300,"magic","area_bomb","Magic Attack-based Fire explosion against all targeted enemies currently engaged in combat. Source Properties: none; no separate Burn status is specified."),
        ("Mec Sonata",20,"damage",1000,"magic","mec_sonata","One-enemy Magic Attack song with a chance to lower the target level-equivalent power temporarily. The level-lowering effect is Extendable."),
        ("Maelstrom",44,"aoe_damage",1500,"magic","maelstrom","Magic Attack-based Water vortex against all enemies with diminishing damage. Source Properties: none."),
        ("Shock",95,"aoe_damage",1800,"magic","shock","Magic Attack-based Lightning + Dark surge against all enemies with diminishing damage. Source Properties: none."),
        ("Starlight Shower",110,"damage",2000,"magic","starlight_shower","Magic Attack laser barrage: one enemy when fighting one target; diminishing damage to all combat targets when fighting several; V-MAX hits all enemies without diminishing."),
        # Support
        ("Cure Beam",1,"heal",100,"support","cure_beam","Single-target healing beam available from the start. Willpower and Skill Level increase healing. Support Effect increases healing and removes Blind and Poison."),
        ("Hypno Flash",16,"damage",300,"support","hypno_flash","Attempts to put one enemy to Sleep. Will and Skill Level improve accuracy and duration; the Mec support weapon improves hit chance. Sleep is Cleanseable and Extendable."),
        ("Jammer",32,"damage",750,"support","jammer","Attempts to Stop one enemy, or all enemies while the Mec support weapon is active. Will and Skill Level improve accuracy and duration; mechanical enemies are easier to affect. Stop is Cleanseable and Extendable."),
        ("Heal Beam",54,"heal",1000,"support","heal_beam","Significant Willpower-based healing. Normally heals one target; Support Effect heals the entire local party for an enhanced amount."),
        ("Logic Bomb",92,"damage",1200,"support","logic_bomb","Attempts to infect one enemy with Paralyze, Silence and Slow. With the Mec support weapon it also attempts Blind, Curse and Immobilize. Will and Skill Level improve accuracy and duration; Machine targets are easier to affect."),
        ("V-MAX",130,"boost",2000,"support","vmax","Will-influenced core overdrive: Protect, Shell, Haste, Regen, Preach, Praise, Permanence; changes several Mec skills. When it ends, Overheat is prevented while the Mec's Soul Weapon remains the active support weapon."),
        # Counter
        ("Intercept System",75,"passive",1000,"counter","intercept_system","Selected Counter that interrupts an incoming enemy attack and answers with laser-guided damage using the highest available offensive stat. Skill Level increases counter damage."),
        # Inherent
        ("Self-Repair",1,"passive",1000,"inherent","self_repair","Automatically restores Feedback self-damage after 3 owner rounds. Source also grants Auto-Regen, but no numeric Auto-Regen amount is supplied, so Soulbound does not fabricate one."),
        ("Combat Mastery",30,"passive",1000,"inherent","combat_mastery","Selected inherent. Increases ordinary Mec Soul Weapon attack damage in its pure Strength/melee role; does not work unarmed. Source: stronger than Attack UP but weaker than Two Hands."),
        ("Maxwell Program",30,"passive",1000,"inherent","maxwell_program","Augments Magic Attack and regenerates 1% of maximum MP every 6 seconds."),
        ("Shooting Mastery",30,"passive",1000,"inherent","shooting_mastery","Automatic inherent from Level 30. Soulbound uses one Soul Weapon: Shooting Mastery strengthens its Dexterity/ranged damage component without requiring a separate ranged weapon; stronger than ordinary Attack UP."),
        # Passive protocols
        ("Strength Protocol",1,"passive",2000,"passive","strength_protocol","Passively increases damage of Mec melee/Strength skills. Scales with this skill level."),
        ("Ranged Protocol",1,"passive",2000,"passive","ranged_protocol","Passively increases damage of Mec ranged/Dexterity shooting skills. Scales with this skill level."),
        ("Feedback Protocol",1,"passive",2000,"passive","feedback_protocol","Automatic protocol. Skill Level increases damage of Destroy, Robo Tackle, Uzi Punch and Kamikaze Crush."),
        ("Magic Protocol",1,"passive",2000,"passive","magic_protocol","Passively increases damage of Mec magic/Intelligence skills. Scales with this skill level."),
    ]
    if len(rows) < len(specs):
        return
    for idx,(name,unlock,kind,source_ap,branch,special,desc) in enumerate(specs):
        row=rows[idx]
        row.clear()
        row.update({
            "id":f"v0319_mec_{special}", "name":name, "aliases":[name.casefold()],
            "unlock":unlock, "kind":kind, "cooldown":0, "mana":0,
            "base_power":0,
            "source_ap_cost":source_ap,
            "source_ap_semantics":"learning_points",
            "source_ap_is_damage_power":False,
            "mec_authored":True, "mec_branch":branch,
            "mec_special":special, "desc":desc,
        })
        if branch in ("inherent","counter"):
            row["mec_role"]=branch
        if kind in ("damage","aoe_damage"):
            row["scale"] = (
                "intelligence" if branch=="magic"
                else "dexterity" if branch=="ranged"
                else "willpower" if branch=="support"
                else "strength"
            )
            row["mult"] = 1.0
            if kind=="aoe_damage": row["aoe"]=True
        if kind=="heal": row["healing_power_from_will_and_skill_level"]=True
        if special in {"strength_protocol","ranged_protocol","feedback_protocol","magic_protocol"}:
            row.update({
                "automatic":True,
                "level_effect":"increases_mapped_skill_damage",
                "protocol_multiplier_level1":1.05,
                "protocol_multiplier_level600":1.75,
                "protocol_numeric_source_defined":False,
                "protocol_balance_curve":"soulbound_1.05_to_1.75_power_0.82",
            })
        if special=="feedback_protocol":
            row.update({
                "source_level_effect_skills":[
                    "destroy","robo_tackle","uzi_punch","kamikaze_crush"
                ],
            })
        if special=="destroy":
            row.update({
                "scale":"attack",
                "secondary_scale":"constitution",
                "source_stat_influence":["hp","vitality","attack"],
                "source_properties":[],
                "target_mode":"one_enemy",
                "feedback_damage":True,
                "feedback_cost_source_defined":False,
                "shield_improves_damage":True,
                "power_increases_as_hp_decreases":True,
                "numeric_source_defined":False,
                "missing_hp_max_damage_bonus":0.50,
                "shield_damage_multiplier":1.10,
                "feedback_max_hp_pct":0.06,
                "balance_model":"soulbound_missinghp50_shield110_feedback6pct",
                "single_soul_weapon":True,
            })
        if special=="robo_tackle":
            row.update({
                "scale":"attack",
                "secondary_scale":"constitution",
                "source_stat_influence":["hp","vitality","attack"],
                "source_properties":[],
                "target_mode":"one_enemy",
                "damage_from_current_hp":True,
                "vitality_influence":True,
                "feedback_damage":True,
                "feedback_cost_source_defined":False,
                "shield_improves_damage":True,
                "vmax_power_and_feedback":True,
                "numeric_source_defined":False,
                "current_hp_power_ratio":0.12,
                "shield_damage_multiplier":1.15,
                "vmax_damage_multiplier":1.20,
                "feedback_current_hp_pct":0.10,
                "vmax_feedback_current_hp_pct":0.25,
                "balance_model":"soulbound_hp12_shield115_vmax120_feedback10_25",
                "single_soul_weapon":True,
            })
        if special=="compress":
            row.update({
                "scale":"target_current_hp_percent",
                "source_stat_influence":["vitality","hp"],
                "source_properties":[],
                "target_mode":"one_enemy",
                "percentage_target_hp_damage":True,
                "percentage_uses_current_hp":True,
                "level_effect":"increases_accuracy",
                "vitality_influence":True,
                "full_hp_increases_power":True,
                "shield_increases_compressing_power":True,
                "feedback_damage":True,
                "feedback_cost_source_defined":False,
                "numeric_source_defined":False,
                "base_accuracy":0.65,
                "skill_level_accuracy_bonus_max":0.30,
                "vitality_accuracy_bonus_anchor":0.05,
                "base_target_current_hp_pct":0.20,
                "full_hp_damage_pct_bonus":0.10,
                "shield_damage_pct_bonus":0.10,
                "vitality_damage_pct_anchor":0.05,
                "max_target_current_hp_pct":0.60,
                "feedback_max_hp_pct":0.08,
                "balance_model":"soulbound_currenthp20_fullhp10_shield10_vit5_cap60_acc65_95_feedback8",
                "single_soul_weapon":True,
            })
        if special=="uzi_punch":
            row.update({
                "scale":"attack",
                "secondary_scale":"constitution",
                "source_stat_influence":["hp","vitality","attack"],
                "source_properties":[],
                "target_mode":"random_enemies",
                "feedback_damage":True,
                "feedback_cost_source_defined":False,
                "shield_improves_damage":True,
                "power_increases_as_hp_decreases":True,
                "numeric_source_defined":False,
                "random_target_count_source_defined":False,
                "random_target_fraction":0.50,
                "missing_hp_max_damage_bonus":0.75,
                "shield_damage_multiplier":1.20,
                "feedback_max_hp_pct":0.12,
                "balance_model":"soulbound_random_half_missinghp75_shield120_feedback12pct",
                "single_soul_weapon":True,
            })
        if special=="crush":
            row.update({
                "scale":"hp_difference",
                "source_stat_influence":["hp","level"],
                "source_properties":[],
                "target_mode":"one_enemy",
                "damage_from_missing_hp":True,
                "level_caps_damage":True,
                "level_effect":"increases_maximum_possible_damage",
                "shield_increases_capacity":True,
                "feedback_damage":True,
                "feedback_cost_source_defined":False,
                "numeric_source_defined":False,
                "capacity_per_character_level":100,
                "capacity_per_skill_level":25,
                "shield_capacity_multiplier":1.25,
                "feedback_source_damage_pct":0.15,
                "balance_model":"soulbound_cap_level100_skill25_shield125_feedback15pct",
                "single_soul_weapon":True,
            })
        if special=="kamikaze_crush":
            row.update({
                "scale":"attack",
                "secondary_scale":"constitution",
                "source_stat_influence":["hp","vitality","attack"],
                "source_properties":[],
                "target_mode":"one_enemy",
                "damage_from_current_hp":True,
                "vitality_influence":True,
                "shield_improves_damage":True,
                "vmax_power_and_feedback":True,
                "numeric_source_defined":False,
                "current_hp_power_ratio":0.20,
                "shield_damage_multiplier":1.20,
                "vmax_damage_multiplier":1.30,
                "feedback_current_hp_pct":0.20,
                "vmax_feedback_current_hp_pct":0.45,
                "balance_model":"soulbound_hp20_shield120_vmax130_feedback20_45",
                "single_soul_weapon":True,
            })
        if special=="self_repair": row.update({"feedback_repair_rounds":3,"auto_regen_source_defined":True,"auto_regen_amount_source_defined":False})
        if special=="maxwell_program": row.update({"magic_attack_augmentation":True,"mp_regen_percent":1.0,"mp_regen_seconds":6.0})
        if special=="combat_mastery":
            row.update({
                "ordinary_soul_weapon_attack_only":True,
                "strength_based_only":True,
                "requires_soul_weapon":True,
                "source_weapon_types":[
                    "axe","claw","greatsword","hammer","katana",
                    "lance","rod","staff","sword"
                ],
                "does_not_work_unarmed":True,
                "stronger_than":"Attack UP",
                "weaker_than":"Two Hands",
                "numeric_source_defined":False,
                "soulbound_damage_multiplier":1.20,
                "soulbound_weapon_model":"mec_soul_weapon_melee_strength_role",
                "balance_model":"soulbound_x1.20_relative_between_attack_up_and_two_hands",
                "single_soul_weapon":True,
            })
        if special=="hammer_crush":
            row.update({
                "scale":"attack",
                "source_stat_influence":["attack"],
                "source_properties":["carries_elements"],
                "target_mode":"one_enemy",
                "attack_influence":True,
                "carries_soul_weapon_elements":True,
                "requires_soul_weapon":"melee",
                "single_soul_weapon":True,
            })
        if special=="cosmic_rave": row.update({"aoe_diminishing":True,"vmax_random_enemies":True,"agility_secondary_influence":True,"carries_soul_weapon_elements":True,"single_soul_weapon":True})
        if special=="plural_slash":
            row.update({
                "scale":"attack",
                "secondary_scale":"dexterity",
                "source_stat_influence":["attack","agility"],
                "source_properties":["carries_elements"],
                "target_mode":"one_enemy",
                "multi_slash":True,
                "multi_hit_count_source_defined":False,
                "agility_secondary_influence":True,
                "secondary_numeric_weight_source_defined":False,
                "carries_soul_weapon_elements":True,
                "requires_soul_weapon":"melee",
                "single_soul_weapon":True,
                "balance_model":"attack_primary_plus_global_secondary_dex35pct",
            })
        if special=="shock_soldier":
            row.update({
                "scale":"attack",
                "source_stat_influence":["attack"],
                "source_properties":["carries_elements"],
                "target_mode":"all_enemies_diminishing",
                "aoe_diminishing":True,
                "diminishing_numeric_source_defined":False,
                "soulbound_diminishing_model":"inverse_sqrt_target_count",
                "carries_soul_weapon_elements":True,
                "requires_soul_weapon":"melee",
                "single_soul_weapon":True,
            })
        if special=="range_fire":
            row.update({
                "scale":"attack",
                "source_stat_influence":["attack"],
                "source_properties":["carries_elements"],
                "target_mode":"all_enemies_non_diminishing",
                "aoe_non_diminishing":True,
                "carries_soul_weapon_elements":True,
                "requires_soul_weapon":"ranged",
                "single_soul_weapon":True,
            })
        if special=="dispose":
            row.update({
                "scale":"attack",
                "source_stat_influence":["attack"],
                "source_properties":["carries_elements"],
                "target_mode":"all_enemies_non_diminishing",
                "aoe_non_diminishing":True,
                "carries_soul_weapon_elements":True,
                "requires_soul_weapon":"ranged",
                "feedback_damage":True,
                "feedback_cost_source_defined":False,
                "soulbound_feedback_max_hp_pct":0.08,
                "feedback_once_per_cast":True,
                "feedback_repair_eligible":True,
                "single_soul_weapon":True,
                "balance_model":"soulbound_feedback_8pct_maxhp_once_per_cast",
            })
        if special=="crosshair":
            row.update({
                "scale":"attack",
                "source_stat_influence":["attack","critical_hit_chance"],
                "source_properties":["carries_elements"],
                "target_mode":"one_enemy",
                "critical_chance_influence":True,
                "attempts_critical":True,
                "critical_model":"character_critical_hit_chance",
                "carries_soul_weapon_elements":True,
                "requires_soul_weapon":"ranged",
                "single_soul_weapon":True,
            })
        if special=="magnify":
            row.update({
                "scale":"attack",
                "secondary_scale":"intelligence",
                "source_stat_influence":["attack","wisdom"],
                "source_properties":["cooldown"],
                "target_mode":"one_enemy",
                "wisdom_magnifies_damage":True,
                "skill_level_reduces_system_failure":True,
                "wisdom_reduces_system_failure":True,
                "systems_failure_causes_overheat_reboot":True,
                "requires_soul_weapon":"ranged",
                "single_soul_weapon":True,
                "mechanic_cooldown":True,
                "numeric_cooldown_source_defined":False,
                "systems_failure_numeric_source_defined":False,
                "soulbound_failure_base_chance":0.35,
                "soulbound_skill_failure_reduction_max":0.20,
                "soulbound_wisdom_failure_reduction_anchor":0.06,
                "soulbound_wisdom_failure_reduction_max":0.12,
                "soulbound_failure_chance_floor":0.02,
                "soulbound_reboot_recovery_actions":1,
                "balance_model":"soulbound_failure35_skillminus20_wisminus12_floor2_one_recovery_action",
            })
        if special=="satellite_linker":
            row.update({
                "scale":"attack",
                "secondary_scale":"intelligence",
                "source_stat_influence":["attack","wisdom"],
                "source_properties":[],
                "target_mode":"one_enemy",
                "periodic_damage":True,
                "minor_damage_over_time":True,
                "wisdom_increases_damage":True,
                "level_effect":"increases_duration",
                "duration_source_defined":False,
                "tick_cadence_source_defined":False,
                "tick_damage_source_defined":False,
                "soulbound_tick_every_owner_rounds":1,
                "soulbound_duration_rounds_level1":3,
                "soulbound_duration_rounds_level600":8,
                "soulbound_tick_damage_multiplier":0.20,
                "soulbound_single_active_link":True,
                "balance_model":"soulbound_tick20pct_every_round_duration3_to_8",
                "single_soul_weapon":True,
            })
        if special=="shoot_all":
            row.update({
                "scale":"attack",
                "source_stat_influence":["attack","critical_hit_chance"],
                "target_mode":"all_enemies_non_diminishing",
                "aoe_non_diminishing":True,
                "critical_chance_influence":True,
                "attempts_critical":True,
                "vmax_increases_critical_and_damage":True,
                "vmax_numeric_source_defined":False,
                "vmax_damage_multiplier":1.25,
                "vmax_critical_chance_bonus":0.15,
                "vmax_balance_model":"soulbound_damage_x1.25_crit_plus15pp",
                "carries_soul_weapon_elements":True,
                "requires_soul_weapon":"ranged",
                "single_soul_weapon":True,
            })
        if special=="laser_spin":
            row.update({
                "scale":"intelligence",
                "source_stat_influence":["magic_attack"],
                "magic_attack_influence":True,
                "source_properties":[],
                "source_requirements":[],
                "source_requires_none":True,
                "target_mode":"all_enemies_diminishing",
                "aoe_diminishing":True,
                "element":"dark",
                "uoss_mp_cost":25,
            })
        if special=="mec_sonata":
            row.update({
                "scale":"intelligence",
                "source_stat_influence":["magic_attack"],
                "magic_attack_influence":True,
                "uoss_mp_cost":50,
                "source_properties":["extendable"],
                "target_mode":"one_enemy",
                "soulbound_target_scope":"enemy_only",
                "soulbound_harmful_debuff":True,
                "enemy_debuffs":["level_equivalent_power_down"],
                "temporary_level_reduction_chance":True,
                "level_reduction_extendable":True,
                "level_reduction_numeric_source_defined":False,
                "level_reduction_duration_source_defined":False,
                "level_reduction_chance_source_defined":False,
                "soulbound_level_reduction_proc_chance":0.30,
                "soulbound_level_equivalent_power_multiplier":0.90,
                "soulbound_level_reduction_rounds":3,
                "balance_model":"soulbound_proc30_levelpower90_3rounds_extendable",
            })
        if special=="maelstrom":
            row.update({
                "scale":"intelligence",
                "source_stat_influence":["magic_attack"],
                "magic_attack_influence":True,
                "source_properties":[],
                "source_requirement_level":44,
                "source_requirement_maps_to":"class_mastery",
                "target_mode":"all_enemies_diminishing",
                "aoe_diminishing":True,
                "diminishing_numeric_source_defined":False,
                "soulbound_diminishing_model":"inverse_sqrt_target_count",
                "element":"water",
                "uoss_mp_cost":80,
            })
        if special=="shock":
            row.update({
                "scale":"intelligence",
                "source_stat_influence":["magic_attack"],
                "magic_attack_influence":True,
                "source_properties":[],
                "source_requirement_level":95,
                "source_requirement_maps_to":"class_mastery",
                "target_mode":"all_enemies_diminishing",
                "aoe_diminishing":True,
                "diminishing_numeric_source_defined":False,
                "soulbound_diminishing_model":"inverse_sqrt_target_count",
                "elements":["lightning","dark"],
                "uoss_mp_cost":150,
            })
        if special=="tiger_rampage":
            row.update({
                "scale":"attack",
                "source_stat_influence":["attack"],
                "source_properties":["carries_elements","extendable"],
                "hits":2,
                "target_mode":"one_enemy",
                "soulbound_target_scope":"enemy_only",
                "soulbound_harmful_debuff":True,
                "enemy_debuffs":["physical_defense_down","magic_defense_down"],
                "carries_soul_weapon_elements":True,
                "requires_soul_weapon":"melee",
                "single_soul_weapon":True,
                "extendable":True,
                "defense_break_physical":True,
                "defense_break_magical":True,
                "defense_break_chance_source_defined":False,
                "defense_break_duration_source_defined":False,
                "defense_break_amount_source_defined":False,
                "soulbound_defense_break_proc_chance":0.35,
                "soulbound_defense_break_rounds":4,
                "soulbound_defense_break_damage_multiplier":1.15,
                "balance_model":"soulbound_proc35_break4_incoming_damage_x1.15_extendable",
            })
        if special=="area_bomb":
            row.update({
                "scale":"intelligence",
                "source_stat_influence":["magic_attack"],
                "magic_attack_influence":True,
                "source_properties":[],
                "source_requirement_level":8,
                "source_requirement_maps_to":"class_mastery",
                "target_mode":"all_targetted_enemies",
                "engaged_only":True,
                "aoe_diminishing":False,
                "element":"fire",
                "uoss_mp_cost":35,
                "burn_status_source_defined":False,
            })
        if special=="pop_knight":
            row.update({
                "scale":"attack",
                "source_stat_influence":["attack"],
                "source_properties":["carries_elements"],
                "target_mode":"all_enemies_non_diminishing",
                "aoe_non_diminishing":True,
                "carries_soul_weapon_elements":True,
                "requires_soul_weapon":"melee",
                "bonus_vs_flying":True,
                "flying_template_flag":"flying",
                "bonus_vs_flying_source_defined":True,
                "flying_bonus_numeric_source_defined":False,
                "soulbound_flying_damage_multiplier":1.25,
                "single_soul_weapon":True,
                "balance_model":"soulbound_flying_x1.25",
            })
        if special=="hypno_flash":
            row.update({
                "scale":"willpower",
                "source_stat_influence":["will"],
                "uoss_mp_cost":15,
                "source_properties":["cleanseable","extendable"],
                "target_mode":"one_enemy",
                "soulbound_target_scope":"enemy_only",
                "soulbound_harmful_debuff":True,
                "enemy_debuffs":["sleep"],
                "control_effect":"sleep",
                "level_effect":"increases_accuracy_and_duration",
                "support_weapon_improves_accuracy":True,
                "cleanseable":True,
                "extendable":True,
                "accuracy_numeric_source_defined":False,
                "duration_numeric_source_defined":False,
                "soulbound_base_accuracy":0.55,
                "soulbound_skill_accuracy_bonus_max":0.25,
                "soulbound_will_accuracy_bonus_max":0.15,
                "soulbound_support_accuracy_bonus":0.10,
                "soulbound_accuracy_cap":0.98,
                "soulbound_duration_rounds_level1":2,
                "soulbound_duration_rounds_level600":6,
                "soulbound_will_duration_bonus_max":2,
                "balance_model":"soulbound_acc55_skill25_will15_support10_cap98_duration2_to_6_plus_will2",
            })
        if special=="heal_beam":
            row.update({
                "scale":"willpower",
                "source_stat_influence":["will"],
                "source_properties":[],
                "source_requirement_level":54,
                "source_requirement_maps_to":"class_mastery",
                "source_target_mode":["one_target","party"],
                "uoss_mp_cost":36,
                "uoss_support_mp_cost":72,
                "target_mode":"one_ally_or_support_party",
                "soulbound_enemy_heal_disabled":True,
                "level_effect":"increases_healing_power",
                "heal_pct":0.50,
                "healing_numeric_source_defined":False,
                "support_weapon_expands_to_party":True,
                "support_heal_multiplier":1.20,
                "support_heal_numeric_source_defined":False,
                "support_effect_requires_support_weapon":True,
                "healing_balance_model":"uncapped_will_skill_eq",
            })
        if special=="cure_beam":
            row.update({
                "scale":"willpower",
                "source_stat_influence":["will"],
                "source_properties":[],
                "source_requirements":[],
                "source_requires_none":True,
                "uoss_mp_cost":10,
                "source_target_mode":["self","one_ally","one_enemy"],
                "target_mode":"self_or_one_ally",
                "soulbound_enemy_heal_disabled":True,
                "level_effect":"increases_healing_power",
                "heal_pct":0.30,
                "healing_numeric_source_defined":False,
                "support_heal_multiplier":1.20,
                "support_heal_numeric_source_defined":False,
                "support_cleanses":["blind","poison"],
                "support_effect_requires_support_weapon":True,
                "healing_balance_model":"uncapped_will_skill_eq",
            })
        if special=="jammer":
            row.update({
                "scale":"willpower",
                "source_stat_influence":["will"],
                "control_effect":"stop",
                "source_properties":["cleanseable","extendable"],
                "cleanseable":True,
                "extendable":True,
                "uoss_mp_cost":20,
                "uoss_support_mp_cost":40,
                "target_mode":"one_or_support_all_enemies",
                "soulbound_target_scope":"enemy_only",
                "soulbound_harmful_debuff":True,
                "enemy_debuffs":["stop"],
                "support_weapon_expands_to_all_enemies":True,
                "machine_accuracy_bonus":True,
                "level_effect":"increases_accuracy_and_duration",
                "accuracy_numeric_source_defined":False,
                "duration_numeric_source_defined":False,
                "machine_bonus_numeric_source_defined":False,
                "soulbound_base_accuracy":0.50,
                "soulbound_skill_accuracy_bonus_max":0.25,
                "soulbound_will_accuracy_bonus_max":0.15,
                "soulbound_machine_accuracy_bonus":0.15,
                "soulbound_accuracy_cap":0.98,
                "soulbound_duration_rounds_level1":8,
                "soulbound_duration_rounds_level600":16,
                "soulbound_will_duration_bonus_max":4,
                "duration_user_benchmark":{"skill_level":9,"observed_actions":8},
                "balance_model":"user_anchor_skill9_about8_then_soulbound_8_to_16_plus_will4",
            })
        if special=="logic_bomb":
            row.update({
                "scale":"willpower",
                "source_stat_influence":["will"],
                "uoss_mp_cost":155,
                "source_properties":["cleanseable","extendable"],
                "target_mode":"one_enemy",
                "soulbound_target_scope":"enemy_only",
                "soulbound_harmful_debuff":True,
                "enemy_debuffs":[
                    "paralyze","silence","slow","blind",
                    "curse_damage_down","immobilize"
                ],
                "control_effects":["paralyze","silence","slow"],
                "support_weapon_extra_effects":["blind","curse","immobilize"],
                "support_weapon_adds_extra_effects":True,
                "machine_accuracy_bonus":True,
                "level_effect":"increases_accuracy_and_duration",
                "cleanseable":True,
                "extendable":True,
                "accuracy_numeric_source_defined":False,
                "duration_numeric_source_defined":False,
                "machine_bonus_numeric_source_defined":False,
                "status_numeric_source_defined":False,
                "soulbound_base_accuracy":0.45,
                "soulbound_skill_accuracy_bonus_max":0.30,
                "soulbound_will_accuracy_bonus_max":0.15,
                "soulbound_machine_accuracy_bonus":0.15,
                "soulbound_accuracy_cap":0.98,
                "soulbound_duration_rounds_level1":3,
                "soulbound_duration_rounds_level600":10,
                "soulbound_will_duration_bonus_max":2,
                "soulbound_paralyze_skip_chance":0.50,
                "soulbound_slow_skip_every_actions":2,
                "soulbound_blind_miss_chance":0.35,
                "soulbound_curse_damage_multiplier":0.80,
                "balance_model":"soulbound_acc45_skill30_will15_machine15_duration3_to_10_statuses",
            })
        if special=="starlight_shower":
            row.update({
                "scale":"intelligence",
                "source_stat_influence":["magic_attack"],
                "magic_attack_influence":True,
                "uoss_mp_cost":225,
                "uoss_vmax_mp_cost":300,
                "source_properties":[],
                "target_mode":"single_or_diminishing_aoe",
                "aoe_diminishing":True,
                "vmax_target_mode":"all_enemies_non_diminishing",
                "vmax_aoe_non_diminishing":True,
                "diminishing_numeric_source_defined":False,
                "diminishing_balance_model":"soulbound_inverse_sqrt_target_count",
            })
        if special=="cosmic_rave":
            row.update({"scale":"attack", "secondary_scale":"dexterity",
                        "source_stat_influence":["attack","agility"],
                        "secondary_scale_weight":"lesser",
                        "carries_soul_weapon_elements":True, "requires_soul_weapon":"melee",
                        "target_mode":"diminishing_aoe_or_vmax_random",
                        "vmax_random_hits":5,
                        "vmax_random_hits_evidence":"user_uoss_combat_log"})
        if special=="intercept_system":
            row.update({
                "source_stat_influence":["variable"],
                "source_properties":[],
                "usage_mode":"job_set_counter",
                "interrupts_incoming_attack":True,
                "counter_damage":True,
                "highest_offensive_stat":True,
                "offensive_stat_candidates":[
                    "strength","dexterity","intelligence","willpower"
                ],
                "level_effect":"increases_damage",
                "numeric_damage_curve_source_defined":False,
                "skill_level_damage_curve":"global_soulbound_skill_power_1_to_600",
                "counter_trigger_chance_source_defined":False,
                "counter_trigger_model":"selected_counter_interrupts_incoming_attack",
            })
        if special=="vmax":
            row.update({"scale":"willpower","source_stat_influence":["will"],
                        "boost":1.0,"cooldown":0,"mechanic_cooldown":True,
                        "duration_scales_with_skill_level":True,
                        "duration_scales_with_will":True,
                        "duration_balance_model":"soulbound_200_to_600_plus_uncapped_will",
                        "support_weapon_model":"mec_soul_weapon",
                        "vmax_status_sources":{
                            "praise":{"effect":"attack_power_up","numeric_source_defined":False},
                            "preach":{"effect":"magic_attack_up","numeric_source_defined":False,
                                      "source_stat_influence":["will"],
                                      "level_effect":"increases_duration"},
                            "protect":{"effect":"incoming_physical_damage_down",
                                       "numeric_source_defined":False,
                                       "source_stat_influence":["will"],
                                       "level_effect":"increases_duration",
                                       "properties":["dispelable","extendable","silenceable"]},
                            "shell":{"effect":"incoming_magic_damage_down",
                                     "numeric_source_defined":False,
                                     "source_stat_influence":["will"],
                                     "level_effect":"increases_duration",
                                     "properties":["dispelable","extendable","silenceable"]},
                            "regen":{"effect":"periodic_small_hp_heal",
                                     "numeric_source_defined":False,
                                     "source_stat_influence":["will"],
                                     "level_effect":"increases_duration",
                                     "tick_cadence_source_defined":False,
                                     "heal_amount_source_defined":False,
                                     "soulbound_tick_every_rounds":3,
                                     "soulbound_heal_model":"small_will_scaled_periodic_heal",
                                     "duration_source":"vmax_timer",
                                     "properties":["dispelable","extendable","reflectable","silenceable"]}
                        }})
    CLASS_SKILLS["Mec"] = rows

_v0319_install_full_mec_kit()

# v1.11.49: canonical Mec contract adapted to Soulbound's one-Soul-Weapon model.
MEC_CANONICAL_CONTRACT_V11149 = {
    "prerequisite_race": "Cyborg",
    "weapon_model": "single_soul_weapon",
    "armor": "all",
    "branches": {
        "melee": {"primary": "strength", "secondary": "dexterity", "protocol": "v0319_mec_strength_protocol"},
        "ranged": {"primary": "dexterity", "secondary": "willpower", "protocol": "v0319_mec_ranged_protocol"},
        "feedback": {"resource": "hp", "defensive_stat": "vitality", "protocol": "v0319_mec_feedback_protocol"},
        "magic": {"primary": "intelligence", "secondary": "willpower", "protocol": "v0319_mec_magic_protocol"},
        "support": {"primary": "willpower", "support_effect": "mec_soul_weapon", "support_weapon": "soul_weapon"},
    },
}
MEC_PROTOCOL_SKILLS_V11155 = {
    "v0319_mec_strength_protocol": (
        "hammer_crush","shock_soldier","plural_slash","pop_knight","tiger_rampage","cosmic_rave",
    ),
    "v0319_mec_ranged_protocol": (
        "crosshair","range_fire","dispose","satellite_linker","magnify","shoot_all",
    ),
    "v0319_mec_feedback_protocol": (
        "destroy","robo_tackle","uzi_punch","kamikaze_crush",
    ),
    "v0319_mec_magic_protocol": (
        "laser_spin","area_bomb","mec_sonata","maelstrom","shock","starlight_shower",
    ),
}

_MEC_EXPECTED_V11149 = {
    "hammer_crush":(1,"melee"),"shock_soldier":(14,"melee"),"plural_slash":(32,"melee"),
    "pop_knight":(46,"melee"),"tiger_rampage":(80,"melee"),"cosmic_rave":(110,"melee"),
    "crosshair":(1,"ranged"),"range_fire":(8,"ranged"),"dispose":(32,"ranged"),
    "satellite_linker":(44,"ranged"),"magnify":(90,"ranged"),"shoot_all":(110,"ranged"),
    "destroy":(1,"feedback"),"robo_tackle":(20,"feedback"),"compress":(30,"feedback"),
    "crush":(46,"feedback"),"uzi_punch":(95,"feedback"),"kamikaze_crush":(110,"feedback"),
    "laser_spin":(1,"magic"),"area_bomb":(8,"magic"),"mec_sonata":(20,"magic"),
    "maelstrom":(44,"magic"),"shock":(95,"magic"),"starlight_shower":(110,"magic"),
    "cure_beam":(1,"support"),"hypno_flash":(16,"support"),"jammer":(32,"support"),
    "heal_beam":(54,"support"),"logic_bomb":(92,"support"),"vmax":(130,"support"),
    "intercept_system":(75,"counter"),"self_repair":(1,"inherent"),"combat_mastery":(30,"inherent"),
    "maxwell_program":(30,"inherent"),"shooting_mastery":(30,"inherent"),
    "strength_protocol":(1,"passive"),"ranged_protocol":(1,"passive"),
    "feedback_protocol":(1,"passive"),"magic_protocol":(1,"passive"),
}
def _mec_contract_audit_v11149():
    rows={s.get("mec_special"):s for s in CLASS_SKILLS.get("Mec",[]) if s.get("mec_special")}
    errors=[]
    protocol_by_special={
        special:protocol_id
        for protocol_id,specials in MEC_PROTOCOL_SKILLS_V11155.items()
        for special in specials
    }
    source_mp_costs={
        "laser_spin":25,"area_bomb":35,"mec_sonata":50,"maelstrom":80,
        "shock":150,"starlight_shower":225,"cure_beam":10,"hypno_flash":15,
        "jammer":20,"heal_beam":36,"logic_bomb":155,
    }
    source_support_mp_costs={"jammer":40,"heal_beam":72}
    for _sid,_row in rows.items():
        if str(_row.get("source_ap_semantics",""))!="learning_points":
            errors.append(f"{_sid}: source AP must mean learning points")
        if bool(_row.get("source_ap_is_damage_power")):
            errors.append(f"{_sid}: source AP cannot be damage power")
        if "source_ap_cost" in _row and int(_row.get("base_power",0) or 0)!=0:
            errors.append(f"{_sid}: authored Mec base_power must not be sourced from AP")

    feedback_protocol=rows.get("feedback_protocol")
    if feedback_protocol:
        _feedback_expected=["destroy","robo_tackle","uzi_punch","kamikaze_crush"]
        if not bool(feedback_protocol.get("automatic")):
            errors.append("feedback_protocol: must be Automatic")
        if str(feedback_protocol.get("level_effect"))!="increases_mapped_skill_damage":
            errors.append("feedback_protocol: Level Effect must increase mapped skill damage")
        if list(feedback_protocol.get("source_level_effect_skills") or [])!=_feedback_expected:
            errors.append("feedback_protocol: source skill list mismatch")
        if list(MEC_PROTOCOL_SKILLS_V11155.get("v0319_mec_feedback_protocol") or ())!=_feedback_expected:
            errors.append("feedback_protocol: runtime mapping must exclude Compress and Crush")
        if bool(feedback_protocol.get("protocol_numeric_source_defined")):
            errors.append("feedback_protocol: numeric curve must remain marked unsourced")

    heal_beam=rows.get("heal_beam")
    if heal_beam:
        if int(heal_beam.get("unlock",0) or 0)!=54:
            errors.append("heal_beam: source Level 54 must map to Biegłość Mec 54")
        if int(heal_beam.get("source_ap_cost",0) or 0)!=1000:
            errors.append("heal_beam: source Base AP cost must remain 1000 learning points")
        if str(heal_beam.get("source_ap_semantics",""))!="learning_points":
            errors.append("heal_beam: AP must remain learning points")
        if int(heal_beam.get("source_requirement_level",0) or 0)!=54:
            errors.append("heal_beam: source requirement must remain Level 54")
        if str(heal_beam.get("source_requirement_maps_to"))!="class_mastery":
            errors.append("heal_beam: source Level must map to class mastery")
        if list(heal_beam.get("source_stat_influence") or [])!=["will"]:
            errors.append("heal_beam: source influence must be Will only")
        if list(heal_beam.get("source_properties") or [])!=[]:
            errors.append("heal_beam: source Properties must be None")
        if list(heal_beam.get("source_target_mode") or [])!=["one_target","party"]:
            errors.append("heal_beam: source target must remain One Target or Party")
        if str(heal_beam.get("target_mode"))!="one_ally_or_support_party":
            errors.append("heal_beam: Soulbound target mode must be one ally or support party")
        if not bool(heal_beam.get("soulbound_enemy_heal_disabled")):
            errors.append("heal_beam: healing combat enemies must remain disabled")
        if int(heal_beam.get("uoss_mp_cost",0) or 0)!=36:
            errors.append("heal_beam: normal MP cost must remain 36")
        if int(heal_beam.get("uoss_support_mp_cost",0) or 0)!=72:
            errors.append("heal_beam: support MP cost must remain 72")
        if str(heal_beam.get("level_effect"))!="increases_healing_power":
            errors.append("heal_beam: Level Effect must increase Healing Power")
        if not bool(heal_beam.get("support_weapon_expands_to_party")):
            errors.append("heal_beam: Support Effect must expand healing to party")

    cure_beam=rows.get("cure_beam")
    if cure_beam:
        if int(cure_beam.get("unlock",0) or 0)!=1:
            errors.append("cure_beam: Reqs None must map to Biegłość Mec 1")
        if int(cure_beam.get("source_ap_cost",0) or 0)!=100:
            errors.append("cure_beam: source Base AP cost must remain 100 learning points")
        if str(cure_beam.get("source_ap_semantics",""))!="learning_points":
            errors.append("cure_beam: AP must remain learning points")
        if list(cure_beam.get("source_requirements") or [])!=[] or not bool(cure_beam.get("source_requires_none")):
            errors.append("cure_beam: source requirements must be None")
        if list(cure_beam.get("source_stat_influence") or [])!=["will"]:
            errors.append("cure_beam: source influence must be Will only")
        if list(cure_beam.get("source_properties") or [])!=[]:
            errors.append("cure_beam: source Properties must be None")
        if list(cure_beam.get("source_target_mode") or [])!=["self","one_ally","one_enemy"]:
            errors.append("cure_beam: source target card must remain Self/One Ally/One Enemy")
        if str(cure_beam.get("target_mode"))!="self_or_one_ally":
            errors.append("cure_beam: Soulbound target mode must be self or one ally")
        if not bool(cure_beam.get("soulbound_enemy_heal_disabled")):
            errors.append("cure_beam: healing combat enemies must remain disabled")
        if str(cure_beam.get("level_effect"))!="increases_healing_power":
            errors.append("cure_beam: Level Effect must increase Healing Power")
        if list(cure_beam.get("support_cleanses") or [])!=["blind","poison"]:
            errors.append("cure_beam: Support Effect must cleanse Blind and Poison")

    shock=rows.get("shock")
    if shock:
        if int(shock.get("unlock",0) or 0)!=95:
            errors.append("shock: source Level 95 must map to Biegłość Mec 95")
        if int(shock.get("source_ap_cost",0) or 0)!=1800:
            errors.append("shock: source Base AP cost must remain 1800 metadata")
        if bool(shock.get("source_ap_is_damage_power")) or int(shock.get("base_power",0) or 0)!=0:
            errors.append("shock: source AP must not be used as combat base power")
        if int(shock.get("source_requirement_level",0) or 0)!=95:
            errors.append("shock: source requirement must remain Level 95")
        if str(shock.get("source_requirement_maps_to"))!="class_mastery":
            errors.append("shock: source Level must map to class mastery")
        if list(shock.get("source_stat_influence") or [])!=["magic_attack"]:
            errors.append("shock: source influence must be Magic Attack only")
        if list(shock.get("source_properties") or [])!=[]:
            errors.append("shock: source Properties must be None")
        if str(shock.get("target_mode"))!="all_enemies_diminishing":
            errors.append("shock: target mode must be All Enemies (Diminishing)")
        if not bool(shock.get("aoe_diminishing")):
            errors.append("shock: diminishing flag missing")
        if bool(shock.get("diminishing_numeric_source_defined")):
            errors.append("shock: numeric diminishing curve must remain marked unsourced")
        if str(shock.get("soulbound_diminishing_model"))!="inverse_sqrt_target_count":
            errors.append("shock: Soulbound diminishing model mismatch")
        if list(shock.get("elements") or [])!=["lightning","dark"]:
            errors.append("shock: elements must be Lightning + Dark")

    maelstrom=rows.get("maelstrom")
    if maelstrom:
        if int(maelstrom.get("unlock",0) or 0)!=44:
            errors.append("maelstrom: source Level 44 must map to Biegłość Mec 44")
        if int(maelstrom.get("source_ap_cost",0) or 0)!=1500:
            errors.append("maelstrom: source Base AP cost must remain 1500 metadata")
        if bool(maelstrom.get("source_ap_is_damage_power")) or int(maelstrom.get("base_power",0) or 0)!=0:
            errors.append("maelstrom: source AP must not be used as combat base power")
        if int(maelstrom.get("source_requirement_level",0) or 0)!=44:
            errors.append("maelstrom: source requirement must remain Level 44")
        if str(maelstrom.get("source_requirement_maps_to"))!="class_mastery":
            errors.append("maelstrom: source Level must map to class mastery")
        if list(maelstrom.get("source_stat_influence") or [])!=["magic_attack"]:
            errors.append("maelstrom: source influence must be Magic Attack only")
        if list(maelstrom.get("source_properties") or [])!=[]:
            errors.append("maelstrom: source Properties must be None")
        if str(maelstrom.get("target_mode"))!="all_enemies_diminishing":
            errors.append("maelstrom: target mode must be All Enemies (Diminishing)")
        if not bool(maelstrom.get("aoe_diminishing")):
            errors.append("maelstrom: diminishing flag missing")
        if bool(maelstrom.get("diminishing_numeric_source_defined")):
            errors.append("maelstrom: numeric diminishing curve must remain marked unsourced")
        if str(maelstrom.get("soulbound_diminishing_model"))!="inverse_sqrt_target_count":
            errors.append("maelstrom: Soulbound diminishing model mismatch")
        if str(maelstrom.get("element","")).casefold()!="water":
            errors.append("maelstrom: element must be Water")

    area_bomb=rows.get("area_bomb")
    if area_bomb:
        if int(area_bomb.get("unlock",0) or 0)!=8:
            errors.append("area_bomb: source Level 8 must map to Biegłość Mec 8")
        if int(area_bomb.get("source_ap_cost",0) or 0)!=300:
            errors.append("area_bomb: source Base AP cost must remain 300 metadata")
        if bool(area_bomb.get("source_ap_is_damage_power")) or int(area_bomb.get("base_power",0) or 0)!=0:
            errors.append("area_bomb: source AP must not be used as combat base power")
        if int(area_bomb.get("source_requirement_level",0) or 0)!=8:
            errors.append("area_bomb: source requirement must remain Level 8")
        if str(area_bomb.get("source_requirement_maps_to"))!="class_mastery":
            errors.append("area_bomb: source Level must map to class mastery")
        if list(area_bomb.get("source_stat_influence") or [])!=["magic_attack"]:
            errors.append("area_bomb: source influence must be Magic Attack only")
        if list(area_bomb.get("source_properties") or [])!=[]:
            errors.append("area_bomb: source Properties must be None")
        if str(area_bomb.get("target_mode"))!="all_targetted_enemies":
            errors.append("area_bomb: target mode must be All Targetted Enemies")
        if not bool(area_bomb.get("engaged_only")):
            errors.append("area_bomb: must hit engaged targets only")
        if bool(area_bomb.get("aoe_diminishing")):
            errors.append("area_bomb: source does not mark this attack Diminishing")
        if str(area_bomb.get("element","")).casefold()!="fire":
            errors.append("area_bomb: element must be Fire")
        if bool(area_bomb.get("burn_status_source_defined")):
            errors.append("area_bomb: no separate Burn status may be invented")

    laser_spin=rows.get("laser_spin")
    if laser_spin:
        if int(laser_spin.get("unlock",0) or 0)!=1:
            errors.append("laser_spin: Reqs None must map to Biegłość Mec 1")
        if int(laser_spin.get("source_ap_cost",0) or 0)!=200:
            errors.append("laser_spin: source Base AP cost must remain 200 metadata")
        if bool(laser_spin.get("source_ap_is_damage_power")) or int(laser_spin.get("base_power",0) or 0)!=0:
            errors.append("laser_spin: source AP must not be used as combat base power")
        if list(laser_spin.get("source_requirements") or [])!=[] or not bool(laser_spin.get("source_requires_none")):
            errors.append("laser_spin: source requirements must be None")
        if list(laser_spin.get("source_stat_influence") or [])!=["magic_attack"]:
            errors.append("laser_spin: source influence must be Magic Attack only")
        if list(laser_spin.get("source_properties") or [])!=[]:
            errors.append("laser_spin: source Properties must be None")
        if str(laser_spin.get("target_mode"))!="all_enemies_diminishing":
            errors.append("laser_spin: target mode must be All Enemies (Diminishing)")
        if not bool(laser_spin.get("aoe_diminishing")):
            errors.append("laser_spin: diminishing flag missing")
        if str(laser_spin.get("element","")).casefold()!="dark":
            errors.append("laser_spin: element must be Dark")

    cosmic=rows.get("cosmic_rave")
    if cosmic:
        if str(cosmic.get("scale"))!="attack":
            errors.append(f"cosmic_rave:scale={cosmic.get('scale')} expected=attack")
        if str(cosmic.get("secondary_scale"))!="dexterity":
            errors.append(
                f"cosmic_rave:secondary={cosmic.get('secondary_scale')} expected=dexterity"
            )
        if int(cosmic.get("vmax_random_hits",0) or 0)!=5:
            errors.append(
                f"cosmic_rave:vmax_random_hits={cosmic.get('vmax_random_hits')} expected=5"
            )
    intercept=rows.get("intercept_system")
    if intercept:
        if list(intercept.get("source_stat_influence") or [])!=["variable"]:
            errors.append("intercept_system: source influence must be Variable")
        if list(intercept.get("source_properties") or [])!=[]:
            errors.append("intercept_system: source Properties must be None")
        if str(intercept.get("usage_mode"))!="job_set_counter":
            errors.append("intercept_system: must use job set counter")
        if not bool(intercept.get("interrupts_incoming_attack")):
            errors.append("intercept_system: must interrupt incoming attack")
        if not bool(intercept.get("highest_offensive_stat")):
            errors.append("intercept_system: must use highest offensive stat")
        if list(intercept.get("offensive_stat_candidates") or [])!=[
            "strength","dexterity","intelligence","willpower"
        ]:
            errors.append("intercept_system: offensive stat candidates mismatch")
        if str(intercept.get("level_effect"))!="increases_damage":
            errors.append("intercept_system: Skill Level must increase Damage")
        if bool(intercept.get("numeric_damage_curve_source_defined")):
            errors.append("intercept_system: numeric Skill Level curve must remain marked unsourced")
        if bool(intercept.get("counter_trigger_chance_source_defined")):
            errors.append("intercept_system: no source trigger chance may be invented")

    tiger_rampage=rows.get("tiger_rampage")
    if tiger_rampage:
        if str(tiger_rampage.get("scale"))!="attack":
            errors.append("tiger_rampage: primary scale must be Attack")
        if list(tiger_rampage.get("source_stat_influence") or [])!=["attack"]:
            errors.append("tiger_rampage: source influence must be Attack")
        if list(tiger_rampage.get("source_properties") or [])!=["carries_elements","extendable"]:
            errors.append("tiger_rampage: source Properties must be Carries Elements + Extendable")
        if int(tiger_rampage.get("hits",0) or 0)!=2:
            errors.append("tiger_rampage: source requires exactly two heavy blows")
        if str(tiger_rampage.get("target_mode"))!="one_enemy":
            errors.append("tiger_rampage: target mode must be One Enemy")
        if not bool(tiger_rampage.get("defense_break_physical")):
            errors.append("tiger_rampage: physical defense break missing")
        if not bool(tiger_rampage.get("defense_break_magical")):
            errors.append("tiger_rampage: magical defense break missing")
        if not bool(tiger_rampage.get("extendable")):
            errors.append("tiger_rampage: defense break must be Extendable")
        if bool(tiger_rampage.get("defense_break_chance_source_defined")):
            errors.append("tiger_rampage: proc chance must remain marked unsourced")
        if bool(tiger_rampage.get("defense_break_duration_source_defined")):
            errors.append("tiger_rampage: break duration must remain marked unsourced")
        if bool(tiger_rampage.get("defense_break_amount_source_defined")):
            errors.append("tiger_rampage: defense reduction amount must remain marked unsourced")
        if not bool(tiger_rampage.get("carries_soul_weapon_elements")):
            errors.append("tiger_rampage: must carry Soul Weapon elements")
        if str(tiger_rampage.get("requires_soul_weapon"))!="melee":
            errors.append("tiger_rampage: melee weapon requirement must map to Soul Weapon")

    pop_knight=rows.get("pop_knight")
    if pop_knight:
        if str(pop_knight.get("scale"))!="attack":
            errors.append("pop_knight: primary scale must be Attack")
        if list(pop_knight.get("source_stat_influence") or [])!=["attack"]:
            errors.append("pop_knight: source influence must be Attack")
        if list(pop_knight.get("source_properties") or [])!=["carries_elements"]:
            errors.append("pop_knight: source Properties must be Carries Elements")
        if str(pop_knight.get("target_mode"))!="all_enemies_non_diminishing":
            errors.append("pop_knight: target mode must be All Enemies non-diminishing")
        if not bool(pop_knight.get("aoe_non_diminishing")):
            errors.append("pop_knight: non-diminishing AoE flag missing")
        if not bool(pop_knight.get("bonus_vs_flying")):
            errors.append("pop_knight: Flying bonus missing")
        if str(pop_knight.get("flying_template_flag"))!="flying":
            errors.append("pop_knight: Flying detection must use canonical template flag")
        if not bool(pop_knight.get("bonus_vs_flying_source_defined")):
            errors.append("pop_knight: source confirms extra damage against Flying")
        if bool(pop_knight.get("flying_bonus_numeric_source_defined")):
            errors.append("pop_knight: numeric Flying bonus must remain marked unsourced")
        if not bool(pop_knight.get("carries_soul_weapon_elements")):
            errors.append("pop_knight: must carry Soul Weapon elements")
        if str(pop_knight.get("requires_soul_weapon"))!="melee":
            errors.append("pop_knight: melee weapon requirement must map to Soul Weapon")

    plural_slash=rows.get("plural_slash")
    if plural_slash:
        if str(plural_slash.get("scale"))!="attack":
            errors.append("plural_slash: primary scale must be Attack")
        if str(plural_slash.get("secondary_scale"))!="dexterity":
            errors.append("plural_slash: Agility must map to Dexterity")
        if list(plural_slash.get("source_stat_influence") or [])!=["attack","agility"]:
            errors.append("plural_slash: source influence must be Attack + Agility")
        if list(plural_slash.get("source_properties") or [])!=["carries_elements"]:
            errors.append("plural_slash: source Properties must be Carries Elements")
        if str(plural_slash.get("target_mode"))!="one_enemy":
            errors.append("plural_slash: target mode must be One Enemy")
        if not bool(plural_slash.get("multi_slash")):
            errors.append("plural_slash: multi-slash identity missing")
        if bool(plural_slash.get("multi_hit_count_source_defined")):
            errors.append("plural_slash: hit count must remain marked unsourced")
        if not bool(plural_slash.get("agility_secondary_influence")):
            errors.append("plural_slash: Agility secondary influence missing")
        if bool(plural_slash.get("secondary_numeric_weight_source_defined")):
            errors.append("plural_slash: Agility numeric weight must remain marked unsourced")
        if not bool(plural_slash.get("carries_soul_weapon_elements")):
            errors.append("plural_slash: must carry Soul Weapon elements")
        if str(plural_slash.get("requires_soul_weapon"))!="melee":
            errors.append("plural_slash: melee weapon requirement must map to Soul Weapon")

    shock_soldier=rows.get("shock_soldier")
    if shock_soldier:
        if str(shock_soldier.get("scale"))!="attack":
            errors.append("shock_soldier: primary scale must be Attack")
        if list(shock_soldier.get("source_stat_influence") or [])!=["attack"]:
            errors.append("shock_soldier: source influence must be Attack")
        if list(shock_soldier.get("source_properties") or [])!=["carries_elements"]:
            errors.append("shock_soldier: source Properties must be Carries Elements")
        if str(shock_soldier.get("target_mode"))!="all_enemies_diminishing":
            errors.append("shock_soldier: target mode must be All Enemies diminishing")
        if not bool(shock_soldier.get("aoe_diminishing")):
            errors.append("shock_soldier: diminishing AoE flag missing")
        if bool(shock_soldier.get("diminishing_numeric_source_defined")):
            errors.append("shock_soldier: numeric diminishing curve must remain marked unsourced")
        if str(shock_soldier.get("soulbound_diminishing_model"))!="inverse_sqrt_target_count":
            errors.append("shock_soldier: Soulbound diminishing model mismatch")
        if not bool(shock_soldier.get("carries_soul_weapon_elements")):
            errors.append("shock_soldier: must carry Soul Weapon elements")
        if str(shock_soldier.get("requires_soul_weapon"))!="melee":
            errors.append("shock_soldier: melee weapon requirement must map to Soul Weapon")

    hammer_crush=rows.get("hammer_crush")
    if hammer_crush:
        if str(hammer_crush.get("scale"))!="attack":
            errors.append("hammer_crush: primary scale must be Attack")
        if list(hammer_crush.get("source_stat_influence") or [])!=["attack"]:
            errors.append("hammer_crush: source influence must be Attack")
        if list(hammer_crush.get("source_properties") or [])!=["carries_elements"]:
            errors.append("hammer_crush: source Properties must be Carries Elements")
        if str(hammer_crush.get("target_mode"))!="one_enemy":
            errors.append("hammer_crush: target mode must be One Enemy")
        if not bool(hammer_crush.get("carries_soul_weapon_elements")):
            errors.append("hammer_crush: must carry Soul Weapon elements")
        if str(hammer_crush.get("requires_soul_weapon"))!="melee":
            errors.append("hammer_crush: melee weapon requirement must map to Soul Weapon")

    dispose=rows.get("dispose")
    if dispose:
        if str(dispose.get("scale"))!="attack":
            errors.append("dispose: primary scale must be Attack")
        if list(dispose.get("source_stat_influence") or [])!=["attack"]:
            errors.append("dispose: source influence must be Attack")
        if list(dispose.get("source_properties") or [])!=["carries_elements"]:
            errors.append("dispose: source Properties must be Carries Elements")
        if str(dispose.get("target_mode"))!="all_enemies_non_diminishing":
            errors.append("dispose: target mode must be All Enemies non-diminishing")
        if not bool(dispose.get("aoe_non_diminishing")):
            errors.append("dispose: area damage must remain non-diminishing")
        if not bool(dispose.get("carries_soul_weapon_elements")):
            errors.append("dispose: must carry Soul Weapon elements")
        if str(dispose.get("requires_soul_weapon"))!="ranged":
            errors.append("dispose: ranged weapon requirement must map to Soul Weapon")
        if not bool(dispose.get("feedback_damage")):
            errors.append("dispose: Feedback self-damage missing")
        if bool(dispose.get("feedback_cost_source_defined")):
            errors.append("dispose: Feedback numeric cost must remain marked unsourced")
        if not bool(dispose.get("feedback_once_per_cast")):
            errors.append("dispose: Feedback must be applied once per cast")
        if not bool(dispose.get("feedback_repair_eligible")):
            errors.append("dispose: Feedback must be eligible for Self-Repair")

    range_fire=rows.get("range_fire")
    if range_fire:
        if str(range_fire.get("scale"))!="attack":
            errors.append("range_fire: primary scale must be Attack")
        if list(range_fire.get("source_stat_influence") or [])!=["attack"]:
            errors.append("range_fire: source influence must be Attack")
        if list(range_fire.get("source_properties") or [])!=["carries_elements"]:
            errors.append("range_fire: source Properties must be Carries Elements")
        if str(range_fire.get("target_mode"))!="all_enemies_non_diminishing":
            errors.append("range_fire: target mode must be All Enemies non-diminishing")
        if not bool(range_fire.get("aoe_non_diminishing")):
            errors.append("range_fire: area damage must remain non-diminishing")
        if not bool(range_fire.get("carries_soul_weapon_elements")):
            errors.append("range_fire: must carry Soul Weapon elements")
        if str(range_fire.get("requires_soul_weapon"))!="ranged":
            errors.append("range_fire: ranged weapon requirement must map to Soul Weapon")

    crosshair=rows.get("crosshair")
    if crosshair:
        if str(crosshair.get("scale"))!="attack":
            errors.append("crosshair: primary scale must be Attack")
        if list(crosshair.get("source_stat_influence") or [])!=[
            "attack","critical_hit_chance"
        ]:
            errors.append("crosshair: source influence must be Attack + Critical Hit Chance")
        if list(crosshair.get("source_properties") or [])!=["carries_elements"]:
            errors.append("crosshair: source Properties must be Carries Elements")
        if str(crosshair.get("target_mode"))!="one_enemy":
            errors.append("crosshair: target mode must be One Enemy")
        if not bool(crosshair.get("critical_chance_influence")):
            errors.append("crosshair: Critical Hit Chance influence missing")
        if not bool(crosshair.get("attempts_critical")):
            errors.append("crosshair: critical attempt contract missing")
        if str(crosshair.get("critical_model"))!="character_critical_hit_chance":
            errors.append("crosshair: must roll the character's real Critical Hit Chance")
        if not bool(crosshair.get("carries_soul_weapon_elements")):
            errors.append("crosshair: must carry Soul Weapon elements")
        if str(crosshair.get("requires_soul_weapon"))!="ranged":
            errors.append("crosshair: ranged weapon requirement must map to Soul Weapon")

    logic_bomb=rows.get("logic_bomb")
    if logic_bomb:
        if list(logic_bomb.get("source_stat_influence") or [])!=["will"]:
            errors.append("logic_bomb: source influence must be Will")
        if str(logic_bomb.get("scale"))!="willpower":
            errors.append("logic_bomb: scale must be Willpower")
        if int(logic_bomb.get("uoss_mp_cost",0) or 0)!=155:
            errors.append("logic_bomb: MP cost must be 155")
        if str(logic_bomb.get("target_mode"))!="one_enemy":
            errors.append("logic_bomb: target mode must be One Enemy")
        if list(logic_bomb.get("source_properties") or [])!=["cleanseable","extendable"]:
            errors.append("logic_bomb: source Properties must be Cleanseable + Extendable")
        if list(logic_bomb.get("control_effects") or [])!=["paralyze","silence","slow"]:
            errors.append("logic_bomb: base statuses must be Paralyze + Silence + Slow")
        if list(logic_bomb.get("support_weapon_extra_effects") or [])!=["blind","curse","immobilize"]:
            errors.append("logic_bomb: support statuses must be Blind + Curse + Immobilize")
        if str(logic_bomb.get("level_effect"))!="increases_accuracy_and_duration":
            errors.append("logic_bomb: Skill Level must increase Accuracy and Duration")
        if not bool(logic_bomb.get("machine_accuracy_bonus")):
            errors.append("logic_bomb: Machine targets must have increased hit rate")
        if bool(logic_bomb.get("accuracy_numeric_source_defined")):
            errors.append("logic_bomb: accuracy curve must remain marked unsourced")
        if bool(logic_bomb.get("duration_numeric_source_defined")):
            errors.append("logic_bomb: duration curve must remain marked unsourced")
        if bool(logic_bomb.get("machine_bonus_numeric_source_defined")):
            errors.append("logic_bomb: Machine bonus must remain marked unsourced")
        if bool(logic_bomb.get("status_numeric_source_defined")):
            errors.append("logic_bomb: status numeric behavior must remain marked unsourced")

    jammer=rows.get("jammer")
    if jammer:
        if list(jammer.get("source_stat_influence") or [])!=["will"]:
            errors.append("jammer: source influence must be Will")
        if str(jammer.get("scale"))!="willpower":
            errors.append("jammer: scale must be Willpower")
        if int(jammer.get("uoss_mp_cost",0) or 0)!=20:
            errors.append("jammer: normal MP cost must be 20")
        if int(jammer.get("uoss_support_mp_cost",0) or 0)!=40:
            errors.append("jammer: support MP cost must be 40")
        if str(jammer.get("target_mode"))!="one_or_support_all_enemies":
            errors.append("jammer: target mode must be one or support-all enemies")
        if list(jammer.get("source_properties") or [])!=["cleanseable","extendable"]:
            errors.append("jammer: source Properties must be Cleanseable + Extendable")
        if str(jammer.get("control_effect"))!="stop":
            errors.append("jammer: control effect must be Stop")
        if str(jammer.get("level_effect"))!="increases_accuracy_and_duration":
            errors.append("jammer: Skill Level must increase Accuracy and Duration")
        if not bool(jammer.get("machine_accuracy_bonus")):
            errors.append("jammer: mechanical enemies must be easier to affect")
        if not bool(jammer.get("support_weapon_expands_to_all_enemies")):
            errors.append("jammer: support weapon must expand effect to all enemies")
        if bool(jammer.get("accuracy_numeric_source_defined")):
            errors.append("jammer: accuracy curve must remain marked unsourced")
        if bool(jammer.get("duration_numeric_source_defined")):
            errors.append("jammer: duration curve must remain marked unsourced")
        if bool(jammer.get("machine_bonus_numeric_source_defined")):
            errors.append("jammer: machine accuracy bonus must remain marked unsourced")

    hypno=rows.get("hypno_flash")
    if hypno:
        if list(hypno.get("source_stat_influence") or [])!=["will"]:
            errors.append("hypno_flash: source influence must be Will")
        if str(hypno.get("scale"))!="willpower":
            errors.append("hypno_flash: scale must be Willpower")
        if int(hypno.get("uoss_mp_cost",0) or 0)!=15:
            errors.append("hypno_flash: MP cost must be 15")
        if str(hypno.get("target_mode"))!="one_enemy":
            errors.append("hypno_flash: target mode must be One Enemy")
        if list(hypno.get("source_properties") or [])!=["cleanseable","extendable"]:
            errors.append("hypno_flash: source Properties must be Cleanseable + Extendable")
        if str(hypno.get("control_effect"))!="sleep":
            errors.append("hypno_flash: control effect must be Sleep")
        if str(hypno.get("level_effect"))!="increases_accuracy_and_duration":
            errors.append("hypno_flash: Skill Level must increase Accuracy and Duration")
        if not bool(hypno.get("support_weapon_improves_accuracy")):
            errors.append("hypno_flash: support weapon must improve hit chance")
        if bool(hypno.get("accuracy_numeric_source_defined")):
            errors.append("hypno_flash: accuracy curve must remain marked unsourced")
        if bool(hypno.get("duration_numeric_source_defined")):
            errors.append("hypno_flash: duration curve must remain marked unsourced")

    mec_sonata=rows.get("mec_sonata")
    if mec_sonata:
        if list(mec_sonata.get("source_stat_influence") or [])!=["magic_attack"]:
            errors.append("mec_sonata: source influence must be Magic Attack only")
        if str(mec_sonata.get("scale"))!="intelligence":
            errors.append("mec_sonata: Magic Attack must use the magic/INT core")
        if int(mec_sonata.get("uoss_mp_cost",0) or 0)!=50:
            errors.append("mec_sonata: MP cost must be 50")
        if str(mec_sonata.get("target_mode"))!="one_enemy":
            errors.append("mec_sonata: target mode must be One Enemy")
        if list(mec_sonata.get("source_properties") or [])!=["extendable"]:
            errors.append("mec_sonata: source Properties must be Extendable")
        if not bool(mec_sonata.get("temporary_level_reduction_chance")):
            errors.append("mec_sonata: temporary level reduction chance missing")
        if not bool(mec_sonata.get("level_reduction_extendable")):
            errors.append("mec_sonata: level reduction must be Extendable")
        if bool(mec_sonata.get("level_reduction_numeric_source_defined")):
            errors.append("mec_sonata: level reduction amount must remain marked unsourced")
        if bool(mec_sonata.get("level_reduction_duration_source_defined")):
            errors.append("mec_sonata: duration must remain marked unsourced")
        if bool(mec_sonata.get("level_reduction_chance_source_defined")):
            errors.append("mec_sonata: proc chance must remain marked unsourced")

    magnify=rows.get("magnify")
    if magnify:
        if list(magnify.get("source_stat_influence") or [])!=["attack","wisdom"]:
            errors.append("magnify: source influence must be Attack + Wisdom")
        if str(magnify.get("scale"))!="attack":
            errors.append("magnify: primary scale must be Attack")
        if str(magnify.get("secondary_scale"))!="intelligence":
            errors.append("magnify: Wisdom must map to Intelligence")
        if str(magnify.get("target_mode"))!="one_enemy":
            errors.append("magnify: target mode must be One Enemy")
        if list(magnify.get("source_properties") or [])!=["cooldown"]:
            errors.append("magnify: source Properties must be Cooldown")
        if not bool(magnify.get("wisdom_magnifies_damage")):
            errors.append("magnify: Wisdom must magnify damage")
        if not bool(magnify.get("skill_level_reduces_system_failure")):
            errors.append("magnify: Skill Level must reduce systems failure")
        if not bool(magnify.get("wisdom_reduces_system_failure")):
            errors.append("magnify: Wisdom must reduce systems failure")
        if not bool(magnify.get("systems_failure_causes_overheat_reboot")):
            errors.append("magnify: systems failure must cause Overheat/reboot")
        if str(magnify.get("requires_soul_weapon"))!="ranged":
            errors.append("magnify: ranged weapon requirement must map to Soul Weapon")
        if bool(magnify.get("numeric_cooldown_source_defined")):
            errors.append("magnify: numeric cooldown duration must remain marked unsourced")
        if bool(magnify.get("systems_failure_numeric_source_defined")):
            errors.append("magnify: numeric failure curve must remain marked unsourced")

    satellite=rows.get("satellite_linker")
    if satellite:
        if list(satellite.get("source_stat_influence") or [])!=["attack","wisdom"]:
            errors.append("satellite_linker: source influence must be Attack + Wisdom")
        if str(satellite.get("scale"))!="attack":
            errors.append("satellite_linker: primary scale must be Attack")
        if str(satellite.get("secondary_scale"))!="intelligence":
            errors.append("satellite_linker: Wisdom must map to Intelligence")
        if str(satellite.get("target_mode"))!="one_enemy":
            errors.append("satellite_linker: target mode must be One Enemy")
        if not bool(satellite.get("periodic_damage")):
            errors.append("satellite_linker: periodic damage missing")
        if str(satellite.get("level_effect"))!="increases_duration":
            errors.append("satellite_linker: Skill Level must increase duration")
        if bool(satellite.get("duration_source_defined")):
            errors.append("satellite_linker: numeric duration must remain marked unsourced")
        if bool(satellite.get("tick_cadence_source_defined")):
            errors.append("satellite_linker: tick cadence must remain marked unsourced")
        if bool(satellite.get("tick_damage_source_defined")):
            errors.append("satellite_linker: tick damage must remain marked unsourced")
        if list(satellite.get("source_properties") or [])!=[]:
            errors.append("satellite_linker: source Properties must remain None")

    shoot_all=rows.get("shoot_all")
    if shoot_all:
        if str(shoot_all.get("scale"))!="attack":
            errors.append(f"shoot_all:scale={shoot_all.get('scale')} expected=attack")
        if list(shoot_all.get("source_stat_influence") or [])!=["attack","critical_hit_chance"]:
            errors.append("shoot_all: source influence must be Attack + Critical Hit Chance")
        if str(shoot_all.get("target_mode"))!="all_enemies_non_diminishing":
            errors.append("shoot_all: target mode must be all enemies non-diminishing")
        if not bool(shoot_all.get("carries_soul_weapon_elements")):
            errors.append("shoot_all: must carry Soul Weapon elements")
        if not bool(shoot_all.get("vmax_increases_critical_and_damage")):
            errors.append("shoot_all: missing V-MAX crit/damage increase")
        if bool(shoot_all.get("vmax_numeric_source_defined")):
            errors.append("shoot_all: V-MAX numeric bonus must remain marked unsourced")
    compress=rows.get("compress")
    if compress:
        if list(compress.get("source_stat_influence") or [])!=["vitality","hp"]:
            errors.append("compress: source influence must be Vitality + HP")
        if str(compress.get("scale"))!="target_current_hp_percent":
            errors.append("compress: damage must be percentage of target current HP")
        if str(compress.get("target_mode"))!="one_enemy":
            errors.append("compress: target mode must be One Enemy")
        if str(compress.get("level_effect"))!="increases_accuracy":
            errors.append("compress: Skill Level must increase Accuracy")
        if not bool(compress.get("percentage_target_hp_damage")):
            errors.append("compress: percentage HP damage flag missing")
        if not bool(compress.get("full_hp_increases_power")):
            errors.append("compress: full HP must increase compressing power")
        if not bool(compress.get("shield_increases_compressing_power")):
            errors.append("compress: shield must increase compressing power")
        if not bool(compress.get("feedback_damage")):
            errors.append("compress: Feedback self-damage missing")
        if bool(compress.get("feedback_cost_source_defined")):
            errors.append("compress: Feedback numeric cost must remain marked unsourced")
        if bool(compress.get("numeric_source_defined")):
            errors.append("compress: numeric percentage/accuracy curve must remain marked unsourced")
        if list(compress.get("source_properties") or [])!=[]:
            errors.append("compress: source Properties must remain None")

    destroy=rows.get("destroy")
    if destroy:
        if list(destroy.get("source_stat_influence") or [])!=["hp","vitality","attack"]:
            errors.append("destroy: source influence must be HP + Vitality + Attack")
        if str(destroy.get("scale"))!="attack":
            errors.append("destroy: primary scale must be Attack")
        if str(destroy.get("secondary_scale"))!="constitution":
            errors.append("destroy: Vitality must map to Constitution")
        if str(destroy.get("target_mode"))!="one_enemy":
            errors.append("destroy: target mode must be One Enemy")
        if not bool(destroy.get("feedback_damage")):
            errors.append("destroy: Feedback self-damage missing")
        if not bool(destroy.get("shield_improves_damage")):
            errors.append("destroy: equipped shield must improve damage")
        if not bool(destroy.get("power_increases_as_hp_decreases")):
            errors.append("destroy: lower HP must increase attack power")
        if bool(destroy.get("feedback_cost_source_defined")):
            errors.append("destroy: Feedback numeric cost must remain marked unsourced")
        if bool(destroy.get("numeric_source_defined")):
            errors.append("destroy: numeric modifiers must remain marked unsourced")
        if list(destroy.get("source_properties") or [])!=[]:
            errors.append("destroy: source Properties must remain None")

    robo_tackle=rows.get("robo_tackle")
    if robo_tackle:
        if list(robo_tackle.get("source_stat_influence") or [])!=["hp","vitality","attack"]:
            errors.append("robo_tackle: source influence must be HP + Vitality + Attack")
        if str(robo_tackle.get("scale"))!="attack":
            errors.append("robo_tackle: primary scale must be Attack")
        if str(robo_tackle.get("secondary_scale"))!="constitution":
            errors.append("robo_tackle: Vitality must map to Constitution")
        if str(robo_tackle.get("target_mode"))!="one_enemy":
            errors.append("robo_tackle: target mode must be One Enemy")
        if not bool(robo_tackle.get("damage_from_current_hp")):
            errors.append("robo_tackle: current HP must influence damage")
        if not bool(robo_tackle.get("shield_improves_damage")):
            errors.append("robo_tackle: equipped shield must improve damage")
        if not bool(robo_tackle.get("vmax_power_and_feedback")):
            errors.append("robo_tackle: V-MAX must increase power and Feedback")
        if not bool(robo_tackle.get("feedback_damage")):
            errors.append("robo_tackle: Feedback self-damage missing")
        if bool(robo_tackle.get("feedback_cost_source_defined")):
            errors.append("robo_tackle: Feedback numeric cost must remain marked unsourced")
        if bool(robo_tackle.get("numeric_source_defined")):
            errors.append("robo_tackle: numeric modifiers must remain marked unsourced")
        if list(robo_tackle.get("source_properties") or [])!=[]:
            errors.append("robo_tackle: source Properties must remain None")

    uzi=rows.get("uzi_punch")
    if uzi:
        if list(uzi.get("source_stat_influence") or [])!=["hp","vitality","attack"]:
            errors.append("uzi_punch: source influence must be HP + Vitality + Attack")
        if str(uzi.get("scale"))!="attack":
            errors.append("uzi_punch: primary scale must be Attack")
        if str(uzi.get("secondary_scale"))!="constitution":
            errors.append("uzi_punch: Vitality must map to Constitution")
        if str(uzi.get("target_mode"))!="random_enemies":
            errors.append("uzi_punch: target mode must be Random Enemies")
        if not bool(uzi.get("feedback_damage")):
            errors.append("uzi_punch: Feedback self-damage missing")
        if not bool(uzi.get("shield_improves_damage")):
            errors.append("uzi_punch: equipped shield must improve damage")
        if not bool(uzi.get("power_increases_as_hp_decreases")):
            errors.append("uzi_punch: lower HP must increase attack power")
        if bool(uzi.get("feedback_cost_source_defined")):
            errors.append("uzi_punch: Feedback numeric cost must remain marked unsourced")
        if bool(uzi.get("numeric_source_defined")):
            errors.append("uzi_punch: numeric modifiers must remain marked unsourced")
        if bool(uzi.get("random_target_count_source_defined")):
            errors.append("uzi_punch: Random Enemies hit count must remain marked unsourced")
        if list(uzi.get("source_properties") or [])!=[]:
            errors.append("uzi_punch: source Properties must remain None")

    crush=rows.get("crush")
    if crush:
        if list(crush.get("source_stat_influence") or [])!=["hp","level"]:
            errors.append("crush: source influence must be HP + Level")
        if str(crush.get("scale"))!="hp_difference":
            errors.append("crush: damage source must be max HP minus current HP")
        if str(crush.get("target_mode"))!="one_enemy":
            errors.append("crush: target mode must be one enemy")
        if not bool(crush.get("damage_from_missing_hp")):
            errors.append("crush: missing HP must drive damage")
        if not bool(crush.get("level_caps_damage")):
            errors.append("crush: Character Level must limit damage capacity")
        if str(crush.get("level_effect"))!="increases_maximum_possible_damage":
            errors.append("crush: Skill Level must increase maximum possible damage")
        if not bool(crush.get("shield_increases_capacity")):
            errors.append("crush: equipped shield must increase capacity")
        if not bool(crush.get("feedback_damage")):
            errors.append("crush: Feedback self-damage missing")
        if bool(crush.get("feedback_cost_source_defined")):
            errors.append("crush: Feedback numeric cost must remain marked unsourced")
        if bool(crush.get("numeric_source_defined")):
            errors.append("crush: numeric cap curve must remain marked unsourced")
        if list(crush.get("source_properties") or [])!=[]:
            errors.append("crush: source Properties must remain None")

    kamikaze=rows.get("kamikaze_crush")
    if kamikaze:
        if list(kamikaze.get("source_stat_influence") or [])!=["hp","vitality","attack"]:
            errors.append("kamikaze_crush: source influence must be HP + Vitality + Attack")
        if str(kamikaze.get("scale"))!="attack":
            errors.append("kamikaze_crush: primary scale must be Attack")
        if str(kamikaze.get("secondary_scale"))!="constitution":
            errors.append("kamikaze_crush: Vitality must map to Constitution")
        if str(kamikaze.get("target_mode"))!="one_enemy":
            errors.append("kamikaze_crush: target mode must be one enemy")
        if not bool(kamikaze.get("damage_from_current_hp")):
            errors.append("kamikaze_crush: current HP must influence damage")
        if not bool(kamikaze.get("shield_improves_damage")):
            errors.append("kamikaze_crush: equipped shield must improve damage")
        if not bool(kamikaze.get("vmax_power_and_feedback")):
            errors.append("kamikaze_crush: V-MAX must increase power and Feedback")
        if bool(kamikaze.get("numeric_source_defined")):
            errors.append("kamikaze_crush: numeric modifiers must remain marked unsourced")
        if list(kamikaze.get("source_properties") or [])!=[]:
            errors.append("kamikaze_crush: source Properties must remain None")

    starlight=rows.get("starlight_shower")
    if starlight:
        if list(starlight.get("source_stat_influence") or [])!=["magic_attack"]:
            errors.append("starlight_shower: source influence must be Magic Attack")
        if int(starlight.get("uoss_mp_cost",0) or 0)!=225:
            errors.append("starlight_shower: normal MP cost must be 225")
        if int(starlight.get("uoss_vmax_mp_cost",0) or 0)!=300:
            errors.append("starlight_shower: V-MAX MP cost must be 300")
        if str(starlight.get("target_mode"))!="single_or_diminishing_aoe":
            errors.append("starlight_shower: normal target mode must be single or diminishing AoE")
        if not bool(starlight.get("aoe_diminishing")):
            errors.append("starlight_shower: normal multi-target mode must diminish")
        if str(starlight.get("vmax_target_mode"))!="all_enemies_non_diminishing":
            errors.append("starlight_shower: V-MAX must target all enemies non-diminishing")
        if not bool(starlight.get("vmax_aoe_non_diminishing")):
            errors.append("starlight_shower: V-MAX non-diminishing flag missing")
        if bool(starlight.get("diminishing_numeric_source_defined")):
            errors.append("starlight_shower: diminishing numeric curve must remain marked unsourced")
        if list(starlight.get("source_properties") or [])!=[]:
            errors.append("starlight_shower: source Properties must remain None")

    vmax=rows.get("vmax")
    if vmax:
        if str(vmax.get("scale"))!="willpower":
            errors.append(f"vmax:scale={vmax.get('scale')} expected=willpower")
        if str(vmax.get("support_weapon_model"))!="mec_soul_weapon":
            errors.append(
                f"vmax:support_weapon_model={vmax.get('support_weapon_model')} expected=mec_soul_weapon"
            )
        if not bool(vmax.get("duration_scales_with_skill_level")):
            errors.append("vmax:missing skill-level duration scaling")
        if not bool(vmax.get("duration_scales_with_will")):
            errors.append("vmax:missing WILL duration scaling")
        _praise=((vmax.get("vmax_status_sources") or {}).get("praise") or {})
        if str(_praise.get("effect"))!="attack_power_up":
            errors.append("vmax:praise must raise Attack power")
        _preach=((vmax.get("vmax_status_sources") or {}).get("preach") or {})
        if str(_preach.get("effect"))!="magic_attack_up":
            errors.append("vmax:preach must raise Magic Attack")
        if "will" not in list(_preach.get("source_stat_influence") or []):
            errors.append("vmax:preach missing WILL influence metadata")
        _protect=((vmax.get("vmax_status_sources") or {}).get("protect") or {})
        if str(_protect.get("effect"))!="incoming_physical_damage_down":
            errors.append("vmax:protect must reduce incoming physical damage")
        if "will" not in list(_protect.get("source_stat_influence") or []):
            errors.append("vmax:protect missing WILL influence metadata")
        _shell=((vmax.get("vmax_status_sources") or {}).get("shell") or {})
        if str(_shell.get("effect"))!="incoming_magic_damage_down":
            errors.append("vmax:shell must reduce incoming magic damage")
        if "will" not in list(_shell.get("source_stat_influence") or []):
            errors.append("vmax:shell missing WILL influence metadata")
        _regen=((vmax.get("vmax_status_sources") or {}).get("regen") or {})
        if str(_regen.get("effect"))!="periodic_small_hp_heal":
            errors.append("vmax:regen must be periodic HP healing")
        if "will" not in list(_regen.get("source_stat_influence") or []):
            errors.append("vmax:regen missing WILL influence metadata")
        if bool(_regen.get("tick_cadence_source_defined")):
            errors.append("vmax:regen cadence must remain unsourced until exact data exists")
        if bool(_regen.get("heal_amount_source_defined")):
            errors.append("vmax:regen heal amount must remain unsourced until exact data exists")
    for protocol_id,specials in MEC_PROTOCOL_SKILLS_V11155.items():
        protocol_row=next((row for row in CLASS_SKILLS.get("Mec",[]) if row.get("id")==protocol_id),None)
        if not protocol_row:
            errors.append(f"missing protocol row:{protocol_id}")
            continue
        if not bool(protocol_row.get("automatic")):
            errors.append(f"{protocol_id}:not automatic")
        if str(protocol_row.get("level_effect"))!="increases_mapped_skill_damage":
            errors.append(f"{protocol_id}:bad level effect")
        if float(protocol_row.get("protocol_multiplier_level1",0.0) or 0.0)!=1.05:
            errors.append(f"{protocol_id}:bad level1 multiplier")
        if float(protocol_row.get("protocol_multiplier_level600",0.0) or 0.0)!=1.75:
            errors.append(f"{protocol_id}:bad level600 multiplier")
    support_contract=MEC_CANONICAL_CONTRACT_V11149["branches"]["support"]
    if str(support_contract.get("support_weapon"))!="soul_weapon":
        errors.append(
            f"support:weapon={support_contract.get('support_weapon')} expected=soul_weapon"
        )
    for sid,(unlock,branch) in _MEC_EXPECTED_V11149.items():
        row=rows.get(sid)
        if not row: errors.append(f"missing:{sid}"); continue
        if int(row.get("unlock",0))!=unlock: errors.append(f"{sid}:unlock={row.get('unlock')} expected={unlock}")
        if str(row.get("mec_branch"))!=branch: errors.append(f"{sid}:branch={row.get('mec_branch')} expected={branch}")
        if int(row.get("cooldown",0) or 0)!=0 and not row.get("mechanic_cooldown"):
            errors.append(f"{sid}:ordinary cooldown")
        expected_protocol=protocol_by_special.get(sid)
        if expected_protocol:
            actual=MEC_CANONICAL_CONTRACT_V11149["branches"][branch].get("protocol")
            if actual!=expected_protocol:
                errors.append(f"{sid}:protocol={actual} expected={expected_protocol}")
        if sid in source_mp_costs and int(row.get("uoss_mp_cost",0) or 0)!=source_mp_costs[sid]:
            errors.append(f"{sid}:mp={row.get('uoss_mp_cost')} expected={source_mp_costs[sid]}")
        if sid in source_support_mp_costs and int(row.get("uoss_support_mp_cost",0) or 0)!=source_support_mp_costs[sid]:
            errors.append(f"{sid}:support_mp={row.get('uoss_support_mp_cost')} expected={source_support_mp_costs[sid]}")
    return {"version":"1.11.49","checked":len(_MEC_EXPECTED_V11149),"errors":errors,"error_count":len(errors)}
MEC_CONTRACT_AUDIT_V11149=_mec_contract_audit_v11149()
if MEC_CONTRACT_AUDIT_V11149["error_count"]:
    raise RuntimeError("Mec Contract Audit v1.11.49 failed: "+"; ".join(MEC_CONTRACT_AUDIT_V11149["errors"]))


# v0.31.7: authored Engineer tool kit based on the user-provided UOSSMUD list.
# Source Base AP means AP/learning points in UOSS. It is metadata only here and
# must never be reused as combat power. Soulbound damage is driven by stats/EQ,
# Soul Power, Skill Level, Upgrade/passives and each tool's authored mechanics.
def _v0317_install_engineer_toolkit():
    rows = CLASS_SKILLS.get("Inżynier", [])
    if len(rows) < 19:
        return
    specs = [
      # name, unlock, kind, source_ap_cost, special, category, description
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
      ("Upgrade",16,"utility",15000,"upgrade","utility","Trwałe narzędzie użytkowe Inżyniera: ulepsza wybrane narzędzie. Nie jest buffem bojowym. Bazowo 1 slot; Silver Gear i Gold Battery zwiększają limit."),
      ("Noise Blaster",18,"aoe_damage",2500,"noise_blaster","area","Fala dźwięku uderza i ucisza przeciwników. Ulepszenie zwiększa obrażenia i efekt kontroli."),
      ("Chainsaw",20,"damage",5000,"chainsaw","single","Piła łańcuchowa zadaje ciężkie obrażenia albo efekt Demi. Ulepszenie wzmacnia Demi do Quarter."),
      ("Mega Bomb",21,"aoe_damage",5000,"mega_bomb","single","Potężna eksplozja: główny cel otrzymuje pełne obrażenia, pozostali mniejsze. Ulepszenie zwiększa obrażenia wszystkim celom."),
      ("Silver Gear",21,"passive",15000,"silver_gear","passive","Pasywnie dodaje drugi slot systemu Upgrade."),
      ("Air Anchor",23,"damage",7500,"air_anchor","single","Kotwica wbija się w cel i zadaje obrażenia. Ulepszenie zwiększa moc efektu."),
      ("Gold Battery",23,"passive",15000,"gold_battery","passive","Pasywnie dodaje trzeci slot systemu Upgrade."),
    ]
    # Replace only 19 generated entries so total class skill count remains 123.
    for index, spec in enumerate(specs):
        name,unlock,kind,source_ap,special,category,desc = spec
        row=rows[index]
        row.clear()
        row.update({
          "id":f"v0317_engineer_{special}","name":name,
          "aliases":[name.casefold()],"unlock":unlock,"kind":kind,"cooldown":4,"mana":0,
          "base_power":0,
          "source_ap_cost":source_ap,
          "source_ap_semantics":"learning_points",
          "source_ap_is_damage_power":False,
          "engineer_tool":True,"engineer_special":special,
          "engineer_category":category,"desc":desc,
        })
        if kind in ("damage","aoe_damage"):
            row.update({"scale":"dexterity","mult":1.0})
            if kind=="aoe_damage": row["aoe"]=True
        _harmful_engineer_effects={
            "bio_blaster":["poison"],
            "flash":["blind","guard_break"],
            "debilitator":["elemental_vulnerability"],
            "drill":["armor_break"],
            "napalm":["flammable_oil"],
            "noise_blaster":["silence","slow"],
            "chainsaw":["hp_leak"],
            "air_anchor":["air_anchor"],
        }
        if special in _harmful_engineer_effects:
            row.update({
                "soulbound_target_scope":"enemy_only",
                "soulbound_harmful_debuff":True,
                "enemy_debuffs":list(_harmful_engineer_effects[special]),
            })
        if special=="upgrade": row.update({"boost":1.0,"duration":1})
    CLASS_SKILLS["Inżynier"] = rows

_v0317_install_engineer_toolkit()

def _v11196_engineer_ap_semantics_audit():
    rows=[
        row for row in CLASS_SKILLS.get("Inżynier",[])
        if row.get("engineer_tool")
    ]
    errors=[]
    if len(rows)!=19:
        errors.append(f"Engineer authored toolkit count={len(rows)} expected=19")
    for row in rows:
        sid=str(row.get("engineer_special","") or row.get("id",""))
        if str(row.get("source_ap_semantics",""))!="learning_points":
            errors.append(f"{sid}: source AP must mean learning points")
        if bool(row.get("source_ap_is_damage_power")):
            errors.append(f"{sid}: source AP cannot be damage power")
        if int(row.get("base_power",0) or 0)!=0:
            errors.append(f"{sid}: Engineer base_power must not be sourced from AP")
        if bool(row.get("soulbound_harmful_debuff")):
            if str(row.get("soulbound_target_scope",""))!="enemy_only":
                errors.append(f"{sid}: harmful Engineer effect must be enemy_only")
    return {"checked":len(rows),"errors":errors,"error_count":len(errors)}

ENGINEER_AP_SEMANTICS_AUDIT_V11196=_v11196_engineer_ap_semantics_audit()
if ENGINEER_AP_SEMANTICS_AUDIT_V11196["error_count"]:
    raise RuntimeError(
        "Engineer AP semantics audit v1.11.96 failed: "
        + "; ".join(ENGINEER_AP_SEMANTICS_AUDIT_V11196["errors"])
    )

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
        "heal", "group_heal", "passive", "utility",
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
        "version": "0.35.6",
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


# v1.11.96: class healing uses the same independent stat-build philosophy as
# damage. Source-authored scales are preserved (e.g. Priest Regen/Healing Wind
# remain WILL). Only heals without an explicit source scale receive the class
# default below.
_CLASS_HEALING_SCALES_V11196 = {
    "Kapłan": ("intelligence", "willpower"),
    "Druid": ("intelligence", "willpower"),
    "Mnich": ("dexterity", "willpower"),
}
for _class_name, (_primary, _secondary) in _CLASS_HEALING_SCALES_V11196.items():
    for _skill in CLASS_SKILLS.get(_class_name, ()):
        if str(_skill.get("kind", "")) not in {"heal", "group_heal"}:
            continue
        if not str(_skill.get("scale", "") or "").strip():
            _skill["scale"] = _primary
            _skill["secondary_scale"] = _secondary
            _skill["healing_stat_identity_v11196"] = True
        if _class_name == "Kapłan":
            if str(_skill.get("kind", "")) == "heal":
                _skill.setdefault("target_mode", "self_or_one_ally")
                _skill.setdefault("soulbound_enemy_heal_disabled", True)
            elif str(_skill.get("kind", "")) == "group_heal":
                _skill.setdefault("target_mode", "local_party")
                _skill.setdefault("soulbound_enemy_heal_disabled", True)


_TARGET_SCOPE_BY_KIND_V11196 = {
    "damage":"enemy_only",
    "aoe_damage":"enemy_only",
    "execute":"enemy_only",
    "drain":"enemy_only",
    "heal":"ally_or_self",
    "group_heal":"allies_only",
    "regen":"ally_or_self",
    "boost":"self_only",
    "guard":"self_only",
    "evade":"self_only",
    "passive":"passive",
    "utility":"special",
}

for _class_name,_skills in CLASS_SKILLS.items():
    for _skill in _skills:
        _kind=str(_skill.get("kind","") or "")
        _skill.setdefault(
            "soulbound_kind_target_scope_v11196",
            _TARGET_SCOPE_BY_KIND_V11196.get(_kind,"unknown"),
        )


def _all_class_skill_target_audit_v11196():
    """Target-role audit for every skill in every playable Soulbound class."""
    errors=[]
    expected_classes={
        "Wojownik","Berserker","Łotrzyk","Łowca","Mnich","Strażnik",
        "Mag","Nekromanta","Kapłan","Czarownik","Druid","Psionik",
        "Inżynier","Mec",
    }
    actual_classes=set(CLASS_SKILLS)
    if actual_classes!=expected_classes:
        errors.append(
            "playable class set mismatch: "
            f"missing={sorted(expected_classes-actual_classes)} "
            f"extra={sorted(actual_classes-expected_classes)}"
        )
    per_class={}
    total=0
    for class_name,skills in CLASS_SKILLS.items():
        per_class[class_name]=len(skills)
        total+=len(skills)
        for skill in skills:
            sid=str(skill.get("id","") or skill.get("name","?"))
            kind=str(skill.get("kind","") or "")
            expected=_TARGET_SCOPE_BY_KIND_V11196.get(kind)
            actual=str(skill.get("soulbound_kind_target_scope_v11196","") or "")
            if expected is None:
                errors.append(f"{class_name}:{sid}: unknown kind={kind}")
                continue
            if actual!=expected:
                errors.append(
                    f"{class_name}:{sid}: kind target scope={actual} expected={expected}"
                )

            # Harmful effects may never point at self/allies even when the skill
            # also deals damage or has a custom authored runtime.
            if bool(skill.get("soulbound_harmful_debuff")):
                if str(skill.get("soulbound_target_scope",""))!="enemy_only":
                    errors.append(
                        f"{class_name}:{sid}: harmful debuff must be enemy_only"
                    )

            # Healing is the inverse invariant: never heal a hostile mob.
            if kind in {"heal","group_heal","regen"}:
                if bool(skill.get("soulbound_harmful_debuff")):
                    errors.append(
                        f"{class_name}:{sid}: healing skill cannot be harmful debuff"
                    )
                if str(skill.get("soulbound_target_scope",""))=="enemy_only":
                    errors.append(
                        f"{class_name}:{sid}: healing skill cannot be enemy_only"
                    )

    return {
        "version":"1.11.96",
        "classes":len(CLASS_SKILLS),
        "skills":total,
        "per_class":per_class,
        "error_count":len(errors),
        "errors":errors,
    }


ALL_CLASS_SKILL_TARGET_AUDIT_V11196=_all_class_skill_target_audit_v11196()
if ALL_CLASS_SKILL_TARGET_AUDIT_V11196["error_count"]:
    raise RuntimeError(
        "All Class Skill Target Audit v1.11.96 failed: "
        + "; ".join(ALL_CLASS_SKILL_TARGET_AUDIT_V11196["errors"][:50])
    )


def _class_healing_scale_audit_v11196():
    errors = []
    report = {}
    for class_name, (primary, secondary) in _CLASS_HEALING_SCALES_V11196.items():
        rows = [
            skill for skill in CLASS_SKILLS.get(class_name, ())
            if str(skill.get("kind", "")) in {"heal", "group_heal"}
        ]
        missing = [
            skill.get("name", skill.get("id", "?"))
            for skill in rows
            if not str(skill.get("scale", "") or "").strip()
        ]
        if missing:
            errors.append(f"{class_name}: heal bez scale: {', '.join(map(str, missing[:20]))}")
        report[class_name] = {
            "heals": len(rows),
            "default_primary": primary,
            "default_secondary": secondary,
        }
    return {
        "version": "1.11.96",
        "report": report,
        "error_count": len(errors),
        "errors": errors,
    }


CLASS_HEALING_SCALE_AUDIT_V11196 = _class_healing_scale_audit_v11196()
if CLASS_HEALING_SCALE_AUDIT_V11196["error_count"]:
    raise RuntimeError(
        "Class Healing Scale Audit v1.11.96 failed: "
        + "; ".join(CLASS_HEALING_SCALE_AUDIT_V11196["errors"][:50])
    )


def _harmful_debuff_target_audit_v11196():
    """All marked harmful player debuffs must affect enemies, never self/allies."""
    errors=[]
    checked=[]
    for class_name, skills in CLASS_SKILLS.items():
        for skill in skills:
            if not bool(skill.get("soulbound_harmful_debuff")):
                continue
            sid=str(skill.get("id","") or skill.get("name",""))
            checked.append(f"{class_name}:{sid}")
            if str(skill.get("soulbound_target_scope",""))!="enemy_only":
                errors.append(f"{class_name}:{sid}: harmful debuff must be enemy_only")
            target_mode=str(skill.get("target_mode","") or "")
            if target_mode in {
                "self","self_or_one_ally","one_ally","local_party",
                "party","all_allies","single_or_support_party",
                "one_ally_or_support_party",
            }:
                errors.append(
                    f"{class_name}:{sid}: harmful debuff cannot target self/allies"
                )
    return {
        "version":"1.11.96",
        "checked":checked,
        "error_count":len(errors),
        "errors":errors,
    }


HARMFUL_DEBUFF_TARGET_AUDIT_V11196=_harmful_debuff_target_audit_v11196()
if HARMFUL_DEBUFF_TARGET_AUDIT_V11196["error_count"]:
    raise RuntimeError(
        "Harmful Debuff Target Audit v1.11.96 failed: "
        + "; ".join(HARMFUL_DEBUFF_TARGET_AUDIT_V11196["errors"][:50])
    )


def _priest_healing_contract_audit_v11196():
    rows = {
        str(skill.get("id", "")): skill
        for skill in CLASS_SKILLS.get("Kapłan", ())
        if str(skill.get("kind", "")) in {"heal", "group_heal", "regen"}
    }
    errors = []

    regen = rows.get("priest_regen")
    if not regen:
        errors.append("priest_regen: missing")
    else:
        if int(regen.get("unlock", 0) or 0) != 1:
            errors.append("priest_regen: Reqs None must map to Biegłość Kapłana 1")
        if int(regen.get("source_ap_cost", 0) or 0) != 300:
            errors.append("priest_regen: Base AP 300 must remain learning points")
        if str(regen.get("source_ap_semantics", "")) != "learning_points":
            errors.append("priest_regen: AP semantics must be learning_points")
        if list(regen.get("source_target_mode") or []) != ["self", "one_ally"]:
            errors.append("priest_regen: target must remain Self/One Ally")
        if list(regen.get("source_stat_influence") or []) != ["will"]:
            errors.append("priest_regen: Stat Influence must remain Will")
        if list(regen.get("source_properties") or []) != [
            "dispelable", "extendable", "reflectable", "silenceable"
        ]:
            errors.append("priest_regen: source Properties mismatch")
        if str(regen.get("level_effect", "")) != "increases_duration":
            errors.append("priest_regen: Level Effect must increase Duration")

    wind = rows.get("priest_healing_wind")
    if not wind:
        errors.append("priest_healing_wind: missing")
    else:
        if int(wind.get("unlock", 0) or 0) != 1:
            errors.append("priest_healing_wind: Reqs None must map to Biegłość Kapłana 1")
        if int(wind.get("source_ap_cost", 0) or 0) != 1500:
            errors.append("priest_healing_wind: Base AP 1500 must remain learning points")
        if str(wind.get("source_ap_semantics", "")) != "learning_points":
            errors.append("priest_healing_wind: AP semantics must be learning_points")
        if int(wind.get("mana", 0) or 0) != 60:
            errors.append("priest_healing_wind: MP cost must remain 60")
        if str(wind.get("source_target_mode", "")) != "all_allies":
            errors.append("priest_healing_wind: target must remain All Allies")
        if list(wind.get("source_stat_influence") or []) != ["will"]:
            errors.append("priest_healing_wind: Stat Influence must remain Will")
        if list(wind.get("source_properties") or []) != ["multicastable", "silenceable"]:
            errors.append("priest_healing_wind: source Properties mismatch")
        if str(wind.get("level_effect", "")) != "increases_healing_power":
            errors.append("priest_healing_wind: Level Effect must increase Healing Power")
        if wind.get("heal_pct") is not None:
            errors.append("priest_healing_wind: no invented source healing percentage allowed")

    for sid, row in rows.items():
        kind = str(row.get("kind", ""))
        if kind == "heal":
            if str(row.get("target_mode", "")) != "self_or_one_ally":
                errors.append(f"{sid}: single heal target must be self_or_one_ally")
            if not bool(row.get("soulbound_enemy_heal_disabled")):
                errors.append(f"{sid}: enemy healing must remain disabled")
        elif kind == "group_heal":
            if str(row.get("target_mode", "")) != "local_party":
                errors.append(f"{sid}: group heal target must be local_party")
            if not bool(row.get("soulbound_enemy_heal_disabled")):
                errors.append(f"{sid}: enemy healing must remain disabled")

    return {
        "version": "1.11.96",
        "checked": len(rows),
        "ids": sorted(rows),
        "error_count": len(errors),
        "errors": errors,
    }


PRIEST_HEALING_CONTRACT_AUDIT_V11196 = _priest_healing_contract_audit_v11196()
if PRIEST_HEALING_CONTRACT_AUDIT_V11196["error_count"]:
    raise RuntimeError(
        "Priest Healing Contract Audit v1.11.96 failed: "
        + "; ".join(PRIEST_HEALING_CONTRACT_AUDIT_V11196["errors"][:50])
    )


def _physical_skill_mana_audit():
    errors = []
    checked = 0
    for class_name in sorted(PHYSICAL_MANA_FREE_CLASSES):
        for skill in CLASS_SKILLS.get(class_name, ()):
            checked += 1
            try:
                raw_mana = int(skill.get("mana", 0) or 0)
            except (TypeError, ValueError):
                errors.append(f"{class_name}/{skill.get('name', skill.get('id', '?'))}: nieprawidłowa mana")
                continue
            if raw_mana != 0:
                errors.append(
                    f"{class_name}/{skill.get('name', skill.get('id', '?'))}: mana={raw_mana}, wymagane 0"
                )
    return {"checked": checked, "error_count": len(errors), "errors": errors}


PHYSICAL_SKILL_MANA_AUDIT = _physical_skill_mana_audit()
if PHYSICAL_SKILL_MANA_AUDIT["error_count"]:
    raise RuntimeError(
        "Physical Skill Mana Audit failed: "
        + "; ".join(PHYSICAL_SKILL_MANA_AUDIT["errors"][:50])
    )



# v1.11.40: global no-cooldown policy.
# Ordinary class skills of every class have no reuse timer. A cooldown may
# survive only when the skill explicitly declares that the timer is part of
# its special mechanic.
SPECIAL_MECHANIC_COOLDOWN_IDS_V11140 = {"v0319_mec_vmax"}
for _class_name, _skills in CLASS_SKILLS.items():
    for _skill in _skills:
        _sid=str(_skill.get("id",""))
        if _sid in SPECIAL_MECHANIC_COOLDOWN_IDS_V11140 or _skill.get("mechanic_cooldown"):
            _skill["mechanic_cooldown"]=True
            continue
        _skill["cooldown"]=0

def _skill_cooldown_audit_v11140():
    errors=[]
    checked=0
    exceptions=[]
    for class_name,skills in CLASS_SKILLS.items():
        for skill in skills:
            checked+=1
            cd=int(skill.get("cooldown",0) or 0)
            if skill.get("mechanic_cooldown"):
                exceptions.append((class_name,skill.get("name"),cd))
            elif cd!=0:
                errors.append(f"{class_name}/{skill.get('name')}: cooldown={cd}")
    return {"version":"1.11.40","checked":checked,"exceptions":exceptions,
            "error_count":len(errors),"errors":errors}

SKILL_COOLDOWN_AUDIT_V11140=_skill_cooldown_audit_v11140()
if SKILL_COOLDOWN_AUDIT_V11140["error_count"]:
    raise RuntimeError("Global Skill Cooldown Audit v1.11.40 failed: "+
                       "; ".join(SKILL_COOLDOWN_AUDIT_V11140["errors"][:50]))


# v1.11.96: every class must remain capable of late-game combat through its
# own stat identity. Character Level is not a substitute for trained stats.
_ENDGAME_OFFENSIVE_KINDS_V11196 = {"damage", "aoe_damage", "execute", "drain"}
_CLASS_OFFENSIVE_SCALES_V11196 = {
    "Wojownik": {"strength"},
    "Berserker": {"strength"},
    "Łotrzyk": {"dexterity"},
    "Łowca": {"dexterity"},
    "Mnich": {"dexterity"},
    "Strażnik": {"strength"},
    "Mag": {"intelligence"},
    "Nekromanta": {"intelligence"},
    "Kapłan": {"intelligence"},
    "Czarownik": {"intelligence"},
    "Druid": {"intelligence"},
    "Psionik": {"intelligence"},
    # Mec intentionally supports all five combat branches.
    "Mec": {"strength", "dexterity", "intelligence", "willpower", "constitution"},
    "Inżynier": {"dexterity"},
}


def _all_class_endgame_damage_audit_v11196():
    errors = []
    report = {}
    endgame_unlock = min(180, CLASS_MASTERY_MAX_LEVEL)
    for class_name, allowed_scales in _CLASS_OFFENSIVE_SCALES_V11196.items():
        skills = tuple(CLASS_SKILLS.get(class_name, ()))
        offensive = [
            skill for skill in skills
            if str(skill.get("kind", "")) in _ENDGAME_OFFENSIVE_KINDS_V11196
        ]
        endgame = [
            skill for skill in offensive
            if int(skill.get("unlock", 1) or 1) >= endgame_unlock
        ]
        if not offensive:
            errors.append(f"{class_name}: brak ofensywnych umiejętności")
        if not endgame:
            errors.append(
                f"{class_name}: brak ofensywnej umiejętności endgame od Biegłości {endgame_unlock}"
            )
        bad = []
        for skill in endgame:
            scale = str(skill.get("scale", "") or "").strip().lower()
            if not scale:
                bad.append(f"{skill.get('name', skill.get('id', '?'))}: brak scale")
                continue
            if scale not in allowed_scales:
                bad.append(
                    f"{skill.get('name', skill.get('id', '?'))}: scale={scale}, "
                    f"dozwolone={sorted(allowed_scales)}"
                )
        if bad:
            errors.extend(f"{class_name}: {row}" for row in bad)
        report[class_name] = {
            "offensive": len(offensive),
            "endgame": len(endgame),
            "allowed_scales": tuple(sorted(allowed_scales)),
            "top_unlock": max((int(skill.get("unlock", 1) or 1) for skill in offensive), default=0),
        }
    return {
        "version": "1.11.96",
        "classes": len(_CLASS_OFFENSIVE_SCALES_V11196),
        "report": report,
        "error_count": len(errors),
        "errors": errors,
    }


ALL_CLASS_ENDGAME_DAMAGE_AUDIT_V11196 = _all_class_endgame_damage_audit_v11196()
if ALL_CLASS_ENDGAME_DAMAGE_AUDIT_V11196["error_count"]:
    raise RuntimeError(
        "All Class Endgame Damage Audit v1.11.96 failed: "
        + "; ".join(ALL_CLASS_ENDGAME_DAMAGE_AUDIT_V11196["errors"][:80])
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
from data.rooms import ROOMS
