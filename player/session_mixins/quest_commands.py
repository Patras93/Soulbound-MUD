# -*- coding: utf-8 -*-
"""Quest completion and player-facing quest commands."""
# v0.45.0: explicit imports; no compatibility-runtime injection.
from core.progression_resources import (
    v0190_quest_currency_reward,
    v0270_quest_character_reward,
    v0522_combat_quest_class_reward,
    v0522_is_profession_quest,
)
from player.session_mixins.dungeon_progression import v0874_quest_stat_progress_base_grant
from player.session_mixins.museum_bounty import v0914_combat_quest_stat_reward
from player.session_mixins.quest_npc import ITEMS, QUESTS, profession_for_tool_type
from player.session_mixins.shops_teachers import currency_reading_text
from world.economy_quests import v0914_combat_quest_soul_reward
from world.equipment_help import QUEST_REPEAT_COOLDOWN_SECONDS

from events.contracts import QuestCompletedEvent

class SessionQuestCommandsMixin:

    async def complete_quest(self, quest_id):
            q = QUESTS[quest_id]
            self.server.db.complete_quest(self.account_id, quest_id)
            self.cleanup_quest_map_artifacts_v0243(quest_id, allow_legacy_generic=False)
            self.server.db.add_lifetime_stat(self.account_id, "quests_completed", 1)
            try:
                self.server.db.record_activity_v0560(
                    self.account_id, "quest", str(q.get("name") or quest_id),
                    f"NPC: {q.get('giver', 'nieznany')}."
                )
            except Exception:
                pass

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
            is_combat_quest = str(q.get("kind") or "") in {"kill", "legendary_rare", "world_boss"}
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

            # v0.52.2: questy typu kill rozwijają także Biegłość aktywnych klas.
            # grant_class_xp zachowuje istniejące x2 EXP, bonus Gildii, Mentora
            # i podział puli pomiędzy aktywne klasy.
            reward_class_xp = v0522_combat_quest_class_reward(q) if is_combat_quest else 0
            if reward_class_xp:
                await self.send(f"Nagroda questa walki: {reward_class_xp} EXP Biegłości.")
                await self.grant_class_xp(reward_class_xp)

            # v0.52.2: progresja profesji/rzemiosł nie zasila już Broni Duszy.
            # Zwykłe questy nieprofesyjne zachowują dotychczasowy Soul XP.
            is_profession_quest = v0522_is_profession_quest(q)
            reward_soul_xp = 0 if is_profession_quest else v0914_combat_quest_soul_reward(q, self.character)
            if reward_soul_xp:
                await self.send(f"Nagroda questa: {reward_soul_xp} Soul XP.")
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

            # Extension point for achievements, chronicles or future systems.
            await self.server.events.publish(
                QuestCompletedEvent(session=self, quest_id=quest_id, quest=q)
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
