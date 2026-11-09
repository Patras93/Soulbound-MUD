# -*- coding: utf-8 -*-
"""Wydzielona trwała warstwa danych świata: fishing."""
from .dependencies import *
from .dependencies import _dbw_crypt_floor_number_lazy, _dbw_is_astral_boss_floor_lazy, _dbw_is_crypt_boss_floor_lazy, _dbw_astral_min_floor_lazy, _dbw_canonical_bestiary_template_id_lazy, _dbw_boss_codex_drop_is_unique_lazy, _dbw_boss_collection_catalog_lazy

class FishingV109Mixin:
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

    def fish_global_record_v022(self, fish_id):
        return self.conn.execute("SELECT * FROM fish_global_records_v022 WHERE fish_id=?",(base_fish_species_id(fish_id),)).fetchone()

    def fish_global_top_v022(self, limit=5):
        return self.conn.execute("SELECT * FROM fish_global_records_v022 ORDER BY best_weight_g DESC,best_length_mm DESC LIMIT ?",(max(1,min(20,int(limit))),)).fetchall()

    def fish_rarest_global_v022(self):
        return self.conn.execute("SELECT * FROM fish_rarest_record_v022 WHERE record_key='global'").fetchone()

    def fish_rarest_personal_v022(self, account_id):
        return self.conn.execute("SELECT * FROM fish_rarest_record_v022 WHERE record_key=?",(f"account:{int(account_id)}",)).fetchone()
