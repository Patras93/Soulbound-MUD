# -*- coding: utf-8 -*-
"""Wydzielona trwała warstwa danych świata: nemesis_ascension."""
from .dependencies import *
from .dependencies import _dbw_crypt_floor_number_lazy, _dbw_is_astral_boss_floor_lazy, _dbw_is_crypt_boss_floor_lazy, _dbw_astral_min_floor_lazy, _dbw_canonical_bestiary_template_id_lazy, _dbw_boss_codex_drop_is_unique_lazy, _dbw_boss_collection_catalog_lazy

class NemesisAscensionV109Mixin:
    def nemesis_row_v029(self, account_id):
        return self.conn.execute(
            "SELECT * FROM nemesis_v029 WHERE account_id=?",
            (int(account_id),),
        ).fetchone()

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
