# -*- coding: utf-8 -*-
"""NPC chains, specialist quests, delivery and talk reactions."""

# v0.44.0: explicit dependencies; no compatibility-global injection.
from core.bootstrap_economy_professions import (
    PROFESSION_NPC_RANK_REACTIONS,
    PROFESSION_NPC_RANK_REACTION_ALIASES,
    PROFESSION_RANK_NAMES,
    profession_for_tool_type,
    profession_max_level,
    profession_npc_reaction_stage,
    profession_rank,
    profession_rank_name,
)
from core.mines_threat import ITEMS
from network.protocol_gameplay_utils import find_by_name, normalize_lookup_text
from systems.content_registry import NPCS, QUESTS
from systems.crafting_quality import player_item_display_name_v0335
from systems.professions import normalize_profession_name
from world.generation_systems import v0160_npcs_in_room


class SessionQuestNpcMixin:

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
                        reasons.append(f"wymaga {profession} poziom {minimum}")
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
                item_name = player_item_display_name_v0335(item_id)
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
            return f"Twoja ranga: {rank_name}, poziom {level}. {reaction}"

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
