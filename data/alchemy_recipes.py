# -*- coding: utf-8 -*-
"""Static Soulbound catalog. Data only; gameplay logic lives elsewhere."""
ALCHEMY_RECIPES = {
    "healing_potion": {
        "name": "Mikstura leczenia", "stations": ("herbalist_hut",),
        "ingredients": {"nettle": 1, "chamomile": 1},
        "output": "healing_potion", "quantity": 1,
        "min_tool_level": 5,
        "desc": "Alchemia level 5. Pokrzywa + Rumianek. Przywraca 35 HP.",
    },
    "mana_potion": {
        "name": "Mikstura Many", "stations": ("herbalist_hut",),
        "ingredients": {"mint": 1, "lemon_balm": 1},
        "output": "mana_potion", "quantity": 1,
        "desc": "Mięta + Melisa. Przywraca 35 Many.",
    },
    "greater_healing_potion": {
        "name": "Wielka Mikstura Leczenia", "stations": ("herbalist_hut",),
        "ingredients": {"yarrow": 1, "ginseng": 1, "mandrake": 1},
        "output": "greater_healing_potion", "quantity": 1,
        "desc": "Krwawnik + Żeń-szeń + Mandragora. Przywraca 70 HP.",
    },
    "greater_mana_potion": {
        "name": "Wielka Mikstura Many", "stations": ("herbalist_hut",),
        "ingredients": {"sage": 1, "moonflower": 1, "star_moss": 1},
        "output": "greater_mana_potion", "quantity": 1,
        "desc": "Szałwia + Kwiat księżycowy + Gwiezdny mech. Przywraca 70 Many.",
    },
    "vitality_elixir": {
        "name": "Eliksir Witalności", "stations": ("herbalist_hut",),
        "ingredients": {"ginseng": 1, "soulroot": 1, "phoenix_leaf": 1},
        "output": "vitality_elixir", "quantity": 1,
        "desc": "Przywraca 55 HP i 30 Many.",
    },
    "soul_elixir": {
        "name": "Eliksir Duszy", "stations": ("herbalist_hut",),
        "ingredients": {"soulroot": 2, "astral_lotus": 1, "soul_shard": 2},
        "output": "soul_elixir", "quantity": 1,
        "desc": "Daje 80 Soul XP.",
    },
    "supreme_healing_potion": {
        "name": "Najwyższa Mikstura Leczenia", "stations": ("herbalist_hut",),
        "ingredients": {"sunfire_bloom": 2, "phoenix_leaf": 1},
        "output": "supreme_healing_potion", "quantity": 1,
        "min_tool_level": 100, "tool_xp": 24,
        "desc": "Alchemia level 100. Przywraca do 130 HP.",
    },
    "supreme_mana_potion": {
        "name": "Najwyższa Mikstura Many", "stations": ("herbalist_hut",),
        "ingredients": {"dragon_sage": 2, "star_moss": 1},
        "output": "supreme_mana_potion", "quantity": 1,
        "min_tool_level": 120, "tool_xp": 28,
        "desc": "Alchemia level 120. Przywraca do 130 Many.",
    },
    "grand_vitality_elixir": {
        "name": "Wielki Eliksir Witalności", "stations": ("herbalist_hut",),
        "ingredients": {"astral_orchid": 2, "soulroot": 1},
        "output": "grand_vitality_elixir", "quantity": 1,
        "min_tool_level": 140, "tool_xp": 32,
        "desc": "Alchemia level 140. Przywraca do 120 HP i 80 Many.",
    },
    "soul_tonic": {
        "name": "Tonik Duszy", "stations": ("herbalist_hut",),
        "ingredients": {"void_lotus": 2, "astral_lotus": 1, "soul_shard": 5},
        "output": "soul_tonic", "quantity": 1,
        "min_tool_level": 160, "tool_xp": 36,
        "desc": "Alchemia level 160. Daje 180 Soul XP.",
    },
    "astral_restoration_elixir": {
        "name": "Astralny Eliksir Odnowy", "stations": ("herbalist_hut",),
        "ingredients": {"phoenix_crown": 2, "sunfire_bloom": 1},
        "output": "astral_restoration_elixir", "quantity": 1,
        "min_tool_level": 180, "tool_xp": 40,
        "desc": "Alchemia level 180. Przywraca do 180 HP i 120 Many.",
    },
    "eternal_soul_elixir": {
        "name": "Eliksir Wiecznej Duszy", "stations": ("herbalist_hut",),
        "ingredients": {"eternal_blossom": 2, "void_lotus": 1, "soul_shard": 10},
        "output": "eternal_soul_elixir", "quantity": 1,
        "min_tool_level": 200, "tool_xp": 50,
        "desc": "Alchemia level 200. Daje 400 Soul XP.",
    },
}

__all__ = ['ALCHEMY_RECIPES']
