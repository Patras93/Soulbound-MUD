# -*- coding: utf-8 -*-
"""Soulbound v0.59.0 - precise 'braki' progression summary."""
from __future__ import annotations

from core.bootstrap_economy_professions import SOUL_TRIAL_QUEST_IDS, currency_reading_text
from core.progression_600 import CHARACTER_MAX_LEVEL, PROFESSION_MAX_LEVEL, SOUL_MAX_TIER
from core.progression_resources import character_xp_to_next
from network.protocol_gameplay_utils import V0926_GUILD_MAX_LEVEL, v0926_guild_upgrade_cost
from player.session_mixins.progress_titles import PROFESSIONS_V0580
from systems.content_registry import QUESTS
from world.dynamic_content import COLLECTION_CATALOGS
from world.economy_quests import COLLECTION_CATEGORY_LABELS


class SessionProgressGapsV0590Mixin:
    """NVDA-friendly list of concrete amounts still missing for major progression."""

    def _character_level_gap_v0590(self):
        c = self.character
        level = int(c.character_level)
        if level >= CHARACTER_MAX_LEVEL:
            return f"Level postaci: maksimum {CHARACTER_MAX_LEVEL}/{CHARACTER_MAX_LEVEL}."
        needed = int(character_xp_to_next(level))
        current = max(0, int(c.character_xp))
        missing = max(0, needed - current)
        return (
            f"Level postaci: brakuje {missing} EXP do Levelu {level + 1}. "
            f"Masz {current} z {needed}."
        )

    def _soul_tier_gap_v0590(self):
        c = self.character
        current_tier = max(1, int(c.soul_tier))
        if current_tier >= SOUL_MAX_TIER:
            return f"Soul Tier: maksimum {SOUL_MAX_TIER}/{SOUL_MAX_TIER}."

        next_tier = current_tier + 1
        required_level = int(c.soul_level_cap_for_current_tier())
        soul_level = int(c.soul_level)
        if soul_level < required_level:
            levels_missing = required_level - soul_level
            xp_need = int(c.soul_xp_to_next())
            xp_now = max(0, int(c.soul_xp))
            xp_missing = max(0, xp_need - xp_now)
            return (
                f"Soul Tier {next_tier}: najpierw osiągnij Soul Level {required_level}. "
                f"Brakuje {levels_missing} poziomów; do najbliższego Soul Levelu brakuje "
                f"{xp_missing} Soul XP ({xp_now}/{xp_need})."
            )

        quest_id = SOUL_TRIAL_QUEST_IDS.get(next_tier)
        quest = QUESTS.get(quest_id) if quest_id else None
        if not quest:
            return f"Soul Tier {next_tier}: próg Soul Level {required_level} osiągnięty; użyj unlock, jeśli Tier jest gotowy."

        row = self.server.db.quest(self.account_id, quest_id)
        giver = str(quest.get("giver") or "Kapłan Elor")
        needed = max(1, int(quest.get("needed", 1) or 1))
        if row and str(row["status"]) == "completed":
            return f"Soul Tier {next_tier}: Próba ukończona. Brakuje tylko użycia komendy unlock."
        if row and str(row["status"]) == "active":
            progress = self.quest_progress_value(quest_id)
            progress = max(0, int(row["progress"] if progress is None else progress))
            remaining = max(0, needed - progress)
            if remaining <= 0:
                return (
                    f"Soul Tier {next_tier}: Próba {quest['name']} ma wykonany cel {progress}/{needed}. "
                    f"Brakuje oddania zadania. NPC: {giver}; potem użyj unlock."
                )
            return (
                f"Soul Tier {next_tier}: aktywna Próba {quest['name']}. "
                f"Postęp {progress}/{needed}; brakuje {remaining}. NPC: {giver}."
            )
        return (
            f"Soul Tier {next_tier}: wymagany Soul Level {required_level} masz osiągnięty. "
            f"Brakuje przyjęcia Próby {quest['name']}. NPC: {giver}."
        )

    def _profession_gap_lines_v0590(self):
        levels = self._profession_levels_v0580()
        parts = []
        for profession in PROFESSIONS_V0580:
            level, xp = levels.get(profession, (1, 0))
            level = max(1, int(level))
            xp = max(0, int(xp))
            if level >= PROFESSION_MAX_LEVEL:
                parts.append(f"{profession}: max {level}/{PROFESSION_MAX_LEVEL}")
                continue
            needed = int(self.profession_xp_to_next(level, profession))
            missing = max(0, needed - xp)
            parts.append(
                f"{profession}: brakuje {missing} XP do {level + 1} ({xp}/{needed})"
            )
        lines = []
        for start in range(0, len(parts), 4):
            label = "Profesje" if start == 0 else "Profesje ciąg dalszy"
            lines.append(f"{label}: " + "; ".join(parts[start:start + 4]) + ".")
        return lines

    def _guild_gap_v0590(self):
        membership = self.server.db.clan_membership(self.account_id)
        if not membership:
            return "Gildia gracza: nie należysz do Gildii."
        level = max(1, int(membership["level"] or 1))
        if level >= V0926_GUILD_MAX_LEVEL:
            return f"Gildia gracza: maksimum {V0926_GUILD_MAX_LEVEL}/{V0926_GUILD_MAX_LEVEL}."
        clan_id = int(membership["clan_id"])
        grow = self.server.db.conn.execute(
            "SELECT treasury FROM player_clans WHERE id=?", (clan_id,)
        ).fetchone()
        treasury = max(0, int(grow["treasury"] or 0)) if grow else 0
        cost = max(0, int(v0926_guild_upgrade_cost(level)))
        missing = max(0, cost - treasury)
        if missing <= 0:
            return (
                f"Gildia gracza: poziom {level}/{V0926_GUILD_MAX_LEVEL}. "
                f"Skarbiec ma środki na poziom {level + 1}; koszt {currency_reading_text(cost, 0, 0)}. "
                "Lider może użyć gildia rozbuduj."
            )
        return (
            f"Gildia gracza: poziom {level}/{V0926_GUILD_MAX_LEVEL}. "
            f"Do rozbudowy na {level + 1} brakuje w skarbcu {currency_reading_text(missing, 0, 0)}; "
            f"koszt {currency_reading_text(cost, 0, 0)}."
        )

    async def _collection_gap_v0590(self):
        await self.sync_collection_from_inventory()
        total = 0
        found = 0
        incomplete = []
        for category, catalog in COLLECTION_CATALOGS.items():
            catalog_ids = set(catalog)
            if not catalog_ids:
                continue
            discovered = set(self.server.db.collection_entry_ids(self.account_id, category))
            category_found = len(catalog_ids.intersection(discovered))
            category_total = len(catalog_ids)
            category_missing = max(0, category_total - category_found)
            total += category_total
            found += category_found
            if category_missing:
                label = COLLECTION_CATEGORY_LABELS.get(category, str(category))
                incomplete.append((category_missing, label, category_found, category_total))
        missing = max(0, total - found)
        if missing <= 0:
            return "Kolekcje: komplet 100%. Niczego nie brakuje."
        incomplete.sort(key=lambda row: (row[0], row[3], row[1]))
        nearest = "; ".join(
            f"{label} — brakuje {cat_missing} ({cat_found}/{cat_total})"
            for cat_missing, label, cat_found, cat_total in incomplete[:3]
        )
        pct = int(found * 100 / max(1, total))
        return (
            f"Kolekcje: {found}/{total}, {pct}%. Do pełnego kompletu brakuje {missing} wpisów. "
            + (f"Najbliższe kompletu: {nearest}." if nearest else "")
        )

    def _active_goal_lines_v0590(self):
        lines = []
        active_rows = [
            row for row in self.server.db.quest_rows(self.account_id)
            if str(row["status"]) == "active" and row["quest_id"] in QUESTS
        ]
        active_rows.sort(key=lambda row: str(QUESTS[row["quest_id"]].get("name", row["quest_id"])).casefold())
        if active_rows:
            lines.append(f"Aktywne questy: {len(active_rows)}.")
            for row in active_rows[:5]:
                quest_id = row["quest_id"]
                quest = QUESTS[quest_id]
                needed = max(1, int(quest.get("needed", 1) or 1))
                progress = self.quest_progress_value(quest_id)
                progress = max(0, int(row["progress"] if progress is None else progress))
                remaining = max(0, needed - progress)
                if remaining <= 0:
                    lines.append(f"Cel: {quest['name']} — gotowe do oddania.")
                else:
                    lines.append(
                        f"Cel: {quest['name']} — {progress}/{needed}; brakuje {remaining}."
                    )
            if len(active_rows) > 5:
                lines.append(f"Pozostałe aktywne questy: {len(active_rows) - 5}. Wpisz quest, aby zobaczyć wszystkie.")

        bounty = self.server.db.bounty_board_state(self.account_id).get("active") or {}
        if bounty:
            progress = max(0, int(bounty.get("progress", 0) or 0))
            needed = max(1, int(bounty.get("needed", 1) or 1))
            lines.append(
                f"Tablica Zleceń: {bounty.get('label', 'Kontrakt')} — {progress}/{needed}; "
                f"brakuje {max(0, needed - progress)}."
            )

        legendary = self.server.db.legendary_contract_state_v022(self.account_id).get("active") or {}
        if legendary:
            progress = max(0, int(legendary.get("progress", 0) or 0))
            needed = max(1, int(legendary.get("needed", 1) or 1))
            lines.append(
                f"Legendarny kontrakt: {legendary.get('label', 'Kontrakt')} — {progress}/{needed}; "
                f"brakuje {max(0, needed - progress)}."
            )

        postal = self.server.db.postal_delivery_state_v0522(self.account_id).get("active") or {}
        if postal:
            lines.append(
                f"Dostawa kurierska: {postal.get('package_name', 'Paczka')} do {postal.get('destination_city', '?')}; "
                f"cel: prowadz {self.postal_guide_query_v0522(postal)}."
            )

        if not lines:
            lines.append("Aktywne cele: brak aktywnych questów, kontraktów i dostaw.")
        return lines

    async def show_progress_gaps_v0590(self, _args=""):
        await self.send("BRAKI — DO NAJBLIŻSZYCH CELÓW")
        await self.send(self._character_level_gap_v0590())
        await self.send(self._soul_tier_gap_v0590())
        for line in self._profession_gap_lines_v0590():
            await self.send(line)
        await self.send(self._guild_gap_v0590())
        await self.send(await self._collection_gap_v0590())
        for line in self._active_goal_lines_v0590():
            await self.send(line)


__all__ = ["SessionProgressGapsV0590Mixin"]
