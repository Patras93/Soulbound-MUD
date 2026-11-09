# -*- coding: utf-8 -*-
"""Wydzielona trwała warstwa danych świata: reputations_lifetime."""
from .dependencies import *
from .dependencies import _dbw_crypt_floor_number_lazy, _dbw_is_astral_boss_floor_lazy, _dbw_is_crypt_boss_floor_lazy, _dbw_astral_min_floor_lazy, _dbw_canonical_bestiary_template_id_lazy, _dbw_boss_codex_drop_is_unique_lazy, _dbw_boss_collection_catalog_lazy

class ReputationsLifetimeV109Mixin:
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

    def city_reputation_v0710(self, account_id, city_name):
        row = self.conn.execute(
            "SELECT reputation FROM city_reputation_v0710 WHERE account_id=? AND city_name=?",
            (int(account_id), str(city_name)),
        ).fetchone()
        return max(1, min(400, int(row["reputation"] or 1))) if row else 1
