# -*- coding: utf-8 -*-
"""Realtime combat lifecycle and basic attacks.

v0.47.0: explicit combat architecture; no compatibility-global injection.
"""
import asyncio
import random
import time

from core.classes_skills import SOUL_WEAPON_ATTACK_TECHNIQUES
from core.progression_600 import SOUL_WEAPON_MASTERY_MAX_LEVEL, soul_weapon_trait_totals
from core.progression_resources import soul_weapon_mastery_bonuses, v0190_scaled_gain
from data.mobs import MOB_TEMPLATES
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
    superboss_healing_blocked_v11179,
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
                # Maxwell Program: exact source regeneration is 1% maximum MP per
                # six seconds. Authored Mec magic/support skills use their exact
                # source MP costs, so Maxwell restores that shared mana resource.
                if self.character.class_name=="Mec":
                    _maxwell=next((s for s in self.available_class_skills() if s.get("mec_special")=="maxwell_program"),None)
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
                damage = max(0, int(round(damage * (1.0 + mastery["damage_percent"] / 100.0))))
                # v0.33.16: właściwości Soul Tier działają tylko na zwykły atak
                # Broni Duszy. Nie modyfikują skilli ani spelli.
                trait_totals = soul_weapon_trait_totals(self.character.soul_tier, self.character.class_name)
                damage = max(0, int(round(damage * (1.0 + trait_totals["damage_percent"] / 100.0))))
                if mob.hp <= max(1, int(round(template["max_hp"] * 0.35))):
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
                _uoss_helper = superboss_helper_profile_v11137(self, template)
                _uoss_helper_damage = 0
                if _uoss_helper and not _zantetsuken_no_melee:
                    # v1.11.86: helpers are real combatants, not a cosmetic x1.0 marker.
                    # Their strike follows the player's current build, so shop/drop/crafted
                    # and future EQ that raises effective stats also raises helper output.
                    _helper_name = str(_uoss_helper.get("name", "Pomocnik"))
                    _helper_magic = _helper_name in {"Popoi", "Primm", "Montblanc", "Byblos"}
                    _helper_stat = self.spell_power() if _helper_magic else self.physical_power()
                    _helper_kind = "magic" if _helper_magic else "physical"
                    _helper_mult = self.equipment_damage_multiplier(_helper_kind)
                    _helper_mult *= self.total_set_damage_multiplier()
                    _uoss_helper_damage = max(
                        1,
                        int(round((self.character.soul_power() + _helper_stat) * 0.65 * _helper_mult)),
                    )
                damage = await self.apply_boss_defense(mob, damage)
                if _zantetsuken_no_melee:
                    damage = 0
                damage = self.v0210_adjust_player_damage(damage)
                _basic_kind = "physical" if self.character.class_type == "physical" else "magic"
                damage, machine_note = v0314_adjust_damage_vs_template(template, damage, _basic_kind, "")
                mob.hp -= damage
                if _uoss_helper_damage > 0 and mob.hp > 0:
                    _uoss_helper_damage = await self.apply_boss_defense(mob, _uoss_helper_damage)
                    _uoss_helper_damage = self.v0210_adjust_player_damage(_uoss_helper_damage)
                    _uoss_helper_damage, _helper_machine_note = v0314_adjust_damage_vs_template(
                        template, _uoss_helper_damage, _helper_kind, _helper_name
                    )
                    _uoss_helper_damage = min(max(0, mob.hp), _uoss_helper_damage)
                    mob.hp -= _uoss_helper_damage
                    if _uoss_helper_damage:
                        await self.send_combat(
                            f"{_helper_name} pomaga: {_uoss_helper_damage} obrażeń. "
                            f"Przeciwnik: {max(0, mob.hp)} z {template['max_hp']} HP.",
                            "normal",
                        )
                self._recap52_dealt=int(getattr(self,"_recap52_dealt",0))+max(0,int(damage))+max(0,int(_uoss_helper_damage))
                await self.grant_soul_weapon_mastery_hit_xp()
                echo_damage = 0
                if not _zantetsuken_no_melee and mob.hp > 0 and mastery["echo_chance"] > 0 and random.random() < mastery["echo_chance"]:
                    echo_damage = max(1, int(round(damage * mastery["echo_damage_percent"] / 100.0)))
                    mob.hp -= echo_damage
                    self._recap52_dealt = int(getattr(self, "_recap52_dealt", 0)) + echo_damage
                soul_heal = 0
                _lifesteal = float(trait_totals.get("lifesteal_percent", 0.0) or 0.0)
                if _lifesteal > 0 and self.current_hp < self.max_hp() and not superboss_healing_blocked_v11179(self):
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
                            await self.realtime_player_action(mob)
                            await self.mec_self_repair_round_v11154()
                            # Overheat has no source duration. One completed player
                            # action is the recovery cycle; after it the state clears.
                            if self.mec_finish_overheat_recovery_v0319():
                                await self.send("OVERHEAT mija. V-MAX może być ponownie użyty.")
                            # Satellite Linker source confirms repeated minor laser
                            # damage, but no tick power/cadence/duration values. Runtime
                            # ticks stay disabled until those values are source-backed.
                            _interval=self.player_action_interval_v11154()
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
                                        target_session.current_hp = 0
                                        await self.server.party_combat_broadcast(target_session, _source_round["text"], detail="essential")
                                        await target_session.die(_enemy_template['name'])
                                        continue
                                    for _ended in superboss_advance_timed_effects_v11179(target_session):
                                        await self.server.party_combat_broadcast(target_session,f"{target_session.character.name}: kończy się efekt {_ended}.",detail="essential")
                                    _source_ability = superboss_source_ability_v11162(_enemy_template, enemy_mob)
                                    _source_effect = superboss_exact_ability_effect_v11160(target_session, _enemy_template, enemy_mob, _source_ability)
                                    _timed_effect=superboss_source_timed_effect_v11179(target_session,_enemy_template,_source_ability)
                                    if _timed_effect:
                                        await self.server.party_combat_broadcast(target_session,f"{target_session.character.name}: {_source_ability} — {_timed_effect['rounds']} rund.",detail="essential")
                                    if _source_ability:
                                        await self.server.party_combat_broadcast(target_session, f"{_enemy_template['name']} używa: {_source_ability}.", detail="essential")
                                    _source_effect_replaces_attack = False
                                    if _source_effect:
                                        if "damage" in _source_effect:
                                            target_session.current_hp=max(0,target_session.current_hp-int(_source_effect["damage"]))
                                            _source_effect_replaces_attack = True
                                        elif "current_hp_fraction" in _source_effect:
                                            target_session.current_hp=max(0,target_session.current_hp-int(round(target_session.current_hp*float(_source_effect["current_hp_fraction"]))))
                                            _source_effect_replaces_attack = True
                                        if target_session.current_hp <= 0:
                                            await target_session.die(_enemy_template['name'])
                                            continue
                                    for _summon_tid in superboss_source_summons_v11162(target_session,_enemy_template,enemy_mob,_source_ability):
                                        _summoned=self.server.world._register_runtime_spawn(target_session.character.room_id,_summon_tid)
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
                                    await self.server.party_combat_broadcast(
                                        target_session,
                                        f"{_enemy_template['name']} atakuje {target_session.character.name}."
                                        + (f" {_uoss_note}" if _uoss_note and _uoss_mult != 1.0 else ""),
                                        detail="normal",
                                    )
                                    if _source_effect_replaces_attack:
                                        # A sourced fixed/current-HP ability is the enemy action.
                                        # Do not append an unsourced ordinary hit on top of it.
                                        continue
                                    if _uoss_mult != 1.0:
                                        _old_damage = _enemy_template.get("damage", 1)
                                        _enemy_template["damage"] = max(1, int(round(float(_old_damage) * _uoss_mult)))
                                        try:
                                            await target_session.enemy_counterattack(enemy_mob)
                                        finally:
                                            _enemy_template["damage"] = _old_damage
                                    else:
                                        await target_session.enemy_counterattack(enemy_mob)

                            next_enemy = time.monotonic() + self.combat_enemy_interval
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
                    try:
                        superboss_clear_source_statuses_v11176(self)
                    except Exception:
                        pass
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
                    _uoss_helper = superboss_helper_profile_v11137(self, MOB_TEMPLATES[mob.template_id])
                    if _uoss_helper:
                        await self.server.party_combat_broadcast(
                            self, f"{_uoss_helper['name']} dołącza jako pomocnik do tej walki.", detail="essential"
                        )
                else:
                    await self.send(
                        f"Walka trwa. Cel: {MOB_TEMPLATES[mob.template_id]['name']}."
                    )
                await self.ensure_realtime_combat()

