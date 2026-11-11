# -*- coding: utf-8 -*-
"""Wspólne zależności db_world, zachowane bez zmiany działania."""

# -*- coding: utf-8 -*-
"""World, dungeon, exploration, records and world progression persistence."""

import json
import time

from config.balance import MINE_MIN_FLOOR
from core.bootstrap_economy_professions import V019_SAFE_INT
from core.progression_resources import roll_mine_wall_hits_required
from data.items import ITEMS
from storage.db_shared import base_fish_species_id
from world import dynamic_world_generator as dynamic_world_v029


def _dbw_crypt_floor_number_lazy(room_id):
    from systems.dungeons_regions import crypt_floor_number as _impl
    return _impl(room_id)


def _dbw_is_astral_boss_floor_lazy(floor):
    from systems.dungeons_regions import is_astral_boss_floor as _impl
    return _impl(floor)


def _dbw_is_crypt_boss_floor_lazy(floor):
    from systems.dungeons_regions import is_crypt_boss_floor as _impl
    return _impl(floor)


def _dbw_astral_min_floor_lazy():
    from systems.dungeons_regions import ASTRAL_MIN_FLOOR
    return int(ASTRAL_MIN_FLOOR)


def _dbw_canonical_bestiary_template_id_lazy(value):
    from world.dynamic_content import canonical_bestiary_template_id as _impl
    return _impl(value)


def _dbw_boss_codex_drop_is_unique_lazy(item_id):
    from world.dynamic_content import boss_codex_drop_is_unique as _impl
    return _impl(item_id)


def _dbw_boss_collection_catalog_lazy():
    from world.dynamic_content import BOSS_COLLECTION_CATALOG
    return BOSS_COLLECTION_CATALOG

