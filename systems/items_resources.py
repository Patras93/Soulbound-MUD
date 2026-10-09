from data import catalog_mutations as _catalog_mut
import math
from core.profession_drop_rates_v1149 import resource_variant_chances_v1149, mining_vein_chances_v1149
import random
ENDGAME_PROFESSION_ITEMS = {
    # Ryby endgame - Rzeka
    "soulfin_trout": {"name": "Pstrąg Duszopłetwy", "type": "resource", "price": None, "sell_gold": 25, "desc": "Rzadka ryba rzeczna. Wędka level 100+."},
    "runic_sturgeon": {"name": "Jesiotr Runiczny", "type": "resource", "price": None, "sell_gold": 45, "desc": "Runiczny jesiotr. Wędka level 140+."},
    "chrono_eel": {"name": "Węgorz Czasu", "type": "resource", "price": None, "sell_gold": 80, "desc": "Niezwykły węgorz. Wędka level 180+."},
    "eternal_salmon": {"name": "Wieczny Łosoś", "type": "resource", "price": None, "sell_gold": 140, "desc": "Mityczny rzeczny połów. Wędka level 200."},

    # Jezioro
    "crystal_carp": {"name": "Kryształowy Karp", "type": "resource", "price": None, "sell_gold": 25, "desc": "Karp o kryształowych łuskach. Wędka level 100+."},
    "moon_pike": {"name": "Księżycowy Szczupak", "type": "resource", "price": None, "sell_gold": 45, "desc": "Rzadka jeziorowa ryba. Wędka level 140+."},
    "starfin_char": {"name": "Gwiezdnopłetwy Golec", "type": "resource", "price": None, "sell_gold": 80, "desc": "Magiczna ryba jeziorowa. Wędka level 180+."},
    "mirror_leviathan": {"name": "Lustrzany Lewiatan", "type": "resource", "price": None, "sell_gold": 150, "desc": "Legendarny mieszkaniec jeziora. Wędka level 200."},

    # Morze
    "storm_cod": {"name": "Sztormowy Dorsz", "type": "resource", "price": None, "sell_gold": 28, "desc": "Ryba nasycona energią sztormu. Wędka level 100+."},
    "abyss_halibut": {"name": "Halibut Otchłani", "type": "resource", "price": None, "sell_gold": 50, "desc": "Głębinowa ryba morska. Wędka level 140+."},
    "void_turbot": {"name": "Turbot Pustki", "type": "resource", "price": None, "sell_gold": 90, "desc": "Mroczny połów morski. Wędka level 180+."},
    "crown_monkfish": {"name": "Koronna Żabnica", "type": "resource", "price": None, "sell_gold": 160, "desc": "Mityczna żabnica. Wędka level 200."},

    # Ocean - po jednym odblokowaniu na każdy próg 100-200
    "celestial_tuna": {"name": "Niebiański Tuńczyk", "type": "resource", "price": None, "sell_gold": 30, "desc": "Oceaniczny połów. Wędka level 100+."},
    "dragon_mahi": {"name": "Smocze Mahi-mahi", "type": "resource", "price": None, "sell_gold": 40, "desc": "Rzadka ryba oceaniczna. Wędka level 120+."},
    "abyss_tuna": {"name": "Tuńczyk Otchłani", "type": "resource", "price": None, "sell_gold": 55, "desc": "Głębinowy tuńczyk. Wędka level 140+."},
    "storm_marlin": {"name": "Marlin Burzy", "type": "resource", "price": None, "sell_gold": 75, "desc": "Potężny marlin. Wędka level 160+."},
    "moon_leviathan": {"name": "Księżycowy Lewiatan", "type": "resource", "price": None, "sell_gold": 110, "desc": "Olbrzymi oceaniczny połów. Wędka level 180+."},
    "eternal_coelacanth": {"name": "Wieczna Latimeria", "type": "resource", "price": None, "sell_gold": 200, "desc": "Najrzadsza ryba oceanu. Wędka level 200."},

    # Rudy 100-200
    "cobalt_ore": {"name": "Ruda Kobaltu", "type": "resource", "price": None, "sell_gold": 18, "desc": "Ruda dostępna od Kilofa level 100."},
    "runestone_ore": {"name": "Ruda Kamienia Runicznego", "type": "resource", "price": None, "sell_gold": 28, "desc": "Ruda dostępna od Kilofa level 120."},
    "dragonsteel_ore": {"name": "Ruda Smoczej Stali", "type": "resource", "price": None, "sell_gold": 42, "desc": "Ruda dostępna od Kilofa level 140."},
    "astral_ore": {"name": "Ruda Astralna", "type": "resource", "price": None, "sell_gold": 65, "desc": "Ruda dostępna od Kilofa level 160."},
    "void_ore": {"name": "Ruda Pustki", "type": "resource", "price": None, "sell_gold": 100, "desc": "Ruda dostępna od Kilofa level 180."},
    "eternium_ore": {"name": "Ruda Eternium", "type": "resource", "price": None, "sell_gold": 180, "desc": "Najrzadsza ruda. Kilof level 200."},

    # Drewno 100-200
    "runewood_log": {"name": "Pień Runicznego Drzewa", "type": "resource", "price": None, "sell_gold": 18, "desc": "Drewno Głębi Gaju. Piła level 100+."},
    "dragonwood_log": {"name": "Pień Smoczego Drzewa", "type": "resource", "price": None, "sell_gold": 28, "desc": "Drewno Głębi Gaju. Piła level 120+."},
    "astralwood_log": {"name": "Pień Astralnego Drzewa", "type": "resource", "price": None, "sell_gold": 42, "desc": "Drewno Głębi Gaju. Piła level 140+."},
    "voidwood_log": {"name": "Pień Drzewa Pustki", "type": "resource", "price": None, "sell_gold": 65, "desc": "Drewno Głębi Gaju. Piła level 160+."},
    "starheart_log": {"name": "Pień Gwiezdnego Serca", "type": "resource", "price": None, "sell_gold": 100, "desc": "Drewno Głębi Gaju. Piła level 180+."},
    "eternal_worldwood_log": {"name": "Pień Wiecznego Drzewa Świata", "type": "resource", "price": None, "sell_gold": 180, "desc": "Najrzadsze drewno. Piła level 200."},

    # Zioła 100-200
    "sunfire_bloom": {"name": "Kwiat Słonecznego Ognia", "type": "resource", "price": None, "sell_gold": 18, "desc": "Zioło Głębi Gaju. Sierp level 100+."},
    "dragon_sage": {"name": "Smocza Szałwia", "type": "resource", "price": None, "sell_gold": 28, "desc": "Zioło Głębi Gaju. Sierp level 120+."},
    "astral_orchid": {"name": "Astralna Orchidea", "type": "resource", "price": None, "sell_gold": 42, "desc": "Zioło Głębi Gaju. Sierp level 140+."},
    "void_lotus": {"name": "Lotos Pustki", "type": "resource", "price": None, "sell_gold": 65, "desc": "Zioło Głębi Gaju. Sierp level 160+."},
    "phoenix_crown": {"name": "Korona Feniksa", "type": "resource", "price": None, "sell_gold": 100, "desc": "Zioło Głębi Gaju. Sierp level 180+."},
    "eternal_blossom": {"name": "Wieczny Kwiat", "type": "resource", "price": None, "sell_gold": 180, "desc": "Najrzadsze zioło. Sierp level 200."},

    # Rzemiosło 100-200
    "runic_guard_charm": {"name": "Runiczny Talizman Straży", "type": "armor", "slot": "charm", "defense": 6, "price": None, "rarity": "crafted", "rarity_name": "Rzemieślniczy", "affix": "constitution", "affix_amount": 2, "desc": "Endgame Rzemiosło level 100. Obrona +6, Kondycja +2."},
    "dragonforge_charm": {"name": "Talizman Smoczej Kuźni", "type": "armor", "slot": "charm", "defense": 7, "price": None, "rarity": "crafted", "rarity_name": "Rzemieślniczy", "affix": "strength", "affix_amount": 3, "desc": "Endgame Rzemiosło level 120. Obrona +7, Siła +3."},
    "astral_forge_charm": {"name": "Astralny Talizman Kuźni", "type": "armor", "slot": "charm", "defense": 8, "price": None, "rarity": "crafted", "rarity_name": "Rzemieślniczy", "affix": "intelligence", "affix_amount": 3, "desc": "Endgame Rzemiosło level 140. Obrona +8, Inteligencja +3."},
    "void_guard_charm": {"name": "Talizman Straży Pustki", "type": "armor", "slot": "charm", "defense": 9, "price": None, "rarity": "crafted", "rarity_name": "Rzemieślniczy", "affix": "willpower", "affix_amount": 4, "desc": "Endgame Rzemiosło level 160. Obrona +9, Siła Woli +4."},
    "worldheart_charm": {"name": "Talizman Serca Świata", "type": "armor", "slot": "charm", "defense": 10, "price": None, "rarity": "crafted", "rarity_name": "Rzemieślniczy", "affix": "hp", "affix_amount": 60, "desc": "Endgame Rzemiosło level 180. Obrona +10, HP +60."},
    "eternal_soul_charm": {"name": "Talizman Wiecznej Duszy", "type": "armor", "slot": "charm", "defense": 12, "price": None, "rarity": "crafted", "rarity_name": "Rzemieślniczy", "affix": "dexterity", "affix_amount": 5, "desc": "Endgame Rzemiosło level 200. Obrona +12, Zręczność +5."},

    # Gotowanie 100-200
    "runic_fish_plate": {"name": "Runiczny Półmisek Rybny", "type": "consumable", "price": None, "heal": 120, "mana": 40, "desc": "Gotowanie level 100. Przywraca do 120 HP i 40 Many."},
    "dragon_ocean_stew": {"name": "Smocza Potrawka Oceaniczna", "type": "consumable", "price": None, "heal": 135, "mana": 55, "desc": "Gotowanie level 120. Przywraca do 135 HP i 55 Many."},
    "abyss_fish_steak": {"name": "Stek Rybny Otchłani", "type": "consumable", "price": None, "heal": 155, "mana": 75, "desc": "Gotowanie level 140. Przywraca do 155 HP i 75 Many."},
    "storm_marlin_feast": {"name": "Uczta Marlina Burzy", "type": "consumable", "price": None, "heal": 180, "mana": 95, "desc": "Gotowanie level 160. Przywraca do 180 HP i 95 Many."},
    "leviathan_banquet": {"name": "Uczta Lewiatana", "type": "consumable", "price": None, "heal": 210, "mana": 120, "desc": "Gotowanie level 180. Przywraca do 210 HP i 120 Many."},
    "eternal_ocean_banquet": {"name": "Wieczna Uczta Oceanu", "type": "consumable", "price": None, "heal": 260, "mana": 160, "desc": "Gotowanie level 200. Przywraca do 260 HP i 160 Many."},

    # Alchemia 100-200
    "supreme_healing_potion": {"name": "Najwyższa Mikstura Leczenia", "type": "consumable", "price": None, "heal": 130, "desc": "Alchemia level 100. Przywraca do 130 HP."},
    "supreme_mana_potion": {"name": "Najwyższa Mikstura Many", "type": "consumable", "price": None, "mana": 130, "desc": "Alchemia level 120. Przywraca do 130 Many."},
    "grand_vitality_elixir": {"name": "Wielki Eliksir Witalności", "type": "consumable", "price": None, "heal": 120, "mana": 80, "desc": "Alchemia level 140. Przywraca do 120 HP i 80 Many."},
    "soul_tonic": {"name": "Tonik Duszy", "type": "consumable", "price": None, "soul_xp": 180, "desc": "Alchemia level 160. Daje 180 Soul XP."},
    "astral_restoration_elixir": {"name": "Astralny Eliksir Odnowy", "type": "consumable", "price": None, "heal": 180, "mana": 120, "desc": "Alchemia level 180. Przywraca do 180 HP i 120 Many."},
    "eternal_soul_elixir": {"name": "Eliksir Wiecznej Duszy", "type": "consumable", "price": None, "soul_xp": 400, "desc": "Alchemia level 200. Daje 400 Soul XP."},
}
_catalog_mut.catalog_update_path('ITEMS', ITEMS, (), ENDGAME_PROFESSION_ITEMS)

# Kanoniczny Moogle Board. Jedyny Moogle Board w katalogu:
# nagroda Black Rabite dla Cyborga oraz pozycja sklepu Moogle Steel.
_catalog_mut.catalog_assign({
    "name": "Moogle Board",
    "type": "armor",
    "slot": "board",
    "defense": 0,
    "price": None,
    "required_level": 150,
    "required_race": "Cyborg",
    "rarity": "cyborg",
    "rarity_name": "Cyborg",
    "stats": {},
    "source_item_type": "Board",
    "cyborg_board_scaling": "character_level",
    "fur_shop_gold_cost": 5000000,
    "fur_shop_token": "uoss_moogle_steel",
    "fur_shop_token_cost": 3,
    "desc": "Moogle Board — unikalna nagroda Black Rabite dla Cyborga. Na Levelu 150 daje +20 do pięciu głównych statystyk; od 151 rośnie o +2 za każdy Level.",
}, 'ITEMS', ITEMS, ("moogle_board",))

_PROGRESSION_400_NAMES = {
    220: "Przebudzenia", 240: "Transcendencji", 260: "Horyzontu",
    280: "Otchłani", 300: "Gwiezdnego Rdzenia", 320: "Pierwotności",
    340: "Nieskończoności", 360: "Korony Świata",
    380: "Ponadczasowy", 400: "Absolutu",
    420: "Przekroczenia", 440: "Gwiezdnego Tronu", 460: "Wiecznego Echa",
    480: "Serca Otchłani", 500: "Korony Gwiazd", 520: "Sądu Horyzontu",
    540: "Kosmicznego Szlaku", 560: "Wieczności",
    580: "Apogeum", 600: "Absolutu Duszy",
}
_FISH_400_LABELS = {
    "river": "Rzeczny Wędrowiec", "lake": "Jeziorny Strażnik",
    "sea": "Morski Władca", "ocean": "Oceaniczny Lewiatan",
}
for _level in PROGRESSION_400_LEVELS:
    _suffix = _PROGRESSION_400_NAMES[_level]
    _sell = 190 + ((_level - 200) // 20) * 11
    _catalog_mut.catalog_assign({
        "name": f"Ruda {_suffix}", "type": "resource", "price": None,
        "sell_gold": _sell,
        "desc": f"Ruda progresji 201-600. Kilof level {_level}+.",
    }, 'ITEMS', ITEMS, (f"ore_400_{_level}",))
    _catalog_mut.catalog_assign({
        "name": f"Pień {_suffix}", "type": "resource", "price": None,
        "sell_gold": _sell,
        "desc": f"Drewno progresji 201-600. Piła level {_level}+.",
    }, 'ITEMS', ITEMS, (f"wood_400_{_level}",))
    _catalog_mut.catalog_assign({
        "name": f"Ziele {_suffix}", "type": "resource", "price": None,
        "sell_gold": _sell,
        "desc": f"Zioło progresji 201-600. Sierp level {_level}+.",
    }, 'ITEMS', ITEMS, (f"herb_400_{_level}",))
    for _habitat, _label in _FISH_400_LABELS.items():
        _catalog_mut.catalog_assign({
            "name": f"{_label} {_suffix}", "type": "resource", "price": None,
            "sell_gold": _sell,
            "desc": f"Ryba progresji 201-600. Wędka level {_level}+.",
        }, 'ITEMS', ITEMS, (f"fish_400_{_habitat}_{_level}",))

_register_world_resource_items()

# v0.8.43: jednorazowe przedmioty z samouczka Archiwisty Sola.
_catalog_mut.catalog_update_path('ITEMS', ITEMS, (), {
    "sol_smith_package": {
        "name": "Paczka Archiwisty dla Kowala",
        "type": "quest", "price": None,
        "desc": "Zapieczętowana paczka Archiwisty Sola. Dostarcz ją Kowalowi Doranowi.",
    },
    "sol_inn_letter": {
        "name": "List Archiwisty do Karczmarki",
        "type": "quest", "price": None,
        "desc": "Krótki list Archiwisty Sola. Dostarcz go Karczmarce Elii.",
    },
    "sol_guard_report": {
        "name": "Meldunek Archiwisty dla Straży",
        "type": "quest", "price": None,
        "desc": "Zapieczętowany meldunek. Dostarcz go Dowódcy Roderikowi.",
    },
    "sol_herbal_notes": {
        "name": "Notatki Archiwisty dla Zielarki",
        "type": "quest", "price": None,
        "desc": "Notatki o florze Gaju Szeptów. Dostarcz je Zielarce Mirze.",
    },
})

# v1.13.17: wspólna krzywa ekonomii mieszka w core/economy_curve.py.
from core.economy_curve import (
    V11314_ECONOMY_STAGE_ANCHORS,
    economy_stage_anchor_v11314,
)


def class_equipment_shop_price_v11314(level, slot_base_price):
    """Cena klasowego EQ jako znaczący, ale osiągalny wydatek."""
    level = max(1, min(600, int(level or 1)))
    base_price = max(1, int(slot_base_price or 1))
    slot_factor = max(0.55, min(1.65, base_price / 130.0))
    target = int(round(
        economy_stage_anchor_v11314(level) * 0.50 * slot_factor
    ))
    return max(base_price, target)


# v1.13.8: wspólna skala jakości EQ dla sklepu, craftingu i dropów.
# Źródła mają różne profile, ale sprzęt z tego samego etapu nie może dzielić
# przepaść typu "sklep 30 statów, drop 3 staty".
def equipment_progression_budget_v1138(level):
    level = max(1, min(600, int(level or 1)))
    anchors = (
        (1, 9), (10, 14), (20, 19), (30, 25), (40, 31),
        (50, 38), (60, 48), (70, 58), (80, 70), (90, 82),
        (100, 100), (150, 160), (200, 240), (300, 420),
        (400, 650), (500, 900), (600, 1200),
    )
    if level <= anchors[0][0]:
        return anchors[0][1]
    if level >= anchors[-1][0]:
        return anchors[-1][1]
    for (l0, b0), (l1, b1) in zip(anchors, anchors[1:]):
        if l0 <= level <= l1:
            ratio = (level - l0) / float(l1 - l0)
            return max(3, int(round(b0 + (b1 - b0) * ratio)))
    return anchors[-1][1]


def equipment_defense_step_v1138(level):
    level = max(1, min(600, int(level or 1)))
    anchors = (
        (1, 0), (10, 1), (20, 2), (30, 3), (40, 4),
        (50, 5), (60, 6), (70, 7), (80, 8), (90, 9),
        (100, 10), (150, 14), (200, 18), (300, 26),
        (400, 34), (500, 42), (600, 50),
    )
    if level <= anchors[0][0]:
        return anchors[0][1]
    if level >= anchors[-1][0]:
        return anchors[-1][1]
    for (l0, d0), (l1, d1) in zip(anchors, anchors[1:]):
        if l0 <= level <= l1:
            ratio = (level - l0) / float(l1 - l0)
            return max(0, int(round(d0 + (d1 - d0) * ratio)))
    return anchors[-1][1]


BLACKSMITH_TIERS = (
    {
        "key": "iron",
        "name": "Żelazny",
        "ore": "iron_ore",
        "ingot": "iron_ingot",
        "tool_level": 1,
        "profession_level": 1,
        "base_defense": 2,
    },
    {
        "key": "silver",
        "name": "Srebrny",
        "ore": "silver_ore",
        "ingot": "silver_ingot",
        "tool_level": 20,
        "profession_level": 20,
        "base_defense": 3,
    },
    {
        "key": "gold",
        "name": "Złoty",
        "ore": "gold_ore",
        "ingot": "gold_ingot",
        "tool_level": 40,
        "profession_level": 40,
        "base_defense": 4,
    },
    {
        "key": "cobalt",
        "name": "Kobaltowy",
        "ore": "cobalt_ore",
        "ingot": "cobalt_ingot",
        "tool_level": 100,
        "profession_level": 100,
        "base_defense": 6,
    },
    {
        "key": "runic",
        "name": "Runiczny",
        "ore": "runestone_ore",
        "ingot": "runestone_ingot",
        "tool_level": 120,
        "profession_level": 120,
        "base_defense": 7,
    },
    {
        "key": "dragonsteel",
        "name": "Smoczej Stali",
        "ore": "dragonsteel_ore",
        "ingot": "dragonsteel_ingot",
        "tool_level": 140,
        "profession_level": 140,
        "base_defense": 8,
    },
    {
        "key": "astral",
        "name": "Astralny",
        "ore": "astral_ore",
        "ingot": "astral_ingot",
        "tool_level": 160,
        "profession_level": 160,
        "base_defense": 9,
    },
    {
        "key": "void",
        "name": "Pustki",
        "ore": "void_ore",
        "ingot": "void_ingot",
        "tool_level": 180,
        "profession_level": 180,
        "base_defense": 10,
    },
    {
        "key": "eternium",
        "name": "Eternium",
        "ore": "eternium_ore",
        "ingot": "eternium_ingot",
        "tool_level": 200,
        "profession_level": 200,
        "base_defense": 12,
    },
)

BLACKSMITH_SLOT_DEFS = {
    "head": ("Hełm", 0, 3),
    "body": ("Pancerz", 3, 5),
    "hands": ("Rękawice", -1, 2),
    "legs": ("Nogawice", 1, 4),
    "feet": ("Buty", -1, 2),
    "charm": ("Talizman", -2, 2),
}

# v0.9.12: materiały Kowalstwa 220-600. Stare Tiery 1-200 zostają 1:1.
_BLACKSMITH_400_LABELS = {
    220: "Przebudzenia", 240: "Transcendencji", 260: "Horyzontu",
    280: "Otchłani", 300: "Gwiezdnego Rdzenia", 320: "Pierwotności",
    340: "Nieskończoności", 360: "Korony Świata",
    380: "Ponadczasowy", 400: "Absolutu",
    420: "Przekroczenia", 440: "Gwiezdnego Tronu", 460: "Wiecznego Echa",
    480: "Serca Otchłani", 500: "Korony Gwiazd", 520: "Sądu Horyzontu",
    540: "Kosmicznego Szlaku", 560: "Wieczności",
    580: "Apogeum", 600: "Absolutu Duszy",
}
BLACKSMITH_TIERS += tuple(
    {
        "key": f"p400_{level}",
        "name": _BLACKSMITH_400_LABELS[level],
        "ore": f"ore_400_{level}",
        "ingot": f"ingot_400_{level}",
        "tool_level": level,
        "profession_level": level,
        "base_defense": 12 + (level - 200) // 40,
    }
    for level in PROGRESSION_400_LEVELS
)

BLACKSMITH_MASTERWORK_STAT_PROFILE = {
    "head": ("willpower", "constitution"),
    "body": ("constitution", "willpower"),
    "hands": ("strength", "dexterity"),
    "legs": ("constitution", "dexterity"),
    "feet": ("dexterity", "constitution"),
    "charm": ("intelligence", "willpower"),
}

BLACKSMITH_MASTERWORK_PROPERTY = {
    "head": "magic_defense_pct",
    "body": "physical_defense_pct",
    "hands": "physical_damage_pct",
    "legs": "max_hp_pct",
    "feet": "dodge_pct",
    "charm": "magic_damage_pct",
}


def _blacksmith_masterwork_profile_v1138(level, slot):
    level = max(1, min(600, int(level or 1)))
    base_budget = equipment_progression_budget_v1138(level)
    stat_budget = max(2, int(round(base_budget * 0.65)))
    first, second = BLACKSMITH_MASTERWORK_STAT_PROFILE[slot]
    first_amount = max(1, int(round(stat_budget * 0.55)))
    second_amount = max(1, stat_budget - first_amount)
    stats = {first: first_amount, second: second_amount}

    prop = BLACKSMITH_MASTERWORK_PROPERTY[slot]
    prop_value = round(
        0.50 + 2.50 * ((level - 1) / 599.0) ** 0.80,
        2,
    )
    properties = {prop: prop_value}

    attack = 0
    magic_attack = 0
    if slot == "hands":
        attack = max(1, int(round(base_budget * 0.10)))
    elif slot == "feet":
        attack = max(0, int(round(base_budget * 0.04)))
    elif slot == "charm":
        magic_attack = max(1, int(round(base_budget * 0.10)))
    elif slot == "head":
        magic_attack = max(0, int(round(base_budget * 0.04)))

    if level >= 500:
        sockets = 5
    elif level >= 360:
        sockets = 4
    elif level >= 200:
        sockets = 3
    elif level >= 100:
        sockets = 2
    else:
        sockets = 1

    return {
        "stats": stats,
        "properties": properties,
        "attack": attack,
        "magic_attack": magic_attack,
        "sockets": sockets,
    }


def _register_blacksmith_items():
    extra_ingots = (
        ("cobalt_ingot", "Kobaltowa sztabka"),
        ("runestone_ingot", "Runiczna sztabka"),
        ("dragonsteel_ingot", "Sztabka Smoczej Stali"),
        ("astral_ingot", "Astralna sztabka"),
        ("void_ingot", "Sztabka Pustki"),
        ("eternium_ingot", "Sztabka Eternium"),
    )
    for item_id, name in extra_ingots:
        _catalog_mut.catalog_assign({
            "name": name,
            "type": "craft_material",
            "price": None,
            "desc": (
                "Przetopiony metal używany w zaawansowanym "
                "Kowalstwie."
            ),
        }, 'ITEMS', ITEMS, (item_id,))

    for tier_number, tier in enumerate(BLACKSMITH_TIERS, 1):
        for slot, (
            slot_name, defense_delta, _ingot_cost
        ) in BLACKSMITH_SLOT_DEFS.items():
            item_id = (
                f"smith_{tier['key']}_{slot}"
            )
            level = int(tier["profession_level"])
            defense = max(
                1,
                int(tier["base_defense"])
                + int(defense_delta)
                + int(round(equipment_defense_step_v1138(level) * 1.10)),
            )
            masterwork = _blacksmith_masterwork_profile_v1138(level, slot)
            _catalog_mut.catalog_assign({
                "name": (
                    f"{slot_name} {tier['name']} "
                    f"[Kowalstwo Tier {tier_number}]"
                ),
                "type": "armor",
                "slot": slot,
                "defense": defense,
                "attack": int(masterwork["attack"]),
                "magic_attack": int(masterwork["magic_attack"]),
                "stats": dict(masterwork["stats"]),
                "properties": dict(masterwork["properties"]),
                "sockets": int(masterwork["sockets"]),
                "crafted_masterwork": True,
                "equipment_identity_source": "blacksmith",
                "source_progression_stage": level,
                "equipment_identity_role": "masterwork_customization",
                "equipment_identity_label": (
                    "Kowalstwo — masterwork, właściwość materiałowa i sockety"
                ),
                "price": None,
                "desc": (
                    f"Wyposażenie wykute przez Kowala. "
                    f"Kowalstwo level {tier['profession_level']}+. "
                    "Młot Rzemieślniczy wpływa na dostęp do lepszych materiałów "
                    "i bonus produktu. Tier Młota musi spełniać próg receptury; "
                    "pojedynczy level Młota wewnątrz Tieru nie skraca czasu. "
                    f"Obrona +{defense}. Masterwork: statystyki, właściwość materiałowa "
                    f"i {int(masterwork['sockets'])} gniazd(a) do dalszego dopracowania."
                ),
                "blacksmith_tier": tier_number,
                "blacksmith_material": tier["key"],
            }, 'ITEMS', ITEMS, (item_id,))

_register_blacksmith_items()
for _level in PROGRESSION_400_LEVELS:
    _catalog_mut.catalog_assign({
        "name": f"Sztabka {_BLACKSMITH_400_LABELS[_level]}",
        "type": "craft_material", "price": None,
        "desc": f"Materiał Kowalstwa level {_level}.",
    }, 'ITEMS', ITEMS, (f"ingot_400_{_level}",))

# ============================================================
# v0.8.58: materiałowe EQ znajdowane na ciałach mobów.
# To osobna linia dropu od Kowalstwa: nie nadpisuje przedmiotów
# crafted ani unikalnych setów/boss lootów.
# ============================================================
CORPSE_MATERIAL_TIERS = (
    {
        "key": "iron", "label": "Żelazny", "min_score": 0,
        "base_defense": 2, "stat_power": 1,
        "primary": "constitution", "secondary": "strength",
        "physical_damage_pct": 0, "magic_damage_pct": 0,
        "physical_defense_pct": 1, "magic_defense_pct": 0,
        "dodge_pct": 0, "max_hp_pct": 1, "max_mana_pct": 0,
        "rarity": "common", "rarity_name": "Pospolity",
        "identity": "wytrzymałość i podstawowa ochrona fizyczna",
    },
    {
        "key": "steel", "label": "Stalowy", "min_score": 1100,
        "base_defense": 3, "stat_power": 1,
        "primary": "strength", "secondary": "constitution",
        "physical_damage_pct": 1, "magic_damage_pct": 0,
        "physical_defense_pct": 1, "magic_defense_pct": 0,
        "dodge_pct": 0, "max_hp_pct": 1, "max_mana_pct": 0,
        "rarity": "uncommon", "rarity_name": "Niepospolity",
        "identity": "Siła, Kondycja i walka fizyczna",
    },
    {
        "key": "mithril", "label": "Mithrilowy", "min_score": 2200,
        "base_defense": 4, "stat_power": 2,
        "primary": "dexterity", "secondary": "intelligence",
        "physical_damage_pct": 1, "magic_damage_pct": 1,
        "physical_defense_pct": 0, "magic_defense_pct": 1,
        "dodge_pct": 1, "max_hp_pct": 0, "max_mana_pct": 1,
        "rarity": "rare", "rarity_name": "Rzadki",
        "identity": "Zręczność, szybkość, krytyki, unik i lekka magia",
    },
    {
        "key": "adamantite", "label": "Adamantytowy", "min_score": 3200,
        "base_defense": 5, "stat_power": 2,
        "primary": "constitution", "secondary": "willpower",
        "physical_damage_pct": 0, "magic_damage_pct": 0,
        "physical_defense_pct": 2, "magic_defense_pct": 2,
        "dodge_pct": 0, "max_hp_pct": 2, "max_mana_pct": 0,
        "rarity": "rare", "rarity_name": "Rzadki",
        "identity": "Kondycja, Siła Woli, HP i ciężka obrona",
    },
    {
        "key": "cobalt", "label": "Kobaltowy", "min_score": 4200,
        "base_defense": 6, "stat_power": 3,
        "primary": "strength", "secondary": "dexterity",
        "physical_damage_pct": 2, "magic_damage_pct": 0,
        "physical_defense_pct": 1, "magic_defense_pct": 0,
        "dodge_pct": 1, "max_hp_pct": 0, "max_mana_pct": 0,
        "rarity": "epic", "rarity_name": "Epicki",
        "identity": "Siła, Zręczność i agresywna walka fizyczna",
    },
    {
        "key": "runic", "label": "Runiczny", "min_score": 12000,
        "base_defense": 7, "stat_power": 3,
        "primary": "intelligence", "secondary": "willpower",
        "physical_damage_pct": 0, "magic_damage_pct": 2,
        "physical_defense_pct": 0, "magic_defense_pct": 2,
        "dodge_pct": 0, "max_hp_pct": 0, "max_mana_pct": 2,
        "rarity": "epic", "rarity_name": "Epicki",
        "identity": "Inteligencja, Siła Woli, Mana i magia",
    },
    {
        "key": "dragonsteel", "label": "Smoczej Stali", "min_score": 22000,
        "base_defense": 8, "stat_power": 4,
        "primary": "strength", "secondary": "constitution",
        "physical_damage_pct": 3, "magic_damage_pct": 1,
        "physical_defense_pct": 2, "magic_defense_pct": 1,
        "dodge_pct": 0, "max_hp_pct": 2, "max_mana_pct": 0,
        "rarity": "legendary", "rarity_name": "Legendarny",
        "identity": "Siła, Kondycja, obrażenia i twardość Smoczej Stali",
    },
    {
        "key": "astral", "label": "Astralny", "min_score": 33000,
        "base_defense": 9, "stat_power": 4,
        "primary": "intelligence", "secondary": "dexterity",
        "physical_damage_pct": 1, "magic_damage_pct": 3,
        "physical_defense_pct": 1, "magic_defense_pct": 2,
        "dodge_pct": 1, "max_hp_pct": 0, "max_mana_pct": 3,
        "rarity": "legendary", "rarity_name": "Legendarny",
        "identity": "Inteligencja, Zręczność, Mana i astralna ofensywa",
    },
    {
        "key": "void", "label": "Pustki", "min_score": 57000,
        "base_defense": 10, "stat_power": 5,
        "primary": "willpower", "secondary": "dexterity",
        "physical_damage_pct": 2, "magic_damage_pct": 3,
        "physical_defense_pct": 1, "magic_defense_pct": 3,
        "dodge_pct": 1, "max_hp_pct": 1, "max_mana_pct": 2,
        "rarity": "mythic", "rarity_name": "Mityczny",
        "identity": "Siła Woli, Zręczność, odporność magiczna i obrażenia Pustki",
    },
    {
        "key": "eternium", "label": "Eternium", "min_score": 400000,
        "base_defense": 12, "stat_power": 6,
        "primary": "strength", "secondary": "willpower",
        "physical_damage_pct": 3, "magic_damage_pct": 3,
        "physical_defense_pct": 3, "magic_defense_pct": 3,
        "dodge_pct": 1, "max_hp_pct": 3, "max_mana_pct": 3,
        "rarity": "eternal", "rarity_name": "Wieczny",
        "identity": "końcowy balans ofensywy, obrony, HP i Many",
    },
)

# v0.9.18: materiałowe EQ jest bramkowane Biegłością aktywnej klasy,
# a nie Soul Levelem. Skala obejmuje pełną progresję 1-600 i uniemożliwia
# założenie endgame EQ przez świeżą postać po samym transferze od innego gracza.
# v0.9.19: materiał nie jest już pojedynczym skokiem mocy. Każdy materiał
# ma warianty EQ co 10 Biegłości. Materiał określa rodzinę/epokę sprzętu,
# a konkretna sztuka ma własny próg 1/10/20/.../600.
CORPSE_MATERIAL_MASTERY_BANDS = {
    "iron": (1, 10, 20, 30),
    "steel": (40, 50, 60, 70),
    "mithril": (80, 90, 100, 110),
    "adamantite": (120, 130, 140, 150),
    "cobalt": (160, 170, 180, 190),
    "runic": (200, 210, 220, 230),
    "dragonsteel": (240, 250, 260, 270),
    "astral": (280, 290, 300, 310),
    "void": (320, 330, 340, 350),
    "eternium": tuple(range(360, 601, 20)),
}
CORPSE_MATERIAL_REQUIRED_MASTERY = {
    key: levels[0] for key, levels in CORPSE_MATERIAL_MASTERY_BANDS.items()
}


def corpse_material_variant_mastery(material_key, variant_index):
    levels = CORPSE_MATERIAL_MASTERY_BANDS[str(material_key)]
    idx = max(0, min(CORPSE_RANDOM_VARIANTS_PER_SLOT - 1, int(variant_index) - 1))
    band_index = min(len(levels) - 1, (idx * len(levels)) // CORPSE_RANDOM_VARIANTS_PER_SLOT)
    return int(levels[band_index])

CORPSE_MATERIAL_SLOT_DEFS = {
    "head": ("Hełm", 0),
    "body": ("Pancerz", 3),
    "shield": ("Tarcza", 2),
    "hands": ("Rękawice", -1),
    "legs": ("Nogawice", 1),
    "feet": ("Buty", -1),
    "charm": ("Talizman", -2),
    "ring": ("Pierścień", -2),
    "necklace": ("Naszyjnik", -1),
    "earring": ("Kolczyk", -2),
    "shoulders": ("Naramienniki", 2),
    "belt": ("Pas", 1),
    "cloak": ("Peleryna", 0),
    "bracers": ("Karwasze", 0),
    "bracelet": ("Bransoletka", -1),
    "accessory": ("Akcesorium", -1),
    "relic": ("Relikt", 0),
}

MATERIAL_STAT_NAMES = {
    "strength": "Siła",
    "dexterity": "Zręczność",
    "constitution": "Kondycja",
    "intelligence": "Inteligencja",
    "willpower": "Siła Woli",
    "hp": "HP",
    "mana": "Mana",
}

MATERIAL_PROPERTY_NAMES = {
    "physical_damage_pct": "obrażenia fizyczne",
    "magic_damage_pct": "obrażenia magiczne",
    "all_damage_pct": "wszystkie obrażenia",
    "physical_defense_pct": "obrona fizyczna",
    "magic_defense_pct": "obrona magiczna",
    "dodge_pct": "unik",
    "max_hp_pct": "maksymalne HP",
    "max_mana_pct": "maksymalna Mana",
    "lifesteal_percent": "wysysanie życia przy ataku",
    "mana_restore_percent": "odzyskiwanie Many przy ataku",
}

CORPSE_MATERIAL_ITEM_IDS = {}
CORPSE_MATERIAL_TIER_BY_KEY = {tier["key"]: tier for tier in CORPSE_MATERIAL_TIERS}


CORPSE_RANDOM_VARIANTS_PER_SLOT = 24

MATERIAL_RANDOM_STAT_POOL = (
    "strength",
    "dexterity",
    "constitution",
    "intelligence",
    "willpower",
)

MATERIAL_RANDOM_PROPERTY_POOL = (
    "physical_damage_pct",
    "magic_damage_pct",
    "physical_defense_pct",
    "magic_defense_pct",
    "dodge_pct",
    "max_hp_pct",
    "max_mana_pct",
)

MATERIAL_STAT_EPITHETS = {
    "strength": "Siły",
    "dexterity": "Zręczności",
    "constitution": "Kondycji",
    "intelligence": "Inteligencji",
    "willpower": "Woli",
}

MATERIAL_SLOT_NAME_FOR_TITLE = {
    "head": "Hełm",
    "body": "Pancerz",
    "shield": "Tarcza",
    "hands": "Rękawice",
    "legs": "Nogawice",
    "feet": "Buty",
    "charm": "Talizman",
    "ring": "Pierścień",
    "necklace": "Naszyjnik",
    "earring": "Kolczyk",
    "shoulders": "Naramienniki",
    "belt": "Pas",
    "cloak": "Peleryna",
    "bracers": "Karwasze",
    "bracelet": "Bransoletka",
    "accessory": "Akcesorium",
    "relic": "Relikt",
}

# Każdy slot ma własny charakter statów. Kolejność jest używana jako
# preferencja przy losowaniu profilu i sprawia, że np. korpus nie wygląda
# statystycznie tak samo jak kolczyk czy karwasze.
MATERIAL_SLOT_STAT_PREFERENCES = {
    "head": ("willpower", "constitution", "intelligence", "strength", "dexterity"),
    "body": ("constitution", "willpower", "strength", "intelligence", "dexterity"),
    "shield": ("constitution", "strength", "willpower", "intelligence", "dexterity"),
    "hands": ("strength", "dexterity", "intelligence", "constitution", "willpower"),
    "legs": ("constitution", "dexterity", "strength", "willpower", "intelligence"),
    "feet": ("dexterity", "constitution", "strength", "willpower", "intelligence"),
    "charm": ("willpower", "intelligence", "constitution", "dexterity", "strength"),
    "ring": ("dexterity", "strength", "intelligence", "willpower", "constitution"),
    "necklace": ("intelligence", "willpower", "constitution", "strength", "dexterity"),
    "earring": ("intelligence", "dexterity", "willpower", "strength", "constitution"),
    "shoulders": ("strength", "constitution", "willpower", "dexterity", "intelligence"),
    "belt": ("constitution", "strength", "willpower", "dexterity", "intelligence"),
    "cloak": ("dexterity", "willpower", "intelligence", "constitution", "strength"),
    "bracers": ("strength", "dexterity", "constitution", "intelligence", "willpower"),
    "bracelet": ("dexterity", "strength", "constitution", "willpower", "intelligence"),
    "accessory": ("willpower", "intelligence", "dexterity", "strength", "constitution"),
    "relic": ("willpower", "intelligence", "strength", "constitution", "dexterity"),
}

MATERIAL_SLOT_POWER_SCALE = {
    "head": 0.55, "body": 0.25, "shield": 0.15, "hands": 0.95,
    "legs": 0.25, "feet": 0.45, "charm": 0.70, "ring": 0.90,
    "necklace": 0.75, "earring": 0.85, "shoulders": 0.35, "belt": 0.30,
    "cloak": 0.50, "bracers": 0.80, "bracelet": 0.75,
    "accessory": 0.95, "relic": 1.10,
}

MATERIAL_SLOT_PROPERTY_PREFERENCES = {
    "head": ("magic_defense_pct", "max_mana_pct", "physical_defense_pct", "max_hp_pct", "magic_damage_pct", "physical_damage_pct", "dodge_pct"),
    "body": ("physical_defense_pct", "max_hp_pct", "magic_defense_pct", "max_mana_pct", "physical_damage_pct", "magic_damage_pct", "dodge_pct"),
    "shield": ("physical_defense_pct", "max_hp_pct", "magic_defense_pct", "physical_damage_pct", "max_mana_pct", "magic_damage_pct", "dodge_pct"),
    "hands": ("physical_damage_pct", "magic_damage_pct", "dodge_pct", "physical_defense_pct", "magic_defense_pct", "max_hp_pct", "max_mana_pct"),
    "legs": ("physical_defense_pct", "max_hp_pct", "dodge_pct", "magic_defense_pct", "physical_damage_pct", "magic_damage_pct", "max_mana_pct"),
    "feet": ("dodge_pct", "physical_defense_pct", "magic_defense_pct", "physical_damage_pct", "magic_damage_pct", "max_hp_pct", "max_mana_pct"),
    "charm": ("max_mana_pct", "magic_defense_pct", "magic_damage_pct", "max_hp_pct", "physical_defense_pct", "dodge_pct", "physical_damage_pct"),
    "ring": ("physical_damage_pct", "magic_damage_pct", "dodge_pct", "max_mana_pct", "max_hp_pct", "physical_defense_pct", "magic_defense_pct"),
    "necklace": ("max_mana_pct", "magic_damage_pct", "magic_defense_pct", "max_hp_pct", "physical_damage_pct", "physical_defense_pct", "dodge_pct"),
    "earring": ("magic_damage_pct", "dodge_pct", "max_mana_pct", "physical_damage_pct", "magic_defense_pct", "physical_defense_pct", "max_hp_pct"),
    "shoulders": ("physical_defense_pct", "physical_damage_pct", "max_hp_pct", "magic_defense_pct", "magic_damage_pct", "dodge_pct", "max_mana_pct"),
    "belt": ("max_hp_pct", "physical_defense_pct", "magic_defense_pct", "dodge_pct", "physical_damage_pct", "magic_damage_pct", "max_mana_pct"),
    "cloak": ("dodge_pct", "magic_defense_pct", "max_mana_pct", "magic_damage_pct", "physical_defense_pct", "physical_damage_pct", "max_hp_pct"),
    "bracers": ("physical_damage_pct", "dodge_pct", "physical_defense_pct", "magic_damage_pct", "max_hp_pct", "magic_defense_pct", "max_mana_pct"),
    "bracelet": ("physical_damage_pct", "dodge_pct", "magic_damage_pct", "physical_defense_pct", "magic_defense_pct", "max_hp_pct", "max_mana_pct"),
    "accessory": ("magic_damage_pct", "physical_damage_pct", "max_mana_pct", "max_hp_pct", "dodge_pct", "magic_defense_pct", "physical_defense_pct"),
    "relic": ("max_mana_pct", "max_hp_pct", "magic_damage_pct", "physical_damage_pct", "magic_defense_pct", "physical_defense_pct", "dodge_pct"),
}


def _material_budget_split(rng, budget, count):
    """Losowy podział dużego budżetu bez pętli po każdym punkcie statystyki."""
    budget = max(count, int(budget))
    if count <= 1:
        return [budget]
    # Losujemy miejsca cięcia kompozycji dodatnich liczb. Koszt zależy od liczby
    # statów (maks. 5), a nie od budżetu, który w no-limit progression może być duży.
    cuts = sorted(rng.sample(range(1, budget), count - 1))
    points = [0] + cuts + [budget]
    values = [points[i + 1] - points[i] for i in range(count)]
    rng.shuffle(values)
    return values


def _material_random_profile(tier, slot, variant_index, salt=0):
    """Deterministyczny profil materiałowego EQ.

    v0.30.37: każdy slot ma własne preferencje statów/właściwości, a rejestracja
    odrzuca powtórzone profile statów w obrębie tego samego materiału i slotu.
    `salt` służy wyłącznie do deterministycznego znalezienia innego profilu.
    """
    tier_index = 1 + next(
        i for i, row in enumerate(CORPSE_MATERIAL_TIERS)
        if row["key"] == tier["key"]
    )
    rng = random.Random(
        f"soulbound-v0.30.37:{tier['key']}:{slot}:{int(variant_index)}:{int(salt)}"
    )

    property_budgets = (1, 1, 2, 3, 4, 5, 7, 8, 10, 12)
    required_mastery = corpse_material_variant_mastery(tier["key"], variant_index)
    band_levels = CORPSE_MATERIAL_MASTERY_BANDS[tier["key"]]
    substep = band_levels.index(required_mastery)

    # Drop nie jest już ubogim kuzynem sklepu. Ten sam etap korzysta z tej samej
    # ogólnej skali mocy, ale roll ma 80-110% budżetu i losowy rozkład statów.
    # Dzięki temu dobry egzemplarz może być lepszy dla konkretnego buildu,
    # podczas gdy sklep pozostaje pewnym, klasowo dopasowanym wyborem.
    quality = 0.80 + rng.random() * 0.30
    progression_budget = equipment_progression_budget_v1138(required_mastery)
    stat_budget = max(2, int(round(progression_budget * quality)))
    property_budget = (
        property_budgets[tier_index - 1]
        + max(0, int(round((quality - 0.80) * 8.0)))
    )

    if tier_index <= 4:
        stat_count = 2
    elif tier_index <= 6:
        stat_count = rng.choice((2, 3))
    elif tier_index <= 8:
        stat_count = 3
    elif tier_index == 9:
        stat_count = rng.choice((3, 4))
    else:
        stat_count = 4
    stat_count = min(stat_count, len(MATERIAL_RANDOM_STAT_POOL), stat_budget)

    # Preferencje slotu są rotowane przez seed, więc slot ma własny charakter,
    # ale 24 warianty nadal nie są kopiami tego samego rozkładu.
    stat_pref = list(MATERIAL_SLOT_STAT_PREFERENCES.get(slot, MATERIAL_RANDOM_STAT_POOL))
    tier_pref = [tier.get("primary"), tier.get("secondary")]
    weighted_stats = []
    for stat in tier_pref + stat_pref + list(MATERIAL_RANDOM_STAT_POOL):
        if stat in MATERIAL_RANDOM_STAT_POOL and stat not in weighted_stats:
            weighted_stats.append(stat)
    # Losuj z preferowanej listy przez permutację, nie przez identyczną stałą parę.
    rotated = weighted_stats[rng.randrange(len(weighted_stats)):] + weighted_stats[:rng.randrange(len(weighted_stats))]
    # Drugi shuffle daje warianty przy zachowaniu slot-specific seed.
    rng.shuffle(rotated)
    chosen_stats = rotated[:stat_count]
    stat_values = _material_budget_split(rng, stat_budget, stat_count)
    stats = dict(zip(chosen_stats, stat_values))

    if tier_index <= 2:
        property_count = 1
    elif tier_index <= 5:
        property_count = 2
    elif tier_index <= 8:
        property_count = 3
    else:
        property_count = 4
    property_count = min(property_count, len(MATERIAL_RANDOM_PROPERTY_POOL), property_budget)
    prop_pref = list(MATERIAL_SLOT_PROPERTY_PREFERENCES.get(slot, MATERIAL_RANDOM_PROPERTY_POOL))
    rng.shuffle(prop_pref)
    chosen_properties = prop_pref[:property_count]
    property_values = _material_budget_split(rng, property_budget, property_count)
    properties = dict(zip(chosen_properties, property_values))

    _slot_label, defense_delta = CORPSE_MATERIAL_SLOT_DEFS[slot]
    defense = max(
        1,
        int(tier["base_defense"])
        + int(defense_delta)
        + int(round(
            equipment_defense_step_v1138(required_mastery)
            * (0.88 + (quality - 0.80) * 0.55)
        )),
    )

    # Losowy profil ofensywny może mieć Attack, Magic Attack albo oba.
    slot_scale = float(MATERIAL_SLOT_POWER_SCALE.get(slot, 0.50))
    flat_pool = max(
        0,
        int(round(progression_budget * 0.11 * slot_scale * quality)),
    )
    physical_score = (
        int(stats.get("strength", 0))
        + int(stats.get("dexterity", 0))
        + int(round(float(properties.get("physical_damage_pct", 0)) * 2.0))
    )
    magic_score = (
        int(stats.get("intelligence", 0))
        + int(stats.get("willpower", 0))
        + int(round(float(properties.get("magic_damage_pct", 0)) * 2.0))
    )
    score_total = physical_score + magic_score
    attack = 0
    magic_attack = 0
    if flat_pool > 0 and score_total > 0:
        attack = int(round(flat_pool * physical_score / float(score_total)))
        magic_attack = max(0, flat_pool - attack)
        if physical_score > 0 and attack <= 0:
            attack = 1
        if magic_score > 0 and magic_attack <= 0:
            magic_attack = 1

    if required_mastery >= 500:
        sockets = 4
    elif required_mastery >= 360:
        sockets = 3
    elif required_mastery >= 240:
        sockets = 2
    elif required_mastery >= 120:
        sockets = 1
    else:
        sockets = 0
    if quality >= 1.04:
        sockets = min(5, sockets + 1)

    return (
        defense, stats, properties, attack, magic_attack, sockets, quality
    )


MATERIAL_TITLE_PHRASE = {
    "iron": "z Żelaza", "steel": "ze Stali", "mithril": "z Mithrilu",
    "adamantite": "z Adamantytu", "cobalt": "z Kobaltu", "runic": "z Metalu Runicznego",
    "dragonsteel": "ze Smoczej Stali", "astral": "z Astralu", "void": "z Pustki",
    "eternium": "z Eternium",
}


def _material_variant_title(tier, slot, stats, variant_index, required_mastery):
    ordered = [stat for stat in MATERIAL_RANDOM_STAT_POOL if stat in stats]
    epithets = [MATERIAL_STAT_EPITHETS[s] for s in ordered[:2]] if ordered else ["Losu"]
    stat_part = " i ".join(epithets)
    slot_name = MATERIAL_SLOT_NAME_FOR_TITLE[slot]
    material_part = MATERIAL_TITLE_PHRASE.get(tier["key"], tier["label"])
    return (
        f"{slot_name} {material_part} {stat_part} "
        f"[Level {int(required_mastery)}, wariant {int(variant_index):02d}]"
    )


def _register_corpse_material_items():
    global CORPSE_MATERIAL_ITEM_IDS
    CORPSE_MATERIAL_ITEM_IDS = {}
    all_names = set()
    for tier_index, tier in enumerate(CORPSE_MATERIAL_TIERS, 1):
        ids = []
        for slot in CORPSE_MATERIAL_SLOT_DEFS:
            seen_stats = set()
            for variant_index in range(1, CORPSE_RANDOM_VARIANTS_PER_SLOT + 1):
                item_id = f"corpse_{tier['key']}_{slot}_v{variant_index:02d}"
                profile = None
                for salt in range(512):
                    (
                        defense, stats, properties,
                        attack, magic_attack, sockets, quality,
                    ) = _material_random_profile(
                        tier, slot, variant_index, salt=salt
                    )
                    stat_sig = tuple(sorted((str(k), int(v)) for k, v in stats.items()))
                    if stat_sig not in seen_stats:
                        profile = (
                            defense, stats, properties, attack,
                            magic_attack, sockets, quality, stat_sig,
                        )
                        break
                if profile is None:
                    raise RuntimeError(
                        f"v0.30.37: nie udało się utworzyć unikalnych statów {tier['key']} {slot} wariant {variant_index}"
                    )
                (
                    defense, stats, properties, attack,
                    magic_attack, sockets, quality, stat_sig,
                ) = profile
                seen_stats.add(stat_sig)
                required_mastery = corpse_material_variant_mastery(tier["key"], variant_index)
                name = _material_variant_title(tier, slot, stats, variant_index, required_mastery)
                if str(name).casefold() in all_names:
                    raise RuntimeError(f"v0.30.37: powtórzona nazwa materiałowego EQ: {name}")
                all_names.add(str(name).casefold())
                stat_text = ", ".join(
                    f"{MATERIAL_STAT_NAMES.get(stat, stat)} +{amount}" for stat, amount in stats.items()
                )
                prop_text = ", ".join(
                    f"{MATERIAL_PROPERTY_NAMES.get(prop, prop)} +{amount}%" for prop, amount in properties.items()
                )
                crit_note = (
                    " Zręczność z tej części zwiększa także szansę na trafienie krytyczne."
                    if stats.get("dexterity", 0) > 0 else ""
                )
                _catalog_mut.catalog_assign({
                    "name": name,
                    "type": "armor",
                    "slot": slot,
                    "defense": defense,
                    "attack": int(attack),
                    "magic_attack": int(magic_attack),
                    "sockets": int(sockets),
                    "drop_quality": round(float(quality), 3),
                    "price": None,
                    "rarity": tier["rarity"],
                    "rarity_name": tier["rarity_name"],
                    "stats": stats,
                    "properties": properties,
                    "corpse_material": tier["key"],
                    "corpse_material_tier": tier_index,
                    "corpse_random_variant": variant_index,
                    "required_mastery": required_mastery,
                    "source_progression_stage": required_mastery,
                    "equipment_identity_source": "corpse_drop",
                    "equipment_identity_role": "random_material_variant",
                    "equipment_identity_label": (
                        "Drop z moba — losowy materiał, wariant i profil "
                        + str(tier["identity"])
                    ),
                    "mastery_requirement_scope": "active_class",
                    # v0.61.2: opis materiałowego EQ jest składany na żądanie.
                }, 'ITEMS', ITEMS, (item_id,))
                ids.append(item_id)
        CORPSE_MATERIAL_ITEM_IDS[tier["key"]] = tuple(ids)


_register_corpse_material_items()


def loot_source_equipment_audit_v11327():
    errors = []

    crafted = [
        item for item in ITEMS.values() if item.get("crafted_masterwork")
    ]
    if not crafted:
        errors.append("missing blacksmith masterwork items")
    else:
        for item in crafted[:200]:
            if int(item.get("source_progression_stage", 0) or 0) <= 0:
                errors.append("blacksmith item missing source progression stage")
                break
            if int(item.get("sockets", 0) or 0) < 1:
                errors.append("blacksmith item lost socket identity")
                break

    corpse = [
        item for item in ITEMS.values()
        if item.get("corpse_material") and not item.get("infinite_depth_variant")
    ]
    if not corpse:
        errors.append("missing corpse material equipment")
    else:
        for item in corpse[:500]:
            mastery = int(item.get("required_mastery", 0) or 0)
            stage = int(item.get("source_progression_stage", 0) or 0)
            if stage != mastery or stage <= 0:
                errors.append("corpse drop source stage mismatch")
                break
            if item.get("equipment_identity_source") != "corpse_drop":
                errors.append("corpse drop identity source missing")
                break

    return {
        "version": "1.13.27",
        "blacksmith_count": len(crafted),
        "corpse_drop_count": len(corpse),
        "error_count": len(errors),
        "errors": errors,
    }


LOOT_SOURCE_EQUIPMENT_AUDIT_V11327 = loot_source_equipment_audit_v11327()


FISH_RARE_VARIANTS = {
    "albino": {
        "label": "Albinos",
        "name_prefix": "Albinos ",
        "value_mult": 3,
        "weight": 50,
        "desc": "Rzadki albinos danego gatunku.",
    },
    "golden": {
        "label": "Złoty",
        "name_prefix": "Złoty okaz ",
        "value_mult": 8,
        "weight": 25,
        "desc": "Bardzo rzadki złoty wariant.",
    },
    "giant": {
        "label": "Olbrzymi",
        "name_prefix": "Olbrzymi okaz ",
        "value_mult": 5,
        "weight": 18,
        "desc": "Nienaturalnie duży okaz gatunku.",
    },
    "ancient": {
        "label": "Pradawny",
        "name_prefix": "Pradawny okaz ",
        "value_mult": 15,
        "weight": 7,
        "desc": "Ekstremalnie rzadki pradawny okaz.",
    },
}

WOOD_RARE_VARIANTS = {
    "lush": {
        "label": "Bujne",
        "name_prefix": "Bujne drewno ",
        "value_mult": 3,
        "weight": 50,
        "desc": "Wyjątkowo zdrowe i gęste drewno.",
    },
    "ancient": {
        "label": "Pradawne",
        "name_prefix": "Pradawne drewno ",
        "value_mult": 7,
        "weight": 30,
        "desc": "Drewno pochodzące z bardzo starego drzewa.",
    },
    "crystal": {
        "label": "Kryształowe",
        "name_prefix": "Kryształowe drewno ",
        "value_mult": 12,
        "weight": 15,
        "desc": "Rzadkie drewno przesiąknięte kryształową energią.",
    },
    "legendary": {
        "label": "Legendarne",
        "name_prefix": "Legendarne drewno ",
        "value_mult": 20,
        "weight": 5,
        "desc": "Najrzadszy wariant drewna.",
    },
}

HERB_RARE_VARIANTS = {
    "lush": {
        "label": "Bujna",
        "name_prefix": "Bujna roślina ",
        "value_mult": 3,
        "weight": 50,
        "desc": "Wyjątkowo dorodny okaz rośliny.",
    },
    "glowing": {
        "label": "Lśniąca",
        "name_prefix": "Lśniąca roślina ",
        "value_mult": 7,
        "weight": 25,
        "desc": "Rzadki okaz emanujący delikatnym blaskiem.",
    },
    "ancient": {
        "label": "Pradawna",
        "name_prefix": "Pradawna roślina ",
        "value_mult": 12,
        "weight": 18,
        "desc": "Bardzo stary i wyjątkowo silny okaz.",
    },
    "legendary": {
        "label": "Legendarna",
        "name_prefix": "Legendarna roślina ",
        "value_mult": 20,
        "weight": 7,
        "desc": "Najrzadszy wariant rośliny.",
    },
}

MINING_VEINS = {
    "common": {
        "name": "Zwykła żyła",
        "quantity": 1,
    },
    "rich": {
        "name": "Bogata żyła",
        "quantity": 2,
    },
    "crystal": {
        "name": "Kryształowa żyła",
        "quantity": 3,
    },
    "legendary": {
        "name": "Legendarna żyła",
        "quantity": 5,
    },
}

def rare_resource_variant_id(category, key, base_item_id):
    return f"rare_{category}_{key}__{base_item_id}"

def _scaled_resource_sale_fields(base_item, multiplier):
    result = {}
    for currency in ("silver", "gold", "mithril"):
        key = f"sell_{currency}"
        value = int(base_item.get(key, 0))
        if value > 0:
            result[key] = max(1, value * int(multiplier))
    return result

def _register_rare_resource_variants():
    groups = (
        (
            "fish",
            tuple(FISH_RESOURCE_IDS),
            FISH_RARE_VARIANTS,
        ),
        (
            "wood",
            tuple(WOOD_RESOURCE_IDS),
            WOOD_RARE_VARIANTS,
        ),
        (
            "herb",
            tuple(HERB_RESOURCE_IDS),
            HERB_RARE_VARIANTS,
        ),
    )

    for category, base_ids, variants in groups:
        for base_item_id in base_ids:
            base_item = ITEMS.get(base_item_id)
            if not base_item:
                continue

            for key, definition in variants.items():
                variant_id = rare_resource_variant_id(
                    category, key, base_item_id
                )
                value_mult = int(definition["value_mult"])
                item = {
                    "name": (
                        definition["name_prefix"]
                        + base_item["name"]
                    ),
                    "type": "resource",
                    "price": None,
                    "desc": (
                        f"{definition['desc']} "
                        f"Bazowy zasób: {base_item['name']}. "
                        f"Wartość sprzedaży x{value_mult}."
                    ),
                    "resource_category": category,
                    "base_resource_id": base_item_id,
                    "rare_resource_variant": key,
                    "rare_resource_label": definition["label"],
                    "rare_value_multiplier": value_mult,
                }
                item.update(
                    _scaled_resource_sale_fields(
                        base_item, value_mult
                    )
                )
                _catalog_mut.catalog_assign(item, 'ITEMS', ITEMS, (variant_id,))

_register_rare_resource_variants()

RARE_FISH_VARIANT_IDS = {
    item_id
    for item_id, item in ITEMS.items()
    if item.get("resource_category") == "fish"
    and item.get("rare_resource_variant")
}
RARE_WOOD_VARIANT_IDS = {
    item_id
    for item_id, item in ITEMS.items()
    if item.get("resource_category") == "wood"
    and item.get("rare_resource_variant")
}
RARE_HERB_VARIANT_IDS = {
    item_id
    for item_id, item in ITEMS.items()
    if item.get("resource_category") == "herb"
    and item.get("rare_resource_variant")
}

FISH_STORAGE_IDS = set(FISH_RESOURCE_IDS) | RARE_FISH_VARIANT_IDS
ORE_STORAGE_IDS = set(ORE_RESOURCE_IDS)
WOOD_STORAGE_IDS = set(WOOD_RESOURCE_IDS) | RARE_WOOD_VARIANT_IDS
HERB_STORAGE_IDS = set(HERB_RESOURCE_IDS) | RARE_HERB_VARIANT_IDS


# v0.9.5: kolekcjonerska rzadkość gatunku. Nie zmienia ceny ani balansu.
FISH_RARITY_LABELS_PL = {
    "common": "pospolita",
    "uncommon": "niepospolita",
    "rare": "rzadka",
    "epic": "epicka",
    "legendary": "legendarna",
}

def base_fish_species_id(item_id):
    item = ITEMS.get(item_id, {})
    return str(item.get("base_resource_id") or item_id)

def fish_unlock_level(item_id):
    item_id = base_fish_species_id(item_id)
    _item = ITEMS.get(item_id, {})
    if _item.get("generator_level") is not None:
        return max(1, min(TOOL_MAX_LEVEL, int(_item.get("generator_level") or 1)))
    levels = []
    if item_id in BASE_FISH_MIN_TOOL_LEVELS:
        levels.append(int(BASE_FISH_MIN_TOOL_LEVELS[item_id]))
    for table in (ENDGAME_FISH_UNLOCKS, MORE_FISH_UNLOCKS, WORLD_FISH_UNLOCKS):
        for rows in table.values():
            for row in rows:
                if len(row) >= 2 and str(row[1]) == item_id:
                    levels.append(int(row[0]))
    return min(levels) if levels else 1

def v096_fish_price_scale(item_id):
    """Cena sprzedaży ryby skaluje się wg poziomu odblokowania gatunku.

    Początek nie jest buffowany cenowo mimo 16 s zamiast 15 s. Endgame jest
    obniżany do ok. 60% ceny/szt., co kompensuje zejście 5 s -> 3 s.
    """
    level = fish_unlock_level(item_id)
    return max(0.60, min(1.0, v096_fishing_reward_scale(level)))

def fish_species_rarity(item_id):
    level = fish_unlock_level(item_id)
    if level >= 200:
        return "legendary"
    if level >= 150:
        return "epic"
    if level >= 80:
        return "rare"
    if level >= 30:
        return "uncommon"
    return "common"

def fish_rarity_label(item_id):
    return FISH_RARITY_LABELS_PL[fish_species_rarity(item_id)]


def fish_trophy_value_multiplier_v1138(item_id):
    """Dodatkowa wartość gatunku niezależna od rzadkiego wariantu okazu."""
    base_id = base_fish_species_id(item_id)
    rarity = fish_species_rarity(base_id)
    mult = {
        "common": 1.00,
        "uncommon": 1.25,
        "rare": 1.75,
        "epic": 2.75,
        "legendary": 4.50,
    }.get(rarity, 1.0)
    name = normalize_lookup_text(ITEMS.get(base_id, {}).get("name", base_id))
    if "rekin" in name or "shark" in name or "żarłacz" in name or "zarlacz" in name:
        mult *= 1.50
    if any(word in name for word in ("lewiatan", "leviathan", "serpent", "smok", "drake")):
        mult *= 2.00
    return max(1.0, float(mult))


def fish_jackpot_xp_multiplier_v1138(item_id):
    item = ITEMS.get(item_id, {})
    variant_mult = max(1.0, float(item.get("rare_value_multiplier", 1.0) or 1.0))
    trophy_mult = fish_trophy_value_multiplier_v1138(item_id)
    # XP rośnie dużo łagodniej niż wartość sprzedaży, żeby jackpot nie omijał grindu.
    return min(4.0, 1.0 + (math.sqrt(variant_mult * trophy_mult) - 1.0) * 0.55)


def rare_resource_xp_multiplier_v1138(item_id):
    item = ITEMS.get(item_id, {})
    value_mult = max(1.0, float(item.get("rare_value_multiplier", 1.0) or 1.0))
    return min(3.5, 1.0 + (math.sqrt(value_mult) - 1.0) * 0.50)

def fish_species_habitats(item_id):
    item_id = base_fish_species_id(item_id)
    labels = []
    if item_id in RIVER_FISH_ATLAS:
        labels.append("rzeka")
    if item_id in LAKE_FISH_ATLAS:
        labels.append("jezioro")
    if item_id in SEA_FISH_ATLAS:
        labels.append("morze")
    if item_id in OCEAN_FISH_ATLAS:
        labels.append("ocean")
    if item_id == "field_blind_sewer_eel":
        labels.append("kanał")
    return tuple(dict.fromkeys(labels))

def roll_fish_measurement(item_id):
    """Losowy rozmiar okazu do rekordów v0.9.5; bez wpływu na balans."""
    item = ITEMS.get(item_id, {})
    base_id = base_fish_species_id(item_id)
    name = normalize_lookup_text(ITEMS.get(base_id, item).get("name", base_id))
    rarity = fish_species_rarity(base_id)
    tiny_words = ("szprot", "sardyn", "sardine", "anchovy", "sardela", "stynk", "uklej", "gudgeon", "kiełb", "kielb")
    eel_words = ("węgorz", "wegorz", "eel")
    shark_words = ("rekin", "shark")
    monster_words = ("lewiatan", "leviathan", "serpent", "smok", "drake")
    large_words = ("tuńczyk", "tunczyk", "tuna", "marlin", "miecznik", "swordfish", "samogłów", "samoglow", "sunfish", "jesiotr", "sturgeon", "catfish", "halibut")
    if any(word in name for word in monster_words):
        length_mm = random.randint(1800, 8000)
        weight_g = random.randint(80000, 1500000)
    elif any(word in name for word in shark_words):
        length_mm = random.randint(700, 5200)
        weight_g = random.randint(8000, 750000)
    elif any(word in name for word in eel_words):
        length_mm = random.randint(250, 2200)
        weight_g = random.randint(150, 30000)
    elif any(word in name for word in tiny_words):
        length_mm = random.randint(60, 360)
        weight_g = random.randint(20, 1200)
    elif any(word in name for word in large_words):
        length_mm = random.randint(350, 2600)
        weight_g = random.randint(1500, 220000)
    else:
        ranges = {
            "common": ((90, 650), (60, 7000)),
            "uncommon": ((120, 900), (100, 14000)),
            "rare": ((160, 1300), (200, 30000)),
            "epic": ((220, 1900), (500, 70000)),
            "legendary": ((400, 3200), (1500, 220000)),
        }
        (lmin, lmax), (wmin, wmax) = ranges[rarity]
        length_mm = random.randint(lmin, lmax)
        weight_g = random.randint(wmin, wmax)
    variant = str(item.get("rare_resource_variant") or "")
    if variant == "giant":
        length_mm = int(round(length_mm * 1.30))
        weight_g = int(round(weight_g * 1.80))
    elif variant == "ancient":
        length_mm = int(round(length_mm * 1.10))
        weight_g = int(round(weight_g * 1.20))
    return max(1, length_mm), max(1, weight_g)

def format_fish_length(length_mm):
    return f"{int(length_mm) / 10.0:.1f} cm"

def format_fish_weight(weight_g):
    weight_g = int(weight_g)
    if weight_g >= 1000:
        return f"{weight_g / 1000.0:.2f} kg"
    return f"{weight_g} g"

def _rare_variant_roll(base_item_id, category, definitions, tool_level, profession_level=None):
    if not base_item_id or base_item_id not in ITEMS:
        return base_item_id
    base = ITEMS[base_item_id]
    # Authored stage/actual resource tier gate premium variants in starter areas.
    resource_level = int(base.get("generator_level") or base.get("min_tool_level") or 1)
    rates = resource_variant_chances_v1149(category, tool_level, profession_level, resource_level)
    roll = random.random()
    total = sum(rates.values())
    if roll >= total:
        return base_item_id
    # One draw, exclusive variants, no overlapping/jackpot duplication.
    for key, chance in rates.items():
        if key not in definitions:
            continue
        if roll < chance:
            variant_id = rare_resource_variant_id(category, key, base_item_id)
            return variant_id if variant_id in ITEMS else base_item_id
        roll -= chance
    return base_item_id


def roll_fish_variant(base_item_id, tool_level, profession_level=None):
    return _rare_variant_roll(base_item_id, "fish", FISH_RARE_VARIANTS, tool_level, profession_level)


def roll_wood_variant(base_item_id, tool_level, profession_level=None):
    return _rare_variant_roll(base_item_id, "wood", WOOD_RARE_VARIANTS, tool_level, profession_level)


def roll_herb_variant(base_item_id, tool_level, profession_level=None):
    return _rare_variant_roll(base_item_id, "herb", HERB_RARE_VARIANTS, tool_level, profession_level)


def roll_mining_vein(tool_level, profession_level=None, floor=None):
    chances = mining_vein_chances_v1149(tool_level, profession_level, floor)
    keys = tuple(chances)
    key = random.choices(keys, weights=[chances[k] for k in keys], k=1)[0]
    result = dict(MINING_VEINS[key]); result["key"] = key
    return result


CLASS_EQUIPMENT_SETS = {
    "Wojownik": {
        "prefix": "warrior_oath",
        "set_name": "Przysięgi",
        "affix": "strength",
        "base_defense": 2,
        "room": "guild_martial_hall",
    },
    "Berserker": {
        "prefix": "berserker_fury",
        "set_name": "Krwawej Furii",
        "affix": "strength",
        "base_defense": 2,
        "room": "guild_martial_hall",
    },
    "Łotrzyk": {
        "prefix": "rogue_shadow",
        "set_name": "Cienia",
        "affix": "dexterity",
        "base_defense": 1,
        "room": "guild_shadow_gallery",
    },
    "Łowca": {
        "prefix": "hunter_echo",
        "set_name": "Echa",
        "affix": "dexterity",
        "base_defense": 1,
        "room": "guild_shadow_gallery",
    },
    "Mnich": {
        "prefix": "monk_spirit",
        "set_name": "Ducha",
        "affix": "willpower",
        "base_defense": 1,
        "room": "guild_body_hall",
    },
    "Strażnik": {
        "prefix": "guardian_bastion",
        "set_name": "Bastionu",
        "affix": "constitution",
        "base_defense": 3,
        "room": "guild_body_hall",
    },
    "Mag": {
        "prefix": "mage_arcane",
        "set_name": "Arkanów",
        "affix": "intelligence",
        "base_defense": 1,
        "room": "guild_arcane_chamber",
    },
    "Nekromanta": {
        "prefix": "necromancer_souls",
        "set_name": "Dusz",
        "affix": "intelligence",
        "base_defense": 1,
        "room": "guild_dark_chamber",
    },
    "Kapłan": {
        "prefix": "priest_light",
        "set_name": "Światła",
        "affix": "willpower",
        "base_defense": 2,
        "room": "guild_sanctuary",
    },
    "Czarownik": {
        "prefix": "warlock_abyss",
        "set_name": "Otchłani",
        "affix": "intelligence",
        "base_defense": 1,
        "room": "guild_dark_chamber",
    },
    "Druid": {
        "prefix": "druid_roots",
        "set_name": "Korzeni",
        "affix": "willpower",
        "base_defense": 1,
        "room": "guild_sanctuary",
    },
    "Psionik": {
        "prefix": "psion_mind", "set_name": "Umysłu", "affix": "willpower", "base_defense": 1, "room": "guild_arcane_chamber",
    },
    "Mec": {
        "prefix": "mec_core", "set_name": "Rdzenia", "affix": "constitution", "base_defense": 3, "room": "guild_martial_hall",
    },
    "Inżynier": {
        "prefix": "engineer_tools", "set_name": "Konstruktora", "affix": "dexterity", "base_defense": 2, "room": "guild_shadow_gallery",
    },
}

# v0.9.11 / v1.13.8: każda klasa ma trzy odrębne linie EQ.
# Pierwsza linia zachowuje stare ID/nazwy dla zgodności save'ów. Od v1.13.8
# linie mają realne profile pojedynczych części: zbalansowany, ofensywny i
# pancerny. Można je dowolnie mieszać; progi setu są liczone po klasie/slotach.
CLASS_EQUIPMENT_STYLES = {
    "Wojownik": ("Przysięgi", "Żelaznej Straży", "Lwiego Serca"),
    "Berserker": ("Krwawej Furii", "Rozbitego Łańcucha", "Wojennego Szału"),
    "Łotrzyk": ("Cienia", "Nocnego Ostrza", "Szeptu"),
    "Łowca": ("Echa", "Leśnego Tropu", "Sokolego Oka"),
    "Mnich": ("Ducha", "Pustej Dłoni", "Wewnętrznego Kręgu"),
    "Strażnik": ("Bastionu", "Kamiennej Tarczy", "Niezłomnej Warty"),
    "Mag": ("Arkanów", "Gwiezdnej Runy", "Kryształowego Splotu"),
    "Nekromanta": ("Dusz", "Kościanej Korony", "Cmentarnego Szeptu"),
    "Kapłan": ("Światła", "Świętego Płomienia", "Łaski"),
    "Czarownik": ("Otchłani", "Czarnego Paktu", "Pustego Księżyca"),
    "Druid": ("Korzeni", "Dzikiego Gaju", "Księżycowej Kory"),
    "Psionik": ("Umysłu", "Kryształowej Myśli", "Astralnego Echa"),
    "Mec": ("Rdzenia", "Tytanowej Ramy", "Reaktora Bojowego"),
    "Inżynier": ("Konstruktora", "Mistrza Narzędzi", "Mechanicznego Geniuszu"),
}

CLASS_EQUIPMENT_SLOT_DEFS = {
    "head": ("Hełm", 1, 90),
    "body": ("Pancerz", 3, 160),
    "shield": ("Tarcza", 2, 145),
    "hands": ("Rękawice", 0, 80),
    "legs": ("Nogawice", 2, 130),
    "feet": ("Buty", 0, 80),
    "charm": ("Talizman", 0, 120),
    "ring": ("Pierścień", 0, 140),
    "necklace": ("Naszyjnik", 1, 180),
    "earring": ("Kolczyk", 0, 130),
    "shoulders": ("Naramienniki", 2, 145),
    "belt": ("Pas", 1, 115),
    "cloak": ("Peleryna", 0, 150),
    "bracers": ("Karwasze", 0, 105),
    "bracelet": ("Bransoletka", 0, 125),
    "accessory": ("Akcesorium", 0, 170),
    "relic": ("Relikt", 0, 200),
}

# Pełna progresja klasowego EQ oparta na Biegłości klasy.
# Biegłość 1 zachowuje historyczne ID przedmiotów z v0.8.47,
# dzięki czemu już kupione/założone wyposażenie pozostaje zgodne z save'em.
CLASS_EQUIPMENT_MASTERY_LEVELS = (1,) + tuple(range(10, CLASS_MASTERY_MAX_LEVEL + 1, 10))
CLASS_EQUIPMENT_ITEMS_BY_CLASS_TIER = {}
CLASS_SHOP_CLASSES_BY_ROOM = {}
CLASS_SHOP_ITEMS_BY_ROOM = {
    "guild_martial_hall": [],
    "guild_shadow_gallery": [],
    "guild_body_hall": [],
    "guild_arcane_chamber": [],
    "guild_dark_chamber": [],
    "guild_sanctuary": [],
}

CLASS_EQUIPMENT_ITEM_IDS = set()


# v0.30.14 / v1.11.96: każde klasowe EQ ma DWIE podstawowe statystyki archetypu.
# Fizyczne: właściwa ofensywna Siła albo Zręczność + Kondycja.
# Magiczne: Inteligencja (UOSS Wisdom) + Siła Woli (UOSS Will).
# Zachowujemy łączny budżet starego
# pojedynczego affixu; Tier 1 dostaje minimalnie 1+1, aby obie statystyki
# były faktycznie obecne. Pierwsza statystyka pozostaje affixem możliwym
# do przekucia, druga jest stałym bonusem bazowym przedmiotu.
CLASS_EQUIPMENT_CLASS_PROFILES = {
    # primary_ratio = udział ofensywnej statystyki archetypu w łącznym budżecie statów.
    # properties różnicują realne zachowanie EQ poza samymi liczbami bazowymi.
    "Wojownik": {
        "primary_ratio": 0.56,
        "identity": "zbalansowana siła i wytrzymałość",
        "properties": {"physical_damage_pct": 0.55, "physical_defense_pct": 0.45},
    },
    "Berserker": {
        "primary_ratio": 0.78,
        "identity": "maksymalna Siła kosztem Kondycji",
        "properties": {"physical_damage_pct": 0.80, "max_hp_pct": 0.20},
    },
    "Łotrzyk": {
        "primary_ratio": 0.64,
        "identity": "Zręczność, unik i fizyczna ofensywa",
        "properties": {"dodge_pct": 0.60, "physical_damage_pct": 0.40},
    },
    "Łowca": {
        "primary_ratio": 0.68,
        "identity": "wysoka Zręczność i mobilna ofensywa",
        "properties": {"physical_damage_pct": 0.65, "dodge_pct": 0.35},
    },
    "Mnich": {
        "primary_ratio": 0.44,
        "identity": "Zręczność, Kondycja i defensywna równowaga",
        "properties": {"magic_defense_pct": 0.55, "dodge_pct": 0.45},
    },
    "Strażnik": {
        "primary_ratio": 0.28,
        "identity": "maksymalna Kondycja i obrona",
        "properties": {"physical_defense_pct": 0.70, "max_hp_pct": 0.30},
    },
    "Mag": {
        "primary_ratio": 0.78,
        "identity": "maksymalna Inteligencja i obrażenia magiczne",
        "properties": {"magic_damage_pct": 0.75, "max_mana_pct": 0.25},
    },
    "Nekromanta": {
        "primary_ratio": 0.66,
        "identity": "Inteligencja z domieszką przeżywalności",
        "properties": {"magic_damage_pct": 0.60, "max_hp_pct": 0.40},
    },
    "Kapłan": {
        "primary_ratio": 0.32,
        "identity": "wysoka Siła Woli, mana i obrona magiczna",
        "properties": {"max_mana_pct": 0.60, "magic_defense_pct": 0.40},
    },
    "Czarownik": {
        "primary_ratio": 0.72,
        "identity": "agresywna Inteligencja i moc magii",
        "properties": {"magic_damage_pct": 0.80, "max_mana_pct": 0.20},
    },
    "Druid": {
        "primary_ratio": 0.46,
        "identity": "Siła Woli, życie i mana w równowadze",
        "properties": {"max_hp_pct": 0.55, "max_mana_pct": 0.45},
    },
    "Psionik": {
        "primary_ratio": 0.54,
        "identity": "równowaga Inteligencji z psychiczną obroną",
        "properties": {"magic_defense_pct": 0.65, "max_mana_pct": 0.35},
    },
    "Mec": {
        "primary_ratio": 0.42,
        "identity": "Kondycja, Zręczność i stabilna ofensywa rdzenia",
        "properties": {"physical_defense_pct": 0.60, "max_hp_pct": 0.40},
    },
    "Inżynier": {
        "primary_ratio": 0.68,
        "identity": "Zręczność, Kondycja, narzędzia i mobilna ofensywa",
        "properties": {"physical_damage_pct": 0.60, "dodge_pct": 0.40},
    },
}

# Sloty też zmieniają charakter rozkładu: ręce/biżuteria bardziej ofensywne,
# pancerz i nogi bardziej w drugą (przeżywalnościową) statystykę archetypu.
CLASS_EQUIPMENT_SLOT_PRIMARY_BIAS = {
    "head": -0.01,
    "body": -0.09,
    "shield": -0.10,
    "hands": 0.09,
    "legs": -0.07,
    "feet": 0.02,
    "charm": 0.04,
    "ring": 0.08,
    "necklace": -0.03,
    "earring": 0.06,
    "shoulders": -0.08,
    "belt": -0.10,
    "cloak": 0.03,
    "bracers": 0.10,
    "bracelet": 0.08,
    "accessory": 0.00,
    "relic": 0.05,
}

CLASS_EQUIPMENT_SLOT_PROPERTY_SCALE = {
    "head": 1.00, "body": 1.15, "shield": 1.10, "hands": 0.95, "legs": 1.10,
    "feet": 0.90, "charm": 0.85, "ring": 0.85, "necklace": 1.00, "earring": 0.82,
    "shoulders": 1.08, "belt": 1.05, "cloak": 0.92, "bracers": 0.95,
    "bracelet": 0.90, "accessory": 1.12, "relic": 1.20,
}


# v1.14.8: wspólny rynek skupu surowców, zachowujący indywidualną wartość
# każdego gatunku ryby / rudy / drewna / rośliny. Nie modyfikuje katalogu
# przedmiotów ani historycznego ekwipunku postaci.
from functools import lru_cache as _resource_market_cache_v1148


def _resource_market_authored_coins_v1148(item):
    return max(0, int(item.get("sell_silver", 0) or 0)) + (        100 * max(0, int(item.get("sell_gold", 0) or 0))
    ) + 100_000_000 * max(0, int(item.get("sell_mithril", 0) or 0))


def _resource_market_base_v1148(category, base_id):
    from core.progression_resources import (
        v0190_resource_stage, v0190_resource_sale_coins,
        v1138_resource_sale_base_coins,
    )
    base = ITEMS.get(base_id, {})
    if not base:
        return 1
    stage = (
        fish_unlock_level(base_id)
        if category == "fish"
        else v0190_resource_stage(base_id, base)
    )
    # Stary authored price i Generator pozostają dolnym ograniczeniem.
    # Etap jest brany z rzeczywistej tabeli odblokowań, a nie z domysłów
    # opartych tylko na nazwie ryby.
    value = max(
        1,
        _resource_market_authored_coins_v1148(base),
        int(v0190_resource_sale_coins(base_id, base)),
        int(v1138_resource_sale_base_coins(stage)),
    )
    if category == "fish":
        value = max(1, int(round(
            value * v096_fish_price_scale(base_id)
            * fish_trophy_value_multiplier_v1138(base_id)
        )))
    return value


@_resource_market_cache_v1148(maxsize=5)
def _resource_market_catalog_v1148(category):
    """Z góry jednoznaczne ceny gatunków, przy podobnych cenach bez spłaszczeń.

    Sortujemy według realnej wartości, więc korekta rozstrzyga tylko kolizje;
    nie zmienia całej krzywej i nie osłabia legendarnych okazów.
    """
    categories = {
        "fish": FISH_RESOURCE_IDS,
        "ore": ORE_RESOURCE_IDS,
        "wood": WOOD_RESOURCE_IDS,
        "herb": HERB_RESOURCE_IDS,
    }
    ids = set(categories.get(category, ()))
    if category == "ore":
        # Surowe kamienie i geody również są częścią sakwy górnika.
        from systems.equipment_crafting import MINING_STORAGE_IDS
        ids.update(MINING_STORAGE_IDS)
    values = [
        (_resource_market_base_v1148(category, item_id), item_id)
        for item_id in ids if item_id in ITEMS
        and not ITEMS[item_id].get("rare_resource_variant")
    ]
    values.sort(key=lambda pair: (pair[0], pair[1]))
    result = {}
    previous = 0
    for natural, item_id in values:
        # Minimum 1 srebro różnicy, nawet dla tanich początkowych ryb.
        # Ceny wciąż zbliżone do starej, gdy naturalna wycena już się różni.
        assigned = max(natural, previous + 1)
        result[item_id] = assigned
        previous = assigned
    return result


@_resource_market_cache_v1148(maxsize=32)
def _resource_market_quote_catalog_v1270(category, demand):
    """Ensure distinct NPC prices after a six-hour market demand adjustment.

    Demand below 100% can round adjacent base prices to the same silver value.
    The existing authored order is retained and tied quotes gain only 1 silver.
    """
    catalogue = _resource_market_catalog_v1148(category)
    quotes = {}
    last = 0
    for item_id, base_price in sorted(catalogue.items(), key=lambda r: (r[1], r[0])):
        candidate = max(1, int(round(base_price * demand)))
        last = max(candidate, last + 1)
        quotes[item_id] = last
    return quotes


def profession_resource_market_value_v1148(item_id, item=None, category=None):
    """Kanoniczna cena skupu/szacowania zasobu w srebrze (100 = 1 złoto).

    Rzadki okaz dziedziczy dokładnie raz cenę gatunku i mnożnik wariantu.
    Przezroczysta dla zapisu SQLite i dla istniejących identyfikatorów.
    """
    item = item or ITEMS.get(item_id, {}) or {}
    base_id = str(item.get("base_resource_id") or item_id)
    if category is None:
        if item_id in FISH_STORAGE_IDS or base_id in FISH_RESOURCE_IDS:
            category = "fish"
        elif item_id in ORE_STORAGE_IDS or base_id in ORE_RESOURCE_IDS:
            category = "ore"
        elif item_id in WOOD_STORAGE_IDS or base_id in WOOD_RESOURCE_IDS:
            category = "wood"
        elif item_id in HERB_STORAGE_IDS or base_id in HERB_RESOURCE_IDS:
            category = "herb"
        else:
            category = "ore"  # surowe klejnoty/geody ze składu górniczego
    catalog = _resource_market_catalog_v1148(category)
    normal = catalog.get(base_id)
    if normal is None:
        normal = _resource_market_base_v1148(category, base_id)
    variant_factor = max(1.0, float(item.get("rare_value_multiplier", 1) or 1))
    from systems.market_dynamics_v1250 import market_demand_v1250
    # Dynamic demand changes the *base resource* quote once. A rare variant
    # multiplies that displayed quote afterwards so variants remain worth
    # exactly their advertised multiple (and NPC sale audits remain valid).
    demand = market_demand_v1250(category)
    # Apply rounding while keeping resource prices unique within a category;
    # rare variants multiply the final base quote exactly once.
    adjusted_base = _resource_market_quote_catalog_v1270(category, demand).get(base_id)
    if adjusted_base is None:
        adjusted_base = max(1, int(round(normal * demand)))
    return max(1, int(round(adjusted_base * variant_factor)))
