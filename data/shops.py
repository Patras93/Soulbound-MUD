# -*- coding: utf-8 -*-
"""Static Soulbound catalog. Data only; gameplay logic lives elsewhere."""
SHOPS = {
    "fish_market": ["fishing_rod"],
    "market": ["healing_potion", "leather_vest", "lucky_charm"],
    "inn": ["healing_potion", "chef_knife"],
    "forge": [
        "iron_helmet",
        "iron_guard",
        "iron_gauntlets",
        "iron_leggings",
        "iron_boots",
        "forge_charm",
        "crafting_hammer",
    ],
    "cave_entrance": ["pickaxe"],
    "lumberjack_camp": ["saw"],
    "herbalist_hut": ["herbalist_sickle", "alchemy_mortar"],
    "jeweler_workshop": ["jeweler_pliers"],
}

__all__ = ['SHOPS']
