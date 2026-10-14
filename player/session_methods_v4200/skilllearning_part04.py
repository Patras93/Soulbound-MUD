# -*- coding: utf-8 -*-
"""Original Soulbound session/DB method bodies, source-preserving extraction.
Globals are bound to the historical host module at class initialization.
"""
async def enemy_counterattack(self, mob):
        if not mob or not mob.alive:
            return
        template = MOB_TEMPLATES[mob.template_id]
        profile = await self.boss_attack_profile(mob, template)
        _incoming_context_v11341 = dict(
            getattr(self, "_incoming_attack_context_v11341", {}) or {}
        )
        self._incoming_attack_context_v11341 = {}
        now=time.time()
        # Legacy seconds-based Feedback repair removed. Self-Repair recovery is
        # handled only by the exact source rule: full Feedback damage after 3 owner rounds.
        # v0.31.9: runtime status effects used by Mec/Engineer authored kits.
        periodic=0
        if now < float(getattr(mob,"v0319_poison_until",0.0) or 0.0):
            periodic += max(1,int(getattr(mob,"v0319_poison_power",1) or 1))
        if now < float(getattr(mob,"v0319_hp_leak_until",0.0) or 0.0):
            periodic += max(1,int(template.get("max_hp",1)*0.025))
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

        # Fallback for any direct counterattack call outside the
        # normal realtime loop. The realtime loop intercepts earlier so sourced
        # special enemy attacks are cancelled as a whole action as well.
        if await self.mec_intercept_incoming_attack_v11196(mob):
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
                f"Pasyw rasy {self.character.race} redukuje trafienie o "
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

        # V-MAX package effects are source-backed statuses. Do not apply
        # invented Protect/Shell percentages or Regen amounts here.
        self._last_death_cause_v11341 = {
            "killer": str(template.get("name") or mob.template_id),
            "template_id": str(mob.template_id),
            "mob_key": str(getattr(mob, "key", "") or ""),
            "ability": str(_incoming_context_v11341.get("ability") or ""),
            "element": str(_incoming_context_v11341.get("element") or ""),
            "damage_type": str(damage_type or ""),
            "damage": int(incoming),
        }
        self.current_hp -= incoming
        self._monster_magic_last_hit_v1151 = True
        self._recap52_taken=int(getattr(self,"_recap52_taken",0))+max(0,int(incoming))
        if time.time() < float(getattr(mob,"v0319_air_anchor_until",0.0) or 0.0) and mob.alive:
            anchor=max(1,int(getattr(mob,"v0319_air_anchor_power",1) or 1))
            mob.hp-=anchor
            await self.send_combat(f"Air Anchor odpowiada na atak: {template['name']} otrzymuje {anchor} obrażeń.","normal")
            if mob.hp<=0:
                await self.mob_defeated(mob); return
        await self.send_combat(
            f"{template['name']} atakuje. Typ obrażeń: "
            f"{'magiczne' if damage_type == 'magic' else 'fizyczne'}. "
            f"{defense_name.capitalize()} zatrzymuje {reduction} obrażeń. "
            f"Otrzymujesz {incoming}. "
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
        mastery = self.class_mastery_level(class_name)
        # `learn` displays only presently unlocked, unknown skills; the
        # historical full catalogue indexes stay stable for `learn <nr>`.
        class_skills = list(CLASS_SKILLS.get(class_name, []))
        value = str(raw or "").strip()
        if not value:
            # Only unlocked, not-yet-learned skills appear in the concise
            # `learn` list. `talk` still shows the complete teacher catalogue.
            await self.teacher_lesson(teacher, only_available=True)
            return
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
                    [candidate for candidate in class_skills
                     if mastery >= int(candidate.get("unlock", 1) or 1)],
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
        auto_role = self.auto_register_learned_skill_v3005(skill)
        await self.send(
            f"{teacher['name']} uczy cię umiejętności klasy "
            f"{class_name}: {skill['name']}. Cena: {cost_text}."
        )
        await self.send(
            f"Nauczono. {skill['name']} zaczyna na Skill Level 1."
        )
        if auto_role == "passive":
            await self.send("Ta umiejętność działa automatycznie lub nie wymaga kolejki.")
        else:
            await self.send(
                f"Automatyczne używanie: {skill['name']} dodano do kolejki "
                f"{self.skill_queue_type_label(auto_role)} bez limitu miejsc. "
                "Podczas ataku zostanie użyty, kiedy będzie gotowy. "
                "Możesz wyłączyć automatyczne skille komendą kolejka off."
            )

