# -*- coding: utf-8 -*-
"""Original Soulbound session/DB method bodies, source-preserving extraction.
Globals are bound to the historical host module at class initialization.
"""
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
            # Opening summons happen before the player's first realtime hit.
            # This also covers skill/AoE engagements routed through this method.
            if getattr(mob, 'engaged_by', None):
                await self.boss_summon_wave_v1301(mob, opening=True)
            self.combat_task = asyncio.create_task(self.realtime_combat_loop())


async def boss_summon_wave_v1301(self, mob, opening=False):
    """Spawn one real helper once at engagement, then unlimited regular waves."""
    template = MOB_TEMPLATES.get(getattr(mob, 'template_id', ''), {})
    if opening and getattr(mob, 'engaged_by', None):
        # Shared arena: partners join before the player's first hit/skill.
        for ally in council_allies(
            self.server.world.room_mobs(mob.room_id), mob.room_id, mob
        ):
            if not getattr(ally, 'engaged_by', None):
                ally.engaged_by = mob.engaged_by
                ally.aoe_engaged_by = mob.engaged_by
                ally.engaged_at = time.monotonic()
                ally.combat_turn = 0
                ally.boss_opening_summoned_v1301 = False
                await self.server.party_combat_broadcast(
                    self, f"Rada Starożytnych: {MOB_TEMPLATES[ally.template_id]['name']} dołącza do bitwy!",
                    detail='essential',
                )
    if not boss_companion_due_v1281(mob, template, opening=opening):
        return False
    # Mark the opening before any awaited broadcast (party-safe).
    if opening:
        mob.boss_opening_summoned_v1301 = True
    add = self.server.world.spawn_boss_companion_v1281(mob)
    if add is None:
        if opening:
            mob.boss_opening_summoned_v1301 = False
        return False
    mob.boss_last_summon_turn_v1281 = int(getattr(mob, 'combat_turn', 0) or 0)
    await self.server.party_combat_broadcast(
        self, f"{template.get('name', 'Boss')} przyzywa "
        f"{MOB_TEMPLATES[add.template_id]['name']}!"
        + (" Uzdrowiciel przywraca część HP bossa."
           if MOB_TEMPLATES[add.template_id].get('boss_guardian_role_v12811') == 'uzdrowiciel' else ""),
        detail='essential',
    )
    return True


async def grant_soul_weapon_mastery_hit_xp(self, mob=None):
            if (
                not self.character
                or self.character.soul_weapon_mastery_level
                >= SOUL_WEAPON_MASTERY_MAX_LEVEL
            ):
                return
            level=max(1,int(self.character.soul_weapon_mastery_level))
            content_stage=level
            if mob is not None:
                template=MOB_TEMPLATES.get(
                    str(getattr(mob,"template_id","")),{}
                )
                if template:
                    content_stage=max(
                        content_stage,v0190_mob_stage(template)
                    )
            gain=v0190_scaled_gain(30,level,"skill",30)
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
            # Soul Weapon mastery also uses the unified per-award Multi Cap.
            # The dedicated skill ledger keeps its overflow separate.
            from systems.experience_bank_v2011 import banked_experience_v2011
            gain=banked_experience_v2011(
                self.server.db, self.account_id, gain, 'skill', level,
                source_key='soul_weapon_mastery',
            )
            result=self.character.add_soul_weapon_mastery_xp(gain)
            self.session_summary_add("soul_weapon_mastery_xp", gain)
            if result["level_ups"]:
                await self.send(
                    f"Soul Weapon Mastery wzrasta do {result['level']}/{SOUL_WEAPON_MASTERY_MAX_LEVEL}.",
                    combat_detail="essential",
                )


async def apply_uoss_helper_turn_v1146(self, mob):
    """One real helper spell per boss round, even for a whole party."""
    if not mob or not mob.alive:
        return None
    template = MOB_TEMPLATES[mob.template_id]
    action = superboss_helper_action_v1146(self, template, mob)
    if not action:
        return None
    name, ability = action["name"], action["ability"]
    party, target = action["party"], action["target"]
    text = None
    if ability in {"Cure Water", "Cure"} and target:
        if superboss_healing_blocked_v11179(target):
            text = f"{name} używa {ability}, ale Nullify Healing blokuje leczenie."
        else:
            base = target.max_hp()
            # 23% is a Soulbound helper balance rule, not a UOSS source value.
            amount = min(max(0, base - target.current_hp), max(1, int(base * .23)))
            target.current_hp += amount
            target._recap52_heal = int(getattr(target, "_recap52_heal", 0) or 0) + amount
            text = f"{name} używa {ability}: {target.character.name} odzyskuje {amount} HP."
    elif ability in {"Faerie Walnut", "X-Ether"} and target:
        before = target.current_mana
        # UOSS specifies 20% only for Popoi's Faerie Walnut.
        percent = .20 if ability == "Faerie Walnut" else .25
        target.current_mana = min(target.max_mana(), target.current_mana + max(1, int(target.max_mana() * percent)))
        text = f"{name} używa {ability}: {target.character.name} odzyskuje {target.current_mana-before} MP."
    elif ability == "Bubble":
        recipients = []
        for member in party:
            if not getattr(member, "uoss_helper_bubble_v1146", False):
                member.uoss_helper_bubble_v1146 = True
                recipients.append(member.character.name)
        text = (f"{name} używa Bubble: +50% maksymalnego HP dla " + ", ".join(recipients) + ".") if recipients else None
    elif ability == "Dryad Preach":
        # No fabricated Protect/Shell multiplier; existing class status APIs
        # define those effects independently. A small group mana regen is a
        # Soulbound support interpretation of this helper action.
        restored = 0
        for member in party:
            gain = min(max(0, member.max_mana()-member.current_mana), max(1, int(member.max_mana()*.08)))
            member.current_mana += gain
            restored += gain
        text = f"{name} używa Dryad Preach: drużyna odzyskuje łącznie {restored} MP."
    elif ability == "Power Breakdown":
        mob.uoss_power_breakdown_v11174 = True
        mob.uoss_power_breakdown_target_scope_v11196 = "enemy_only"
        text = f"Seifer używa Power Breakdown: moc ataków bossa spada."
    else:
        if mob.hp <= 1:
            return None
        if name == "Popoi" and ability in {"Vine Hell", "Luna"}:
            affected = []
            for enemy in self.server.session_engaged_mobs(self, self.character.room_id):
                if not enemy.alive:
                    continue
                enemy_template = MOB_TEMPLATES.get(enemy.template_id, {})
                if enemy_template.get("uoss_unique_superboss_key") == "black_rabite":
                    continue  # UOSS: Black Rabite is immune to all statuses.
                flag = "uoss_helper_slow_rounds_v1146" if ability == "Vine Hell" else "uoss_helper_mini_rounds_v1146"
                setattr(enemy, flag, 3)
                affected.append(enemy_template.get("name", enemy.template_id))
            if affected:
                await self.server.party_combat_broadcast(
                    self, f"{name}: {ability} nakłada efekt na: " + ", ".join(affected) + ".",
                    detail="normal",
                )
        kind = "physical" if name == "Seifer" else "magic"
        power = self.physical_power() if kind == "physical" else self.spell_power()
        # Not source-exact damage; helper action takes the place of the old
        # extra generic helper hit on every basic/skill attack.
        mult = float((superboss_helper_profile_v11137(self, template) or {}).get("damage_multiplier", 1.0))
        damage = max(1, int((power + self.character.soul_power()) * .32 * mult))
        damage = await self.apply_boss_defense(mob, damage)
        damage = self.v0210_adjust_player_damage(damage)
        damage, _ = v0314_adjust_damage_vs_template(template, damage, kind, ability)
        damage = min(max(0, mob.hp - 1), max(0, int(damage)))
        mob.hp -= damage
        self._recap52_dealt = int(getattr(self, "_recap52_dealt", 0) or 0) + damage
        text = f"{name} używa {ability}: {damage} obrażeń. {template['name']}: {mob.hp} HP."
    if text:
        await self.server.party_combat_broadcast(self, text, detail="essential")
    return ability


async def realtime_player_action(self, mob):
            if not mob or not mob.alive:
                return
            # Re-evaluate only upward so late party joins / stronger current
            # builds cannot leave an already engaged mob as a one-hit sponge.
            self.apply_adaptive_mob_scale_v11330(mob)
            await self.apply_uoss_helper_turn_v1146(mob)
            await self.mercenary_combat_turn_v1170(mob)
            if not mob.alive or mob.hp <= 0:
                return
            await self.chaos_boss_phase_v1800(mob)
            await self.ancient_boss_phase_v1900(mob)
            await self.summon_combat_turn_v1700(mob)
            if not mob.alive or mob.hp <= 0:
                return
            await self.class_support_turn_v1700()
            if not mob.alive or mob.hp <= 0:
                return  # mercenary finished the encounter via mob_defeated
            # Timed V-MAX must expire during ordinary realtime combat too,
            # not only when the player manually invokes another skill.
            await self.mec_refresh_vmax_v0319()
            # v1.12.1: auto-kolejka i Broń Duszy są niezależnymi warstwami
            # tej samej rundy gracza. Kolejka może wykonać maksymalnie jeden
            # gotowy skill/spell, ale nie zużywa już zwykłego ataku Bronią Duszy.
            # Dzięki temu pełna kolejka bez cooldownów nie blokuje Soul Weapon
            # Mastery, właściwości Broni Duszy ani samego autoataku.
            await self.try_auto_skill_queue(mob)
            if (
                not mob
                or not mob.alive
                or mob.room_id != self.character.room_id
            ):
                return

            template = MOB_TEMPLATES[mob.template_id]
            self._last_mana_focus_gain = 0
            # Maxwell Program: exact source regeneration is 1% maximum MP per
            # six seconds. Authored Mec magic/support skills use their exact
            # source MP costs, so Maxwell restores that shared mana resource.
            if self.character.class_name=="Mec":
                _maxwell=next((s for s in self.class_skills() if s.get("mec_special")=="maxwell_program"),None)
                if _maxwell and self.job_ability_selected("inherent",_maxwell["id"]):
                    _now=time.monotonic()
                    _last=float(getattr(self,"v0319_maxwell_mana_tick",0.0) or 0.0)
                    if _last<=0.0:
                        self.v0319_maxwell_mana_tick=_now
                    elif _now-_last>=6.0:
                        _ticks=max(1,int((_now-_last)//6.0))
                        self.v0319_maxwell_mana_tick=_last+6.0*_ticks
                        _gain=max(1,int(round(self.max_mana()*0.01)))*_ticks
                        self.current_mana=min(self.max_mana(),self.current_mana+_gain)
            _relic_id,_relic=self.active_soul_weapon_relic_v11176()
            _zantetsuken_no_melee=(_relic_id=="uoss_odin_unique_2" and self.character.class_type=="physical")
            damage = 0 if _zantetsuken_no_melee else self.player_damage()
            # Combat Mastery / Shooting Mastery are selected inherents. Their
            # source helps establish weapon/stat gates and relative strength,
            # but provide no numeric bonus. Until the real hand/weapon model
            # supplies a canonical mastery modifier, do not fabricate one here.
            # v0.35.1: Soul Weapon Mastery wzmacnia wyłącznie zwykły atak broni.
            mastery = soul_weapon_mastery_bonuses(self.character.soul_weapon_mastery_level)
            damage = max(0, int(round(damage * (1.0 + (mastery["damage_percent"] + weapon_resonance_percent(self.character.soul_weapon_mastery_level)) / 100.0))))
            # v0.33.16: właściwości Soul Tier działają tylko na zwykły atak
            # Broni Duszy. Nie modyfikują skilli ani spelli.
            trait_totals = soul_weapon_trait_totals_v11193(self.character.soul_tier, self.character.class_name)
            damage = max(0, int(round(damage * (1.0 + trait_totals["damage_percent"] / 100.0))))
            if mob.hp <= max(
                1,
                int(round(self.mob_effective_max_hp_v11330(mob, template) * 0.35)),
            ):
                damage = max(0, int(round(damage * (1.0 + trait_totals["execute_damage_percent"] / 100.0))))
            _is_boss_target = any(template.get(flag) for flag in (
                "world_boss", "mini_boss", "crypt_boss", "astral_boss",
                "mythic_crypt_boss", "mythic_astral_boss", "giant_fortress_boss",
            ))
            if _is_boss_target:
                _boss_bonus = float(trait_totals["boss_damage_percent"]) + float(mastery["boss_damage_percent"])
                if _boss_bonus > 0 and not _zantetsuken_no_melee:
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
                damage = max(0, int(round(damage * weapon_crit_multiplier)))
                await self.send_combat(
                    f"TRAFIENIE KRYTYCZNE BRONI DUSZY! Zręczność {self.effective_dexterity()}. "
                    f"Szansa tego ataku: {round(weapon_crit_chance * 100, 1)} procent.",
                    "normal",
                )
            # Helpers now cast one active UOSS-inspired action per boss round.
            # Never append an identical bonus strike to every party attack.
            _uoss_helper_damage = 0
            damage = await self.apply_boss_defense(mob, damage)
            if _zantetsuken_no_melee:
                damage = 0
            damage = self.v0210_adjust_player_damage(damage)
            _basic_kind = "physical" if self.character.class_type == "physical" else "magic"
            damage, machine_note = v0314_adjust_damage_vs_template(template, damage, _basic_kind, "")

            # v1.12.5: ordinary Soul Weapon multi-hit reads final Speed.
            # DEX/AGI builds Speed, while Haste separately doubles the available
            # hit string. Resolve
            # hits sequentially and stop immediately when the target dies,
            # matching logs where a nearly dead target receives fewer hits.
            _potential_hits = 1 if _zantetsuken_no_melee else self.basic_attack_hit_count_v11196()
            _actual_hits = 0
            damage = max(0, int(damage * self.class_damage_multiplier_v1700()))
            _per_hit_damage = max(0, int(damage))
            _total_basic_damage = 0
            for _ in range(_potential_hits):
                if mob.hp <= 0:
                    break
                mob.hp -= _per_hit_damage
                _total_basic_damage += _per_hit_damage
                _actual_hits += 1
            damage = _total_basic_damage
            self._recap52_dealt=int(getattr(self,"_recap52_dealt",0))+max(0,int(damage))+max(0,int(_uoss_helper_damage))
            await self.grant_soul_weapon_mastery_hit_xp(mob)
            echo_damage = 0
            if not _zantetsuken_no_melee and mob.hp > 0 and mastery["echo_chance"] > 0 and random.random() < mastery["echo_chance"]:
                echo_damage = max(1, int(round(damage * mastery["echo_damage_percent"] / 100.0)))
                mob.hp -= echo_damage
                self._recap52_dealt = int(getattr(self, "_recap52_dealt", 0)) + echo_damage
            soul_heal = 0
            _eq_specials_v1150 = self.equipment_property_totals()
            _lifesteal = float(trait_totals.get("lifesteal_percent", 0.0) or 0.0) + min(8.0, float(_eq_specials_v1150.get("lifesteal_percent", 0.0) or 0.0))
            if _lifesteal > 0 and self.current_hp < self.max_hp() and not superboss_healing_blocked_v11179(self):
                soul_heal = min(self.max_hp() - self.current_hp, max(1, int(round(damage * _lifesteal / 100.0))))
                if soul_heal > 0:
                    self.current_hp += soul_heal
                    self._recap52_heal = int(getattr(self, "_recap52_heal", 0)) + soul_heal
            _mana_restore = 0
            _mana_pct = float(trait_totals.get("mana_restore_percent", 0.0) or 0.0) + min(6.0, float(_eq_specials_v1150.get("mana_restore_percent", 0.0) or 0.0))
            if _mana_pct > 0 and self.current_mana < self.max_mana():
                _mana_restore = min(self.max_mana() - self.current_mana, max(1, int(round(damage * _mana_pct / 100.0))))
                if _mana_restore > 0:
                    self.current_mana += _mana_restore
            technique = SOUL_WEAPON_ATTACK_TECHNIQUES.get(
                self.character.class_name, "Atak Broni Duszy"
            )
            await self.send_combat(
                f"Broń Duszy {self.character.soul_weapon}: {technique}. "
                f"Cel {template['name']}. "
                + (
                    f"Trafiasz {_actual_hits} razy po {_per_hit_damage} obrażeń. Łącznie {damage}. "
                    if _actual_hits > 1 else
                    f"Zadajesz {damage} obrażeń. "
                )
                + f"Przeciwnik: {max(0, mob.hp)} z {self.mob_effective_max_hp_v11330(mob, template)} życia."
                + (f" Właściwość Broni Duszy leczy {soul_heal}." if soul_heal > 0 else "")
                + (f" Odzyskujesz {_mana_restore} Many." if _mana_restore > 0 else "")
                + (f" Echo Broni Duszy zadaje dodatkowo {echo_damage} obrażeń." if echo_damage > 0 else "")
                + machine_note,
                "normal",
            )
            _party_attack = (
                f"{self.character.name}: {technique}, {_actual_hits} trafień, "
                f"{damage + echo_damage} obrażeń w {template['name']}"
            )
            if critical:
                _party_attack += ". Krytyk"
            if mob.hp <= 0:
                _party_attack += ". Pokonany"
            await self.server.party_combat_broadcast(self, _party_attack + ".")
            if mob.hp <= 0:
                await self.mob_defeated(mob)

