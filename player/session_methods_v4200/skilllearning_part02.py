# -*- coding: utf-8 -*-
"""Original Soulbound session/DB method bodies, source-preserving extraction.
Globals are bound to the historical host module at class initialization.
"""
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


def skill_content_stage_v11342(self, skill):
        stages=[]
        for key in (
            "generator_level","required_mastery","required_level",
            "min_level","level","req_level",
        ):
            try:
                value=int(skill.get(key,0) or 0)
            except (TypeError,ValueError):
                value=0
            if value>0:
                stages.append(value)
        if self.combat_mob_key:
            mob=self.server.world.mobs.get(self.combat_mob_key)
            if mob and mob.alive and mob.room_id==self.character.room_id:
                template=MOB_TEMPLATES.get(mob.template_id,{})
                if template:
                    stages.append(v0190_mob_stage(template))
        if not stages:
            try:
                stages.append(int(self.highest_active_class_mastery()))
            except (TypeError,ValueError):
                stages.append(1)
        return max(1,min(800,max(stages)))


async def grant_skill_use_xp(self, skill):
        current=self.skill_progress_data(skill)
        raw_gain=25+random.randint(0,10)
        skill_level=max(1,current.get("level",1))
        content_stage=self.skill_content_stage_v11342(skill)
        gain=v0190_scaled_gain(
            raw_gain,skill_level,"skill",30
        )
        gain=max(
            1,
            int(round(
                gain
                * self.progression_content_multiplier_v11342(
                    content_stage
                )
            )),
        )
        gain=self.apply_double_xp(gain)
        from systems.experience_bank_v2011 import banked_experience_v2011
        gain=banked_experience_v2011(
            self.server.db, self.account_id, gain, 'skill', skill_level,
            source_key=skill['id'])
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
                # Mec Protocols level from real use of their own authored branch,
                # not from unrelated Mec actions. Other passive/inherent skills
                # preserve the existing class-wide passive XP behavior.
                protocol_specials=MEC_PROTOCOL_SKILLS_V11155.get(passive["id"])
                if protocol_specials is not None:
                    if str(skill.get("mec_special","")) not in set(protocol_specials):
                        continue
                passive_level = max(1, int(self.skill_progress_data(passive).get('level', 1)))
                passive_paid = banked_experience_v2011(
                    self.server.db, self.account_id, passive_gain,
                    'skill', passive_level, source_key=passive['id'])
                self.server.db.add_skill_xp(self.account_id, passive["id"], passive_paid)
        return result


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
                mob.boss_opening_summoned_v1301 = False
                mob.boss_last_summon_turn_v1281 = -1
            # Skill openers can kill a boss before its first normal turn;
            # the opening guardian must join before damage is applied.
            await self.boss_summon_wave_v1301(mob, opening=True)
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

        # Tiger Rampage lowers both physical and magical defense. Mobs do not
        # expose separate mutable defense values, so Soulbound represents the
        # dual defense loss as increased incoming damage while the break lasts.
        if (
            damage>0
            and int(
                getattr(mob,"v11196_tiger_defense_break_rounds",0) or 0
            )>0
        ):
            damage=max(
                1,int(round(
                    damage
                    * max(
                        1.0,
                        float(
                            getattr(
                                mob,
                                "v11196_tiger_defense_break_damage_multiplier",
                                1.15,
                            )
                            or 1.15
                        ),
                    )
                ))
            )

        # Real 10-second monster ally guard: shared with normal hits and skills.
        from systems.monster_ai import monster_ai_guard_damage_v1160
        damage = monster_ai_guard_damage_v1160(mob, damage)
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

        max_hp_for_phase = (
            max(1, int(getattr(mob, "adaptive_max_hp_v11330", 0) or template.get("max_hp", 1)))
            if template.get("ancient_avatar_v1330")
            else max(1, int(template.get("max_hp", 1)))
        )
        ratio = mob.hp / max_hp_for_phase
        if ratio <= 0.25:
            stage, mult = 3, 1.60
        elif ratio <= 0.50:
            stage, mult = 2, 1.35
        elif ratio <= 0.75:
            stage, mult = 1, 1.15
        else:
            stage, mult = 0, 1.0

        if template.get("ancient_avatar_v1330"):
            # Guardian role progression uses this encounter-local phase field.
            mob.v1230_boss_phase = stage
        if stage > int(getattr(mob, "phase_stage", 0)):
            mob.phase_stage = stage
            await self.send(
                f"FAZA {stage + 1}. {template['name']} staje się groźniejszy. "
                f"Siła kontrataków: +{int(round((mult - 1.0) * 100))} procent."
            )
        return mult

