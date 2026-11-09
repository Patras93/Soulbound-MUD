# -*- coding: utf-8 -*-
"""Wydzielona trwała warstwa danych świata: bounties_quests."""
from .dependencies import *
from .dependencies import _dbw_crypt_floor_number_lazy, _dbw_is_astral_boss_floor_lazy, _dbw_is_crypt_boss_floor_lazy, _dbw_astral_min_floor_lazy, _dbw_canonical_bestiary_template_id_lazy, _dbw_boss_codex_drop_is_unique_lazy, _dbw_boss_collection_catalog_lazy

class BountiesQuestsV109Mixin:
    def dynamic_world_quest_v015(self, account_id):
        row = self.conn.execute(
            "SELECT * FROM dynamic_world_quests_v015 WHERE account_id=?", (account_id,)
        ).fetchone()
        return row

    def clear_dynamic_world_quest_v015(self, account_id):
        self.conn.execute("DELETE FROM dynamic_world_quests_v015 WHERE account_id=?", (account_id,))
        self.conn.commit()
