# -*- coding: utf-8 -*-
"""Wydzielona trwała warstwa danych świata: mines."""
from .dependencies import *
from .dependencies import _dbw_crypt_floor_number_lazy, _dbw_is_astral_boss_floor_lazy, _dbw_is_crypt_boss_floor_lazy, _dbw_astral_min_floor_lazy, _dbw_canonical_bestiary_template_id_lazy, _dbw_boss_codex_drop_is_unique_lazy, _dbw_boss_collection_catalog_lazy

class MinesV109Mixin:
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

    def mine_tunnel_directions_v1251(self, account_id, floor, x, y):
        from core.mine_tunnels import HORIZONTAL_MINE_DIRECTIONS
        return tuple(direction for direction in HORIZONTAL_MINE_DIRECTIONS
                     if self.mine_tunnel_target_v1251(account_id, floor, x, y, direction))

    def mine_tunnel_cells_v1260(self, account_id, floor):
        rows = self.conn.execute(
            'SELECT x, y FROM mine_tunnel_cells_v1251 WHERE account_id=? AND floor=?',
            (int(account_id), int(floor))).fetchall()
        return [(0, 0)] + [(int(row['x']),int(row['y'])) for row in rows]

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
