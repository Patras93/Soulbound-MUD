# -*- coding: utf-8 -*-
"""World, dungeon, exploration, records and world progression persistence."""

import json
import time

from config.balance import MINE_MIN_FLOOR
from core.bootstrap_economy_professions import V019_SAFE_INT
from core.progression_resources import roll_mine_wall_hits_required
from data.items import ITEMS
from systems.dungeons_regions import (
    ASTRAL_MIN_FLOOR, crypt_floor_number, is_astral_boss_floor, is_crypt_boss_floor,
)
from systems.items_resources import base_fish_species_id
from world import dynamic_world_generator as dynamic_world_v029
from world.dynamic_content import (
    BOSS_COLLECTION_CATALOG, boss_codex_drop_is_unique, canonical_bestiary_template_id,
)

class DatabaseWorldMixin:
    def crypt_checkpoint(self, account_id):
        row = self.conn.execute(
            "SELECT crypt_checkpoint FROM characters WHERE account_id=?",
            (account_id,),
        ).fetchone()
        return int(row["crypt_checkpoint"] or 0) if row else 0

    def unlock_crypt_checkpoint(self, account_id, floor):
        floor = int(floor)
        if not is_crypt_boss_floor(floor):
            return self.crypt_checkpoint(account_id)

        current = self.crypt_checkpoint(account_id)
        new_value = max(current, floor)
        if new_value != current:
            self.conn.execute(
                "UPDATE characters SET crypt_checkpoint=? "
                "WHERE account_id=?",
                (new_value, account_id),
            )
            self.conn.commit()
        return new_value

    def sync_legacy_crypt_checkpoint(self, account_id, room_id):
        floor = crypt_floor_number(room_id)
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

    def unlock_astral_checkpoint(self, account_id, floor):
        floor = int(floor)
        if not is_astral_boss_floor(floor):
            return self.astral_checkpoint(account_id)

        current = self.astral_checkpoint(account_id)
        new_value = max(current, floor)
        if new_value != current:
            self.conn.execute(
                """
                INSERT INTO astral_progress(account_id,checkpoint)
                VALUES(?,?)
                ON CONFLICT(account_id)
                DO UPDATE SET checkpoint=excluded.checkpoint
                """,
                (account_id, new_value),
            )
            self.conn.commit()
        return new_value

    def astral_portal(self, account_id):
        return self.astral_checkpoint(account_id)

    def unlock_astral_portal(self, account_id, floor):
        return self.unlock_astral_checkpoint(account_id, floor)

    def boss_floor_cleared(self, account_id, dungeon_kind, floor):
        dungeon_kind = str(dungeon_kind or "").strip().lower()
        floor = max(1, int(floor))
        # Zgodność starych save'ów: checkpoint Krypty/Wieży oznacza, że wszystkie
        # wcześniejsze bossy co 10 zostały już kiedyś pokonane.
        if dungeon_kind == "crypt" and floor <= self.crypt_checkpoint(account_id):
            return True
        if dungeon_kind == "astral" and floor <= self.astral_checkpoint(account_id):
            return True
        row = self.conn.execute(
            "SELECT 1 FROM boss_floor_clears WHERE account_id=? AND dungeon_kind=? AND floor=?",
            (account_id, dungeon_kind, floor),
        ).fetchone()
        return bool(row)

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

    def mine_progress(self, account_id):
        self.ensure_mine_progress(account_id)
        row = self.conn.execute(
            """
            SELECT max_floor_unlocked,wall_hits,wall_required_hits
            FROM mine_progress
            WHERE account_id=?
            """,
            (account_id,),
        ).fetchone()
        highest = max(
            MINE_MIN_FLOOR,
            int(row["max_floor_unlocked"]),
        )
        hits = max(0, int(row["wall_hits"]))
        required_hits = max(0, int(row["wall_required_hits"]))

        # Stare zapisy nie miały losowego progu. Losujemy go raz
        # dla aktualnej ściany i zapisujemy, aby restart niczego nie zmieniał.
        if required_hits <= hits:
            required_hits = roll_mine_wall_hits_required(highest, hits)
            self.conn.execute(
                "UPDATE mine_progress SET wall_required_hits=? WHERE account_id=?",
                (required_hits, account_id),
            )
            self.conn.commit()

        return {
            "max_floor_unlocked": highest,
            "wall_hits": hits,
            "wall_required_hits": required_hits,
        }

    def add_mine_wall_hit(self, account_id, floor):
        floor = int(floor)
        progress = self.mine_progress(account_id)
        highest = progress["max_floor_unlocked"]
        hits = progress["wall_hits"]
        required_hits = progress["wall_required_hits"]

        if floor != highest:
            return {
                "max_floor_unlocked": highest,
                "wall_hits": hits,
                "wall_required_hits": required_hits,
                "unlocked_floor": None,
            }

        hits += 1
        unlocked_floor = None
        if hits >= required_hits:
            highest = highest + 1
            hits = 0
            unlocked_floor = highest
            required_hits = roll_mine_wall_hits_required(highest, 0)

        self.conn.execute(
            """
            UPDATE mine_progress
            SET max_floor_unlocked=?, wall_hits=?, wall_required_hits=?
            WHERE account_id=?
            """,
            (highest, hits, required_hits, account_id),
        )
        self.conn.commit()
        return {
            "max_floor_unlocked": highest,
            "wall_hits": hits,
            "wall_required_hits": required_hits,
            "unlocked_floor": unlocked_floor,
        }

    def reset_mine_for_server_start(self):
        """v0.30.35: reset Kopalni Głębinowej przy każdym starcie procesu/deployu.

        Reset dotyczy wyłącznie wspólnego stanu przejścia Kopalni: odblokowanej
        głębokości oraz postępu bieżącej ściany. Nie dotyka Górnictwa, Kilofa,
        surowców, EQ, questów ani żadnej progresji postaci. Postacie zapisane
        wewnątrz dynamicznych pięter są przenoszone do wejścia, żeby po resecie
        nie pozostawały poniżej ponownie zamkniętej ściany.
        """
        progress_rows = int(self.conn.execute(
            "SELECT COUNT(*) AS n FROM mine_progress"
        ).fetchone()["n"] or 0)
        moved_rows = int(self.conn.execute(
            "SELECT COUNT(*) AS n FROM characters WHERE room_id LIKE 'mine_floor_%'"
        ).fetchone()["n"] or 0)
        self.conn.execute(
            "UPDATE mine_progress SET max_floor_unlocked=?, wall_hits=0, wall_required_hits=0",
            (MINE_MIN_FLOOR,),
        )
        self.conn.execute(
            "UPDATE characters SET room_id='crystal_chamber' WHERE room_id LIKE 'mine_floor_%'"
        )
        self.conn.commit()
        return {
            "progress_rows_reset": progress_rows,
            "characters_moved_to_entrance": moved_rows,
            "max_floor_unlocked": MINE_MIN_FLOOR,
            "wall_hits": 0,
        }

    def mark_room_discovered(self, account_id, room_id):
        cur = self.conn.execute(
            "INSERT OR IGNORE INTO exploration_rooms(account_id,room_id) VALUES(?,?)",
            (account_id, room_id),
        )
        self.conn.commit()
        return cur.rowcount > 0

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

    def record_bestiary_kill(self, account_id, mob_template_id, kill_ms=None):
        mob_template_id = canonical_bestiary_template_id(mob_template_id)
        previous = self.conn.execute(
            "SELECT kills,fastest_kill_ms FROM bestiary_stats "
            "WHERE account_id=? AND mob_template_id=?",
            (account_id, mob_template_id),
        ).fetchone()
        is_new = previous is None
        old_fastest = int(previous["fastest_kill_ms"]) if previous and previous["fastest_kill_ms"] is not None else None
        clean_ms = None
        if kill_ms is not None:
            try:
                clean_ms = max(1, int(kill_ms))
            except (TypeError, ValueError):
                clean_ms = None
        self.conn.execute(
            """
            INSERT INTO bestiary_stats(
                account_id,mob_template_id,kills,fastest_kill_ms,first_killed_at,last_killed_at
            ) VALUES(?,?,1,?,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)
            ON CONFLICT(account_id,mob_template_id) DO UPDATE SET
                kills=bestiary_stats.kills+1,
                fastest_kill_ms=CASE
                    WHEN excluded.fastest_kill_ms IS NULL THEN bestiary_stats.fastest_kill_ms
                    WHEN bestiary_stats.fastest_kill_ms IS NULL THEN excluded.fastest_kill_ms
                    WHEN excluded.fastest_kill_ms < bestiary_stats.fastest_kill_ms THEN excluded.fastest_kill_ms
                    ELSE bestiary_stats.fastest_kill_ms
                END,
                last_killed_at=CURRENT_TIMESTAMP
            """,
            (account_id, mob_template_id, clean_ms),
        )
        self.conn.commit()
        row = self.bestiary_entry(account_id, mob_template_id)
        new_fastest = row["fastest_kill_ms"] if row else None
        is_record = (
            clean_ms is not None
            and new_fastest == clean_ms
            and (old_fastest is None or clean_ms < old_fastest)
        )
        return row, is_new, is_record

    def bestiary_entry(self, account_id, mob_template_id):
        mob_template_id = canonical_bestiary_template_id(mob_template_id)
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

    def record_boss_codex_kill(self, account_id, boss_id, grouped=False):
        boss_id = canonical_bestiary_template_id(boss_id)
        if boss_id not in BOSS_COLLECTION_CATALOG:
            return None
        solo_inc = 0 if grouped else 1
        group_inc = 1 if grouped else 0
        self.conn.execute(
            "INSERT INTO boss_codex_stats(account_id,boss_id,solo_kills,group_kills) VALUES(?,?,?,?) "
            "ON CONFLICT(account_id,boss_id) DO UPDATE SET "
            "solo_kills=boss_codex_stats.solo_kills+excluded.solo_kills, "
            "group_kills=boss_codex_stats.group_kills+excluded.group_kills",
            (account_id, boss_id, solo_inc, group_inc),
        )
        self.conn.commit()
        return self.boss_codex_stats(account_id, boss_id)

    def boss_codex_stats(self, account_id, boss_id):
        boss_id = canonical_bestiary_template_id(boss_id)
        return self.conn.execute(
            "SELECT boss_id,solo_kills,group_kills FROM boss_codex_stats "
            "WHERE account_id=? AND boss_id=?",
            (account_id, boss_id),
        ).fetchone()

    def add_boss_codex_drop(self, account_id, boss_id, item_id):
        boss_id = canonical_bestiary_template_id(boss_id)
        if boss_id not in BOSS_COLLECTION_CATALOG or item_id not in ITEMS:
            return False
        if not boss_codex_drop_is_unique(item_id):
            return False
        cur = self.conn.execute(
            "INSERT OR IGNORE INTO boss_codex_drops(account_id,boss_id,item_id) VALUES(?,?,?)",
            (account_id, boss_id, item_id),
        )
        self.conn.commit()
        return cur.rowcount > 0

    def boss_codex_drops(self, account_id, boss_id):
        boss_id = canonical_bestiary_template_id(boss_id)
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

    def promote_nemesis_v029(self, account_id, base_template_id, base_name, player_name, level, room_id):
        account_id = int(account_id)
        previous = self.nemesis_row_v029(account_id)
        same = bool(previous and int(previous["active"] or 0) and str(previous["base_template_id"]) == str(base_template_id))
        rank = min(10, (int(previous["rank"] or 1) + 1) if same else 1)
        kills = (int(previous["kills_player"] or 0) + 1) if same else 1
        defeats = int(previous["defeats"] or 0) if previous else 0
        stage = max(1, min(400, int(level or 1) + (rank - 1) * 8))
        name = dynamic_world_v029.nemesis_name(str(base_name), account_id, str(player_name), rank)
        self.conn.execute(
            "INSERT INTO nemesis_v029(account_id,base_template_id,nemesis_name,rank,level,room_id,kills_player,defeats,active,updated_at) "
            "VALUES(?,?,?,?,?,?,?,?,1,CURRENT_TIMESTAMP) "
            "ON CONFLICT(account_id) DO UPDATE SET base_template_id=excluded.base_template_id,nemesis_name=excluded.nemesis_name,"
            "rank=excluded.rank,level=excluded.level,room_id=excluded.room_id,kills_player=excluded.kills_player,defeats=excluded.defeats,"
            "active=1,updated_at=CURRENT_TIMESTAMP",
            (account_id, str(base_template_id), name, rank, stage, str(room_id), kills, defeats),
        )
        self.conn.commit()
        return self.nemesis_row_v029(account_id)

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

    def add_ascension_xp_v021(self, account_id, track, amount):
        from world.runtime_progression import V021_ASCENSION_MAX_RANK, v0210_ascension_xp_to_next
        row=self.ascension_row_v021(account_id,track)
        rank=max(0,int(row["rank"] or 0)); xp=max(0,int(row["xp"] or 0)); gain=max(0,int(amount or 0))
        xp=min(V019_SAFE_INT,xp+gain); ups=0
        while rank < V021_ASCENSION_MAX_RANK:
            needed=v0210_ascension_xp_to_next(rank)
            if needed<=0 or xp<needed: break
            xp-=needed; rank+=1; ups+=1
        if rank>=V021_ASCENSION_MAX_RANK:
            rank=V021_ASCENSION_MAX_RANK; xp=0
        self.conn.execute(
            "UPDATE ascension_progress_v021 SET rank=?,xp=? WHERE account_id=? AND track=?",
            (rank,xp,account_id,str(track)),
        ); self.conn.commit()
        return {"track":str(track),"rank":rank,"xp":xp,"rank_ups":ups,"gain":gain,"next_xp":v0210_ascension_xp_to_next(rank)}

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

    def mark_instance_floor_visited(self, account_id, instance_kind, floor):
        instance_kind = str(instance_kind or "")
        floor = max(1, int(floor))
        previous = self.conn.execute(
            "SELECT 1 FROM instance_map_progress WHERE account_id=? AND instance_kind=? AND floor=?",
            (account_id, instance_kind, floor),
        ).fetchone()
        self.conn.execute(
            "INSERT INTO instance_map_progress(account_id,instance_kind,floor) VALUES(?,?,?) "
            "ON CONFLICT(account_id,instance_kind,floor) DO UPDATE SET last_visited_at=CURRENT_TIMESTAMP",
            (account_id, instance_kind, floor),
        )
        self.conn.commit()
        return previous is None

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

    def instance_checkpoint_floors(self, account_id, instance_kind):
        kind = str(instance_kind or "")
        result = {
            int(row["floor"])
            for row in self.conn.execute(
                "SELECT floor FROM instance_map_checkpoints WHERE account_id=? AND instance_kind=?",
                (account_id, kind),
            ).fetchall()
        }
        # Jednorazowo zaliczone bramki bossów są również checkpointami mapy.
        result.update(
            int(row["floor"])
            for row in self.conn.execute(
                "SELECT floor FROM boss_floor_clears WHERE account_id=? AND dungeon_kind=?",
                (account_id, kind),
            ).fetchall()
        )
        # Zgodność starych save'ów, które miały tylko najwyższy portal.
        if kind == "crypt":
            highest = self.crypt_checkpoint(account_id)
            result.update(range(10, highest + 1, 10))
        elif kind == "astral":
            highest = self.astral_checkpoint(account_id)
            start = int(ASTRAL_MIN_FLOOR)
            if highest >= start:
                result.update(range(start, highest + 1, 10))
        return result

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
    def record_activity_v0560(self, account_id, category, title, detail="", created_at=None):
        category = str(category or "system").strip().casefold()[:32] or "system"
        title = " ".join(str(title or "").split())[:240]
        detail = " ".join(str(detail or "").split())[:500]
        if not title:
            return False
        stamp = int(time.time() if created_at is None else created_at)
        self.conn.execute(
            "INSERT INTO activity_journal_v0560(account_id,category,title,detail,created_at) VALUES(?,?,?,?,?)",
            (int(account_id), category, title, detail, stamp),
        )
        # The journal is intentionally bounded; enough for recent history without
        # allowing an endlessly growing save.
        self.conn.execute(
            "DELETE FROM activity_journal_v0560 WHERE account_id=? AND id NOT IN ("
            "SELECT id FROM activity_journal_v0560 WHERE account_id=? ORDER BY created_at DESC,id DESC LIMIT 300)",
            (int(account_id), int(account_id)),
        )
        self.conn.commit()
        return True

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

    def bounty_board_state(self, account_id):
        row = self.conn.execute(
            "SELECT offers_json,active_json,completed_count FROM bounty_boards WHERE account_id=?",
            (account_id,),
        ).fetchone()
        if not row:
            return {"offers": [], "active": {}, "completed_count": 0}
        try:
            offers = json.loads(row["offers_json"] or "[]")
        except Exception:
            offers = []
        try:
            active = json.loads(row["active_json"] or "{}")
        except Exception:
            active = {}
        if not isinstance(offers, list):
            offers = []
        if not isinstance(active, dict):
            active = {}
        return {
            "offers": offers,
            "active": active,
            "completed_count": max(0, int(row["completed_count"] or 0)),
        }

    def save_bounty_board_state(self, account_id, offers=None, active=None, completed_count=None):
        current = self.bounty_board_state(account_id)
        if offers is None:
            offers = current["offers"]
        if active is None:
            active = current["active"]
        if completed_count is None:
            completed_count = current["completed_count"]
        self.conn.execute(
            """
            INSERT INTO bounty_boards(account_id,offers_json,active_json,completed_count,updated_at)
            VALUES(?,?,?,?,CURRENT_TIMESTAMP)
            ON CONFLICT(account_id) DO UPDATE SET
                offers_json=excluded.offers_json,
                active_json=excluded.active_json,
                completed_count=excluded.completed_count,
                updated_at=CURRENT_TIMESTAMP
            """,
            (
                account_id,
                json.dumps(list(offers or []), ensure_ascii=False, separators=(",", ":")),
                json.dumps(dict(active or {}), ensure_ascii=False, separators=(",", ":")),
                max(0, int(completed_count or 0)),
            ),
        )
        self.conn.commit()

    def dynamic_world_quest_v015(self, account_id):
        row = self.conn.execute(
            "SELECT * FROM dynamic_world_quests_v015 WHERE account_id=?", (account_id,)
        ).fetchone()
        return row

    def save_dynamic_world_quest_v015(self, account_id, quest):
        quest = dict(quest or {})
        self.conn.execute(
            """
            INSERT INTO dynamic_world_quests_v015(
                account_id,quest_key,quest_type,target,label,needed,progress,
                reward_soul_xp,reward_gold,accepted_slot,completed,updated_at
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,CURRENT_TIMESTAMP)
            ON CONFLICT(account_id) DO UPDATE SET
                quest_key=excluded.quest_key, quest_type=excluded.quest_type,
                target=excluded.target, label=excluded.label, needed=excluded.needed,
                progress=excluded.progress, reward_soul_xp=excluded.reward_soul_xp,
                reward_gold=excluded.reward_gold, accepted_slot=excluded.accepted_slot,
                completed=excluded.completed, updated_at=CURRENT_TIMESTAMP
            """,
            (account_id, str(quest.get("quest_key", "")), str(quest.get("quest_type", "")),
             str(quest.get("target", "any")), str(quest.get("label", "")),
             max(0,int(quest.get("needed",0))), max(0,int(quest.get("progress",0))),
             max(0,int(quest.get("reward_soul_xp",0))), max(0,int(quest.get("reward_gold",0))),
             int(quest.get("accepted_slot",0)), 1 if quest.get("completed") else 0)
        )
        self.conn.commit()

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

    def record_fish_catch(self, account_id, fish_id, quantity, length_mm, weight_g, room_id):
        fish_id = base_fish_species_id(fish_id)
        quantity = max(1, int(quantity or 1))
        length_mm = max(0, int(length_mm or 0))
        weight_g = max(0, int(weight_g or 0))
        room_id = str(room_id or "")
        old = self.fish_journal_entry(account_id, fish_id)
        old_length = int(old["best_length_mm"] or 0) if old else 0
        old_weight = int(old["best_weight_g"] or 0) if old else 0
        result = {
            "new_species": old is None,
            "new_length_record": length_mm > old_length,
            "new_weight_record": weight_g > old_weight,
        }
        self.conn.execute(
            """
            INSERT INTO fish_journal(
                account_id,fish_id,caught_count,best_length_mm,best_weight_g,
                first_room_id,last_room_id,first_caught_at,last_caught_at
            ) VALUES(?,?,?,?,?,?,?,CURRENT_TIMESTAMP,CURRENT_TIMESTAMP)
            ON CONFLICT(account_id,fish_id) DO UPDATE SET
                caught_count=fish_journal.caught_count+excluded.caught_count,
                best_length_mm=MAX(fish_journal.best_length_mm,excluded.best_length_mm),
                best_weight_g=MAX(fish_journal.best_weight_g,excluded.best_weight_g),
                last_room_id=excluded.last_room_id,
                last_caught_at=CURRENT_TIMESTAMP
            """,
            (account_id, fish_id, quantity, length_mm, weight_g, room_id, room_id),
        )
        self.conn.commit()
        row = self.fish_journal_entry(account_id, fish_id)
        result.update({
            "caught_count": int(row["caught_count"] or 0),
            "best_length_mm": int(row["best_length_mm"] or 0),
            "best_weight_g": int(row["best_weight_g"] or 0),
        })
        return result

    def record_fishing_global_v022(self, fish_id, item_id, holder_name, length_mm, weight_g, account_id=None):
        from world.runtime_progression import v022_fish_rarity_score, v022_fish_rarity_text
        fish_id=base_fish_species_id(fish_id); item_id=str(item_id or fish_id); holder_name=str(holder_name or "Nieznany")
        length_mm=max(0,int(length_mm or 0)); weight_g=max(0,int(weight_g or 0))
        row=self.conn.execute("SELECT * FROM fish_global_records_v022 WHERE fish_id=?",(fish_id,)).fetchone()
        old_l=int(row["best_length_mm"] or 0) if row else 0; old_w=int(row["best_weight_g"] or 0) if row else 0
        new_l=length_mm>old_l; new_w=weight_g>old_w
        best_l=max(old_l,length_mm); best_w=max(old_w,weight_g)
        lholder=holder_name if new_l else (str(row["length_holder"] or "") if row else "")
        wholder=holder_name if new_w else (str(row["weight_holder"] or "") if row else "")
        self.conn.execute("""INSERT INTO fish_global_records_v022(fish_id,best_length_mm,length_holder,best_weight_g,weight_holder,updated_at) VALUES(?,?,?,?,?,CURRENT_TIMESTAMP)
            ON CONFLICT(fish_id) DO UPDATE SET best_length_mm=excluded.best_length_mm,length_holder=excluded.length_holder,best_weight_g=excluded.best_weight_g,weight_holder=excluded.weight_holder,updated_at=CURRENT_TIMESTAMP""",
            (fish_id,best_l,lholder,best_w,wholder))
        score=v022_fish_rarity_score(item_id); rare=self.conn.execute("SELECT * FROM fish_rarest_record_v022 WHERE record_key='global'").fetchone()
        old_score=int(rare["rarity_score"] or 0) if rare else 0; old_rare_weight=int(rare["weight_g"] or 0) if rare else 0
        new_rare=score>old_score or (score==old_score and weight_g>old_rare_weight)
        if new_rare:
            self.conn.execute("""INSERT INTO fish_rarest_record_v022(record_key,rarity_score,fish_id,item_id,holder_name,length_mm,weight_g,rarity_label,updated_at) VALUES('global',?,?,?,?,?,?,?,CURRENT_TIMESTAMP)
                ON CONFLICT(record_key) DO UPDATE SET rarity_score=excluded.rarity_score,fish_id=excluded.fish_id,item_id=excluded.item_id,holder_name=excluded.holder_name,length_mm=excluded.length_mm,weight_g=excluded.weight_g,rarity_label=excluded.rarity_label,updated_at=CURRENT_TIMESTAMP""",
                (score,fish_id,item_id,holder_name,length_mm,weight_g,v022_fish_rarity_text(item_id)))
        new_personal_rare=False
        if account_id is not None:
            pkey=f"account:{int(account_id)}"; personal=self.conn.execute("SELECT * FROM fish_rarest_record_v022 WHERE record_key=?",(pkey,)).fetchone()
            pscore=int(personal["rarity_score"] or 0) if personal else 0; pweight=int(personal["weight_g"] or 0) if personal else 0
            new_personal_rare=score>pscore or (score==pscore and weight_g>pweight)
            if new_personal_rare:
                self.conn.execute("""INSERT INTO fish_rarest_record_v022(record_key,rarity_score,fish_id,item_id,holder_name,length_mm,weight_g,rarity_label,updated_at) VALUES(?,?,?,?,?,?,?,?,CURRENT_TIMESTAMP)
                    ON CONFLICT(record_key) DO UPDATE SET rarity_score=excluded.rarity_score,fish_id=excluded.fish_id,item_id=excluded.item_id,holder_name=excluded.holder_name,length_mm=excluded.length_mm,weight_g=excluded.weight_g,rarity_label=excluded.rarity_label,updated_at=CURRENT_TIMESTAMP""",
                    (pkey,score,fish_id,item_id,holder_name,length_mm,weight_g,v022_fish_rarity_text(item_id)))
        self.conn.commit(); return {"new_global_length":new_l,"new_global_weight":new_w,"new_global_rarest":new_rare,"new_personal_rarest":new_personal_rare}

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

    def add_world_project_contribution_v022(self, project_id, account_id, category, amount, points):
        from world.runtime_progression import V022_WORLD_PROJECTS
        spec=V022_WORLD_PROJECTS[project_id]; state=self.world_project_state_v022(project_id); progress=dict(state["progress"]); category=str(category); amount=max(0,int(amount)); points=max(0,int(points))
        need=int(spec["requirements"].get(category,0)); old=int(progress.get(category,0) or 0); accepted=min(amount,max(0,need-old))
        if accepted<=0: return {"accepted":0,"completed":state["completed"],"newly_completed":False,"progress":progress}
        progress[category]=old+accepted
        completed=all(int(progress.get(k,0) or 0)>=int(v) for k,v in spec["requirements"].items())
        newly=completed and not state["completed"]
        self.conn.execute("UPDATE world_projects_v022 SET progress_json=?,completed=?,completed_at=CASE WHEN ?=1 AND completed=0 THEN CURRENT_TIMESTAMP ELSE completed_at END WHERE project_id=?",(json.dumps(progress,ensure_ascii=False,separators=(",",":")),1 if completed else 0,1 if completed else 0,project_id))
        cur=self.world_project_contribution_v022(project_id,account_id); resources=dict(cur["resources"]); coins=int(cur["coins"]);
        if category=="coins": coins+=accepted
        else: resources[category]=int(resources.get(category,0) or 0)+accepted
        self.conn.execute("""INSERT INTO world_project_contributions_v022(project_id,account_id,points,resources_json,coins,reward_claimed,updated_at) VALUES(?,?,?,?,?,0,CURRENT_TIMESTAMP)
            ON CONFLICT(project_id,account_id) DO UPDATE SET points=world_project_contributions_v022.points+excluded.points,resources_json=excluded.resources_json,coins=excluded.coins,updated_at=CURRENT_TIMESTAMP""",
            (project_id,account_id,points,json.dumps(resources,ensure_ascii=False,separators=(",",":")),coins))
        self.conn.commit(); return {"accepted":accepted,"completed":completed,"newly_completed":newly,"progress":progress}

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
    def postal_delivery_state_v0522(self, account_id):
        row = self.conn.execute(
            "SELECT active_json,completed_count,abandoned_count FROM postal_delivery_state_v0522 WHERE account_id=?",
            (int(account_id),),
        ).fetchone()
        if not row:
            return {"active": {}, "completed_count": 0, "abandoned_count": 0}
        try:
            active = json.loads(row["active_json"] or "{}")
        except Exception:
            active = {}
        return {
            "active": active if isinstance(active, dict) else {},
            "completed_count": max(0, int(row["completed_count"] or 0)),
            "abandoned_count": max(0, int(row["abandoned_count"] or 0)),
        }

    def save_postal_delivery_state_v0522(
        self, account_id, *, active=None, completed_count=None, abandoned_count=None
    ):
        current = self.postal_delivery_state_v0522(account_id)
        active = current["active"] if active is None else dict(active or {})
        completed_count = current["completed_count"] if completed_count is None else max(0, int(completed_count))
        abandoned_count = current["abandoned_count"] if abandoned_count is None else max(0, int(abandoned_count))
        self.conn.execute(
            """
            INSERT INTO postal_delivery_state_v0522(account_id,active_json,completed_count,abandoned_count,updated_at)
            VALUES(?,?,?,?,CURRENT_TIMESTAMP)
            ON CONFLICT(account_id) DO UPDATE SET
                active_json=excluded.active_json,
                completed_count=excluded.completed_count,
                abandoned_count=excluded.abandoned_count,
                updated_at=CURRENT_TIMESTAMP
            """,
            (
                int(account_id),
                json.dumps(active, ensure_ascii=False, separators=(",", ":")),
                completed_count,
                abandoned_count,
            ),
        )
        self.conn.commit()
        return {
            "active": active,
            "completed_count": completed_count,
            "abandoned_count": abandoned_count,
        }

    # v0.53.0 - Courier Guild progression and permanent courier statistics.
    def courier_guild_state_v0530(self, account_id):
        row = self.conn.execute(
            "SELECT reputation,total_earnings,longest_route,visited_cities_json "
            "FROM courier_guild_state_v0530 WHERE account_id=?",
            (int(account_id),),
        ).fetchone()
        if not row:
            return {
                "reputation": 1,
                "total_earnings": 0,
                "longest_route": 0,
                "visited_cities": [],
            }
        try:
            visited = json.loads(row["visited_cities_json"] or "[]")
        except Exception:
            visited = []
        if not isinstance(visited, list):
            visited = []
        return {
            "reputation": max(1, min(400, int(row["reputation"] or 1))),
            "total_earnings": max(0, int(row["total_earnings"] or 0)),
            "longest_route": max(0, int(row["longest_route"] or 0)),
            "visited_cities": sorted({str(x) for x in visited if str(x).strip()}),
        }

    def save_courier_guild_state_v0530(
        self, account_id, *, reputation=None, total_earnings=None,
        longest_route=None, visited_cities=None
    ):
        current = self.courier_guild_state_v0530(account_id)
        reputation = current["reputation"] if reputation is None else max(1, min(400, int(reputation)))
        total_earnings = current["total_earnings"] if total_earnings is None else max(0, int(total_earnings))
        longest_route = current["longest_route"] if longest_route is None else max(0, int(longest_route))
        visited_cities = current["visited_cities"] if visited_cities is None else sorted({str(x) for x in visited_cities if str(x).strip()})
        self.conn.execute(
            """
            INSERT INTO courier_guild_state_v0530(
                account_id,reputation,total_earnings,longest_route,visited_cities_json,updated_at
            ) VALUES(?,?,?,?,?,CURRENT_TIMESTAMP)
            ON CONFLICT(account_id) DO UPDATE SET
                reputation=excluded.reputation,
                total_earnings=excluded.total_earnings,
                longest_route=excluded.longest_route,
                visited_cities_json=excluded.visited_cities_json,
                updated_at=CURRENT_TIMESTAMP
            """,
            (
                int(account_id), reputation, total_earnings, longest_route,
                json.dumps(visited_cities, ensure_ascii=False, separators=(",", ":")),
            ),
        )
        self.conn.commit()
        return {
            "reputation": reputation,
            "total_earnings": total_earnings,
            "longest_route": longest_route,
            "visited_cities": visited_cities,
        }

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

    def add_city_reputation_v0710(self, account_id, city_name, amount=1):
        city_name = str(city_name or "").strip()
        amount = int(amount or 0)
        if not city_name or amount == 0:
            return self.city_reputation_v0710(account_id, city_name) if city_name else 1
        old = self.city_reputation_v0710(account_id, city_name)
        new = max(1, min(400, old + amount))
        self.conn.execute(
            """
            INSERT INTO city_reputation_v0710(account_id,city_name,reputation,updated_at)
            VALUES(?,?,?,CURRENT_TIMESTAMP)
            ON CONFLICT(account_id,city_name) DO UPDATE SET
                reputation=excluded.reputation,updated_at=CURRENT_TIMESTAMP
            """,
            (int(account_id), city_name, new),
        )
        self.conn.commit()
        return new
