# -*- coding: utf-8 -*-
"""Quest lists, matching, turn-in and interaction flow."""

class SessionQuestTurninMixin:

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
            await self.send(f"AKTYWNE ZADANIA: {len(rows)}.")
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
            await self.send(f"UKOŃCZONE ZADANIA: {len(rows)}.")
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
