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

class DatabaseWorldMixin:
    def crypt_checkpoint(self, account_id):
        row = self.conn.execute(
            "SELECT crypt_checkpoint FROM characters WHERE account_id=?",
            (account_id,),
        ).fetchone()
        return int(row["crypt_checkpoint"] or 0) if row else 0

    def unlock_crypt_checkpoint(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method unlock_crypt_checkpoint")

    def sync_legacy_crypt_checkpoint(self, account_id, room_id):
        floor = _dbw_crypt_floor_number_lazy(room_id)
        if floor is None:
            return self.crypt_checkpoint(account_id)

        # Stara postać stojąca na piętrze N musiała wcześniej przejść
        # wszystkie bossy poniżej N. Nie zaliczamy bossa bieżącego piętra.
        safe_floor = ((max(1, floor) - 1) // 10) * 10
        if safe_floor >= 10:
            return self.unlock_crypt_checkpoint(account_id, safe_floor)
        return self.crypt_checkpoint(account_id)

    def crypt_portal(self, account_id):
        return self.crypt_checkpoint(account_id)

    def unlock_crypt_portal(self, account_id, floor):
        return self.unlock_crypt_checkpoint(account_id, floor)

    def astral_checkpoint(self, account_id):
        row = self.conn.execute(
            "SELECT checkpoint FROM astral_progress WHERE account_id=?",
            (account_id,),
        ).fetchone()
        return int(row["checkpoint"] or 0) if row else 0

    def unlock_astral_checkpoint(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method unlock_astral_checkpoint")

    def astral_portal(self, account_id):
        return self.astral_checkpoint(account_id)

    def unlock_astral_portal(self, account_id, floor):
        return self.unlock_astral_checkpoint(account_id, floor)

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

    def mine_tunnel_exists_v1251(self, account_id, floor, x, y):
        if int(x) == 0 and int(y) == 0:
            return True  # Central mine room was always available.
        return self.conn.execute(
            "SELECT 1 FROM mine_tunnel_cells_v1251 WHERE account_id=? AND floor=? AND x=? AND y=?",
            (int(account_id), int(floor), int(x), int(y)),
        ).fetchone() is not None

    def mine_tunnel_target_v1251(self, account_id, floor, x, y, direction):
        from core.mine_tunnels import HORIZONTAL_MINE_DIRECTIONS, mine_tunnel_room_id
        delta = HORIZONTAL_MINE_DIRECTIONS.get(direction)
        if delta is None or not self.mine_tunnel_exists_v1251(account_id, floor, x, y):
            return None
        nx, ny = x + delta[0], y + delta[1]
        if not self.mine_tunnel_exists_v1251(account_id, floor, nx, ny):
            return None
        return mine_tunnel_room_id(floor, account_id, nx, ny)

    def mine_tunnel_hit_v1251(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method mine_tunnel_hit_v1251")

    def mine_tunnel_directions_v1251(self, account_id, floor, x, y):
        from core.mine_tunnels import HORIZONTAL_MINE_DIRECTIONS
        return tuple(direction for direction in HORIZONTAL_MINE_DIRECTIONS
                     if self.mine_tunnel_target_v1251(account_id, floor, x, y, direction))

    def mine_tunnel_cells_v1260(self, account_id, floor):
        rows = self.conn.execute(
            'SELECT x, y FROM mine_tunnel_cells_v1251 WHERE account_id=? AND floor=?',
            (int(account_id), int(floor))).fetchall()
        return [(0, 0)] + [(int(row['x']),int(row['y'])) for row in rows]

    def mine_discover_v1260(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method mine_discover_v1260")

    def mine_claim_v1260(self, account_id, floor, x, y):
        """One-time vault/relic award, made durable before payout."""
        with self.conn:
            return self.conn.execute(
                'INSERT OR IGNORE INTO mine_claimed_v1260(account_id,floor,x,y) '
                'VALUES(?,?,?,?)',tuple(map(int,(account_id,floor,x,y)))).rowcount > 0

    def mine_claimed_v1260(self, account_id, floor, x, y):
        return self.conn.execute(
            'SELECT 1 FROM mine_claimed_v1260 WHERE account_id=? AND floor=? AND x=? AND y=?',
            tuple(map(int,(account_id,floor,x,y)))).fetchone() is not None

    def mercenary_memory_read_v1260(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method mercenary_memory_read_v1260")

    def mercenary_memory_save_v1260(self, account_id, role, species, values):
        import json
        with self.conn:
            self.conn.execute('INSERT INTO mercenary_memory_v1260('
                'account_id,role,species,attempts_json,success_json) VALUES(?,?,?,?,?) '
                'ON CONFLICT(account_id,role,species) DO UPDATE SET '
                'attempts_json=excluded.attempts_json,success_json=excluded.success_json',
                (int(account_id),str(role),str(species)[:160],
                 json.dumps(values['attempts']),json.dumps(values['success'])))

    def grand_expedition_start_v1260(self, account_id):
        row=self.conn.execute('SELECT cycle,completed FROM grand_expeditions_v1260 WHERE account_id=?',
                              (int(account_id),)).fetchone()
        if row and not row['completed']:
            return False
        cycle = int(row['cycle'])+1 if row else 1
        with self.conn:
            self.conn.execute('INSERT INTO grand_expeditions_v1260(account_id,cycle,stage,completed) '
                'VALUES(?,?,0,0) ON CONFLICT(account_id) DO UPDATE SET '
                'cycle=excluded.cycle,stage=0,completed=0',(int(account_id),cycle))
        return True

    def grand_expedition_state_v1260(self, account_id):
        row=self.conn.execute('SELECT cycle,stage,completed FROM grand_expeditions_v1260 '
                              'WHERE account_id=?',(int(account_id),)).fetchone()
        return dict(row) if row else None

    def grand_expedition_visit_v1260(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method grand_expedition_visit_v1260")

    def grand_expedition_claim_v1260(self, account_id):
        with self.conn:
            row=self.conn.execute('SELECT cycle FROM grand_expeditions_v1260 '
                'WHERE account_id=? AND stage=4 AND completed=0',(int(account_id),)).fetchone()
            if not row:
                return None
            self.conn.execute('UPDATE grand_expeditions_v1260 SET completed=1 '
                              'WHERE account_id=?',(int(account_id),))
        return int(row['cycle'])

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

    def exploration_room_point_awards_v2322(self, account_id):
        rows = self.conn.execute(
            "SELECT room_id, ep_points FROM exploration_room_points_v2322 WHERE account_id=?",
            (account_id,),
        ).fetchall()
        return {str(row['room_id']): int(row['ep_points']) for row in rows}

    def discovered_room_ids(self, account_id):
        rows = self.conn.execute(
            "SELECT room_id FROM exploration_rooms WHERE account_id=?",
            (account_id,),
        ).fetchall()
        return {str(row["room_id"]) for row in rows}

    def claim_exploration_reward(self, account_id, zone):
        cur = self.conn.execute(
            "INSERT OR IGNORE INTO exploration_rewards(account_id,zone) VALUES(?,?)",
            (account_id, zone),
        )
        self.conn.commit()
        return cur.rowcount > 0

    def exploration_reward_claimed(self, account_id, zone):
        row = self.conn.execute(
            "SELECT 1 FROM exploration_rewards WHERE account_id=? AND zone=?",
            (account_id, zone),
        ).fetchone()
        return bool(row)

    def record_bestiary_kill(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method record_bestiary_kill")

    def bestiary_entry(self, account_id, mob_template_id):
        mob_template_id = _dbw_canonical_bestiary_template_id_lazy(mob_template_id)
        return self.conn.execute(
            "SELECT mob_template_id,kills,fastest_kill_ms,first_killed_at,last_killed_at "
            "FROM bestiary_stats WHERE account_id=? AND mob_template_id=?",
            (account_id, mob_template_id),
        ).fetchone()

    def bestiary_rows(self, account_id):
        return self.conn.execute(
            "SELECT mob_template_id,kills,fastest_kill_ms,first_killed_at,last_killed_at "
            "FROM bestiary_stats WHERE account_id=? ORDER BY kills DESC,mob_template_id",
            (account_id,),
        ).fetchall()

    def record_boss_codex_kill(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method record_boss_codex_kill")

    def boss_codex_stats(self, account_id, boss_id):
        boss_id = _dbw_canonical_bestiary_template_id_lazy(boss_id)
        return self.conn.execute(
            "SELECT boss_id,solo_kills,group_kills FROM boss_codex_stats "
            "WHERE account_id=? AND boss_id=?",
            (account_id, boss_id),
        ).fetchone()

    def add_boss_codex_drop(self, account_id, boss_id, item_id):
        boss_id = _dbw_canonical_bestiary_template_id_lazy(boss_id)
        if boss_id not in _dbw_boss_collection_catalog_lazy() or item_id not in ITEMS:
            return False
        if not _dbw_boss_codex_drop_is_unique_lazy(item_id):
            return False
        cur = self.conn.execute(
            "INSERT OR IGNORE INTO boss_codex_drops(account_id,boss_id,item_id) VALUES(?,?,?)",
            (account_id, boss_id, item_id),
        )
        self.conn.commit()
        return cur.rowcount > 0

    def boss_codex_drops(self, account_id, boss_id):
        boss_id = _dbw_canonical_bestiary_template_id_lazy(boss_id)
        rows = self.conn.execute(
            "SELECT item_id,discovered_at FROM boss_codex_drops "
            "WHERE account_id=? AND boss_id=? ORDER BY discovered_at,item_id",
            (account_id, boss_id),
        ).fetchall()
        return rows

    def add_collection_entry(self, account_id, category, entry_id):
        cur = self.conn.execute(
            "INSERT OR IGNORE INTO collection_codex(account_id,category,entry_id) VALUES(?,?,?)",
            (account_id, category, entry_id),
        )
        self.conn.commit()
        return cur.rowcount > 0

    def collection_entry_ids(self, account_id, category):
        rows = self.conn.execute(
            "SELECT entry_id FROM collection_codex WHERE account_id=? AND category=?",
            (account_id, category),
        ).fetchall()
        return {str(row["entry_id"]) for row in rows}

    def collection_entry_discovered_at(self, account_id, category, entry_id):
        row = self.conn.execute(
            "SELECT discovered_at FROM collection_codex WHERE account_id=? AND category=? AND entry_id=?",
            (account_id, category, entry_id),
        ).fetchone()
        return str(row["discovered_at"]) if row and row["discovered_at"] is not None else None

    def touch_collection_entry(self, account_id, category, entry_id):
        self.conn.execute(
            "INSERT INTO collection_codex(account_id,category,entry_id,discovered_at) VALUES(?,?,?,CURRENT_TIMESTAMP) "
            "ON CONFLICT(account_id,category,entry_id) DO UPDATE SET discovered_at=CURRENT_TIMESTAMP",
            (account_id, category, entry_id),
        )
        self.conn.commit()
        return True

    def remove_collection_entry(self, account_id, category, entry_id):
        cur = self.conn.execute(
            "DELETE FROM collection_codex WHERE account_id=? AND category=? AND entry_id=?",
            (account_id, category, entry_id),
        )
        self.conn.commit()
        return cur.rowcount > 0

    def nemesis_row_v029(self, account_id):
        return self.conn.execute(
            "SELECT * FROM nemesis_v029 WHERE account_id=?",
            (int(account_id),),
        ).fetchone()

    def promote_nemesis_v029(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method promote_nemesis_v029")

    def defeat_nemesis_v029(self, account_id):
        row = self.nemesis_row_v029(account_id)
        if not row:
            return None
        self.conn.execute(
            "UPDATE nemesis_v029 SET active=0,defeats=defeats+1,updated_at=CURRENT_TIMESTAMP WHERE account_id=?",
            (int(account_id),),
        )
        self.conn.commit()
        return self.nemesis_row_v029(account_id)

    def ascension_row_v021(self, account_id, track):
        track=str(track or "")
        self.conn.execute(
            "INSERT OR IGNORE INTO ascension_progress_v021(account_id,track,rank,xp) VALUES(?,?,0,0)",
            (account_id,track),
        )
        self.conn.commit()
        return self.conn.execute(
            "SELECT track,rank,xp FROM ascension_progress_v021 WHERE account_id=? AND track=?",
            (account_id,track),
        ).fetchone()

    def add_ascension_xp_v021(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method add_ascension_xp_v021")

    def ascension_rows_v021(self, account_id):
        return self.conn.execute(
            "SELECT track,rank,xp FROM ascension_progress_v021 WHERE account_id=? ORDER BY rank DESC,track",
            (account_id,),
        ).fetchall()

    def world_tier_v021(self, account_id):
        from world.runtime_progression import V021_WORLD_TIER_MAX
        self.conn.execute("INSERT OR IGNORE INTO world_tier_settings_v021(account_id,tier) VALUES(?,1)",(account_id,))
        self.conn.commit()
        row=self.conn.execute("SELECT tier FROM world_tier_settings_v021 WHERE account_id=?",(account_id,)).fetchone()
        return max(1,min(V021_WORLD_TIER_MAX,int(row["tier"] if row else 1)))

    def set_world_tier_v021(self, account_id, tier):
        from world.runtime_progression import V021_WORLD_TIER_MAX
        tier=max(1,min(V021_WORLD_TIER_MAX,int(tier)))
        self.conn.execute(
            "INSERT INTO world_tier_settings_v021(account_id,tier) VALUES(?,?) ON CONFLICT(account_id) DO UPDATE SET tier=excluded.tier",
            (account_id,tier),
        ); self.conn.commit(); return tier

    def endless_gauntlet_best_v021(self, account_id):
        self.conn.execute("INSERT OR IGNORE INTO endless_gauntlet_progress_v021(account_id,best_round) VALUES(?,0)",(account_id,))
        self.conn.commit()
        row=self.conn.execute("SELECT best_round FROM endless_gauntlet_progress_v021 WHERE account_id=?",(account_id,)).fetchone()
        return max(0,int(row["best_round"] if row else 0))

    def mark_endless_gauntlet_round_v021(self, account_id, round_no):
        round_no=max(0,int(round_no))
        self.conn.execute(
            "INSERT INTO endless_gauntlet_progress_v021(account_id,best_round) VALUES(?,?) ON CONFLICT(account_id) DO UPDATE SET best_round=MAX(best_round,excluded.best_round)",
            (account_id,round_no),
        ); self.conn.commit(); return self.endless_gauntlet_best_v021(account_id)

    def mark_instance_floor_visited(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method mark_instance_floor_visited")

    def instance_visited_floors(self, account_id, instance_kind):
        rows = self.conn.execute(
            "SELECT floor FROM instance_map_progress WHERE account_id=? AND instance_kind=? ORDER BY floor",
            (account_id, str(instance_kind or "")),
        ).fetchall()
        return {int(row["floor"]) for row in rows}

    def instance_highest_floor(self, account_id, instance_kind):
        row = self.conn.execute(
            "SELECT MAX(floor) AS floor FROM instance_map_progress WHERE account_id=? AND instance_kind=?",
            (account_id, str(instance_kind or "")),
        ).fetchone()
        return int(row["floor"] or 0) if row else 0

    def mark_instance_secret(self, account_id, instance_kind, floor, secret_name):
        cur = self.conn.execute(
            "INSERT OR IGNORE INTO instance_map_secrets(account_id,instance_kind,floor,secret_name) VALUES(?,?,?,?)",
            (account_id, str(instance_kind or ""), max(1, int(floor)), str(secret_name or "Sekret")),
        )
        self.conn.commit()
        return cur.rowcount > 0

    def instance_secret_rows(self, account_id, instance_kind):
        return self.conn.execute(
            "SELECT floor,secret_name,discovered_at FROM instance_map_secrets "
            "WHERE account_id=? AND instance_kind=? ORDER BY floor",
            (account_id, str(instance_kind or "")),
        ).fetchall()

    def mark_instance_checkpoint(self, account_id, instance_kind, floor):
        cur = self.conn.execute(
            "INSERT OR IGNORE INTO instance_map_checkpoints(account_id,instance_kind,floor) VALUES(?,?,?)",
            (account_id, str(instance_kind or ""), max(1, int(floor))),
        )
        self.conn.commit()
        return cur.rowcount > 0

    def instance_checkpoint_floors(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method instance_checkpoint_floors")

    def highest_boss_floor_cleared(self, account_id, instance_kind):
        floors = self.instance_checkpoint_floors(account_id, instance_kind)
        return max(floors) if floors else 0

    def treasure_chest_opened_at(self, account_id, room_id):
        row = self.conn.execute(
            "SELECT opened_at FROM treasure_chest_cooldowns WHERE account_id=? AND room_id=?",
            (account_id, room_id),
        ).fetchone()
        return int(row["opened_at"]) if row else 0

    def mark_treasure_chest_opened(self, account_id, room_id, opened_at=None):
        stamp = int(time.time() if opened_at is None else opened_at)
        self.conn.execute(
            "INSERT INTO treasure_chest_cooldowns(account_id,room_id,opened_at) VALUES(?,?,?) "
            "ON CONFLICT(account_id,room_id) DO UPDATE SET opened_at=excluded.opened_at",
            (account_id, room_id, stamp),
        )
        self.conn.commit()
        return stamp

    # v0.56.0 - durable, compact player activity journal.
    def record_activity_v0560(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method record_activity_v0560")

    def activity_rows_v0560(self, account_id, limit=30, category=None):
        limit = max(1, min(100, int(limit or 30)))
        if category:
            return self.conn.execute(
                "SELECT id,category,title,detail,created_at FROM activity_journal_v0560 "
                "WHERE account_id=? AND category=? ORDER BY created_at DESC,id DESC LIMIT ?",
                (int(account_id), str(category).casefold(), limit),
            ).fetchall()
        return self.conn.execute(
            "SELECT id,category,title,detail,created_at FROM activity_journal_v0560 "
            "WHERE account_id=? ORDER BY created_at DESC,id DESC LIMIT ?",
            (int(account_id), limit),
        ).fetchall()

    def achievement_metric(self, account_id, metric):
        row = self.conn.execute(
            "SELECT value FROM achievement_progress WHERE account_id=? AND metric=?",
            (account_id, metric),
        ).fetchone()
        return int(row["value"]) if row else 0

    def add_achievement_metric(self, account_id, metric, amount=1):
        self.conn.execute(
            """
            INSERT INTO achievement_progress(account_id,metric,value) VALUES(?,?,?)
            ON CONFLICT(account_id,metric)
            DO UPDATE SET value=value+excluded.value
            """,
            (account_id, metric, int(amount)),
        )
        self.conn.commit()
        return self.achievement_metric(account_id, metric)

    def set_achievement_metric_max(self, account_id, metric, value):
        value = max(0, int(value))
        self.conn.execute(
            """
            INSERT INTO achievement_progress(account_id,metric,value) VALUES(?,?,?)
            ON CONFLICT(account_id,metric) DO UPDATE SET
                value=MAX(achievement_progress.value, excluded.value)
            """,
            (account_id, metric, value),
        )
        self.conn.commit()
        return self.achievement_metric(account_id, metric)

    def unlock_achievement(self, account_id, achievement_id, name, tier):
        cur = self.conn.execute(
            "INSERT OR IGNORE INTO achievements(account_id,achievement_id,name,tier) VALUES(?,?,?,?)",
            (account_id, achievement_id, name, tier),
        )
        self.conn.commit()
        is_new = cur.rowcount > 0
        if is_new:
            self.record_activity_v0560(
                account_id, "osiagniecie", str(name), f"Poziom osiągnięcia: {tier}."
            )
        return is_new

    def achievement_rows(self, account_id):
        return self.conn.execute(
            "SELECT achievement_id,name,tier,unlocked_at FROM achievements "
            "WHERE account_id=? ORDER BY unlocked_at, achievement_id",
            (account_id,),
        ).fetchall()

    def unlock_title(self, account_id, title_id, title_name):
        cur = self.conn.execute(
            "INSERT OR IGNORE INTO unlocked_titles(account_id,title_id,title_name) VALUES(?,?,?)",
            (account_id, title_id, title_name),
        )
        self.conn.commit()
        is_new = cur.rowcount > 0
        if is_new:
            self.record_activity_v0560(
                account_id, "awans", f"Nowy tytuł: {title_name}", "Odblokowano nowy tytuł lub kamień milowy progresji."
            )
        return is_new

    def title_rows(self, account_id):
        return self.conn.execute(
            "SELECT title_id,title_name,unlocked_at FROM unlocked_titles "
            "WHERE account_id=? ORDER BY title_name COLLATE NOCASE",
            (account_id,),
        ).fetchall()

    def bounty_board_state(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method bounty_board_state")

    def save_bounty_board_state(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method save_bounty_board_state")

    def dynamic_world_quest_v015(self, account_id):
        row = self.conn.execute(
            "SELECT * FROM dynamic_world_quests_v015 WHERE account_id=?", (account_id,)
        ).fetchone()
        return row

    def save_dynamic_world_quest_v015(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method save_dynamic_world_quest_v015")

    def clear_dynamic_world_quest_v015(self, account_id):
        self.conn.execute("DELETE FROM dynamic_world_quests_v015 WHERE account_id=?", (account_id,))
        self.conn.commit()

    def faction_reputation_v016(self, account_id, faction_id):
        row = self.conn.execute(
            "SELECT reputation FROM faction_reputation_v016 WHERE account_id=? AND faction_id=?",
            (account_id, str(faction_id)),
        ).fetchone()
        return max(0, int(row["reputation"] or 0)) if row else 0

    def faction_reputations_v016(self, account_id):
        rows = self.conn.execute(
            "SELECT faction_id,reputation FROM faction_reputation_v016 WHERE account_id=?",
            (account_id,),
        ).fetchall()
        return {str(row["faction_id"]): max(0,int(row["reputation"] or 0)) for row in rows}

    def add_faction_reputation_v016(self, account_id, faction_id, amount=1):
        amount = max(0, int(amount or 0))
        if amount <= 0:
            return self.faction_reputation_v016(account_id, faction_id)
        self.conn.execute(
            "INSERT INTO faction_reputation_v016(account_id,faction_id,reputation) VALUES(?,?,?) "
            "ON CONFLICT(account_id,faction_id) DO UPDATE SET "
            "reputation=faction_reputation_v016.reputation+excluded.reputation,updated_at=CURRENT_TIMESTAMP",
            (account_id, str(faction_id), amount),
        )
        self.conn.commit()
        return self.faction_reputation_v016(account_id, faction_id)

    def lifetime_stat(self, account_id, stat_key):
        row = self.conn.execute(
            "SELECT value FROM lifetime_statistics WHERE account_id=? AND stat_key=?",
            (account_id, str(stat_key)),
        ).fetchone()
        return max(0, int(row["value"] or 0)) if row else 0

    def add_lifetime_stat(self, account_id, stat_key, amount=1):
        amount = int(amount or 0)
        if amount <= 0:
            return self.lifetime_stat(account_id, stat_key)
        self.conn.execute(
            "INSERT INTO lifetime_statistics(account_id,stat_key,value) VALUES(?,?,?) "
            "ON CONFLICT(account_id,stat_key) DO UPDATE SET "
            "value=lifetime_statistics.value+excluded.value,updated_at=CURRENT_TIMESTAMP",
            (account_id, str(stat_key), amount),
        )
        self.conn.commit()
        return self.lifetime_stat(account_id, stat_key)

    def set_lifetime_stat_max(self, account_id, stat_key, value):
        value = max(0, int(value or 0))
        self.conn.execute(
            "INSERT INTO lifetime_statistics(account_id,stat_key,value) VALUES(?,?,?) "
            "ON CONFLICT(account_id,stat_key) DO UPDATE SET "
            "value=MAX(lifetime_statistics.value,excluded.value),updated_at=CURRENT_TIMESTAMP",
            (account_id, str(stat_key), value),
        )
        self.conn.commit()
        return self.lifetime_stat(account_id, stat_key)

    def lifetime_stats(self, account_id):
        rows = self.conn.execute(
            "SELECT stat_key,value FROM lifetime_statistics WHERE account_id=?",
            (account_id,),
        ).fetchall()
        return {str(row["stat_key"]): max(0, int(row["value"] or 0)) for row in rows}

    def fish_journal_entry(self, account_id, fish_id):
        return self.conn.execute(
            "SELECT * FROM fish_journal WHERE account_id=? AND fish_id=?",
            (account_id, base_fish_species_id(fish_id)),
        ).fetchone()

    def fish_journal_rows(self, account_id):
        return self.conn.execute(
            "SELECT * FROM fish_journal WHERE account_id=? ORDER BY caught_count DESC, fish_id",
            (account_id,),
        ).fetchall()

    def fish_journal_ids(self, account_id):
        return {str(row["fish_id"]) for row in self.fish_journal_rows(account_id)}

    def record_fish_catch(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method record_fish_catch")

    def record_fishing_global_v022(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method record_fishing_global_v022")

    def fish_global_record_v022(self, fish_id):
        return self.conn.execute("SELECT * FROM fish_global_records_v022 WHERE fish_id=?",(base_fish_species_id(fish_id),)).fetchone()

    def fish_global_top_v022(self, limit=5):
        return self.conn.execute("SELECT * FROM fish_global_records_v022 ORDER BY best_weight_g DESC,best_length_mm DESC LIMIT ?",(max(1,min(20,int(limit))),)).fetchall()

    def fish_rarest_global_v022(self):
        return self.conn.execute("SELECT * FROM fish_rarest_record_v022 WHERE record_key='global'").fetchone()

    def fish_rarest_personal_v022(self, account_id):
        return self.conn.execute("SELECT * FROM fish_rarest_record_v022 WHERE record_key=?",(f"account:{int(account_id)}",)).fetchone()

    def world_project_state_v022(self, project_id):
        project_id=str(project_id); row=self.conn.execute("SELECT * FROM world_projects_v022 WHERE project_id=?",(project_id,)).fetchone()
        if not row:
            self.conn.execute("INSERT INTO world_projects_v022(project_id,progress_json,completed) VALUES(?,'{}',0)",(project_id,)); self.conn.commit(); row=self.conn.execute("SELECT * FROM world_projects_v022 WHERE project_id=?",(project_id,)).fetchone()
        try: progress=json.loads(row["progress_json"] or "{}")
        except Exception: progress={}
        return {"project_id":project_id,"progress":progress if isinstance(progress,dict) else {},"completed":bool(row["completed"]),"completed_at":row["completed_at"]}

    def world_project_contribution_v022(self, project_id, account_id):
        row=self.conn.execute("SELECT * FROM world_project_contributions_v022 WHERE project_id=? AND account_id=?",(project_id,account_id)).fetchone()
        if not row: return {"points":0,"coins":0,"resources":{},"reward_claimed":False}
        try: resources=json.loads(row["resources_json"] or "{}")
        except Exception: resources={}
        return {"points":int(row["points"] or 0),"coins":int(row["coins"] or 0),"resources":resources if isinstance(resources,dict) else {},"reward_claimed":bool(row["reward_claimed"])}

    def add_world_project_contribution_v022(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method add_world_project_contribution_v022")

    def mark_world_project_reward_claimed_v022(self, project_id, account_id):
        cur=self.conn.execute("UPDATE world_project_contributions_v022 SET reward_claimed=1,updated_at=CURRENT_TIMESTAMP WHERE project_id=? AND account_id=? AND reward_claimed=0",(project_id,account_id)); self.conn.commit(); return cur.rowcount>0

    def legendary_contract_state_v022(self, account_id):
        row=self.conn.execute("SELECT * FROM legendary_contracts_v022 WHERE account_id=?",(account_id,)).fetchone()
        if not row: return {"offers":[],"active":{},"completed_count":0}
        try: offers=json.loads(row["offers_json"] or "[]")
        except Exception: offers=[]
        try: active=json.loads(row["active_json"] or "{}")
        except Exception: active={}
        return {"offers":offers if isinstance(offers,list) else [],"active":active if isinstance(active,dict) else {},"completed_count":int(row["completed_count"] or 0)}

    def save_legendary_contract_state_v022(self, account_id, offers=None, active=None, completed_count=None):
        cur=self.legendary_contract_state_v022(account_id); offers=cur["offers"] if offers is None else offers; active=cur["active"] if active is None else active; completed_count=cur["completed_count"] if completed_count is None else completed_count
        self.conn.execute("""INSERT INTO legendary_contracts_v022(account_id,offers_json,active_json,completed_count,updated_at) VALUES(?,?,?,?,CURRENT_TIMESTAMP)
            ON CONFLICT(account_id) DO UPDATE SET offers_json=excluded.offers_json,active_json=excluded.active_json,completed_count=excluded.completed_count,updated_at=CURRENT_TIMESTAMP""",
            (account_id,json.dumps(list(offers or []),ensure_ascii=False,separators=(",",":")),json.dumps(dict(active or {}),ensure_ascii=False,separators=(",",":")),max(0,int(completed_count or 0))))
        self.conn.commit()


    # v0.52.2 - persistent city package deliveries.  Offer lists are generated
    # deterministically from the 15-minute time slot; only the accepted package
    # needs persistence so refresh/reconnect never destroys an active delivery.
    def postal_delivery_state_v0522(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method postal_delivery_state_v0522")

    def save_postal_delivery_state_v0522(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method save_postal_delivery_state_v0522")

    # v0.53.0 - Courier Guild progression and permanent courier statistics.
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

    # v0.71.0 - trwała reputacja osobno dla każdego miasta.
    def city_reputation_v0710(self, account_id, city_name):
        row = self.conn.execute(
            "SELECT reputation FROM city_reputation_v0710 WHERE account_id=? AND city_name=?",
            (int(account_id), str(city_name)),
        ).fetchone()
        return max(1, min(400, int(row["reputation"] or 1))) if row else 1

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

