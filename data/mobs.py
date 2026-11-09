# -*- coding: utf-8 -*-
"""Static Soulbound catalog. Data only; gameplay logic lives elsewhere."""
from data.catalogs_v109.mobs_01 import build_catalog as _mobs_part_01
from data.catalogs_v109.mobs_02 import build_catalog as _mobs_part_02

MOB_TEMPLATES = {}
MOB_TEMPLATES.update(_mobs_part_01())
MOB_TEMPLATES.update(_mobs_part_02())

__all__ = ['MOB_TEMPLATES']
