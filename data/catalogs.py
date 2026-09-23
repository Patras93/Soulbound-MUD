# -*- coding: utf-8 -*-
"""Convenient read-only import surface for Soulbound's static catalogs."""
from data.items import ITEMS
from data.rooms import ROOMS
from data.npcs import NPCS
from data.quests import QUESTS
from data.mobs import MOB_TEMPLATES
from data.shops import SHOPS
from data.crafting_recipes import CRAFT_RECIPES
from data.alchemy_recipes import ALCHEMY_RECIPES

__all__ = [
    "ITEMS", "ROOMS", "NPCS", "QUESTS", "MOB_TEMPLATES", "SHOPS",
    "CRAFT_RECIPES", "ALCHEMY_RECIPES",
]
