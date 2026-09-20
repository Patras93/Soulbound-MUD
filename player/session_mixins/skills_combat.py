# -*- coding: utf-8 -*-
"""Soulbound v0.30.51 Session mixin: skills_combat."""

def party_drop_recipients_v0359(item_id, recipients):
    """Return every eligible local party member for a successful mob drop.

    The configured drop chance is rolled once per defeated mob. If that roll
    succeeds, each party member already selected by ``mob_defeated`` (same room
    and eligible for the kill rewards) receives one copy of the item. This rule
    applies uniformly to elixirs, potions, materials, runes, gems, technology
    components, Soul Shards and every other normal entry in ``template["drops"]``.
    """
    return list(recipients or [])

class SessionSkillsCombatMixin:
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
            await self.send(
                f"Odblokowano Tier {next_tier} z {SOUL_MAX_TIER}. "
                f"Moc Broni Duszy: {self.character.soul_power()}."
            )
            await self.send(
                f"Nowy bonus klasowy Broni Duszy: "
                f"{self.character.soul_weapon_class_bonus_text()}."
            )
            trait = soul_weapon_trait_for_tier(next_tier, self.character.class_name)
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

    def class_skills(self):
            skills = []
            for class_name in self.active_class_names():
                skills.extend(CLASS_SKILLS.get(class_name, []))
            return skills

    def class_teacher(self, class_name=None):
            wanted = class_name or self.character.class_name
            for npc_id, npc in NPCS.items():
                if npc.get("teacher_class") == wanted:
                    return npc_id, npc
            return None, None

    def normalized_skill_text(self, value):
            return self.normalize_description_query(value)

    def skill_natural_tokens(self, skill):
            tokens = set()
            names = [skill["name"], skill["id"]] + skill.get("aliases", [])
            names += skill.get("natural_tags", [])

            for value in names:
                normalized = self.normalized_skill_text(value)
                if not normalized:
                    continue
                tokens.add(normalized)
                tokens.update(normalized.split())

            return tokens

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

    def class_codex_training_cost(self, class_name, skill):
            base_cost = self.skill_training_cost_silver(skill)
            discount = self.character.guild_training_discount(class_name)
            final_cost = max(1, int(round(base_cost * (1.0 - discount))))
            return base_cost, final_cost, discount

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

                    mana = int(skill.get("mana", 0) or 0)
                    mana_text = f" Mana {mana}." if mana else ""
                    await self.send(
                        f"{number}. {skill['name']}. Biegłość {skill['unlock']}. "
                        f"Nauczyciel: {teacher_name}, {teacher_room}. "
                        f"Koszt: {cost}. Status: {status}."
                        f"{mana_text} Cooldown {skill.get('cooldown', 0)} sekund. "
                        f"{skill.get('desc', '')}"
                    )

    async def show_all_skill_names(self):
            await self.send("NAZWY SKILLI WSZYSTKICH KLAS")
            for class_name in [cls[0] for cls in CLASSES]:
                skills = CLASS_SKILLS.get(class_name, [])
                names = ", ".join(
                    f"{index}. {skill['name']}"
                    for index, skill in enumerate(skills, 1)
                )
                await self.send(f"{class_name}: {names}.")
            await self.send(
                "Nazw możesz używać w komendach skill <nazwa> oraz naucz <nazwa>."
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
                for skill in CLASS_SKILLS.get(class_name, []):
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
                    elif self.class_mastery_level(class_name) >= int(skill["unlock"]):
                        status = (
                            f"gotowa do nauki u {teacher['name']} "
                            f"w lokacji {teacher_room}"
                        )
                    else:
                        status = (
                            f"zablokowana: wymaga Biegłości klasy {skill['unlock']}"
                        )

                    mana = (
                        f", Mana {skill.get('mana', 0)}"
                        if skill.get("mana", 0) else ""
                    )
                    effective_cd = self.effective_skill_cooldown(
                        skill, skill_level
                    )
                    remaining = max(
                        0,
                        int(
                            self.skill_cooldowns.get(skill["id"], 0)
                            - time.time() + 0.999
                        ),
                    )
                    cd = (
                        f", pozostały cooldown {remaining} sekund"
                        if remaining else ""
                    )

                    await self.send(
                        f"{global_number}. {skill['name']}. {status}."
                        f"{progress_text} Cooldown bazowy {skill['cooldown']} sekund, "
                        f"aktualny {effective_cd} sekund{mana}{cd}. "
                        f"{skill['desc']}"
                    )

            await self.send(
                "Numery dotyczą wspólnej listy aktywnych klas. "
                "Przy nauczycielu komenda learn <numer> używa lokalnej listy jego klasy."
            )
            await self.send(
                "Każdy nauczony skill ma własny Skill Level 1-600 i XP. "
                "Wpisz skills all, aby usłyszeć pulę wszystkich klas."
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

    def protected_friendly_npc(self, query):
            room_id = self.character.room_id
            candidates = {
                npc_id: npc
                for npc_id, npc in NPCS.items()
                if npc.get("room") == room_id
            }
            if not candidates:
                return None

            found = find_by_name(candidates, query)
            if not found:
                return None
            return found[1]

    async def reject_friendly_npc_attack(self, query):
            npc = self.protected_friendly_npc(query)
            if not npc:
                return False

            await self.send(
                f"{npc['name']} jest pokojowym i chronionym NPC-em. "
                "Sprzedawców, nauczycieli, postaci zadaniowych i innych "
                "pomocnych NPC-ów nie można atakować ani zabijać."
            )
            return True

    def protected_player_target(self, query):
            raw = normalize_lookup_text(str(query or "").strip())
            if not raw:
                return None
            for session in list(self.server.sessions):
                if session.closed or not session.character:
                    continue
                if session.character.room_id != self.character.room_id:
                    continue
                if normalize_lookup_text(session.character.name) == raw:
                    return session
            return None

    async def reject_player_attack(self, query):
            target = self.protected_player_target(query)
            if not target:
                return False
            if target is self:
                await self.send(
                    "Nie możesz zaatakować własnej postaci. PvP jest wyłączone w Soulbound."
                )
            else:
                await self.send(
                    f"Nie możesz zaatakować gracza {target.character.name}. "
                    "PvP jest wyłączone: gracze nie mogą ranić ani zabijać innych graczy."
                )
            return True

    def skill_progress_data(self, skill):
            if not self.server.db.knows_skill(self.account_id, skill["id"]):
                return {"level": 0, "xp": 0, "uses": 0}
            row = self.server.db.skill_progress(self.account_id, skill["id"])
            return {
                "level": int(row["level"]),
                "xp": int(row["xp"]),
                "uses": int(row["uses"]),
            }

    def effective_skill_cooldown(self, skill, skill_level):
            return max(
                1,
                int(round(skill["cooldown"] * skill_cooldown_multiplier(skill_level)))
            )

    async def grant_skill_use_xp(self, skill):
            current = self.skill_progress_data(skill)
            raw_gain = 25 + random.randint(0, 10)
            gain = v0190_scaled_gain(raw_gain, max(1, current.get("level", 1)), "skill", 30)
            gain = self.apply_double_xp(gain)
            result = self.server.db.add_skill_xp(
                self.account_id, skill["id"], gain
            )
            if result["level_ups"]:
                await self.send(
                    f"{skill['name']} awansuje na Skill Level {result['level']}.",
                    combat_detail="essential" if self.combat_mob_key else None,
                )
            if result["level"] >= SKILL_MAX_LEVEL:
                await self.send(
                    f"{skill['name']}: Skill Level {SKILL_MAX_LEVEL}. Maksymalny poziom.",
                    combat_detail="full" if self.combat_mob_key else None,
                )
            else:
                await self.send(
                    f"{skill['name']}: Skill XP +{gain}. "
                    f"Level {result['level']}, XP {result['xp']} z {result['next_xp']}.",
                    combat_detail="full" if self.combat_mob_key else None,
                )
            # v0.33.0: pasywne umiejętności tej samej klasy również rozwijają się
            # podczas realnego używania aktywnych skilli. Dostają 25% bazowego Skill XP,
            # dzięki czemu ich poziom 1-600 ma znaczenie bez osobnej komendy cast.
            if str(skill.get("kind", "")) != "passive":
                skill_class = self.skill_class_name(skill)
                passive_gain = max(1, gain // 4)
                for passive in CLASS_SKILLS.get(skill_class, []):
                    if passive.get("kind") != "passive" or passive.get("id") == skill.get("id"):
                        continue
                    if not self.server.db.knows_skill(self.account_id, passive["id"]):
                        continue
                    self.server.db.add_skill_xp(self.account_id, passive["id"], passive_gain)
            return result

    def skill_scale_value(self, scale):
            # v0.34.6: respektuj autorskie źródło mocy konkretnego skilla.
            # Łowca/Łotrzyk oraz zręcznościowe techniki Mnicha/Meca/Inżyniera
            # muszą naprawdę liczyć Zręczność zamiast wpadać w fallback Siły.
            scale = str(scale or "strength").lower()
            if scale == "intelligence":
                return self.effective_intelligence()
            if scale == "dexterity":
                return self.effective_dexterity()
            return self.effective_strength()

    def engagement_block_message(self, mob):
            name = MOB_TEMPLATES[mob.template_id]["name"]
            if self.server.party_key_for_account(self.account_id) is None:
                return f"{name} walczy już z innym graczem."
            return f"{name} walczy już z graczem spoza twojej drużyny."

    async def skill_combat_target(self, query):
            if str(query or "").strip() and await self.reject_player_attack(query):
                return None
            self.server.world.refresh()
            mob = None
            if self.combat_mob_key:
                mob = self.server.world.mobs.get(self.combat_mob_key)
                if not mob or not mob.alive or mob.room_id != self.character.room_id:
                    self.combat_mob_key = None
                    mob = None

            if mob is None:
                if not query.strip():
                    await self.send("Ta umiejętność wymaga celu. Podaj nazwę przeciwnika.")
                    return None
                if await self.reject_player_attack(query):
                    return None
                if await self.reject_friendly_npc_attack(query):
                    return None
                mob = self.server.world.find_mob(self.character.room_id, query)
                if not mob:
                    await self.send("Nie widzę tutaj takiego przeciwnika.")
                    return None
                if not self.server.engagement_allowed(self, mob):
                    await self.send(self.engagement_block_message(mob))
                    return None
                was_unengaged = not mob.engaged_by
                protector = await self.server.apply_party_protection(self, mob)
                if was_unengaged:
                    if mob.engaged_at <= 0:
                        mob.engaged_at = time.monotonic()
                    if not mob.engaged_by:
                        mob.engaged_by = self.character.name
                    mob.combat_turn = 0
                    mob.player_hits = 0
                self.combat_mob_key = mob.key
                await self.server.broadcast_room(
                    self.character.room_id,
                    f"{self.character.name} rozpoczyna walkę umiejętnością klasową.",
                    exclude=self,
                )
                await self.send(
                    "Rozpoczyna się walka w czasie rzeczywistym. Cel został ustawiony; ataki i auto kolejka działają automatycznie."
                )
            return mob

    async def apply_boss_defense(self, mob, damage):
            if not mob or not mob.alive:
                return max(0, int(damage))

            template = MOB_TEMPLATES[mob.template_id]
            mechanic = template.get("boss_mechanic")
            damage = max(0, int(damage))

            elite_affix = template.get("elite_affix")
            if elite_affix == "armored" and damage > 0:
                reduced = max(
                    1,
                    int(round(damage * 0.70)),
                )
                await self.send_combat(
                    f"Affix Opancerzony redukuje obrażenia "
                    f"z {damage} do {reduced}."
                )
                damage = reduced

            if not mechanic:
                return damage

            mob.player_hits += 1

            if mechanic == "grave_shield" and mob.player_hits % 3 == 0:
                reduced = max(1, damage // 2) if damage > 0 else 0
                await self.send_combat(
                    f"{template['name']} aktywuje Tarczę Grobowca. "
                    f"Twoje obrażenia spadają z {damage} do {reduced}."
                )
                return reduced

            if mechanic == "ethereal_evade" and random.random() < 0.25:
                await self.send_combat(
                    f"{template['name']} rozpływa się w eterze i całkowicie unika trafienia."
                )
                return 0

            if mechanic == "hundred_lord" and mob.player_hits % 4 == 0:
                reduced = max(1, int(round(damage * 0.60))) if damage > 0 else 0
                await self.send_combat(
                    f"{template['name']} tworzy Pieczęć Stu Pięter. "
                    f"Obrażenia zostają zredukowane z {damage} do {reduced}."
                )
                return reduced

            if mechanic == "iron_bones" and mob.player_hits % 3 == 0:
                reduced = max(1, int(round(damage * 0.55))) if damage > 0 else 0
                await self.send_combat(
                    f"{template['name']} wzmacnia Żelazne Kości. "
                    f"Obrażenia spadają z {damage} do {reduced}."
                )
                return reduced

            if mechanic == "phantom_emperor" and random.random() < 0.30:
                await self.send_combat(
                    f"{template['name']} wykonuje Widmowy Unik i znika przed trafieniem."
                )
                return 0

            if mechanic == "final_guardian" and mob.player_hits % 4 == 0:
                reduced = max(1, damage // 2) if damage > 0 else 0
                await self.send_combat(
                    f"{template['name']} aktywuje Straż Końca. "
                    f"Obrażenia spadają z {damage} do {reduced}."
                )
                return reduced

            if mechanic == "two_hundred_lord" and mob.player_hits % 5 == 0:
                reduced = max(1, damage // 2) if damage > 0 else 0
                await self.send_combat(
                    f"{template['name']} aktywuje Barierę Końca. "
                    f"Obrażenia spadają z {damage} do {reduced}."
                )
                return reduced

            if mechanic == "stellar_barrier" and mob.player_hits % 3 == 0:
                reduced = max(1, damage // 2) if damage > 0 else 0
                await self.send_combat(
                    f"{template['name']} aktywuje Gwiezdną Barierę. "
                    f"Obrażenia spadają z {damage} do {reduced}."
                )
                return reduced

            if mechanic == "comet_evade" and random.random() < 0.25:
                await self.send_combat(
                    f"{template['name']} wykonuje Unik Komety i znika przed trafieniem."
                )
                return 0

            if mechanic == "firmament_guard" and mob.player_hits % 4 == 0:
                reduced = max(1, damage // 2) if damage > 0 else 0
                await self.send_combat(
                    f"{template['name']} aktywuje Straż Firmamentu. "
                    f"Obrażenia spadają z {damage} do {reduced}."
                )
                return reduced

            if mechanic == "astral_sovereign" and mob.player_hits % 5 == 0:
                reduced = max(1, damage // 2) if damage > 0 else 0
                await self.send_combat(
                    f"{template['name']} aktywuje Barierę Suwerena. "
                    f"Obrażenia spadają z {damage} do {reduced}."
                )
                return reduced

            if mechanic == "crystal_lord" and mob.player_hits % 4 == 0:
                reduced = max(1, damage // 2) if damage > 0 else 0
                await self.send_combat(
                    f"{template['name']} aktywuje Kryształową Barierę. "
                    f"Obrażenia spadają z {damage} do {reduced}."
                )
                return reduced

            return damage

    async def boss_phase_multiplier(self, mob, template):
            is_boss = bool(
                template.get("world_boss")
                or template.get("crypt_boss")
                or template.get("astral_boss")
                or template.get("mythic_crypt_boss")
                or template.get("mythic_astral_boss")
                or template.get("boss_mechanic")
            )
            if not is_boss:
                return 1.0

            ratio = mob.hp / max(1, int(template.get("max_hp", 1)))
            if ratio <= 0.25:
                stage, mult = 3, 1.60
            elif ratio <= 0.50:
                stage, mult = 2, 1.35
            elif ratio <= 0.75:
                stage, mult = 1, 1.15
            else:
                stage, mult = 0, 1.0

            if stage > int(getattr(mob, "phase_stage", 0)):
                mob.phase_stage = stage
                await self.send(
                    f"FAZA {stage + 1}. {template['name']} staje się groźniejszy. "
                    f"Siła kontrataków: +{int(round((mult - 1.0) * 100))} procent."
                )
            return mult

    async def boss_attack_profile(self, mob, template):
            mob.combat_turn += 1
            turn = mob.combat_turn
            mechanic = template.get("boss_mechanic")
            profile = {
                "damage_type": template.get("damage_type", "physical"),
                "damage_multiplier": 1.0,
                "defense_factor": 1.0,
                "drain_pct": 0.0,
            }

            profile["damage_multiplier"] *= await self.boss_phase_multiplier(
                mob, template
            )

            if mechanic == "bone_crush" and turn % 3 == 0:
                profile["damage_multiplier"] = 1.60
                await self.send(f"{template['name']} używa Kościanego Miażdżenia.")

            elif mechanic == "blood_drain" and turn % 3 == 0:
                profile["damage_multiplier"] = 1.25
                profile["drain_pct"] = 0.50
                await self.send(f"{template['name']} używa Krwawego Drenażu.")

            elif mechanic == "ash_curse" and turn % 3 == 0:
                profile["damage_type"] = "magic"
                profile["damage_multiplier"] = 1.25
                profile["defense_factor"] = 0.50
                await self.send(
                    f"{template['name']} rzuca Klątwę Popiołu. "
                    "Połowa twojej obrony magicznej zostaje pominięta."
                )

            elif mechanic == "catacomb_echo" and turn % 4 == 0:
                profile["damage_multiplier"] = 1.70
                await self.send(
                    f"{template['name']} wyzwala Echo Katakumb. "
                    "To jedna, ale wyjątkowo silna odpowiedź bossa."
                )

            elif mechanic == "spectral_shift":
                profile["damage_type"] = "magic" if turn % 2 else "physical"
                await self.send(
                    f"{template['name']} zmienia widmową fazę. "
                    f"Ten kontratak jest "
                    f"{'magiczny' if profile['damage_type'] == 'magic' else 'fizyczny'}."
                )

            elif mechanic == "necro_regen" and turn % 4 == 0:
                heal = max(1, int(round(template["max_hp"] * 0.07)))
                before = mob.hp
                mob.hp = min(template["max_hp"], mob.hp + heal)
                actual = mob.hp - before
                if actual > 0:
                    await self.send(
                        f"{template['name']} używa Nekroregeneracji "
                        f"i odzyskuje {actual} HP. "
                        f"Boss: {mob.hp} z {template['max_hp']} HP."
                    )

            elif mechanic == "bone_rage":
                if mob.hp <= template["max_hp"] // 2:
                    profile["damage_multiplier"] = 1.50
                    await self.send(
                        f"{template['name']} walczy w Furii Króla Kości."
                    )

            elif mechanic == "hundred_lord":
                if mob.hp <= template["max_hp"] // 2:
                    profile["damage_multiplier"] *= 1.25
                if turn % 3 == 0:
                    profile["damage_type"] = "magic"
                    profile["damage_multiplier"] *= 1.50
                    profile["defense_factor"] = 0.75
                    await self.send(
                        f"{template['name']} używa Załamania Duszy."
                    )
                elif mob.hp <= template["max_hp"] // 2:
                    await self.send(
                        f"{template['name']} walczy w drugiej fazie."
                    )

            elif mechanic == "soul_breaker" and turn % 3 == 0:
                profile["damage_type"] = "magic"
                profile["damage_multiplier"] = 1.45
                profile["defense_factor"] = 0.75
                await self.send(
                    f"{template['name']} używa Rozdarcia Duszy."
                )

            elif mechanic == "abyss_queen" and turn % 4 == 0:
                profile["damage_type"] = "magic"
                profile["damage_multiplier"] = 1.35
                profile["drain_pct"] = 0.40
                await self.send(
                    f"{template['name']} używa Drenażu Otchłani."
                )

            elif mechanic == "iron_bones" and turn % 3 == 0:
                profile["damage_type"] = "physical"
                profile["damage_multiplier"] = 1.60
                await self.send(
                    f"{template['name']} wykonuje Uderzenie Żelaznych Kości."
                )

            elif mechanic == "black_flame" and turn % 3 == 0:
                profile["damage_type"] = "magic"
                profile["damage_multiplier"] = 1.55
                profile["defense_factor"] = 0.50
                await self.send(
                    f"{template['name']} uwalnia Czarny Płomień."
                )

            elif mechanic == "endless_echo" and turn % 4 == 0:
                profile["damage_multiplier"] = 1.85
                await self.send(
                    f"{template['name']} wyzwala Bezdenne Echo."
                )

            elif mechanic == "astral_reaper":
                profile["damage_type"] = "magic" if turn % 2 else "physical"
                if turn % 5 == 0:
                    profile["damage_multiplier"] = 1.60
                    await self.send(
                        f"{template['name']} wykonuje Astralne Żniwo."
                    )
                else:
                    await self.send(
                        f"{template['name']} zmienia astralną fazę. "
                        f"Kontratak jest "
                        f"{'magiczny' if profile['damage_type'] == 'magic' else 'fizyczny'}."
                    )

            elif mechanic == "void_regen":
                if turn % 4 == 0:
                    heal = max(1, int(round(template["max_hp"] * 0.08)))
                    before = mob.hp
                    mob.hp = min(template["max_hp"], mob.hp + heal)
                    actual = mob.hp - before
                    if actual > 0:
                        await self.send(
                            f"{template['name']} regeneruje {actual} HP energią Pustki. "
                            f"Boss: {mob.hp} z {template['max_hp']} HP."
                        )
                if turn % 3 == 0:
                    profile["damage_type"] = "magic"
                    profile["damage_multiplier"] = 1.30

            elif mechanic == "phantom_emperor" and turn % 3 == 0:
                profile["damage_type"] = "magic"
                profile["damage_multiplier"] = 1.60
                profile["defense_factor"] = 0.75
                await self.send(
                    f"{template['name']} używa Cesarskiego Widma."
                )

            elif mechanic == "final_guardian":
                if mob.hp <= template["max_hp"] // 2:
                    profile["damage_multiplier"] = 1.60
                    await self.send(
                        f"{template['name']} wchodzi w Ostatnią Straż."
                    )

            elif mechanic == "two_hundred_lord":
                if mob.hp <= template["max_hp"] // 2:
                    profile["damage_multiplier"] *= 1.35
                if turn % 3 == 0:
                    profile["damage_type"] = "magic"
                    profile["damage_multiplier"] *= 1.65
                    profile["defense_factor"] = 0.60
                    await self.send(
                        f"{template['name']} używa Załamania Wieczności."
                    )
                elif mob.hp <= template["max_hp"] // 2:
                    await self.send(
                        f"{template['name']} walczy w finałowej fazie Dwustu Pięter."
                    )

            elif mechanic == "astral_shift":
                profile["damage_type"] = (
                    "magic" if turn % 2 else "physical"
                )
                await self.send(
                    f"{template['name']} zmienia Astralną Fazę. "
                    f"Kontratak jest "
                    f"{'magiczny' if profile['damage_type'] == 'magic' else 'fizyczny'}."
                )

            elif mechanic == "stellar_barrier" and turn % 3 == 0:
                profile["damage_type"] = "magic"
                profile["damage_multiplier"] = 1.35
                await self.send(
                    f"{template['name']} wystrzeliwuje Gwiezdną Lancę."
                )

            elif mechanic == "nebula_drain" and turn % 4 == 0:
                profile["damage_type"] = "magic"
                profile["damage_multiplier"] = 1.40
                profile["drain_pct"] = 0.45
                await self.send(
                    f"{template['name']} używa Drenażu Nebuli."
                )

            elif mechanic == "comet_evade" and turn % 3 == 0:
                profile["damage_multiplier"] = 1.55
                await self.send(
                    f"{template['name']} uderza Szarżą Komety."
                )

            elif mechanic == "starfire" and turn % 3 == 0:
                profile["damage_type"] = "magic"
                profile["damage_multiplier"] = 1.55
                profile["defense_factor"] = 0.50
                await self.send(
                    f"{template['name']} wyzwala Gwiezdny Ogień."
                )

            elif mechanic == "orbital_echo" and turn % 4 == 0:
                profile["damage_multiplier"] = 1.85
                await self.send(
                    f"{template['name']} wyzwala Echo Orbitalne."
                )

            elif mechanic == "constellation_burst" and turn % 3 == 0:
                profile["damage_type"] = "magic"
                profile["damage_multiplier"] = 1.65
                profile["defense_factor"] = 0.70
                await self.send(
                    f"{template['name']} wyzwala Rozbłysk Konstelacji."
                )

            elif mechanic == "astral_regen":
                if turn % 4 == 0:
                    heal = max(
                        1,
                        int(round(template["max_hp"] * 0.08))
                    )
                    before = mob.hp
                    mob.hp = min(
                        template["max_hp"],
                        mob.hp + heal,
                    )
                    actual = mob.hp - before
                    if actual > 0:
                        await self.send(
                            f"{template['name']} regeneruje {actual} HP "
                            "energią Astralu."
                        )
                if turn % 3 == 0:
                    profile["damage_type"] = "magic"
                    profile["damage_multiplier"] = 1.35

            elif mechanic == "stellar_storm" and turn % 3 == 0:
                profile["damage_type"] = "magic"
                profile["damage_multiplier"] = 1.70
                profile["defense_factor"] = 0.70
                await self.send(
                    f"{template['name']} przywołuje Gwiezdną Burzę."
                )

            elif mechanic == "firmament_guard":
                if mob.hp <= template["max_hp"] // 2:
                    profile["damage_multiplier"] = 1.60
                    await self.send(
                        f"{template['name']} przechodzi w Ostatnią Straż Firmamentu."
                    )

            elif mechanic == "astral_sovereign":
                if mob.hp <= template["max_hp"] // 2:
                    profile["damage_multiplier"] *= 1.35
                if turn % 3 == 0:
                    profile["damage_type"] = "magic"
                    profile["damage_multiplier"] *= 1.70
                    profile["defense_factor"] = 0.60
                    await self.send(
                        f"{template['name']} używa Astralnego Załamania."
                    )
                elif mob.hp <= template["max_hp"] // 2:
                    await self.send(
                        f"{template['name']} wchodzi w fazę Suwerena."
                    )

            elif mechanic == "goblin_king" and turn % 3 == 0:
                profile["damage_multiplier"] = 1.50
                await self.send(
                    f"{template['name']} wykonuje Królewską Szarżę."
                )

            elif mechanic == "shadow_alpha":
                if mob.hp <= template["max_hp"] // 2:
                    profile["damage_multiplier"] = 1.40
                    await self.send(
                        f"{template['name']} wpada w Szał Cienia."
                    )

            elif mechanic == "ruin_warden" and turn % 4 == 0:
                profile["damage_type"] = "magic"
                profile["damage_multiplier"] = 1.35
                profile["defense_factor"] = 0.75
                await self.send(
                    f"{template['name']} uwalnia Runiczny Wybuch."
                )

            elif mechanic == "crystal_lord" and turn % 3 == 0:
                profile["damage_type"] = "magic"
                profile["damage_multiplier"] = 1.45
                await self.send(
                    f"{template['name']} wyzwala Kryształowy Promień."
                )

            elif mechanic == "bandit_combo" and turn % 3 == 0:
                profile["damage_multiplier"] = 1.40
                await self.send(
                    f"{template['name']} wykonuje Brutalną Kombinację."
                )

            elif mechanic == "giant_crush" and turn % 3 == 0:
                profile["damage_multiplier"] *= 1.60
                await self.send(
                    f"{template['name']} wykonuje Miażdżenie Giganta."
                )

            elif mechanic == "cyclops_beam" and turn % 3 == 0:
                profile["damage_type"] = "magic"
                profile["damage_multiplier"] *= 1.55
                profile["defense_factor"] = min(
                    profile["defense_factor"], 0.70
                )
                await self.send(
                    f"{template['name']} wyzwala Promień Cyklopa."
                )

            elif mechanic == "boulder_storm" and turn % 4 == 0:
                profile["damage_multiplier"] *= 1.85
                await self.send(
                    f"{template['name']} wywołuje Burzę Głazów."
                )

            elif mechanic == "giant_thunder":
                if turn % 2:
                    profile["damage_type"] = "magic"
                if turn % 3 == 0:
                    profile["damage_multiplier"] *= 1.65
                    await self.send(
                        f"{template['name']} przywołuje Grom Gigantów."
                    )

            elif mechanic == "giant_king":
                if mob.hp <= template["max_hp"] // 2:
                    profile["damage_multiplier"] *= 1.40
                if turn % 3 == 0:
                    profile["damage_multiplier"] *= 1.70
                    await self.send(
                        f"{template['name']} używa Królewskiego Trzęsienia."
                    )

            elite_affix = template.get("elite_affix")
            if elite_affix == "vampiric":
                profile["drain_pct"] = max(
                    profile["drain_pct"], 0.35
                )
            elif elite_affix == "regenerating":
                if turn % 3 == 0:
                    heal = max(
                        1,
                        int(round(template["max_hp"] * 0.04)),
                    )
                    before = mob.hp
                    mob.hp = min(
                        template["max_hp"],
                        mob.hp + heal,
                    )
                    actual = mob.hp - before
                    if actual > 0:
                        await self.send(
                            f"Affix Regenerujący odnawia "
                            f"{actual} HP przeciwnika."
                        )
            elif elite_affix == "ice":
                profile["damage_type"] = "magic"
                profile["damage_multiplier"] *= 1.15
            elif elite_affix == "fire":
                profile["damage_type"] = "magic"
                profile["damage_multiplier"] *= 1.25
            elif elite_affix == "astral":
                profile["damage_type"] = (
                    "magic" if turn % 2 else "physical"
                )
                profile["damage_multiplier"] *= 1.30
                profile["defense_factor"] = min(
                    profile["defense_factor"], 0.75
                )
            elif elite_affix == "furious":
                profile["damage_multiplier"] *= 1.40
            elif elite_affix == "storm":
                profile["damage_type"] = "magic"
                profile["damage_multiplier"] *= 1.30
                profile["defense_factor"] = min(profile["defense_factor"], 0.88)
            elif elite_affix == "toxic":
                profile["damage_multiplier"] *= 1.15
                profile["defense_factor"] = min(profile["defense_factor"], 0.65)
            elif elite_affix == "cursed":
                profile["damage_type"] = "magic"
                profile["damage_multiplier"] *= 1.20
                profile["defense_factor"] = min(
                    profile["defense_factor"], 0.82
                )

            return profile

    async def enemy_counterattack(self, mob):
            if not mob or not mob.alive:
                return
            template = MOB_TEMPLATES[mob.template_id]
            profile = await self.boss_attack_profile(mob, template)
            now=time.time()
            if now >= float(getattr(self,"v0319_feedback_repair_at",0.0) or 0.0) and int(getattr(self,"v0319_feedback_repair_pool",0) or 0)>0 and self.current_hp>0:
                repaired=min(int(getattr(self,"v0319_feedback_repair_pool",0)), max(0,self.max_hp()-self.current_hp))
                if repaired>0:
                    self.current_hp+=repaired
                    await self.send_combat(f"Self-Repair odzyskuje {repaired} HP po Feedback damage.","normal")
                self.v0319_feedback_repair_pool=0; self.v0319_feedback_repair_at=0.0
            # v0.31.9: runtime status effects used by Mec/Engineer authored kits.
            periodic=0
            if now < float(getattr(mob,"v0319_poison_until",0.0) or 0.0):
                periodic += max(1,int(getattr(mob,"v0319_poison_power",1) or 1))
            if now < float(getattr(mob,"v0319_hp_leak_until",0.0) or 0.0):
                periodic += max(1,int(template.get("max_hp",1)*0.025))
            if now < float(getattr(mob,"v0319_satellite_until",0.0) or 0.0):
                periodic += max(1,int(getattr(mob,"v0319_satellite_power",1) or 1))
            if periodic:
                mob.hp -= periodic
                await self.send_combat(f"Efekty technologiczne zadają {periodic} obrażeń {template['name']}. HP {max(0,mob.hp)}.","normal")
                if mob.hp <= 0:
                    await self.mob_defeated(mob); return
            if now < float(getattr(mob,"v0319_sleep_until",0.0) or 0.0):
                mob.v0319_sleep_until=0.0
                await self.send_combat(f"{template['name']} śpi i traci turę.","normal"); return
            if now < float(getattr(mob,"v0319_disabled_until",0.0) or 0.0):
                await self.send_combat(f"{template['name']} jest wyłączony przez Jammer i traci turę.","normal"); return
            if now < float(getattr(mob,"v0319_slow_until",0.0) or 0.0) and getattr(mob,"combat_turn",0)%2==0:
                await self.send_combat(f"{template['name']} jest spowolniony i traci turę.","full"); return
            if now < float(getattr(mob,"v0319_blind_until",0.0) or 0.0) and random.random()<0.35:
                await self.send_combat(f"{template['name']} pudłuje przez Blind.","normal"); return

            _intercept_level=1
            if self.mec_skill_known_v0319("v0319_mec_intercept_system"):
                _intercept_level=int(self.server.db.skill_progress(self.account_id,"v0319_mec_intercept_system")["level"])
            _intercept_progress=(max(1,min(SKILL_MAX_LEVEL,_intercept_level))-1)/float(max(1, SKILL_MAX_LEVEL-1))
            _intercept_chance=0.10 + 0.25*(_intercept_progress**0.82)
            if self.mec_skill_known_v0319("v0319_mec_intercept_system") and profile.get("damage_type")=="physical" and random.random()<_intercept_chance:
                counter=max(1,int(((self.physical_power()+self.spell_power())/2)*(1.0+1.5*_intercept_progress)))
                mob.hp-=counter
                await self.send_combat(f"Intercept System przerywa atak {template['name']} i kontruje za {counter}.","normal")
                if mob.hp<=0:
                    await self.mob_defeated(mob); return
                return

            if self.skill_evade:
                self.skill_evade = False
                await self.send_combat(
                    f"{template['name']} atakuje, ale aktywna umiejętność gwarantuje unik.",
                    "normal",
                )
                return

            if random.random() < self.dodge_chance():
                await self.send_combat(
                    f"{template['name']} atakuje, ale unikasz ciosu dzięki szybkości.",
                    "normal",
                )
                return

            damage_type = profile["damage_type"]
            if damage_type == "magic":
                full_reduction = self.magic_defense()
                defense_name = "obrona magiczna"
            else:
                full_reduction = self.defense()
                defense_name = "obrona fizyczna"

            raw_damage = max(1, int(round(
                template["damage"] * profile["damage_multiplier"] * self.v0210_enemy_damage_multiplier()
            )))
            requested_reduction = max(
                0,
                int(round(full_reduction * profile["defense_factor"]))
            )
            # Płaska obrona nie może sama wyzerować trafienia. Zwykłe moby mogą
            # stracić do 75% bazowego ciosu, bossowie do 60%; późniejsze guardy,
            # pasywy rasowe i klasowe nadal działają niezależnie.
            defense_cap_ratio = 0.60 if v0863_is_boss_template(template) else 0.75
            defense_cap = max(0, int(math.floor(raw_damage * defense_cap_ratio)))
            reduction = min(requested_reduction, defense_cap)
            incoming = max(
                1,
                raw_damage + random.randint(-2, 2) - reduction
            )

            if self.skill_guard > 0:
                guard = self.skill_guard
                self.skill_guard = 0
                before = incoming
                incoming = max(1, incoming - guard)
                self._recap32_guard_saved=int(getattr(self,"_recap32_guard_saved",0))+max(0,before-incoming)
                await self.send_combat(
                    f"Aktywna osłona redukuje trafienie dodatkowo o "
                    f"{before - incoming} obrażeń.",
                    "full",
                )

            if damage_type == "physical":
                physical_race_percent = (
                    self.character.racial_physical_damage_reduction_percent()
                )
                if physical_race_percent > 0:
                    before_physical_race = incoming
                    incoming = max(
                        1,
                        int(round(
                            incoming
                            * (1.0 - physical_race_percent / 100.0)
                        ))
                    )
                    prevented = max(
                        0, before_physical_race - incoming
                    )
                    if prevented > 0:
                        await self.send_combat(
                            f"Rasowa odporność Trolla redukuje obrażenia "
                            f"fizyczne o {physical_race_percent} procent, "
                            f"czyli o {prevented} obrażeń.",
                            "full",
                        )

            incoming, racial_prevented = (
                self.character.apply_racial_damage_reduction(incoming)
            )
            if racial_prevented > 0:
                await self.send_combat(
                    f"Rasowa odporność Krasnoluda redukuje trafienie o "
                    f"{self.character.racial_damage_reduction_percent()} procent, "
                    f"czyli o {racial_prevented} obrażeń.",
                    "full",
                )

            incoming, class_prevented = (
                self.character.apply_class_damage_reduction(incoming)
            )
            if class_prevented > 0:
                await self.send_combat(
                    f"Pasyw klasy {self.character.class_name} redukuje trafienie o "
                    f"{self.character.class_damage_reduction_percent()} procent, "
                    f"czyli o {class_prevented} obrażeń.",
                    "full",
                )

            # v0.31.9 V-MAX Protect/Shell adaptation: reduce incoming physical/magic damage while active.
            if self.party_vmax_support_active_v03511():
                before_vmax=incoming
                incoming=max(1,int(round(incoming*0.80)))
                if before_vmax>incoming:
                    await self.send_combat(f"V-MAX Protect/Shell redukuje trafienie o {before_vmax-incoming}.","full")
            self.current_hp -= incoming
            if self.party_vmax_support_active_v03511():
                regen=max(1,int(self.max_hp()*0.02))
                self.current_hp=min(self.max_hp(),self.current_hp+regen)
            self._recap52_taken=int(getattr(self,"_recap52_taken",0))+max(0,int(incoming))
            if time.time() < float(getattr(mob,"v0319_air_anchor_until",0.0) or 0.0) and mob.alive:
                anchor=max(1,int(getattr(mob,"v0319_air_anchor_power",1) or 1))
                mob.hp-=anchor
                await self.send_combat(f"Air Anchor odpowiada na atak: {template['name']} otrzymuje {anchor} obrażeń.","normal")
                if mob.hp<=0:
                    await self.mob_defeated(mob); return
            # Self-Repair: passive combat regeneration for Mec when learned.
            if self.mec_skill_known_v0319("v0319_mec_self_repair") and self.current_hp>0:
                _sr_level=int(self.server.db.skill_progress(self.account_id,"v0319_mec_self_repair")["level"]); _sr_p=(max(1,min(SKILL_MAX_LEVEL,_sr_level))-1)/float(max(1, SKILL_MAX_LEVEL-1))
                rep=max(1,int(self.max_hp()*(0.005+0.025*(_sr_p**0.82)))); self.current_hp=min(self.max_hp(),self.current_hp+rep)
            await self.send_combat(
                f"{template['name']} atakuje. Typ obrażeń: "
                f"{'magiczne' if damage_type == 'magic' else 'fizyczne'}. "
                f"Otrzymujesz {incoming} obrażeń po redukcji przez {defense_name}. "
                f"Twoje życie: {max(0, self.current_hp)} z {self.max_hp()}.",
                "normal",
            )
            await self.server.party_combat_broadcast(
                self,
                f"{template['name']} trafia {self.character.name} za {incoming}. "
                f"HP {max(0, self.current_hp)} z {self.max_hp()}.",
                detail="normal",
            )
            await self.combat_hp_warning()

            drain_pct = float(profile.get("drain_pct", 0.0))
            if drain_pct > 0 and mob.alive:
                heal = max(1, int(round(incoming * drain_pct)))
                before = mob.hp
                mob.hp = min(template["max_hp"], mob.hp + heal)
                actual = mob.hp - before
                if actual > 0:
                    await self.send_combat(
                        f"{template['name']} wysysa życie i odzyskuje "
                        f"{actual} HP. Boss: {mob.hp} z "
                        f"{template['max_hp']} HP.",
                        "normal",
                    )

            if self.current_hp <= 0:
                await self.die(template["name"])
                return
            await self.server.auto_priest_party_heal(self)
            await self.maybe_auto_wimpy()

    def natural_learn_skill_from_input(
            self,
            raw,
            class_skills,
        ):
            normalized = self.normalize_description_query(raw)
            if not normalized:
                return None

            words = normalized.split()
            intent = words[0]
            spec = NATURAL_SKILL_INTENTS.get(intent)
            if not spec:
                return None

            candidates = []
            learned = self.server.db.learned_skill_ids(
                self.account_id
            )

            for skill in class_skills:
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

                # Najpierw preferuj najwyżej odblokowany skill,
                # którego gracz jeszcze nie zna.
                unknown_bonus = (
                    1 if skill["id"] not in learned else 0
                )
                score = (
                    unknown_bonus,
                    int(skill["unlock"]),
                )
                candidates.append((score, skill))

            if not candidates:
                return None

            candidates.sort(
                key=lambda entry: entry[0],
                reverse=True,
            )
            best_score = candidates[0][0]
            best = [
                skill
                for score, skill in candidates
                if score == best_score
            ]

            # W obrębie jednego nauczyciela klasy remis powinien być
            # bardzo rzadki. Nie zgadujemy przy identycznym wyniku.
            if len(best) != 1:
                return None

            return best[0]

    async def learn_class_skill(self, raw):
            if self.combat_mob_key:
                await self.send("Nie możesz uczyć się umiejętności podczas walki.")
                return

            teacher_id, teacher = self.teacher_here_for_active_class()
            if not teacher:
                await self.send(
                    "Musisz być przy nauczycielu jednej ze swoich aktywnych klas. "
                    "Wpisz teachers, aby sprawdzić lokacje."
                )
                return

            class_name = teacher["teacher_class"]
            class_skills = CLASS_SKILLS.get(class_name, [])
            value = raw.strip()
            normalized = self.normalize_description_query(value)
            if normalized.startswith("sie ") or normalized.startswith("się "):
                split = value.split(maxsplit=1)
                value = split[1] if len(split) > 1 else ""

            skill = None
            if value.strip().isdigit():
                number = int(value.strip())
                if 1 <= number <= len(class_skills):
                    skill = class_skills[number - 1]
            else:
                wanted = self.normalize_description_query(value)
                for candidate in class_skills:
                    names = [
                        candidate["name"], candidate["id"]
                    ] + candidate.get("aliases", [])
                    if any(
                        wanted == self.normalize_description_query(name)
                        for name in names
                    ):
                        skill = candidate
                        break

                # Naturalna nauka: naucz leczenie, naucz tarcza,
                # naucz ogien, naucz ciecie, naucz pocisk itd.
                if not skill:
                    skill = self.natural_learn_skill_from_input(
                        value,
                        class_skills,
                    )

            if not skill:
                await self.send(
                    f"Nie rozpoznaję umiejętności klasy {class_name}. "
                    f"Możesz użyć pełnej nazwy albo naturalnej kategorii, "
                    f"np. naucz leczenie, naucz tarcza, naucz ciecie, "
                    f"naucz pocisk lub naucz ogien. "
                    f"Wpisz talk {teacher['name']}."
                )
                return

            if self.server.db.knows_skill(self.account_id, skill["id"]):
                await self.send(f"Już znasz umiejętność {skill['name']}.")
                return

            mastery = self.class_mastery_level(class_name)
            if mastery < int(skill["unlock"]):
                await self.send(
                    f"{skill['name']} wymaga Biegłości klasy {skill['unlock']}, "
                    f"a masz {mastery}."
                )
                return

            training_cost = self.skill_training_cost_silver(skill)

            _training_discount = self.character.guild_training_discount(class_name)
            training_cost = max(1, int(round(training_cost * (1.0 - _training_discount))))

            cost_text = self.training_cost_text(training_cost)
            if not self.pay_training_cost(training_cost):
                await self.send(
                    f"Nauka {skill['name']} kosztuje {cost_text}. "
                    "Nie masz wystarczającej ilości pieniędzy."
                )
                return

            self.server.db.learn_skill(self.account_id, skill["id"])
            await self.send(
                f"{teacher['name']} uczy cię umiejętności klasy "
                f"{class_name}: {skill['name']}. Cena: {cost_text}."
            )
            await self.send(
                f"Nauczono. {skill['name']} zaczyna na Skill Level 1."
            )

    def skill_by_id(self, skill_id):
            for class_name, skills in CLASS_SKILLS.items():
                for skill in skills:
                    if skill["id"] == skill_id:
                        return skill
            return None

    def skill_queue_type(self, skill):
            class_name = self.skill_class_name(skill)
            return "magic" if class_type_for_name(class_name) == "magic" else "physical"

    def skill_queue_type_label(self, queue_type):
            return "magiczna" if queue_type == "magic" else "fizyczna"

    def skill_queue_active_mastery(self, queue_type):
            levels = []
            for row in self.server.db.active_class_rows(
                self.account_id, self.character.class_name
            ):
                wanted_type = class_type_for_name(row["class_name"])
                if wanted_type == queue_type:
                    levels.append(int(row["level"]))
            return max(levels) if levels else 0

    def skill_queue_capacity(self, queue_type):
            # v0.30.18: startowa pojemność kolejki to 10 slotów.
            # Sloty nadal rosną wyłącznie z Character Level, nie z Biegłości klasy:
            # Level 1=10, 10=11, 100=20, 200=30, 400=50, 600=70.
            if self.skill_queue_active_mastery(queue_type) <= 0:
                return 0
            character_level = max(1, min(CHARACTER_MAX_LEVEL, int(self.character.character_level)))
            return min(10 + CHARACTER_MAX_LEVEL // 10, 10 + character_level // 10)

    def skill_queue_entries(self, queue_type, active_only=False):
            rows = list(self.server.db.skill_queue_rows(self.account_id, queue_type))
            if active_only:
                rows = rows[: self.skill_queue_capacity(queue_type)]
            return rows

    def skill_queue_find_position(self, query):
            raw = str(query or "").strip()
            normalized = self.normalize_description_query(raw)
            if not raw:
                return None, None, None

            # v0.8.36: publiczna składnia używa zwykłych numerów slotów,
            # np. `fizyczna 1`, `magiczna 2`, `slot 1 fizyczna`.
            # Dawne F1/M1 pozostają akceptowane wyłącznie dla kompatybilności.
            short = normalized.replace(" ", "")
            match = re.fullmatch(r"([fm])(\d+)", short)
            if match:
                queue_type = "physical" if match.group(1) == "f" else "magic"
                return queue_type, int(match.group(2)), None

            type_map = {
                "f": "physical", "fiz": "physical", "fizyczna": "physical",
                "fizyczne": "physical", "physical": "physical",
                "m": "magic", "mag": "magic", "magiczna": "magic",
                "magiczne": "magic", "magic": "magic",
            }

            tokens = raw.split()
            norm_tokens = [self.normalize_description_query(token) for token in tokens]

            # fizyczna 1 / magiczna 2
            if len(tokens) >= 2 and norm_tokens[0] in type_map and tokens[1].isdigit():
                return type_map[norm_tokens[0]], int(tokens[1]), None

            # slot 1 fizyczna / slot 2 magiczna
            if len(tokens) >= 3 and norm_tokens[0] in ("slot", "miejsce") and tokens[1].isdigit():
                if norm_tokens[2] in type_map:
                    return type_map[norm_tokens[2]], int(tokens[1]), None

            # fizyczna slot 1 / magiczna slot 2
            if len(tokens) >= 3 and norm_tokens[0] in type_map and norm_tokens[1] in ("slot", "miejsce") and tokens[2].isdigit():
                return type_map[norm_tokens[0]], int(tokens[2]), None

            # Nazwa skilla: szukamy także w nieaktywnych wpisach, aby można było
            # usunąć skill z kolejki po wyłączeniu klasy multiclass.
            for row in self.server.db.skill_queue_rows(self.account_id):
                skill = self.skill_by_id(row["skill_id"])
                if not skill:
                    continue
                names = [skill["name"], skill["id"]] + skill.get("aliases", [])
                if any(
                    normalized == self.normalize_description_query(name)
                    for name in names
                ):
                    return row["queue_type"], int(row["position"]), skill
            return None, None, None

    async def show_skill_queue(self, queue_type=None):
            enabled = self.server.db.skill_queue_enabled(self.account_id)
            await self.send(
                "AUTO KOLEJKA SKILLI: " + ("WŁĄCZONA." if enabled else "WYŁĄCZONA.")
            )
            types = [queue_type] if queue_type in ("physical", "magic") else ["physical", "magic"]
            for current_type in types:
                mastery = self.skill_queue_active_mastery(current_type)
                capacity = self.skill_queue_capacity(current_type)
                rows = self.skill_queue_entries(current_type)
                label = self.skill_queue_type_label(current_type).capitalize()
                if mastery <= 0:
                    await self.send(
                        f"Kolejka {label}: 0 aktywnych slotów. "
                        "Nie masz aktywnej klasy tego typu."
                    )
                else:
                    await self.send(
                        f"Kolejka {label}: {len(rows)} zapisanych, {capacity} aktywnych slotów. "
                        f"Level postaci: {self.character.character_level}."
                    )
                if not rows:
                    await self.send(f"Kolejka {label}: pusta.")
                    continue
                for row in rows:
                    skill = self.skill_by_id(row["skill_id"])
                    name = skill["name"] if skill else row["skill_id"]
                    position = int(row["position"])
                    class_name = self.skill_class_name(skill) if skill else "nieznana klasa"
                    if class_name not in self.active_class_names():
                        active_text = "uśpiony: klasa nieaktywna"
                    elif position <= capacity:
                        active_text = "aktywny"
                    else:
                        active_text = "uśpiony ponad limitem"
                    await self.send(
                        f"Slot {position}. {name}. Typ {label.lower()}. Klasa {class_name}. {active_text}."
                    )
            await self.send(
                "Komendy: kolejka lista [fizyczna|magiczna], kolejka dodaj <skill>, "
                "kolejka usuń fizyczna <slot> / kolejka usuń magiczna <slot>, "
                "kolejka wyczyść [fizyczna|magiczna], kolejka góra fizyczna <slot>, "
                "kolejka dół magiczna <slot>, kolejka on, kolejka off. Dodanie skilla automatycznie włącza kolejkę."
            )

    async def handle_skill_queue(self, raw):
            text = str(raw or "").strip()
            if not text:
                await self.show_skill_queue()
                return

            parts = text.split(maxsplit=1)
            action = self.normalize_description_query(parts[0])
            value = parts[1].strip() if len(parts) > 1 else ""

            if action in ("on", "wlacz", "włącz", "start", "1"):
                self.server.db.set_skill_queue_enabled(self.account_id, True)
                await self.send(
                    "Auto kolejka skilli włączona. Podczas komendy atakuj system "
                    "spróbuje użyć następnego gotowego skilla z kolejki; jeśli żaden "
                    "nie jest gotowy, wykona zwykły atak."
                )
                return
            if action in ("off", "wylacz", "wyłącz", "stop", "0"):
                self.server.db.set_skill_queue_enabled(self.account_id, False)
                await self.send("Auto kolejka skilli wyłączona.")
                return
            if action in ("status", "lista", "list", "show"):
                list_type = self.normalize_description_query(value)
                if list_type in ("f", "fiz", "fizyczna", "fizyczne", "physical"):
                    await self.show_skill_queue("physical")
                elif list_type in ("m", "mag", "magiczna", "magiczne", "magic"):
                    await self.show_skill_queue("magic")
                else:
                    await self.show_skill_queue()
                return
            if action in ("fizyczna", "fizyczne", "physical"):
                await self.show_skill_queue("physical")
                return
            if action in ("magiczna", "magiczne", "magic"):
                await self.show_skill_queue("magic")
                return

            if action in ("dodaj", "add", "+"):
                if not value:
                    await self.send("Użycie: kolejka dodaj <nazwa skilla>.")
                    return
                skill, _target = self.find_skill_from_input(value)
                if not skill:
                    await self.send(
                        "Nie rozpoznaję skilla aktywnej klasy. Użyj pełnej nazwy z komendy skills."
                    )
                    return
                if not self.server.db.knows_skill(self.account_id, skill["id"]):
                    await self.send(f"Najpierw musisz nauczyć się umiejętności {skill['name']}.")
                    return
                skill_class = self.skill_class_name(skill)
                mastery = self.class_mastery_level(skill_class)
                if mastery < int(skill["unlock"]):
                    await self.send(
                        f"{skill['name']} wymaga Biegłości klasy {skill['unlock']}. "
                        f"Aktualna Biegłość {skill_class}: {mastery}."
                    )
                    return
                queue_type = self.skill_queue_type(skill)
                capacity = self.skill_queue_capacity(queue_type)
                if capacity <= 0:
                    await self.send(
                        f"Nie masz aktywnych slotów kolejki {self.skill_queue_type_label(queue_type)}."
                    )
                    return
                current = self.skill_queue_entries(queue_type)
                if len(current) >= capacity:
                    await self.send(
                        f"Kolejka {self.skill_queue_type_label(queue_type)} jest pełna: "
                        f"{len(current)} z {capacity} slotów. Level postaci {self.character.character_level}. "
                        "Rozwijaj Level postaci, aby odblokować więcej slotów."
                    )
                    return
                ok, result = self.server.db.add_skill_queue_entry(
                    self.account_id, queue_type, skill["id"]
                )
                if not ok:
                    await self.send(str(result))
                    return
                # v0.8.34: kolejka ma działać natychmiast po dodaniu skilla/spella.
                # Użytkownik nie musi już wykonywać osobnego `kolejka on`.
                self.server.db.set_skill_queue_enabled(self.account_id, True)
                await self.send(
                    f"Dodano do kolejki {self.skill_queue_type_label(queue_type)}: "
                    f"{skill['name']}. Slot {result} z {capacity}. "
                    "Auto kolejka została włączona. Jeśli walka już trwa, wpis może zostać użyty od najbliższej automatycznej akcji."
                )
                return

            if action in ("usun", "usuń", "remove", "delete", "-"):
                queue_type, position, skill = self.skill_queue_find_position(value)
                if not queue_type or not position:
                    await self.send(
                        "Nie znajduję takiego wpisu. Użyj np. kolejka usuń fizyczna 1, "
                        "kolejka usuń magiczna 2 albo kolejka usuń <nazwa skilla>."
                    )
                    return
                if skill is None:
                    rows = self.skill_queue_entries(queue_type)
                    skill = next(
                        (self.skill_by_id(row["skill_id"]) for row in rows if int(row["position"]) == position),
                        None,
                    )
                removed = self.server.db.remove_skill_queue_entry(
                    self.account_id, queue_type, position
                )
                if not removed:
                    await self.send("Nie ma takiego slotu w kolejce.")
                    return
                removed_skill = skill or self.skill_by_id(removed)
                name = removed_skill["name"] if removed_skill else removed
                self.skill_queue_cursors[queue_type] = 0
                await self.send(f"Usunięto z kolejki: {name}.")
                return

            if action in ("wyczysc", "wyczyść", "clear"):
                normalized_value = self.normalize_description_query(value)
                if normalized_value in ("f", "fiz", "fizyczna", "fizyczne", "physical"):
                    self.server.db.clear_skill_queue(self.account_id, "physical")
                    self.skill_queue_cursors["physical"] = 0
                    await self.send("Wyczyszczono kolejkę fizyczną.")
                elif normalized_value in ("m", "mag", "magiczna", "magiczne", "magic"):
                    self.server.db.clear_skill_queue(self.account_id, "magic")
                    self.skill_queue_cursors["magic"] = 0
                    await self.send("Wyczyszczono kolejkę magiczną.")
                else:
                    self.server.db.clear_skill_queue(self.account_id)
                    self.skill_queue_cursors = {"physical": 0, "magic": 0}
                    await self.send("Wyczyszczono obie kolejki skilli.")
                return

            if action in ("gora", "góra", "up", "dol", "dół", "down"):
                queue_type, position, _skill = self.skill_queue_find_position(value)
                if not queue_type or not position:
                    await self.send("Użycie: kolejka góra fizyczna 2 albo kolejka dół magiczna 1.")
                    return
                delta = -1 if action in ("gora", "góra", "up") else 1
                if not self.server.db.move_skill_queue_entry(
                    self.account_id, queue_type, position, delta
                ):
                    await self.send("Nie można przesunąć tego slotu w wybranym kierunku.")
                    return
                self.skill_queue_cursors[queue_type] = 0
                await self.send("Kolejność skilli została zmieniona.")
                return

            await self.send(
                "Użycie: kolejka, kolejka lista [fizyczna|magiczna], kolejka dodaj <skill>, "
                "kolejka usuń fizyczna <slot> / kolejka usuń magiczna <slot>, "
                "kolejka wyczyść, kolejka fizyczna, kolejka magiczna, kolejka on/off."
            )

    def cleanup_skill_buffs(self):
            """Usuń wygasłe czasowe buffy i ogłoś naturalne wygaśnięcie dokładnie raz."""
            now = time.time()
            buffs = getattr(self, "active_skill_buffs", {})
            expired_names = []
            for skill_id, data in list(buffs.items()):
                if now >= float(data.get("until", 0.0) or 0.0):
                    removed = buffs.pop(skill_id, None)
                    if removed:
                        expired_names.append(str(removed.get("name") or skill_id))
            for name in expired_names:
                try:
                    asyncio.get_running_loop().create_task(
                        self.send(f"Buff wygasł: {name}.")
                    )
                except RuntimeError:
                    # Poza działającą pętlą asyncio (np. statyczny audit) nie ma klienta,
                    # któremu można wysłać komunikat.
                    pass

    def skill_buff_active(self, skill_id):
            self.cleanup_skill_buffs()
            return skill_id in getattr(self, "active_skill_buffs", {})

    def skill_buff_multiplier(self, exclude_skill_id=None):
            """Łączny mnożnik wszystkich aktywnych buffów.

            Bonusy sumują się addytywnie (+35% i +55% = +90%), więc różne buffy
            nadal mogą działać razem i uniwersalnie wzmacniają wszystkie skille/spelle.
            v0.8.64 ogranicza łączny bonus do +125% (x2.25). Buffy nie wzmacniają
            siły kolejnego buffa - zapobiega to pętli multiclass buff->buff.
            """
            self.cleanup_skill_buffs()
            total_bonus = 0.0
            for skill_id, data in getattr(self, "active_skill_buffs", {}).items():
                if exclude_skill_id and skill_id == exclude_skill_id:
                    continue
                total_bonus += max(0.0, float(data.get("boost", 1.0) or 1.0) - 1.0)
            return min(2.25, 1.0 + total_bonus)

    def clear_skill_buffs(self):
            getattr(self, "active_skill_buffs", {}).clear()

    def local_party_buff_recipients_v03511(self):
            """All living party members standing with the caster, including solo self."""
            recipients = self.server.party_sessions(
                self.account_id, same_room=self.character.room_id
            ) or [self]
            valid = [
                session for session in recipients
                if not session.closed and session.character and session.current_hp > 0
                and session.character.room_id == self.character.room_id
            ]
            if self not in valid and self.character and not self.closed and self.current_hp > 0:
                valid.append(self)
            return sorted(valid, key=lambda session: session.character.name.casefold())

    def apply_party_boost_v03511(self, skill_id, name, boost, until, source=None):
            """Apply one combat boost to every living local party member."""
            recipients = self.local_party_buff_recipients_v03511()
            data = {
                "name": str(name),
                "boost": max(1.0, float(boost or 1.0)),
                "until": float(until),
                "source": str(source or self.character.name),
            }
            for session in recipients:
                session.active_skill_buffs[str(skill_id)] = dict(data)
            return recipients

    def party_vmax_support_active_v03511(self):
            """V-MAX party support grants Protect/Shell/Regen without granting Mec-only skill rewrites."""
            return (
                self.mec_vmax_active_v0319()
                or time.time() < float(getattr(self, "v03511_party_vmax_until", 0.0) or 0.0)
            )

    def engineer_skill_known_v0317(self, skill_id):
            try:
                return bool(self.server.db.knows_skill(self.account_id, skill_id))
            except Exception:
                return False

    def engineer_upgrade_slots_v0317(self):
            slots = 1
            if self.engineer_skill_known_v0317("v0317_engineer_silver_gear"):
                slots += 1
            if self.engineer_skill_known_v0317("v0317_engineer_gold_battery"):
                slots += 1
            return slots

    def engineer_upgraded_tools_v0317(self):
            try:
                rows = self.server.db.conn.execute(
                    "SELECT skill_id FROM engineer_tool_upgrades_v0317 WHERE account_id=? ORDER BY upgraded_at, skill_id",
                    (int(self.account_id),),
                ).fetchall()
                return {str(row["skill_id"]) for row in rows}
            except Exception:
                return set()

    def engineer_tool_is_upgraded_v0317(self, skill):
            return str(skill.get("id", "")) in self.engineer_upgraded_tools_v0317()

    def engineer_passive_multiplier_v0317(self, skill):
            category = str(skill.get("engineer_category", ""))
            mult = 1.0
            pairs = []
            if category == "single": pairs.append("v0317_engineer_hypercharge")
            if category == "area": pairs.append("v0317_engineer_lindblum")
            for sid in pairs:
                if not self.engineer_skill_known_v0317(sid):
                    continue
                row = self.server.db.skill_progress(self.account_id, sid)
                level = int(row["level"])
                progress = (max(1, min(SKILL_MAX_LEVEL, level)) - 1) / float(max(1, SKILL_MAX_LEVEL - 1))
                mult *= 1.05 + 0.25 * (progress ** 0.82)
            return mult


    def mec_skill_known_v0319(self, skill_id):
            try:
                return bool(self.server.db.knows_skill(self.account_id, skill_id))
            except Exception:
                return False

    def mec_vmax_active_v0319(self):
            return time.time() < float(getattr(self, "v0319_vmax_until", 0.0) or 0.0)

    def mec_overheat_active_v0319(self):
            return time.time() < float(getattr(self, "v0319_overheat_until", 0.0) or 0.0)

    async def mec_refresh_vmax_v0319(self):
            now=time.time()
            until=float(getattr(self,"v0319_vmax_until",0.0) or 0.0)
            if until and now >= until:
                self.v0319_vmax_until=0.0
                # UOSS source confirms Overheat after V-MAX; exact duration is not supplied,
                # so Soulbound uses a short 20-second recovery window.
                _vd,_vc=self.server.db.vmax_upgrades_v03114(self.account_id)
                _overheat=max(4,20-8*_vc)
                self.v0319_overheat_until=max(float(getattr(self,"v0319_overheat_until",0.0) or 0.0),now+_overheat)
                self.active_skill_buffs.pop("v0319_mec_vmax",None)
                await self.send(f"V-MAX wygasa. OVERHEAT: wszystkie statystyki bojowe są osłabione przez {_overheat} sekund i V-MAX nie może być ponownie użyty.")

    def mec_branch_multiplier_v0319(self, branch):
            mult=1.0
            checks={
              "melee":("v0319_mec_combat_mastery","v0319_mec_strength_protocol"),
              "ranged":("v0319_mec_shooting_mastery","v0319_mec_ranged_protocol"),
              "feedback":(None,"v0319_mec_feedback_protocol"),
              "magic":("v0319_mec_maxwell_program","v0319_mec_magic_protocol"),
            }
            for sid in checks.get(branch,()):
                if sid and self.mec_skill_known_v0319(sid):
                    row=self.server.db.skill_progress(self.account_id,sid)
                    level=int(row["level"]); progress=(max(1,min(SKILL_MAX_LEVEL,level))-1)/float(max(1, SKILL_MAX_LEVEL-1))
                    mult*=1.04 + 0.21*(progress**0.82)
            if self.mec_overheat_active_v0319(): mult*=0.75
            return mult

    def engineer_upgrade_effect_text_v0319(self, special, upgraded):
            if not upgraded: return "bazowe"
            return {
              "auto_crossbow":"więcej obrażeń", "mako_gun":"więcej obrażeń + dobór najlepszego elementu",
              "bio_blaster":"więcej obrażeń + mocniejszy Poison", "flash":"więcej obrażeń + Blind/Guard Break",
              "debilitator":"3 podatności żywiołowe", "drill":"więcej obrażeń + dispel pozytywnych efektów + pęknięcie pancerza",
              "napalm":"więcej obrażeń + łatwopalny olej", "launcher":"do 6 pocisków",
              "noise_blaster":"obrażenia obszarowe + dłuższe Silence + Slow", "chainsaw":"Demi -> Quarter + HP Leak",
              "mega_bomb":"zwiększone obrażenia wszystkim celom", "air_anchor":"większy proc damage",
            }.get(special,"ulepszony efekt")

    def auto_queue_skill_usable(self, skill, mob):
            if not skill:
                return False
            skill_class = self.skill_class_name(skill)
            if skill_class not in self.active_class_names():
                return False
            if not self.server.db.knows_skill(self.account_id, skill["id"]):
                return False
            if not self.skill_mastery_unlocked(skill):
                return False
            if self.skill_cooldowns.get(skill["id"], 0) > time.time():
                return False
            if int(skill.get("mana", 0)) > self.current_mana:
                return False

            kind = skill.get("kind")
            if kind in ("passive", "utility"):
                return False
            if kind in ("damage", "drain", "execute", "aoe_damage"):
                if not mob or not mob.alive or mob.room_id != self.character.room_id:
                    return False
            elif kind == "heal":
                recipients = self.server.party_sessions(
                    self.account_id, same_room=self.character.room_id
                ) or [self]
                if not any(
                    session.current_hp < session.max_hp()
                    for session in recipients
                    if not session.closed and session.character and session.current_hp > 0
                ):
                    return False
            elif kind == "group_heal":
                recipients = self.server.party_sessions(
                    self.account_id, same_room=self.character.room_id
                ) or [self]
                if not any(session.current_hp < session.max_hp() for session in recipients):
                    return False
            elif kind == "guard" and self.skill_guard > 0:
                return False
            elif kind == "evade":
                if self.skill_evade:
                    return False
            elif kind == "boost":
                # Nie ponawiaj tego samego buffa, dopóki jeszcze działa. Inne buffy
                # mogą być aktywowane równocześnie i składają się addytywnie.
                if self.skill_buff_active(skill.get("id")):
                    return False
            return True

    async def try_auto_skill_queue(self, mob):
            if not self.server.db.skill_queue_enabled(self.account_id):
                return False

            preferred = self.skill_queue_next_type
            order = [preferred, "magic" if preferred == "physical" else "physical"]
            for queue_type in order:
                rows = self.skill_queue_entries(queue_type, active_only=True)
                if not rows:
                    continue
                count = len(rows)
                start = self.skill_queue_cursors.get(queue_type, 0) % count
                for offset in range(count):
                    index = (start + offset) % count
                    row = rows[index]
                    skill = self.skill_by_id(row["skill_id"])
                    if not self.auto_queue_skill_usable(skill, mob):
                        continue
                    self.skill_queue_cursors[queue_type] = (index + 1) % count
                    self.skill_queue_next_type = (
                        "magic" if queue_type == "physical" else "physical"
                    )
                    # combat_mob_key jest już ustawiony przez attack(), więc skille
                    # ofensywne automatycznie trafiają bieżący cel.
                    self.auto_queue_casting = True
                    try:
                        await self.use_class_skill(skill["name"])
                    finally:
                        self.auto_queue_casting = False
                    return True
            return False

    async def use_class_skill(self, raw):
            skill, target_text = self.find_skill_from_input(raw)
            if not skill:
                await self.send("Nie rozpoznaję tej umiejętności albo naturalny skrót jest niejednoznaczny. Wpisz skills albo umiejetnosci i użyj pełnej nazwy.")
                return

            skill_class = self.skill_class_name(skill)
            mastery = self.class_mastery_level(skill_class)
            if mastery < int(skill["unlock"]):
                await self.send(
                    f"{skill['name']} wymaga Biegłości klasy {skill['unlock']}. "
                    f"Aktualna Biegłość {skill_class}: {mastery}."
                )
                return

            if not self.server.db.knows_skill(self.account_id, skill["id"]):
                skill_class = self.skill_class_name(skill)
                teacher_id, teacher = self.class_teacher(skill_class)
                await self.send(
                    f"Nie znasz jeszcze umiejętności {skill['name']} klasy "
                    f"{skill_class}. Musisz nauczyć się jej u {teacher['name']} "
                    f"w lokacji {ROOMS[teacher['room']]['name']}."
                )
                return

            progress = self.server.db.skill_progress(self.account_id, skill["id"])
            skill_level = int(progress["level"])
            skill_power = skill_power_multiplier(skill_level)
            effective_cooldown = self.effective_skill_cooldown(skill, skill_level)

            now = time.time()
            await self.mec_refresh_vmax_v0319()
            ready_at = self.skill_cooldowns.get(skill["id"], 0)
            if ready_at > now:
                await self.send(
                    f"{skill['name']} jest na cooldownie jeszcze {int(ready_at - now + 0.999)} sekund."
                )
                return
            mana_cost = skill.get("mana", 0)
            if mana_cost > self.current_mana:
                await self.send(
                    f"Za mało Many. {skill['name']} wymaga {mana_cost}, a masz {self.current_mana}."
                )
                return

            kind = skill["kind"]
            if kind == "passive":
                await self.send(f"{skill['name']} jest umiejętnością pasywną i działa automatycznie, gdy jest nauczona.")
                return
            if kind == "evade" and self.skill_evade:
                await self.send("Masz już aktywny gwarantowany unik.")
                return
            offensive = kind in ("damage", "drain", "execute", "aoe_damage")
            mob = None
            aoe_mobs = []
            if kind == "aoe_damage":
                if self.auto_fishing or self.auto_fishing_task:
                    await self.stop_auto_fishing(announce=False)
                    await self.send("Auto-łowienie wyłączone z powodu walki.")
                if self.auto_mining or self.auto_mining_task:
                    await self.stop_auto_mining(announce=False)
                    await self.send("Auto-kopanie wyłączone z powodu walki.")
                if self.auto_woodcutting or self.auto_woodcutting_task:
                    await self.stop_auto_woodcutting(announce=False)
                    await self.send("Auto-Drwalstwo wyłączone z powodu walki.")
                self.server.world.refresh()
                aoe_mobs = [
                    candidate for candidate in self.server.world.room_mobs(self.character.room_id)
                    if candidate.alive
                ]
                if not aoe_mobs:
                    await self.send("Nie ma tutaj żywych przeciwników dla czaru obszarowego.")
                    return
                # Najpierw czyścimy osierocone aggro. Dzięki temu mob nie jest
                # blokowany przez gracza, którego już nie ma w pokoju lub walce.
                for candidate in aoe_mobs:
                    self.server.sanitize_mob_engagement(candidate)
                # Zachowujemy właściciela aggro sprzed AoE. Obszarówka może zranić
                # moba walczącego z obcym graczem, ale nie kradnie jego aggro/nagród.
                aoe_reward_owner = {candidate.key: candidate.engaged_by for candidate in aoe_mobs}
                available_for_aggro = [
                    candidate for candidate in aoe_mobs
                    if self.server.engagement_allowed(self, candidate)
                ]
                for candidate in available_for_aggro:
                    if not candidate.engaged_by:
                        if candidate.engaged_at <= 0:
                            candidate.engaged_at = time.monotonic()
                        candidate.engaged_by = self.character.name
                        candidate.combat_turn = 0
                        candidate.player_hits = 0
                # Realtime target ustawiamy tylko na moba, którego wolno nam normalnie
                # zaatakować. Samo AoE nadal obejmuje cały pokój.
                mob = next(
                    (candidate for candidate in available_for_aggro if candidate.key == self.combat_mob_key),
                    available_for_aggro[0] if available_for_aggro else None,
                )
                if mob is not None:
                    self.combat_mob_key = mob.key
            elif offensive:
                if self.auto_fishing or self.auto_fishing_task:
                    await self.stop_auto_fishing(announce=False)
                    await self.send("Auto-łowienie wyłączone z powodu walki.")
                if self.auto_mining or self.auto_mining_task:
                    await self.stop_auto_mining(announce=False)
                    await self.send("Auto-kopanie wyłączone z powodu walki.")
                if self.auto_woodcutting or self.auto_woodcutting_task:
                    await self.stop_auto_woodcutting(announce=False)
                    await self.send("Auto-Drwalstwo wyłączone z powodu walki.")
                mob = await self.skill_combat_target(target_text)
                if not mob:
                    return

            self.current_mana -= mana_cost
            self.skill_cooldowns[skill["id"]] = now + effective_cooldown

            # v0.31.7: Engineer authored tool mechanics.
            if skill.get("engineer_tool"):
                special = str(skill.get("engineer_special", ""))
                upgraded = self.engineer_tool_is_upgraded_v0317(skill)
                passive_mult = self.engineer_passive_multiplier_v0317(skill)

                if special == "upgrade":
                    query = (target_text or "").strip()
                    if not query:
                        active = self.engineer_upgraded_tools_v0317()
                        names = [row["name"] for row in CLASS_SKILLS.get("Inżynier", []) if row.get("id") in active]
                        details=[]
                        for row in CLASS_SKILLS.get("Inżynier", []):
                            if row.get("id") in active:
                                details.append(f"{row['name']} ({self.engineer_upgrade_effect_text_v0319(row.get('engineer_special',''), True)})")
                        await self.send(
                            f"Upgrade 2.0: sloty {len(active)}/{self.engineer_upgrade_slots_v0317()}. " +
                            ("Ulepszone: " + "; ".join(details) + "." if details else "Brak ulepszonych narzędzi.") +
                            " Użyj: Upgrade <nazwa narzędzia> albo Upgrade reset."
                        )
                        return
                    if normalize_lookup_text(query) in ("reset","clear","wyczysc","wyczyść"):
                        self.server.db.conn.execute("DELETE FROM engineer_tool_upgrades_v0317 WHERE account_id=?",(int(self.account_id),))
                        self.server.db.conn.commit()
                        await self.send("Upgrade: wyczyszczono wszystkie sloty ulepszeń Inżyniera.")
                        await self.grant_skill_use_xp(skill)
                        return
                    candidates=[row for row in CLASS_SKILLS.get("Inżynier", []) if row.get("engineer_tool") and row.get("engineer_special") not in ("upgrade","scanner") and row.get("kind") != "passive"]
                    target=None
                    qn=normalize_lookup_text(query)
                    for row in candidates:
                        if qn in {normalize_lookup_text(row.get("name","")), normalize_lookup_text(row.get("id","")), *[normalize_lookup_text(a) for a in row.get("aliases",[])]}:
                            target=row; break
                    if not target:
                        await self.send("Upgrade: nie rozpoznaję narzędzia Inżyniera do ulepszenia.")
                        return
                    current=self.engineer_upgraded_tools_v0317()
                    if target["id"] in current:
                        await self.send(f"{target['name']} jest już ulepszone.")
                        return
                    if len(current) >= self.engineer_upgrade_slots_v0317():
                        await self.send(f"Brak wolnego slotu Upgrade. Masz {len(current)}/{self.engineer_upgrade_slots_v0317()}. Użyj Upgrade reset albo naucz się Silver Gear / Gold Battery.")
                        return
                    if self.available_recipe_item("engineer_upgrade_kit") <= 0:
                        await self.send("Ulepszenie wymaga 1 Zestawu Upgrade Inżyniera. Wykonaj go przez techcraft zestaw upgrade.")
                        return
                    if not self.consume_recipe_item("engineer_upgrade_kit", 1):
                        await self.send("Nie udało się pobrać Zestawu Upgrade Inżyniera.")
                        return
                    self.server.db.conn.execute("INSERT OR IGNORE INTO engineer_tool_upgrades_v0317(account_id,skill_id) VALUES(?,?)",(int(self.account_id),target["id"]))
                    self.server.db.conn.commit()
                    await self.send(f"Upgrade: {target['name']} zostało ulepszone. Zużyto 1 Zestaw Upgrade Inżyniera. Sloty {len(current)+1}/{self.engineer_upgrade_slots_v0317()}.")
                    await self.grant_skill_use_xp(skill)
                    return

                if special == "scanner":
                    if not mob:
                        return
                    template=MOB_TEMPLATES[mob.template_id]
                    weaknesses=template.get("weaknesses") or template.get("machine_weaknesses") or ("brak jawnych",)
                    resistances=template.get("resistances") or template.get("machine_resistances") or ("brak jawnych",)
                    await self.send(
                        f"Scanner: {template.get('name',mob.template_id)}. HP {max(0,mob.hp)} z {template.get('max_hp',0)}. "
                        f"Typ: {'Machine' if template.get('machine') else template.get('type','organic')}. "
                        f"Ranga: {template.get('rank','normal')}. Słabości: {', '.join(map(str,weaknesses))}. "
                        f"Odporności: {', '.join(map(str,resistances))}."
                    )
                    await self.grant_skill_use_xp(skill)
                    return

                if special == "debilitator":
                    if not mob:
                        return
                    elements=("fire","ice","lightning","water","holy","dark")
                    count=3 if upgraded else 1
                    picked=random.sample(elements,count)
                    duration=45 if self.engineer_skill_known_v0317("v0317_engineer_kinematics") else 30
                    mob.v0317_vulnerabilities=set(picked)
                    mob.v0317_vulnerability_until=time.time()+duration
                    await self.send(f"Debilitator: {MOB_TEMPLATES[mob.template_id]['name']} otrzymuje słabość: {', '.join(picked)} na {duration} s.")
                    await self.grant_skill_use_xp(skill)
                    return

                if special == "launcher":
                    alive=[target for target in aoe_mobs if target.alive]
                    if not alive:
                        return
                    hits=6 if upgraded else 4
                    targets=random.choices(alive,k=hits)
                    total=0; defeated=[]; seen=set()
                    for target in targets:
                        if not target.alive: continue
                        before=max(1,target.hp)
                        damage=max(1,before//2)
                        target.hp-=damage; total+=damage
                        name=MOB_TEMPLATES[target.template_id]['name']
                        await self.send(f"Launcher: {name} traci połowę bieżącego HP: {damage}. HP {max(0,target.hp)}.")
                        if target.hp<=0 and target.key not in seen:
                            seen.add(target.key); defeated.append(target)
                    await self.grant_skill_use_xp(skill)
                    await self.send(f"Launcher: {hits} pocisków, łączne obrażenia {total}.")
                    for target in defeated:
                        await self.mob_defeated(target)
                    if any(x.alive for x in alive): await self.ensure_realtime_combat()
                    return

                if special in ("auto_crossbow","mako_gun","bio_blaster","flash","drill","napalm","noise_blaster","chainsaw","mega_bomb","air_anchor"):
                    base=max(1,int(skill.get("base_power",100) or 100))
                    upgrade_mult=1.30 if upgraded else 1.0
                    if special in ("drill","chainsaw","air_anchor"): upgrade_mult=1.35 if upgraded else 1.0
                    if special=="mako_gun":
                        element="lightning" if upgraded and mob and MOB_TEMPLATES[mob.template_id].get("machine") else random.choice(("fire","ice","lightning","water","holy","dark"))
                    else:
                        element={"bio_blaster":"bio poison","flash":"holy","napalm":"fire","noise_blaster":"sound"}.get(special,"")
                    if special in ("auto_crossbow","bio_blaster","flash","napalm","noise_blaster","mega_bomb"):
                        targets=[x for x in aoe_mobs if x.alive]
                    else:
                        targets=[mob] if mob else []
                    total=0; defeated=[]; seen=set()
                    for i,target in enumerate(targets):
                        template=MOB_TEMPLATES[target.template_id]
                        # Mega Bomb: full damage main target, reduced splash normally.
                        local_mult=passive_mult*upgrade_mult*skill_power*self.skill_buff_multiplier()
                        if special=="mega_bomb" and i>0 and not upgraded: local_mult*=0.55
                        # Chainsaw can use Demi / upgraded Quarter as a floor effect.
                        if special=="chainsaw":
                            remaining_fraction=0.25 if upgraded else 0.50
                            damage=max(int(base*local_mult), int(max(1,target.hp)*(1.0-remaining_fraction)))
                        else:
                            damage=max(1,int(base*local_mult)+random.randint(-3,3))
                        # Drill bypasses boss defense/protect-shell equivalent.
                        if special!="drill": damage=await self.apply_boss_defense(target,damage)
                        damage=self.v0210_adjust_player_damage(damage)
                        # Debilitator vulnerabilities apply to matching elemental tools.
                        if time.time() < float(getattr(target,"v0317_vulnerability_until",0.0) or 0.0) and element in set(getattr(target,"v0317_vulnerabilities",set()) or set()):
                            damage=int(round(damage*1.50))
                        if time.time() < float(getattr(target,"v0317_oiled_until",0.0) or 0.0) and "fire" in element:
                            damage=int(round(damage*1.25))
                        damage,mnote=v0314_adjust_damage_vs_template(template,damage,element or "physical",skill.get("name",""))
                        target.hp-=damage; total+=damage
                        await self.send(f"{skill['name']}: {template['name']} otrzymuje {damage} obrażeń. HP {max(0,target.hp)}.{mnote}")
                        if special=="napalm" and upgraded:
                            duration=45 if self.engineer_skill_known_v0317("v0317_engineer_kinematics") else 30
                            target.v0317_oiled_until=time.time()+duration
                        if special=="bio_blaster":
                            duration=(40 if upgraded else 25) + (15 if self.engineer_skill_known_v0317("v0317_engineer_kinematics") else 0)
                            target.v0319_poison_until=time.time()+duration
                            target.v0319_poison_power=max(1,int(base*(0.12 if upgraded else 0.07)))
                        if special=="flash" and upgraded:
                            target.v0319_blind_until=time.time()+45
                            target.v0319_guard_break_until=time.time()+25
                        if special=="drill" and upgraded:
                            target.v0319_armor_break_until=time.time()+30
                        if special=="noise_blaster" and upgraded:
                            target.v0319_silence_until=time.time()+45
                            target.v0319_slow_until=time.time()+30
                        if special=="chainsaw" and upgraded:
                            target.v0319_hp_leak_until=time.time()+30
                        if special=="air_anchor":
                            target.v0319_air_anchor_until=time.time()+(45 if upgraded else 30)
                            target.v0319_air_anchor_power=max(1,int(base*(0.16 if upgraded else 0.10)))
                        if target.hp<=0 and target.key not in seen:
                            seen.add(target.key); defeated.append(target)
                    await self.grant_skill_use_xp(skill)
                    await self.send(f"{skill['name']}: łączne obrażenia {total}." + (" ULEPSZONE." if upgraded else ""))
                    for target in defeated: await self.mob_defeated(target)
                    if any(x.alive for x in targets if x): await self.ensure_realtime_combat()
                    return


            # v0.31.9: Full authored Mec mechanics from the supplied UOSSMUD ability list.
            if skill.get("mec_authored"):
                special=str(skill.get("mec_special","")); branch=str(skill.get("mec_branch",""))
                vmax=self.mec_vmax_active_v0319()
                if special=="vmax":
                    if vmax:
                        await self.send("V-MAX jest już aktywny."); return
                    if self.mec_overheat_active_v0319():
                        await self.send(f"V-MAX zablokowany przez Overheat jeszcze przez {int(getattr(self,'v0319_overheat_until',0)-time.time()+.999)} s."); return
                    will=max(1,int(self.effective_willpower()))
                    _vd,_vc=self.server.db.vmax_upgrades_v03114(self.account_id)
                    _skill_progress=(max(1,min(SKILL_MAX_LEVEL,skill_level))-1)/float(max(1, SKILL_MAX_LEVEL-1))
                    _skill_duration_mult=1.0 + 0.80*(_skill_progress**0.90)
                    duration=min(180,int(round((25 + will//8 + 10*_vd)*_skill_duration_mult)))  # v0.33.0: Skill Level V-MAX rozwija czas działania.
                    self.v0319_vmax_until=time.time()+duration
                    recipients = self.apply_party_boost_v03511(
                        skill["id"], "V-MAX", 1.30, self.v0319_vmax_until, self.character.name
                    )
                    for session in recipients:
                        session.v03511_party_vmax_until = max(
                            float(getattr(session, "v03511_party_vmax_until", 0.0) or 0.0),
                            self.v0319_vmax_until,
                        )
                    await self.send(
                        f"V-MAX aktywny przez {duration} s dla {len(recipients)} członków drużyny w tej lokacji. "
                        "Wszyscy otrzymują +30 procent do skilli/spelli oraz Protect, Shell i Regen. "
                        "Mec uruchamiający V-MAX zachowuje też swoje specjalne zmiany skilli."
                    )
                    for session in recipients:
                        if session is self:
                            continue
                        await session.send(
                            f"{self.character.name} aktywuje V-MAX. Przez {duration} s otrzymujesz +30 procent do skilli/spelli oraz Protect, Shell i Regen."
                        )
                    await self.grant_skill_use_xp(skill); return

                if special in ("cure_beam","heal_beam"):
                    # Reuse Soulbound smart healing. Heal Beam's Support Effect becomes party-wide during V-MAX.
                    if special=="heal_beam" and vmax:
                        recipients=self.server.party_sessions(self.account_id,same_room=self.character.room_id) or [self]
                        total=0
                        for sess in recipients:
                            if sess.closed or not sess.character or sess.current_hp<=0: continue
                            amount=max(1,int(sess.max_hp()*(0.45*skill_power)))
                            before=sess.current_hp; sess.current_hp=min(sess.max_hp(),sess.current_hp+amount); total+=sess.current_hp-before
                        await self.send(f"Heal Beam — Support Effect: cała drużyna odzyskuje łącznie {total} HP.")
                        await self.grant_skill_use_xp(skill); return
                    # let generic heal handler below handle single target

                if special in ("cosmic_rave","shoot_all","starlight_shower","shock_soldier","pop_knight","range_fire","dispose","uzi_punch","laser_spin","area_bomb","maelstrom","shock"):
                    alive=[x for x in aoe_mobs if x.alive]
                    if not alive: return
                    if special=="cosmic_rave" and vmax:
                        targets=random.choices(alive,k=5)
                    elif special=="starlight_shower" and not vmax:
                        targets=[mob] if mob else [alive[0]]
                    elif special=="uzi_punch":
                        targets=random.choices(alive,k=min(5,max(2,len(alive))))
                    else:
                        targets=list(alive)
                    base=max(1,int(skill.get("base_power",100) or 100)); total=0; defeated=[]; seen=set()
                    mult=skill_power*self.mec_branch_multiplier_v0319(branch)*self.skill_buff_multiplier(exclude_skill_id="v0319_mec_vmax")
                    if special=="shoot_all" and vmax: mult*=1.35
                    if special=="starlight_shower" and vmax: mult*=1.25
                    for target in targets:
                        if not target.alive: continue
                        template=MOB_TEMPLATES[target.template_id]
                        damage=max(1,int(base*mult)+random.randint(-6,6))
                        damage,crit=self.roll_critical_hit(damage)
                        if special=="shoot_all" and vmax and random.random()<0.20:
                            damage=int(damage*1.5); crit=True
                        damage=await self.apply_boss_defense(target,damage); damage=self.v0210_adjust_player_damage(damage)
                        element={"laser_spin":"dark","area_bomb":"fire","maelstrom":"water","shock":"lightning","starlight_shower":"magic"}.get(special,"physical")
                        damage,note=v0314_adjust_damage_vs_template(template,damage,element,skill.get("name",""))
                        target.hp-=damage; total+=damage
                        await self.send(f"{skill['name']}: {template['name']} {damage} obrażeń. HP {max(0,target.hp)}.{note}")
                        if target.hp<=0 and target.key not in seen: seen.add(target.key); defeated.append(target)
                    await self.grant_skill_use_xp(skill)
                    await self.send(f"{skill['name']}: łączne obrażenia {total}, pokonani {len(defeated)}.")
                    for target in defeated: await self.mob_defeated(target)
                    if any(x.alive for x in alive): await self.ensure_realtime_combat()
                    return

                if special in ("hypno_flash","jammer","logic_bomb"):
                    if not mob: return
                    template=MOB_TEMPLATES[mob.template_id]
                    duration=30
                    if special=="hypno_flash": mob.v0319_sleep_until=time.time()+duration
                    elif special=="jammer":
                        duration=45 if template.get("machine") else 25
                        targets=[x for x in aoe_mobs if x.alive] if vmax else [mob]
                        for t in targets: t.v0319_disabled_until=time.time()+duration
                    else:
                        mob.v0319_silence_until=time.time()+duration; mob.v0319_slow_until=time.time()+duration
                        if vmax: mob.v0319_blind_until=time.time()+duration; mob.v0319_disabled_until=time.time()+duration
                    await self.send(f"{skill['name']}: efekt kontroli na {template['name']} przez {duration} s" + (". Support Effect aktywny." if vmax else "."))
                    await self.grant_skill_use_xp(skill); return

                if special=="satellite_linker" and mob:
                    mob.v0319_satellite_until=time.time()+45; mob.v0319_satellite_power=max(1,int(skill.get("base_power",1000)*self.mec_branch_multiplier_v0319(branch)))
                if special=="tiger_rampage" and mob: mob.v0319_armor_break_until=time.time()+30
                if special=="mec_sonata" and mob and random.random()<0.40: mob.v0319_level_down_until=time.time()+30
                if special=="magnify" and random.random()<0.25: self.v0319_lock_until=time.time()+12
                # Other single-target Mec attacks continue through the normal Soulbound damage handler below.

            # v0.31.5: V-MAX is a dedicated Mec state used by Cosmic Rave.
            if skill.get("id") == "v0315_mec_vmax":
                duration = int(skill.get("duration", 30) or 30)
                recipients = self.apply_party_boost_v03511(
                    skill["id"], "V-MAX", float(skill.get("boost", 1.0) or 1.0),
                    now + duration, self.character.name
                )
                for session in recipients:
                    session.v03511_party_vmax_until = max(
                        float(getattr(session, "v03511_party_vmax_until", 0.0) or 0.0), now + duration
                    )
                await self.send(f"V-MAX aktywny drużynowo przez {duration} sekund. Cosmic Rave Meca wykona teraz 5 losowych trafień.")
                await self.grant_skill_use_xp(skill)
                return

            if skill.get("id") == "v0315_mec_cosmic_rave":
                # Use the room-wide target list already prepared for AoE.
                alive = [target for target in aoe_mobs if target.alive]
                if not alive:
                    await self.send("Nie ma tutaj żywych przeciwników dla Cosmic Rave.")
                    return
                vmax = self.skill_buff_active("v0315_mec_vmax")
                targets = random.choices(alive, k=5) if vmax else list(alive)
                base_power = int(skill.get("base_power", 2000) or 2000)
                multiplier = skill_power
                multiplier *= self.character.class_physical_damage_multiplier()
                multiplier *= self.character.racial_all_damage_multiplier()
                multiplier *= self.total_set_damage_multiplier()
                multiplier *= self.equipment_damage_multiplier("physical")
                multiplier *= self.skill_buff_multiplier(exclude_skill_id="v0315_mec_vmax")
                defeated_keys = set()
                defeated = []
                total_damage = 0
                await self.send(
                    f"Cosmic Rave. Moc bazowa {base_power}. " +
                    ("V-MAX: 5 losowych trafień." if vmax else f"Cele: wszyscy przeciwnicy ({len(alive)}).")
                )
                for target in targets:
                    if not target.alive:
                        continue
                    template = MOB_TEMPLATES[target.template_id]
                    damage = max(1, int(base_power * multiplier) + random.randint(-10, 10))
                    damage, critical = self.roll_critical_hit(damage)
                    damage = await self.apply_boss_defense(target, damage)
                    damage = self.v0210_adjust_player_damage(damage)
                    damage, _ = v0314_adjust_damage_vs_template(template, damage, "physical", "Cosmic Rave")
                    target.hp -= damage
                    total_damage += damage
                    await self.send(f"{template['name']}: Cosmic Rave {damage} obrażeń. HP {max(0,target.hp)} z {template['max_hp']}.")
                    if target.hp <= 0 and target.key not in defeated_keys:
                        defeated_keys.add(target.key); defeated.append(target)
                await self.grant_skill_use_xp(skill)
                await self.send(f"Cosmic Rave: łączne obrażenia {total_damage}, pokonani {len(defeated)}.")
                for target in defeated:
                    owner_name = aoe_reward_owner.get(target.key)
                    reward_session = self.server.find_character_session(owner_name) if owner_name and owner_name != self.character.name else self
                    if reward_session is None or reward_session.closed or not reward_session.character or reward_session.character.room_id != self.character.room_id:
                        reward_session = self
                    await reward_session.mob_defeated(target)
                survivors = [x for x in alive if x.alive and self.server.engagement_allowed(self, x)]
                if survivors:
                    self.combat_mob_key = survivors[0].key
                    await self.ensure_realtime_combat()
                return

            if kind == "boost":
                base_boost = float(skill.get("boost", 1.0) or 1.0)
                # v0.8.64: Skill Level rozwija buff wolniej niż bezpośredni damage.
                base_bonus = max(0.0, base_boost - 1.0)
                scaled_bonus = base_bonus * (1.0 + max(0.0, skill_power - 1.0) * 0.50)
                scaled_boost = 1.0 + min(0.90, scaled_bonus)
                duration = GLOBAL_SKILL_BUFF_DURATION_SECONDS
                recipients = self.apply_party_boost_v03511(
                    skill["id"], skill["name"], max(1.0, scaled_boost),
                    now + duration, self.character.name
                )
                bonus_pct = int(round((max(1.0, scaled_boost) - 1.0) * 100))
                total_pct = int(round((self.skill_buff_multiplier() - 1.0) * 100))
                await self.send(
                    f"Buff drużynowy aktywowany: {skill['name']}. "
                    f"Czas działania: {duration} sekund. "
                    f"Wzmocnienie: {bonus_pct} procent. "
                    f"Objęci członkowie: {sum(1 for x in recipients if not x.closed and x.character and x.current_hp > 0)}. "
                    f"Łączne aktywne wzmocnienie: {total_pct} procent."
                )
                for session in recipients:
                    if session is self or session.closed or not session.character or session.current_hp <= 0:
                        continue
                    await session.send(
                        f"{self.character.name} aktywuje buff {skill['name']}. "
                        f"Działa na ciebie przez {duration} sekund. "
                        f"Wzmocnienie: {bonus_pct} procent."
                    )
                await self.grant_skill_use_xp(skill)
                if self.combat_mob_key:
                    await self.ensure_realtime_combat()
                return

            if kind == "guard":
                buff_mult = self.skill_buff_multiplier()
                scaled_guard = max(
                    1,
                    int(round(skill.get("guard", 0) * skill_power * buff_mult)),
                )
                recipients = self.local_party_buff_recipients_v03511()
                for session in recipients:
                    session.skill_guard = max(session.skill_guard, scaled_guard)
                await self.send(
                    f"Drużynowy guard {skill['name']} na Skill Level {skill_level}. "
                    f"{len(recipients)} członków w tej lokacji: następne trafienie każdego zostanie dodatkowo zredukowane o {scaled_guard}."
                )
                for session in recipients:
                    if session is not self:
                        await session.send(
                            f"{self.character.name} używa {skill['name']}. Twój następny otrzymany cios zostanie dodatkowo zredukowany o {scaled_guard}."
                        )
                await self.grant_skill_use_xp(skill)
                if mana_cost:
                    await self.send(f"Mana: {self.current_mana} z {self.max_mana()}.")
                if self.combat_mob_key:
                    await self.ensure_realtime_combat()
                return

            if kind == "evade":
                recipients = self.local_party_buff_recipients_v03511()
                for session in recipients:
                    session.skill_evade = True
                await self.send(
                    f"Drużynowy unik {skill['name']} na Skill Level {skill_level}. "
                    f"{len(recipients)} członków w tej lokacji uniknie swojego następnego ataku przeciwnika."
                )
                for session in recipients:
                    if session is not self:
                        await session.send(
                            f"{self.character.name} używa {skill['name']}. Twój następny atak przeciwnika zostanie automatycznie uniknięty."
                        )
                await self.grant_skill_use_xp(skill)
                if self.combat_mob_key:
                    await self.ensure_realtime_combat()
                return

            if kind == "group_heal":
                recipients = self.server.party_sessions(self.account_id, same_room=self.character.room_id)
                if not recipients:
                    recipients = [self]
                heal_pct = min(0.45, skill.get("heal_pct", 0.20) * skill_power * self.character.racial_healing_multiplier() * self.character.class_healing_multiplier())
                heal_pct = min(0.60, heal_pct * self.skill_buff_multiplier())
                total_healed = 0
                for session in sorted(recipients, key=lambda target: target.character.name.lower()):
                    target_max = session.max_hp()
                    amount = max(1, int(target_max * heal_pct))
                    before = session.current_hp
                    session.current_hp = min(target_max, session.current_hp + amount)
                    actual = session.current_hp - before
                    total_healed += actual
                    if session is self:
                        await self.send(f"{skill['name']}: odzyskujesz {actual} HP. Masz {session.current_hp} z {target_max} HP.")
                    else:
                        await session.send(f"{self.character.name} używa {skill['name']}. Odzyskujesz {actual} HP. Masz {session.current_hp} z {target_max} HP.")
                _group_heal_msg = (
                    f"{self.character.name}: {skill['name']} leczy drużynę. "
                    f"Cele {len(recipients)}, przywrócono łącznie {total_healed} HP."
                )
                await self.send(f"Leczenie obszarowe obejmuje {len(recipients)} członków drużyny w tej lokacji. Wyleczono łącznie {total_healed} HP.")
                await self.server.party_combat_broadcast(self, _group_heal_msg)
                await self.grant_skill_use_xp(skill)
                if mana_cost:
                    await self.send(f"Mana: {self.current_mana} z {self.max_mana()}.")
                if self.combat_mob_key:
                    await self.ensure_realtime_combat()
                return

            if kind == "heal":
                # v0.31.6: zwykły heal pozostaje single-target, ale automatycznie
                # wybiera najbardziej rannego żywego członka party w tej samej
                # lokacji. Solo wybiera gracza. Skill nie marnuje się, gdy nikt
                # nie potrzebuje leczenia. group_heal nadal leczy całą drużynę.
                recipients = self.server.party_sessions(
                    self.account_id, same_room=self.character.room_id
                ) or [self]
                injured = [
                    session for session in recipients
                    if not session.closed and session.character and session.current_hp > 0
                    and session.current_hp < session.max_hp()
                ]
                if not injured:
                    await self.send(
                        f"{skill['name']}: nikt w drużynie w tej lokacji nie potrzebuje leczenia."
                    )
                    return
                target = min(
                    injured,
                    key=lambda session: (
                        session.current_hp / max(1, session.max_hp()),
                        session.current_hp,
                        session.character.name.lower(),
                    ),
                )
                heal_pct = min(
                    0.65,
                    skill.get("heal_pct", 0.25)
                    * skill_power
                    * self.character.racial_healing_multiplier()
                    * self.character.class_healing_multiplier()
                )
                heal_pct = min(0.80, heal_pct * self.skill_buff_multiplier())
                target_max = target.max_hp()
                heal = max(1, int(target_max * heal_pct))
                before = target.current_hp
                target.current_hp = min(target_max, target.current_hp + heal)
                actual = target.current_hp - before
                if target is self:
                    await self.send(
                        f"Używasz {skill['name']} na Skill Level {skill_level}. "
                        f"Odzyskujesz {actual} HP. Masz teraz {target.current_hp} z {target_max} HP."
                    )
                else:
                    await target.send(
                        f"{self.character.name} używa {skill['name']} na tobie. "
                        f"Odzyskujesz {actual} HP. Masz {target.current_hp} z {target_max} HP."
                    )
                    await self.send(
                        f"Używasz {skill['name']} na {target.character.name}. "
                        f"Przywrócono {actual} HP."
                    )
                await self.server.party_nearby_broadcast(
                    self,
                    f"{self.character.name}: {skill['name']} leczy {target.character.name} za {actual} HP.",
                    exclude=[self, target],
                    detail="normal",
                    history_category="combat",
                )
                if self.character.racial_healing_bonus_percent() > 0:
                    await self.send(
                        f"Bonus rasy {self.character.race}: "
                        f"+{self.character.racial_healing_bonus_percent()} procent mocy leczenia."
                    )
                class_heal_bonus = int(
                    round((self.character.class_healing_multiplier() - 1.0) * 100)
                )
                if class_heal_bonus > 0:
                    await self.send(
                        f"Bonus aktywnych klas: +{class_heal_bonus} procent "
                        "mocy leczenia."
                    )
                await self.grant_skill_use_xp(skill)
                if mana_cost:
                    await self.send(f"Mana: {self.current_mana} z {self.max_mana()}.")
                if self.combat_mob_key:
                    await self.ensure_realtime_combat()
                return

            if kind == "aoe_damage":
                scale = self.skill_scale_value(skill.get("scale", "intelligence"))
                multiplier = skill.get("mult", 1.0) * skill_power
                multiplier *= self.character.class_magic_damage_multiplier()
                multiplier *= self.character.racial_magic_damage_multiplier()
                multiplier *= self.character.racial_all_damage_multiplier()
                multiplier *= self.total_set_damage_multiplier()
                multiplier *= self.equipment_damage_multiplier("magic")
                multiplier *= self.skill_buff_multiplier()
                await self.send(
                    f"Używasz {skill['name']} na Skill Level {skill_level}. "
                    f"Cele w lokacji: {len(aoe_mobs)}."
                )
                defeated, survivors = [], []
                total_damage = 0
                critical_hits = 0
                for target in list(aoe_mobs):
                    if not target.alive:
                        continue
                    template = MOB_TEMPLATES[target.template_id]
                    damage = max(1, int((self.character.soul_power() + scale) * multiplier) + random.randint(-2, 3))
                    damage, critical = self.roll_critical_hit(damage)
                    if critical:
                        self.record_social_record_v03051("biggest_crit", damage)
                        critical_hits += 1
                    damage = await self.apply_boss_defense(target, damage)
                    damage = self.v0210_adjust_player_damage(damage)
                    damage, machine_note = v0314_adjust_damage_vs_template(
                        template, damage, "magic", skill.get("name", "")
                    )
                    target.hp -= damage
                    total_damage += damage
                    marker = " Krytyk." if critical else ""
                    await self.send(f"{template['name']}: {damage} obrażeń.{marker} HP {max(0, target.hp)} z {template['max_hp']}.")
                    (defeated if target.hp <= 0 else survivors).append(target)
                await self.grant_skill_use_xp(skill)
                if mana_cost:
                    await self.send(f"Mana: {self.current_mana} z {self.max_mana()}.")
                await self.send(f"{skill['name']}: łączne obrażenia {total_damage}, pokonani przeciwnicy {len(defeated)}.")
                _party_aoe = (
                    f"{self.character.name}: {skill['name']}, {total_damage} obrażeń łącznie, "
                    f"cele {len(aoe_mobs)}, pokonani {len(defeated)}"
                )
                if critical_hits:
                    _party_aoe += f", krytyki {critical_hits}"
                await self.server.party_combat_broadcast(self, _party_aoe + ".")
                for target in defeated:
                    owner_name = aoe_reward_owner.get(target.key)
                    reward_session = (
                        self.server.find_character_session(owner_name)
                        if owner_name and owner_name != self.character.name
                        else self
                    )
                    if (
                        reward_session is None
                        or reward_session.closed
                        or not reward_session.character
                        or reward_session.character.room_id != self.character.room_id
                    ):
                        reward_session = self
                    await reward_session.mob_defeated(target)
                counter = next(
                    (target for target in survivors
                     if target.alive and self.server.engagement_allowed(self, target)),
                    None,
                )
                if counter:
                    self.combat_mob_key = counter.key
                    await self.ensure_realtime_combat()
                elif self.combat_mob_key and not self.server.engagement_allowed(
                    self, self.server.world.mobs.get(self.combat_mob_key)
                ):
                    self.combat_mob_key = None
                return

            template = MOB_TEMPLATES[mob.template_id]
            scale = self.skill_scale_value(skill.get("scale", "strength"))
            multiplier = skill.get("mult", 1.0) * skill_power
            skill_class = self.skill_class_name(skill)
            skill_class_type = class_type_for_name(skill_class)
            if skill_class_type == "physical":
                multiplier *= self.character.class_physical_damage_multiplier()
                multiplier *= self.character.racial_physical_damage_multiplier()
            else:
                multiplier *= self.character.class_magic_damage_multiplier()
                multiplier *= self.character.racial_magic_damage_multiplier()
            multiplier *= self.character.racial_all_damage_multiplier()
            multiplier *= self.total_set_damage_multiplier()
            multiplier *= self.equipment_damage_multiplier(
                "physical" if skill_class_type == "physical" else "magic"
            )
            multiplier *= self.skill_buff_multiplier()

            if kind == "execute":
                hp_ratio = mob.hp / max(1, template["max_hp"])
                execute_threshold = v0863_execute_threshold(template)
                if hp_ratio <= execute_threshold:
                    multiplier *= min(2.0, float(skill.get("execute_mult", 1.5)))
                    await self.send(
                        f"Egzekucyjny próg aktywny: przeciwnik ma nie więcej niż "
                        f"{int(round(execute_threshold * 100))} procent HP."
                    )

            damage = max(
                1,
                int(
                    (self.character.soul_power() + scale) * multiplier
                ) + random.randint(-2, 3),
            )
            damage, critical = self.roll_critical_hit(damage)
            if critical:
                self.record_social_record_v03051("biggest_crit", damage)
                await self.send(
                    f"TRAFIENIE KRYTYCZNE umiejętnością "
                    f"{skill['name']}! Zręczność "
                    f"{self.effective_dexterity()}. "
                    f"Szansa: "
                    f"{int(round(self.critical_chance() * 100))} procent."
                )
            damage = await self.apply_boss_defense(mob, damage)
            damage = self.v0210_adjust_player_damage(damage)
            damage, machine_note = v0314_adjust_damage_vs_template(
                template, damage,
                "physical" if skill_class_type == "physical" else "magic",
                skill.get("name", ""),
            )
            mob.hp -= damage
            # v0.34.6: cechy Broni Duszy nie modyfikują skilli/spelli.
            # Lifesteal/Mana/execute/boss bonus z Soul Weapon Traits działa wyłącznie
            # w realtime_player_action(), czyli na zwykłym ataku Broni Duszy.
            self._recap52_dealt=int(getattr(self,"_recap52_dealt",0))+max(0,int(damage))
            await self.send(
                f"Używasz {skill['name']} na {template['name']}. "
                f"Zadajesz {damage} obrażeń. Przeciwnik: {max(0, mob.hp)} z {template['max_hp']} HP."
                + machine_note
            )
            _party_skill = (
                f"{self.character.name}: {skill['name']}, {damage} obrażeń w {template['name']}"
            )
            if critical:
                _party_skill += ". Krytyk"
            if mob.hp <= 0:
                _party_skill += ". Pokonany"
            await self.server.party_combat_broadcast(self, _party_skill + ".")

            if kind == "drain":
                if template.get("machine"):
                    requested_heal = 0
                    await self.send("Machine nie posiada energii życiowej do wyssania.")
                else:
                    requested_heal = max(
                        1,
                        int(damage * skill.get("drain_pct", 0.4) * self.character.class_drain_healing_multiplier())
                    )
                # Drain nadal skaluje się z obrażeniami, ale pojedynczy cast nie
                # może przywrócić więcej niż 25% maksymalnego HP.
                drain_cap = max(1, int(round(self.max_hp() * 0.25)))
                heal = min(requested_heal, drain_cap)
                before = self.current_hp
                self.current_hp = min(self.max_hp(), self.current_hp + heal)
                actual = self.current_hp - before
                await self.send(
                    f"Wysysanie przywraca {actual} HP. Masz {self.current_hp} z {self.max_hp()} HP."
                )

            self_damage = skill.get("self_damage", 0)
            if skill.get("self_damage_pct"):
                self_damage += max(1, int(self.max_hp() * skill["self_damage_pct"]))
            if self_damage:
                self.current_hp -= self_damage
                if skill.get("mec_branch")=="feedback" and self.mec_skill_known_v0319("v0319_mec_self_repair"):
                    _sr_level=int(self.server.db.skill_progress(self.account_id,"v0319_mec_self_repair")["level"]); _sr_p=(max(1,min(SKILL_MAX_LEVEL,_sr_level))-1)/float(max(1, SKILL_MAX_LEVEL-1))
                    self.v0319_feedback_repair_pool=int(getattr(self,"v0319_feedback_repair_pool",0) or 0)+max(1,int(self_damage*(0.35+0.45*_sr_p)))
                    self.v0319_feedback_repair_at=time.time()+8.0
                await self.send(
                    f"Koszt umiejętności: tracisz {self_damage} HP. "
                    f"Masz {max(0, self.current_hp)} z {self.max_hp()} HP."
                )
                if self.current_hp <= 0:
                    await self.die("własna umiejętność")
                    return

            await self.grant_skill_use_xp(skill)

            if mana_cost:
                await self.send(f"Mana: {self.current_mana} z {self.max_mana()}.")

            if mob.hp <= 0:
                await self.mob_defeated(mob)
                return

            await self.ensure_realtime_combat()

    def player_damage(self):
            c = self.character

            if c.class_type == "physical":
                # Siła odpowiada za atak fizyczny.
                base_damage = c.soul_power() + self.physical_power() + random.randint(-3, 4)
                return max(
                    1,
                    int(
                        round(
                            base_damage
                            * c.class_physical_damage_multiplier()
                            * c.racial_physical_damage_multiplier()
                            * c.racial_all_damage_multiplier()
                            * self.total_set_damage_multiplier()
                            * self.equipment_damage_multiplier("physical")
                        )
                    )
                )

            # v0.30.17: magiczny autoatak Bronią Duszy skaluje się z Inteligencją,
            # nie z Siłą. Soul Power jest rdzeniem broni, spell_power wkładem INT.
            if self.current_mana >= 4:
                self.current_mana -= 4
                base_damage = (
                    c.soul_power()
                    + self.spell_power()
                    + random.randint(-3, 4)
                )
                return max(
                    1,
                    int(
                        round(
                            base_damage
                            * c.class_magic_damage_multiplier()
                            * c.racial_magic_damage_multiplier()
                            * c.racial_all_damage_multiplier()
                            * self.total_set_damage_multiplier()
                            * self.equipment_damage_multiplier("magic")
                        )
                    )
                )

            # Bez Many klasa magiczna nadal może uderzyć Bronią Duszy.
            # v0.8.65: taki słabszy atak uruchamia Skupienie Broni Duszy i
            # odzyskuje niewielką część Many. Zapobiega to wielominutowemu
            # utknięciu magicznych klas na słabym autoataku w długich walkach,
            # ale nie daje darmowej regeneracji dopóki Mana nie jest wyczerpana.
            base_damage = (
                c.soul_power()
                + self.spell_power() // 2
                + random.randint(-2, 2)
            )
            max_mana = self.max_mana()
            mana_focus = min(40, max(4, int(round(max_mana * 0.05))))
            self.current_mana = min(max_mana, self.current_mana + mana_focus)
            self._last_mana_focus_gain = mana_focus
            return max(
                    1,
                    int(
                        round(
                            base_damage
                            * c.class_magic_damage_multiplier()
                            * c.racial_magic_damage_multiplier()
                            * c.racial_all_damage_multiplier()
                            * self.total_set_damage_multiplier()
                        )
                    )
                )

    def consider_player_expected_hit(self):
            c = self.character

            if c.class_type == "physical":
                base_damage = (
                    c.soul_power()
                    + self.physical_power()
                    + 0.5
                )
                value = (
                    base_damage
                    * c.class_physical_damage_multiplier()
                    * c.racial_physical_damage_multiplier()
                    * c.racial_all_damage_multiplier()
                    * self.total_set_damage_multiplier()
                    * self.equipment_damage_multiplier("physical")
                )
            elif self.current_mana >= 4:
                base_damage = (
                    c.soul_power()
                    + self.spell_power()
                    + 0.5
                )
                value = (
                    base_damage
                    * c.class_magic_damage_multiplier()
                    * c.racial_magic_damage_multiplier()
                    * c.racial_all_damage_multiplier()
                    * self.total_set_damage_multiplier()
                    * self.equipment_damage_multiplier("magic")
                )
            else:
                base_damage = (
                    c.soul_power()
                    + self.spell_power() / 2.0
                )
                value = (
                    base_damage
                    * c.class_magic_damage_multiplier()
                    * c.racial_magic_damage_multiplier()
                    * c.racial_all_damage_multiplier()
                    * self.total_set_damage_multiplier()
                    * self.equipment_damage_multiplier("magic")
                )

            # Średnia wartość uwzględnia prawdopodobieństwo krytyka,
            # ale nie zużywa many i nie wykonuje żadnego rzutu RNG.
            crit_factor = (
                1.0
                + self.critical_chance()
                * (self.critical_multiplier() - 1.0)
            )
            return max(1.0, float(value) * crit_factor)

    def consider_enemy_expected_hit(self, template):
            damage_type = template.get("damage_type", "physical")
            raw = max(1.0, float(template.get("damage", 1)))

            if damage_type == "magic":
                reduction = float(self.magic_defense())
            else:
                reduction = float(self.defense())

            incoming = max(1.0, raw - reduction)

            if damage_type == "physical":
                physical_race_percent = (
                    self.character.racial_physical_damage_reduction_percent()
                )
                incoming *= max(
                    0.0,
                    1.0 - physical_race_percent / 100.0,
                )

            racial_percent = (
                self.character.racial_damage_reduction_percent()
            )
            incoming *= max(
                0.0,
                1.0 - racial_percent / 100.0,
            )

            class_percent = (
                self.character.class_damage_reduction_percent()
            )
            incoming *= max(
                0.0,
                1.0 - class_percent / 100.0,
            )

            # Unik obniża średnie obrażenia w dłuższej walce.
            incoming *= max(
                0.0,
                1.0 - self.dodge_chance(),
            )

            return max(1.0, incoming)

    def consider_rating(self, mob, template):
            player_hit = self.consider_player_expected_hit() / max(1.0,self.v0210_world_tier_multipliers()["effective_hp"])
            enemy_hit = self.consider_enemy_expected_hit(template) * self.v0210_enemy_damage_multiplier()

            mob_hp = max(1, int(mob.hp))
            player_hp = max(1, int(self.current_hp))

            turns_to_kill = mob_hp / player_hit
            turns_to_die = player_hp / enemy_hit
            ratio = turns_to_die / max(0.01, turns_to_kill)

            # Boss mechanics are deliberately treated as extra danger.
            if template.get("boss_mechanic"):
                ratio *= 0.82
            if (
                template.get("crypt_boss")
                or template.get("astral_boss")
                or template.get("mythic_crypt_boss")
                or template.get("mythic_astral_boss")
            ):
                ratio *= 0.90
            if template.get("world_boss"):
                ratio *= 0.90

            if ratio >= 3.0:
                label = "bardzo słaby"
                advice = "Powinien być dla ciebie łatwy."
            elif ratio >= 1.9:
                label = "słaby"
                advice = "Masz wyraźną przewagę."
            elif ratio >= 1.25:
                label = "korzystny"
                advice = "Masz przewagę, ale przeciwnik może zranić."
            elif ratio >= 0.80:
                label = "porównywalny"
                advice = "Walka może być wyrównana."
            elif ratio >= 0.50:
                label = "niebezpieczny"
                advice = "Przeciwnik ma przewagę. Przygotuj leczenie lub skille."
            elif ratio >= 0.28:
                label = "bardzo niebezpieczny"
                advice = "Ryzyko śmierci jest wysokie."
            else:
                label = "śmiertelnie groźny"
                advice = "Bez mocnego przygotowania lepiej go teraz nie atakować."

            return {
                "label": label,
                "advice": advice,
                "player_hit": max(1, int(round(player_hit))),
                "enemy_hit": max(1, int(round(enemy_hit))),
                "turns_to_kill": max(1, int(math.ceil(turns_to_kill))),
                "turns_to_die": max(1, int(math.ceil(turns_to_die))),
            }

    async def consider_mob(self, query):
            self.server.world.refresh()
            mobs = self.server.world.room_mobs(
                self.character.room_id
            )

            if not mobs:
                await self.send(
                    "Nie ma tutaj przeciwnika do oceny."
                )
                return

            raw = str(query or "").strip()
            if not raw:
                if len(mobs) == 1:
                    mob = mobs[0]
                else:
                    await self.send(
                        "Użycie: consider <mob>. "
                        "Przeciwnicy tutaj: "
                        + ", ".join(
                            MOB_TEMPLATES[m.template_id]["name"]
                            for m in mobs
                        )
                        + "."
                    )
                    return
            else:
                # v0.8.44: CON używa dokładnie tego samego uniwersalnego
                # resolvera żywych/zabijalnych mobów co k <mob>. Dzięki temu
                # działają fragmenty nazw, brak polskich znaków i numer wystąpienia.
                mob = self.server.world.find_mob(
                    self.character.room_id,
                    raw,
                )
                if not mob:
                    npc = self.protected_friendly_npc(raw)
                    if npc:
                        await self.send(
                            f"{npc['name']} jest pokojowym i chronionym NPC-em. "
                            "Komenda con działa tylko na przeciwników, których da się zabić."
                        )
                    else:
                        await self.send(
                            "Nie widzę tutaj takiego żywego przeciwnika do oceny. "
                            "Użyj con <mob>, np. con goblin albo con 2 goblin."
                        )
                    return

            template = MOB_TEMPLATES[mob.template_id]
            rating = self.consider_rating(mob, template)
            damage_type = (
                "magiczne"
                if template.get("damage_type") == "magic"
                else "fizyczne"
            )

            await self.send(
                f"CONSIDER: {template['name']}."
            )
            await self.send(
                f"Ocena zagrożenia: {rating['label']}."
            )
            await self.send(
                f"Przeciwnik ma {max(0, mob.hp)} z "
                f"{template['max_hp']} HP. "
                f"Bazowy atak: {template['damage']}. "
                f"Typ obrażeń: {damage_type}."
            )
            await self.send(
                f"Szacowany twój normalny cios: około "
                f"{rating['player_hit']}. "
                f"Szacowane otrzymane obrażenia na odpowiedź: około "
                f"{rating['enemy_hit']}."
            )
            await self.send(
                f"Orientacyjnie: około {rating['turns_to_kill']} twoich "
                f"normalnych trafień do pokonania przeciwnika i około "
                f"{rating['turns_to_die']} jego skutecznych odpowiedzi "
                f"do pokonania ciebie przy obecnym HP."
            )

            elite_text = template.get(
                "elite_affix_text"
            )
            if elite_text:
                await self.send(
                    f"Elitarny affix: {elite_text}"
                )

            if template.get("rare_troll"):
                await self.send(
                    "Rzadki wariant trolla."
                )

            mechanic = template.get("boss_mechanic_text")
            if mechanic:
                await self.send(
                    f"Mechanika bossa: {mechanic}"
                )
            elif template.get("boss_mechanic"):
                await self.send(
                    "To boss ze specjalną mechaniką. "
                    "Ocena consider jest orientacyjna."
                )

            xp_profile = self.dynamic_kill_xp_profile(template, room_id=self.character.room_id)
            await self.send(
                f"EXP przy obecnej sile postaci: {xp_profile['label']}, "
                f"mnożnik x{xp_profile['multiplier']:.2f} dla EXP statów, Soul XP i Class XP. "
                f"Siła postaci {xp_profile['power']}/{CHARACTER_MAX_LEVEL}, siła przeciwnika około {xp_profile['target']}/{CHARACTER_MAX_LEVEL}."
            )
            await self.send(rating["advice"])
            await self.send(
                "Consider jest tylko oceną: nie rozpoczyna walki "
                "i nie uruchamia automatycznej pętli walki."
            )

    async def stop_realtime_combat(self):
            """Zatrzymaj pętlę walki bez pozostawiania zadania w tle."""
            task = self.combat_task
            self.combat_task = None
            if task and task is not asyncio.current_task() and not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass

    async def ensure_realtime_combat(self):
            if not hasattr(self, "_recap52_start") or not getattr(self, "_recap52_start", 0):
                self._recap52_start=__import__("time").time(); self._recap52_dealt=0; self._recap52_taken=0; self._recap52_heal=0; self._recap52_crits=0; self._recap52_skills=0; self._recap32_guard_saved=0
            if self.closed or not self.combat_mob_key:
                return
            mob = self.server.world.mobs.get(self.combat_mob_key)
            if (
                not mob
                or not mob.alive
                or mob.room_id != self.character.room_id
            ):
                self.combat_mob_key = None
                return
            if self.combat_task and not self.combat_task.done():
                return
            self.combat_task = asyncio.create_task(self.realtime_combat_loop())

    async def grant_soul_weapon_mastery_hit_xp(self):
            if not self.character or self.character.soul_weapon_mastery_level >= SOUL_WEAPON_MASTERY_MAX_LEVEL:
                return
            level = max(1, int(self.character.soul_weapon_mastery_level))
            gain = v0190_scaled_gain(30, level, "skill", 30)
            gain = self.apply_double_xp(gain)
            result = self.character.add_soul_weapon_mastery_xp(gain)
            self.session_summary_add("soul_weapon_mastery_xp", gain)
            if result["level_ups"]:
                await self.send(
                    f"Soul Weapon Mastery wzrasta do {result['level']}/{SOUL_WEAPON_MASTERY_MAX_LEVEL}.",
                    combat_detail="essential",
                )

    async def realtime_player_action(self, mob):
            if not mob or not mob.alive:
                return
            # Kolejka ma pierwszeństwo. Jeśli żaden zapisany skill/spell nie jest
            # obecnie gotowy, wykonujemy zwykły automatyczny atak Bronią Duszy.
            if await self.try_auto_skill_queue(mob):
                return

            template = MOB_TEMPLATES[mob.template_id]
            self._last_mana_focus_gain = 0
            damage = self.player_damage()
            # v0.35.1: Soul Weapon Mastery wzmacnia wyłącznie zwykły atak broni.
            mastery = soul_weapon_mastery_bonuses(self.character.soul_weapon_mastery_level)
            damage = max(1, int(round(damage * (1.0 + mastery["damage_percent"] / 100.0))))
            # v0.33.16: właściwości Soul Tier działają tylko na zwykły atak
            # Broni Duszy. Nie modyfikują skilli ani spelli.
            trait_totals = soul_weapon_trait_totals(self.character.soul_tier, self.character.class_name)
            damage = max(1, int(round(damage * (1.0 + trait_totals["damage_percent"] / 100.0))))
            if mob.hp <= max(1, int(round(template["max_hp"] * 0.35))):
                damage = max(1, int(round(damage * (1.0 + trait_totals["execute_damage_percent"] / 100.0))))
            _is_boss_target = any(template.get(flag) for flag in (
                "world_boss", "mini_boss", "crypt_boss", "astral_boss",
                "mythic_crypt_boss", "mythic_astral_boss", "giant_fortress_boss",
            ))
            if _is_boss_target:
                _boss_bonus = float(trait_totals["boss_damage_percent"]) + float(mastery["boss_damage_percent"])
                if _boss_bonus > 0:
                    damage = max(1, int(round(damage * (1.0 + _boss_bonus / 100.0))))
            mana_focus_gain = int(getattr(self, "_last_mana_focus_gain", 0) or 0)
            if mana_focus_gain > 0:
                await self.send_combat(
                    f"Skupienie Broni Duszy: odzyskujesz {mana_focus_gain} Many. "
                    f"Mana {self.current_mana} z {self.max_mana()}.",
                    "normal",
                )
            weapon_crit_chance = min(0.60, self.critical_chance() + trait_totals["crit_chance"] + mastery["crit_chance"])
            critical = random.random() < weapon_crit_chance
            if critical:
                weapon_crit_multiplier = self.critical_multiplier() * (1.0 + (trait_totals["crit_damage_percent"] + mastery["crit_damage_percent"]) / 100.0)
                damage = max(1, int(round(damage * weapon_crit_multiplier)))
                await self.send_combat(
                    f"TRAFIENIE KRYTYCZNE BRONI DUSZY! Zręczność {self.effective_dexterity()}. "
                    f"Szansa tego ataku: {round(weapon_crit_chance * 100, 1)} procent.",
                    "normal",
                )
            damage = await self.apply_boss_defense(mob, damage)
            damage = self.v0210_adjust_player_damage(damage)
            _basic_kind = "physical" if self.character.class_type == "physical" else "magic"
            damage, machine_note = v0314_adjust_damage_vs_template(template, damage, _basic_kind, "")
            mob.hp -= damage
            self._recap52_dealt=int(getattr(self,"_recap52_dealt",0))+max(0,int(damage))
            await self.grant_soul_weapon_mastery_hit_xp()
            echo_damage = 0
            if mob.hp > 0 and mastery["echo_chance"] > 0 and random.random() < mastery["echo_chance"]:
                echo_damage = max(1, int(round(damage * mastery["echo_damage_percent"] / 100.0)))
                mob.hp -= echo_damage
                self._recap52_dealt = int(getattr(self, "_recap52_dealt", 0)) + echo_damage
            soul_heal = 0
            _lifesteal = float(trait_totals.get("lifesteal_percent", 0.0) or 0.0)
            if _lifesteal > 0 and self.current_hp < self.max_hp():
                soul_heal = min(self.max_hp() - self.current_hp, max(1, int(round(damage * _lifesteal / 100.0))))
                if soul_heal > 0:
                    self.current_hp += soul_heal
                    self._recap52_heal = int(getattr(self, "_recap52_heal", 0)) + soul_heal
            _mana_restore = 0
            _mana_pct = float(trait_totals.get("mana_restore_percent", 0.0) or 0.0)
            if _mana_pct > 0 and self.current_mana < self.max_mana():
                _mana_restore = min(self.max_mana() - self.current_mana, max(1, int(round(damage * _mana_pct / 100.0))))
                if _mana_restore > 0:
                    self.current_mana += _mana_restore
            technique = SOUL_WEAPON_ATTACK_TECHNIQUES.get(
                self.character.class_name, "Atak Broni Duszy"
            )
            await self.send_combat(
                f"Broń Duszy {self.character.soul_weapon}: {technique}. "
                f"Cel {template['name']}. Zadajesz {damage} obrażeń. "
                f"Przeciwnik: {max(0, mob.hp)} z {template['max_hp']} życia."
                + (f" Właściwość Broni Duszy leczy {soul_heal}." if soul_heal > 0 else "")
                + (f" Odzyskujesz {_mana_restore} Many." if _mana_restore > 0 else "")
                + (f" Echo Broni Duszy zadaje dodatkowo {echo_damage} obrażeń." if echo_damage > 0 else "")
                + machine_note,
                "normal",
            )
            _party_attack = (
                f"{self.character.name}: {technique}, {damage + echo_damage} obrażeń w {template['name']}"
            )
            if critical:
                _party_attack += ". Krytyk"
            if mob.hp <= 0:
                _party_attack += ". Pokonany"
            await self.server.party_combat_broadcast(self, _party_attack + ".")
            if mob.hp <= 0:
                await self.mob_defeated(mob)

    async def realtime_combat_loop(self):
            """Niezależne timery gracza i moba; brak tur i ręcznego klikania rund."""
            this_task = asyncio.current_task()
            next_player = time.monotonic()
            # Krótki margines na pierwszą akcję gracza, aby rozpoczęcie walki było
            # czytelne dla NVDA i nie powodowało natychmiastowego ciosu w tej samej ms.
            next_enemy = time.monotonic() + 0.75
            try:
                while not self.closed and self.combat_mob_key:
                    mob = self.server.world.mobs.get(self.combat_mob_key)
                    if (
                        not mob
                        or not mob.alive
                        or mob.room_id != self.character.room_id
                    ):
                        self.combat_mob_key = None
                        break

                    now = time.monotonic()
                    if now >= next_player:
                        await self.realtime_player_action(mob)
                        next_player = time.monotonic() + self.combat_player_interval
                        if not self.combat_mob_key or self.current_hp <= 0:
                            break
                        mob = self.server.world.mobs.get(self.combat_mob_key)
                        if not mob or not mob.alive:
                            break

                    now = time.monotonic()
                    if now >= next_enemy:
                        # v0.8.65: jeden mob ma jeden aktywny cel aggro. Członkowie
                        # drużyny mogą zadawać obrażenia temu samemu przeciwnikowi,
                        # ale nie tworzą własnych pełnych timerów kontrataku bossa.
                        if not mob.engaged_by:
                            if mob.engaged_at <= 0:
                                mob.engaged_at = time.monotonic()
                            mob.engaged_by = self.character.name
                        if mob.engaged_by == self.character.name:
                            target_session = self.server.party_combat_target(self, mob)
                            if target_session and not target_session.closed and target_session.current_hp > 0:
                                # v0.31.16: party target feed. The victim receives the native
                                # detailed damage line from enemy_counterattack; everyone else
                                # in the same party/room gets a short NVDA-friendly target line.
                                await self.server.party_combat_broadcast(
                                    target_session,
                                    f"{MOB_TEMPLATES[mob.template_id]['name']} atakuje {target_session.character.name}.",
                                    detail="normal",
                                )
                                await target_session.enemy_counterattack(mob)
                        next_enemy = time.monotonic() + self.combat_enemy_interval
                        if not self.combat_mob_key or self.current_hp <= 0:
                            break

                    wait_for = min(next_player, next_enemy) - time.monotonic()
                    await asyncio.sleep(max(0.05, min(0.20, wait_for)))
            except asyncio.CancelledError:
                pass
            except Exception as exc:
                # Nie zabijaj sesji przez błąd zadania w tle; gracz może ponownie
                # rozpocząć walkę komendą atakuj/k.
                try:
                    await self.send(f"Pętla walki została zatrzymana: {exc}")
                except Exception:
                    pass
            finally:
                if self.combat_task is this_task:
                    self.combat_task = None

    async def attack(self, query):
            wanted = (query or "").strip()
            if wanted and await self.reject_player_attack(wanted):
                return
            if self.auto_fishing or self.auto_fishing_task:
                await self.stop_auto_fishing(announce=False)
                await self.send("Auto-łowienie wyłączone z powodu walki.")
            if self.auto_mining or self.auto_mining_task:
                await self.stop_auto_mining(announce=False)
                await self.send("Auto-kopanie wyłączone z powodu walki.")
            if self.auto_woodcutting or self.auto_woodcutting_task:
                await self.stop_auto_woodcutting(announce=False)
                await self.send("Auto-Drwalstwo wyłączone z powodu walki.")
            if self.auto_herbalism or self.auto_herbalism_task:
                await self.stop_auto_herbalism(announce=False)
                await self.send("Auto-Zielarstwo wyłączone z powodu walki.")

            self.server.world.refresh()
            mob = None
            current = None
            if self.combat_mob_key:
                current = self.server.world.mobs.get(self.combat_mob_key)
                if (
                    not current
                    or not current.alive
                    or current.room_id != self.character.room_id
                ):
                    self.combat_mob_key = None
                    current = None

            if current and wanted:
                requested = self.server.world.find_mob(self.character.room_id, wanted)
                if not requested:
                    if await self.reject_player_attack(wanted):
                        return
                    if await self.reject_friendly_npc_attack(wanted):
                        return
                    await self.send("Nie widzę tutaj takiego przeciwnika do zabicia.")
                    return
                if requested.key != current.key:
                    if not self.server.engagement_allowed(self, requested):
                        await self.send(self.engagement_block_message(requested))
                        return
                    self.server.reassign_mob_engagement(current, self)
                    mob = requested
                    await self.send(
                        f"Zmieniasz cel na {MOB_TEMPLATES[mob.template_id]['name']}."
                    )
                else:
                    mob = current
            elif current:
                mob = current
            else:
                # v0.8.35: najpierw próbujemy znaleźć prawdziwego, żywego moba.
                # Dzięki temu pokojowy NPC o podobnej nazwie nie blokuje komendy
                # k <mob>, jeżeli w tym samym pokoju istnieje zabijalny przeciwnik.
                mob = self.server.world.find_mob(self.character.room_id, wanted)
                if not mob:
                    if await self.reject_player_attack(wanted):
                        return
                    if await self.reject_friendly_npc_attack(wanted):
                        return
                    await self.send("Nie widzę tutaj takiego przeciwnika do zabicia.")
                    return
                if not self.server.engagement_allowed(self, mob):
                    await self.send(self.engagement_block_message(mob))
                    return

            new_fight = self.combat_mob_key != mob.key
            was_unengaged = not mob.engaged_by
            protector = await self.server.apply_party_protection(self, mob)
            if was_unengaged:
                if mob.engaged_at <= 0:
                    mob.engaged_at = time.monotonic()
                if not mob.engaged_by:
                    mob.engaged_by = self.character.name
                mob.combat_turn = 0
                mob.player_hits = 0
            self.combat_mob_key = mob.key

            if new_fight:
                self.combat_hp_warn_level = 0
                await self.server.auto_assist_party_combat(self, mob)
                await self.server.broadcast_room(
                    self.character.room_id,
                    f"{self.character.name} atakuje {MOB_TEMPLATES[mob.template_id]['name']}.",
                    exclude=self,
                )
                await self.send(
                    "Walka w czasie rzeczywistym rozpoczęta. "
                    "Auto kolejka i zwykłe ataki działają automatycznie; użyj flee, aby się wycofać."
                )
            else:
                await self.send(
                    f"Walka trwa. Cel: {MOB_TEMPLATES[mob.template_id]['name']}."
                )
            await self.ensure_realtime_combat()

    def class_for_milestone_loot(self):
            active = self.active_class_names()
            if active:
                return active[0]
            return self.character.class_name

    async def grant_milestone_boss_loot(self, template, floor):
            marker = milestone_boss_tier(floor)
            if not marker:
                return
            class_name = self.class_for_milestone_loot()
            if class_name not in LEGENDARY_CLASS_SET_ITEMS_BY_CLASS_TIER:
                return
            mastery = legendary_loot_mastery_for_floor(floor)
            set_pool = list(LEGENDARY_CLASS_SET_ITEMS_BY_CLASS_TIER[class_name][mastery])
            discovered_eq = self.server.db.collection_entry_ids(self.account_id, "equipment")
            missing = [item_id for item_id in set_pool if item_id not in discovered_eq]
            set_item = random.choice(missing or set_pool)
            self.server.db.add_item(self.account_id, set_item, 1)
            await self.record_item_collection(
                set_item, source=template.get("name", "Boss kamienia milowego"), announce=True
            )
            boss_id = str(template.get("template_id") or "")
            if boss_id:
                self.server.db.add_boss_codex_drop(self.account_id, boss_id, set_item)
            await self.send(
                f"Loot setowy klasy {class_name}: {ITEMS[set_item]['name']}. "
                f"Wymaga Biegłości {mastery}."
            )
            if marker == 100:
                relic_id = LEGENDARY_CLASS_RELIC_BY_CLASS_TIER[class_name][mastery]
                self.server.db.add_item(self.account_id, relic_id, 1)
                await self.record_item_collection(
                    relic_id, source=template.get("name", "Boss setnego piętra"), announce=True
                )
                if boss_id:
                    self.server.db.add_boss_codex_drop(self.account_id, boss_id, relic_id)
                await self.send(
                    f"Legendarny loot klasy {class_name}: {ITEMS[relic_id]['name']}. "
                    f"Wymaga Biegłości {mastery}."
                )

    async def mob_defeated(self, mob):
            # Zwycięstwo, loot, questy i nagrody są zawsze ważne nawet w trybie
            # combat concise. Nie dziedziczą wyciszenia rutynowej auto kolejki.
            self.auto_queue_casting = False
            template = MOB_TEMPLATES[mob.template_id]
            _nemesis_owner = int(template.get("v029_nemesis_owner_account_id", 0) or 0)
            if _nemesis_owner:
                _resolved = self.server.db.defeat_nemesis_v029(_nemesis_owner)
                self.server.db.add_collection_entry(_nemesis_owner, "nemesis_defeated_v029", str(template.get("name", mob.template_id)))
                for _s in list(self.server.sessions):
                    if _s.account_id == _nemesis_owner:
                        await _s.send(
                            f"NEMESIS POKONANY: {template['name']}. Łącznie pokonane Nemesis: {int(_resolved['defeats'] or 0) if _resolved else 1}."
                        )
                        break
            fight_duration_ms = None
            if mob.engaged_at > 0:
                fight_duration_ms = max(1, int(round((time.monotonic() - mob.engaged_at) * 1000)))
            mob.alive = False
            respawn_seconds = mob_respawn_seconds(template)
            mob.respawn_at = time.time() + respawn_seconds
            mob.engaged_by = None
            corpse=self.server.world.create_corpse(mob)
            if corpse:
                if corpse.items:
                    await self.send(f"Pozostaje ciało: {corpse.mob_name}. Ma na sobie {len(corpse.items)} elementów ekwipunku. Wpisz ciało albo przeszukaj ciało.")
                else:
                    await self.send(f"Pozostaje ciało: {corpse.mob_name}. Nie widać na nim ekwipunku.")

            for session in list(self.server.sessions):
                if session.combat_mob_key == mob.key:
                    session.combat_mob_key = None

            recipients = self.server.party_sessions(
                self.account_id, same_room=self.character.room_id
            )
            if not recipients:
                recipients = [self]
            recipients = sorted(
                recipients, key=lambda s: s.character.name.lower()
            )
            count = len(recipients)

            if template.get("v020_megadungeon_boss"):
                _mk=str(template.get("v020_mega_key")); _mi=int(template.get("v020_mega_index",0) or 0)
                for session in recipients:
                    first=session.server.db.mark_boss_floor_cleared(session.account_id,f"v020_mega_{_mk}",_mi)
                    session.server.db.add_collection_entry(session.account_id,"mega_boss_kills_v020",f"{_mk}:{_mi}")
                    if first:
                        await session.send(f"Megaloch: próg {_mi} zaliczony na stałe. Przejście do następnej sekcji pozostanie otwarte po respawnie bossa.")
            if template.get("v020_gauntlet") and int(template.get("v020_gauntlet_round",0) or 0)==5:
                _gk=str(template.get("v020_gauntlet"))
                for session in recipients:
                    first=session.server.db.add_collection_entry(session.account_id,"gauntlet_clears_v020",_gk)
                    session.server.db.add_collection_entry(session.account_id,"gauntlet_final_kills_v020",f"{_gk}:{int(time.time()//3600)}")
                    if first: await session.unlock_title(f"v020:gauntlet:{_gk}",f"Pogromca Próby: {V020_GAUNTLETS[_gk]['name']}")
            if template.get("v020_mythic_world_boss"):
                _bid=canonical_bestiary_template_id(mob.template_id)
                for session in recipients:
                    session.server.db.add_collection_entry(session.account_id,"mythic_world_kills_v020",f"{_bid}:{int(time.time()//V020_MYTHIC_WORLD_BOSS_SECONDS)}")
                    await session.add_faction_reputation_v016("frontier_watch",75,reason="mythic_world_boss")
            if template.get("v021_endless_gauntlet"):
                _round=v0210_endless_gauntlet_identity(mob.room_id) or 0
                for session in recipients:
                    best=session.server.db.mark_endless_gauntlet_round_v021(session.account_id,_round)
                    session.server.db.add_collection_entry(session.account_id,"endless_gauntlet_v021",str(_round))
                    if _round and _round%25==0:
                        await session.unlock_title(f"v021:endless:{_round}",f"Wieczny Pretendent — runda {_round}")
                    await session.send(f"Endless Gauntlet: ukończona runda {_round}. Najlepsza runda {best}.")

            boss_kind, cleared_floor = boss_floor_identity(template)
            if boss_kind and cleared_floor:
                for session in recipients:
                    first_clear = self.server.db.mark_boss_floor_cleared(
                        session.account_id, boss_kind, cleared_floor
                    )
                    if first_clear:
                        self.server.db.mark_instance_checkpoint(
                            session.account_id, boss_kind, cleared_floor
                        )
                        await session.send(
                            f"Próg bossa {cleared_floor} został zaliczony na stałe. "
                            "Po respawnie boss pozostaje opcjonalny i nie blokuje już dalszej drogi."
                        )
                    if milestone_boss_tier(cleared_floor):
                        await session.grant_milestone_boss_loot(template, cleared_floor)

            boss_floor = (
                int(template.get("crypt_floor", 0))
                if template.get("crypt_boss")
                else 0
            )
            if is_crypt_boss_floor(boss_floor):
                for session in recipients:
                    before_checkpoint = (
                        self.server.db.crypt_portal(session.account_id)
                    )
                    after_checkpoint = (
                        self.server.db.unlock_crypt_portal(
                            session.account_id, boss_floor
                        )
                    )
                    if after_checkpoint > before_checkpoint:
                        await session.send(
                            f"Odblokowano Portal Krypty do piętra "
                            f"{boss_floor}."
                        )
                        await session.send(
                            "Portal odblokowany. Ten boss został zaliczony; po respawnie jest opcjonalny "
                            "i nie blokuje już zejścia dla tej postaci."
                        )

            astral_boss_floor = (
                int(template.get("astral_floor", 0))
                if template.get("astral_boss")
                else 0
            )
            if is_astral_boss_floor(astral_boss_floor):
                for session in recipients:
                    before_checkpoint = (
                        self.server.db.astral_portal(
                            session.account_id
                        )
                    )
                    after_checkpoint = (
                        self.server.db.unlock_astral_portal(
                            session.account_id,
                            astral_boss_floor,
                        )
                    )
                    if after_checkpoint > before_checkpoint:
                        await session.send(
                            f"Odblokowano Astralny Portal do poziomu "
                            f"{astral_boss_floor}."
                        )
                        await session.send(
                            "Checkpoint Wieży zapisany. Ten boss został zaliczony; po respawnie jest opcjonalny "
                            "i nie blokuje już drogi w górę dla tej postaci."
                        )

            for session in recipients:
                if count > 1:
                    await session.send(
                        f"Drużyna pokonuje: {template['name']}. "
                        f"Nagrody obejmują {count} obecnych członków."
                    )
                else:
                    await session.send(f"Pokonujesz: {template['name']}.")

            # v0.19: jedna wspólna pula monet z generatora całej gry.
            generated_coins=v0190_combat_reward(template,"coins")
            currency_rewards={currency:{s.account_id:0 for s in recipients} for currency in ("silver","gold","mithril")}
            if generated_coins>0:
                base_share,remainder=divmod(generated_coins,count)
                for session in recipients:
                    currency_rewards["silver"][session.account_id]=base_share
                currency_rewards["silver"][self.account_id]+=remainder

            _v0927_guild_progressed = set()
            for session in recipients:
                silver = min(V019_SAFE_INT, int(round(currency_rewards["silver"][session.account_id] * session.v0210_reward_multiplier())))
                gold = currency_rewards["gold"][session.account_id]
                mithril = currency_rewards["mithril"][session.account_id]
                session.character.silver += silver
                session.character.gold += gold
                session.character.mithril += mithril

                if silver or gold or mithril:
                    await session.send(
                        "Twój udział waluty: "
                        + currency_reading_text(silver, gold, mithril) + "."
                    )

                # v0.19: Global Progression & Reward Generator.
                # Duże nagrody nie są przycinane procentowym capem. Długość gry
                # kontrolują rosnące wymagania EXP oraz kosztów.
                xp_profile=session.dynamic_kill_xp_profile(template,room_id=session.character.room_id)
                # v0.23.0: NIE podbijamy mnożnika do minimum 1.0. To był błąd,
                # przez który słabsze moby nigdy nie traciły EXP podczas farmy.
                xp_mult=float(xp_profile["multiplier"]) * session.v0210_reward_multiplier()
                _party_bonus=dungeon_party_bonus_v0320(session)
                xp_mult*=float(_party_bonus.get("multiplier",1.0))
                if int(_party_bonus.get("bonus_pct",0))>0:
                    await session.send_combat(f"Dungeon Party Bonus: +{int(_party_bonus['bonus_pct'])}% EXP; członków obok {_party_bonus['members']}; różne klasy {_party_bonus['diverse']}.",detail="full")
                raw_stat_reward=min(V019_SAFE_INT,max(0,int(round(v0190_combat_reward(template,"stat")*xp_mult))))
                raw_stat_reward=session.apply_double_xp(raw_stat_reward)
                stat_rewards=[]
                for stat_name in session.character.STAT_PROGRESS_FIELDS:
                    stat_rewards.append(raw_stat_reward)
                    for msg in session.character.add_stat_progress(raw_stat_reward,targets=(stat_name,)):
                        await session.send(msg)
                stat_reward_text=str(raw_stat_reward)

                soul_xp_reward=min(V019_SAFE_INT,max(0,int(round(v0190_combat_reward(template,"soul")*xp_mult))))
                await session.grant_soul_xp(soul_xp_reward)

                class_xp_reward=min(V019_SAFE_INT,max(0,int(round(v0190_combat_reward(template,"class")*xp_mult))))
                await session.send_combat(
                    f"Generator v0.19 + dynamiczny EXP v0.23: etap {v0190_mob_stage(template)}, "
                    f"ranga {v0190_mob_rank(template)}, siła postaci {xp_profile['power']}/{CHARACTER_MAX_LEVEL}, "
                    f"siła moba {xp_profile['target']}/{CHARACTER_MAX_LEVEL}, mnożnik x{xp_profile['multiplier']:.2f}; "
                    f"bazowy EXP statów {stat_reward_text}; Soul XP {soul_xp_reward}; Class XP {class_xp_reward}; "
                    f"EXP postaci {character_xp_reward if 'character_xp_reward' in locals() else v0190_combat_reward(template,'character')}.",
                    detail="full",
                )
                await session.grant_class_xp(class_xp_reward)
                character_xp_reward=min(V019_SAFE_INT,max(0,int(round(v0190_combat_reward(template,"character")*xp_mult))))
                for _msg in session.add_character_xp_with_event(character_xp_reward):
                    await session.send(_msg)
                await session.record_mob_progress(mob)

                bestiary_row, bestiary_new, bestiary_record = self.server.db.record_bestiary_kill(
                    session.account_id, mob.template_id, fight_duration_ms
                )
                bestiary_id = canonical_bestiary_template_id(mob.template_id)
                if bestiary_id in BOSS_COLLECTION_CATALOG:
                    self.server.db.record_boss_codex_kill(
                        session.account_id, bestiary_id, grouped=(count > 1)
                    )
                # v0.9.27: wspólne kontrakty i osiągnięcia Gildii.
                _guild=session.guild_row_v0926()
                if _guild:
                    _gid=int(_guild["clan_id"])
                    if _gid not in _v0927_guild_progressed:
                        _v0927_guild_progressed.add(_gid)
                        _is_boss=v0866_is_boss_template(template)
                        self.server.db.clan_metric_add(_gid,"boss_kills" if _is_boss else "mob_kills",1)
                        _changed=self.server.db.guild_contract_add_v0927(_gid,"bosses" if _is_boss else "kills",1)
                        await session.finish_ready_guild_contracts_v0927(_gid,_changed)
                        if template.get("guild_boss") and int(template.get("guild_id",0))==_gid:
                            _rec=self.server.db.conn.execute("SELECT fastest_kill_ms FROM player_guild_boss_records_v0927 WHERE clan_id=?",(_gid,)).fetchone()
                            _old=int(_rec["fastest_kill_ms"]) if _rec and _rec["fastest_kill_ms"] is not None else None
                            _best=fight_duration_ms if _old is None else min(_old,fight_duration_ms)
                            _name=str(template.get("name","Boss Gildii")); _tid=f"hall_{int(template.get('guild_hall_level',1))}"
                            self.server.db.conn.execute("INSERT INTO player_guild_boss_records_v0927(clan_id,kills,fastest_kill_ms,last_boss_name,last_killed_at) VALUES(?,1,?,?,CURRENT_TIMESTAMP) ON CONFLICT(clan_id) DO UPDATE SET kills=kills+1,fastest_kill_ms=?,last_boss_name=?,last_killed_at=CURRENT_TIMESTAMP",(_gid,_best,_name,_best,_name))
                            self.server.db.conn.execute("INSERT INTO player_guild_trophies_v0927(clan_id,trophy_id,name,count) VALUES(?,?,?,1) ON CONFLICT(clan_id,trophy_id) DO UPDATE SET count=count+1",(_gid,_tid,f"Trofeum: {_name}"))
                            _reward=(2_000+int(template.get('guild_hall_level',1))*1_000)*SILVER_PER_GOLD
                            self.server.db.conn.execute("UPDATE player_clans SET treasury=treasury+? WHERE id=?",(_reward,_gid)); self.server.db.conn.commit(); self.server.db.clan_metric_add(_gid,"guild_boss_kills",1); self.server.db.clan_log(_gid,session.account_id,f"Gildia pokonuje {_name}. Trofeum zapisane; do skarbca trafia {currency_reading_text(_reward,0,0)}.")
                            await session.send(f"Boss Gildii pokonany. Trofeum zapisane, a skarbiec otrzymuje {currency_reading_text(_reward,0,0)}.")
                await session.advance_bounty("kill", bestiary_id, 1)
                await session.advance_legendary_contract_v022("kill", 1)
                if v0866_is_boss_template(template):
                    await session.advance_legendary_contract_v022("boss", 1)
                if template.get("world_boss") or template.get("v016_world_boss") or template.get("v020_mythic_world_boss"):
                    await session.advance_legendary_contract_v022("worldboss", 1)
                await session.advance_dynamic_world_quest_v015("kill", bestiary_id, 1)
                if template.get("v016_legendary_rare"):
                    await session.advance_v0140_quest_progress("legendary_rare", template.get("v016_biome", "any"), 1)
                    await session.add_faction_reputation_v016("frontier_watch", 15, reason="legendary_rare")
                    session.server.db.add_collection_entry(session.account_id, "legendary_rares_v016", bestiary_id)
                if template.get("v016_world_boss"):
                    await session.advance_v0140_quest_progress("world_boss", template.get("v016_biome", "any"), 1)
                    await session.add_faction_reputation_v016("frontier_watch", 40, reason="world_boss")
                    session.server.db.add_collection_entry(session.account_id, "world_bosses_v016", bestiary_id)
                if template.get("v018_great_ruin_guardian"):
                    session.server.db.add_collection_entry(session.account_id, "great_ruin_guardians_v018", bestiary_id)
                    await session.add_faction_reputation_v016("cartographers", 20, reason="great_ruin")
                if template.get("v018_legendary_event_boss"):
                    session.server.db.add_collection_entry(session.account_id, "legendary_event_bosses_v018", bestiary_id)
                    await session.add_faction_reputation_v016("frontier_watch", 50, reason="legendary_event")
                bestiary_ids_now = {
                    str(row["mob_template_id"])
                    for row in self.server.db.bestiary_rows(session.account_id)
                }
                await session.set_achievement_progress(
                    "bestiary_unique", len(bestiary_ids_now.intersection(BESTIARY_CATALOG))
                )
                bestiary_name = MOB_TEMPLATES.get(bestiary_id, template).get("name", template["name"])
                if bestiary_new:
                    await session.send(
                        f"Bestiariusz: nowy wpis — {bestiary_name}. "
                        "Wpisz bestiariusz " + bestiary_name + "."
                    )
                elif bestiary_record and bestiary_row and bestiary_row["fastest_kill_ms"] is not None:
                    await session.send(
                        f"Bestiariusz: nowy rekord {bestiary_name}: "
                        f"{int(bestiary_row['fastest_kill_ms']) / 1000.0:.2f} s."
                    )

                # v0.8.10: postęp zadania klasowego Gildii.
                try:
                    active_classes = session.active_class_names()
                    guild_class = active_classes[0] if active_classes else session.character.class_name
                    quest_data = GUILD_CLASS_QUESTS.get(guild_class)
                    states = session.character._guild_json("guild_class_quests_json")
                    state = states.get(guild_class, {})
                    if quest_data and isinstance(state, dict) and state.get("accepted") and not state.get("completed"):
                        needed = int(quest_data[4])
                        old_progress = int(state.get("progress", 0))
                        new_progress = min(needed, old_progress + 1)
                        state["progress"] = new_progress
                        states[guild_class] = state
                        session.character._set_guild_json("guild_class_quests_json", states)
                        if new_progress >= needed:
                            await session.send(
                                f"Zadanie Gildii {quest_data[0]}: {new_progress} z {needed}. "
                                "Cel wykonany. Użyj zadanieklasowe, aby odebrać nagrodę."
                            )
                        else:
                            await session.send(f"Zadanie Gildii {quest_data[0]}: {new_progress} z {needed}.")
                except Exception:
                    pass

                # v0.8.10: bounty zalicza się każdemu uprawnionemu członkowi drużyny.
                try:
                    bounty_state = session.character.guild_bounty_state()
                    if bounty_state.get("target") == mob.template_id and not bounty_state.get("completed"):
                        bounty_state["completed"] = True
                        session.character.set_guild_bounty_state(bounty_state)
                        await session.send("Cel zlecenia Gildii pokonany. Użyj: guildbounty odbierz.")
                except Exception:
                    pass

                # v0.8.53: każdy zabijalny mob może być bezpośrednim celem questa
                # przez własny template_id. Zachowujemy również historyczne aliasy
                # quest_target/quest_targets, więc stare questy nadal zaliczają całe
                # rodziny mobów (np. wszystkie odmiany goblinów).
                quest_targets = [mob.template_id]
                primary_target = template.get("quest_target")
                if primary_target:
                    quest_targets.append(primary_target)
                quest_targets.extend(
                    template.get("quest_targets") or ()
                )

                for target in dict.fromkeys(quest_targets):
                    changed = self.server.db.increment_quest(
                        session.account_id, target
                    )
                    for quest_id, _progress in changed:
                        await session.announce_active_quest_progress(quest_id)

                await session.grant_hourly_quest_kill_drop_v0929(
                    mob.template_id, template
                )
                try:
                    _dur=int(fight_duration_ms or 0)
                    session.server.db.conn.execute("INSERT INTO combat_recaps_v03052(account_id,opponent,duration_ms,damage_dealt,damage_taken,healing,crits,skills_used,result) VALUES(?,?,?,?,?,?,?,?,?)",(session.account_id,str(template.get("name",mob.template_id)),_dur,int(getattr(session,"_recap52_dealt",0)),int(getattr(session,"_recap52_taken",0)),int(getattr(session,"_recap52_heal",0)),int(getattr(session,"_recap52_crits",0)),int(getattr(session,"_recap52_skills",0)),"victory"))
                    session.server.db.set_recap_summary_v0320(session.account_id, self.character.name, f"Pokonano {template.get('name',mob.template_id)}", int(getattr(session,"_recap32_guard_saved",0)), int(getattr(session,"_recap52_heal",0)), "victory")
                    session.server.db.add_combat_event_v0320(session.account_id,f"Finalny cios zadaje {self.character.name}. {template.get('name',mob.template_id)} zostaje pokonany.","final")
                    session.server.db.conn.commit(); session._recap52_start=0
                except Exception:
                    pass
                self.server.db.save_character(session.character)

            for item_id, chance in template["drops"].items():
                if random.random() <= chance:
                    # v0.35.9: every normal mob drop is shared locally with the
                    # whole eligible party. Roll the configured chance exactly once
                    # per defeated mob; on success each present reward recipient gets
                    # one copy of the same item.
                    drop_recipients = party_drop_recipients_v0359(item_id, recipients)
                    for winner in drop_recipients:
                        if item_id in globals().get("TECH_COMPONENT_IDS", set()) or ITEMS.get(item_id, {}).get("craftbox_category") == "technology":
                            self.server.db.add_storage_item(winner.account_id, "craftbox", item_id, 1)
                        else:
                            self.server.db.add_item(winner.account_id, item_id, 1)
                        await winner.record_item_collection(
                            item_id, source=template["name"], announce=True
                        )

                    boss_id_for_drop = canonical_bestiary_template_id(mob.template_id)
                    if boss_id_for_drop in BOSS_COLLECTION_CATALOG:
                        for party_session in recipients:
                            new_drop = self.server.db.add_boss_codex_drop(
                                party_session.account_id, boss_id_for_drop, item_id
                            )
                            if new_drop:
                                await party_session.send(
                                    f"Boss Codex: odkryty drop {ITEMS[item_id]['name']} z "
                                    f"{BOSS_COLLECTION_CATALOG[boss_id_for_drop]}."
                                )

                    for party_session in drop_recipients:
                        if party_session.loot_message_allowed(item_id):
                            if count > 1:
                                await party_session.send(
                                    f"Drop drużynowy: każdy obecny członek otrzymuje "
                                    f"{ITEMS[item_id]['name']}."
                                )
                            else:
                                await party_session.send(
                                    f"Drop: otrzymujesz {ITEMS[item_id]['name']}."
                                )

            await self.server.broadcast_room(
                self.character.room_id,
                (
                    f"{self.character.name} i drużyna pokonują "
                    f"{template['name']}."
                    if count > 1
                    else f"{self.character.name} pokonuje {template['name']}."
                ),
                exclude=self,
            )

    async def flee(self):
            if not self.combat_mob_key:
                await self.send("Nie jesteś w walce.")
                return
            if self.server.party_protector_session(self.account_id) is self:
                await self.stop_party_protection(announce=True)
            self.server.release_all_engagements_for_session(self)
            self.combat_mob_key = None
            await self.stop_realtime_combat()
            self.skill_guard = 0
            self.skill_evade = False
            self.skill_evade_lockout_until = 0.0
            self.clear_skill_buffs()
            await self.send("Wycofujesz się z walki.")
            await self.server.party_combat_broadcast(
                self, f"{self.character.name} wycofuje się z walki.", detail="normal"
            )

    async def die(self, killer):
            key = self.party_key()
            if key is not None and self.server.party_protectors.get(key) == self.account_id:
                self.server.party_protectors.pop(key, None)
                await self.server.party_nearby_broadcast(
                    self,
                    f"{self.character.name} pada; osłona drużyny zostaje wyłączona.",
                    exclude=[self],
                    detail="essential",
                    history_category="combat",
                )
            if self.resting or self.rest_task:
                await self.stop_rest(announce=False)
            _killer_mob = self.server.world.mobs.get(self.combat_mob_key) if self.combat_mob_key else None
            self.server.release_all_engagements_for_session(self)
            if _killer_mob and _killer_mob.template_id in MOB_TEMPLATES:
                _kt = MOB_TEMPLATES[_killer_mob.template_id]
                _base = str(_kt.get("base_template") or _killer_mob.template_id)
                _base_t = MOB_TEMPLATES.get(_base, _kt)
                _stage = int(ROOMS.get(old_room if 'old_room' in locals() else self.character.room_id, {}).get("generator_level", _kt.get("generator_level", 1)) or 1)
                _row = self.server.db.promote_nemesis_v029(
                    self.account_id, _base, _base_t.get("name", _kt.get("name", _base)), self.character.name, _stage, self.character.room_id
                )
                self.server.world.remove_v029_nemesis(self.account_id)
                await self.send(f"NEMESIS POWSTAJE: {_row['nemesis_name']}. Ranga {int(_row['rank'])}. Wpisz nemesis po odrodzeniu.")
            self.combat_mob_key = None
            await self.stop_realtime_combat()
            self.skill_guard = 0
            self.skill_evade = False
            self.skill_evade_lockout_until = 0.0
            # v0.30.35: śmierć jest bezstratna. Nie kasuje waluty, przedmiotów,
            # EQ, progresji ani aktywnych 30-sekundowych buffów.
            self.character.deaths += 1
            self.server.db.add_lifetime_stat(self.account_id, "deaths", 1)
            old_room = self.character.room_id
            self.character.room_id = "temple"
            self.current_hp = self.max_hp()
            self.current_mana = self.max_mana()
            self.server.db.save_character(self.character)
            await self.server.broadcast_room(
                old_room, f"{self.character.name} pada w walce.", exclude=self
            )
            try:
                _dur=int(max(0.0,__import__("time").time()-float(getattr(self,"_recap52_start",__import__("time").time())))*1000)
                self.server.db.conn.execute("INSERT INTO death_recaps_v03052(account_id,killer,room_id,damage_taken,duration_ms) VALUES(?,?,?,?,?)",(self.account_id,str(killer),str(old_room),int(getattr(self,"_recap52_taken",0)),_dur))
                self.server.db.conn.execute("INSERT INTO combat_recaps_v03052(account_id,opponent,duration_ms,damage_dealt,damage_taken,healing,crits,skills_used,result) VALUES(?,?,?,?,?,?,?,?,?)",(self.account_id,str(killer),_dur,int(getattr(self,"_recap52_dealt",0)),int(getattr(self,"_recap52_taken",0)),int(getattr(self,"_recap52_heal",0)),int(getattr(self,"_recap52_crits",0)),int(getattr(self,"_recap52_skills",0)),"death"))
                self.server.db.set_recap_summary_v0320(self.account_id,str(killer),f"Śmierć od: {killer}",int(getattr(self,"_recap32_guard_saved",0)),int(getattr(self,"_recap52_heal",0)),"death")
                self.server.db.add_combat_event_v0320(self.account_id,f"{killer} zadaje finalny cios. {self.character.name} ginie.","final")
                self.server.db.conn.commit(); self._recap52_start=0
            except Exception:
                pass
            await self.send(f"Pokonuje cię {killer}.")
            await self.send(
                "Śmierć nie powoduje utraty waluty, przedmiotów, EQ ani progresji. "
                "Aktywne buffy zachowują pozostały czas działania."
            )
            await self.send("Twoja dusza odradza się w Świątyni Odrodzenia.")
            await self.look()
