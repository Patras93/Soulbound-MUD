# -*- coding: utf-8 -*-
"""Soulbound v0.56.0 - durable activity journal and NVDA-friendly 'co robic'."""
from __future__ import annotations

import time

from network.protocol_gameplay_utils import normalize_lookup_text
from player.session_mixins.exp_terrain import EXP_AREAS, NPCS, QUESTS
from world.dynamic_content import ALL_EXPLORATION_ROOMS


_ACTIVITY_CATEGORY_ALIASES_V0560 = {
    "boss": "boss", "bossy": "boss", "bossowie": "boss",
    "quest": "quest", "questy": "quest", "zadania": "quest",
    "drop": "drop", "dropy": "drop", "loot": "drop",
    "dostawa": "dostawa", "dostawy": "dostawa", "paczki": "dostawa",
    "osiagniecie": "osiagniecie", "osiagniecia": "osiagniecie", "achievement": "osiagniecie",
    "awans": "awans", "awansy": "awans", "level": "awans",
}


class SessionActivityGuidanceV0560Mixin:
    def _activity_age_v0560(self, created_at):
        age = max(0, int(time.time()) - int(created_at or 0))
        if age < 60:
            return "teraz"
        if age < 3600:
            return f"{max(1, age // 60)} min temu"
        if age < 86400:
            return f"{max(1, age // 3600)} godz. temu"
        return f"{max(1, age // 86400)} dni temu"

    async def show_activity_journal_v0560(self, args=""):
        raw = str(args or "").strip()
        parts = raw.split()
        category = None
        limit = 20
        for part in parts:
            norm = normalize_lookup_text(part)
            if norm.isdigit():
                limit = max(1, min(100, int(norm)))
                continue
            category = _ACTIVITY_CATEGORY_ALIASES_V0560.get(norm, category)
        rows = self.server.db.activity_rows_v0560(self.account_id, limit=limit, category=category)
        label = f" — {category}" if category else ""
        await self.send(f"DZIENNIK AKTYWNOŚCI{label}: ostatnie {len(rows)} wpisów.")
        if not rows:
            await self.send(
                "Brak wpisów w tej kategorii. Dziennik zapisuje nowe zdarzenia od v0.56.0."
            )
            return
        for index, row in enumerate(rows, 1):
            detail = str(row["detail"] or "").strip()
            extra = f" {detail}" if detail else ""
            await self.send(
                f"{index}. [{row['category']}] {row['title']}. {self._activity_age_v0560(row['created_at'])}.{extra}"
            )
        await self.send(
            "Filtry: dziennik bossy, questy, dropy, dostawy, osiągnięcia, awansy. "
            "Możesz dodać liczbę, np. dziennik questy 10."
        )

    def _what_to_do_add_v0560(self, rows, seen, key, text):
        if key in seen or not text:
            return
        seen.add(key)
        rows.append(str(text))

    async def show_what_to_do_v0560(self, args=""):
        suggestions = []
        seen = set()

        # 1. Ready/active quests are the most concrete next actions.
        active_rows = [
            row for row in self.server.db.quest_rows(self.account_id)
            if row["status"] == "active" and row["quest_id"] in QUESTS
        ]
        for row in active_rows:
            qid = row["quest_id"]
            quest = QUESTS[qid]
            progress, ready = self.quest_progress_for_turnin(qid)
            if ready:
                giver = quest.get("giver", "NPC")
                self._what_to_do_add_v0560(
                    suggestions, seen, "ready_quest",
                    f"Oddaj gotowe zadanie: {quest['name']}. NPC: {giver}. Użyj prowadz {giver}."
                )
                break
        for row in active_rows:
            qid = row["quest_id"]
            quest = QUESTS[qid]
            progress, ready = self.quest_progress_for_turnin(qid)
            if not ready:
                self._what_to_do_add_v0560(
                    suggestions, seen, "active_quest",
                    f"Kontynuuj zadanie: {quest['name']}. Postęp {progress} z {quest.get('needed', '?')}."
                )
                break

        # 2. A quest available from an NPC standing in the current room.
        for npc_id, npc in self.local_quest_npcs().items():
            for qid in self.quest_ids_for_npc(npc_id, npc):
                if self.quest_is_available_to_accept_v099(qid):
                    self._what_to_do_add_v0560(
                        suggestions, seen, "local_quest",
                        f"Masz nowe zadanie tutaj: {QUESTS[qid]['name']} od {npc['name']}. Wpisz quest list {npc['name']}."
                    )
                    break
            if "local_quest" in seen:
                break

        # 3. Courier work: finish an active parcel first; otherwise take a job or go to the office.
        delivery = self.server.db.postal_delivery_state_v0522(self.account_id)
        active_delivery = delivery.get("active") or {}
        if active_delivery:
            destination = active_delivery.get("destination_city", "cel dostawy")
            self._what_to_do_add_v0560(
                suggestions, seen, "courier",
                f"Dostarcz aktywną paczkę do: {destination}. Wpisz poczta status albo prowadz {destination}."
            )
        else:
            city = self.postal_city_for_room_v0522()
            if city:
                self._what_to_do_add_v0560(
                    suggestions, seen, "courier",
                    f"Weź zlecenie kurierskie w {city}. Wpisz poczta."
                )
            else:
                self._what_to_do_add_v0560(
                    suggestions, seen, "courier",
                    "Sprawdź zlecenia Gildii Kurierów. Wpisz prowadz poczta, a potem poczta."
                )

        # 4. Pick the current combat area from the real dynamic recommendation logic.
        recommended = [area for area in EXP_AREAS if self.exp_area_recommended(area)]
        if recommended:
            area = recommended[0]
        elif EXP_AREAS:
            power = self.character_progression_power()
            area = min(EXP_AREAS, key=lambda a: abs(self.exp_area_target_power(a) - power))
        else:
            area = None
        if area:
            self._what_to_do_add_v0560(
                suggestions, seen, "exp",
                f"Poexpij w terenie dopasowanym do postaci: {area['name']}. Prowadzenie: prowadz {area['guide']}."
            )

        # 5. Global hourly quest that is actually off cooldown now.
        for qid in self.hourly_quest_ids():
            if self.quest_is_available_to_accept_v099(qid):
                quest = QUESTS[qid]
                self._what_to_do_add_v0560(
                    suggestions, seen, "hourly",
                    f"Dostępne jest godzinne zlecenie: {quest['name']}. Dawca: {quest.get('giver','NPC')}. Wpisz quest godzinne."
                )
                break

        # 6. Profession catch-up: suggest the currently lowest profession.
        try:
            row = self.server.db.conn.execute(
                "SELECT profession,level FROM professions WHERE account_id=? ORDER BY level ASC,profession COLLATE NOCASE LIMIT 1",
                (self.account_id,),
            ).fetchone()
        except Exception:
            row = None
        if row:
            self._what_to_do_add_v0560(
                suggestions, seen, "profession",
                f"Rozwiń najsłabszą profesję: {row['profession']} poziom {int(row['level'])}. Wpisz walk profesje lub help profesje."
            )

        # 7. Exploration is always useful if the world is not complete.
        discovered = len(self.server.db.discovered_room_ids(self.account_id))
        total = max(1, len(ALL_EXPLORATION_ROOMS))
        if discovered < total:
            pct = int(round(discovered * 100 / total))
            self._what_to_do_add_v0560(
                suggestions, seen, "exploration",
                f"Eksploruj świat: odkryto około {pct} procent śledzonych lokacji. Wpisz mapa albo eksploracja."
            )

        # Guaranteed fallbacks keep the command predictable: exactly five useful lines.
        fallbacks = [
            ("hourly_fallback", "Sprawdź wszystkie zlecenia odnawialne: quest godzinne."),
            ("events", "Sprawdź aktywne wydarzenia świata: eventy albo worldevents."),
            ("progress", "Sprawdź najbliższy cel progresji: progress oraz xp."),
            ("bestiary", "Uzupełniaj Bestiariusz i kolekcje: bestiariusz oraz kolekcja."),
            ("dungeons", "Sprawdź postęp instancji: krypta, wieza albo megadungeony."),
        ]
        for key, text in fallbacks:
            if len(suggestions) >= 5:
                break
            self._what_to_do_add_v0560(suggestions, seen, key, text)

        await self.send(
            f"CO ROBIĆ — 5 PROPOZYCJI. Level postaci {int(self.character.character_level)}; "
            f"orientacyjna siła {self.character_progression_power()}."
        )
        for index, text in enumerate(suggestions[:5], 1):
            await self.send(f"{index}. {text}")


__all__ = ["SessionActivityGuidanceV0560Mixin"]
