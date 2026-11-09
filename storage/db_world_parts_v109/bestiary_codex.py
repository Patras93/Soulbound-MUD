# -*- coding: utf-8 -*-
"""Wydzielona trwała warstwa danych świata: bestiary_codex."""
from .dependencies import *
from .dependencies import _dbw_crypt_floor_number_lazy, _dbw_is_astral_boss_floor_lazy, _dbw_is_crypt_boss_floor_lazy, _dbw_astral_min_floor_lazy, _dbw_canonical_bestiary_template_id_lazy, _dbw_boss_codex_drop_is_unique_lazy, _dbw_boss_collection_catalog_lazy

class BestiaryCodexV109Mixin:
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
