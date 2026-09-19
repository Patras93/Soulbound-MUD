# -*- coding: utf-8 -*-
"""Soulbound v0.30.51 Session mixin: quests."""

class SessionQuestsMixin:
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

            if q["kind"] in ("deliver_npc", "talk_npc", "talk_class_teacher"):
                return min(int(row["progress"]), int(q.get("needed", 1)))

            if q["kind"] in (
                "explore_frontier", "discover_secret", "mini_dungeon",
                "world_event", "legendary_rare", "world_boss",
            ):
                return min(int(row["progress"]), int(q.get("needed", 1)))

            return None

    async def announce_active_quest_progress(self, quest_id):
            q = QUESTS.get(quest_id)
            if not q:
                return

            progress = self.quest_progress_value(quest_id)
            if progress is None:
                return

            needed = int(q["needed"])

            if q.get("kind") == "collect":
                have = self.server.db.item_qty(
                    self.account_id,
                    q["target"],
                )
                item_name = ITEMS[q["target"]]["name"]
                if progress >= needed and have >= needed:
                    await self.send(
                        f"Quest aktywny: {q['name']}. "
                        f"Wykonano {progress} z {needed}: "
                        f"{item_name}. Masz {have} sztuk. "
                        "Dziennik zaktualizowany. GOTOWE DO ODDANIA."
                    )
                elif progress >= needed:
                    await self.send(
                        f"Quest aktywny: {q['name']}. "
                        f"Wykonano {progress} z {needed}: "
                        f"{item_name}. "
                        f"Do oddania masz {have} z {needed}. "
                        "Wykonanie jest zakończone, ale musisz "
                        "posiadać wymagane przedmioty do oddania."
                    )
                else:
                    await self.send(
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
                    await self.send(
                        f"Quest aktywny: {q['name']}. Różne gatunki {progress} z {needed}: "
                        + ", ".join(names)
                        + ". Cel wykonany; zachowaj po jednej sztuce zaliczonych gatunków do oddania."
                    )
                else:
                    await self.send(
                        f"Quest aktywny: {q['name']}. Różne gatunki {progress} z {needed}."
                        + ((" Zaliczono: " + ", ".join(names) + ".") if names else "")
                    )
                return

            if q.get("kind") == "collect_resource":
                have = self.resource_quest_have(q["target"])
                name = ITEMS[q["target"]]["name"]
                if progress >= needed and have >= needed:
                    await self.send(
                        f"Quest aktywny: {q['name']}. "
                        f"Zdobyto {progress} z {needed}: {name}. "
                        f"Masz {have}. Quest gotowy do oddania."
                    )
                elif progress >= needed:
                    await self.send(
                        f"Quest aktywny: {q['name']}. "
                        f"Zdobyto {progress} z {needed}: {name}. "
                        f"Do oddania masz {have} z {needed}."
                    )
                else:
                    await self.send(
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
                await self.send(
                    f"Quest aktywny: {q['name']}. " + "; ".join(details) + (
                        ". Dziennik zaktualizowany. GOTOWE DO ODDANIA." if ready else "."
                    )
                )
                return

            if q.get("kind") == "craft_set":
                targets = tuple(q.get("targets") or ())
                have = sum(
                    1
                    for item_id in targets
                    if self.server.db.item_qty(
                        self.account_id, item_id
                    ) > 0
                )
                if progress >= needed and have >= needed:
                    await self.send(
                        f"Quest aktywny: {q['name']}. "
                        f"Elementy zestawu wykonane {progress} z {needed}. "
                        "Dziennik zaktualizowany. Pełny zestaw GOTOWY DO ODDANIA."
                    )
                else:
                    await self.send(
                        f"Quest aktywny: {q['name']}. "
                        f"Elementy zestawu wykonane {progress} z {needed}. "
                        f"Posiadasz {have} z {needed}."
                    )
                return

            if progress >= needed:
                await self.send(
                    f"Quest aktywny: {q['name']}. "
                    f"Postęp {progress} z {needed}. "
                    "Dziennik zaktualizowany. GOTOWE DO ODDANIA — wróć do NPC."
                )
            else:
                await self.send(
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

    def quest_crafted_item_have_v0333(self, base_id):
            return sum(
                int(self.server.db.item_qty(self.account_id, item_id))
                for item_id in self.quest_crafted_equivalent_ids_v0333(base_id)
            )

    def consume_quest_crafted_items_v0333(self, base_id, quantity):
            remaining = max(0, int(quantity))
            for item_id in self.quest_crafted_equivalent_ids_v0333(base_id):
                if remaining <= 0:
                    break
                have = int(self.server.db.item_qty(self.account_id, item_id))
                take = min(have, remaining)
                if take > 0:
                    if not self.server.db.remove_item(self.account_id, item_id, take):
                        return False
                    remaining -= take
            return remaining == 0

    def quest_progress_for_turnin(self, quest_id):
            q = QUESTS.get(quest_id)
            row = self.server.db.quest(self.account_id, quest_id)
            if not q or not row or row["status"] != "active":
                return 0, False

            needed = int(q.get("needed", 0))
            if q["kind"] == "kill":
                progress = int(row["progress"])
                return progress, progress >= needed

            if q["kind"] == "collect":
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

    def hourly_quest_ids(self, at_time=None):
            """Pełna lista godzinnych zleceń; bez rotacji."""
            return [qid for qid in HOURLY_QUEST_IDS if qid in QUESTS]

    async def show_hourly_quests(self):
            quest_ids = self.hourly_quest_ids()
            self.quest_list_context = {"source": "hourly", "quest_ids": quest_ids}
            if not quest_ids:
                await self.send("Brak godzinnych zleceń.")
                return
            await self.send(
                f"GODZINNE ZLECENIA: {len(quest_ids)}. Wszystkie są zawsze dostępne; "
                "każde odnawia się niezależnie po 60 minutach od ukończenia."
            )
            for number, quest_id in enumerate(quest_ids, 1):
                quest = QUESTS[quest_id]
                await self.send(
                    f"{number}. {quest['name']}. {self.quest_offer_state(quest_id)}. "
                    f"Cel: {quest['description']}"
                )
            await self.send(
                "Przyjmowanie: quest accept <numer>. Możesz przyjąć wszystkie dostępne godzinne zlecenia. "
                "Gotowe zlecenie oddajesz komendą oddaj quest <numer> z listy aktywnych."
            )

    def quest_lock_reasons(self, quest_id):
            """Powody, dla których quest nie może jeszcze zostać przyjęty."""
            quest = QUESTS.get(quest_id)
            if not quest:
                return ["brak definicji zadania"]

            reasons = []

            # v0.30.10: questy nie mają globalnej blokady Levelu postaci.
            # Zachowujemy wyłącznie wymagania wynikające z treści zadania: poprzedni
            # quest, Soul Level/Tier oraz specjalistyczną profesję/narzędzie.
            required_quest = quest.get("requires_quest")
            if required_quest and not self.quest_completed(required_quest):
                previous = QUESTS.get(required_quest, {})
                reasons.append(
                    "wymaga ukończenia: "
                    + previous.get("name", required_quest)
                )

            required_soul_level = int(quest.get("required_soul_level", 0) or 0)
            if required_soul_level and self.character.soul_level < required_soul_level:
                reasons.append(f"wymaga Soul Level {required_soul_level}")

            required_soul_tier = int(quest.get("required_soul_tier", 0) or 0)
            if required_soul_tier and self.character.soul_tier < required_soul_tier:
                reasons.append(f"wymaga Soul Tier {required_soul_tier}")

            tool_type = quest.get("specialist_tool_type")
            profession = quest.get("required_profession") or quest.get("reward_profession") or profession_for_tool_type(tool_type)
            min_prof = int(quest.get("min_profession_level", quest.get("min_tool_level", 0)) or 0)
            if profession and min_prof:
                prow = self.server.db.profession(self.account_id, profession)
                if int(prow["level"]) < min_prof:
                    reasons.append(f"wymaga {profession} level {min_prof}")

            return reasons

    def quest_offer_state(self, quest_id):
            quest = QUESTS[quest_id]
            row = self.server.db.quest(self.account_id, quest_id)
            if row and row["status"] == "active":
                progress, ready = self.quest_progress_for_turnin(quest_id)
                if ready:
                    return f"aktywne, ZAKTUALIZOWANO — GOTOWE DO ODDANIA, {progress} z {quest['needed']}"
                return f"aktywne, {progress} z {quest['needed']}"

            if row and row["status"] == "abandoned":
                reasons = self.quest_lock_reasons(quest_id)
                if reasons:
                    return "porzucone, zablokowane: " + ", ".join(reasons)
                return "porzucone, dostępne ponownie"

            if row and row["status"] == "completed":
                if quest.get("repeatable"):
                    cooldown = int(
                        quest.get("repeat_cooldown", QUEST_REPEAT_COOLDOWN_SECONDS)
                    )
                    remaining = self.server.db.repeat_quest_seconds_remaining(
                        self.account_id, quest_id, cooldown
                    )
                    if remaining > 0:
                        return (
                            "ukończone, odnowienie za "
                            + self.format_duration_short(remaining)
                        )
                    return "dostępne ponownie"
                return "ukończone"

            reasons = self.quest_lock_reasons(quest_id)
            if reasons:
                return "zablokowane: " + ", ".join(reasons)
            return "dostępne"

    def local_quest_npcs(self):
            result = {}
            for npc_id, npc in NPCS.items():
                if npc.get("room") != self.character.room_id:
                    continue
                if self.quest_ids_for_npc(npc_id, npc):
                    result[npc_id] = npc
            return result

    async def show_npc_quest_offers(self, npc_id, npc, remember=True):
            quest_ids = self.quest_ids_for_npc(npc_id, npc)
            if not quest_ids:
                await self.send(f"{npc['name']} nie ma teraz żadnych questów.")
                return []

            if remember:
                self.quest_list_context = {
                    "source": "npc",
                    "room_id": self.character.room_id,
                    "npc_id": npc_id,
                    "quest_ids": list(quest_ids),
                }

            await self.send(f"QUEST LIST: {npc['name']}. {len(quest_ids)} zadań.")
            for number, quest_id in enumerate(quest_ids, 1):
                quest = QUESTS[quest_id]
                state = self.quest_offer_state(quest_id)
                reward_coins = v0190_quest_currency_reward(quest)
                await self.send(
                    f"{number}. {quest['name']}. {state}. "
                    f"Nagroda: {currency_reading_text(reward_coins, 0, 0)}."
                )
            await self.send(
                "Przyjmowanie: quest accept <numer> albo quest przyjmij <numer>. "
                "Szczegóły: quest info <numer>."
            )
            return quest_ids

    async def show_quest_npc_list(self, npc_query=""):
            candidates = self.local_quest_npcs()
            if not candidates:
                await self.send("W tej lokacji żaden NPC nie oferuje questów.")
                self.quest_list_context = None
                return

            query = str(npc_query or "").strip()
            normalized = self.normalize_description_query(query)
            for prefix in ("u ", "od ", "npc "):
                if normalized.startswith(prefix):
                    query = query.split(None, 1)[1].strip() if " " in query else ""
                    break

            if query:
                found = find_by_name(candidates, query)
                if not found:
                    await self.send(
                        "Nie rozpoznaję tutaj tego NPC z questami. Dostępni: "
                        + ", ".join(npc["name"] for npc in candidates.values())
                        + "."
                    )
                    return
                npc_id, npc = found
                await self.show_npc_quest_offers(npc_id, npc)
                return

            if len(candidates) == 1:
                npc_id, npc = next(iter(candidates.items()))
                await self.show_npc_quest_offers(npc_id, npc)
                return

            await self.send("NPC z questami w tej lokacji:")
            for number, npc in enumerate(candidates.values(), 1):
                await self.send(f"{number}. {npc['name']}.")
            await self.send("Wpisz quest list <NPC>, np. quest list Orin.")
            self.quest_list_context = None

    def quest_from_context(self, raw_number):
            value = str(raw_number or "").strip()
            if not value.isdigit():
                return None, "Podaj numer questa z ostatniej listy NPC."
            context = self.quest_list_context
            if not context:
                return None, (
                    "Najpierw wyświetl listę: quest, quest ukończone albo quest list <NPC>."
                )
            if (
                context.get("source") == "npc"
                and context.get("room_id") != self.character.room_id
            ):
                return None, "Lista NPC jest nieaktualna. Ponownie wpisz quest list <NPC>."
            quest_ids = list(context.get("quest_ids") or ())
            index = int(value) - 1
            if index < 0 or index >= len(quest_ids):
                return None, f"Nie ma questa numer {value} na ostatniej liście."
            return quest_ids[index], None

    def quest_accept_npc_name_v099(self, quest_id, preferred_npc_id=None):
            """Nazwa NPC, który faktycznie oferuje quest w bieżącym kontekście."""
            if preferred_npc_id in NPCS:
                npc = NPCS[preferred_npc_id]
                if (
                    npc.get("room") == self.character.room_id
                    and quest_id in self.quest_ids_for_npc(preferred_npc_id, npc)
                ):
                    return npc.get("name", QUESTS.get(quest_id, {}).get("giver", "NPC"))

            quest = QUESTS.get(quest_id, {})
            giver_norm = self.normalize_description_query(quest.get("giver", ""))
            # Najpierw NPC w bieżącej lokacji, potem globalny fallback po nazwie givera.
            ordered = list(NPCS.items())
            ordered.sort(key=lambda pair: pair[1].get("room") != self.character.room_id)
            for npc_id, npc in ordered:
                if quest_id not in self.quest_ids_for_npc(npc_id, npc):
                    continue
                if giver_norm:
                    npc_norm = self.normalize_description_query(npc.get("name", ""))
                    if npc_norm == giver_norm:
                        return npc.get("name", quest.get("giver", "NPC"))
                if npc.get("room") == self.character.room_id:
                    return npc.get("name", quest.get("giver", "NPC"))
            return str(quest.get("giver") or "NPC")

    def quest_accept_reaction_v099(self, quest, npc_name, repeated=False):
            """Krótka kwestia NPC wypowiadana przed zapisaniem przyjęcia questa."""
            prefix = "Witaj znowu. " if repeated else "Dobrze, że przyszedłeś. "
            name_cf = str(npc_name).casefold()
            profession = normalize_profession_name(
                quest.get("reward_profession")
                or quest.get("required_profession")
                or profession_for_tool_type(quest.get("reward_tool_type"))
                or profession_for_tool_type(quest.get("specialist_tool_type"))
                or ""
            )

            if quest.get("target") == "salvaged_steel_plate":
                return (
                    "Dobrze. Cztery stalowe płyty idą prosto do pieca; "
                    "przetopię je na stal potrzebną kuźni."
                )

            if profession == "Wędkarstwo" or "borys" in name_cf or "mistrz wędkarstwa" in name_cf:
                core = "Mam dla ciebie zadanie związane z wodą i połowem. Pokaż, że potrafisz czytać łowisko, a nie tylko zarzucać wędkę."
            elif profession == "Górnictwo" or any(x in name_cf for x in ("górnik", "gornik", "kordan", "dagna")):
                core = "Mam dla ciebie robotę w skale. Liczy się pewna ręka, dobry urobek i żadnego marnowania żyły."
            elif profession == "Drwalstwo" or any(x in name_cf for x in ("drwal", "bran", "oren")):
                core = "Mam dla ciebie pracę w lesie. Tnij dokładnie i przynieś materiał w dobrym stanie."
            elif profession == "Zielarstwo" or any(x in name_cf for x in ("zielar", "sena", "liora", "ira")):
                core = "Mam dla ciebie zadanie zielarskie. Zbieraj uważnie, żeby nie zniszczyć tego, po co idziesz."
            elif profession == "Gotowanie" or "marcel" in name_cf:
                core = "Mam dla ciebie zamówienie z kuchni. Liczy się wykonanie, nie pośpiech."
            elif profession == "Alchemia" or "orin" in name_cf:
                core = "Mam dla ciebie zadanie alchemiczne. Pilnuj proporcji i wykonaj je dokładnie."
            elif profession == "Kowalstwo" or any(x in name_cf for x in ("kowal", "haldor", "brok")):
                core = "Mam dla ciebie zlecenie rzemieślnicze. Materiał ma być dobrze wykorzystany, a wykonanie równe."
            elif profession == "Jubilerstwo" or "mirella" in name_cf:
                core = "Mam dla ciebie precyzyjne zlecenie jubilerskie. Tu każdy detal ma znaczenie."
            else:
                kind = quest.get("kind")
                if kind == "kill":
                    core = "Mam dla ciebie zadanie w terenie. Trzeba usunąć zagrożenie, zanim urośnie jeszcze bardziej."
                elif kind in ("collect", "collect_resource", "collect_category", "collect_distinct_category"):
                    core = "Potrzebuję konkretnych materiałów. Zdobądź je po przyjęciu tego zadania i przynieś mi pełną wymaganą ilość."
                elif kind == "craft_set":
                    core = "Potrzebuję kompletnego wykonania. Przygotuj cały wymagany zestaw i wróć z nim do mnie."
                elif kind == "deliver_npc":
                    core = "Mam przesyłkę, która musi dotrzeć do właściwej osoby. Dopilnuj jej osobiście."
                elif kind in ("talk_npc", "talk_class_teacher"):
                    core = "To zadanie wymaga rozmowy z właściwą osobą. Idź tam, wysłuchaj jej i wróć z wykonanym etapem."
                else:
                    core = "Mam dla ciebie zadanie. Wykonaj je zgodnie z opisem i wróć do mnie po zakończeniu."
            if repeated:
                if core.startswith("Mam dla ciebie "):
                    core = core[len("Mam dla ciebie "):]
                if core:
                    core = core[0].upper() + core[1:]
                return "Witaj znowu. Mam dla ciebie kolejne zlecenie. " + core
            return prefix + core

    def quest_is_available_to_accept_v099(self, quest_id):
            quest = QUESTS.get(quest_id)
            if not quest:
                return False
            row = self.server.db.quest(self.account_id, quest_id)
            if row and row["status"] == "active":
                return False
            if self.quest_lock_reasons(quest_id):
                return False
            if row and row["status"] == "completed":
                if not quest.get("repeatable"):
                    return False
                cooldown = int(quest.get("repeat_cooldown", QUEST_REPEAT_COOLDOWN_SECONDS))
                return self.server.db.repeat_quest_seconds_remaining(
                    self.account_id, quest_id, cooldown
                ) <= 0
            return True

    async def announce_npc_quest_context_v099(self, npc_id, npc):
            """NPC mówi o nowych zadaniach i rozpoznaje powrót do właściwego odbiorcy."""
            offer_ids = self.quest_ids_for_npc(npc_id, npc)
            quest_ids = list(offer_ids)

            # Dostawy i rozmowy mogą być oddawane u innego NPC niż pierwotny giver.
            # Nie dodajemy ich do oferty tego NPC, ale pozwalamy mu rozpoznać powrót.
            npc_name_norm = self.normalize_description_query(npc.get("name", ""))
            for row in self.server.db.quest_rows(self.account_id):
                quest_id = row["quest_id"]
                if row["status"] != "active" or quest_id not in QUESTS:
                    continue
                quest = QUESTS[quest_id]
                turnin_name = self.quest_turnin_npc_name_v098(quest)
                if self.normalize_description_query(turnin_name) == npc_name_norm and quest_id not in quest_ids:
                    quest_ids.append(quest_id)

            if not quest_ids:
                return

            ready = []
            active = []
            available = []
            cooldowns = []
            for quest_id in quest_ids:
                quest = QUESTS[quest_id]
                row = self.server.db.quest(self.account_id, quest_id)
                if row and row["status"] == "active":
                    progress, is_ready = self.quest_progress_for_turnin(quest_id)
                    entry = (quest["name"], progress, int(quest.get("needed", 1)))
                    (ready if is_ready else active).append(entry)
                    continue

                if quest_id in offer_ids and self.quest_is_available_to_accept_v099(quest_id):
                    available.append(quest["name"])
                    continue

                if quest_id in offer_ids and row and row["status"] == "completed" and quest.get("repeatable"):
                    cooldown = int(quest.get("repeat_cooldown", QUEST_REPEAT_COOLDOWN_SECONDS))
                    remaining = self.server.db.repeat_quest_seconds_remaining(
                        self.account_id, quest_id, cooldown
                    )
                    if remaining > 0:
                        cooldowns.append((quest["name"], remaining))

            name = npc.get("name", "NPC")
            if ready:
                if len(ready) == 1:
                    qname, progress, needed = ready[0]
                    await self.send(
                        f"{name}: Witaj ponownie. Widzę, że zadanie {qname} jest gotowe. "
                        f"Postęp {progress} z {needed}. Możesz je teraz oddać."
                    )
                else:
                    await self.send(
                        f"{name}: Witaj ponownie. Masz u mnie {len(ready)} zadań gotowych do oddania. "
                        "Możesz je teraz rozliczyć."
                    )
            elif active:
                if len(active) == 1:
                    qname, progress, needed = active[0]
                    await self.send(
                        f"{name}: Witaj ponownie. Widzę, że nadal pracujesz nad zadaniem {qname}. "
                        f"Postęp {progress} z {needed}. Wróć, gdy skończysz."
                    )
                else:
                    await self.send(
                        f"{name}: Witaj ponownie. Nadal masz u mnie {len(active)} aktywne zadania. "
                        "Sprawdź ich bieżący postęp w dzienniku."
                    )

            if available:
                if len(available) == 1:
                    await self.send(
                        f"{name}: Mam dla ciebie zadanie: {available[0]}. "
                        "Jeśli chcesz, wybierz je z listy zadań."
                    )
                else:
                    await self.send(
                        f"{name}: Mam dla ciebie {len(available)} dostępne zadania. "
                        "Wybierz interesujące cię z listy zadań."
                    )
            elif not ready and not active and cooldowns:
                qname, remaining = min(cooldowns, key=lambda x: x[1])
                await self.send(
                    f"{name}: Dobrze cię znowu widzieć. Na razie nie mam nowego zadania. "
                    f"{qname} będzie dostępne ponownie za {self.format_duration_short(remaining)}."
                )
            elif not ready and not active:
                await self.send(
                    f"{name}: Dobrze cię znowu widzieć. Na razie nie mam dla ciebie nowego zadania."
                )

    async def accept_quest_id(self, quest_id, npc_id=None):
            if self.combat_mob_key:
                await self.send("Nie możesz przyjmować questa podczas walki.")
                return
            quest = QUESTS.get(quest_id)
            if not quest:
                await self.send("Nie znaleziono tego questa.")
                return

            row = self.server.db.quest(self.account_id, quest_id)
            if row and row["status"] == "active":
                progress, ready = self.quest_progress_for_turnin(quest_id)
                suffix = " Cel wykonany." if ready else ""
                await self.send(
                    f"Quest już aktywny: {quest['name']}. "
                    f"Postęp {progress} z {quest['needed']}.{suffix}"
                )
                return

            if row and row["status"] == "completed":
                if not quest.get("repeatable"):
                    await self.send(f"Quest {quest['name']} jest już ukończony.")
                    return
                cooldown = int(
                    quest.get("repeat_cooldown", QUEST_REPEAT_COOLDOWN_SECONDS)
                )
                remaining = self.server.db.repeat_quest_seconds_remaining(
                    self.account_id, quest_id, cooldown
                )
                if remaining > 0:
                    await self.send(
                        f"Quest {quest['name']} odnawia się za "
                        f"{self.format_duration_short(remaining)}."
                    )
                    return

            reasons = self.quest_lock_reasons(quest_id)
            if reasons:
                await self.send(
                    f"Nie możesz jeszcze przyjąć questa {quest['name']}: "
                    + ", ".join(reasons)
                    + "."
                )
                return

            repeated = bool(row and row["status"] in ("completed", "abandoned"))
            accept_npc = self.quest_accept_npc_name_v099(quest_id, npc_id)
            accept_reaction = self.quest_accept_reaction_v099(quest, accept_npc, repeated=repeated)
            await self.send(f"{accept_npc}: {accept_reaction}")

            if repeated:
                self.server.db.restart_quest(self.account_id, quest_id)
                await self.send(f"Quest przyjęty ponownie: {quest['name']}.")
            else:
                self.server.db.start_quest(self.account_id, quest_id)
                await self.send(f"Quest przyjęty: {quest['name']}.")

            # v0.8.43: przedmioty potrzebne do jednorazowych dostaw Sola.
            for item_id, qty in (quest.get("accept_items") or {}).items():
                wanted_qty = max(1, int(qty))
                have_qty = self.server.db.item_qty(self.account_id, item_id)
                if quest.get("accept_items_always"):
                    missing = wanted_qty
                else:
                    missing = max(0, wanted_qty - have_qty)
                if missing:
                    self.server.db.add_item(self.account_id, item_id, missing)
                    await self.send(
                        f"Otrzymujesz przedmiot questowy: {ITEMS[item_id]['name']} x{missing}."
                    )
            if any(ITEMS.get(iid, {}).get("quest_treasure_map_for") == quest_id for iid in (quest.get("accept_items") or {})):
                self.server.db.add_collection_entry(
                    self.account_id, "quest_map_grants_v0243", quest_id
                )

            await self.send(quest["description"])
            await self.announce_active_quest_progress(quest_id)

    async def accept_quest_from_context(self, args):
            text = str(args or "").strip()
            # Wygodny wariant bez kontekstu: quest accept Orin 2.
            match = re.match(r"^(.*?)(\d+)$", text)
            if match and match.group(1).strip():
                npc_query = match.group(1).strip()
                number = match.group(2)
                candidates = self.local_quest_npcs()
                found = find_by_name(candidates, npc_query)
                if not found:
                    await self.send("Nie rozpoznaję tutaj tego NPC z questami.")
                    return
                npc_id, npc = found
                await self.show_npc_quest_offers(npc_id, npc, remember=True)
                quest_id, error = self.quest_from_context(number)
            else:
                quest_id, error = self.quest_from_context(text)

            if error:
                await self.send(error)
                return
            context = self.quest_list_context or {}
            npc_id = context.get("npc_id") if context.get("source") == "npc" else None
            await self.accept_quest_id(quest_id, npc_id=npc_id)

    async def quest_info_from_context(self, number):
            quest_id, error = self.quest_from_context(number)
            if error:
                await self.send(error)
                return
            quest = QUESTS[quest_id]
            row = self.server.db.quest(self.account_id, quest_id)

            await self.send(f"QUEST INFO: {quest['name']}.")
            await self.send(f"NPC: {quest.get('giver', 'brak')}.")
            await self.send(f"Stan: {self.quest_offer_state(quest_id)}.")
            if quest.get("soul_trial_tier"):
                await self.send(f"Trudność Próby Duszy: {quest.get('trial_band', soul_trial_difficulty_band(quest['soul_trial_tier']))}.")
            description = str(quest.get("description", "Brak opisu")).strip()
            await self.send(
                "Opis: " + description.rstrip(".?!") + "."
            )
            if quest.get("kind") == "deliver_npc":
                target = NPCS.get(quest.get("target_npc"), {})
                item_id = quest.get("quest_item")
                item_name = ITEMS.get(item_id, {}).get("name", "przesyłka")
                await self.send(
                    f"Cel: dostarcz {item_name} do NPC: {target.get('name', 'nieznany')}."
                )
            elif quest.get("kind") == "talk_class_teacher":
                _teacher_id, teacher = self.class_teacher(self.character.class_name)
                teacher_name = teacher.get("name", "nauczyciel klasy") if teacher else "nauczyciel klasy"
                await self.send(
                    f"Cel: porozmawiaj z {teacher_name}. Klasa: {self.character.class_name}."
                )

            if row and row["status"] == "active":
                progress, ready = self.quest_progress_for_turnin(quest_id)
                ready_text = " ZAKTUALIZOWANO — GOTOWE DO ODDANIA." if ready else ""
                await self.send(
                    f"Postęp: {progress} z {int(quest.get('needed', 1))}.{ready_text}"
                )
                stock = self.quest_turnin_stock_status(quest_id)
                if stock is not None:
                    have, stock_needed, label = stock
                    missing = max(0, int(stock_needed) - int(have))
                    text = f"Do oddania: {have} z {stock_needed}: {label}."
                    if missing:
                        text += f" Brakuje {missing}."
                    await self.send(text)
            elif row and int(row["completion_count"] or 0) > 0:
                await self.send(
                    f"Historia: ukończono {int(row['completion_count'] or 0)} razy."
                )

            requirements = []
            required_quest = quest.get("requires_quest")
            if required_quest:
                requirements.append(
                    "ukończ quest " + QUESTS.get(required_quest, {}).get("name", required_quest)
                )
            tool_type = quest.get("specialist_tool_type")
            profession = (
                quest.get("required_profession")
                or quest.get("reward_profession")
                or profession_for_tool_type(tool_type)
            )
            min_profession = int(
                quest.get("min_profession_level", quest.get("min_tool_level", 0)) or 0
            )
            if profession and min_profession:
                requirements.append(f"{profession} level {min_profession}")
            if quest.get("required_soul_level"):
                requirements.append(f"Soul Level {quest['required_soul_level']}")
            if quest.get("required_soul_tier"):
                requirements.append(f"Soul Tier {quest['required_soul_tier']}")
            if requirements:
                await self.send("Wymagania: " + ", ".join(requirements) + ".")
            else:
                await self.send("Wymagania: brak dodatkowych wymagań.")

            reward_parts = []
            generated_currency=v0190_quest_currency_reward(quest)
            if generated_currency:
                reward_parts.append(currency_reading_text(generated_currency,0,0))
            for item_id, qty in (quest.get("reward_items") or {}).items():
                item_name = ITEMS.get(item_id, {}).get("name", item_id)
                reward_parts.append(f"{item_name} x{qty}")
            if quest.get("reward_profession_xp"):
                reward_parts.append(
                    f"{quest.get('reward_profession', 'profesja')} XP {quest['reward_profession_xp']}"
                )
            if quest.get("reward_tool_xp"):
                reward_parts.append(f"XP narzędzia {quest['reward_tool_xp']}")
            generated_stat=v0190_quest_stat_reward(quest)
            if generated_stat:
                reward_parts.append(f"EXP każdej statystyki {generated_stat}")
            generated_soul=v0190_quest_soul_reward(quest)
            if generated_soul:
                reward_parts.append(f"Soul XP {generated_soul}")
            if quest.get("unlocks_soul_tier"):
                reward_parts.append(f"odblokowanie Próby Soul Tier {quest['unlocks_soul_tier']}")
            await self.send(
                "Nagrody: " + (", ".join(reward_parts) if reward_parts else "brak dodatkowych nagród") + "."
            )
            if quest.get("manual_currency_reward_coins") is not None:
                await self.send("Waluta questa: ręcznie zbalansowana i chroniona przed automatycznym przeliczeniem.")

            if quest.get("repeatable"):
                cooldown = int(
                    quest.get("repeat_cooldown", QUEST_REPEAT_COOLDOWN_SECONDS)
                )
                await self.send(
                    "Powtarzalność: tak. Odnowienie po ukończeniu: "
                    + self.format_duration_short(cooldown)
                    + "."
                )
            else:
                await self.send("Powtarzalność: nie.")

    def cleanup_quest_map_artifacts_v0243(self, quest_id, *, allow_legacy_generic=False):
            """Usuwa questowe mapy i tropy przypisane do porzucanego/kończonego questa."""
            quest_map_ids = [
                item_id for item_id, item in ITEMS.items()
                if item.get("quest_treasure_map_for") == quest_id
            ]
            removed_items = 0
            for item_id in quest_map_ids:
                qty = self.server.db.item_qty(self.account_id, item_id)
                if qty > 0:
                    self.server.db.remove_item(self.account_id, item_id, qty)
                    removed_items += qty

            tracked = self.server.db.collection_entry_ids(
                self.account_id, "quest_treasure_targets_v0243"
            )
            removed_targets = 0
            prefix = f"{quest_id}|"
            for entry in tuple(tracked):
                if not entry.startswith(prefix):
                    continue
                target = entry[len(prefix):]
                self.server.db.remove_collection_entry(
                    self.account_id, "treasure_targets_v0140", target
                )
                self.server.db.remove_collection_entry(
                    self.account_id, "quest_treasure_targets_v0243", entry
                )
                removed_targets += 1

            # Kompatybilność z aktywnym questem przyjętym jeszcze na v0.24.1/v0.24.2:
            # tam Eren wydawał zwykłą Mapę Skarbu Rubieży. Usuwamy najwyżej jedną sztukę
            # tylko wtedy, gdy konto nigdy nie dostało nowej mapy questowej v0.24.3.
            grant_marker = f"{quest_id}"
            has_new_grant = grant_marker in self.server.db.collection_entry_ids(
                self.account_id, "quest_map_grants_v0243"
            )
            if allow_legacy_generic and not has_new_grant and quest_id == "city_cartographer_secret_marks":
                if self.server.db.item_qty(self.account_id, V014_TREASURE_MAP_ITEM) > 0:
                    if self.server.db.remove_item(self.account_id, V014_TREASURE_MAP_ITEM, 1):
                        removed_items += 1
            return removed_items, removed_targets

    async def abandon_quest_from_context(self, value):
            if self.combat_mob_key:
                await self.send("Nie możesz porzucać questa podczas walki.")
                return
            text = str(value or "").strip()
            quest_id = None
            error = None
            if text.isdigit():
                quest_id, error = self.quest_from_context(text)
            else:
                wanted = self.normalize_description_query(text)
                active = [
                    row for row in self.server.db.quest_rows(self.account_id)
                    if row["status"] == "active" and row["quest_id"] in QUESTS
                ]
                matches = []
                for row in active:
                    quest = QUESTS[row["quest_id"]]
                    names = (quest.get("name", ""), row["quest_id"])
                    normalized = [self.normalize_description_query(name) for name in names]
                    if wanted and any(wanted == name or wanted in name for name in normalized):
                        matches.append(row["quest_id"])
                if len(matches) == 1:
                    quest_id = matches[0]
                elif len(matches) > 1:
                    error = "Nazwa pasuje do kilku aktywnych questów. Wpisz quest, a potem quest porzuć <numer>."
                else:
                    error = "Nie znaleziono takiego aktywnego questa. Wpisz quest, aby zobaczyć numery."
            if error:
                await self.send(error)
                return
            quest = QUESTS.get(quest_id)
            row = self.server.db.quest(self.account_id, quest_id)
            if not quest or not row or row["status"] != "active":
                await self.send("Ten quest nie jest obecnie aktywny.")
                return
            if not self.server.db.abandon_quest(self.account_id, quest_id):
                await self.send("Nie udało się porzucić tego questa.")
                return
            removed_maps, removed_trops = self.cleanup_quest_map_artifacts_v0243(
                quest_id, allow_legacy_generic=True
            )
            for item_id, qty in (quest.get("accept_items") or {}).items():
                have_qty = self.server.db.item_qty(self.account_id, item_id)
                if have_qty > 0:
                    self.server.db.remove_item(
                        self.account_id, item_id, min(have_qty, max(1, int(qty)))
                    )
            await self.send(
                f"Quest porzucony: {quest['name']}. Bieżący postęp został wyzerowany. "
                "Możesz później przyjąć to zadanie ponownie od właściwego NPC."
            )
            if removed_maps or removed_trops:
                await self.send(
                    f"Usunięto questowe mapy: {removed_maps}; anulowane tropy mapy: {removed_trops}."
                )
            # Odśwież kontekst do listy aktywnych, aby numery po porzuceniu były czytelne.
            await self.show_active_quests()

    async def show_active_quests(self):
            rows = [
                row for row in self.server.db.quest_rows(self.account_id)
                if row["status"] == "active" and row["quest_id"] in QUESTS
            ]
            if not rows:
                self.quest_list_context = None
                await self.send("Nie masz aktywnych questów.")
                return
            self.quest_list_context = {
                "source": "active",
                "quest_ids": [row["quest_id"] for row in rows],
            }
            await self.send(f"AKTYWNE QUESTY: {len(rows)}.")
            for number, row in enumerate(rows, 1):
                quest = QUESTS[row["quest_id"]]
                progress, ready = self.quest_progress_for_turnin(row["quest_id"])
                state = "ZAKTUALIZOWANO — GOTOWE DO ODDANIA" if ready else "aktywne"
                stock = self.quest_turnin_stock_status(row["quest_id"])
                stock_text = ""
                if stock is not None:
                    have, stock_needed, label = stock
                    missing = max(0, int(stock_needed) - int(have))
                    stock_text = f" Do oddania {have} z {stock_needed}: {label}."
                    if missing:
                        stock_text += f" Brakuje {missing}."
                await self.send(
                    f"{number}. {quest['name']}. {state}. "
                    f"Postęp {progress} z {quest['needed']}.{stock_text} NPC: {quest['giver']}."
                )
            await self.send("Szczegóły: quest info <numer>.")

    async def show_completed_quests(self):
            rows = [
                row for row in self.server.db.quest_rows(self.account_id)
                if int(row["completion_count"] or 0) > 0 and row["quest_id"] in QUESTS
            ]
            if not rows:
                self.quest_list_context = None
                await self.send("Nie masz jeszcze ukończonych questów.")
                return
            rows.sort(
                key=lambda row: (int(row["completed_at"] or 0), row["quest_id"]),
                reverse=True,
            )
            self.quest_list_context = {
                "source": "completed",
                "quest_ids": [row["quest_id"] for row in rows],
            }
            await self.send(f"UKOŃCZONE QUESTY: {len(rows)}.")
            for number, row in enumerate(rows, 1):
                quest = QUESTS[row["quest_id"]]
                count = int(row["completion_count"] or 0)
                extra = ""
                if row["status"] == "active":
                    extra = " Obecnie ponownie aktywny."
                elif quest.get("repeatable"):
                    cooldown = int(
                        quest.get("repeat_cooldown", QUEST_REPEAT_COOLDOWN_SECONDS)
                    )
                    remaining = self.server.db.repeat_quest_seconds_remaining(
                        self.account_id, row["quest_id"], cooldown
                    )
                    if remaining > 0:
                        extra = (
                            " Powtórka za "
                            + self.format_duration_short(remaining)
                            + "."
                        )
                    else:
                        extra = " Dostępny do ponownego przyjęcia."
                await self.send(
                    f"{number}. {quest['name']}. Ukończono {count} razy.{extra}"
                )
            await self.send("Szczegóły: quest info <numer>.")

    def local_quest_ids(self):
            local_npcs = {
                npc_id: npc
                for npc_id, npc in NPCS.items()
                if npc["room"] == self.character.room_id
            }
            giver_names = {
                self.normalize_description_query(npc["name"])
                for npc in local_npcs.values()
            }

            result = []
            for quest_id, quest in QUESTS.items():
                giver = self.normalize_description_query(quest.get("giver", ""))
                target_npc = str(quest.get("target_npc", "") or "")
                if (giver and giver in giver_names) or (target_npc and target_npc in local_npcs):
                    result.append(quest_id)
            return result

    def normalize_turnin_query(self, query):
            value = self.normalize_description_query(query)
            generic = {
                "", "quest", "questa", "questy",
                "zadanie", "zadania", "zlecenie", "zlecenia",
            }
            if value in generic:
                return ""

            for prefix in (
                "quest ",
                "questa ",
                "zadanie ",
                "zadania ",
                "zlecenie ",
            ):
                if value.startswith(prefix):
                    return value[len(prefix):].strip()

            return value

    def match_local_active_quest(self, query):
            wanted = self.normalize_turnin_query(query)
            candidates = []

            for quest_id in self.local_quest_ids():
                row = self.server.db.quest(self.account_id, quest_id)
                if not row or row["status"] != "active":
                    continue
                quest = QUESTS[quest_id]
                candidates.append((quest_id, quest))

            if not wanted:
                return candidates

            exact = []
            partial = []
            for quest_id, quest in candidates:
                qid = self.normalize_description_query(quest_id)
                name = self.normalize_description_query(quest["name"])
                if wanted in (qid, name):
                    exact.append((quest_id, quest))
                elif wanted in qid or wanted in name:
                    partial.append((quest_id, quest))

            if exact:
                return exact
            return partial

    def quest_id_for_turnin_number(self, raw_number):
            value = str(raw_number or "").strip()
            if not value.isdigit():
                return None, "Podaj numer questa, np. oddaj quest 1."
            index = int(value) - 1
            context = self.quest_list_context or {}
            source = context.get("source")
            if source in ("active", "npc"):
                if source == "npc" and context.get("room_id") != self.character.room_id:
                    return None, "Lista NPC jest nieaktualna. Ponownie wpisz quest list <NPC>."
                quest_ids = list(context.get("quest_ids") or ())
                if index < 0 or index >= len(quest_ids):
                    return None, f"Nie ma questa numer {value} na ostatnio pokazanej liście."
                quest_id = quest_ids[index]
                row = self.server.db.quest(self.account_id, quest_id)
                if not row or row["status"] != "active":
                    return None, (
                        f"Quest {value}: {QUESTS.get(quest_id, {}).get('name', quest_id)} "
                        "nie jest obecnie aktywny."
                    )
                return quest_id, None
            if source == "completed":
                return None, "Ostatnia lista pokazuje ukończone questy. Wpisz questy, aby zobaczyć aktywne."
            return self.active_quest_id_by_number(value)

    async def turn_in_quest_id(self, quest_id):
            if self.combat_mob_key:
                await self.send("Nie możesz oddawać zadania podczas walki.")
                return
            quest = QUESTS.get(quest_id)
            row = self.server.db.quest(self.account_id, quest_id)
            if not quest or not row or row["status"] != "active":
                await self.send("Ten quest nie jest obecnie aktywny.")
                return
            local_ids = set(self.local_quest_ids())
            if quest_id not in local_ids and not quest.get("remote_turnin"):
                npc_name = self.quest_turnin_npc_name_v098(quest)
                await self.send(
                    f"Quest: {quest['name']}. Aby go oddać, idź do NPC: {npc_name}."
                )
                return
            progress, ready = self.quest_progress_for_turnin(quest_id)
            if not ready:
                await self.send(
                    f"Zadanie nie jest jeszcze gotowe do oddania: {quest['name']}. "
                    f"Postęp {progress} z {quest['needed']}."
                )
                stock = self.quest_turnin_stock_status(quest_id)
                if stock is not None:
                    have, needed, label = stock
                    missing = max(0, int(needed) - int(have))
                    await self.send(
                        f"Do oddania masz {have} z {needed}: {label}."
                        + (f" Brakuje {missing}." if missing else "")
                    )
                return
            await self.handle_quest_interaction(quest_id)

    async def turn_in_quest(self, query):
            if self.combat_mob_key:
                await self.send(
                    "Nie możesz oddawać zadania podczas walki."
                )
                return

            local_npcs = [
                npc
                for npc in NPCS.values()
                if npc["room"] == self.character.room_id
            ]
            if not local_npcs:
                await self.send(
                    "Nie ma tutaj NPC, któremu można oddać zadanie."
                )
                return

            matches = self.match_local_active_quest(query)
            wanted = self.normalize_turnin_query(query)

            if wanted:
                if not matches:
                    await self.send(
                        "Nie masz tutaj aktywnego zadania pasującego do tej nazwy."
                    )
                    return
                if len(matches) > 1:
                    await self.send(
                        "Pasuje kilka zadań. Podaj pełną nazwę: "
                        + ", ".join(q["name"] for _qid, q in matches)
                        + "."
                    )
                    return

                quest_id, quest = matches[0]
                progress, ready = self.quest_progress_for_turnin(quest_id)
                if not ready:
                    await self.send(
                        f"Zadanie nie jest jeszcze gotowe do oddania: "
                        f"{quest['name']}. Postęp {progress} z "
                        f"{quest['needed']}."
                    )
                    return

                await self.handle_quest_interaction(quest_id)
                return

            ready = []
            active = []
            for quest_id, quest in matches:
                progress, is_ready = self.quest_progress_for_turnin(quest_id)
                active.append((quest_id, quest, progress, is_ready))
                if is_ready:
                    ready.append((quest_id, quest))

            if len(ready) == 1:
                await self.handle_quest_interaction(ready[0][0])
                return

            if len(ready) > 1:
                await self.send(
                    "Masz tutaj kilka zadań gotowych do oddania. "
                    "Wpisz oddaj <nazwa zadania>: "
                    + ", ".join(q["name"] for _qid, q in ready)
                    + "."
                )
                return

            if active:
                await self.send(
                    "Masz tutaj aktywne zadania, ale żadne nie jest jeszcze "
                    "gotowe do oddania."
                )
                for _quest_id, quest, progress, _is_ready in active:
                    stock = self.quest_turnin_stock_status(_quest_id)
                    extra = ""
                    if stock is not None:
                        have, stock_needed, label = stock
                        missing = max(0, int(stock_needed) - int(have))
                        extra = f" Do oddania {have} z {stock_needed}: {label}."
                        if missing:
                            extra += f" Brakuje {missing}."
                    await self.send(
                        f"{quest['name']}: {progress} z {quest['needed']}.{extra}"
                    )
                return

            await self.send(
                "Nie masz tutaj aktywnego zadania do oddania."
            )

    async def handle_quest_interaction(self, quest_id):
            q = QUESTS[quest_id]
            row = self.server.db.quest(self.account_id, quest_id)

            if not row:
                self.server.db.start_quest(self.account_id, quest_id)
                await self.send(f"Nowe zadanie: {q['name']}. {q['description']}")
                await self.announce_active_quest_progress(quest_id)
                return

            if row["status"] == "completed":
                if q.get("repeatable"):
                    cooldown = int(
                        q.get(
                            "repeat_cooldown",
                            QUEST_REPEAT_COOLDOWN_SECONDS,
                        )
                    )
                    remaining = self.server.db.repeat_quest_seconds_remaining(
                        self.account_id, quest_id, cooldown
                    )
                    if remaining > 0:
                        await self.send(
                            f"Zadanie {q['name']} jest na odnowieniu. "
                            f"Możesz powtórzyć je za "
                            f"{self.format_duration_short(remaining)}."
                        )
                        return

                    self.server.db.restart_quest(self.account_id, quest_id)
                    cooldown_minutes = max(1, int(cooldown) // 60)
                    await self.send(
                        f"Zadanie ponownie dostępne po {cooldown_minutes} minutach: "
                        f"{q['name']}. {q['description']}"
                    )
                    await self.announce_active_quest_progress(quest_id)
                    return

                if q.get("unlocks_soul_tier"):
                    await self.send(
                        f"Próba ukończona: {q['name']}. "
                        f"Możesz użyć unlock, aby odblokować Tier "
                        f"{q['unlocks_soul_tier']} Broni Duszy."
                    )
                    return

                await self.send(f"Zadanie {q['name']} jest już ukończone.")
                return

            if q["kind"] == "kill":
                progress = int(row["progress"])
                if progress < q["needed"]:
                    await self.send(
                        f"Quest aktywny: {q['name']}. "
                        f"Postęp {progress} z {q['needed']}. "
                        f"{q['description']}"
                    )
                    return

            elif q["kind"] == "collect":
                # v0.8.66: każdy collect zaczyna 0/x i wymaga wykonania celu
                # po przyjęciu. Sam stary zapas nigdy nie zalicza postępu.
                completed_events = min(
                    int(row["progress"]),
                    int(q["needed"]),
                )
                if completed_events < int(q["needed"]):
                    action = "Wykonano" if q.get("track_craft_progress") else "Zdobyto"
                    await self.send(
                        f"Quest aktywny: {q['name']}. "
                        f"{action} {completed_events} z {q['needed']}: "
                        f"{ITEMS[q['target']]['name']}."
                    )
                    return

                have = self.quest_crafted_item_have_v0333(q["target"])
                if have < q["needed"]:
                    await self.send(
                        f"Quest aktywny: {q['name']}. "
                        f"Cel wykonany {completed_events} z {q['needed']}, "
                        f"ale do oddania masz {have} z {q['needed']}: "
                        f"{ITEMS[q['target']]['name']}."
                    )
                    return

                if not self.consume_quest_crafted_items_v0333(q["target"], q["needed"]):
                    await self.send("Nie udało się pobrać przedmiotów do oddania questa.")
                    return

            elif q["kind"] == "collect_resource":
                gathered = min(
                    int(row["progress"]),
                    int(q["needed"]),
                )
                if gathered < int(q["needed"]):
                    await self.send(
                        f"Quest aktywny: {q['name']}. "
                        f"Zdobyto {gathered} z {q['needed']}: "
                        f"{ITEMS[q['target']]['name']}."
                    )
                    return

                container = self.resource_quest_container(
                    q["target"]
                )
                have = self.resource_quest_have(
                    q["target"]
                )
                if have < int(q["needed"]):
                    await self.send(
                        f"Cel zdobywania wykonany, ale do oddania "
                        f"masz {have} z {q['needed']}: "
                        f"{ITEMS[q['target']]['name']}."
                    )
                    return

                ok = (
                    self.server.db.consume_items_across_storage_and_inventory(
                        self.account_id,
                        self.resource_quest_equivalent_ids(q["target"]),
                        int(q["needed"]),
                        container,
                    )
                )
                if not ok:
                    await self.send(
                        "Nie udało się pobrać wymaganych surowców."
                    )
                    return

            elif q["kind"] == "collect_resource_set":
                requirements = dict(q.get("resource_targets") or {})
                counts = self.server.db.resource_set_progress_v0929(
                    self.account_id, quest_id, requirements
                )
                missing_progress = []
                missing_items = []
                for target_id, needed_each in requirements.items():
                    got = int(counts.get(target_id, 0))
                    have = self.resource_quest_have(target_id)
                    if got < int(needed_each):
                        missing_progress.append(f"{ITEMS[target_id]['name']} {got}/{int(needed_each)}")
                    if have < int(needed_each):
                        missing_items.append(f"{ITEMS[target_id]['name']} {have}/{int(needed_each)}")
                if missing_progress:
                    await self.send("Quest aktywny: brakuje wydobycia: " + ", ".join(missing_progress) + ".")
                    return
                if missing_items:
                    await self.send("Brakuje surowców do fizycznego oddania: " + ", ".join(missing_items) + ".")
                    return
                for target_id, needed_each in requirements.items():
                    ok = self.server.db.consume_items_across_storage_and_inventory(
                        self.account_id,
                        self.resource_quest_equivalent_ids(target_id),
                        int(needed_each),
                        self.resource_quest_container(target_id),
                    )
                    if not ok:
                        await self.send("Nie udało się pobrać wymaganych próbek rudy.")
                        return

            elif q["kind"] == "craft_set":
                targets = tuple(q.get("targets") or ())
                crafted = self.craft_set_progress(
                    row, q
                )
                if crafted < len(targets):
                    await self.send(
                        f"Quest aktywny: {q['name']}. "
                        f"Elementy zestawu {crafted} z {len(targets)}."
                    )
                    return

                missing = [
                    item_id
                    for item_id in targets
                    if self.quest_crafted_item_have_v0333(item_id) <= 0
                ]
                if missing:
                    await self.send(
                        "Pełny zestaw został już wykuty, ale brakuje "
                        "elementów do oddania: "
                        + ", ".join(
                            ITEMS[item_id]["name"]
                            for item_id in missing
                        )
                        + "."
                    )
                    return

                for item_id in targets:
                    if not self.consume_quest_crafted_items_v0333(item_id, 1):
                        await self.send(
                            "Nie udało się pobrać elementu zestawu do oddania questa."
                        )
                        return

            elif q["kind"] in ("deliver_npc", "talk_npc", "talk_class_teacher"):
                progress = int(row["progress"])
                if progress < int(q.get("needed", 1)):
                    if q["kind"] == "deliver_npc":
                        target = NPCS.get(q.get("target_npc"), {})
                        target_name = target.get("name", "właściwego NPC")
                        await self.send(
                            f"Quest aktywny: {q['name']}. Dostarcz przesyłkę do: {target_name}."
                        )
                    elif q["kind"] == "talk_class_teacher":
                        await self.send(
                            f"Quest aktywny: {q['name']}. Porozmawiaj z nauczycielem swojej klasy: "
                            f"{self.character.class_name}."
                        )
                    else:
                        await self.send(f"Quest aktywny: {q['name']}. Cel nie został jeszcze wykonany.")
                    return

            elif q["kind"] == "collect_distinct_category":
                category = self.quest_collect_category_info(q["target"])
                if not category:
                    await self.send("Błąd konfiguracji zadania.")
                    return
                _ids, container, label = category
                distinct_ids = self.server.db.distinct_category_items_v023(
                    self.account_id, quest_id
                )[: int(q["needed"])]
                if len(distinct_ids) < int(q["needed"]):
                    await self.send(
                        f"Quest aktywny: {q['name']}. Różne gatunki {len(distinct_ids)} z {q['needed']}."
                    )
                    return
                missing = [iid for iid in distinct_ids if self.resource_quest_have(iid) < 1]
                if missing:
                    await self.send(
                        "Cel wykonany, ale brakuje do oddania: "
                        + ", ".join(ITEMS.get(iid, {"name": iid})["name"] for iid in missing)
                        + "."
                    )
                    return
                for iid in distinct_ids:
                    ok = self.server.db.consume_items_across_storage_and_inventory(
                        self.account_id, self.resource_quest_equivalent_ids(iid), 1, container
                    )
                    if not ok:
                        await self.send("Nie udało się pobrać wymaganych ryb.")
                        return

            elif q["kind"] == "collect_category":
                category = self.quest_collect_category_info(q["target"])
                if not category:
                    await self.send("Błąd konfiguracji zadania.")
                    return

                ids, container, label = category
                row = self.server.db.quest(self.account_id, quest_id)
                progress = min(int(row["progress"]), int(q["needed"]))
                if progress < q["needed"]:
                    await self.send(
                        f"Quest aktywny: {q['name']}. "
                        f"Postęp {progress} z {q['needed']} wymaganych {label}."
                    )
                    return
                have = self.server.db.total_items_across_storage_and_inventory(
                    self.account_id, ids, container
                )
                if have < q["needed"]:
                    await self.send(
                        f"Cel wykonany, ale do oddania masz {have} z "
                        f"{q['needed']} wymaganych {label}."
                    )
                    return

                ok = (
                    self.server.db.consume_items_across_storage_and_inventory(
                        self.account_id, ids, q["needed"], container
                    )
                )
                if not ok:
                    await self.send(
                        "Nie udało się pobrać wymaganych surowców."
                    )
                    return

            await self.complete_quest(quest_id)

    def quest_completed(self, quest_id):
            row = self.server.db.quest(
                self.account_id, quest_id
            )
            # v0.8.31: ukończenie jest historią, nie tylko bieżącym statusem.
            # Powtórne przyjęcie questa nie może zablokować kolejnego etapu,
            # który wymaga, aby poprzedni był kiedykolwiek ukończony.
            return bool(
                row
                and (
                    row["status"] == "completed"
                    or int(row["completion_count"] or 0) > 0
                )
            )

    def npc_chain_quest_available(self, quest_id):
            quest = QUESTS.get(quest_id)
            if not quest:
                return False
            required = quest.get("requires_quest")
            if required and not self.quest_completed(required):
                return False
            return True

    def npc_chain_current_quest(self, npc):
            chain = tuple(npc.get("quest_chain") or ())
            if not chain:
                return npc.get("quest")

            for quest_id in chain:
                row = self.server.db.quest(
                    self.account_id, quest_id
                )
                if row and row["status"] == "active":
                    return quest_id

            available = [
                quest_id
                for quest_id in chain
                if self.npc_chain_quest_available(quest_id)
            ]
            return available[-1] if available else chain[0]

    async def show_npc_quest_chain(self, npc):
            chain = tuple(npc.get("quest_chain") or ())
            if not chain:
                return
            await self.send(
                f"Łańcuch zadań: {len(chain)} etapy."
            )
            for number, quest_id in enumerate(chain, 1):
                quest = QUESTS[quest_id]
                row = self.server.db.quest(
                    self.account_id, quest_id
                )
                if row and row["status"] == "active":
                    state = "aktywne"
                elif row and row["status"] == "completed":
                    state = "ukończone"
                elif self.npc_chain_quest_available(quest_id):
                    state = "dostępne"
                else:
                    state = "zablokowane"
                await self.send(
                    f"Etap {number}: {quest['name']}. {state}."
                )

    def specialist_quest_available(self, quest_id):
            quest = QUESTS.get(quest_id)
            if not quest:
                return False

            required_quest = quest.get("requires_quest")
            if (
                required_quest
                and not self.quest_completed(required_quest)
            ):
                return False

            tool_type = quest.get("specialist_tool_type")
            profession = (
                quest.get("required_profession")
                or quest.get("reward_profession")
                or profession_for_tool_type(tool_type)
            )
            if profession:
                prow = self.server.db.profession(self.account_id, profession)
                required_profession_level = int(
                    quest.get("min_profession_level", quest.get("min_tool_level", 1))
                )
                if (
                    int(prow["level"])
                    < required_profession_level
                ):
                    return False

            return True

    def specialist_current_quest(self, npc):
            chain = tuple(npc.get("specialist_quests") or ())
            if not chain:
                quest_id = npc.get("quest")
                return quest_id, None

            # Jeśli jakiś etap jest aktywny, zawsze kontynuujemy właśnie jego.
            for quest_id in chain:
                row = self.server.db.quest(
                    self.account_id, quest_id
                )
                if row and row["status"] == "active":
                    return quest_id, None

            # Najwyższy odblokowany etap staje się bieżącym.
            available = [
                quest_id
                for quest_id in chain
                if self.specialist_quest_available(quest_id)
            ]
            if available:
                current = available[-1]
            else:
                current = chain[0]

            # Opis kolejnego progu.
            next_info = None
            try:
                index = chain.index(current)
            except ValueError:
                index = 0

            if index + 1 < len(chain):
                next_id = chain[index + 1]
                next_q = QUESTS[next_id]
                next_info = (
                    next_q["name"],
                    int(next_q.get("min_profession_level", next_q.get("min_tool_level", 1))),
                )

            return current, next_info

    async def show_specialist_quest_progression(self, npc):
            chain = tuple(npc.get("specialist_quests") or ())
            if not chain:
                return

            tool_type = npc.get("specialist_tool_type")
            profession = profession_for_tool_type(tool_type)
            if not profession:
                profession = QUESTS[chain[0]].get("reward_profession")
            prow = self.server.db.profession(self.account_id, profession) if profession else None
            profession_level = int(prow["level"]) if prow else 1

            await self.send(
                f"Łańcuch zleceń specjalisty: {len(chain)} etapy. "
                f"Aktualny poziom {profession}: {profession_level}."
            )

            for number, quest_id in enumerate(chain, 1):
                quest = QUESTS[quest_id]
                row = self.server.db.quest(self.account_id, quest_id)
                minimum = int(quest.get("min_profession_level", quest.get("min_tool_level", 1)))

                if row and row["status"] == "active":
                    state = "aktywne"
                elif row and row["status"] == "completed":
                    state = "ukończone"
                elif not self.specialist_quest_available(quest_id):
                    required = quest.get("requires_quest")
                    reasons = []
                    if profession and profession_level < minimum:
                        reasons.append(f"wymaga {profession} level {minimum}")
                    if required and not self.quest_completed(required):
                        reasons.append("wymaga ukończenia poprzedniego etapu")
                    state = "zablokowane: " + ", ".join(reasons)
                else:
                    state = "dostępne"

                await self.send(f"Etap {number}: {quest['name']}. {state}.")

    async def show_profession_specialist(self, npc):
            tool_type = npc.get("specialist_tool_type")
            if not tool_type:
                return

            await self.show_single_tool(tool_type)

            topic = npc.get("specialist_topic")
            if topic:
                await self.send(
                    f"Specjalizacja: {topic}. "
                    f"Pełny stan wszystkich profesji: profesje. "
                    f"Pełny stan narzędzi: narzedzia."
                )

            recipes = npc.get("specialist_recipes")
            if recipes:
                await self.send(
                    f"Receptury tej specjalizacji: wpisz {recipes}."
                )

    async def deliver_quest_item(self, args=""):
            """v0.23: jawne dostarczanie przedmiotów questowych do właściwego NPC.

            `dostarcz mapa` jest wygodnym, czytelnym dla NVDA odpowiednikiem
            rozmowy z odbiorcą. Komenda nigdy nie oddaje losowego questa: przy
            kilku dopasowaniach wypisuje możliwe dostawy i prosi o dokładniejszą
            nazwę.
            """
            if self.combat_mob_key:
                await self.send("Nie możesz dostarczać przedmiotów questowych podczas walki.")
                return

            raw = str(args or "").strip()
            query = normalize_lookup_text(raw)
            active = []
            for row in self.server.db.quest_rows(self.account_id):
                if row["status"] != "active":
                    continue
                quest_id = row["quest_id"]
                quest = QUESTS.get(quest_id)
                if not quest or quest.get("kind") != "deliver_npc":
                    continue
                item_id = quest.get("quest_item")
                target_id = quest.get("target_npc")
                target = NPCS.get(target_id, {})
                item = ITEMS.get(item_id, {})
                if not item_id or not target_id:
                    continue
                item_name = str(item.get("name", item_id))
                searchable = normalize_lookup_text(
                    " ".join((item_name, quest.get("name", ""), item_id))
                )
                # Naturalne skróty dla najczęstszych przesyłek, np. `dostarcz mapa`.
                query_match = (not query) or query in searchable
                if query and query in ("mapa", "mape", "mapę", "map"):
                    query_match = "map" in searchable
                if query_match:
                    active.append((quest_id, quest, item_id, item_name, target_id, target))

            if not active:
                if raw:
                    await self.send(f"Nie masz aktywnej dostawy pasującej do: {raw}.")
                else:
                    await self.send("Nie masz aktywnego questa z przedmiotem do dostarczenia.")
                return

            here = [entry for entry in active if entry[5].get("room") == self.character.room_id]
            candidates = here or active
            if len(candidates) > 1:
                await self.send("Pasuje kilka aktywnych dostaw. Podaj dokładniejszą nazwę:")
                for _qid, quest, _iid, item_name, _tid, target in candidates:
                    await self.send(f"{item_name} — {quest['name']} — odbiorca: {target.get('name', 'nieznany')}.")
                return

            quest_id, quest, item_id, item_name, target_id, target = candidates[0]
            if target.get("room") != self.character.room_id:
                await self.send(
                    f"Odbiorcy nie ma tutaj. Dostarcz {item_name} do: "
                    f"{target.get('name', 'właściwy NPC')}. Możesz użyć prowadz {target.get('name', '')}."
                )
                return

            needed = max(1, int(quest.get("needed", 1)))
            have = self.server.db.item_qty(self.account_id, item_id)
            if have < needed:
                await self.send(
                    f"Nie masz wymaganej przesyłki: {item_name}. "
                    "Jeśli zaginęła, porzuć quest i przyjmij go ponownie po jego dostępności."
                )
                return

            self.server.db.remove_item(self.account_id, item_id, needed)
            await self.send(f"Dostarczasz: {item_name}.")
            self.server.db.set_quest_progress(
                self.account_id, quest_id, int(quest.get("needed", 1))
            )
            await self.announce_active_quest_progress(quest_id)
            await self.complete_quest(quest_id)

    async def process_starter_talk_quests(self, npc_id, npc):
            """v0.23: obsługuje KAŻDĄ aktywną dostawę/rozmowę u właściwego NPC.

            Historyczna nazwa funkcji zostaje dla zgodności. W v0.22 tylko questy
            oznaczone starter_quest były tu wykonywane, przez co miejskie dostawy
            deliver_npc pozostawały na 0/1 mimo rozmowy z prawidłowym odbiorcą.
            """
            completed_any = False
            for row in list(self.server.db.quest_rows(self.account_id)):
                if row["status"] != "active":
                    continue
                quest_id = row["quest_id"]
                quest = QUESTS.get(quest_id)
                if not quest:
                    continue

                kind = quest.get("kind")
                if kind not in ("deliver_npc", "talk_npc", "talk_class_teacher"):
                    continue
                matches = False
                if kind in ("deliver_npc", "talk_npc"):
                    matches = quest.get("target_npc") == npc_id
                elif kind == "talk_class_teacher":
                    matches = (
                        bool(npc.get("teacher_class"))
                        and npc.get("teacher_class") == self.character.class_name
                    )

                if not matches:
                    continue

                if kind == "deliver_npc":
                    item_id = quest.get("quest_item")
                    needed = max(1, int(quest.get("needed", 1)))
                    if not item_id or self.server.db.item_qty(self.account_id, item_id) < needed:
                        item_name = ITEMS.get(item_id, {}).get("name", "przedmiot questowy")
                        await self.send(
                            f"Nie masz wymaganej przesyłki: {item_name}. "
                            "Porzuć i przyjmij quest ponownie u Archiwisty Sola, jeśli przedmiot zaginął."
                        )
                        continue
                    self.server.db.remove_item(self.account_id, item_id, needed)
                    await self.send(
                        f"Przekazujesz: {ITEMS[item_id]['name']}."
                    )

                self.server.db.set_quest_progress(
                    self.account_id, quest_id, int(quest.get("needed", 1))
                )
                await self.announce_active_quest_progress(quest_id)
                await self.complete_quest(quest_id)
                completed_any = True

            return completed_any

    def profession_rank_reaction(self, npc_id, npc):
            """v0.9.7: krótka reakcja NPC na bieżącą rangę profesji gracza."""
            profession = normalize_profession_name(npc.get("rank_profession"))
            if profession not in PROFESSION_RANK_NAMES:
                return ""
            row = self.server.db.profession(self.account_id, profession)
            level = max(1, min(profession_max_level(profession), int(row["level"])))
            rank = profession_rank(level, profession)
            rank_name = profession_rank_name(profession, level)
            stage = profession_npc_reaction_stage(rank)
            reaction_key = PROFESSION_NPC_RANK_REACTION_ALIASES.get(npc_id, npc_id)
            table = PROFESSION_NPC_RANK_REACTIONS.get(reaction_key, {})
            reaction = table.get(stage)
            if not reaction:
                # Bezpieczny fallback dla przyszłych NPC profesyjnych.
                reaction = (
                    "Widzę twój rozwój w tej profesji. Im wyższa ranga, "
                    "tym bardziej rozmówcy traktują cię jak doświadczonego fachowca."
                )
            return f"Twoja ranga: {rank_name}, level {level}. {reaction}"

    async def talk(self, query):
            raw_query = str(query or "").strip()
            normalized = self.normalize_description_query(raw_query)
            if normalized.startswith("to "):
                raw_query = raw_query.split(None, 1)[1].strip()
            elif normalized.startswith("z "):
                raw_query = raw_query.split(None, 1)[1].strip()

            candidates = v0160_npcs_in_room(self.character.room_id)
            found = find_by_name(candidates, raw_query)
            if not found:
                if candidates:
                    await self.send("Nie rozpoznaję tego NPC.")
                else:
                    await self.send(
                        "Nie ma tutaj nikogo, z kim można rozpocząć rozmowę."
                    )
                return

            npc_id, npc = found
            dialogue = npc["dialogue"]
            rank_reaction = self.profession_rank_reaction(npc_id, npc)
            if rank_reaction:
                dialogue = f"{dialogue} {rank_reaction}"
            await self.send(f"{npc['name']}: {dialogue}")

            await self.process_starter_talk_quests(npc_id, npc)

            # v0.9.9: NPC sam informuje o nowych zadaniach i rozpoznaje powrót
            # z zadaniem aktywnym lub gotowym do oddania.
            await self.announce_npc_quest_context_v099(npc_id, npc)

            if npc.get("teacher_class"):
                await self.teacher_lesson(npc)
                return

            if npc.get("specialist_tool_type"):
                await self.show_profession_specialist(npc)

            quest_ids = self.quest_ids_for_npc(npc_id, npc)
            if quest_ids:
                # v0.8.31: rozmowa pokazuje ofertę, ale niczego nie przyjmuje
                # automatycznie. Gracz wybiera konkretny numer.
                await self.show_npc_quest_offers(npc_id, npc)

    def quest_turnin_npc_name_v098(self, quest):
            """Zwraca NPC, który faktycznie odbiera zadanie w bieżącym turn-in."""
            kind = quest.get("kind")
            target_npc = quest.get("target_npc")
            if kind in ("deliver_npc", "talk_npc") and target_npc in NPCS:
                return NPCS[target_npc].get("name", quest.get("giver", "NPC"))
            if kind == "talk_class_teacher":
                for npc in NPCS.values():
                    if (
                        npc.get("room") == self.character.room_id
                        and npc.get("teacher_class") == self.character.class_name
                    ):
                        return npc.get("name", "Nauczyciel klasy")
                return "Nauczyciel klasy"
            return str(quest.get("giver") or "NPC")

    def quest_turnin_reaction_v098(self, quest, npc_name):
            """Krótki komentarz NPC przy oddaniu, dopasowany do celu/profesji."""
            name_cf = str(npc_name).casefold()
            profession = normalize_profession_name(
                quest.get("reward_profession")
                or quest.get("required_profession")
                or profession_for_tool_type(quest.get("reward_tool_type"))
                or profession_for_tool_type(quest.get("specialist_tool_type"))
                or ""
            )

            if profession == "Wędkarstwo" or "borys" in name_cf or "mistrz wędkarstwa" in name_cf:
                return "Dobry połów. Widać, że znasz wodę i nie wyciągasz sieci byle jak."
            if profession == "Górnictwo" or any(x in name_cf for x in ("górnik", "gornik", "kordan", "dagna")):
                return "Porządny urobek. Taki materiał ma wartość i zasługuje na uczciwą zapłatę."
            if profession == "Drwalstwo" or any(x in name_cf for x in ("drwal", "bran", "oren")):
                return "Dobra robota. Drewno jest pozyskane porządnie i bez marnowania materiału."
            if profession == "Zielarstwo" or any(x in name_cf for x in ("zielar", "sena", "liora", "ira", "aptekarka")):
                return "Dobrze zebrane. Rośliny zachowały to, co w nich najcenniejsze."
            if profession == "Gotowanie" or "marcel" in name_cf:
                return "Dobra robota. Smak i wykonanie są takie, jakich oczekuję od fachowca."
            if profession == "Alchemia" or "orin" in name_cf:
                return "Właściwe proporcje i czyste wykonanie. Tak powinno wyglądać ukończone zlecenie."
            if profession == "Kowalstwo" or any(x in name_cf for x in ("kowal", "haldor", "brok")):
                return "Solidna robota. Wykonanie jest równe, a materiał został dobrze wykorzystany."
            if profession == "Jubilerstwo" or "mirella" in name_cf:
                return "Precyzyjna praca. Kamień i oprawa są przygotowane tak, jak należy."

            kind = quest.get("kind")
            if kind == "kill":
                return "Dobra robota. Cel został wykonany i okolica jest dzięki temu bezpieczniejsza."
            if kind in ("collect", "collect_resource", "collect_resource_set", "collect_category", "collect_distinct_category"):
                return "Właśnie tego potrzebowałem. Wszystko się zgadza i zadanie uznaję za wykonane."
            if kind == "craft_set":
                return "Pełny zestaw jest gotowy. To wykonanie zasługuje na zapłatę."
            if kind == "deliver_npc":
                return "Przesyłka dotarła w całości. Dziękuję za dostarczenie jej osobiście."
            if kind in ("talk_npc", "talk_class_teacher"):
                return "Dobrze, że przyszedłeś. To wystarczy, aby uznać ten etap zadania za wykonany."
            return "Dobra robota. Zadanie zostało wykonane zgodnie z ustaleniami."

    async def complete_quest(self, quest_id):
            q = QUESTS[quest_id]
            self.server.db.complete_quest(self.account_id, quest_id)
            self.cleanup_quest_map_artifacts_v0243(quest_id, allow_legacy_generic=False)
            self.server.db.add_lifetime_stat(self.account_id, "quests_completed", 1)

            # v0.9.8: NPC najpierw reaguje na oddanie, potem przekazuje nagrody.
            turnin_npc = self.quest_turnin_npc_name_v098(q)
            turnin_reaction = self.quest_turnin_reaction_v098(q, turnin_npc)
            await self.send(f"{turnin_npc}: {turnin_reaction}")

            reward_prof_xp = int(
                q.get("reward_profession_xp", 0)
            )
            reward_tool_xp = int(
                q.get("reward_tool_xp", 0)
            )
            reward_tool_type = q.get("reward_tool_type")
            reward_profession = (
                q.get("reward_profession")
                or profession_for_tool_type(reward_tool_type)
            )

            if reward_prof_xp:
                await self.grant_profession_reward_xp(
                    reward_profession,
                    reward_prof_xp,
                    reward_tool_type,
                    reward_tool_xp,
                )
            elif reward_tool_xp and reward_tool_type:
                await self.grant_tool_reward_xp(
                    reward_tool_type,
                    reward_tool_xp,
                )

            # EXP rozwoju statystyk nie tworzy levelu postaci.
            # v0.19: quest może dawać bardzo duże liczby EXP. Nie obcinamy
            # nagrody procentowym capem; tempo kontroluje globalna krzywa wymagań.
            is_combat_quest = q.get("kind") == "kill"
            # v0.9.14: każdy quest walki daje prawdziwy EXP sześciu statystyk.
            # Korzystamy z istniejącego add_stat_progress, więc rosną bezpośrednio
            # Siła, Zręczność, Kondycja, Inteligencja, Siła Woli i Charyzma.
            reward_exp = v0914_combat_quest_stat_reward(q)

            quest_stat_applied = []
            if reward_exp:
                for stat_name in self.character.STAT_PROGRESS_FIELDS:
                    granted = v0874_quest_stat_progress_base_grant(
                        self.character, stat_name, reward_exp, q.get("repeatable", False)
                    )
                    granted = self.apply_double_xp(granted)
                    quest_stat_applied.append(granted)
                    for msg in self.character.add_stat_progress(
                        granted, targets=(stat_name,)
                    ):
                        await self.send(msg)

            # v0.19: quest walki daje duży Soul XP z globalnego generatora.
            # Bramka Soul Tier pozostaje jedyną twardą blokadą progresji Soul.
            reward_soul_xp = v0914_combat_quest_soul_reward(q, self.character)
            if reward_soul_xp:
                await self.send(f"Nagroda questa walki: {reward_soul_xp} Soul XP.")
                await self.grant_soul_xp(reward_soul_xp)

            quest_coins=v0190_quest_currency_reward(q)
            self.character.silver += quest_coins
            quest_character_xp=v0270_quest_character_reward(q)
            for _msg in self.add_character_xp_with_event(quest_character_xp):
                await self.send(_msg)
            for item_id, qty in q["reward_items"].items():
                self.server.db.add_item(self.account_id, item_id, qty)
                await self.record_item_collection(
                    item_id,
                    source=f"Nagroda questa: {q['name']}",
                    announce=True,
                    amount=qty,
                )
            self.server.db.save_character(self.character)
            if q.get("reward_faction_v016"):
                await self.add_faction_reputation_v016(
                    str(q.get("reward_faction_v016")), int(q.get("reward_faction_amount_v016", 0) or 0),
                    reason=f"quest:{quest_id}",
                )
            await self.send(f"Zadanie ukończone: {q['name']}.")
            if q.get("unlocks_soul_tier"):
                await self.send(
                    f"Próba Broni Duszy zakończona. Tier "
                    f"{q['unlocks_soul_tier']} jest gotowy do odblokowania "
                    "komendą unlock."
                )
            if q.get("repeatable"):
                cooldown = int(
                    q.get("repeat_cooldown", QUEST_REPEAT_COOLDOWN_SECONDS)
                )
                await self.send(
                    "To zadanie jest powtarzalne. Będzie ponownie dostępne "
                    f"za {max(1, cooldown // 60)} minut."
                )
            if reward_exp:
                if quest_stat_applied:
                    lo = min(quest_stat_applied)
                    hi = max(quest_stat_applied)
                    amount_text = str(lo) if lo == hi else f"{lo}-{hi}"
                else:
                    amount_text = "0"
                await self.send(
                    f"Bazowa nagroda EXP statystyk: {reward_exp}; "
                    f"zastosowano {amount_text} EXP osobno do Siły, Zręczności, Kondycji, "
                    "Inteligencji, Siły Woli i Charyzmy przed bonusem rasy."
                )
            if quest_coins:
                await self.send(
                    f"{turnin_npc} wręcza ci nagrodę: "
                    + currency_reading_text(quest_coins,0,0) + "."
                )
            for item_id, qty in q["reward_items"].items():
                await self.send(
                    f"{turnin_npc} wręcza ci nagrodę: "
                    f"{ITEMS[item_id]['name']} x{qty}."
                )

    def active_quest_id_by_number(self, raw_number):
            """Numer z listy `quest` / `questy` zawsze oznacza aktywny quest."""
            value = str(raw_number or "").strip()
            if not value.isdigit():
                return None, "Podaj numer aktywnego questa, np. oddaj quest 2."
            rows = [
                row for row in self.server.db.quest_rows(self.account_id)
                if row["status"] == "active" and row["quest_id"] in QUESTS
            ]
            index = int(value) - 1
            if index < 0 or index >= len(rows):
                return None, f"Nie masz aktywnego questa numer {value}. Wpisz questy, aby zobaczyć listę."
            return rows[index]["quest_id"], None

    def strip_optional_quest_word(self, text):
            """Obsługuje naturalne formy: accept quest 2 / oddaj quest 2."""
            raw = str(text or "").strip()
            norm = self.normalize_description_query(raw)
            prefixes = (
                "quest ", "questa ", "questy ", "zadanie ", "zadania ",
                "zlecenie ", "zlecenia ",
            )
            for prefix in prefixes:
                if norm.startswith(prefix):
                    return raw.split(maxsplit=1)[1].strip() if " " in raw else ""
            return raw

    async def accept_quest_command(self, args):
            """Top-level: accept quest <numer> / przyjmij quest <numer>."""
            value = self.strip_optional_quest_word(args)
            if not value:
                await self.send(
                    "Użycie: accept quest <numer>. Najpierw wpisz quest list <NPC>."
                )
                return
            await self.accept_quest_from_context(value)

    async def turn_in_quest_command(self, args):
            """Top-level: oddaj quest <numer>, z zachowaniem starego oddaj <nazwa>."""
            raw = str(args or "").strip()
            value = self.strip_optional_quest_word(raw)
            # v0.25.0: numer oznacza pozycję z ostatnio pokazanej listy (questy lub
            # quest list <NPC>). Bez kontekstu używamy globalnej listy aktywnych.
            if value.isdigit():
                quest_id, error = self.quest_id_for_turnin_number(value)
                if error:
                    await self.send(error)
                    return
                await self.turn_in_quest_id(quest_id)
                return
            # Stare formy nadal działają: oddaj, oddaj <nazwa questa>, oddaj zadanie.
            await self.turn_in_quest(raw)

    async def quests(self, args=""):
            raw = str(args or "").strip()
            norm = self.normalize_description_query(raw)

            if not norm or norm in ("aktywne", "active", "aktywny", "current"):
                await self.show_active_quests()
                return

            if norm in (
                "ukonczone", "ukończone", "completed", "done", "historia", "history"
            ):
                await self.show_completed_quests()
                return

            if norm in ("godzinne", "godzinny", "hourly", "hourlies"):
                await self.show_hourly_quests()
                return

            if norm == "list" or norm == "lista":
                await self.show_quest_npc_list("")
                return

            for prefix in ("list ", "lista "):
                if norm.startswith(prefix):
                    # Używamy surowego tekstu, żeby zachować nazwę NPC.
                    npc_query = raw.split(maxsplit=1)[1] if " " in raw else ""
                    await self.show_quest_npc_list(npc_query)
                    return

            for prefix in ("accept ", "przyjmij ", "przyjm "):
                if norm.startswith(prefix):
                    value = raw.split(maxsplit=1)[1] if " " in raw else ""
                    value = self.strip_optional_quest_word(value)
                    await self.accept_quest_from_context(value)
                    return

            for prefix in ("info ", "opis "):
                if norm.startswith(prefix):
                    value = raw.split(maxsplit=1)[1] if " " in raw else ""
                    await self.quest_info_from_context(value)
                    return

            for prefix in ("porzuc ", "porzuć ", "abandon ", "drop "):
                if norm.startswith(prefix):
                    value = raw.split(maxsplit=1)[1] if " " in raw else ""
                    await self.abandon_quest_from_context(value)
                    return

            for prefix in ("oddaj ", "turnin ", "zdaj "):
                if norm.startswith(prefix):
                    value = raw.split(maxsplit=1)[1] if " " in raw else ""
                    value = self.strip_optional_quest_word(value)
                    if value.isdigit():
                        quest_id, error = self.quest_id_for_turnin_number(value)
                    else:
                        quest_id, error = self.quest_from_context(value)
                    if error:
                        await self.send(error)
                        return
                    await self.turn_in_quest_id(quest_id)
                    return

            await self.send(
                "Questy: quest/questy — aktywne; quest godzinne — wszystkie odnawialne zlecenia godzinne; quest ukończone/questy ukończone — historia; "
                "quest list <NPC> — numerowana oferta; quest accept <numer> lub accept quest <numer> — przyjmij; "
                "quest info <numer> — szczegóły; quest oddaj <numer> lub oddaj quest <numer> — oddaj aktywny quest; "
                "quest porzuć <numer> — porzuć aktywne zadanie."
            )
