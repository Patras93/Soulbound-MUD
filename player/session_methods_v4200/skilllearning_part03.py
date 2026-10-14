# -*- coding: utf-8 -*-
"""Original Soulbound session/DB method bodies, source-preserving extraction.
Globals are bound to the historical host module at class initialization.
"""
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

        # Authored ancient avatars exchange elemental techniques each phase.
        # Their real guardians are spawned by the existing boss wave system.
        if template.get('ancient_avatar_v1330'):
            max_hp=max(1,int(getattr(mob,'adaptive_max_hp_v11330',0) or template.get('max_hp',1)))
            ratio=max(0.0,float(mob.hp)/max_hp)
            phase=3 if ratio<=.25 else 2 if ratio<=.50 else 1 if ratio<=.75 else 0
            ancient=ancient_attack(mob.template_id,turn,phase)
            if ancient:
                profile['damage_type']=ancient['damage_type']
                profile['damage_multiplier']*=ancient['damage_multiplier']
                profile['defense_factor']=min(profile['defense_factor'],ancient['defense_factor'])
                profile['drain_pct']=max(profile['drain_pct'],ancient['drain_pct'])
                if ancient['special']:
                    await self.send(f"{template['name']} używa {ancient['special']}! Żywioł: {ancient['element']}. Faza {phase+1}/4.")
            # Ally support is scoped to the shared arena: no remote healing,
            # no support from dead bosses, no effect on independent UOSS.
            allies = council_allies(self.server.world.room_mobs(mob.room_id), mob.room_id, mob)
            if allies and turn % 4 == 0:
                partner = min(allies, key=lambda m: m.hp / max(1, int(getattr(m,'adaptive_max_hp_v11330',0) or MOB_TEMPLATES[m.template_id]['max_hp'])))
                partner_max = max(1,int(getattr(partner,'adaptive_max_hp_v11330',0) or MOB_TEMPLATES[partner.template_id]['max_hp']))
                amount = max(1,int(partner_max * .03))
                healed = max(0,min(amount, partner_max - partner.hp))
                if healed:
                    partner.hp += healed
                    await self.send(f"RADA STAROŻYTNYCH: {template['name']} uzdrawia {MOB_TEMPLATES[partner.template_id]['name']} za {healed} HP.")
            if allies and turn % 5 == 0:
                profile['damage_multiplier'] *= 1.12
                await self.send(f"RADA STAROŻYTNYCH: {template['name']} wykonuje wspólny atak z sojusznikiem!")
        return profile


async def mec_intercept_incoming_attack_v11196(self, mob):
        """Interrupt one incoming enemy attack when Intercept System is selected."""
        if not mob or not mob.alive:
            return False
        if not self.job_ability_selected(
            "counter","v0319_mec_intercept_system"
        ):
            return False
        _intercept=self.skill_by_id("v0319_mec_intercept_system")
        if not (
            _intercept
            and self.server.db.knows_skill(
                self.account_id,_intercept["id"]
            )
        ):
            return False

        _stat_values={
            "strength":max(1,int(self.effective_strength())),
            "dexterity":max(1,int(self.effective_dexterity())),
            "intelligence":max(1,int(self.effective_intelligence())),
            "willpower":max(1,int(self.effective_willpower())),
        }
        _stat_name,_stat_value=max(
            _stat_values.items(),
            key=lambda item:(item[1],item[0]),
        )
        _counter_skill=dict(_intercept)
        _counter_skill["scale"]=_stat_name
        _counter_level=max(
            1,min(
                SKILL_MAX_LEVEL,
                int(
                    self.server.db.skill_progress(
                        self.account_id,_intercept["id"]
                    )["level"]
                ),
            )
        )
        _counter_type=(
            "magic"
            if _stat_name in ("intelligence","willpower")
            else "physical"
        )
        # UOSS Base AP 1000 is a learning cost, not counter damage.
        # Intercept power comes from the selected effective offensive stat,
        # EQ/Soul Power and Skill Level through the shared combat core.
        _counter_core=self.offensive_skill_core_power_v11185(
            _counter_skill,
            0,
        )
        _counter_mult=(
            skill_power_multiplier(_counter_level)
            * self.offensive_skill_damage_multiplier_v11186(
                _counter_skill,_counter_type
            )
        )
        counter=max(1,int(round(_counter_core*_counter_mult)))
        counter=await self.apply_boss_defense(mob,counter)
        counter=self.v0210_adjust_player_damage(counter)
        counter=min(max(0,int(mob.hp)),max(0,int(counter)))
        mob.hp-=counter
        self._recap52_dealt=(
            int(getattr(self,"_recap52_dealt",0) or 0)+counter
        )
        _stat_labels={
            "strength":"Siła",
            "dexterity":"Zręczność",
            "intelligence":"Inteligencja",
            "willpower":"Siła Woli",
        }
        template=MOB_TEMPLATES[mob.template_id]
        await self.send_combat(
            f"Intercept System przerywa atak {template['name']} i "
            f"kontruje laserami za {counter}. Najwyższy stat: "
            f"{_stat_labels[_stat_name]} {_stat_value}. "
            f"Skill Level {_counter_level}.",
            "normal",
        )
        await self.grant_skill_use_xp(_intercept)
        if mob.hp<=0:
            await self.mob_defeated(mob)
        return True

