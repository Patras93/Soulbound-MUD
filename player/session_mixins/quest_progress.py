# -*- coding: utf-8 -*-
"""Quest progress calculation and progress announcements."""
# v0.45.0: explicit imports; no compatibility-runtime injection.
from network.protocol_gameplay_utils import V0929_RIVER_FISH_STORAGE_IDS
from player.session_mixins.character_profile import SOUL_TRIAL_QUEST_IDS
from player.session_mixins.crafting import CRAFT_MATERIAL_STORAGE_IDS
from player.session_mixins.exp_terrain import QUESTS
from player.session_mixins.gathering_actions import base_fish_species_id
from player.session_mixins.museum_bounty import canonical_profession_resource_id
from player.session_mixins.profession_storage import ORE_STORAGE_IDS
from player.session_mixins.shops_teachers import FISH_STORAGE_IDS, HERB_STORAGE_IDS, ITEMS, WOOD_STORAGE_IDS
from systems.crafting_quality import parse_crafting_quality_variant_v0332


class SessionQuestProgressMixin:

    def quest_collect_category_info(self, target):
            mapping = {
                "fish": (FISH_STORAGE_IDS, "net", "ryb"),
                "fish_river": (V0929_RIVER_FISH_STORAGE_IDS, "net", "ryb rzecznych"),
                "ore": (ORE_STORAGE_IDS, "bag", "rud"),
                "wood": (WOOD_STORAGE_IDS, "woodpile", "sztuk drewna"),
                "herb": (HERB_STORAGE_IDS, "herbbag", "ziół"),
            }
            return mapping.get(target)

    def resource_quest_container(self, item_id):
            if item_id in FISH_STORAGE_IDS:
                return "net"
            if item_id in ORE_STORAGE_IDS:
                return "bag"
            if item_id in WOOD_STORAGE_IDS:
                return "woodpile"
            if item_id in HERB_STORAGE_IDS:
                return "herbbag"
            return None

    def resource_quest_equivalent_ids(self, item_id):
            """Bazowy surowiec + jego jakościowe warianty dla konkretnego questa."""
            base_id = canonical_profession_resource_id(item_id)
            return {
                candidate_id
                for candidate_id in ITEMS
                if canonical_profession_resource_id(candidate_id) == base_id
            } or {item_id}

    def resource_quest_have(self, item_id):
            container = self.resource_quest_container(item_id)
            equivalent_ids = self.resource_quest_equivalent_ids(item_id)
            if not container:
                return sum(
                    self.server.db.item_qty(self.account_id, candidate_id)
                    for candidate_id in equivalent_ids
                )
            return (
                self.server.db.total_items_across_storage_and_inventory(
                    self.account_id,
                    equivalent_ids,
                    container,
                )
            )

    async def announce_resource_quest_progress(
            self, item_id, amount=1
        ):
            changed = self.server.db.increment_resource_quest(
                self.account_id,
                item_id,
                amount,
            )
            for quest_id, progress, needed in changed:
                quest = QUESTS[quest_id]
                target_id = canonical_profession_resource_id(quest["target"])
                target_name = ITEMS.get(target_id, ITEMS[item_id])["name"]
                if progress >= needed:
                    await self.send(
                        f"Postęp questa: {quest['name']}. "
                        f"Postęp {progress} z {needed}: {target_name}. "
                        "Cel wykonany."
                    )
                else:
                    await self.send(
                        f"Postęp questa: {quest['name']}. "
                        f"Postęp {progress} z {needed}: {target_name}."
                    )

            multi_changed = self.server.db.increment_resource_set_quest_v0929(
                self.account_id, item_id, amount
            )
            for quest_id, total, needed, target_id, target_progress, target_needed in multi_changed:
                quest = QUESTS[quest_id]
                target_name = ITEMS.get(target_id, {"name": target_id})["name"]
                await self.send(
                    f"Postęp questa: {quest['name']}. {target_name}: "
                    f"{target_progress} z {target_needed}. Łącznie {total} z {needed}."
                )
                if total >= needed:
                    await self.send("Wszystkie próbki zostały zebrane. Wróć do NPC.")

    def craft_set_progress(self, row, quest):
            targets = tuple(quest.get("targets") or ())
            mask = int(row["progress"])
            return sum(
                1
                for index in range(len(targets))
                if mask & (1 << index)
            )

    def quest_progress_value(self, quest_id):
            q = QUESTS.get(quest_id)
            if not q:
                return None

            row = self.server.db.quest(self.account_id, quest_id)
            if not row or row["status"] != "active":
                return None

            if q["kind"] == "kill":
                return min(int(row["progress"]), int(q["needed"]))

            if q["kind"] in ("collect", "collect_category", "collect_distinct_category", "collect_resource", "collect_resource_set"):
                # v0.30.7: wszystkie komunikaty/UI korzystają z tego samego
                # realnego postępu do oddania. Historyczny licznik zdarzeń nadal
                # istnieje w SQLite, ale sam nie udaje już zasobów, których gracz
                # fizycznie nie ma.
                progress, _ready = self.quest_progress_for_turnin(quest_id)
                return int(progress)

            if q["kind"] == "craft_set":
                return self.craft_set_progress(row, q)

            if q["kind"] == "profession_action":
                return min(int(row["progress"]), int(q.get("needed", 1)))

            if q["kind"] in ("deliver_npc", "talk_npc", "talk_class_teacher"):
                return min(int(row["progress"]), int(q.get("needed", 1)))

            if q["kind"] in (
                "explore_frontier", "discover_secret", "mini_dungeon",
                "world_event", "legendary_rare", "world_boss",
            ):
                return min(int(row["progress"]), int(q.get("needed", 1)))

            return None

    async def announce_active_quest_progress(self, quest_id, event_label=None):
            q = QUESTS.get(quest_id)
            if not q:
                return

            # v0.58.4: quest progress is gameplay-essential. During active combat
            # Session.send() otherwise auto-classifies ordinary text as normal
            # combat detail, which can be hidden by concise combat log mode.
            async def _send_progress(message):
                await self.send(
                    message,
                    combat_detail="essential",
                    history_category="quest",
                )

            progress = self.quest_progress_value(quest_id)
            if progress is None:
                return

            needed = int(q["needed"])

            if q.get("kind") == "collect":
                # v0.34.4: collect pokazuje ten sam fizyczny stan, z którego
                # korzysta oddawanie questa: inventory + właściwy magazyn
                # profesji (np. Szkatułka Rzemieślnicza dla sztabek/płyt).
                have = self.quest_crafted_item_have_v0333(q["target"])
                item_name = ITEMS[q["target"]]["name"]
                if progress >= needed and have >= needed:
                    await _send_progress(
                        f"Quest aktywny: {q['name']}. "
                        f"Wykonano {progress} z {needed}: "
                        f"{item_name}. Masz {have} sztuk. "
                        "Dziennik zaktualizowany. GOTOWE DO ODDANIA."
                    )
                elif progress >= needed:
                    await _send_progress(
                        f"Quest aktywny: {q['name']}. "
                        f"Wykonano {progress} z {needed}: "
                        f"{item_name}. "
                        f"Do oddania masz {have} z {needed}. "
                        "Wykonanie jest zakończone, ale musisz "
                        "posiadać wymagane przedmioty do oddania."
                    )
                else:
                    await _send_progress(
                        f"Quest aktywny: {q['name']}. "
                        f"Wykonano {progress} z {needed}: "
                        f"{item_name}."
                    )
                return

            if q.get("kind") == "collect_distinct_category":
                species = self.server.db.distinct_category_items_v023(
                    self.account_id, quest_id
                )
                names = [ITEMS.get(i, {"name": i})["name"] for i in species]
                if progress >= needed:
                    await _send_progress(
                        f"Quest aktywny: {q['name']}. Różne gatunki {progress} z {needed}: "
                        + ", ".join(names)
                        + ". Cel wykonany; zachowaj po jednej sztuce zaliczonych gatunków do oddania."
                    )
                else:
                    await _send_progress(
                        f"Quest aktywny: {q['name']}. Różne gatunki {progress} z {needed}."
                        + ((" Zaliczono: " + ", ".join(names) + ".") if names else "")
                    )
                return

            if q.get("kind") == "collect_resource":
                have = self.resource_quest_have(q["target"])
                name = ITEMS[q["target"]]["name"]
                if progress >= needed and have >= needed:
                    await _send_progress(
                        f"Quest aktywny: {q['name']}. "
                        f"Zdobyto {progress} z {needed}: {name}. "
                        f"Masz {have}. Quest gotowy do oddania."
                    )
                elif progress >= needed:
                    await _send_progress(
                        f"Quest aktywny: {q['name']}. "
                        f"Zdobyto {progress} z {needed}: {name}. "
                        f"Do oddania masz {have} z {needed}."
                    )
                else:
                    await _send_progress(
                        f"Quest aktywny: {q['name']}. "
                        f"Zdobyto {progress} z {needed}: {name}."
                    )
                return

            if q.get("kind") == "collect_resource_set":
                requirements = dict(q.get("resource_targets") or {})
                counts = self.server.db.resource_set_progress_v0929(
                    self.account_id, quest_id, requirements
                )
                details = []
                ready = True
                for target_id, target_needed in requirements.items():
                    got = min(int(target_needed), int(counts.get(target_id, 0)))
                    have = self.resource_quest_have(target_id)
                    details.append(
                        f"{ITEMS[target_id]['name']} {got}/{int(target_needed)}; masz {have}"
                    )
                    if got < int(target_needed) or have < int(target_needed):
                        ready = False
                await _send_progress(
                    f"Quest aktywny: {q['name']}. " + "; ".join(details) + (
                        ". Dziennik zaktualizowany. GOTOWE DO ODDANIA." if ready else "."
                    )
                )
                return

            if q.get("kind") == "craft_set":
                targets = tuple(q.get("targets") or ())
                # v0.34.4: przyszłościowo licz także elementy zestawu, które
                # trafią do magazynu profesji lub występują jako wariant jakości.
                have = sum(
                    1
                    for item_id in targets
                    if self.quest_crafted_item_have_v0333(item_id) > 0
                )
                if progress >= needed and have >= needed:
                    await _send_progress(
                        f"Quest aktywny: {q['name']}. "
                        f"Elementy zestawu wykonane {progress} z {needed}. "
                        "Dziennik zaktualizowany. Pełny zestaw GOTOWY DO ODDANIA."
                    )
                else:
                    await _send_progress(
                        f"Quest aktywny: {q['name']}. "
                        f"Elementy zestawu wykonane {progress} z {needed}. "
                        f"Posiadasz {have} z {needed}."
                    )
                return

            if q.get("kind") == "kill":
                label = str(event_label or q.get("progress_label") or "").strip()
                credited = f"Zaliczono: {label}. " if label else "Zabicie zaliczone. "
                if progress >= needed:
                    await _send_progress(
                        f"Postęp questa: {q['name']}. "
                        f"{credited}Postęp {progress} z {needed}. "
                        f"GOTOWE DO ODDANIA. NPC: {q.get('giver', 'NPC')}."
                    )
                else:
                    await _send_progress(
                        f"Postęp questa: {q['name']}. "
                        f"{credited}Postęp {progress} z {needed}."
                    )
                return

            if progress >= needed:
                await _send_progress(
                    f"Quest aktywny: {q['name']}. "
                    f"Postęp {progress} z {needed}. "
                    "Dziennik zaktualizowany. GOTOWE DO ODDANIA — wróć do NPC."
                )
            else:
                await _send_progress(
                    f"Quest aktywny: {q['name']}. "
                    f"Postęp {progress} z {needed}."
                )

    async def announce_collect_category_quest_progress(self, target, amount=1):
            amount = max(0, int(amount))
            if amount <= 0:
                return
            for row in self.server.db.quest_rows(self.account_id):
                if row["status"] != "active":
                    continue
                q = QUESTS.get(row["quest_id"])
                if (
                    not q
                    or q.get("kind") != "collect_category"
                    or q.get("target") != target
                ):
                    continue
                needed = int(q.get("needed", 1))
                old_progress = int(row["progress"])
                new_progress = min(needed, old_progress + amount)
                # v0.30.7: po pierwszym dojściu do celu dalsze zbiory nie
                # powtarzają "quest gotowy do oddania".
                if new_progress == old_progress:
                    continue
                self.server.db.set_quest_progress(
                    self.account_id, row["quest_id"], new_progress
                )
                await self.announce_active_quest_progress(row["quest_id"])

    async def announce_distinct_category_quest_progress(self, target, item_id):
            if target == "fish":
                distinct_id = base_fish_species_id(item_id)
            else:
                distinct_id = canonical_profession_resource_id(item_id)
            for row in self.server.db.quest_rows(self.account_id):
                if row["status"] != "active":
                    continue
                q = QUESTS.get(row["quest_id"])
                if (
                    not q
                    or q.get("kind") != "collect_distinct_category"
                    or q.get("target") != target
                ):
                    continue
                _progress, added = self.server.db.mark_distinct_category_item_v023(
                    self.account_id, row["quest_id"], distinct_id, q.get("needed", 1)
                )
                if added:
                    await self.announce_active_quest_progress(row["quest_id"])

    async def announce_craft_quest_progress(
            self, item_id, amount=1
        ):
            changed = self.server.db.increment_craft_quest(
                self.account_id,
                item_id,
                amount,
            )

            for quest_id, progress, needed in changed:
                quest = QUESTS[quest_id]
                item_name = ITEMS[item_id]["name"]

                if quest.get("kind") == "craft_set":
                    if progress >= needed:
                        await self.send(
                            f"Postęp questa: {quest['name']}. "
                            f"Wykonałeś element: {item_name}. "
                            f"Elementy zestawu {progress} z {needed}. "
                            "Pełny zestaw wykonany 1 z 1."
                        )
                    else:
                        await self.send(
                            f"Postęp questa: {quest['name']}. "
                            f"Wykonałeś element: {item_name}. "
                            f"Elementy zestawu {progress} z {needed}."
                        )
                    continue

                if progress >= needed:
                    await self.send(
                        f"Postęp questa: {quest['name']}. "
                        f"Wykonałeś: {item_name}. "
                        f"Postęp {progress} z {needed}. "
                        "Wymagana liczba została wykonana. "
                        f"Zachowaj {needed} sztuk do oddania "
                        f"{quest['giver']}."
                    )
                else:
                    await self.send(
                        f"Postęp questa: {quest['name']}. "
                        f"Wykonałeś: {item_name}. "
                        f"Postęp {progress} z {needed}."
                    )

            # v0.60.0: rotujące zamówienia NPC liczą te same realne craft events.
            await self.announce_crafting_order_progress_v0600(item_id, amount)

    def format_duration_short(self, seconds):
            seconds = max(0, int(seconds))
            minutes, sec = divmod(seconds, 60)
            if minutes and sec:
                return f"{minutes} min {sec} sek"
            if minutes:
                return f"{minutes} min"
            return f"{sec} sek"

    def soul_tier_quest_for_current_state(self):
            next_tier = self.character.can_unlock()
            if not next_tier:
                return None
            return SOUL_TRIAL_QUEST_IDS.get(next_tier)

    def soul_tier_quest_completed(self, tier):
            quest_id = SOUL_TRIAL_QUEST_IDS.get(int(tier))
            if not quest_id:
                return True
            row = self.server.db.quest(self.account_id, quest_id)
            return bool(row and row["status"] == "completed")

    def quest_turnin_stock_status(self, quest_id):
            """Return (have, needed, label) for quests that consume a physical shared stock."""
            q = QUESTS.get(quest_id)
            if not q:
                return None
            needed = int(q.get("needed", 0))
            kind = q.get("kind")
            if kind == "collect":
                row = self.server.db.quest(self.account_id, quest_id)
                gathered = min(int(row["progress"] if row else 0), needed)
                have = min(gathered, int(self.quest_crafted_item_have_v0333(q["target"])))
                return (have, needed, ITEMS[q["target"]]["name"])
            if kind == "collect_category":
                category = self.quest_collect_category_info(q.get("target"))
                if not category:
                    return None
                ids, container, label = category
                row = self.server.db.quest(self.account_id, quest_id)
                gathered = min(int(row["progress"] if row else 0), needed)
                physical = self.server.db.total_items_across_storage_and_inventory(
                    self.account_id, ids, container
                )
                return (min(gathered, int(physical)), needed, label)
            if kind == "collect_resource":
                row = self.server.db.quest(self.account_id, quest_id)
                gathered = min(int(row["progress"] if row else 0), needed)
                have = min(gathered, int(self.resource_quest_have(q["target"])))
                return (have, needed, ITEMS[q["target"]]["name"])
            if kind == "collect_distinct_category":
                distinct_ids = self.server.db.distinct_category_items_v023(self.account_id, quest_id)[:needed]
                have = sum(1 for item_id in distinct_ids if self.resource_quest_have(item_id) >= 1)
                return (min(have, needed), needed, "różnych zaliczonych gatunków")
            if kind == "collect_resource_set":
                requirements = dict(q.get("resource_targets") or {})
                counts = self.server.db.resource_set_progress_v0929(self.account_id, quest_id, requirements)
                stock_needed = sum(int(value) for value in requirements.values())
                have = sum(
                    min(int(value), int(counts.get(item_id, 0)), int(self.resource_quest_have(item_id)))
                    for item_id, value in requirements.items()
                )
                return (min(have, stock_needed), stock_needed, "wymaganych próbek surowców")
            if kind == "craft_set":
                targets = tuple(q.get("targets") or ())
                have = sum(1 for item_id in targets if self.quest_crafted_item_have_v0333(item_id) > 0)
                return (have, len(targets), "elementów zestawu")
            return None

    def quest_crafted_equivalent_ids_v0333(self, base_id):
            """Return base item plus all Crafting Quality variants representing it."""
            ids = {str(base_id)}
            for item_id, item in ITEMS.items():
                if str(item.get("crafted_base_id_v03054") or "") == str(base_id):
                    ids.add(str(item_id))
            # Defensive fallback for legacy/persisted variants not yet registered in ITEMS.
            try:
                for row in self.server.db.inventory(self.account_id):
                    item_id = str(row["item_id"])
                    parsed = parse_crafting_quality_variant_v0332(item_id)
                    if parsed and parsed.get("base_id") == str(base_id):
                        ids.add(item_id)
            except Exception:
                pass
            return tuple(sorted(ids))

    def quest_collect_storage_container_v03310(self, base_id):
            """Return the profession storage used by a physical collect target, if any."""
            ids = set(self.quest_crafted_equivalent_ids_v0333(base_id))
            if any(item_id in CRAFT_MATERIAL_STORAGE_IDS for item_id in ids):
                return "craftbox"
            if any(item_id in FISH_STORAGE_IDS for item_id in ids):
                return "net"
            if any(item_id in ORE_STORAGE_IDS for item_id in ids):
                return "bag"
            if any(item_id in WOOD_STORAGE_IDS for item_id in ids):
                return "woodpile"
            if any(item_id in HERB_STORAGE_IDS for item_id in ids):
                return "herbbag"
            return None

    def quest_crafted_item_have_v0333(self, base_id):
            ids = self.quest_crafted_equivalent_ids_v0333(base_id)
            container = self.quest_collect_storage_container_v03310(base_id)
            return int(self.server.db.total_items_across_storage_and_inventory(
                self.account_id, ids, container
            ))

    def consume_quest_crafted_items_v0333(self, base_id, quantity):
            ids = self.quest_crafted_equivalent_ids_v0333(base_id)
            container = self.quest_collect_storage_container_v03310(base_id)
            return bool(self.server.db.consume_items_across_storage_and_inventory(
                self.account_id, ids, max(0, int(quantity)), container
            ))

    def recover_broken_collect_progress_v03310(self, quest_id):
            """One-way recovery for active collect quests affected by old storage/craft bugs.

            We only raise progress up to physically owned stock and never above needed. This
            repairs currently active Haldor/crafting orders that stayed at 0/x even though
            the required items were produced/looted after acceptance.
            """
            q = QUESTS.get(quest_id)
            row = self.server.db.quest(self.account_id, quest_id)
            if not q or not row or row["status"] != "active" or q.get("kind") != "collect":
                return 0
            needed = max(1, int(q.get("needed", 1)))
            current = max(0, int(row["progress"]))
            physical = min(needed, int(self.quest_crafted_item_have_v0333(q.get("target"))))
            if physical > current and (q.get("track_craft_progress") or q.get("target") in CRAFT_MATERIAL_STORAGE_IDS):
                self.server.db.set_quest_progress(self.account_id, quest_id, physical)
                return physical
            return current

    def quest_progress_for_turnin(self, quest_id):
            q = QUESTS.get(quest_id)
            row = self.server.db.quest(self.account_id, quest_id)
            if not q or not row or row["status"] != "active":
                return 0, False

            needed = int(q.get("needed", 0))
            if q["kind"] == "kill":
                progress = int(row["progress"])
                return progress, progress >= needed

            if q["kind"] == "profession_action":
                progress = min(int(row["progress"]), needed)
                return progress, progress >= needed

            if q["kind"] == "collect":
                # v0.33.11: napraw aktywne questy, które przez stary błąd
                # storage/craft pozostały na 0/x mimo posiadania celu.
                self.recover_broken_collect_progress_v03310(quest_id)
                row = self.server.db.quest(self.account_id, quest_id)
                # v0.30.7: widoczny postęp questa dostawczego oznacza realną
                # liczbę zaliczonych sztuk, które nadal są dostępne do oddania.
                # Historyczny licznik zdarzeń nadal chroni przed starym zapasem.
                gathered = min(int(row["progress"]), needed)
                have = self.quest_crafted_item_have_v0333(q["target"])
                progress = min(gathered, int(have), needed)
                return progress, progress >= needed

            if q["kind"] == "collect_category":
                category = self.quest_collect_category_info(q["target"])
                if not category:
                    return 0, False
                ids, container, _label = category
                gathered = min(int(row["progress"]), needed)
                have = self.server.db.total_items_across_storage_and_inventory(
                    self.account_id, ids, container
                )
                progress = min(gathered, int(have), needed)
                return progress, progress >= needed

            if q["kind"] == "collect_distinct_category":
                distinct_ids = self.server.db.distinct_category_items_v023(
                    self.account_id, quest_id
                )[:needed]
                # Liczymy tylko zaliczone gatunki, które nadal są fizycznie
                # dostępne do oddania. Sam historyczny wpis nie udaje postępu.
                progress = sum(
                    1 for item_id in distinct_ids
                    if self.resource_quest_have(item_id) >= 1
                )
                progress = min(progress, needed)
                return progress, progress >= needed

            if q["kind"] == "collect_resource":
                gathered = min(int(row["progress"]), needed)
                have = self.resource_quest_have(q["target"])
                progress = min(gathered, int(have), needed)
                return progress, progress >= needed

            if q["kind"] == "collect_resource_set":
                requirements = dict(q.get("resource_targets") or {})
                counts = self.server.db.resource_set_progress_v0929(
                    self.account_id, quest_id, requirements
                )
                progress = sum(
                    min(
                        int(needed_each),
                        int(counts.get(target_id, 0)),
                        int(self.resource_quest_have(target_id)),
                    )
                    for target_id, needed_each in requirements.items()
                )
                progress = min(progress, needed)
                return progress, progress >= needed

            if q["kind"] == "craft_set":
                progress = self.craft_set_progress(row, q)
                targets = tuple(q.get("targets") or ())
                have_all = all(
                    self.quest_crafted_item_have_v0333(item_id) > 0
                    for item_id in targets
                )
                return (
                    progress,
                    progress >= needed and have_all,
                )

            return int(row["progress"]), int(row["progress"]) >= needed

    def quest_ids_for_npc(self, npc_id, npc):
            """Zwraca stabilną, numerowaną ofertę questów jednego NPC."""
            result = []

            def add(quest_id):
                if quest_id and quest_id in QUESTS and quest_id not in result:
                    result.append(quest_id)

            add(npc.get("quest"))
            for quest_id in tuple(npc.get("quest_chain") or ()):
                add(quest_id)
            for quest_id in tuple(npc.get("specialist_quests") or ()):
                add(quest_id)

            # Giver jest dodatkowym źródłem. Dzięki temu np. Kapłan Elor
            # pokazuje również wszystkie Próby Broni Duszy.
            giver_name = self.normalize_description_query(npc.get("name", ""))
            for quest_id, quest in QUESTS.items():
                if (
                    giver_name
                    and self.normalize_description_query(quest.get("giver", ""))
                    == giver_name
                ):
                    add(quest_id)

            # v0.8.53: u Elora Próby są zawsze czytane w naturalnej kolejności
            # Tier 2 -> Tier 20, niezależnie od historycznej kolejności definicji
            # quest_id w pliku. Zwykły quest Szczury pod świątynią zostaje pierwszy.
            if npc_id == "priest_elor":
                trial_ids = set(SOUL_TRIAL_QUEST_IDS.values())
                regular = [qid for qid in result if qid not in trial_ids]
                trials = sorted(
                    (qid for qid in result if qid in trial_ids),
                    key=lambda qid: int(QUESTS[qid].get("unlocks_soul_tier", 999)),
                )
                result = regular + trials
            return result
