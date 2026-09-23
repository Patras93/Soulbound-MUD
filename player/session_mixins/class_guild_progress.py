# -*- coding: utf-8 -*-
"""Class guild status, quests, exams and bounties."""
# v0.45.0: explicit imports; no compatibility-runtime injection.
from player.character import GUILD_REPUTATION_MAX, GUILD_REPUTATION_RANKS
from player.session_mixins.character_profile import currency_reading_text
from player.session_mixins.museum_bounty import v0914_combat_quest_stat_reward
from systems.equipment_crafting import GUILD_BOUNTY_TARGETS, GUILD_CLASS_QUESTS, GUILD_EXAM_REPUTATION, GUILD_EXAM_THRESHOLDS
from world.economy_quests import v0914_combat_quest_soul_reward


class SessionClassGuildProgressMixin:

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
                    lines.append(
                        f"{cls}: reputacja {rep}/{GUILD_REPUTATION_MAX}, ranga {rank[1]}, "
                        f"zniżka na naukę {discount}%, {next_text}, "
                        f"egzaminy: {', '.join(exams) if exams else 'brak'}."
                    )
                await self.send("\n".join(lines))
                return

            wanted = query.casefold()
            for cls in GUILD_CLASS_QUESTS:
                if cls.casefold() == wanted:
                    rep = self.character.guild_reputation(cls)
                    rank = self.character.guild_rep_rank(cls)
                    q = GUILD_CLASS_QUESTS[cls]
                    await self.send(
                        f"{cls}. Reputacja {rep}/{GUILD_REPUTATION_MAX}. Ranga: {rank[1]}. "
                        f"Zniżka na naukę: {int(rank[2]*100)}%. "
                        f"Zadanie klasowe: {q[0]}. {q[1]}"
                    )
                    return
            await self.send("Nie znam takiej klasy. Użyj: gildia info.")

    async def guild_class_quest(self, args=""):
            active = self.active_class_names()
            if not active:
                await self.send("Nie masz aktywnej klasy.")
                return
            cls = active[0]
            data = GUILD_CLASS_QUESTS.get(cls)
            if not data:
                await self.send("Ta klasa nie ma jeszcze zadania gildyjnego.")
                return

            states = self.character._guild_json("guild_class_quests_json")
            state = states.get(cls, {})
            if state is True:
                state = {"completed": True}
            if state.get("completed"):
                await self.send(f"Zadanie klasowe {cls} jest już ukończone.")
                return

            needed = int(data[4])
            if not state.get("accepted"):
                if self.character.soul_level < 25:
                    await self.send(f"{data[0]} wymaga Soul 25.")
                    return
                states[cls] = {"accepted": True, "progress": 0, "completed": False}
                self.character._set_guild_json("guild_class_quests_json", states)
                self.server.db.save_character(self.character)
                await self.send(f"Przyjęto zadanie: {data[0]}. {data[1]} Postęp 0 z {needed}.")
                return

            progress = int(state.get("progress", 0))
            if progress < needed:
                await self.send(f"{data[0]}. Postęp {progress} z {needed}. {data[1]}")
                return

            state["completed"] = True
            states[cls] = state
            self.character._set_guild_json("guild_class_quests_json", states)
            new_rep = self.character.add_guild_reputation(cls, data[2])
            self.character.silver += data[3]
            combat_quest = {
                "kind": "kill", "needed": needed, "required_soul_level": 25,
                "repeatable": False,
            }
            guild_stat_xp = v0914_combat_quest_stat_reward(combat_quest)
            await self.grant_combat_quest_stat_xp(
                guild_stat_xp, repeatable=False, source_label="Zadanie klasowe Gildii"
            )
            guild_soul_xp = v0914_combat_quest_soul_reward(combat_quest, self.character)
            await self.send(f"Zadanie klasowe Gildii: +{guild_soul_xp} Soul XP.")
            await self.grant_soul_xp(guild_soul_xp)
            self.server.db.save_character(self.character)
            await self.send(
                f"Ukończono zadanie klasowe: {data[0]}. "
                f"Reputacja {cls} +{data[2]}, waluta +" + currency_reading_text(data[3], 0, 0) + ". "
                f"Reputacja teraz {new_rep}/{GUILD_REPUTATION_MAX}."
            )

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
