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

# v110: no missing/invisible profession equipment. Authorised staging and
# installed v110 only; v109 historical shops are otherwise byte-identical.
from systems.runtime_activation import enabled as _v110_shops_enabled
if _v110_shops_enabled():
    from core.archetypes.expansion import PROFESSION_SPECS as _v110_professions
    SHOPS['market'].extend('v11000_prof_tool_'+str(i+1)
                           for i in range(len(_v110_professions)))

__all__ = ['SHOPS']
