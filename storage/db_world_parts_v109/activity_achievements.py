# -*- coding: utf-8 -*-
"""Wydzielona trwała warstwa danych świata: activity_achievements."""
from .dependencies import *
from .dependencies import _dbw_crypt_floor_number_lazy, _dbw_is_astral_boss_floor_lazy, _dbw_is_crypt_boss_floor_lazy, _dbw_astral_min_floor_lazy, _dbw_canonical_bestiary_template_id_lazy, _dbw_boss_codex_drop_is_unique_lazy, _dbw_boss_collection_catalog_lazy

class ActivityAchievementsV109Mixin:
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
