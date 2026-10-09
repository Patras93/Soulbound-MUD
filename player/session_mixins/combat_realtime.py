# -*- coding: utf-8 -*-
"""Realtime combat lifecycle and basic attacks.

v0.47.0: explicit combat architecture; no compatibility-global injection.
"""
import asyncio
import random
import time

from core.classes_skills import SOUL_WEAPON_ATTACK_TECHNIQUES
from core.progression_600 import SOUL_WEAPON_MASTERY_MAX_LEVEL, soul_weapon_trait_totals_v11193
from core.progression_resources import (
    soul_weapon_mastery_bonuses,
    v0190_mob_stage,
    v0190_scaled_gain,
)
from core.player_math import (
    basic_attack_hits_from_speed,
    character_offensive_build_multiplier,
)
from data.mobs import MOB_TEMPLATES
from systems.game_feel_rewards import mob_attack_flavor_v11324
from systems.elite_variants import (
    elite_enemy_action_multiplier_v11338,
    elite_regen_amount_v11338,
)
from systems.encounter_brain_v1230 import boss_tactics_phase_v1230, tactical_element_v1230, ordinary_tactics_v1230
from systems.boss_companions_v1281 import boss_companion_due_v1281
from systems.soul_ancients_v1330 import weapon_resonance_percent
from systems.soul_evolutions_v1332 import council_allies
from systems.monster_ecology_v1250 import ecology_turn_v1250, adaptive_skills_v1250, adaptive_defense_v1250, adaptive_cadence_v1250
from systems.monster_ai import (
    monster_ai_plan_v1160, monster_ai_execute_v1160,
    monster_ai_eligible_v1160, monster_ai_necromancer_v1160,
    monster_ai_attack_multiplier_v1160, monster_ai_lifesteal_v1160,
)
from systems.monster_magic import (
    monster_magic_apply_v1151, monster_magic_tick_v1151,
    monster_magic_player_action_v1151, monster_magic_action_interval_v1151,
    monster_magic_incoming_multiplier_v1151, monster_magic_clear_v1151,
)
from systems.elemental_combat import (
    elemental_mob_attack_profile_v11339,
    elemental_target_ward_multiplier_v11339,
    elemental_target_ward_text_v11339,
)
from world.machine_expansion import v0314_adjust_damage_vs_template
from world.uoss_superboss_runtime import (
    superboss_attack_gate_v11137, superboss_helper_profile_v11137,
    superboss_phase_event_v11138, superboss_incoming_multiplier_v11138,
    superboss_source_round_event_v11160, superboss_exact_ability_effect_v11160,
    superboss_source_ability_v11162, superboss_source_summons_v11162,
    superboss_source_attack_multiplier_v11162, superboss_source_status_v11162,
    superboss_apply_source_status_v11173, superboss_combat_start_effects_v11176,
    superboss_add_round_event_v11176, superboss_clear_source_statuses_v11176,
    superboss_source_timed_effect_v11179, superboss_advance_timed_effects_v11179,
    superboss_healing_blocked_v11179, superboss_helper_action_v1146,
    superboss_helper_release_v1146,
)

class SessionCombatRealtimeMixin:
    async def stop_realtime_combat(self):
                """Zatrzymaj pętlę walki bez pozostawiania zadania w tle."""
                task = self.combat_task
                self.combat_task = None
                if task and task is not asyncio.current_task() and not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:  # AUDIT_INTENTIONAL_PASS: normal task cancellation
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
                result=self.character.add_soul_weapon_mastery_xp(gain)
                self.session_summary_add("soul_weapon_mastery_xp", gain)
                if result["level_ups"]:
                    await self.send(
                        f"Soul Weapon Mastery wzrasta do {result['level']}/{SOUL_WEAPON_MASTERY_MAX_LEVEL}.",
                        combat_detail="essential",
                    )

    def basic_attack_hit_count_v11196(self):
                """Final Speed drives Soul Weapon multi-hit; Haste doubles the series."""
                return basic_attack_hits_from_speed(
                    self.speed(),
                    haste=self.beneficial_status_active_v11154("haste"),
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

    async def realtime_combat_loop(self):
                """Realtime: jeden główny cel gracza, ale każdy mob z aggro kontratakuje."""
                this_task = asyncio.current_task()
                next_player = time.monotonic()
                # Krótki margines na pierwszą akcję gracza, aby rozpoczęcie walki było
                # czytelne dla NVDA i nie powodowało natychmiastowego ciosu w tej samej ms.
                next_enemy = time.monotonic() + 0.75
                try:
                    while not self.closed:
                        if self.current_hp <= 0 or not self.character:
                            break

                        mob = (
                            self.server.world.mobs.get(self.combat_mob_key)
                            if self.combat_mob_key
                            else None
                        )
                        if (
                            not mob
                            or not mob.alive
                            or mob.room_id != self.character.room_id
                        ):
                            # Po AoE śmierć głównego celu nie kończy walki, jeśli inne
                            # trafione moby nadal mają aggro na tę postać.
                            engaged = self.server.session_engaged_mobs(
                                self, self.character.room_id
                            )
                            if not engaged:
                                self.combat_mob_key = None
                                break
                            mob = engaged[0]
                            self.combat_mob_key = mob.key

                        now = time.monotonic()
                        if now >= next_player:
                            for _magic_tick_v1151 in monster_magic_tick_v1151(self, now):
                                await self.send_combat(_magic_tick_v1151, "essential")
                            _magic_skip_v1151 = monster_magic_player_action_v1151(self, now)
                            if _magic_skip_v1151:
                                await self.send_combat(
                                    f"{_magic_skip_v1151}: tracisz jedną automatyczną akcję. Efekt nie może ponownie przerwać ataku przed wygaśnięciem.",
                                    "essential",
                                )
                            else:
                                await self.realtime_player_action(mob)
                            await self.apply_active_regen_round_v11196()
                            await self.mec_self_repair_round_v11154()
                            await self.apply_satellite_linker_round_v11196()
                            # Overheat has no source duration. One completed player
                            # action is the recovery cycle; after it the state clears.
                            if self.mec_finish_overheat_recovery_v0319():
                                await self.send("OVERHEAT mija. V-MAX może być ponownie użyty.")
                            _interval=monster_magic_action_interval_v1151(
                                self, self.player_action_interval_v11154()
                            )
                            next_player = time.monotonic() + _interval
                            # Haste source says attacks/actions occur more frequently,
                            # but supplies no numeric speed multiplier. Soulbound has no
                            # canonical fast interval yet, so do not fabricate one.
                            # The explicit Haste status remains authoritative and also
                            # negates Slow; cadence will use a canonical fast interval
                            # once the engine defines one.
                            if self.current_hp <= 0:
                                break

                            mob = (
                                self.server.world.mobs.get(self.combat_mob_key)
                                if self.combat_mob_key
                                else None
                            )
                            if (
                                not mob
                                or not mob.alive
                                or mob.room_id != self.character.room_id
                            ):
                                engaged = self.server.session_engaged_mobs(
                                    self, self.character.room_id
                                )
                                if not engaged:
                                    self.combat_mob_key = None
                                    break
                                mob = engaged[0]
                                self.combat_mob_key = mob.key

                        now = time.monotonic()
                        if now >= next_enemy:
                            # Każdy żywy mob, którego aggro należy do tej postaci,
                            # wykonuje kontratak. Dla zwykłej walki lista ma jeden mob;
                            # po AoE może zawierać cały zaatakowany pokój.
                            enemy_mobs = self.server.session_engaged_mobs(
                                self, self.character.room_id
                            )
                            if not enemy_mobs and mob.alive:
                                if not mob.engaged_by:
                                    if mob.engaged_at <= 0:
                                        mob.engaged_at = time.monotonic()
                                    mob.engaged_by = self.character.name
                                if mob.engaged_by == self.character.name:
                                    enemy_mobs = [mob]

                            for enemy_mob in enemy_mobs:
                                # One combat round belongs to the mob action, not to
                                # each party member selected as its target.
                                enemy_mob.combat_turn=int(getattr(enemy_mob,"combat_turn",0) or 0)+1
                                if (
                                    self.closed
                                    or self.current_hp <= 0
                                    or not enemy_mob.alive
                                    or enemy_mob.room_id != self.character.room_id
                                ):
                                    break
                                _slow_left = max(0, int(getattr(enemy_mob, "uoss_helper_slow_rounds_v1146", 0) or 0))
                                _mini_left = max(0, int(getattr(enemy_mob, "uoss_helper_mini_rounds_v1146", 0) or 0))
                                if _slow_left:
                                    enemy_mob.uoss_helper_slow_rounds_v1146 = _slow_left - 1
                                    if enemy_mob.combat_turn % 2 == 0:
                                        await self.server.party_combat_broadcast(
                                            self, f"{MOB_TEMPLATES[enemy_mob.template_id]['name']} traci akcję przez Slow Popoiego.",
                                            detail="normal",
                                        )
                                        continue
                                if _mini_left:
                                    enemy_mob.uoss_helper_mini_rounds_v1146 = _mini_left - 1
                                _elite_template_v11338 = MOB_TEMPLATES[enemy_mob.template_id]
                                _elite_regen_v11338 = elite_regen_amount_v11338(
                                    _elite_template_v11338,
                                    self.mob_effective_max_hp_v11330(
                                        enemy_mob, _elite_template_v11338
                                    ),
                                    enemy_mob.hp,
                                )
                                if _elite_template_v11338.get("elite_affix") == "vampiric":
                                    _elite_regen_v11338 = 0
                                if _elite_regen_v11338 > 0:
                                    enemy_mob.hp += _elite_regen_v11338
                                    _elite_regen_text_v11338 = (
                                        f"{_elite_template_v11338['name']} wysysa energię i odzyskuje "
                                        f"{_elite_regen_v11338} HP."
                                    )
                                    await self.send_combat(
                                        _elite_regen_text_v11338, "normal"
                                    )
                                    await self.server.party_combat_broadcast(
                                        self,
                                        _elite_regen_text_v11338,
                                        detail="normal",
                                    )
                                _tiger_break_rounds=max(
                                    0,int(
                                        getattr(
                                            enemy_mob,
                                            "v11196_tiger_defense_break_rounds",
                                            0,
                                        )
                                        or 0
                                    )
                                )
                                if _tiger_break_rounds>0:
                                    _tiger_break_rounds=max(0,_tiger_break_rounds-1)
                                    enemy_mob.v11196_tiger_defense_break_rounds=(
                                        _tiger_break_rounds
                                    )
                                    if _tiger_break_rounds<=0:
                                        await self.server.party_combat_broadcast(
                                            self,
                                            f"{MOB_TEMPLATES[enemy_mob.template_id]['name']}: "
                                            "uszkodzenie obrony z Tiger Rampage wygasa.",
                                            detail="normal",
                                        )

                                _logic_rounds=max(
                                    0,int(getattr(enemy_mob,"v11196_logic_bomb_rounds",0) or 0)
                                )
                                _logic_effects=set(
                                    getattr(enemy_mob,"v11196_logic_bomb_effects",set()) or set()
                                ) if _logic_rounds>0 else set()
                                _logic_active=bool(_logic_rounds>0 and _logic_effects)
                                if _logic_active:
                                    enemy_mob.v11196_logic_bomb_rounds=max(
                                        0,_logic_rounds-1
                                    )
                                    if enemy_mob.v11196_logic_bomb_rounds<=0:
                                        # Effects remain active for this attempted mob
                                        # action and expire immediately afterward.
                                        _logic_expires_after_action=True
                                    else:
                                        _logic_expires_after_action=False
                                else:
                                    _logic_expires_after_action=False

                                _jammer_rounds=max(
                                    0,int(getattr(enemy_mob,"v11196_jammer_stop_rounds",0) or 0)
                                )
                                if _jammer_rounds>0:
                                    _jammer_rounds=max(0,_jammer_rounds-1)
                                    enemy_mob.v11196_jammer_stop_rounds=_jammer_rounds
                                    await self.server.party_combat_broadcast(
                                        self,
                                        f"{MOB_TEMPLATES[enemy_mob.template_id]['name']} jest zatrzymany przez Jammer i pomija akcję."
                                        + (
                                            f" Pozostało {_jammer_rounds} akcji Stop."
                                            if _jammer_rounds>0 else
                                            " Stop się kończy."
                                        ),
                                        detail="normal",
                                    )
                                    continue
                                _hypno_rounds=max(
                                    0,int(getattr(enemy_mob,"v11196_hypno_sleep_rounds",0) or 0)
                                )
                                if _hypno_rounds>0:
                                    _hypno_rounds=max(0,_hypno_rounds-1)
                                    enemy_mob.v11196_hypno_sleep_rounds=_hypno_rounds
                                    await self.server.party_combat_broadcast(
                                        self,
                                        f"{MOB_TEMPLATES[enemy_mob.template_id]['name']} śpi i pomija akcję."
                                        + (
                                            f" Pozostało {_hypno_rounds} akcji Sleep."
                                            if _hypno_rounds>0 else
                                            " Sleep się kończy."
                                        ),
                                        detail="normal",
                                    )
                                    continue
                                if _logic_active and "paralyze" in _logic_effects:
                                    _paralyze_chance=max(
                                        0.0,min(
                                            1.0,
                                            float(
                                                getattr(
                                                    enemy_mob,
                                                    "v11196_logic_paralyze_skip_chance",
                                                    0.50,
                                                )
                                                or 0.50
                                            ),
                                        )
                                    )
                                    if random.random() < _paralyze_chance:
                                        await self.server.party_combat_broadcast(
                                            self,
                                            f"{MOB_TEMPLATES[enemy_mob.template_id]['name']} jest sparaliżowany przez Logic Bomb i traci akcję.",
                                            detail="normal",
                                        )
                                        if _logic_expires_after_action:
                                            enemy_mob.v11196_logic_bomb_effects=set()
                                        continue
                                if _logic_active and "slow" in _logic_effects:
                                    _slow_every=max(
                                        2,int(
                                            getattr(
                                                enemy_mob,
                                                "v11196_logic_slow_skip_every_actions",
                                                2,
                                            )
                                            or 2
                                        )
                                    )
                                    _slow_counter=int(
                                        getattr(
                                            enemy_mob,
                                            "v11196_logic_slow_counter",
                                            0,
                                        )
                                        or 0
                                    )+1
                                    enemy_mob.v11196_logic_slow_counter=_slow_counter
                                    if _slow_counter % _slow_every==0:
                                        await self.server.party_combat_broadcast(
                                            self,
                                            f"{MOB_TEMPLATES[enemy_mob.template_id]['name']} jest spowolniony przez Logic Bomb i traci tę akcję.",
                                            detail="normal",
                                        )
                                        if _logic_expires_after_action:
                                            enemy_mob.v11196_logic_bomb_effects=set()
                                        continue
                                # Follow-up waves are real mobs with no alive-count limit.
                                if not (_logic_active and "silence" in _logic_effects):
                                    if await self.boss_summon_wave_v1301(enemy_mob):
                                        continue
                                # AI support is one mob action, not a second attack
                                # against every party member. Authored bosses are exempt.
                                _ai_template_v1160 = MOB_TEMPLATES[enemy_mob.template_id]
                                _ai_ready_v1160 = (
                                    enemy_mob.combat_turn % 3 == 0
                                    and monster_ai_eligible_v1160(enemy_mob, _ai_template_v1160)
                                )
                                _room_ai_v1160 = tuple(
                                    other for other in self.server.world.mobs.values()
                                    if other.room_id == enemy_mob.room_id
                                    and (other.engaged_by == enemy_mob.engaged_by or (
                                        not other.alive and monster_ai_necromancer_v1160(_ai_template_v1160)
                                    ))
                                ) if _ai_ready_v1160 else ()
                                _ai_plan_v1160 = monster_ai_plan_v1160(
                                    enemy_mob, _ai_template_v1160,
                                    [other for other in _room_ai_v1160 if other.alive],
                                    [other for other in _room_ai_v1160 if not other.alive],
                                ) if _ai_ready_v1160 else None
                                # Logic Bomb Silence cancels monster spellcasting.
                                if _ai_plan_v1160 and not (_logic_active and "silence" in _logic_effects):
                                    _ai_text_v1160 = monster_ai_execute_v1160(
                                        self.server.world, enemy_mob, _ai_template_v1160, _ai_plan_v1160,
                                    )
                                    if _ai_text_v1160:
                                        await self.server.party_combat_broadcast(
                                            self, _ai_text_v1160, detail="essential"
                                        )
                                        continue
                                # v1.25: species ecology support uses this mob's own action.
                                _ecology_v1250 = ecology_turn_v1250(
                                    self.server.world, enemy_mob, _ai_template_v1160)
                                if _ecology_v1250:
                                    await self.server.party_combat_broadcast(
                                        self, _ecology_v1250, detail="essential")
                                    continue
                                _adaptive_guard_v1250 = adaptive_defense_v1250(enemy_mob, _ai_template_v1160)
                                if _adaptive_guard_v1250:
                                    await self.server.party_combat_broadcast(
                                        self, _adaptive_guard_v1250, detail="essential")
                                    continue
                                # Ordinary mobs have a separate rare support turn;
                                # authored boss AI and specialist logic stay intact.
                                _ordinary_text_v1230 = ordinary_tactics_v1230(
                                    self.server.world, enemy_mob, _ai_template_v1160
                                )
                                if _ordinary_text_v1230:
                                    await self.server.party_combat_broadcast(
                                        self, _ordinary_text_v1230, detail="essential"
                                    )
                                    continue
                                # Phase transitions affect only this mob's offense.
                                # UOSS and manually scripted bosses are excluded.
                                _phase_1230 = boss_tactics_phase_v1230(enemy_mob, _ai_template_v1160)
                                if _phase_1230:
                                    await self.server.party_combat_broadcast(self, _phase_1230, detail="essential")
                                _sonata_rounds=max(
                                    0,int(getattr(enemy_mob,"v11196_mec_sonata_rounds",0) or 0)
                                )
                                _sonata_power_mult=(
                                    max(
                                        0.01,min(
                                            1.0,
                                            float(
                                                getattr(
                                                    enemy_mob,
                                                    "v11196_mec_sonata_power_mult",
                                                    1.0,
                                                )
                                                or 1.0
                                            ),
                                        )
                                    )
                                    if _sonata_rounds>0 else 1.0
                                )
                                _action_template = MOB_TEMPLATES[enemy_mob.template_id]
                                _elemental_template_v1160 = (
                                    dict(_action_template, attack_elements_v11339=("ice",))
                                    if _action_template.get("elite_affix") == "ice"
                                    else _action_template
                                )
                                _elemental_attack_v11339 = elemental_mob_attack_profile_v11339(
                                    _elemental_template_v1160,
                                    random.random(),
                                    getattr(enemy_mob, "combat_turn", 0),
                                )
                                _elemental_attack_v11339 = tactical_element_v1230(
                                    enemy_mob, _elemental_template_v1160, _elemental_attack_v11339
                                )
                                # Elemental special replaces the old flavor spike for
                                # this action so two independent burst multipliers do
                                # not stack into an accidental one-shot.
                                _mob_flavor_v11324 = (
                                    None
                                    if _elemental_attack_v11339
                                    else mob_attack_flavor_v11324(
                                        _action_template, random.random()
                                    )
                                )
                                _storm_every_v11338 = max(
                                    0,
                                    int(_action_template.get("elite_storm_every_v11338", 0) or 0),
                                )
                                if (
                                    _action_template.get("elite_affix") == "storm"
                                    and _storm_every_v11338 > 0
                                    and int(getattr(enemy_mob, "combat_turn", 0) or 0)
                                    % _storm_every_v11338 == 0
                                ):
                                    _storm_text_v11338 = (
                                        f"{_action_template['name']}: burzowe wyładowanie wzmacnia ten atak."
                                    )
                                    await self.send_combat(
                                        _storm_text_v11338, "essential"
                                    )
                                    await self.server.party_combat_broadcast(
                                        self,
                                        _storm_text_v11338,
                                        detail="essential",
                                    )
                                # Existing arena companions must fight alongside the
                                # boss; static world spawns are otherwise passive.
                                for _companion in self.server.world.engage_superboss_companions_v1144(enemy_mob):
                                    await self.server.party_combat_broadcast(
                                        self,
                                        f"{MOB_TEMPLATES[_companion.template_id]['name']} dołącza do walki u boku {MOB_TEMPLATES[enemy_mob.template_id]['name']}.",
                                        detail="essential",
                                    )
                                _party_targets = self.server.party_combat_targets(self, enemy_mob)
                                # One mob action attacks the whole living local party.
                                # The existing realtime loop owner remains the sole
                                # executor for mobs whose engaged_by belongs to it,
                                # preventing duplicate party-wide attacks.
                                for target_session in _party_targets:
                                    if not (
                                        target_session
                                        and not target_session.closed
                                        and target_session.current_hp > 0
                                    ):
                                        continue
                                    _enemy_template = MOB_TEMPLATES[enemy_mob.template_id]
                                    if not getattr(enemy_mob,"uoss_start_effects_done_v11176",False):
                                        enemy_mob.uoss_start_effects_done_v11176=True
                                        for _msg in superboss_combat_start_effects_v11176(target_session,_enemy_template,enemy_mob):
                                            await self.server.party_combat_broadcast(target_session,_msg,detail="essential")
                                    _add_event=superboss_add_round_event_v11176(_enemy_template,enemy_mob)
                                    if _add_event:
                                        await self.server.party_combat_broadcast(target_session,_add_event["text"],detail="essential")
                                        if _add_event.get("despawn"):
                                            continue
                                    _source_round = superboss_source_round_event_v11160(target_session, _enemy_template, enemy_mob)
                                    if _source_round and _source_round.get("instant_death"):
                                        target_session._last_death_cause_v11341 = {
                                            "killer": str(_enemy_template.get("name") or enemy_mob.template_id),
                                            "template_id": str(enemy_mob.template_id),
                                            "mob_key": str(getattr(enemy_mob, "key", "") or ""),
                                            "ability": str(_source_round.get("name") or _source_round.get("text") or "atak natychmiastowej śmierci"),
                                            "damage_type": "",
                                            "damage": max(0, int(target_session.current_hp or 0)),
                                        }
                                        target_session.current_hp = 0
                                        await self.server.party_combat_broadcast(target_session, _source_round["text"], detail="essential")
                                        await target_session.die(_enemy_template['name'])
                                        continue
                                    for _ended in superboss_advance_timed_effects_v11179(target_session):
                                        await self.server.party_combat_broadcast(target_session,f"{target_session.character.name}: kończy się efekt {_ended}.",detail="essential")
                                    _source_ability = superboss_source_ability_v11162(_enemy_template, enemy_mob)
                                    if await target_session.mec_intercept_incoming_attack_v11196(
                                        enemy_mob
                                    ):
                                        # Intercept cancels the complete incoming
                                        # attack action for this target, including
                                        # sourced special damage/status/summon handling.
                                        # If the counterlaser killed the mob, stop the
                                        # party-target loop so a dead enemy cannot
                                        # finish the same action on later members.
                                        if not enemy_mob.alive:
                                            break
                                        continue
                                    _logic_silenced=bool(
                                        _logic_active and "silence" in _logic_effects
                                    )
                                    if _source_ability and _logic_silenced:
                                        await self.server.party_combat_broadcast(
                                            target_session,
                                            f"{_enemy_template['name']}: Silence z Logic Bomb blokuje {_source_ability}.",
                                            detail="normal",
                                        )
                                        _source_ability=None
                                    if (
                                        _source_ability in {"Zantetsuken", "Shin-Zantetsuken"}
                                        and (superboss_helper_profile_v11137(target_session, _enemy_template) or {}).get("name") == "Seifer"
                                    ):
                                        if getattr(enemy_mob, "uoss_seifer_counter_turn_v1146", -1) != enemy_mob.combat_turn:
                                            enemy_mob.uoss_seifer_counter_turn_v1146 = enemy_mob.combat_turn
                                            await self.server.party_combat_broadcast(
                                                target_session,
                                                "Seifer używa Zantetsuken Reverse i odbija atak Odina!",
                                                detail="essential",
                                            )
                                        _source_ability = None
                                    _source_effect = superboss_exact_ability_effect_v11160(target_session, _enemy_template, enemy_mob, _source_ability)
                                    _timed_effect=superboss_source_timed_effect_v11179(target_session,_enemy_template,_source_ability)
                                    if _timed_effect:
                                        await self.server.party_combat_broadcast(target_session,f"{target_session.character.name}: {_source_ability} — {_timed_effect['rounds']} rund.",detail="essential")
                                    if _source_ability and getattr(enemy_mob, "uoss_ability_announced_turn_v1145", -1) != enemy_mob.combat_turn:
                                        enemy_mob.uoss_ability_announced_turn_v1145 = enemy_mob.combat_turn
                                        await self.server.party_combat_broadcast(target_session, f"{_enemy_template['name']} używa: {_source_ability}.", detail="essential")
                                    _source_effect_replaces_attack = False
                                    if _source_effect:
                                        _hp_before_v11341 = int(target_session.current_hp or 0)
                                        if "damage" in _source_effect:
                                            target_session.current_hp=max(0,target_session.current_hp-int(_source_effect["damage"]))
                                            _source_effect_replaces_attack = True
                                        elif "current_hp_fraction" in _source_effect:
                                            target_session.current_hp=max(0,target_session.current_hp-int(round(target_session.current_hp*float(_source_effect["current_hp_fraction"]))))
                                            _source_effect_replaces_attack = True
                                        _source_damage_v11341 = max(
                                            0, _hp_before_v11341 - int(target_session.current_hp or 0)
                                        )
                                        if _source_effect_replaces_attack:
                                            target_session._last_death_cause_v11341 = {
                                                "killer": str(_enemy_template.get("name") or enemy_mob.template_id),
                                                "template_id": str(enemy_mob.template_id),
                                                "mob_key": str(getattr(enemy_mob, "key", "") or ""),
                                                "ability": str(_source_ability or "specjalna zdolność"),
                                                "damage_type": "",
                                                "damage": _source_damage_v11341,
                                            }
                                        if target_session.current_hp <= 0:
                                            await target_session.die(_enemy_template['name'])
                                            continue
                                    _source_summons=tuple(
                                        superboss_source_summons_v11162(
                                            target_session,_enemy_template,enemy_mob,_source_ability
                                        )
                                    )
                                    for _summon_tid in _source_summons:
                                        _summoned=self.server.world.spawn_superboss_summon_v1144(enemy_mob,_summon_tid)
                                        if _summoned:
                                            if _summoned.engaged_at <= 0: _summoned.engaged_at=time.monotonic()
                                            if not _summoned.engaged_by: _summoned.engaged_by=target_session.character.name
                                            await self.server.party_combat_broadcast(target_session,f"{_enemy_template['name']} przyzywa {MOB_TEMPLATES[_summon_tid]['name']}.",detail="essential")
                                    _source_status_result=superboss_apply_source_status_v11173(target_session,_enemy_template,_source_ability)
                                    if _source_status_result:
                                        _source_status=_source_status_result["status"]
                                        if _source_status_result.get("blocked"):
                                            await self.server.party_combat_broadcast(target_session,f"{target_session.character.name}: {_source_status} zablokowany przez EQ.",detail="essential")
                                        else:
                                            await self.server.party_combat_broadcast(target_session,f"{target_session.character.name} otrzymuje status: {_source_status}.",detail="essential")
                                    _phase_event = superboss_phase_event_v11138(target_session, _enemy_template, enemy_mob)
                                    if _phase_event:
                                        _phase, _label = _phase_event
                                        await self.server.party_combat_broadcast(
                                            target_session,
                                            f"{_enemy_template['name']}: FAZA {_phase} — {_label}.",
                                            detail="essential",
                                        )
                                    _uoss_mult, _uoss_note = superboss_incoming_multiplier_v11138(
                                        target_session, _enemy_template, enemy_mob
                                    )
                                    _uoss_mult *= superboss_source_attack_multiplier_v11162(_enemy_template,_source_ability)
                                    _uoss_mult *= _sonata_power_mult
                                    if getattr(enemy_mob, "uoss_power_breakdown_v11174", False):
                                        _uoss_mult *= 0.85  # Soulbound balance; UOSS has no published percentage
                                    if _mini_left:
                                        _uoss_mult *= 0.80  # Soulbound helper balance for Mini
                                    if _logic_active and "curse" in _logic_effects:
                                        _uoss_mult *= max(
                                            0.01,min(
                                                1.0,
                                                float(
                                                    getattr(
                                                        enemy_mob,
                                                        "v11196_logic_curse_damage_multiplier",
                                                        0.80,
                                                    )
                                                    or 0.80
                                                ),
                                            )
                                        )
                                    _silence_blocks_basic_magic=bool(
                                        _logic_silenced
                                        and str(
                                            _enemy_template.get("damage_type","")
                                            or ""
                                        ).strip().casefold()=="magic"
                                    )
                                    if _silence_blocks_basic_magic:
                                        await self.server.party_combat_broadcast(
                                            target_session,
                                            f"{_enemy_template['name']}: Silence blokuje magiczny atak.",
                                            detail="normal",
                                        )
                                        continue
                                    _flavor_note_v11324 = (
                                        str(_mob_flavor_v11324.get("text") or "")
                                        if _mob_flavor_v11324 else ""
                                    )
                                    _elemental_note_v11339 = ""
                                    if _elemental_attack_v11339:
                                        _elemental_note_v11339 = (
                                            " "
                                            + str(_elemental_attack_v11339.get("text") or "")
                                            + elemental_target_ward_text_v11339(
                                                target_session,
                                                _elemental_attack_v11339.get("element"),
                                            )
                                        )
                                    await self.server.party_combat_broadcast(
                                        target_session,
                                        f"{_enemy_template['name']} atakuje {target_session.character.name}."
                                        + (f" {_uoss_note}" if _uoss_note and _uoss_mult != 1.0 else "")
                                        + (f" {_flavor_note_v11324}" if _flavor_note_v11324 else "")
                                        + _elemental_note_v11339,
                                        detail="normal",
                                    )
                                    if _source_effect_replaces_attack:
                                        # A sourced fixed/current-HP ability is the enemy action.
                                        # Do not append an unsourced ordinary hit on top of it.
                                        continue
                                    if (
                                        _logic_active
                                        and "blind" in _logic_effects
                                        and random.random() < max(
                                            0.0,min(
                                                0.95,
                                                float(
                                                    getattr(
                                                        enemy_mob,
                                                        "v11196_logic_blind_miss_chance",
                                                        0.35,
                                                    )
                                                    or 0.35
                                                ),
                                            )
                                        )
                                    ):
                                        await self.server.party_combat_broadcast(
                                            target_session,
                                            f"{_enemy_template['name']} chybia przez Blind z Logic Bomb.",
                                            detail="normal",
                                        )
                                        continue
                                    _flavor_mult_v11324 = (
                                        float(_mob_flavor_v11324.get("damage_multiplier", 1.0))
                                        if _mob_flavor_v11324 else 1.0
                                    )
                                    _adaptive_enemy_mult_v11330 = (
                                        target_session.adaptive_enemy_damage_multiplier_v11330(
                                            enemy_mob, _enemy_template
                                        )
                                    )
                                    _elite_enemy_mult_v11338 = (
                                        elite_enemy_action_multiplier_v11338(
                                            _enemy_template,
                                            getattr(enemy_mob, "combat_turn", 0),
                                        )
                                    )
                                    _elemental_enemy_mult_v11339 = 1.0
                                    if _elemental_attack_v11339:
                                        _elemental_enemy_mult_v11339 = (
                                            float(
                                                _elemental_attack_v11339.get(
                                                    "damage_multiplier", 1.0
                                                )
                                                or 1.0
                                            )
                                            * elemental_target_ward_multiplier_v11339(
                                                target_session,
                                                _elemental_attack_v11339.get("element"),
                                            )
                                        )
                                    _basic_attack_ability_v11341 = (
                                        str(_source_ability or "")
                                        if _source_ability
                                        and not _source_status_result
                                        and not _timed_effect
                                        and not _source_summons
                                        else ""
                                    )
                                    target_session._incoming_attack_context_v11341 = {
                                        "ability": _basic_attack_ability_v11341,
                                        "element": str(
                                            (_elemental_attack_v11339 or {}).get("label") or ""
                                        ),
                                    }
                                    _enemy_action_mult_v11324 = (
                                        _uoss_mult
                                        * _flavor_mult_v11324
                                        * _adaptive_enemy_mult_v11330
                                        * _elite_enemy_mult_v11338
                                        * monster_ai_attack_multiplier_v1160(enemy_mob)
                                        * adaptive_skills_v1250(
                                            enemy_mob, _enemy_template,
                                            getattr(enemy_mob, 'adaptive_party_dps_v11330', 0),
                                            _enemy_template.get('damage', 1))
                                        * _elemental_enemy_mult_v11339
                                        * monster_magic_incoming_multiplier_v1151(target_session)
                                    )
                                    target_session._monster_magic_last_hit_v1151 = False
                                    _hp_before_monster_v1160 = int(target_session.current_hp or 0)
                                    if (
                                        _enemy_action_mult_v11324 != 1.0
                                        or _elemental_attack_v11339
                                    ):
                                        _old_damage = _enemy_template.get("damage", 1)
                                        _old_damage_type = _enemy_template.get(
                                            "damage_type", "physical"
                                        )
                                        _enemy_template["damage"] = max(
                                            1,
                                            int(round(
                                                float(_old_damage)
                                                * _enemy_action_mult_v11324
                                            )),
                                        )
                                        if _elemental_attack_v11339:
                                            _enemy_template["damage_type"] = str(
                                                _elemental_attack_v11339.get(
                                                    "defense_channel", "magic"
                                                )
                                                or "magic"
                                            )
                                        try:
                                            await target_session.enemy_counterattack(enemy_mob)
                                        finally:
                                            _enemy_template["damage"] = _old_damage
                                            _enemy_template["damage_type"] = _old_damage_type
                                    else:
                                        await target_session.enemy_counterattack(enemy_mob)
                                    _drained_v1160 = monster_ai_lifesteal_v1160(
                                        enemy_mob, _enemy_template,
                                        max(0, _hp_before_monster_v1160 - int(target_session.current_hp or 0)),
                                    )
                                    if _drained_v1160:
                                        await self.server.party_combat_broadcast(
                                            target_session,
                                            f"{_enemy_template['name']} wysysa {_drained_v1160} HP z trafienia.",
                                            detail="normal",
                                        )
                                    # Apply a spell status only after an actual hit:
                                    # dodge, guard evasion and Mec interception never proc it.
                                    if (
                                        _elemental_attack_v11339
                                        and getattr(target_session, "_monster_magic_last_hit_v1151", False)
                                        and target_session.current_hp > 0
                                    ):
                                        _element_v1151 = _elemental_attack_v11339["element"]
                                        _ward_getter_v1151 = getattr(
                                            target_session, "equipment_element_ward_v11176", None
                                        )
                                        _ward_v1151 = (
                                            float(_ward_getter_v1151(_element_v1151) or 0.0)
                                            if callable(_ward_getter_v1151) else 0.0
                                        )
                                        _spell_status_v1151 = monster_magic_apply_v1151(
                                            target_session, _element_v1151, random.random(),
                                            ward=_ward_v1151,
                                        )
                                        if _spell_status_v1151:
                                            await self.server.party_combat_broadcast(
                                                target_session,
                                                f"{target_session.character.name}: {_spell_status_v1151}",
                                                detail="essential",
                                            )

                                if _logic_active and _logic_expires_after_action:
                                    enemy_mob.v11196_logic_bomb_effects=set()
                                    enemy_mob.v11196_logic_slow_counter=0
                                    await self.server.party_combat_broadcast(
                                        self,
                                        f"{MOB_TEMPLATES[enemy_mob.template_id]['name']}: efekty Logic Bomb wygasają.",
                                        detail="normal",
                                    )

                                if _sonata_rounds>0:
                                    _sonata_rounds=max(0,_sonata_rounds-1)
                                    enemy_mob.v11196_mec_sonata_rounds=_sonata_rounds
                                    if _sonata_rounds<=0:
                                        enemy_mob.v11196_mec_sonata_power_mult=1.0
                                        await self.server.party_combat_broadcast(
                                            self,
                                            f"{MOB_TEMPLATES[enemy_mob.template_id]['name']}: "
                                            "kończy się obniżenie poziomowej mocy z Mec Sonata.",
                                            detail="normal",
                                        )

                            next_enemy = time.monotonic() + adaptive_cadence_v1250(
                                enemy_mobs, MOB_TEMPLATES, self.combat_enemy_interval)
                            if self.current_hp <= 0:
                                break

                        # v1.11.21: śpij bezpośrednio do następnej zaplanowanej
                        # akcji (z limitem 1 s dla responsywnego przerwania walki).
                        # Poprzedni limit 0.20 s budził każdą walczącą sesję 5 razy
                        # na sekundę nawet wtedy, gdy żadna akcja nie była gotowa.
                        wait_for = min(next_player, next_enemy) - time.monotonic()
                        await asyncio.sleep(max(0.05, min(1.0, wait_for)))
                except asyncio.CancelledError:  # AUDIT_INTENTIONAL_PASS: normal task cancellation
                    pass
                except Exception as exc:
                    # Nie zabijaj sesji przez błąd zadania w tle; gracz może ponownie
                    # rozpocząć walkę komendą atakuj/k.
                    try:
                        await self.send(f"Pętla walki została zatrzymana: {exc}")
                    except Exception:  # AUDIT_INTENTIONAL_PASS: session may already be disconnected while reporting loop failure
                        pass
                finally:
                    monster_magic_clear_v1151(self)
                    try:
                        superboss_clear_source_statuses_v11176(self)
                    except Exception as exc:
                        reporter = getattr(self.server, "report_runtime_error", None)
                        if callable(reporter):
                            reporter(
                                exc,
                                handler="superboss_clear_source_statuses_v11176",
                            )
                    if self.combat_task is this_task:
                        self.combat_task = None
                    # Release after the final local fighter leaves the encounter.
                    if getattr(self, "character", None) and getattr(self, "server", None):
                        superboss_helper_release_v1146(self)

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
                    # v0.80.2: bez jawnej nazwy najpierw przejmij jednoznaczny
                    # wspólny cel lokalnej drużyny. Mob zaatakowany przez dowolnego
                    # członka party jest legalnym celem całej drużyny.
                    if not wanted:
                        party_targets = self.server.party_engaged_mobs(
                            self, self.character.room_id
                        )
                        if len(party_targets) == 1:
                            mob = party_targets[0]
                        elif len(party_targets) > 1:
                            await self.send(
                                "Drużyna walczy z kilkoma przeciwnikami. Podaj cel: "
                                + ", ".join(
                                    MOB_TEMPLATES[target.template_id]["name"]
                                    for target in party_targets
                                )
                                + "."
                            )
                            return
                    # v0.8.35: najpierw próbujemy znaleźć prawdziwego, żywego moba.
                    # Dzięki temu pokojowy NPC o podobnej nazwie nie blokuje komendy
                    # k <mob>, jeżeli w tym samym pokoju istnieje zabijalny przeciwnik.
                    if mob is None:
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

                _uoss_template = MOB_TEMPLATES[mob.template_id]
                _uoss_ok, _uoss_reason = superboss_attack_gate_v11137(self, _uoss_template)
                if not _uoss_ok:
                    await self.send(_uoss_reason)
                    return

                _adaptive_profile_v11330 = self.apply_adaptive_mob_scale_v11330(mob)
                new_fight = self.combat_mob_key != mob.key
                was_unengaged = not mob.engaged_by
                protector = await self.server.apply_party_protection(self, mob)
                if was_unengaged:
                    if mob.engaged_at <= 0:
                        mob.engaged_at = time.monotonic()
                    if not mob.engaged_by:
                        mob.engaged_by = self.character.name
                    mob.combat_turn = 0
                    mob.boss_opening_summoned_v1301 = False
                    mob.boss_last_summon_turn_v1281 = -1
                    mob.phase_stage = 0
                    mob.uoss_ability_announced_turn_v1145 = -1
                    # A fresh encounter cannot inherit last fight's helper debuffs.
                    mob.uoss_helper_action_turns_v1146 = {}
                    mob.uoss_helper_preach_v1146 = False
                    mob.uoss_power_breakdown_v11174 = False
                    mob.uoss_seifer_breakdown_v11174 = False
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
                    if _adaptive_profile_v11330:
                        await self.send_combat(
                            "Skala starcia: "
                            f"{_adaptive_profile_v11330['party_size']} graczy, "
                            f"ranga {_adaptive_profile_v11330['rank']}, "
                            f"HP x{_adaptive_profile_v11330['hp_multiplier']:.2f}, "
                            f"nagroda x{_adaptive_profile_v11330['reward_multiplier']:.2f}.",
                            "full",
                        )
                    _uoss_helper = superboss_helper_profile_v11137(self, MOB_TEMPLATES[mob.template_id])
                    if _uoss_helper:
                        await self.server.party_combat_broadcast(
                            self,
                            f"{_uoss_helper['name']} dołącza jako pomocnik do tej walki. "
                            f"Rola: {_uoss_helper.get('role', 'support')}.",
                            detail="essential"
                        )
                else:
                    await self.send(
                        f"Walka trwa. Cel: {MOB_TEMPLATES[mob.template_id]['name']}."
                    )
                await self.ensure_realtime_combat()

