# -*- coding: utf-8 -*-
"""Wspólne zależności db_world, zachowane bez zmiany działania."""
# v4.20.0: bound, AST-identical method implementations (MRO unchanged)
from core.legacy_method_binding_v4200 import bind_legacy_method_v4200 as _sb420_bind
import storage.methods_v4200.databaseworld_part01 as _sb420_src_01
# DatabaseWorldMixin.unlock_crypt_checkpoint -> storage/methods_v4200/databaseworld_part01.py
# DatabaseWorldMixin.unlock_astral_checkpoint -> storage/methods_v4200/databaseworld_part01.py
# DatabaseWorldMixin.boss_floor_cleared -> storage/methods_v4200/databaseworld_part01.py
# DatabaseWorldMixin.mine_progress -> storage/methods_v4200/databaseworld_part01.py
# DatabaseWorldMixin.add_mine_wall_hit -> storage/methods_v4200/databaseworld_part01.py
# DatabaseWorldMixin.mine_tunnel_hit_v1251 -> storage/methods_v4200/databaseworld_part01.py
# DatabaseWorldMixin.mine_discover_v1260 -> storage/methods_v4200/databaseworld_part01.py
# DatabaseWorldMixin.mercenary_memory_read_v1260 -> storage/methods_v4200/databaseworld_part01.py
# DatabaseWorldMixin.grand_expedition_visit_v1260 -> storage/methods_v4200/databaseworld_part01.py
# DatabaseWorldMixin.mine_startup_status -> storage/methods_v4200/databaseworld_part01.py
# DatabaseWorldMixin.mark_room_discovered_with_points_v2322 -> storage/methods_v4200/databaseworld_part01.py
# DatabaseWorldMixin.record_bestiary_kill -> storage/methods_v4200/databaseworld_part01.py
# DatabaseWorldMixin.record_boss_codex_kill -> storage/methods_v4200/databaseworld_part01.py
# DatabaseWorldMixin.promote_nemesis_v029 -> storage/methods_v4200/databaseworld_part01.py
# DatabaseWorldMixin.add_ascension_xp_v021 -> storage/methods_v4200/databaseworld_part01.py
# DatabaseWorldMixin.mark_instance_floor_visited -> storage/methods_v4200/databaseworld_part01.py
# DatabaseWorldMixin.instance_checkpoint_floors -> storage/methods_v4200/databaseworld_part01.py
# DatabaseWorldMixin.record_activity_v0560 -> storage/methods_v4200/databaseworld_part01.py
# DatabaseWorldMixin.bounty_board_state -> storage/methods_v4200/databaseworld_part01.py
# DatabaseWorldMixin.save_bounty_board_state -> storage/methods_v4200/databaseworld_part01.py
# DatabaseWorldMixin.save_dynamic_world_quest_v015 -> storage/methods_v4200/databaseworld_part01.py
# DatabaseWorldMixin.record_fish_catch -> storage/methods_v4200/databaseworld_part01.py
import storage.methods_v4200.databaseworld_part02 as _sb420_src_02
# DatabaseWorldMixin.record_fishing_global_v022 -> storage/methods_v4200/databaseworld_part02.py
# DatabaseWorldMixin.add_world_project_contribution_v022 -> storage/methods_v4200/databaseworld_part02.py
# DatabaseWorldMixin.postal_delivery_state_v0522 -> storage/methods_v4200/databaseworld_part02.py
# DatabaseWorldMixin.save_postal_delivery_state_v0522 -> storage/methods_v4200/databaseworld_part02.py
# DatabaseWorldMixin.courier_guild_state_v0530 -> storage/methods_v4200/databaseworld_part02.py
# DatabaseWorldMixin.save_courier_guild_state_v0530 -> storage/methods_v4200/databaseworld_part02.py
# DatabaseWorldMixin.add_city_reputation_v0710 -> storage/methods_v4200/databaseworld_part02.py

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

