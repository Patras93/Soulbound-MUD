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


from .db_world_parts_v109 import (
    DungeonsCheckpointsV109Mixin,
    MinesV109Mixin,
    MercenariesExpeditionsV109Mixin,
    ExplorationV109Mixin,
    BestiaryCodexV109Mixin,
    CollectionsV109Mixin,
    NemesisAscensionV109Mixin,
    InstancesChestsV109Mixin,
    ActivityAchievementsV109Mixin,
    BountiesQuestsV109Mixin,
    ReputationsLifetimeV109Mixin,
    FishingV109Mixin,
    ProjectsContractsV109Mixin,
)

class DatabaseWorldMixin(
    DungeonsCheckpointsV109Mixin,
    MinesV109Mixin,
    MercenariesExpeditionsV109Mixin,
    ExplorationV109Mixin,
    BestiaryCodexV109Mixin,
    CollectionsV109Mixin,
    NemesisAscensionV109Mixin,
    InstancesChestsV109Mixin,
    ActivityAchievementsV109Mixin,
    BountiesQuestsV109Mixin,
    ReputationsLifetimeV109Mixin,
    FishingV109Mixin,
    ProjectsContractsV109Mixin,
):
    """Dotychczasowe API zapisu świata; metody chronione pozostawiono."""

    def unlock_crypt_checkpoint(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method unlock_crypt_checkpoint")


    def unlock_astral_checkpoint(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method unlock_astral_checkpoint")


    def boss_floor_cleared(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method boss_floor_cleared")


    def mark_boss_floor_cleared(self, account_id, dungeon_kind, floor):
        dungeon_kind = str(dungeon_kind or "").strip().lower()
        floor = max(1, int(floor))
        cur = self.conn.execute(
            "INSERT OR IGNORE INTO boss_floor_clears(account_id,dungeon_kind,floor) VALUES(?,?,?)",
            (account_id, dungeon_kind, floor),
        )
        self.conn.commit()
        return cur.rowcount > 0


    def ensure_mine_progress(self, account_id):
        self.conn.execute(
            """
            INSERT OR IGNORE INTO mine_progress(
                account_id,max_floor_unlocked,wall_hits,wall_required_hits
            ) VALUES(?,1,0,0)
            """,
            (account_id,),
        )
        self.conn.commit()


    def mine_progress(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method mine_progress")


    def add_mine_wall_hit(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method add_mine_wall_hit")


    def mine_tunnel_hit_v1251(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method mine_tunnel_hit_v1251")


    def mine_discover_v1260(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method mine_discover_v1260")


    def mercenary_memory_read_v1260(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method mercenary_memory_read_v1260")


    def grand_expedition_visit_v1260(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method grand_expedition_visit_v1260")


    def mine_startup_status(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method mine_startup_status")


    def mark_room_discovered(self, account_id, room_id):
        cur = self.conn.execute(
            "INSERT OR IGNORE INTO exploration_rooms(account_id,room_id) VALUES(?,?)",
            (account_id, room_id),
        )
        self.conn.commit()
        return cur.rowcount > 0


    def mark_room_discovered_with_points_v2322(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method mark_room_discovered_with_points_v2322")


    def exploration_reward_claimed(self, account_id, zone):
        row = self.conn.execute(
            "SELECT 1 FROM exploration_rewards WHERE account_id=? AND zone=?",
            (account_id, zone),
        ).fetchone()
        return bool(row)


    def record_bestiary_kill(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method record_bestiary_kill")


    def record_boss_codex_kill(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method record_boss_codex_kill")


    def promote_nemesis_v029(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method promote_nemesis_v029")


    def add_ascension_xp_v021(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method add_ascension_xp_v021")


    def mark_instance_floor_visited(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method mark_instance_floor_visited")


    def instance_checkpoint_floors(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method instance_checkpoint_floors")


    def record_activity_v0560(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method record_activity_v0560")


    def bounty_board_state(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method bounty_board_state")


    def save_bounty_board_state(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method save_bounty_board_state")


    def save_dynamic_world_quest_v015(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method save_dynamic_world_quest_v015")


    def lifetime_stat(self, account_id, stat_key):
        row = self.conn.execute(
            "SELECT value FROM lifetime_statistics WHERE account_id=? AND stat_key=?",
            (account_id, str(stat_key)),
        ).fetchone()
        return max(0, int(row["value"] or 0)) if row else 0


    def record_fish_catch(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method record_fish_catch")


    def record_fishing_global_v022(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method record_fishing_global_v022")


    def add_world_project_contribution_v022(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method add_world_project_contribution_v022")


    def postal_delivery_state_v0522(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method postal_delivery_state_v0522")


    def save_postal_delivery_state_v0522(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method save_postal_delivery_state_v0522")


    def courier_guild_state_v0530(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method courier_guild_state_v0530")


    def save_courier_guild_state_v0530(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method save_courier_guild_state_v0530")


    def record_courier_city_visit_v0530(self, account_id, city_name):
        city_name = str(city_name or "").strip()
        if not city_name:
            return self.courier_guild_state_v0530(account_id)
        state = self.courier_guild_state_v0530(account_id)
        visited = set(state["visited_cities"])
        if city_name in visited:
            return state
        visited.add(city_name)
        return self.save_courier_guild_state_v0530(
            account_id, visited_cities=sorted(visited)
        )


    def city_reputations_v0710(self, account_id):
        rows = self.conn.execute(
            "SELECT city_name,reputation FROM city_reputation_v0710 WHERE account_id=?",
            (int(account_id),),
        ).fetchall()
        return {
            str(row["city_name"]): max(1, min(400, int(row["reputation"] or 1)))
            for row in rows
        }


    def add_city_reputation_v0710(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method add_city_reputation_v0710")



# v4.20.0: exact historical implementations rebound onto original class.
DatabaseWorldMixin.unlock_crypt_checkpoint = _sb420_bind(_sb420_src_01.unlock_crypt_checkpoint, globals(), "DatabaseWorldMixin")
DatabaseWorldMixin.unlock_astral_checkpoint = _sb420_bind(_sb420_src_01.unlock_astral_checkpoint, globals(), "DatabaseWorldMixin")
DatabaseWorldMixin.boss_floor_cleared = _sb420_bind(_sb420_src_01.boss_floor_cleared, globals(), "DatabaseWorldMixin")
DatabaseWorldMixin.mine_progress = _sb420_bind(_sb420_src_01.mine_progress, globals(), "DatabaseWorldMixin")
DatabaseWorldMixin.add_mine_wall_hit = _sb420_bind(_sb420_src_01.add_mine_wall_hit, globals(), "DatabaseWorldMixin")
DatabaseWorldMixin.mine_tunnel_hit_v1251 = _sb420_bind(_sb420_src_01.mine_tunnel_hit_v1251, globals(), "DatabaseWorldMixin")
DatabaseWorldMixin.mine_discover_v1260 = _sb420_bind(_sb420_src_01.mine_discover_v1260, globals(), "DatabaseWorldMixin")
DatabaseWorldMixin.mercenary_memory_read_v1260 = _sb420_bind(_sb420_src_01.mercenary_memory_read_v1260, globals(), "DatabaseWorldMixin")
DatabaseWorldMixin.grand_expedition_visit_v1260 = _sb420_bind(_sb420_src_01.grand_expedition_visit_v1260, globals(), "DatabaseWorldMixin")
DatabaseWorldMixin.mine_startup_status = _sb420_bind(_sb420_src_01.mine_startup_status, globals(), "DatabaseWorldMixin")
DatabaseWorldMixin.mark_room_discovered_with_points_v2322 = _sb420_bind(_sb420_src_01.mark_room_discovered_with_points_v2322, globals(), "DatabaseWorldMixin")
DatabaseWorldMixin.record_bestiary_kill = _sb420_bind(_sb420_src_01.record_bestiary_kill, globals(), "DatabaseWorldMixin")
DatabaseWorldMixin.record_boss_codex_kill = _sb420_bind(_sb420_src_01.record_boss_codex_kill, globals(), "DatabaseWorldMixin")
DatabaseWorldMixin.promote_nemesis_v029 = _sb420_bind(_sb420_src_01.promote_nemesis_v029, globals(), "DatabaseWorldMixin")
DatabaseWorldMixin.add_ascension_xp_v021 = _sb420_bind(_sb420_src_01.add_ascension_xp_v021, globals(), "DatabaseWorldMixin")
DatabaseWorldMixin.mark_instance_floor_visited = _sb420_bind(_sb420_src_01.mark_instance_floor_visited, globals(), "DatabaseWorldMixin")
DatabaseWorldMixin.instance_checkpoint_floors = _sb420_bind(_sb420_src_01.instance_checkpoint_floors, globals(), "DatabaseWorldMixin")
DatabaseWorldMixin.record_activity_v0560 = _sb420_bind(_sb420_src_01.record_activity_v0560, globals(), "DatabaseWorldMixin")
DatabaseWorldMixin.bounty_board_state = _sb420_bind(_sb420_src_01.bounty_board_state, globals(), "DatabaseWorldMixin")
DatabaseWorldMixin.save_bounty_board_state = _sb420_bind(_sb420_src_01.save_bounty_board_state, globals(), "DatabaseWorldMixin")
DatabaseWorldMixin.save_dynamic_world_quest_v015 = _sb420_bind(_sb420_src_01.save_dynamic_world_quest_v015, globals(), "DatabaseWorldMixin")
DatabaseWorldMixin.record_fish_catch = _sb420_bind(_sb420_src_01.record_fish_catch, globals(), "DatabaseWorldMixin")
DatabaseWorldMixin.record_fishing_global_v022 = _sb420_bind(_sb420_src_02.record_fishing_global_v022, globals(), "DatabaseWorldMixin")
DatabaseWorldMixin.add_world_project_contribution_v022 = _sb420_bind(_sb420_src_02.add_world_project_contribution_v022, globals(), "DatabaseWorldMixin")
DatabaseWorldMixin.postal_delivery_state_v0522 = _sb420_bind(_sb420_src_02.postal_delivery_state_v0522, globals(), "DatabaseWorldMixin")
DatabaseWorldMixin.save_postal_delivery_state_v0522 = _sb420_bind(_sb420_src_02.save_postal_delivery_state_v0522, globals(), "DatabaseWorldMixin")
DatabaseWorldMixin.courier_guild_state_v0530 = _sb420_bind(_sb420_src_02.courier_guild_state_v0530, globals(), "DatabaseWorldMixin")
DatabaseWorldMixin.save_courier_guild_state_v0530 = _sb420_bind(_sb420_src_02.save_courier_guild_state_v0530, globals(), "DatabaseWorldMixin")
DatabaseWorldMixin.add_city_reputation_v0710 = _sb420_bind(_sb420_src_02.add_city_reputation_v0710, globals(), "DatabaseWorldMixin")


DatabaseWorldMixin.claim_landmark_ep_v1002 = _sb420_bind(_sb420_src_01.claim_landmark_ep_v1002, globals(), "DatabaseWorldMixin")
