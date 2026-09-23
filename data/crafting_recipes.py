# -*- coding: utf-8 -*-
"""Static Soulbound catalog. Data only; gameplay logic lives elsewhere."""
CRAFT_RECIPES = {
    "iron_ingot": {
        "name": "Żelazna sztabka", "stations": ("forge",),
        "ingredients": {"iron_ore": 1}, "output": "iron_ingot", "quantity": 1,
        "desc": "Przetop 1 Rudę żelaza w 1 Żelazną sztabkę.",
    },
    "silver_ingot": {
        "name": "Srebrna sztabka", "stations": ("forge",),
        "ingredients": {"silver_ore": 1}, "output": "silver_ingot", "quantity": 1,
        "desc": "Przetop 1 Rudę srebra w 1 Srebrną sztabkę.",
    },
    "gold_ingot": {
        "name": "Złota sztabka", "stations": ("forge",),
        "ingredients": {"gold_ore": 1}, "output": "gold_ingot", "quantity": 1,
        "desc": "Przetop 1 Rudę złota w 1 Złotą sztabkę.",
    },
    "oak_plank": {
        "name": "Deska dębowa", "stations": ("lumberjack_camp",),
        "ingredients": {"oak_log": 2}, "output": "oak_plank", "quantity": 1,
        "desc": "Obrób 2 Pnie dębu w 1 Deskę dębową.",
    },
    "ash_plank": {
        "name": "Deska jesionowa", "stations": ("lumberjack_camp",),
        "ingredients": {"ash_log": 2}, "output": "ash_plank", "quantity": 1,
        "desc": "Obrób 2 Pnie jesionu w 1 Deskę jesionową.",
    },
    "yew_plank": {
        "name": "Deska cisowa", "stations": ("lumberjack_camp",),
        "ingredients": {"yew_log": 2}, "output": "yew_plank", "quantity": 1,
        "desc": "Obrób 2 Pnie cisu w 1 Deskę cisową.",
    },
    "ironwood_plank": {
        "name": "Deska żelaznego drzewa", "stations": ("lumberjack_camp",),
        "ingredients": {"ironwood_log": 2}, "output": "ironwood_plank", "quantity": 1,
        "desc": "Obrób 2 Pnie żelaznego drzewa w 1 Deskę.",
    },
    "spiritwood_plank": {
        "name": "Deska drzewa duchów", "stations": ("lumberjack_camp",),
        "ingredients": {"spiritwood_log": 2}, "output": "spiritwood_plank", "quantity": 1,
        "desc": "Obrób 2 Pnie drzewa duchów w 1 magiczną Deskę.",
    },
    "oak_iron_charm": {
        "name": "Talizman Dębu i Żelaza", "stations": ("forge",),
        "ingredients": {"oak_plank": 2, "iron_ingot": 1},
        "output": "oak_iron_charm", "quantity": 1,
        "desc": "Talizman obronny +2 z drewna dębowego i żelaza.",
    },
    "yew_silver_charm": {
        "name": "Talizman Cisu i Srebra", "stations": ("forge",),
        "ingredients": {"yew_plank": 2, "silver_ingot": 1},
        "output": "yew_silver_charm", "quantity": 1,
        "desc": "Rzadki talizman obronny +3.",
    },
    "spiritwood_gold_charm": {
        "name": "Talizman Drzewa Dusz", "stations": ("forge",),
        "ingredients": {"spiritwood_plank": 2, "gold_ingot": 1},
        "output": "spiritwood_gold_charm", "quantity": 1,
        "desc": "Zaawansowany talizman obronny +5.",
    },
    "runic_guard_charm": {
        "name": "Runiczny Talizman Straży", "stations": ("forge",),
        "ingredients": {"cobalt_ingot": 2, "runewood_log": 2},
        "output": "runic_guard_charm", "quantity": 1,
        "min_tool_level": 100, "tool_xp": 24,
        "desc": "Kowalstwo level 100. 2 Kobaltowe sztabki + 2 Runiczne drewno. Obrona +6, Kondycja +2.",
    },
    "dragonforge_charm": {
        "name": "Talizman Smoczej Kuźni", "stations": ("forge",),
        "ingredients": {"runestone_ingot": 2, "dragonwood_log": 2},
        "output": "dragonforge_charm", "quantity": 1,
        "min_tool_level": 120, "tool_xp": 28,
        "desc": "Kowalstwo level 120. 2 Runiczne sztabki + 2 Smocze drewno. Obrona +7, Siła +3.",
    },
    "astral_forge_charm": {
        "name": "Astralny Talizman Kuźni", "stations": ("forge",),
        "ingredients": {"dragonsteel_ingot": 2, "astralwood_log": 2},
        "output": "astral_forge_charm", "quantity": 1,
        "min_tool_level": 140, "tool_xp": 32,
        "desc": "Kowalstwo level 140. 2 Sztabki Smoczej Stali + 2 Astralne drewno. Obrona +8, Inteligencja +3.",
    },
    "void_guard_charm": {
        "name": "Talizman Straży Pustki", "stations": ("forge",),
        "ingredients": {"astral_ingot": 2, "voidwood_log": 2},
        "output": "void_guard_charm", "quantity": 1,
        "min_tool_level": 160, "tool_xp": 36,
        "desc": "Kowalstwo level 160. 2 Astralne sztabki + 2 Drewno Pustki. Obrona +9, Siła Woli +4.",
    },
    "worldheart_charm": {
        "name": "Talizman Serca Świata", "stations": ("forge",),
        "ingredients": {"void_ingot": 2, "starheart_log": 2},
        "output": "worldheart_charm", "quantity": 1,
        "min_tool_level": 180, "tool_xp": 40,
        "desc": "Kowalstwo level 180. 2 Sztabki Pustki + 2 Drewno Serca Gwiazdy. Obrona +10, HP +60.",
    },
    "eternal_soul_charm": {
        "name": "Talizman Wiecznej Duszy", "stations": ("forge",),
        "ingredients": {"eternium_ingot": 2, "eternal_worldwood_log": 2},
        "output": "eternal_soul_charm", "quantity": 1,
        "min_tool_level": 200, "tool_xp": 50,
        "desc": "Kowalstwo level 200. 2 Sztabki Eternium + 2 Wieczne drewno. Obrona +12, Zręczność +5.",
    },
}

__all__ = ['CRAFT_RECIPES']
