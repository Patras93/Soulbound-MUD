# -*- coding: utf-8 -*-
"""Class, skill queue and skill progression persistence."""

from config.balance import CLASS_MASTERY_MAX_LEVEL, MULTICLASS_MAX_ACTIVE, SKILL_MAX_LEVEL
from core.progression_resources import class_mastery_xp_to_next, skill_xp_to_next

class DatabaseProgressionMixin:
    def ensure_class_progress(self, account_id, class_name):
        self.conn.execute(
            "INSERT OR IGNORE INTO class_progress(account_id,class_name,level,xp,active_slot) "
            "VALUES(?,?,1,0,NULL)",
            (account_id, class_name),
        )
        self.conn.commit()

    def ensure_primary_class(self, account_id, class_name):
        self.ensure_class_progress(account_id, class_name)
        self.conn.execute(
            "UPDATE class_progress SET active_slot=NULL "
            "WHERE account_id=? AND active_slot=1 AND class_name<>?",
            (account_id, class_name),
        )
        self.conn.execute(
            "UPDATE class_progress SET active_slot=1 "
            "WHERE account_id=? AND class_name=?",
            (account_id, class_name),
        )
        self.conn.commit()

    def class_progress_row(self, account_id, class_name):
        self.ensure_class_progress(account_id, class_name)
        return self.conn.execute(
            "SELECT class_name,level,xp,active_slot FROM class_progress "
            "WHERE account_id=? AND class_name=?",
            (account_id, class_name),
        ).fetchone()

    def active_class_rows(self, account_id, primary_class):
        self.ensure_primary_class(account_id, primary_class)
        return self.conn.execute(
            "SELECT class_name,level,xp,active_slot FROM class_progress "
            "WHERE account_id=? AND active_slot IS NOT NULL "
            "ORDER BY active_slot",
            (account_id,),
        ).fetchall()

    def active_class_names(self, account_id, primary_class):
        return [
            row["class_name"]
            for row in self.active_class_rows(account_id, primary_class)
        ]

    def activate_secondary_class(self, account_id, primary_class, class_name):
        self.ensure_primary_class(account_id, primary_class)
        rows = self.active_class_rows(account_id, primary_class)
        active_names = [row["class_name"] for row in rows]

        if class_name in active_names:
            return False, "Ta klasa jest już aktywna."
        if len(active_names) >= MULTICLASS_MAX_ACTIVE:
            return False, "Masz już maksymalnie 3 aktywne klasy."

        used_slots = {
            int(row["active_slot"])
            for row in rows
            if row["active_slot"] is not None
        }
        slot = next(
            number for number in range(2, MULTICLASS_MAX_ACTIVE + 1)
            if number not in used_slots
        )

        self.ensure_class_progress(account_id, class_name)
        self.conn.execute(
            "UPDATE class_progress SET active_slot=? "
            "WHERE account_id=? AND class_name=?",
            (slot, account_id, class_name),
        )
        self.conn.commit()
        return True, slot

    def deactivate_secondary_class(self, account_id, primary_class, class_name):
        self.ensure_primary_class(account_id, primary_class)
        if class_name == primary_class:
            return False, "Nie można wyłączyć klasy głównej."

        row = self.conn.execute(
            "SELECT active_slot FROM class_progress "
            "WHERE account_id=? AND class_name=?",
            (account_id, class_name),
        ).fetchone()
        if not row or row["active_slot"] is None:
            return False, "Ta klasa nie jest aktywna."

        self.conn.execute(
            "UPDATE class_progress SET active_slot=NULL "
            "WHERE account_id=? AND class_name=?",
            (account_id, class_name),
        )
        self.conn.commit()
        return True, None

    def add_class_mastery_xp(self, account_id, class_name, amount):
        self.ensure_class_progress(account_id, class_name)
        row = self.class_progress_row(account_id, class_name)
        level = int(row["level"])
        xp = int(row["xp"])
        gain = max(0, int(amount))
        xp += gain
        level_ups = 0

        while level < CLASS_MASTERY_MAX_LEVEL:
            needed = class_mastery_xp_to_next(level)
            if needed <= 0 or xp < needed:
                break
            xp -= needed
            level += 1
            level_ups += 1

        overflow_xp = 0
        if level >= CLASS_MASTERY_MAX_LEVEL:
            level = CLASS_MASTERY_MAX_LEVEL
            overflow_xp = max(0, int(xp))
            xp = 0

        self.conn.execute(
            "UPDATE class_progress SET level=?,xp=? "
            "WHERE account_id=? AND class_name=?",
            (level, xp, account_id, class_name),
        )
        self.conn.commit()
        return {
            "class_name": class_name,
            "level": level,
            "xp": xp,
            "level_ups": level_ups,
            "next_xp": class_mastery_xp_to_next(level),
            "gain": gain,
            "overflow_xp": overflow_xp,
        }

    def skill_queue_rows(self, account_id, queue_type=None):
        if queue_type is None:
            return self.conn.execute(
                "SELECT queue_type,position,skill_id FROM skill_queue "
                "WHERE account_id=? ORDER BY CASE queue_type WHEN 'physical' THEN 0 ELSE 1 END, position",
                (account_id,),
            ).fetchall()
        return self.conn.execute(
            "SELECT queue_type,position,skill_id FROM skill_queue "
            "WHERE account_id=? AND queue_type=? ORDER BY position",
            (account_id, queue_type),
        ).fetchall()

    def skill_queue_enabled(self, account_id):
        self.conn.execute(
            "INSERT OR IGNORE INTO skill_queue_settings(account_id,enabled) VALUES(?,0)",
            (account_id,),
        )
        self.conn.commit()
        row = self.conn.execute(
            "SELECT enabled FROM skill_queue_settings WHERE account_id=?",
            (account_id,),
        ).fetchone()
        return bool(row and int(row["enabled"]))

    def set_skill_queue_enabled(self, account_id, enabled):
        self.conn.execute(
            "INSERT INTO skill_queue_settings(account_id,enabled) VALUES(?,?) "
            "ON CONFLICT(account_id) DO UPDATE SET enabled=excluded.enabled",
            (account_id, 1 if enabled else 0),
        )
        self.conn.commit()

    def combat_log_mode(self, account_id):
        self.conn.execute(
            "INSERT OR IGNORE INTO combat_log_settings(account_id,mode) VALUES(?, 'normal')",
            (account_id,),
        )
        self.conn.commit()
        row = self.conn.execute(
            "SELECT mode FROM combat_log_settings WHERE account_id=?",
            (account_id,),
        ).fetchone()
        mode = str(row["mode"] if row else "normal").lower()
        return mode if mode in ("concise", "normal", "full") else "normal"

    def set_combat_log_mode(self, account_id, mode):
        mode = str(mode or "normal").lower()
        if mode not in ("concise", "normal", "full"):
            mode = "normal"
        self.conn.execute(
            "INSERT INTO combat_log_settings(account_id,mode) VALUES(?,?) "
            "ON CONFLICT(account_id) DO UPDATE SET mode=excluded.mode",
            (account_id, mode),
        )
        self.conn.commit()
        return mode

    def wimpy_percent(self, account_id):
        self.conn.execute(
            "INSERT OR IGNORE INTO wimpy_settings(account_id,percent) VALUES(?,0)",
            (account_id,),
        )
        self.conn.commit()
        row = self.conn.execute(
            "SELECT percent FROM wimpy_settings WHERE account_id=?",
            (account_id,),
        ).fetchone()
        value = int(row["percent"] if row else 0)
        return max(0, min(99, value))

    def set_wimpy_percent(self, account_id, percent):
        percent = max(0, min(99, int(percent or 0)))
        self.conn.execute(
            "INSERT INTO wimpy_settings(account_id,percent) VALUES(?,?) "
            "ON CONFLICT(account_id) DO UPDATE SET percent=excluded.percent",
            (account_id, percent),
        )
        self.conn.commit()
        return percent

    def replace_skill_queue(self, account_id, queue_type, skill_ids):
        queue_type = str(queue_type)
        skill_ids = list(skill_ids)
        self.conn.execute(
            "DELETE FROM skill_queue WHERE account_id=? AND queue_type=?",
            (account_id, queue_type),
        )
        for index, skill_id in enumerate(skill_ids, 1):
            self.conn.execute(
                "INSERT INTO skill_queue(account_id,queue_type,position,skill_id) VALUES(?,?,?,?)",
                (account_id, queue_type, index, skill_id),
            )
        self.conn.commit()

    def add_skill_queue_entry(self, account_id, queue_type, skill_id):
        exists = self.conn.execute(
            "SELECT queue_type,position FROM skill_queue WHERE account_id=? AND skill_id=?",
            (account_id, skill_id),
        ).fetchone()
        if exists:
            return False, f"Umiejętność jest już w kolejce {exists['queue_type']} na pozycji {exists['position']}."
        row = self.conn.execute(
            "SELECT COALESCE(MAX(position),0) AS max_position FROM skill_queue "
            "WHERE account_id=? AND queue_type=?",
            (account_id, queue_type),
        ).fetchone()
        position = int(row["max_position"]) + 1
        self.conn.execute(
            "INSERT INTO skill_queue(account_id,queue_type,position,skill_id) VALUES(?,?,?,?)",
            (account_id, queue_type, position, skill_id),
        )
        self.conn.commit()
        return True, position

    def remove_skill_queue_entry(self, account_id, queue_type, position):
        rows = self.skill_queue_rows(account_id, queue_type)
        skill_ids = [row["skill_id"] for row in rows]
        index = int(position) - 1
        if index < 0 or index >= len(skill_ids):
            return None
        removed = skill_ids.pop(index)
        self.replace_skill_queue(account_id, queue_type, skill_ids)
        return removed

    def remove_skill_queue_skill(self, account_id, skill_id):
        row = self.conn.execute(
            "SELECT queue_type,position FROM skill_queue WHERE account_id=? AND skill_id=?",
            (account_id, skill_id),
        ).fetchone()
        if not row:
            return None
        return self.remove_skill_queue_entry(
            account_id, row["queue_type"], int(row["position"])
        )

    def clear_skill_queue(self, account_id, queue_type=None):
        if queue_type is None:
            self.conn.execute(
                "DELETE FROM skill_queue WHERE account_id=?",
                (account_id,),
            )
        else:
            self.conn.execute(
                "DELETE FROM skill_queue WHERE account_id=? AND queue_type=?",
                (account_id, queue_type),
            )
        self.conn.commit()

    def move_skill_queue_entry(self, account_id, queue_type, position, delta):
        rows = self.skill_queue_rows(account_id, queue_type)
        skill_ids = [row["skill_id"] for row in rows]
        index = int(position) - 1
        target = index + int(delta)
        if index < 0 or index >= len(skill_ids) or target < 0 or target >= len(skill_ids):
            return False
        skill_ids[index], skill_ids[target] = skill_ids[target], skill_ids[index]
        self.replace_skill_queue(account_id, queue_type, skill_ids)
        return True

    def learned_skill_ids(self, account_id):
        rows = self.conn.execute(
            "SELECT skill_id FROM learned_skills WHERE account_id=? ORDER BY learned_at, skill_id",
            (account_id,),
        ).fetchall()
        return {row["skill_id"] for row in rows}

    def knows_skill(self, account_id, skill_id):
        return self.conn.execute(
            "SELECT 1 FROM learned_skills WHERE account_id=? AND skill_id=?",
            (account_id, skill_id),
        ).fetchone() is not None

    def learn_skill(self, account_id, skill_id):
        before = self.conn.total_changes
        self.conn.execute(
            "INSERT OR IGNORE INTO learned_skills(account_id,skill_id) VALUES(?,?)",
            (account_id, skill_id),
        )
        self.conn.commit()
        learned_now = self.conn.total_changes > before
        self.ensure_skill_progress(account_id, skill_id)
        return learned_now

    def ensure_skill_progress(self, account_id, skill_id):
        self.conn.execute(
            "INSERT OR IGNORE INTO skill_progress(account_id,skill_id,level,xp,uses) VALUES(?,?,1,0,0)",
            (account_id, skill_id),
        )
        self.conn.commit()

    def skill_progress(self, account_id, skill_id):
        self.ensure_skill_progress(account_id, skill_id)
        return self.conn.execute(
            "SELECT level,xp,uses FROM skill_progress WHERE account_id=? AND skill_id=?",
            (account_id, skill_id),
        ).fetchone()

    def add_skill_xp(self, account_id, skill_id, amount):
        self.ensure_skill_progress(account_id, skill_id)
        row = self.skill_progress(account_id, skill_id)
        level = int(row["level"])
        xp = int(row["xp"]) + max(0, int(amount))
        uses = int(row["uses"]) + 1
        level_ups = 0

        while level < SKILL_MAX_LEVEL:
            needed = skill_xp_to_next(level)
            if needed <= 0 or xp < needed:
                break
            xp -= needed
            level += 1
            level_ups += 1

        if level >= SKILL_MAX_LEVEL:
            level = SKILL_MAX_LEVEL
            xp = 0

        self.conn.execute(
            "UPDATE skill_progress SET level=?,xp=?,uses=? WHERE account_id=? AND skill_id=?",
            (level, xp, uses, account_id, skill_id),
        )
        self.conn.commit()
        return {
            "level": level,
            "xp": xp,
            "uses": uses,
            "level_ups": level_ups,
            "next_xp": skill_xp_to_next(level),
        }
