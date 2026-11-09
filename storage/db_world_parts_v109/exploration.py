# -*- coding: utf-8 -*-
"""Wydzielona trwała warstwa danych świata: exploration."""
from .dependencies import *
from .dependencies import _dbw_crypt_floor_number_lazy, _dbw_is_astral_boss_floor_lazy, _dbw_is_crypt_boss_floor_lazy, _dbw_astral_min_floor_lazy, _dbw_canonical_bestiary_template_id_lazy, _dbw_boss_codex_drop_is_unique_lazy, _dbw_boss_collection_catalog_lazy

class ExplorationV109Mixin:
    def exploration_room_point_awards_v2322(self, account_id):
        rows = self.conn.execute(
            "SELECT room_id, ep_points FROM exploration_room_points_v2322 WHERE account_id=?",
            (account_id,),
        ).fetchall()
        awards = {str(row['room_id']): int(row['ep_points']) for row in rows}
        zero_rows = self.conn.execute(
            "SELECT room_id FROM exploration_zero_ep_v1002 WHERE account_id=?",
            (account_id,),
        ).fetchall()
        for row in zero_rows:
            awards.setdefault(str(row['room_id']), 0)
        return awards

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
