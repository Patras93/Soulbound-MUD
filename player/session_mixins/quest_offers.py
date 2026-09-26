# -*- coding: utf-8 -*-
"""Quest availability, NPC offers, accepting and abandoning."""
# v0.45.0: explicit imports; no compatibility-runtime injection.
import re
from core.progression_resources import v0190_quest_currency_reward, v0190_quest_soul_reward, v0190_quest_stat_reward, v0270_quest_character_reward
from player.session_mixins.character_profile import soul_trial_difficulty_band
from player.session_mixins.exp_terrain import QUESTS
from player.session_mixins.gathering import profession_for_tool_type
from player.session_mixins.inventory_equipment import V014_TREASURE_MAP_ITEM, player_item_display_name_v0335
from player.session_mixins.shops_teachers import ITEMS, NPCS, currency_reading_text, find_by_name
from systems.content_registry import HOURLY_QUEST_IDS
from systems.professions import normalize_profession_name
from world.equipment_help import QUEST_REPEAT_COOLDOWN_SECONDS


class SessionQuestOffersMixin:

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
                reasons.append(f"wymaga Soul Poziom {required_soul_level}")

            required_soul_tier = int(quest.get("required_soul_tier", 0) or 0)
            if required_soul_tier and self.character.soul_tier < required_soul_tier:
                reasons.append(f"wymaga Soul Tier {required_soul_tier}")

            tool_type = quest.get("specialist_tool_type")
            profession = quest.get("required_profession") or quest.get("reward_profession") or profession_for_tool_type(tool_type)
            min_prof = int(quest.get("min_profession_level", quest.get("min_tool_level", 0)) or 0)
            if profession and min_prof:
                prow = self.server.db.profession(self.account_id, profession)
                if int(prow["level"]) < min_prof:
                    reasons.append(f"wymaga {profession} poziom {min_prof}")

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

            await self.send(f"LISTA ZADAŃ: {npc['name']}. {len(quest_ids)} zadań.")
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

    async def accept_quest_id(self, quest_id, npc_id=None, _party_shared=False, _party_leader_name=None):
            """Przyjmij quest; lider automatycznie dzieli przyjęcie z lokalną drużyną.

            v0.36.1: jeśli wywołujący jest liderem drużyny, po własnym udanym
            przyjęciu ten sam quest jest przyjmowany niezależnie przez każdego
            żywego członka drużyny stojącego w tej samej lokacji. Każdy gracz
            zachowuje własny wpis 0/x, wymagania, cooldown, accept_items i progres.
            Wewnętrzny ``_party_shared`` zapobiega rekurencyjnemu ponownemu
            rozsyłaniu questa przez członków drużyny.
            """
            if self.combat_mob_key:
                if _party_shared and _party_leader_name:
                    await self.send(
                        f"Nie dołączasz do questa przyjmowanego przez {_party_leader_name}: "
                        "jesteś w walce."
                    )
                else:
                    await self.send("Nie możesz przyjmować questa podczas walki.")
                return False
            quest = QUESTS.get(quest_id)
            if not quest:
                await self.send("Nie znaleziono tego questa.")
                return False

            row = self.server.db.quest(self.account_id, quest_id)
            if row and row["status"] == "active":
                progress, ready = self.quest_progress_for_turnin(quest_id)
                suffix = " Cel wykonany." if ready else ""
                await self.send(
                    f"Quest już aktywny: {quest['name']}. "
                    f"Postęp {progress} z {quest['needed']}.{suffix}"
                )
                return False

            if row and row["status"] == "completed":
                if not quest.get("repeatable"):
                    await self.send(f"Quest {quest['name']} jest już ukończony.")
                    return False
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
                    return False

            reasons = self.quest_lock_reasons(quest_id)
            if reasons:
                await self.send(
                    f"Nie możesz jeszcze przyjąć questa {quest['name']}: "
                    + ", ".join(reasons)
                    + "."
                )
                return False

            repeated = bool(row and row["status"] in ("completed", "abandoned"))
            accept_npc = self.quest_accept_npc_name_v099(quest_id, npc_id)
            if _party_shared and _party_leader_name:
                await self.send(
                    f"Lider {_party_leader_name} przyjmuje dla drużyny quest: {quest['name']}."
                )
            else:
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

            # v0.36.1: tylko faktyczny lider rozsyła przyjęcie dalej i tylko
            # po własnym poprawnym przyjęciu. Osoby w innym pokoju, offline lub
            # martwe nie dostają questa. Każdy odbiorca przechodzi własne
            # wymagania questa/cooldown i zaczyna z własnym postępem 0/x.
            if not _party_shared:
                party_key = self.server.party_key_for_account(self.account_id)
                if party_key is not None and int(party_key) == int(self.account_id):
                    recipients = [
                        session
                        for session in self.server.party_sessions(
                            self.account_id, same_room=self.character.room_id
                        )
                        if session is not self
                        and session.character
                        and not session.closed
                        and int(getattr(session, "current_hp", 0) or 0) > 0
                    ]
                    accepted_names = []
                    skipped_names = []
                    for member in sorted(
                        recipients, key=lambda session: session.character.name.lower()
                    ):
                        accepted = await member.accept_quest_id(
                            quest_id,
                            npc_id=npc_id,
                            _party_shared=True,
                            _party_leader_name=self.character.name,
                        )
                        if accepted:
                            accepted_names.append(member.character.name)
                        else:
                            skipped_names.append(member.character.name)
                    if accepted_names:
                        await self.send(
                            "Quest przyjęła razem z tobą drużyna: "
                            + ", ".join(accepted_names)
                            + "."
                        )
                    if skipped_names:
                        await self.send(
                            "Nie wszyscy mogli przyjąć ten quest. Pominięto: "
                            + ", ".join(skipped_names)
                            + "."
                        )
            return True

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

            await self.send(f"INFORMACJE O ZADANIU: {quest['name']}.")
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
                requirements.append(f"{profession} poziom {min_profession}")
            if quest.get("required_soul_level"):
                requirements.append(f"Soul Poziom {quest['required_soul_level']}")
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
                item_name = player_item_display_name_v0335(item_id)
                reward_parts.append(f"{item_name} x{qty}")
            if quest.get("reward_profession_xp"):
                reward_parts.append(
                    f"{quest.get('reward_profession', 'profesja')} XP {quest['reward_profession_xp']}"
                )
            if quest.get("reward_tool_xp"):
                reward_parts.append(f"XP narzędzia {quest['reward_tool_xp']}")
            generated_character = v0270_quest_character_reward(quest)
            if generated_character:
                reward_parts.append(f"EXP postaci {generated_character}")
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
            cache = getattr(type(self).cleanup_quest_map_artifacts_v0243, "_map_ids_v0717", None)
            if not isinstance(cache, tuple) or cache[0] != len(ITEMS):
                grouped = {}
                for item_id, item in ITEMS.items():
                    owner = item.get("quest_treasure_map_for")
                    if owner:
                        grouped.setdefault(str(owner), []).append(item_id)
                cache = (len(ITEMS), {key: tuple(values) for key, values in grouped.items()})
                type(self).cleanup_quest_map_artifacts_v0243._map_ids_v0717 = cache
            quest_map_ids = cache[1].get(str(quest_id), ())
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
