# -*- coding: utf-8 -*-
"""Skill discovery, catalog, learning and target validation."""

# v0.44.0: explicit dependencies; no compatibility-global injection.
import math
import random
import time
from core.bootstrap_economy_professions import SOUL_MILESTONE_TIERS, SOUL_TRIAL_QUEST_IDS, soul_weapon_trait_for_tier
from core.classes_skills import CLASSES, CLASS_SKILLS, NATURAL_SKILL_INTENTS, ROOMS
from core.progression_600 import SKILL_MAX_LEVEL, SOUL_MAX_TIER, SOUL_TIER_THRESHOLDS
from core.progression_resources import skill_cooldown_multiplier, skill_xp_to_next, v0190_scaled_gain
from network.protocol_gameplay_utils import find_by_name, normalize_lookup_text
from systems.content_registry import MOB_TEMPLATES, NPCS, QUESTS
from systems.equipment_crafting import GUILD_REPUTATION_MAX
from world.economy_quests import v0863_is_boss_template


class SessionSkillLearningMixin:
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
            # v0.36.8: odblokowanie Soul Tieru jest wydarzeniem lokalnym.
            # Każdy gracz stojący w dokładnie tej samej lokacji dostaje krótką
            # informację, niezależnie od członkostwa w drużynie. Właściciel
            # Tieru ma już pełny komunikat powyżej, więc jest wykluczony z
            # broadcastu, aby NVDA nie czytał awansu dwa razy.
            await self.server.broadcast_room(
                self.character.room_id,
                f"{self.character.name} odblokował Tier Duszy {next_tier} z {SOUL_MAX_TIER}.",
                exclude=self,
                history_category="system",
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
                            self.skill_cooldown_ready_at_v0364(skill)
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
                    party_targets = self.server.party_engaged_mobs(
                        self, self.character.room_id
                    )
                    if len(party_targets) == 1:
                        mob = party_targets[0]
                    elif len(party_targets) > 1:
                        await self.send(
                            "Drużyna walczy z kilkoma przeciwnikami. Podaj nazwę celu: "
                            + ", ".join(
                                MOB_TEMPLATES[target.template_id]["name"]
                                for target in party_targets
                            )
                            + "."
                        )
                        return None
                    else:
                        await self.send("Ta umiejętność wymaga celu. Podaj nazwę przeciwnika.")
                        return None
                if mob is None:
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
