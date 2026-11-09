# -*- coding: utf-8 -*-
"""v109: muzeum, osiągnięcia i zlecenia — museum. Historyczne metody bez zmian."""
from .dependencies import *

class MuseumMuseumV109Mixin:
    def v0260_completed_set_ids(self):
            discovered_eq = self.server.db.collection_entry_ids(self.account_id, "equipment")
            completed = set()
            for set_id, piece_groups in V0260_SET_PIECE_GROUPS.items():
                if piece_groups and all(set(ids).intersection(discovered_eq) for ids in piece_groups.values()):
                    completed.add(set_id)
            return completed

    def v0260_museum_found_ids(self, category):
            category = str(category or "")
            if category == "sets":
                return self.v0260_completed_set_ids()
            db_category = {
                "fish": "fish", "minerals": "minerals", "herbs": "herbs",
                "wood": "wood_v026", "bosses": "bosses",
                "legendary": "legendary_v026", "secrets": "museum_secrets_v026",
            }.get(category)
            if not db_category:
                return set()
            return self.server.db.collection_entry_ids(self.account_id, db_category)

    def v0260_museum_snapshot(self):
            rows = []
            total_found = 0
            total_entries = 0
            for category, catalog in V0260_MUSEUM_CATALOGS.items():
                found = self.v0260_museum_found_ids(category)
                count = len(set(catalog).intersection(found))
                total = len(catalog)
                pct = int(count * 100 / max(1, total))
                rows.append((category, count, total, pct))
                total_found += count
                total_entries += total
            # Każdy z ośmiu działów waży równo. Dzięki temu tysiące wariantów
            # legendarnego EQ nie dominują procentu całej kolekcji.
            overall = round(
                sum((count * 100.0 / max(1, total)) for _cat, count, total, _pct in rows)
                / max(1, len(rows)),
                1,
            )
            prestige = int(round(overall * 10))
            return rows, total_found, total_entries, overall, prestige

    async def v0260_sync_museum(self):
            # Importuje stare osiągnięcia do nowego Muzeum bez odbierania graczowi historii.
            await self.sync_collection_from_inventory()
            old_materials = self.server.db.collection_entry_ids(self.account_id, "materials")
            for item_id in V0260_WOOD_CATALOG:
                if item_id in old_materials:
                    self.server.db.add_collection_entry(self.account_id, "wood_v026", item_id)

            historic_items = set()
            for old_cat in ("equipment", "unique", "named"):
                historic_items.update(self.server.db.collection_entry_ids(self.account_id, old_cat))
            for item_id in V0260_LEGENDARY_ITEM_CATALOG:
                if item_id in historic_items:
                    self.server.db.add_collection_entry(self.account_id, "legendary_v026", item_id)

            for room_id in self.server.db.collection_entry_ids(self.account_id, "surface_secrets_v0140"):
                if room_id in V0260_SURFACE_SECRET_CATALOG:
                    self.server.db.add_collection_entry(self.account_id, "museum_secrets_v026", room_id)
            for kind in INSTANCE_MAP_DEFS:
                for row in self.server.db.instance_secret_rows(self.account_id, kind):
                    idx = instance_secret_index(kind, int(row["floor"]))
                    if idx is not None:
                        key = f"instance:{kind}:{idx}"
                        if key in V0260_INSTANCE_SECRET_CATALOG:
                            self.server.db.add_collection_entry(self.account_id, "museum_secrets_v026", key)

    async def v0260_check_museum_rewards(self, announce=True):
            rows, _found, _total, overall, _prestige = self.v0260_museum_snapshot()
            for category, count, total, pct in rows:
                if total <= 0 or count < total:
                    continue
                title_name = V0260_MUSEUM_CATEGORY_TITLES[category]
                aid = f"museum:{category}:complete"
                if self.server.db.unlock_achievement(self.account_id, aid, f"Muzeum: {V0260_MUSEUM_LABELS[category]}", "Platinum"):
                    if announce:
                        await self.send(f"Muzeum ukończone: {V0260_MUSEUM_LABELS[category]}, 100%.")
                await self.unlock_title(f"museum:{category}", title_name, announce=announce)
            for threshold, title_name in V0260_GLOBAL_MUSEUM_TITLES:
                if overall >= threshold:
                    await self.unlock_title(f"museum:overall:{threshold}", title_name, announce=announce)
            return overall

    async def show_museum_v0260(self, args=""):
            await self.v0260_sync_museum()
            await self.v0260_check_museum_rewards(announce=True)
            raw = str(args or "").strip()
            norm = normalize_lookup_text(raw)
            parts = raw.split()
            if not norm or norm in ("status", "all", "wszystko"):
                rows, found, total, overall, prestige = self.v0260_museum_snapshot()
                await self.send(f"MUZEUM SOULBOUND — ukończenie kolekcji całej gry: {found} z {total}, {overall}%.")
                await self.send(f"Prestiż Muzealny: {prestige} z 1000. Ranga: {v0260_museum_rank(overall)}.")
                for category, count, cat_total, pct in rows:
                    await self.send(f"{V0260_MUSEUM_LABELS[category]}: {count} z {cat_total}, {pct}%.")
                await self.send("Szczegóły: muzeum ryby, rudy, ziola, drewno, bossowie, sety, legendarne albo sekrety.")
                return

            key = normalize_lookup_text(parts[0]).replace(" ", "") if parts else norm.replace(" ", "")
            category = V0260_MUSEUM_ALIASES.get(key)
            if not category:
                await self.send("Działy Muzeum: ryby, rudy, ziola, drewno, bossowie, sety, legendarne, sekrety.")
                return
            page = 1
            if len(parts) > 1 and parts[-1].isdigit():
                page = max(1, int(parts[-1]))
            catalog = V0260_MUSEUM_CATALOGS[category]
            found_ids = self.v0260_museum_found_ids(category)
            rows = sorted(catalog.items(), key=lambda row: normalize_lookup_text(row[1]))
            page_size = 40
            pages = max(1, math.ceil(len(rows) / page_size))
            page = min(page, pages)
            found_count = len(set(catalog).intersection(found_ids))
            pct = int(found_count * 100 / max(1, len(catalog)))
            await self.send(f"MUZEUM — {V0260_MUSEUM_LABELS[category]}: {found_count} z {len(catalog)}, {pct}%. Strona {page} z {pages}.")
            start = (page - 1) * page_size
            for number, (entry_id, name) in enumerate(rows[start:start + page_size], start + 1):
                if entry_id in found_ids:
                    await self.send(f"{number}. {name}. Odkryty.")
                else:
                    await self.send(f"{number}. Nieodkryty wpis.")
            if page < pages:
                await self.send(f"Następna strona: muzeum {parts[0]} {page + 1}.")

    async def show_prestige_v0260(self):
            await self.v0260_sync_museum()
            await self.v0260_check_museum_rewards(announce=True)
            _rows, found, total, overall, prestige = self.v0260_museum_snapshot()
            await self.send(f"PRESTIŻ MUZEALNY: {prestige} z 1000. Ranga: {v0260_museum_rank(overall)}.")
            await self.send(f"Muzeum: {found} z {total} wpisów, {overall}% ukończenia.")
            active = self.character.active_title or "brak"
            await self.send(f"Aktywny tytuł: {active}.")
            bonus = self.v0260_title_bonus_text()
            if bonus:
                await self.send(f"Aktywny bonus tytułu: {bonus}.")
            else:
                await self.send("Aktywny tytuł nie daje bonusu mechanicznego.")
