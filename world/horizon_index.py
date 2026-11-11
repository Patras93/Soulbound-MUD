# -*- coding: utf-8 -*-
"""Publiczny rejestr krain v109. Definicje sa w modulach rozdzialow."""
from world.horizons.entry import entry
from world.horizons.przebudzenie import CHAPTER_ONE
from world.horizons.zapomniani import CHAPTER_TWO
from world.horizons.wiecznosc import CHAPTER_THREE

CHAPTERS = (CHAPTER_ONE, CHAPTER_TWO, CHAPTER_THREE)
REGIONS = tuple(region for chapter in CHAPTERS for region in chapter)
assert len(REGIONS) == 12 and len(CHAPTERS) == 3
assert len({r[0] for r in REGIONS}) == 12
assert len({r[1] for r in REGIONS}) == 12
assert len({name for region in REGIONS for name in region[5]}) == 144
