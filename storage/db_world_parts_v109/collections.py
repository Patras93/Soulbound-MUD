# -*- coding: utf-8 -*-
"""Wydzielona trwała warstwa danych świata: collections."""
from .dependencies import *
from .dependencies import _dbw_crypt_floor_number_lazy, _dbw_is_astral_boss_floor_lazy, _dbw_is_crypt_boss_floor_lazy, _dbw_astral_min_floor_lazy, _dbw_canonical_bestiary_template_id_lazy, _dbw_boss_codex_drop_is_unique_lazy, _dbw_boss_collection_catalog_lazy

class CollectionsV109Mixin:
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
