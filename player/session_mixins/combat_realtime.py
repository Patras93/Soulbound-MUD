# -*- coding: utf-8 -*-
"""Realtime combat lifecycle and basic attacks.

v0.47.0: explicit combat architecture; no compatibility-global injection.
"""
import asyncio
import random
import time

from core.classes_skills import SOUL_WEAPON_ATTACK_TECHNIQUES
from core.progression_600 import SOUL_WEAPON_MASTERY_MAX_LEVEL
from core.progression_resources import soul_weapon_mastery_bonuses, v0190_scaled_gain
from core.bootstrap_economy_professions import soul_weapon_trait_totals
from data.mobs import MOB_TEMPLATES
from world.machine_expansion import v0314_adjust_damage_vs_template

class SessionCombatRealtimeMixin:
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

