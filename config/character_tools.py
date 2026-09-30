# -*- coding: utf-8 -*-
"""Shared character-bound tool IDs.

Kept in a lightweight config module so database schema code can import the
canonical tool set without importing world/mining runtime modules.
"""

CHARACTER_BOUND_TOOL_IDS = frozenset({
    "fishing_rod",
    "pickaxe",
    "saw",
    "crafting_hammer",
    "chef_knife",
    "herbalist_sickle",
    "alchemy_mortar",
    "jeweler_pliers",
    "tailor_kit",
    "tanning_knife",
    "carpenter_tools",
    "runic_focus",
    "archaeology_brush",
    "surveyor_compass",
})
