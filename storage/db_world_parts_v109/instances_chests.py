# -*- coding: utf-8 -*-
"""Wydzielona trwała warstwa danych świata: instances_chests."""
from .dependencies import *
from .dependencies import _dbw_crypt_floor_number_lazy, _dbw_is_astral_boss_floor_lazy, _dbw_is_crypt_boss_floor_lazy, _dbw_astral_min_floor_lazy, _dbw_canonical_bestiary_template_id_lazy, _dbw_boss_codex_drop_is_unique_lazy, _dbw_boss_collection_catalog_lazy

class InstancesChestsV109Mixin:
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
