# -*- coding: utf-8 -*-
"""Static Soulbound catalog. Data only; gameplay logic lives elsewhere."""
from data.catalog_parts.mobs_01 import build_catalog as _mobs_part_01
from data.catalog_parts.mobs_02 import build_catalog as _mobs_part_02

MOB_TEMPLATES = {}
MOB_TEMPLATES.update(_mobs_part_01())
MOB_TEMPLATES.update(_mobs_part_02())

from systems.v115.playable_regions import build_mobs as _v115_mobs
if set(MOB_TEMPLATES).intersection(_v115_mobs()):
    raise ValueError('v115: kolizja ID potworów')
MOB_TEMPLATES.update(_v115_mobs())

# v115: own dungeon mobs and bosses; base world mobs remain unchanged.
from systems.v115.regional_dungeons import build_mobs as _v115_dungeon_mobs
if set(MOB_TEMPLATES).intersection(_v115_dungeon_mobs()):
    raise ValueError('v115: kolizja potworów lochu')
MOB_TEMPLATES.update(_v115_dungeon_mobs())

__all__ = ['MOB_TEMPLATES']
