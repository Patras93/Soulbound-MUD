# -*- coding: utf-8 -*-
"""v109: muzeum, osiągnięcia i zlecenia — collection. Historyczne metody bez zmian."""
from .dependencies import *

class MuseumCollectionV109Mixin:
    async def announce_item_collect_quest_progress(self, item_id, amount=1):
            """v0.8.66: postęp collect rośnie tylko od nowego zdobycza po przyjęciu."""
            changed = self.server.db.increment_item_collect_quest(
                self.account_id, item_id, amount
            )
            # v11.00.9: item quest progress must survive concise combat log.
            # Use the canonical stock-aware quest reporter after SQLite update.
            for quest_id, _progress, _needed in changed:
                await self.announce_active_quest_progress(quest_id)

    async def grant_hourly_quest_kill_drop_v0929(self, mob_template_id, template):
            # v0.30.38: specjalne questy kill->item zwiększają licznik bezpośrednio
            # w miejscu przyznania przedmiotu. Nie polegamy już na pośrednim
            # record_item_collection(), dzięki czemu NVDA zawsze dostaje X/Y.
            for quest_id in (
                "haldor_broken_blades_v0929",
                "haldor_armor_recycling_v0929",
                "orin_toxic_glands_v0929",
            ):
                row = self.server.db.quest(self.account_id, quest_id)
                quest = QUESTS.get(quest_id)
                if not row or row["status"] != "active" or not quest:
                    continue
                if int(row["progress"]) >= int(quest.get("needed", 1)):
                    continue
                item_id = v0929_kill_drop_item(quest_id, mob_template_id, template)
                if not item_id:
                    continue

                self.server.db.add_item(self.account_id, item_id, 1)
                changed = self.server.db.increment_item_collect_quest(
                    self.account_id, item_id, 1
                )
                await self.send(
                    f"Przedmiot questowy: {ITEMS[item_id]['name']} x1 z {template.get('name', mob_template_id)}."
                )
                for changed_quest_id, _progress, _needed in changed:
                    if changed_quest_id == quest_id:
                        await self.announce_active_quest_progress(changed_quest_id)

                # Kolekcja/Museum nadal dostaje przedmiot, ale nie może drugi raz
                # podbić tego samego questa.
                await self.record_item_collection(
                    item_id, source=template.get("name", mob_template_id),
                    announce=True, record_history=False, amount=1,
                    quest_progress=False,
                )

    async def record_item_collection(
            self, item_id, source="", announce=True, record_history=True, amount=1,
            quest_progress=True,
        ):
            item = ITEMS.get(item_id)
            if not item:
                return
            zone = ROOMS.get(self.character.room_id, {}).get("zone", "")
            rank = loot_rarity_rank(item_id)
            if record_history and rank >= 1:
                rarity = str(item.get("rarity_name") or item.get("rarity") or "Rare")
                item_display_name_v03811 = player_item_display_name_v0335(item_id)
                self.server.db.add_drop_history(
                    self.account_id,
                    item_id,
                    item_display_name_v03811,
                    rarity,
                    source,
                    zone,
                )
                if rank >= 3:
                    try:
                        self.server.db.record_server_exceptional_drop_v03811(
                            self.account_id, self.character.name, item_id,
                            item_display_name_v03811, rarity, source, zone,
                        )
                    except Exception as exc:
                        print(f"EXCEPTIONAL_DROP_RECORD_ERROR: {type(exc).__name__}: {exc}", flush=True)

            base_resource_id = canonical_profession_resource_id(item_id)
            collection_candidates = []
            if base_resource_id in FISH_COLLECTION_CATALOG:
                collection_candidates.append(("fish", base_resource_id))
            if base_resource_id in MINERAL_COLLECTION_CATALOG:
                collection_candidates.append(("minerals", base_resource_id))
            if base_resource_id in HERB_COLLECTION_CATALOG:
                collection_candidates.append(("herbs", base_resource_id))
            if base_resource_id in MATERIAL_COLLECTION_CATALOG:
                collection_candidates.append(("materials", base_resource_id))
            if item_id in GEM_COLLECTION_CATALOG:
                collection_candidates.append(("gems", item_id))
            if item_id in UNIQUE_ITEM_COLLECTION_CATALOG:
                collection_candidates.append(("unique", item_id))
            if item_id in EQUIPMENT_COLLECTION_CATALOG:
                collection_candidates.append(("equipment", item_id))
            if base_resource_id in V0260_WOOD_CATALOG:
                collection_candidates.append(("wood_v026", base_resource_id))
            if item_id in V0260_LEGENDARY_ITEM_CATALOG:
                collection_candidates.append(("legendary_v026", item_id))

            museum_changed = False
            for category, entry_id in collection_candidates:
                is_new = self.server.db.add_collection_entry(
                    self.account_id, category, entry_id
                )
                if is_new and category in ("wood_v026", "legendary_v026"):
                    museum_changed = True
                if is_new and announce:
                    if category == "wood_v026":
                        await self.send(f"Nowy wpis Muzeum: Drewno — {V0260_WOOD_CATALOG[entry_id]}.")
                    elif category == "legendary_v026":
                        await self.send(f"Nowy wpis Muzeum: Legendarne przedmioty — {V0260_LEGENDARY_ITEM_CATALOG[entry_id]}.")
                    else:
                        await self.send(
                            f"Nowa kolekcja: {COLLECTION_CATEGORY_LABELS[category]} — "
                            f"{COLLECTION_CATALOGS[category][entry_id]}."
                        )

            if item_id in NAMED_LOOT_CATALOG:
                is_new = self.server.db.add_collection_entry(
                    self.account_id, "named", item_id
                )
                if is_new and announce:
                    await self.send(
                        f"Nowy wpis Codexu: {NAMED_LOOT_CATALOG[item_id]}, Named Loot."
                    )

            set_entry = SET_ENTRY_BY_ITEM.get(item_id)
            if set_entry:
                is_new = self.server.db.add_collection_entry(
                    self.account_id, "sets", set_entry
                )
                if is_new and announce:
                    await self.send(
                        f"Nowy wpis Codexu: {SET_COLLECTION_CATALOG[set_entry]['name']}, Set."
                    )
                museum_changed = museum_changed or bool(is_new)

            if museum_changed and announce:
                await self.v0260_check_museum_rewards(announce=True)

            # v0.8.40: quest item progress is spoken immediately after loot.
            # This deliberately ignores the loot speech filter: quest progress is
            # gameplay-critical information for screen-reader users.
            if announce and quest_progress:
                await self.announce_item_collect_quest_progress(
                    item_id, max(1, int(amount))
                )

    async def sync_collection_from_inventory(self):
            owned = {row["item_id"] for row in self.server.db.inventory(self.account_id)}
            owned.update(row["item_id"] for row in self.server.db.equipment(self.account_id))
            for container in ("net", "bag", "woodpile", "herbbag", "craftbox"):
                owned.update(
                    row["item_id"] for row in self.server.db.storage_rows(self.account_id, container)
                )
            for item_id in owned:
                await self.record_item_collection(
                    item_id, source="posiadany przedmiot",
                    announce=False, record_history=False
                )
            for fish_id in self.server.db.fish_journal_ids(self.account_id):
                if fish_id in FISH_COLLECTION_CATALOG:
                    self.server.db.add_collection_entry(self.account_id, "fish", fish_id)
