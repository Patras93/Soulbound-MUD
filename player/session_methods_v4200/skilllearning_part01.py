# -*- coding: utf-8 -*-
"""Original Soulbound session/DB method bodies, source-preserving extraction.
Globals are bound to the historical host module at class initialization.
"""
async def unlock(self):
        if self.character.soul_tier >= SOUL_MAX_TIER:
            await self.send(
                f"Broń Duszy ma już maksymalny Tier {SOUL_MAX_TIER}."
            )
            return

        next_tier = self.character.soul_tier + 1
        needed_level = SOUL_TIER_THRESHOLDS[next_tier - 1]
        if self.character.soul_level < needed_level:
            await self.send(
                f"Tier {next_tier} wymaga Soul Level {needed_level}. "
                f"Masz Soul Level {self.character.soul_level}."
            )
            return

        required_quest = SOUL_TRIAL_QUEST_IDS.get(next_tier)
        if required_quest and not self.soul_tier_quest_completed(next_tier):
            await self.send(
                f"Masz wymagany Soul Level, ale Tier {next_tier} wymaga jeszcze "
                f"zadania {QUESTS[required_quest]['name']}. "
                "Idź do Kapłana Elora w Świątyni Odrodzenia."
            )
            return

        self.character.soul_tier = next_tier
        self.server.db.save_character(self.character)
        tier_title = soul_tier_title_for_class(next_tier, self.character.class_name)
        await self.send(
            f"Odblokowano Soul Tier {next_tier} z {SOUL_MAX_TIER}: {tier_title}. "
            f"Moc Broni Duszy: {self.character.soul_power()}."
        )
        # v0.36.8: odblokowanie Soul Tieru jest wydarzeniem lokalnym.
        # Każdy gracz stojący w dokładnie tej samej lokacji dostaje krótką
        # informację, niezależnie od członkostwa w drużynie. Właściciel
        # Tieru ma już pełny komunikat powyżej, więc jest wykluczony z
        # broadcastu, aby NVDA nie czytał awansu dwa razy.
        await self.server.broadcast_room(
            self.character.room_id,
            f"{self.character.name} odblokował Soul Tier {next_tier}: {tier_title}.",
            exclude=self,
            history_category="system",
        )
        await self.send(
            f"Nowy bonus klasowy Broni Duszy: "
            f"{self.character.soul_weapon_class_bonus_text()}."
        )
        trait = soul_weapon_trait_for_tier_v11193(next_tier, self.character.class_name)
        if trait:
            await self.send(
                f"Nowa właściwość Broni Duszy: {trait['name']}. {trait['description']}."
            )
        if next_tier in SOUL_MILESTONE_TIERS:
            await self.send(
                "KAMIEŃ MILOWY. " + self.soul_milestone_text(next_tier)
            )
        if next_tier < SOUL_MAX_TIER:
            await self.send(self.soul_next_goal_text())


async def handle_job_set(self, raw):
        parts=str(raw or "").strip().split(maxsplit=2)
        if len(parts)<2 or parts[0].casefold()!="set":
            await self.send("Użycie: job set inherent <nazwa> albo job set counter <nazwa>.")
            return
        slot=parts[1].casefold()
        if slot not in ("inherent","counter"):
            await self.send("Dostępne sloty job: inherent, counter.")
            return
        if len(parts)<3:
            current=self.selected_job_ability(slot)
            await self.send(f"{slot}: {current['name'] if current else 'brak'}.")
            return
        wanted=parts[2].strip()
        # UOSS source syntax includes the job name, e.g.
        # "job set counter mec Intercept System". Soulbound also accepts
        # the shorter "job set counter Intercept System".
        if wanted.casefold().startswith("mec "):
            wanted=wanted[4:].strip()
        if wanted.casefold() in ("none","brak","off","wyłącz","wylacz"):
            self.server.db.clear_job_ability_slot(self.account_id,slot)
            await self.send(f"Slot {slot} wyłączony.")
            return
        skill,_target=self.find_skill_from_input(wanted)
        if not skill or str(skill.get("mec_role","")).casefold()!=slot:
            await self.send(f"Nie znajduję nauczonej umiejętności typu {slot} o tej nazwie.")
            return
        if not self.server.db.knows_skill(self.account_id,skill["id"]):
            await self.send(f"Najpierw naucz się: {skill['name']}.")
            return
        if not self.skill_mastery_unlocked(skill):
            await self.send(f"Nie spełniasz jeszcze wymagań: {skill['name']}.")
            return
        self.server.db.set_job_ability_slot(self.account_id,slot,skill["id"])
        await self.send(f"Ustawiono {slot}: {skill['name']}.")


def natural_skill_from_input(self, raw):
        raw = str(raw or "").strip()
        normalized = self.normalized_skill_text(raw)
        if not normalized:
            return None, ""

        words = normalized.split()
        raw_words = raw.split()

        # Naturalny intent jest pierwszym słowem.
        intent = words[0]
        spec = NATURAL_SKILL_INTENTS.get(intent)
        if not spec:
            return None, ""

        known = self.server.db.learned_skill_ids(self.account_id)
        candidates = []

        for skill in self.class_skills():
            if skill["id"] not in known:
                continue
            if not self.skill_mastery_unlocked(skill):
                continue

            kinds = spec.get("kinds")
            if kinds and skill.get("kind") not in kinds:
                continue

            wanted_tags = spec.get("tags")
            if wanted_tags:
                tokens = self.skill_natural_tokens(skill)
                if not tokens.intersection(wanted_tags):
                    continue

            progress = self.server.db.skill_progress(
                self.account_id, skill["id"]
            )
            score = (
                int(skill["unlock"]),
                int(progress["level"]),
            )
            candidates.append((score, skill))

        if not candidates:
            return None, ""

        candidates.sort(key=lambda entry: entry[0], reverse=True)
        best_score = candidates[0][0]
        best = [
            skill
            for score, skill in candidates
            if score == best_score
        ]

        # Przy remisie nie wybieramy losowo pomiędzy multiclassami.
        if len(best) != 1:
            return None, ""

        target = " ".join(raw_words[1:]) if len(raw_words) > 1 else ""
        return best[0], target


def find_skill_from_input(self, raw):
        skills = self.class_skills()
        raw = raw.strip()
        if not raw:
            return None, ""

        first = raw.split(maxsplit=1)
        if first[0].isdigit():
            number = int(first[0])
            if 1 <= number <= len(skills):
                return (
                    skills[number - 1],
                    first[1] if len(first) > 1 else "",
                )

        normalized = self.normalized_skill_text(raw)
        matches = []

        # Najpierw pełne nazwy, ID i oficjalne aliasy.
        for skill in skills:
            for name in [skill["name"], skill["id"]] + skill.get("aliases", []):
                n = self.normalized_skill_text(name)
                if normalized == n:
                    matches.append((len(n), skill, ""))
                elif normalized.startswith(n + " "):
                    word_count = len(name.split())
                    target = " ".join(raw.split()[word_count:])
                    matches.append((len(n), skill, target))

        if matches:
            matches.sort(key=lambda x: x[0], reverse=True)
            return matches[0][1], matches[0][2]

        # Naturalne intencje, np. heal, tarcza, ogien, ciecie, pocisk.
        natural_skill, natural_target = self.natural_skill_from_input(raw)
        if natural_skill:
            return natural_skill, natural_target

        # Fallback: krótka nazwa po fragmencie pełnej nazwy/aliasu,
        # ale tylko jeśli wskazuje dokładnie jeden skill.
        shortcut_matches = {}
        raw_words = raw.split()

        for skill in skills:
            shortcuts = set()
            names = [skill["name"]] + skill.get("aliases", [])
            for name in names:
                n = self.normalized_skill_text(name)
                words = n.split()
                if not words:
                    continue

                shortcuts.update(words)

                for count in range(1, len(words)):
                    shortcuts.add(" ".join(words[:count]))
                    shortcuts.add(" ".join(words[count:]))

            shortcuts.difference_update({
                "maly", "male", "wielki", "wielkie", "cios",
                "uderzenie", "bariera", "duszy", "krwi",
                "umyslu", "energii",
            })

            for shortcut in shortcuts:
                if normalized == shortcut:
                    target = ""
                elif normalized.startswith(shortcut + " "):
                    word_count = len(shortcut.split())
                    target = " ".join(raw_words[word_count:])
                else:
                    continue

                shortcut_matches.setdefault(skill["id"], []).append(
                    (len(shortcut), skill, target)
                )

        if len(shortcut_matches) != 1:
            return None, ""

        only_matches = next(iter(shortcut_matches.values()))
        only_matches.sort(key=lambda x: x[0], reverse=True)
        return only_matches[0][1], only_matches[0][2]


def class_codex_class_name(self, query):
        value = self.normalize_description_query(query or "")
        if not value:
            return None
        english = {
            "warrior": "Wojownik",
            "berserker": "Berserker",
            "rogue": "Łotrzyk",
            "hunter": "Łowca",
            "monk": "Mnich",
            "guardian": "Strażnik",
            "mage": "Mag",
            "necromancer": "Nekromanta",
            "priest": "Kapłan",
            "cleric": "Kapłan",
            "warlock": "Czarownik",
            "druid": "Druid",
            "psionic": "Psionik",
            "psion": "Psionik",
        }
        if value in english:
            return english[value]
        return self.find_class_name(query)


async def show_class_codex(self, args=""):
        """NVDA-friendly class skill codex with teacher, Soul requirement and current price."""
        raw = (args or "").strip()
        normalized = self.normalize_description_query(raw)
        all_classes = [row[0] for row in CLASSES]
        active = self.active_class_names()
        learned = self.server.db.learned_skill_ids(self.account_id)

        if normalized in ("", "info", "pomoc", "help"):
            await self.send(
                "CODEX KLASOWY. Użycie: kodeksklasowy <klasa>, "
                "kodeksklasowy moje albo kodeksklasowy wszystkie. "
                "English: classcodex <class>, classcodex mine, classcodex all."
            )
            await self.send("Klasy: " + ", ".join(all_classes) + ".")
            return

        if normalized in ("moje", "mine", "my", "aktywne", "active"):
            classes = list(active)
        elif normalized in ("wszystkie", "all", "pełny", "pelny", "full"):
            classes = list(all_classes)
        else:
            class_name = self.class_codex_class_name(raw)
            if not class_name:
                await self.send(
                    "Nie rozpoznaję klasy. Użyj kodeksklasowy info, aby usłyszeć listę klas."
                )
                return
            classes = [class_name]

        if not classes:
            await self.send("Nie masz aktywnej klasy do pokazania.")
            return

        for class_name in classes:
            teacher_id, teacher = self.class_teacher(class_name)
            teacher_name = teacher["name"] if teacher else "brak nauczyciela"
            teacher_room = (
                ROOMS[teacher["room"]]["name"]
                if teacher and teacher.get("room") in ROOMS
                else "nieznana lokacja"
            )
            rep = self.character.guild_reputation(class_name)
            rank = self.character.guild_rep_rank(class_name)
            discount_percent = int(round(self.character.guild_training_discount(class_name) * 100))
            active_text = "aktywna" if class_name in active else "nieaktywna"
            await self.send(
                f"CODEX KLASOWY: {class_name}. Klasa {active_text}. "
                f"Nauczyciel: {teacher_name}. Sala: {teacher_room}. "
                f"Reputacja Gildii: {rep}/{GUILD_REPUTATION_MAX}, {rank[1]}. "
                f"Rabat na naukę: {discount_percent} procent."
            )

            skills = CLASS_SKILLS.get(class_name, [])
            if not skills:
                await self.send("Brak zdefiniowanych umiejętności tej klasy.")
                continue

            for number, skill in enumerate(skills, 1):
                base_cost, final_cost, discount = self.class_codex_training_cost(class_name, skill)
                if skill["id"] in learned:
                    row = self.server.db.skill_progress(self.account_id, skill["id"])
                    level = int(row["level"])
                    status = f"ODBLOCKOWANA I NAUCZONA, Skill Level {level}"
                elif class_name not in active:
                    if self.class_mastery_level(class_name) < int(skill["unlock"]):
                        status = (
                            f"ZABLOKOWANA: klasa nieaktywna i wymaga Biegłości {skill['unlock']}"
                        )
                    else:
                        status = "ZABLOKOWANA: klasa nieaktywna"
                elif self.class_mastery_level(class_name) < int(skill["unlock"]):
                    status = f"ZABLOKOWANA: wymaga Biegłości {skill['unlock']}"
                else:
                    status = "ODBLOKOWANA: dostępna do nauki"

                if discount > 0:
                    cost = (
                        f"{self.training_cost_text(final_cost)} po rabacie {int(round(discount*100))} procent; "
                        f"cena bazowa {self.training_cost_text(base_cost)}"
                    )
                else:
                    cost = self.training_cost_text(final_cost)

                mana = effective_skill_mana_cost(skill, class_name)
                mana_text = f" Mana {mana}." if mana else ""
                await self.send(
                    f"{number}. {skill['name']}. Biegłość {skill['unlock']}. "
                    f"Nauczyciel: {teacher_name}, {teacher_room}. "
                    f"Koszt: {cost}. Status: {status}."
                    f"{mana_text}"
                    + (f" Mechaniczny cooldown {skill.get('cooldown', 0)} sekund." if skill.get("mechanic_cooldown") else " Bez cooldownu.")
                    + f" {skill.get('desc', '')}"
                )


async def show_skill_catalog_names(self, class_names, title):
        """NVDA-friendly compact catalog: names in chunks, grouped by class."""
        class_names = list(class_names or [])
        await self.send(title)
        total = 0
        for class_name in class_names:
            skills = list(CLASS_SKILLS.get(class_name, []))
            total += len(skills)
            await self.send(f"{class_name}: {len(skills)} umiejętności.")
            if not skills:
                continue
            chunk_size = 20
            for start_index in range(0, len(skills), chunk_size):
                chunk = skills[start_index:start_index + chunk_size]
                first = start_index + 1
                last = start_index + len(chunk)
                names = ", ".join(
                    f"{index}. {skill['name']}"
                    for index, skill in enumerate(chunk, first)
                )
                await self.send(f"{class_name} {first}-{last}: {names}.")
        await self.send(
            f"Łącznie: {total}. Szczegóły konkretnej umiejętności: "
            "help <nazwa>, help skill <nazwa> albo skill info <nazwa>."
        )


async def show_skills(self, args=""):
        mode = normalize_lookup_text(str(args or "").strip())
        all_classes = [row[0] for row in CLASSES]
        if mode in ("all", "wszystkie", "wszystko", "pelne", "pelny", "full"):
            await self.show_skill_catalog_names(
                all_classes,
                "SKILLS ALL. Wszystkie skille i spelle wszystkich 14 klas.",
            )
            return

        # Wygodne skills <klasa> bez konieczności otwierania kodeksu.
        if mode:
            matched = next(
                (name for name in all_classes if normalize_lookup_text(name) == mode),
                None,
            )
            if matched:
                await self.show_skill_catalog_names(
                    [matched], f"SKILLS: {matched}."
                )
                return
            await self.send(
                "Użycie: skills, skills all albo skills <klasa>."
            )
            return

        active = self.active_class_names()
        learned = self.server.db.learned_skill_ids(self.account_id)
        await self.send(
            f"UMIEJĘTNOŚCI AKTYWNYCH KLAS. Klasy: {', '.join(active)}. "
            f"Soul Level: {self.character.soul_level}."
        )

        global_number = 0
        for class_name in active:
            teacher_id, teacher = self.class_teacher(class_name)
            teacher_room = (
                ROOMS[teacher["room"]]["name"] if teacher else "nieznana lokacja"
            )
            await self.send(f"Klasa {class_name}:")
            mastery = self.class_mastery_level(class_name)
            visible_skills = [
                skill
                for skill in CLASS_SKILLS.get(class_name, [])
                if skill["id"] in learned or mastery >= int(skill.get("unlock", 1) or 1)
            ]
            if not visible_skills:
                await self.send(
                    "Brak umiejętności dostępnych na aktualnej Biegłości tej klasy."
                )
                continue
            for skill in visible_skills:
                global_number += 1
                progress_text = ""
                skill_level = 1

                if skill["id"] in learned:
                    row = self.server.db.skill_progress(
                        self.account_id, skill["id"]
                    )
                    skill_level = int(row["level"])
                    if skill_level >= SKILL_MAX_LEVEL:
                        progress_text = (
                            f" Skill Level {skill_level}, maksymalny."
                        )
                    else:
                        progress_text = (
                            f" Skill Level {skill_level}, XP {row['xp']} z "
                            f"{skill_xp_to_next(skill_level)}, użycia {row['uses']}."
                        )
                    status = "nauczona"
                else:
                    status = (
                        f"gotowa do nauki u {teacher['name']} "
                        f"w lokacji {teacher_room}"
                    )

                mana_cost = effective_skill_mana_cost(skill, class_name)
                mana = f", Mana {mana_cost}" if mana_cost else ""
                if skill.get("mechanic_cooldown"):
                    effective_cd = self.effective_skill_cooldown(skill, skill_level)
                    remaining = max(
                        0, int(self.skill_cooldown_ready_at_v0364(skill) - time.time() + 0.999)
                    )
                    cooldown_text = f" Mechaniczny cooldown {effective_cd} sekund"
                    if remaining:
                        cooldown_text += f", pozostało {remaining} sekund"
                    cooldown_text += "."
                else:
                    cooldown_text = " Bez cooldownu."

                await self.send(
                    f"{global_number}. {skill['name']}. {status}."
                    f"{progress_text}{mana}{cooldown_text} {skill['desc']}"
                )

        await self.send(
            "Numery dotyczą wspólnej listy aktywnych klas. "
            "Przy nauczycielu komenda learn <numer> używa lokalnej listy jego klasy."
        )
        await self.send(
            f"Każdy nauczony skill ma własny Skill Level 1-{SKILL_MAX_LEVEL} i XP. "
            "Lista pokazuje tylko skille odblokowane na aktualnej Biegłości klasy."
        )


async def show_spells(self, args=""):
        mode = normalize_lookup_text(str(args or "").strip())
        magic_classes = [name for name, class_type, _weapon, _power in CLASSES if class_type == "magic"]
        if mode in ("all", "wszystkie", "wszystko", "pelne", "pelny", "full"):
            await self.show_skill_catalog_names(
                magic_classes,
                "SPELLS ALL. Czary wszystkich klas magicznych.",
            )
            return

        if mode:
            matched = next(
                (name for name in magic_classes if normalize_lookup_text(name) == mode),
                None,
            )
            if matched:
                await self.show_skill_catalog_names([matched], f"SPELLS: {matched}.")
                return
            await self.send(
                "Użycie: spells, spells all, spels all, czary albo spells <klasa magiczna>."
            )
            return

        active_magic = [name for name in self.active_class_names() if name in magic_classes]
        if not active_magic:
            await self.send(
                "Nie masz aktywnej klasy magicznej. Wpisz spells all, aby poznać wszystkie czary."
            )
            return
        await self.show_skill_catalog_names(
            active_magic,
            "CZARY AKTYWNYCH KLAS MAGICZNYCH.",
        )

