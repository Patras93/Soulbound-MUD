# -*- coding: utf-8 -*-
"""Original Soulbound session/DB method bodies, source-preserving extraction.
Globals are bound to the historical host module at class initialization.
"""
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

