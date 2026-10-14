# -*- coding: utf-8 -*-
"""Original Soulbound session/DB method bodies, source-preserving extraction.
Globals are bound to the historical host module at class initialization.
"""
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
                            # v1.80.8: poison/fire periodic hits and ice/lightning
                            # control run ONCE per monster action (not per party
                            # member). A DOT kill uses normal XP/Fame/party credit.
                            _effect_lines, _effect_skip, _effect_kill = summon_status_enemy_turn_v1808(enemy_mob)
                            for _effect_line in _effect_lines:
                                await self.server.party_combat_broadcast(
                                    self, _effect_line, detail="essential")
                            if _effect_kill:
                                await self.mob_defeated(enemy_mob)
                                continue
                            if _effect_skip:
                                continue
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
                            # v2.10.0: one NVDA-critical phase/telegraph per
                            # mob turn, before ordinary optional AI actions.
                            _titan_notice_v2100 = titan_round_v2100(
                                enemy_mob, MOB_TEMPLATES[enemy_mob.template_id])
                            if _titan_notice_v2100:
                                await self.server.party_combat_broadcast(
                                    self, _titan_notice_v2100, detail="essential")
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
                            # v1.90.1: avoid an O(world_mobs) scan for each
                            # magic/elite enemy in a 10+ target AoE encounter.
                            # Skip candidate collection while AI is on cooldown.
                            _ai_now_v1901 = time.monotonic()
                            _ai_ready_v1160 = monster_ai_due_v1901(
                                enemy_mob, _ai_template_v1160, _ai_now_v1901
                            )
                            if _ai_ready_v1160:
                                _ai_live_v1901, _ai_dead_v1901 = monster_ai_room_candidates_v1901(
                                    self.server.world, enemy_mob, _ai_template_v1160
                                )
                                _ai_plan_v1160 = monster_ai_plan_v1160(
                                    enemy_mob, _ai_template_v1160,
                                    _ai_live_v1901, _ai_dead_v1901,
                                    now=_ai_now_v1901,
                                )
                            else:
                                _ai_plan_v1160 = None
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
                            _elemental_template_v1160 = effective_elemental_template(
                                enemy_mob, _elemental_template_v1160)
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
                                    * (1.0 + .09 * max(0,min(3,int(getattr(enemy_mob,'_v1900_god_phase',0) or 0)))
                                       if _enemy_template.get('v1900_ancient_god') else 1.0)
                                    * _elite_enemy_mult_v11338
                                    * titan_attack_multiplier_v2100(enemy_mob, _enemy_template, target_session)
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
                                # v1.70.2 — living summons can intercept normal
                                # enemy strikes and really die at zero HP. Scripted
                                # boss effects have already been applied separately.
                                _raw_pet_attack_v1702=max(1,int(round(
                                    float(_enemy_template.get("damage",1))
                                    * _enemy_action_mult_v11324
                                    * target_session.v0210_enemy_damage_multiplier()
                                )))
                                _hit_summon_v1702 = await target_session.summon_take_enemy_hit_v1702(
                                    enemy_mob,raw_damage=_raw_pet_attack_v1702)
                                if not _hit_summon_v1702:
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

