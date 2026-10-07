# -*- coding: utf-8 -*-
"""Class guild status, quests, exams and bounties."""
# v0.45.0: explicit imports; no compatibility-runtime injection.
import time

from player.character import GUILD_REPUTATION_MAX, GUILD_REPUTATION_RANKS
from player.session_mixins.character_profile import currency_reading_text
from player.session_mixins.museum_bounty import v0914_combat_quest_stat_reward
from systems.equipment_crafting import (
    GUILD_BOUNTY_TARGETS,
    GUILD_CLASS_QUEST_POOLS,
    GUILD_CLASS_QUESTS,
    GUILD_EXAM_REPUTATION,
    GUILD_EXAM_THRESHOLDS,
    guild_class_quest_pool_for_mastery_v11342,
    guild_class_quest_stage_v11342,
)
from world.economy_quests import v0914_combat_quest_soul_reward


class SessionClassGuildProgressMixin:

    def class_guild_quest_hour_slot_v1120(self, now=None):
        now = time.time() if now is None else float(now)
        return int(now // 3600)

    def class_guild_quest_refresh_seconds_v1120(self, now=None):
        now = time.time() if now is None else float(now)
        remaining = 3600 - (int(now) % 3600)
        return max(1, remaining)

    def class_guild_mastery_level_v11342(self, class_name):
        row = self.server.db.class_progress_row(self.account_id, class_name)
        return max(1, int(row["level"])) if row else 1

    def class_guild_quest_pool_v11342(self, class_name, state=None):
        if state is None:
            _states, state = self.class_guild_quest_state_v1120(class_name)
        mastery = max(1, int((state or {}).get("mastery_level", 1) or 1))
        return tuple(guild_class_quest_pool_for_mastery_v11342(class_name, mastery))

    def class_guild_quest_order_v1120(self, class_name, slot=None):
        pool = tuple(GUILD_CLASS_QUEST_POOLS.get(class_name, ()))
        if not pool:
            return ()
        slot = self.class_guild_quest_hour_slot_v1120() if slot is None else int(slot)
        classes = tuple(GUILD_CLASS_QUEST_POOLS)
        class_index = classes.index(class_name) if class_name in classes else 0
        offset = (slot + class_index) % len(pool)
        order = tuple(range(len(pool)))
        order = order[offset:] + order[:offset]
        return tuple((index, pool[index]) for index in order)

    def class_guild_quest_state_v1120(self, class_name):
        """Return current hourly state and migrate old one-quest saves in place."""
        states = self.character._guild_json("guild_class_quests_json")
        raw = states.get(class_name, {})
        slot = self.class_guild_quest_hour_slot_v1120()
        changed = False

        if raw is True:
            raw = {"completed": True, "ever_completed": True}
            changed = True
        if not isinstance(raw, dict):
            raw = {}
            changed = True

        old_quests = raw.get("quests") if isinstance(raw.get("quests"), dict) else {}
        ever_completed = bool(raw.get("ever_completed") or raw.get("completed"))
        if any(bool(value.get("completed")) for value in old_quests.values() if isinstance(value, dict)):
            ever_completed = True

        if "slot" not in raw:
            # v1.11.x stored one flat quest per class. Preserve its progress as
            # the first (legacy-compatible) quest in the new hourly pool.
            quest_rows = {}
            old_progress = max(0, int(raw.get("progress", 0) or 0))
            old_completed = bool(raw.get("completed"))
            if raw.get("accepted") or old_progress or old_completed:
                quest_rows["0"] = {
                    "progress": old_progress,
                    "completed": old_completed,
                }
            state = {
                "slot": slot,
                "active": 0 if raw.get("accepted") and not old_completed else None,
                "quests": quest_rows,
                "ever_completed": ever_completed,
                # Existing in-progress legacy task keeps base difficulty until
                # the next hourly refresh instead of changing under the player.
                "mastery_level": 1,
            }
            changed = True
        elif int(raw.get("slot", -1)) != slot:
            state = {
                "slot": slot,
                "active": None,
                "quests": {},
                "ever_completed": ever_completed,
                "mastery_level": self.class_guild_mastery_level_v11342(class_name),
            }
            changed = True
        else:
            state = dict(raw)
            state["slot"] = slot
            state["ever_completed"] = ever_completed
            if "mastery_level" not in state:
                # First hour after upgrade: preserve current task numbers.
                state["mastery_level"] = 1 if (
                    state.get("active") is not None or state.get("quests")
                ) else self.class_guild_mastery_level_v11342(class_name)
                changed = True
            if not isinstance(state.get("quests"), dict):
                state["quests"] = {}
                changed = True
            active = state.get("active")
            if active is not None:
                try:
                    active = int(active)
                except (TypeError, ValueError):
                    active = None
                if active is None or not (0 <= active < len(GUILD_CLASS_QUEST_POOLS.get(class_name, ()))):
                    active = None
                if state.get("active") != active:
                    state["active"] = active
                    changed = True

        if changed:
            states[class_name] = state
            self.character._set_guild_json("guild_class_quests_json", states)
            self.server.db.save_character(self.character)
        return states, state

    async def advance_class_guild_quest_v11132(self, activity, amount=1):
        active = self.active_class_names()
        if not active:
            return False
        cls = active[0]
        states, state = self.class_guild_quest_state_v1120(cls)
        pool = self.class_guild_quest_pool_v11342(cls, state)
        if not pool:
            return False

        active_index = state.get("active")
        if active_index is None:
            return False
        try:
            active_index = int(active_index)
            data = pool[active_index]
        except (TypeError, ValueError, IndexError):
            return False
        if str(data[5]) != str(activity):
            return False

        quests = state.setdefault("quests", {})
        qstate = quests.setdefault(str(active_index), {"progress": 0, "completed": False})
        if qstate.get("completed"):
            return False

        needed = int(data[4])
        old = int(qstate.get("progress", 0) or 0)
        new = min(needed, old + max(0, int(amount)))
        if new <= old:
            return False

        qstate["progress"] = new
        states[cls] = state
        self.character._set_guild_json("guild_class_quests_json", states)
        self.server.db.save_character(self.character)
        if new >= needed:
            await self.send(
                f"Zadanie Gildii {data[0]}: {new} z {needed}. "
                "Cel wykonany. Użyj zadanieklasowe, aby odebrać nagrodę."
            )
        else:
            await self.send(f"Zadanie Gildii {data[0]}: {new} z {needed}.")
        return True

    async def show_guild(self, args=""):
        active = list(getattr(self.character, "classes", []) or [])
        if not active and getattr(self.character, "class_name", None):
            active = [self.character.class_name]
        query = (args or "").strip()
        if not query or query.lower() in ("info", "status", "stan"):
            lines = ["Gildia klasowa:"]
            for cls in active:
                rep = self.character.guild_reputation(cls)
                rank = self.character.guild_rep_rank(cls)
                discount = int(round(self.character.guild_training_discount(cls) * 100))
                exams = [str(t) for t in GUILD_EXAM_THRESHOLDS if self.character.guild_exam_done(cls, t)]
                next_rank = next((r for r in GUILD_REPUTATION_RANKS if r[0] > rep), None)
                next_text = f"następna ranga przy {next_rank[0]}" if next_rank else "maksymalna ranga"
                quest_count = len(GUILD_CLASS_QUEST_POOLS.get(cls, ()))
                lines.append(
                    f"{cls}: reputacja {rep}/{GUILD_REPUTATION_MAX}, ranga {rank[1]}, "
                    f"zniżka na naukę {discount}%, {next_text}, "
                    f"egzaminy: {', '.join(exams) if exams else 'brak'}, "
                    f"zadania godzinne: {quest_count}."
                )
            lines.append("Zadania aktywnej klasy: zadanieklasowe.")
            await self.send("\n".join(lines))
            return

        wanted = query.casefold()
        for cls in GUILD_CLASS_QUEST_POOLS:
            if cls.casefold() == wanted:
                rep = self.character.guild_reputation(cls)
                rank = self.character.guild_rep_rank(cls)
                await self.send(
                    f"{cls}. Reputacja {rep}/{GUILD_REPUTATION_MAX}. Ranga: {rank[1]}. "
                    f"Zniżka na naukę: {int(rank[2]*100)}%. "
                    f"Zadania klasowe: {len(GUILD_CLASS_QUEST_POOLS[cls])} różnych ofert, "
                    "odnawianych co godzinę i skalowanych z Biegłością klasy. "
                    "Dla aktywnej klasy użyj zadanieklasowe."
                )
                return
        await self.send("Nie znam takiej klasy. Użyj: gildia info.")

    async def guild_class_quest(self, args=""):
        active = self.active_class_names()
        if not active:
            await self.send("Nie masz aktywnej klasy.")
            return
        cls = active[0]
        states, state = self.class_guild_quest_state_v1120(cls)
        pool = self.class_guild_quest_pool_v11342(cls, state)
        if not pool:
            await self.send("Ta klasa nie ma jeszcze zadań gildyjnych.")
            return

        ordered = self.class_guild_quest_order_v1120(cls, state["slot"])
        raw = (args or "").strip()
        norm = raw.casefold()
        quests = state.setdefault("quests", {})

        async def send_list():
            refresh_seconds = self.class_guild_quest_refresh_seconds_v1120()
            refresh_minutes = max(1, (refresh_seconds + 59) // 60)
            mastery = max(1, int(state.get("mastery_level", 1) or 1))
            _threshold, stage_label, _effort, _reward = guild_class_quest_stage_v11342(
                mastery
            )
            await self.send(
                f"ZADANIA KLASOWE — {cls}. Etap: {stage_label}, "
                f"Biegłość {mastery}. Pięć różnych ofert w tym cyklu. "
                f"Etap i wymagania są stałe do odnowienia za około "
                f"{refresh_minutes} min."
            )
            active_index = state.get("active")
            for number, (quest_index, data) in enumerate(ordered, 1):
                qstate = quests.get(str(quest_index), {})
                progress = int(qstate.get("progress", 0) or 0)
                needed = int(data[4])
                if qstate.get("completed"):
                    status = "UKOŃCZONE"
                elif active_index == quest_index:
                    status = f"AKTYWNE {progress}/{needed}"
                elif progress:
                    status = f"wstrzymane {progress}/{needed}"
                else:
                    status = "dostępne"
                await self.send(
                    f"{number}. {data[0]}. {data[1]} "
                    f"Typ: {data[5]}. Status: {status}. "
                    f"Nagroda: reputacja +{data[2]}, waluta +"
                    + currency_reading_text(data[3], 0, 0) + "."
                )
            await self.send(
                "Przyjęcie: zadanieklasowe <numer>. "
                "Status/odbiór aktywnego: zadanieklasowe. "
                "Zmiana zadania: zadanieklasowe porzuc, potem wybierz numer."
            )

        if norm in ("lista", "list", "oferty", "offers"):
            await send_list()
            return

        if norm in ("porzuc", "porzuć", "abandon"):
            active_index = state.get("active")
            if active_index is None:
                await self.send("Nie masz aktywnego zadania klasowego.")
                return
            state["active"] = None
            states[cls] = state
            self.character._set_guild_json("guild_class_quests_json", states)
            self.server.db.save_character(self.character)
            await self.send(
                "Wstrzymano aktywne zadanie klasowe. Postęp pozostaje zapisany do końca bieżącej godziny."
            )
            return

        if raw:
            try:
                display_index = int(raw) - 1
            except ValueError:
                await self.send(
                    "Użycie: zadanieklasowe, zadanieklasowe lista, "
                    "zadanieklasowe <numer> albo zadanieklasowe porzuc."
                )
                return
            if display_index < 0 or display_index >= len(ordered):
                await self.send(f"Dostępne numery: 1-{len(ordered)}.")
                return
            quest_index, data = ordered[display_index]
            qstate = quests.setdefault(str(quest_index), {"progress": 0, "completed": False})
            if qstate.get("completed"):
                await self.send(
                    f"{data[0]} jest już ukończone w tym cyklu godzinnym. Wybierz inne zadanie."
                )
                return
            current_active = state.get("active")
            if current_active is not None and int(current_active) != int(quest_index):
                await self.send(
                    "Masz już inne aktywne zadanie klasowe. "
                    "Użyj zadanieklasowe porzuc, aby przełączyć się bez kasowania postępu."
                )
                return
            if self.character.soul_level < 25:
                await self.send(f"{data[0]} wymaga Soul 25.")
                return
            state["active"] = int(quest_index)
            states[cls] = state
            self.character._set_guild_json("guild_class_quests_json", states)
            self.server.db.save_character(self.character)
            await self.send(
                f"Przyjęto zadanie: {data[0]}. {data[1]} "
                f"Postęp {int(qstate.get('progress', 0) or 0)} z {int(data[4])}."
            )
            return

        active_index = state.get("active")
        if active_index is None:
            await send_list()
            return

        active_index = int(active_index)
        data = pool[active_index]
        qstate = quests.setdefault(str(active_index), {"progress": 0, "completed": False})
        needed = int(data[4])
        progress = int(qstate.get("progress", 0) or 0)

        if qstate.get("completed"):
            state["active"] = None
            states[cls] = state
            self.character._set_guild_json("guild_class_quests_json", states)
            self.server.db.save_character(self.character)
            await send_list()
            return

        if progress < needed:
            refresh_seconds = self.class_guild_quest_refresh_seconds_v1120()
            refresh_minutes = max(1, (refresh_seconds + 59) // 60)
            await self.send(
                f"{data[0]}. Postęp {progress} z {needed}. {data[1]} "
                f"Odnowienie cyklu za około {refresh_minutes} min."
            )
            return

        qstate["completed"] = True
        state["active"] = None
        state["ever_completed"] = True
        states[cls] = state
        self.character._set_guild_json("guild_class_quests_json", states)

        new_rep = self.character.add_guild_reputation(cls, data[2])
        self.character.silver += data[3]
        objective_kind = str(data[5])
        combat_quest = {
            "kind": "kill" if objective_kind in ("kill", "boss") else objective_kind,
            "needed": needed,
            "required_soul_level": 25,
            "repeatable": True,
        }
        guild_stat_xp = v0914_combat_quest_stat_reward(combat_quest)
        await self.grant_combat_quest_stat_xp(
            guild_stat_xp, repeatable=True, source_label="Godzinne zadanie klasowe Gildii"
        )
        guild_soul_xp = v0914_combat_quest_soul_reward(combat_quest, self.character)
        await self.send(f"Zadanie klasowe Gildii: +{guild_soul_xp} Soul XP.")
        await self.grant_soul_xp(guild_soul_xp)
        self.server.db.save_character(self.character)

        completed_count = sum(
            1 for value in quests.values()
            if isinstance(value, dict) and value.get("completed")
        )
        await self.send(
            f"Ukończono zadanie klasowe: {data[0]}. "
            f"Reputacja {cls} +{data[2]}, waluta +"
            + currency_reading_text(data[3], 0, 0) + ". "
            f"Reputacja teraz {new_rep}/{GUILD_REPUTATION_MAX}. "
            f"W tej godzinie ukończono {completed_count} z {len(pool)} zadań."
        )
        if completed_count < len(pool):
            await self.send("Możesz od razu wybrać kolejne: zadanieklasowe.")
        else:
            await self.send("Wszystkie pięć zadań tej klasy ukończone w bieżącej godzinie.")

    async def guild_exam(self, args=""):
            raw = (args or "").strip()
            active = list(getattr(self.character, "classes", []) or [])
            if not active and getattr(self.character, "class_name", None):
                active = [self.character.class_name]
            if not active:
                await self.send("Nie masz aktywnej klasy.")
                return
            cls = active[0]

            if not raw:
                states = []
                for threshold in GUILD_EXAM_THRESHOLDS:
                    state = "zdany" if self.character.guild_exam_done(cls, threshold) else "niezdany"
                    states.append(
                        f"Soul {threshold}: {state}, wymagana reputacja {GUILD_EXAM_REPUTATION[threshold]}"
                    )
                await self.send(f"Egzaminy {cls}. " + ". ".join(states) + ".")
                return

            try:
                threshold = int(raw.split()[0])
            except Exception:
                await self.send("Użycie: egzamin 50, egzamin 100, egzamin 150 lub egzamin 200.")
                return
            if threshold not in GUILD_EXAM_THRESHOLDS:
                await self.send("Dostępne egzaminy: 50, 100, 150, 200.")
                return
            if self.character.guild_exam_done(cls, threshold):
                await self.send(f"Egzamin Soul {threshold} jest już zdany.")
                return
            if getattr(self.character, "soul_level", 1) < threshold:
                await self.send(f"Ten egzamin wymaga Soul {threshold}.")
                return

            if threshold == 50 and not self.character.guild_class_quest_done(cls):
                await self.send("Najpierw ukończ zadanie klasowe Gildii: zadanieklasowe.")
                return

            required_rep = GUILD_EXAM_REPUTATION[threshold]
            current_rep = self.character.guild_reputation(cls)
            if current_rep < required_rep:
                await self.send(
                    f"Egzamin Soul {threshold} wymaga reputacji {required_rep} w klasie {cls}. "
                    f"Masz {current_rep}. Wykonuj guildbounty i zadania Gildii."
                )
                return

            # Require previous exam except first.
            idx = GUILD_EXAM_THRESHOLDS.index(threshold)
            if idx > 0 and not self.character.guild_exam_done(cls, GUILD_EXAM_THRESHOLDS[idx-1]):
                await self.send(f"Najpierw zdaj egzamin Soul {GUILD_EXAM_THRESHOLDS[idx-1]}.")
                return

            # v0.8.61: koszt egzaminu skaluje się z nową ekonomią jednego salda.
            total_silver_cost = {
                50: 100_000,       # 100 złota
                100: 2_000_000,    # 2 000 złota
                150: 50_000_000,   # 50 000 złota
                200: 250_000_000,  # 250 000 złota
            }[threshold]
            if not self.pay_training_cost(total_silver_cost):
                await self.send(f"Egzamin Soul {threshold} kosztuje " + currency_reading_text(total_silver_cost, 0, 0) + ". Nie masz wystarczającej ilości pieniędzy.")
                return

            self.character.mark_guild_exam_done(cls, threshold)
            reward_rep = {50: 75, 100: 125, 150: 175, 200: 250}[threshold]
            rep = self.character.add_guild_reputation(cls, reward_rep)
            self.server.db.save_character(self.character)
            await self.send(
                f"Zdano egzamin {cls} Soul {threshold}. "
                "Koszt " + currency_reading_text(total_silver_cost, 0, 0) + f". Reputacja +{reward_rep}. "
                f"Reputacja teraz {rep}/{GUILD_REPUTATION_MAX}."
            )

    async def guild_bounty(self, args=""):
            arg = (args or "").strip().casefold()
            state = self.character.guild_bounty_state()
            current = state.get("target")

            if not arg or arg in ("info", "status"):
                if current:
                    target = next((x for x in GUILD_BOUNTY_TARGETS if x[0] == current), None)
                    if target:
                        await self.send(
                            f"Aktywne zlecenie: {target[1]}. "
                            f"Nagroda: reputacja +{target[2]}, waluta +" + currency_reading_text(target[3], 0, 0) + ". "
                            f"Po zabiciu celu użyj: guildbounty odbierz."
                        )
                        return
                lines = ["Tablica zleceń Gildii:"]
                for i, row in enumerate(GUILD_BOUNTY_TARGETS, 1):
                    lines.append(f"{i}. {row[1]} — reputacja +{row[2]}, waluta +" + currency_reading_text(row[3], 0, 0) + ".")
                lines.append("Użyj: guildbounty <numer>.")
                await self.send("\n".join(lines))
                return

            if arg in ("odbierz", "claim"):
                if not current:
                    await self.send("Nie masz aktywnego zlecenia.")
                    return
                # Track kill if generic kill history exists; otherwise allow claim only if marked externally.
                completed = bool(state.get("completed", False))
                if not completed:
                    await self.send("Cel zlecenia nie został jeszcze pokonany.")
                    return
                target = next((x for x in GUILD_BOUNTY_TARGETS if x[0] == current), None)
                if not target:
                    await self.send("To zlecenie jest nieprawidłowe.")
                    return
                active = list(getattr(self.character, "classes", []) or [])
                if not active and getattr(self.character, "class_name", None):
                    active = [self.character.class_name]
                cls = active[0] if active else "Wojownik"
                rep = self.character.add_guild_reputation(cls, target[2])
                self.character.silver += target[3]
                combat_quest = {
                    "kind": "kill", "target": target[0], "needed": 1,
                    "repeatable": True,
                }
                guild_stat_xp = v0914_combat_quest_stat_reward(combat_quest)
                await self.grant_combat_quest_stat_xp(
                    guild_stat_xp, repeatable=True, source_label="Zlecenie bojowe Gildii"
                )
                guild_soul_xp = v0914_combat_quest_soul_reward(combat_quest, self.character)
                await self.send(f"Zlecenie bojowe Gildii: +{guild_soul_xp} Soul XP.")
                await self.grant_soul_xp(guild_soul_xp)
                self.character.set_guild_bounty_state({})
                self.server.db.save_character(self.character)
                await self.send(
                    f"Odebrano nagrodę za {target[1]}. "
                    f"Reputacja {cls} +{target[2]}, waluta +" + currency_reading_text(target[3], 0, 0) + ". "
                    f"Reputacja teraz {rep}/{GUILD_REPUTATION_MAX}."
                )
                return

            try:
                idx = int(arg) - 1
            except Exception:
                await self.send("Użycie: guildbounty, guildbounty <numer>, guildbounty odbierz.")
                return
            if idx < 0 or idx >= len(GUILD_BOUNTY_TARGETS):
                await self.send("Nie ma takiego numeru zlecenia.")
                return
            target = GUILD_BOUNTY_TARGETS[idx]
            self.character.set_guild_bounty_state({
                "target": target[0],
                "completed": False,
            })
            self.server.db.save_character(self.character)
            await self.send(
                f"Przyjęto zlecenie: {target[1]}. "
                f"Nagroda: reputacja +{target[2]}, waluta +" + currency_reading_text(target[3], 0, 0) + "."
            )
