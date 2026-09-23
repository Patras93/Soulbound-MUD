# -*- coding: utf-8 -*-
"""Quest persistence and quest progress updates."""

import time

from data.quests import QUESTS
from network.protocol_gameplay_utils import canonical_profession_resource_id

class DatabaseQuestMixin:
    def quest(self, account_id, quest_id):
        return self.conn.execute(
            "SELECT * FROM quests WHERE account_id=? AND quest_id=?",
            (account_id, quest_id),
        ).fetchone()

    def start_quest(self, account_id, quest_id):
        self.conn.execute(
            "INSERT OR IGNORE INTO quests("
            "account_id,quest_id,status,progress,completed_at,completion_count"
            ") VALUES(?,?, 'active',0,0,0)",
            (account_id, quest_id),
        )
        self.conn.execute(
            "DELETE FROM quest_resource_progress_v0929 WHERE account_id=? AND quest_id=?",
            (account_id, quest_id),
        )
        self.conn.commit()

    def restart_quest(self, account_id, quest_id):
        self.conn.execute(
            "UPDATE quests SET status='active',progress=0 "
            "WHERE account_id=? AND quest_id=?",
            (account_id, quest_id),
        )
        self.conn.execute(
            "DELETE FROM quest_resource_progress_v0929 WHERE account_id=? AND quest_id=?",
            (account_id, quest_id),
        )
        self.conn.commit()

    def set_quest_progress(self, account_id, quest_id, progress):
        self.conn.execute(
            "UPDATE quests SET progress=? WHERE account_id=? AND quest_id=?",
            (max(0, int(progress)), account_id, quest_id),
        )
        self.conn.commit()

    def abandon_quest(self, account_id, quest_id):
        row = self.quest(account_id, quest_id)
        if not row or row["status"] != "active":
            return False
        # Nie kasujemy completion_count ani completed_at: historia wcześniejszych
        # ukończeń ma pozostać. Porzucenie kasuje tylko bieżące podejście/postęp.
        self.conn.execute(
            "UPDATE quests SET status='abandoned',progress=0 "
            "WHERE account_id=? AND quest_id=?",
            (account_id, quest_id),
        )
        self.conn.execute(
            "DELETE FROM quest_resource_progress_v0929 WHERE account_id=? AND quest_id=?",
            (account_id, quest_id),
        )
        self.conn.commit()
        return True

    def repeat_quest_seconds_remaining(self, account_id, quest_id, cooldown):
        row = self.quest(account_id, quest_id)
        if not row or row["status"] != "completed":
            return 0
        completed_at = int(row["completed_at"] or 0)
        if completed_at <= 0:
            return 0
        elapsed = max(0, int(time.time()) - completed_at)
        return max(0, int(cooldown) - elapsed)

    def quest_rows(self, account_id):
        return self.conn.execute(
            "SELECT * FROM quests WHERE account_id=? ORDER BY status,quest_id",
            (account_id,),
        ).fetchall()

    def increment_quest(self, account_id, target):
        rows = self.conn.execute(
            "SELECT * FROM quests WHERE account_id=? AND status='active'",
            (account_id,),
        ).fetchall()
        changed = []
        for row in rows:
            q = QUESTS.get(row["quest_id"])
            if not q or q["kind"] != "kill" or q["target"] != target:
                continue
            new_progress = min(q["needed"], row["progress"] + 1)
            # v0.30.7: gotowy quest nie ogłasza ponownie tego samego
            # stanu po każdym kolejnym zabiciu tego samego celu.
            if int(new_progress) == int(row["progress"]):
                continue
            self.conn.execute(
                "UPDATE quests SET progress=? WHERE account_id=? AND quest_id=?",
                (new_progress, account_id, row["quest_id"]),
            )
            changed.append((row["quest_id"], new_progress))
        self.conn.commit()
        return changed

    def increment_item_collect_quest(self, account_id, item_id, amount=1):
        """v0.8.66: zwykłe collect liczy wyłącznie nowe zdobycze po przyjęciu."""
        amount = max(0, int(amount))
        if amount <= 0:
            return []
        rows = self.conn.execute(
            "SELECT * FROM quests WHERE account_id=? AND status='active'",
            (account_id,),
        ).fetchall()
        changed = []
        for row in rows:
            quest = QUESTS.get(row["quest_id"])
            if (
                not quest
                or quest.get("kind") != "collect"
                or quest.get("track_craft_progress")
                or quest.get("target") != item_id
            ):
                continue
            needed = max(1, int(quest.get("needed", 1)))
            old_progress = max(0, int(row["progress"]))
            new_progress = min(needed, old_progress + amount)
            if new_progress == old_progress:
                continue
            self.conn.execute(
                "UPDATE quests SET progress=? WHERE account_id=? AND quest_id=?",
                (new_progress, account_id, row["quest_id"]),
            )
            changed.append((row["quest_id"], new_progress, needed))
        self.conn.commit()
        return changed

    def increment_craft_quest(
        self, account_id, item_id, amount=1
    ):
        amount = max(0, int(amount))
        if amount <= 0:
            return []

        rows = self.conn.execute(
            "SELECT * FROM quests "
            "WHERE account_id=? AND status='active'",
            (account_id,),
        ).fetchall()

        changed = []
        for row in rows:
            quest = QUESTS.get(row["quest_id"])
            if not quest or not quest.get(
                "track_craft_progress"
            ):
                continue

            if quest.get("kind") == "collect":
                if quest.get("target") != item_id:
                    continue
                needed = max(
                    1, int(quest.get("needed", 1))
                )
                old_progress = int(row["progress"])
                new_progress = min(
                    needed,
                    old_progress + amount,
                )
                self.conn.execute(
                    "UPDATE quests SET progress=? "
                    "WHERE account_id=? AND quest_id=?",
                    (
                        new_progress,
                        account_id,
                        row["quest_id"],
                    ),
                )
                changed.append(
                    (
                        row["quest_id"],
                        new_progress,
                        needed,
                    )
                )
                continue

            if quest.get("kind") == "craft_set":
                targets = tuple(
                    quest.get("targets") or ()
                )
                if item_id not in targets:
                    continue

                index = targets.index(item_id)
                old_mask = int(row["progress"])
                new_mask = old_mask | (1 << index)
                if new_mask == old_mask:
                    continue

                self.conn.execute(
                    "UPDATE quests SET progress=? "
                    "WHERE account_id=? AND quest_id=?",
                    (
                        new_mask,
                        account_id,
                        row["quest_id"],
                    ),
                )
                changed.append(
                    (
                        row["quest_id"],
                        int(new_mask).bit_count(),
                        len(targets),
                    )
                )

        self.conn.commit()
        return changed

    def increment_resource_quest(
        self, account_id, item_id, amount=1
    ):
        amount = max(0, int(amount))
        if amount <= 0:
            return []

        rows = self.conn.execute(
            "SELECT * FROM quests "
            "WHERE account_id=? AND status='active'",
            (account_id,),
        ).fetchall()

        changed = []
        progress_item_id = canonical_profession_resource_id(item_id)
        for row in rows:
            quest = QUESTS.get(row["quest_id"])
            quest_target = canonical_profession_resource_id(
                quest.get("target") if quest else ""
            )
            if (
                not quest
                or quest.get("kind") != "collect_resource"
                or not quest.get("track_resource_progress")
                or quest_target != progress_item_id
            ):
                continue

            needed = max(
                1, int(quest.get("needed", 1))
            )
            old_progress = int(row["progress"])
            new_progress = min(
                needed,
                old_progress + amount,
            )
            # v0.30.7: po osiągnięciu celu nie zwracamy sztucznej
            # "zmiany" 30->30. Dzięki temu komunikat o gotowości questa
            # nie powtarza się przy każdym następnym zbiorze.
            if new_progress == old_progress:
                continue
            self.conn.execute(
                "UPDATE quests SET progress=? "
                "WHERE account_id=? AND quest_id=?",
                (
                    new_progress,
                    account_id,
                    row["quest_id"],
                ),
            )
            changed.append(
                (
                    row["quest_id"],
                    new_progress,
                    needed,
                )
            )

        self.conn.commit()
        return changed

    def resource_set_progress_v0929(self, account_id, quest_id, targets):
        result = {}
        for target_id in targets:
            row = self.conn.execute(
                "SELECT progress FROM quest_resource_progress_v0929 "
                "WHERE account_id=? AND quest_id=? AND target_id=?",
                (account_id, quest_id, canonical_profession_resource_id(target_id)),
            ).fetchone()
            result[target_id] = max(0, int(row["progress"])) if row else 0
        return result

    def distinct_category_items_v023(self, account_id, quest_id):
        rows = self.conn.execute(
            "SELECT target_id FROM quest_resource_progress_v0929 "
            "WHERE account_id=? AND quest_id=? AND progress>0 ORDER BY target_id",
            (account_id, quest_id),
        ).fetchall()
        return [str(row["target_id"]) for row in rows]

    def mark_distinct_category_item_v023(self, account_id, quest_id, item_id, needed):
        """Zapisz jeden NOWY gatunek/typ dla questa wymagającego różnych zasobów."""
        needed = max(1, int(needed))
        existing = self.distinct_category_items_v023(account_id, quest_id)
        if item_id in existing or len(existing) >= needed:
            return len(existing), False
        self.conn.execute(
            "INSERT INTO quest_resource_progress_v0929(account_id,quest_id,target_id,progress) "
            "VALUES(?,?,?,1) ON CONFLICT(account_id,quest_id,target_id) DO NOTHING",
            (account_id, quest_id, str(item_id)),
        )
        count = len(self.distinct_category_items_v023(account_id, quest_id))
        self.conn.execute(
            "UPDATE quests SET progress=? WHERE account_id=? AND quest_id=?",
            (min(needed, count), account_id, quest_id),
        )
        self.conn.commit()
        return min(needed, count), True

    def increment_resource_set_quest_v0929(self, account_id, item_id, amount=1):
        amount = max(0, int(amount))
        if amount <= 0:
            return []
        item_base = canonical_profession_resource_id(item_id)
        rows = self.conn.execute(
            "SELECT * FROM quests WHERE account_id=? AND status='active'",
            (account_id,),
        ).fetchall()
        changed = []
        for row in rows:
            quest = QUESTS.get(row["quest_id"])
            if not quest or quest.get("kind") != "collect_resource_set":
                continue
            requirements = dict(quest.get("resource_targets") or {})
            matched_target = None
            target_needed = 0
            for target_id, needed in requirements.items():
                if canonical_profession_resource_id(target_id) == item_base:
                    matched_target = target_id
                    target_needed = max(1, int(needed))
                    break
            if matched_target is None:
                continue
            current = self.resource_set_progress_v0929(
                account_id, row["quest_id"], requirements
            ).get(matched_target, 0)
            updated = min(target_needed, current + amount)
            # v0.30.7: brak ponownego komunikatu po osiągnięciu limitu.
            if updated == current:
                continue
            self.conn.execute(
                "INSERT INTO quest_resource_progress_v0929(account_id,quest_id,target_id,progress) "
                "VALUES(?,?,?,?) ON CONFLICT(account_id,quest_id,target_id) "
                "DO UPDATE SET progress=excluded.progress",
                (account_id, row["quest_id"], canonical_profession_resource_id(matched_target), updated),
            )
            counts = self.resource_set_progress_v0929(
                account_id, row["quest_id"], requirements
            )
            counts[matched_target] = updated
            total = sum(min(max(1, int(requirements[t])), int(counts.get(t, 0))) for t in requirements)
            self.conn.execute(
                "UPDATE quests SET progress=? WHERE account_id=? AND quest_id=?",
                (total, account_id, row["quest_id"]),
            )
            changed.append((row["quest_id"], total, int(quest.get("needed", total)), matched_target, updated, target_needed))
        self.conn.commit()
        return changed

    def complete_quest(self, account_id, quest_id):
        self.conn.execute(
            "UPDATE quests SET status='completed',completed_at=?,"
            "completion_count=completion_count+1 "
            "WHERE account_id=? AND quest_id=?",
            (int(time.time()), account_id, quest_id),
        )
        self.conn.commit()
