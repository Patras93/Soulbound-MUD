from core.legacy_function_binding_v410 import bind_legacy_function_v410 as _sb410_bind

import core.v410_mec_mastery as _sb410_mod_v410_mec_mastery
import core.v410_class_skill_audits as _sb410_mod_v410_class_skill_audits

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


# v4.00.1: class skill dictionaries live in their own declarative module.
# v4.00.2: Each evaluation of the legacy facade must own independent skill
# dictionaries. Audits sometimes re-execute this file in the same process;
# reusing an imported mutable catalog used to append duplicate master skills.
from copy import deepcopy as _deepcopy_skill_catalog_v402
from core.class_skill_catalog import (
    CLASS_SKILLS as _AUTHORED_CLASS_SKILLS_V402,
    ENDGAME_CLASS_SKILLS as _AUTHORED_ENDGAME_CLASS_SKILLS_V402,
)
CLASS_SKILLS = _deepcopy_skill_catalog_v402(_AUTHORED_CLASS_SKILLS_V402)
ENDGAME_CLASS_SKILLS = _deepcopy_skill_catalog_v402(_AUTHORED_ENDGAME_CLASS_SKILLS_V402)

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


def _make_soul_grid_skill(*args, **kwargs):
    """Compatibility entrypoint; rebound to the unchanged native implementation."""
    raise RuntimeError("Unbound native function: _make_soul_grid_skill")
_make_soul_grid_skill = _sb410_bind(_sb410_mod_v410_class_skill_audits._make_soul_grid_skill, globals())


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
    (620, "Płomień Nowej Ery"), (640, "Sąd Żywych Gwiazd"),
    (660, "Korona Nieskończonych Ścieżek"), (680, "Brama Wiecznej Chwały"),
    (700, "Pradawne Dziedzictwo"), (720, "Oko Niebiańskich Władców"),
    (740, "Tron Wiecznej Potęgi"), (760, "Ostatnie Przebudzenie"),
    (780, "Dziedzictwo Kosmicznej Duszy"), (800, "Absolut Przyszłości"),
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


def _v0922_alt_skill(*args, **kwargs):
    """Compatibility entrypoint; rebound to the unchanged native implementation."""
    raise RuntimeError("Unbound native function: _v0922_alt_skill")
_v0922_alt_skill = _sb410_bind(_sb410_mod_v410_class_skill_audits._v0922_alt_skill, globals())


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
_V03014_SKILL_TITLES += (
    "Sąd Przebudzonych", "Łuna Nowej Ery", "Tron Północnych Gwiazd",
    "Wieczna Przystań", "Zew Siedmiu Światów", "Żywy Kryształ",
    "Wicher Przeznaczenia", "Serce Pradawnych", "Złoty Brzask",
    "Pieczęć Odrodzenia", "Gniew Wiecznej Zorzy", "Śpiew Galaktyk",
    "Korona Tysiąca Bram", "Brama Nowej Duszy", "Ognisty Horyzont",
    "Przysięga Nieśmiertelnych", "Wieczny Ślad", "Pradawny Próg",
    "Wrota Nieskończoności", "Zwycięstwo Nowej Ery",
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

def _v0310_build_tech_class_skills(*args, **kwargs):
    """Compatibility entrypoint; rebound to the unchanged native implementation."""
    raise RuntimeError("Unbound native function: _v0310_build_tech_class_skills")
_v0310_build_tech_class_skills = _sb410_bind(_sb410_mod_v410_class_skill_audits._v0310_build_tech_class_skills, globals())

_v0310_build_tech_class_skills()

# v0.31.9: Full authored Mec kit based on the user-provided UOSSMUD ability list.
# Source Base AP is an AP/learning cost from UOSS, NOT an attack-power value.
# Soulbound stores it only as source_ap_cost metadata; combat power comes from
# Soul Power, effective stats/EQ, Skill Level, protocols and authored mechanics.
def _v0319_install_full_mec_kit(*args, **kwargs):
    """Compatibility entrypoint; rebound to the unchanged native implementation."""
    raise RuntimeError("Unbound native function: _v0319_install_full_mec_kit")
_v0319_install_full_mec_kit = _sb410_bind(_sb410_mod_v410_mec_mastery._v0319_install_full_mec_kit, globals())

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
def _mec_contract_audit_v11149(*args, **kwargs):
    """Compatibility entrypoint; rebound to the unchanged native implementation."""
    raise RuntimeError("Unbound native function: _mec_contract_audit_v11149")
_mec_contract_audit_v11149 = _sb410_bind(_sb410_mod_v410_mec_mastery._mec_contract_audit_v11149, globals())
MEC_CONTRACT_AUDIT_V11149=_mec_contract_audit_v11149()


# v0.31.7: authored Engineer tool kit based on the user-provided UOSSMUD list.
# Source Base AP means AP/learning points in UOSS. It is metadata only here and
# must never be reused as combat power. Soulbound damage is driven by stats/EQ,
# Soul Power, Skill Level, Upgrade/passives and each tool's authored mechanics.
def _v0317_install_engineer_toolkit(*args, **kwargs):
    """Compatibility entrypoint; rebound to the unchanged native implementation."""
    raise RuntimeError("Unbound native function: _v0317_install_engineer_toolkit")
_v0317_install_engineer_toolkit = _sb410_bind(_sb410_mod_v410_mec_mastery._v0317_install_engineer_toolkit, globals())

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

def _v03014_unique_generated_skill_names(*args, **kwargs):
    """Compatibility entrypoint; rebound to the unchanged native implementation."""
    raise RuntimeError("Unbound native function: _v03014_unique_generated_skill_names")
_v03014_unique_generated_skill_names = _sb410_bind(_sb410_mod_v410_class_skill_audits._v03014_unique_generated_skill_names, globals())


V03014_SKILLS_RENAMED, V03014_OLD_NAME_ALIASES = _v03014_unique_generated_skill_names()

# v1.28.0: replace generated placeholder numbers on high Warrior masteries
# without changing spell IDs, mechanics or previous command aliases.
def _v1280_warrior_high_mastery_names():
    titles = {level: _V03014_SKILL_TITLES[i] for i, level in enumerate(_V0922_MASTERY_LEVELS)}
    updated = 0
    for sk in CLASS_SKILLS["Wojownik"]:
        sid = str(sk.get("id", ""))
        match = re.search(r"^v0922_warrior_grid_(\d+)_(\d+)$", sid)
        if not match or int(match.group(1)) <= 600:
            continue
        level, number = int(match.group(1)), int(match.group(2))
        prefixes = ("Zamach Odpowiedzi", "Przecięcie Gardy", "Przysięga")
        prefix = prefixes[(number-1) % 3]
        name = f"{prefix}: {titles[level]} Wojownika"
        old = sk.get("name", "")
        sk["aliases"] = list(dict.fromkeys(list(sk.get("aliases") or ()) + [str(old), name]))
        sk["name"] = name
        updated += 1
    return updated

V1280_WARRIOR_NAMES = _v1280_warrior_high_mastery_names()



def _v03014_skill_name_audit(*args, **kwargs):
    """Compatibility entrypoint; rebound to the unchanged native implementation."""
    raise RuntimeError("Unbound native function: _v03014_skill_name_audit")
_v03014_skill_name_audit = _sb410_bind(_sb410_mod_v410_class_skill_audits._v03014_skill_name_audit, globals())


# The generator later redistributes unlock numbers, but it does not change names.
# A second final audit is executed near the bottom of the file after Generator Core.
V03014_SKILL_NAME_AUDIT_PREGEN = _v03014_skill_name_audit()

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

# v3.20.0 — true learnable class mastery skills. Existing class trainers and
# automatic queues use the canonical CLASS_SKILLS catalogue; no replacement of
# old skills, levels, class names, effects, or SQLite data.
_MASTER_ARTS_V3200 = {
    'Wojownik': ('Przełamanie Korony', 'Szarża Stu Sztandarów', 'Przysięga Twardej Stali'),
    'Berserker': ('Krwawa Kometa', 'Huragan Gniewu', 'Ryk Ostatniej Bitwy'),
    'Łotrzyk': ('Cięcie Tysiąca Cieni', 'Noc Ostrzy', 'Maska Doskonałego Ataku'),
    'Łowca': ('Strzała Spadającej Gwiazdy', 'Grad Strzał Dziczy', 'Instynkt Mistrza Tropu'),
    'Mnich': ('Uderzenie Pustej Dłoni', 'Fala Duchowej Energii', 'Medytacja Siedmiu Bram'),
    'Strażnik': ('Gromowy Cios Bastionu', 'Fala Żelaznej Obrony', 'Niezłomna Przysięga'),
    'Mag': ('Złamanie Zaklęcia Eonów', 'Burza Dziewięciu Sfer', 'Koncentracja Arkana'),
    'Nekromanta': ('Dotyk Wiecznego Milczenia', 'Taniec Dusz Przodków', 'Rytuał Czarnego Znaku'),
    'Kapłan': ('Sąd Świetlistego Kręgu', 'Światło na Wszystkich Wrogów', 'Modlitwa Nieśmiertelnych'),
    'Czarownik': ('Pieśń Otchłani', 'Rozdarcie Przestworzy', 'Pakt Bez Imienia'),
    'Druid': ('Korzeń Pierwszego Drzewa', 'Zew Starej Puszczy', 'Przymierze Dziczy'),
    'Psionik': ('Pęknięcie Rzeczywistości', 'Kaskada Wspomnień', 'Skupienie Siedmiu Myśli'),
    'Mec': ('Działo Wszechświata', 'Orbitalna Salwa Meca', 'Przeciążenie Reaktora'),
    'Inżynier': ('Precyzyjna Detonacja', 'Salwa Nanomechanizmów', 'Hiperkalibracja'),
}
for _master_class, _master_kind, *_ in CLASSES:
    _one, _many, _focus = _MASTER_ARTS_V3200[_master_class]
    _magic = _master_kind == 'magic'
    _scale = ('intelligence' if _magic else 'dexterity' if _master_class in ('Łotrzyk', 'Łowca', 'Mnich', 'Inżynier') else 'strength')
    _prefix = 'v3200_'+_master_class.lower()
    CLASS_SKILLS.setdefault(_master_class, []).extend((
        {'id':_prefix+'_signature','name':_one,'aliases':[_one.lower()],
         'natural_tags':['mistrzostwo','precyzyjny','legenda'],
         'unlock':260,'kind':'damage','cooldown':12,'mana':42 if _magic else 0,
         'desc':'Mistrzowski atak skupiony na jednym celu; skaluje się ze statystyką klasy.',
         'scale':_scale,'mult':3.15},
        {'id':_prefix+'_area','name':_many,'aliases':[_many.lower()],
         'natural_tags':['mistrzostwo','aoe','obszar'],
         'unlock':420,'kind':'aoe_damage','cooldown':18,'mana':62 if _magic else 0,
         'desc':'Mistrzowski atak obszarowy na wszystkich dostępnych wrogów w pokoju.',
         'scale':_scale,'mult':2.60},
        {'id':_prefix+'_focus','name':_focus,'aliases':[_focus.lower()],
         'natural_tags':['mistrzostwo','wzmocnienie'],
         'unlock':600,'kind':'boost','cooldown':25,'mana':48 if _magic else 0,
         'desc':'Wzmocnienie mistrzostwa zwiększa moc kolejnych umiejętności.',
         'boost':1.50,'duration':14},
    ))




# v5.00.0: true learnable class skills through the existing trainers/queue.
from core.class_mastery_v5000 import install as _install_class_mastery_v5000
V5000_MASTER_ARTS = _install_class_mastery_v5000(CLASS_SKILLS, CLASSES)

# Czytelna kolejność dla skills, nauczycieli i Kodeksu Klasowego.
for _class_name in CLASS_SKILLS:
    CLASS_SKILLS[_class_name].sort(
        key=lambda skill: (int(skill.get("unlock", 1)), skill.get("name", ""))
    )


# v1.13.30: a passive is state, not an activated combat button. Older shared
# skill constructors could leave a normal cooldown on passive rows (notably
# technology toolkits). Normalize the semantic contract after all class rows
# are assembled, while preserving every passive's authored effect fields.
V11330_AUTOMATIC_PASSIVES_NORMALIZED = 0
for _class_name, _skills in CLASS_SKILLS.items():
    for _skill in _skills:
        if str(_skill.get("kind", "")).strip().lower() != "passive":
            continue
        if int(_skill.get("cooldown", 0) or 0) != 0 or not bool(_skill.get("automatic")):
            V11330_AUTOMATIC_PASSIVES_NORMALIZED += 1
        _skill["cooldown"] = 0
        _skill["automatic"] = True
        _skill.setdefault("target_mode", "passive")


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


def _all_class_skill_target_audit_v11196(*args, **kwargs):
    """Compatibility entrypoint; rebound to the unchanged native implementation."""
    raise RuntimeError("Unbound native function: _all_class_skill_target_audit_v11196")
_all_class_skill_target_audit_v11196 = _sb410_bind(_sb410_mod_v410_class_skill_audits._all_class_skill_target_audit_v11196, globals())


ALL_CLASS_SKILL_TARGET_AUDIT_V11196=_all_class_skill_target_audit_v11196()


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


def _priest_healing_contract_audit_v11196(*args, **kwargs):
    """Compatibility entrypoint; rebound to the unchanged native implementation."""
    raise RuntimeError("Unbound native function: _priest_healing_contract_audit_v11196")
_priest_healing_contract_audit_v11196 = _sb410_bind(_sb410_mod_v410_class_skill_audits._priest_healing_contract_audit_v11196, globals())


PRIEST_HEALING_CONTRACT_AUDIT_V11196 = _priest_healing_contract_audit_v11196()


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



# v1.11.40 / v1.13.30: global no-cooldown policy.
# Every class skill has zero ordinary reuse cooldown. Timed effects, V-MAX
# duration and Overheat/reboot are separate mechanics and must never be exposed
# or enforced as a skill reuse cooldown.
SPECIAL_MECHANIC_COOLDOWN_IDS_V11140 = set()
for _class_name, _skills in CLASS_SKILLS.items():
    for _skill in _skills:
        _skill["cooldown"]=0
        _skill.pop("mechanic_cooldown", None)

def _skill_cooldown_audit_v11140():
    errors=[]
    checked=0
    exceptions=[]
    for class_name,skills in CLASS_SKILLS.items():
        for skill in skills:
            checked+=1
            cd=int(skill.get("cooldown",0) or 0)
            if cd!=0:
                errors.append(f"{class_name}/{skill.get('name')}: cooldown={cd}")
            if skill.get("mechanic_cooldown"):
                errors.append(f"{class_name}/{skill.get('name')}: mechanic cooldown flag present")
    return {"version":"1.13.30","checked":checked,"exceptions":exceptions,
            "error_count":len(errors),"errors":errors}

SKILL_COOLDOWN_AUDIT_V11140=_skill_cooldown_audit_v11140()


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


def _all_class_endgame_damage_audit_v11196(*args, **kwargs):
    """Compatibility entrypoint; rebound to the unchanged native implementation."""
    raise RuntimeError("Unbound native function: _all_class_endgame_damage_audit_v11196")
_all_class_endgame_damage_audit_v11196 = _sb410_bind(_sb410_mod_v410_class_skill_audits._all_class_endgame_damage_audit_v11196, globals())


ALL_CLASS_ENDGAME_DAMAGE_AUDIT_V11196 = _all_class_endgame_damage_audit_v11196()


def all_class_gamefeel_audit_v11330(*args, **kwargs):
    """Compatibility entrypoint; rebound to the unchanged native implementation."""
    raise RuntimeError("Unbound native function: all_class_gamefeel_audit_v11330")
all_class_gamefeel_audit_v11330 = _sb410_bind(_sb410_mod_v410_class_skill_audits.all_class_gamefeel_audit_v11330, globals())


ALL_CLASS_GAMEFEEL_AUDIT_V11330 = all_class_gamefeel_audit_v11330()

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

# v9.00.0: additive classes/races only after legacy class-skill migrations.
from systems.new_heroes_v900 import register_classes as _register_new_heroes_v900
_register_new_heroes_v900(globals())

# v11.00.0: native techniques learned through existing trainers, without resets.
from core.class_mastery_v1100 import install as _install_class_mastery_v1100
V1100_CLASS_TECHNIQUES = _install_class_mastery_v1100(CLASS_SKILLS, CLASSES)


# v11.00.10 — all 22 classes: replace repeated generic mastery titles with
# authored, class/skill-kind appropriate names. IDs, aliases and stats stable.
from core.unique_skill_names_v1110 import install as _install_unique_skill_names_v1110
V1110_UNIQUE_SKILL_NAMES = _install_unique_skill_names_v1110(CLASS_SKILLS)
