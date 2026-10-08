# -*- coding: utf-8 -*-
"""v1.18.0: read-only, screen-reader-friendly quality-of-life commands.

This module intentionally neither grants rewards nor mutates permanent player data.
"""
from __future__ import annotations

import time
import unicodedata


def _norm_v1180(value):
    return "".join(c for c in unicodedata.normalize("NFKD", str(value or "").lower())
                   if not unicodedata.combining(c)).replace("ł", "l").strip()


def _treasure_filter_v1180(argument):
    """Return (rarity, limit, name search). Invalid inputs yield a helpful error."""
    words = str(argument or "").strip().split()
    rarity, limit, query = None, 10, ""
    if words and _norm_v1180(words[0]) in ("wszystkie", "all", "ostatnie"):
        words.pop(0)
    elif words and _norm_v1180(words[0]) in ("legendarne", "legendarna", "legendary", "legend"):
        rarity = "legendary"
        words.pop(0)
    elif words and _norm_v1180(words[0]) in ("epickie", "epicka", "epic"):
        rarity = "epic"
        words.pop(0)
    elif words and _norm_v1180(words[0]) in ("rzadkie", "rzadka", "rare"):
        rarity = "rare"
        words.pop(0)
    if words and words[0].isdigit():
        limit = max(1, min(30, int(words.pop(0))))
    if words and _norm_v1180(words[0]) in ("szukaj", "search"):
        words.pop(0)
    query = " ".join(words).strip()
    return rarity, limit, query


class SessionQualityOfLifeV1180Mixin:
    async def show_treasures_v1180(self, args=""):
        """Concise filtered view of the existing persistent drop_history table."""
        if self.account_id is None:
            await self.send("Najpierw zaloguj postać.")
            return
        rarity, limit, query = _treasure_filter_v1180(args)
        if _norm_v1180(args) in ("pomoc", "help", "?"):
            await self.send("Zdobycze: zdobycze [legendarne|epickie|rzadkie|wszystkie] [1-30]; zdobycze szukaj <nazwa>.")
            return
        # Preserve existing records: no table migration, no extra drop writes.
        rows = self.server.db.conn.execute(
            "SELECT item_name, rarity, source, zone FROM drop_history "
            "WHERE account_id=? ORDER BY id DESC LIMIT 500", (self.account_id,)
        ).fetchall()
        filtered = []
        for row in rows:
            row_rarity = _norm_v1180(row["rarity"])
            if rarity and rarity not in row_rarity and {
                "legendary": "legend", "epic": "epic", "rare": "rar"
            }[rarity] not in row_rarity:
                continue
            if query and _norm_v1180(query) not in _norm_v1180(
                " ".join(str(row[k] or "") for k in ("item_name", "rarity", "source", "zone"))
            ):
                continue
            filtered.append(row)
            if len(filtered) >= limit:
                break
        if not filtered:
            await self.send("ZDOBYCZE: brak pasujących zapisów w historii dropów.")
            return
        await self.send(f"ZDOBYCZE: ostatnie {len(filtered)} pasujących wpisów. Historia jest trwała.")
        for index, row in enumerate(filtered, 1):
            await self.send(
                f"{index}. {row['item_name']}; rzadkość: {row['rarity'] or 'nieznana'}; "
                f"źródło: {row['source'] or 'nieznane'}; "
                f"strefa: {row['zone'] or 'nieznana'}."
            )
        await self.send("Filtry: zdobycze legendarne, zdobycze rzadkie 20, zdobycze szukaj <nazwa>.")

    async def show_tasks_v1180(self, args=""):
        """One read-only snapshot of current automation and progress for NVDA."""
        if self.account_id is None:
            await self.send("Najpierw zaloguj postać.")
            return
        await self.send("PRACE I KOLEJKI — STATUS")
        smelt = getattr(self, "smelt_task_v1124", None)
        if smelt is not None and not smelt.done():
            end = getattr(self, "smelt_wait_until_v1180", 0.0)
            remaining = max(0, int(round(end - time.monotonic()))) if end else None
            label = str(getattr(self, "smelt_label_v1124", "") or "w toku")
            detail = f"; pozostało około {remaining} s" if remaining is not None else "; kończenie partii"
            await self.send(f"Przetop: {label}{detail}. Zatrzymanie: przetop stop.")
        else:
            await self.send("Przetop: nieaktywny.")
        activities = (
            ("Wędkarstwo", "auto_fishing", "auto_fishing_task"),
            ("Górnictwo", "auto_mining", "auto_mining_task"),
            ("Drwalstwo", "auto_woodcutting", "auto_woodcutting_task"),
            ("Zielarstwo", "auto_herbalism", "auto_herbalism_task"),
        )
        for label, enabled_name, task_name in activities:
            task = getattr(self, task_name, None)
            running = bool(task is not None and not task.done())
            if getattr(self, enabled_name, False) and running:
                await self.send(f"{label}: automatyczne zbieranie aktywne.")
            elif running:
                await self.send(f"{label}: kończenie bieżącej czynności, bez następnej.")
        enabled = self.server.db.skill_queue_enabled(self.account_id)
        rows = self.server.db.skill_queue_rows(self.account_id)
        await self.send(f"Kolejka skilli: {'włączona' if enabled else 'wyłączona'}, "
                        f"{len(rows)} zapisanych umiejętności. Szczegóły: kolejka lista.")
        if not any(getattr(self, enabled_name, False) for _, enabled_name, _ in activities) and not (
            smelt is not None and not smelt.done()
        ):
            await self.send("Brak aktywnej automatycznej pracy profesji.")
        await self.send("Komendy: przetop status, kolejka lista, prowadz status, prace.")
