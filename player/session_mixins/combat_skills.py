# -*- coding: utf-8 -*-
"""Class-skill execution for Soulbound combat.

v0.47.0: explicit combat architecture; no compatibility-global injection.
"""
import random
import time

from core.classes_skills import CLASS_SKILLS
from core.progression_600 import SKILL_MAX_LEVEL
from core.progression_resources import class_type_for_name, skill_power_multiplier
from core.bootstrap_economy_professions import GLOBAL_SKILL_BUFF_DURATION_SECONDS
from data.mobs import MOB_TEMPLATES
from data.rooms import ROOMS
from network.protocol_gameplay_utils import normalize_lookup_text
from world.machine_expansion import v0314_adjust_damage_vs_template
from world.economy_quests import v0863_execute_threshold

class SessionCombatSkillsMixin:
    async def use_class_skill(self, raw):
                skill, target_text = self.find_skill_from_input(raw)
                if not skill:
                    await self.send("Nie rozpoznaję tej umiejętności albo naturalny skrót jest niejednoznaczny. Wpisz skills albo umiejetnosci i użyj pełnej nazwy.")
                    return

                skill_class = self.skill_class_name(skill)
                mastery = self.class_mastery_level(skill_class)
                if mastery < int(skill["unlock"]):
                    await self.send(
                        f"{skill['name']} wymaga Biegłości klasy {skill['unlock']}. "
                        f"Aktualna Biegłość {skill_class}: {mastery}."
                    )
                    return

                if not self.server.db.knows_skill(self.account_id, skill["id"]):
                    skill_class = self.skill_class_name(skill)
                    teacher_id, teacher = self.class_teacher(skill_class)
                    await self.send(
                        f"Nie znasz jeszcze umiejętności {skill['name']} klasy "
                        f"{skill_class}. Musisz nauczyć się jej u {teacher['name']} "
                        f"w lokacji {ROOMS[teacher['room']]['name']}."
                    )
                    return

                progress = self.server.db.skill_progress(self.account_id, skill["id"])
                skill_level = int(progress["level"])
                skill_power = skill_power_multiplier(skill_level)
                effective_cooldown = self.effective_skill_cooldown(skill, skill_level)

                now = time.time()
                await self.mec_refresh_vmax_v0319()
                ready_at = self.skill_cooldown_ready_at_v0364(skill)
                if ready_at > now:
                    await self.send(
                        f"{skill['name']} jest na cooldownie jeszcze {int(ready_at - now + 0.999)} sekund."
                    )
                    return
                mana_cost = skill.get("mana", 0)
                if mana_cost > self.current_mana:
                    await self.send(
                        f"Za mało Many. {skill['name']} wymaga {mana_cost}, a masz {self.current_mana}."
                    )
                    return

                kind = skill["kind"]
                if kind == "passive":
                    await self.send(f"{skill['name']} jest umiejętnością pasywną i działa automatycznie, gdy jest nauczona.")
                    return
                if kind == "evade" and self.skill_evade:
                    await self.send("Masz już aktywny gwarantowany unik.")
                    return
                offensive = kind in ("damage", "drain", "execute", "aoe_damage")
                mob = None
                aoe_mobs = []
                if kind == "aoe_damage":
                    if self.auto_fishing or self.auto_fishing_task:
                        await self.stop_auto_fishing(announce=False)
                        await self.send("Auto-łowienie wyłączone z powodu walki.")
                    if self.auto_mining or self.auto_mining_task:
                        await self.stop_auto_mining(announce=False)
                        await self.send("Auto-kopanie wyłączone z powodu walki.")
                    if self.auto_woodcutting or self.auto_woodcutting_task:
                        await self.stop_auto_woodcutting(announce=False)
                        await self.send("Auto-Drwalstwo wyłączone z powodu walki.")
                    self.server.world.refresh()
                    aoe_mobs = [
                        candidate for candidate in self.server.world.room_mobs(self.character.room_id)
                        if candidate.alive
                    ]
                    if not aoe_mobs:
                        await self.send("Nie ma tutaj żywych przeciwników dla czaru obszarowego.")
                        return
                    # Najpierw czyścimy osierocone aggro. Dzięki temu mob nie jest
                    # blokowany przez gracza, którego już nie ma w pokoju lub walce.
                    for candidate in aoe_mobs:
                        self.server.sanitize_mob_engagement(candidate)
                    # Zachowujemy właściciela aggro sprzed AoE. Obszarówka może zranić
                    # moba walczącego z obcym graczem, ale nie kradnie jego aggro/nagród.
                    aoe_reward_owner = {candidate.key: candidate.engaged_by for candidate in aoe_mobs}
                    available_for_aggro = [
                        candidate for candidate in aoe_mobs
                        if self.server.engagement_allowed(self, candidate)
                    ]
                    for candidate in available_for_aggro:
                        if not candidate.engaged_by:
                            if candidate.engaged_at <= 0:
                                candidate.engaged_at = time.monotonic()
                            candidate.engaged_by = self.character.name
                            candidate.combat_turn = 0
                            candidate.player_hits = 0
                    # Realtime target ustawiamy tylko na moba, którego wolno nam normalnie
                    # zaatakować. Samo AoE nadal obejmuje cały pokój.
                    mob = next(
                        (candidate for candidate in available_for_aggro if candidate.key == self.combat_mob_key),
                        available_for_aggro[0] if available_for_aggro else None,
                    )
                    if mob is not None:
                        self.combat_mob_key = mob.key
                elif offensive:
                    if self.auto_fishing or self.auto_fishing_task:
                        await self.stop_auto_fishing(announce=False)
                        await self.send("Auto-łowienie wyłączone z powodu walki.")
                    if self.auto_mining or self.auto_mining_task:
                        await self.stop_auto_mining(announce=False)
                        await self.send("Auto-kopanie wyłączone z powodu walki.")
                    if self.auto_woodcutting or self.auto_woodcutting_task:
                        await self.stop_auto_woodcutting(announce=False)
                        await self.send("Auto-Drwalstwo wyłączone z powodu walki.")
                    mob = await self.skill_combat_target(target_text)
                    if not mob:
                        return

                self.current_mana -= mana_cost
                self.start_skill_cooldown_v0364(skill, effective_cooldown, now)

                # v0.31.7: Engineer authored tool mechanics.
                if skill.get("engineer_tool"):
                    special = str(skill.get("engineer_special", ""))
                    upgraded = self.engineer_tool_is_upgraded_v0317(skill)
                    passive_mult = self.engineer_passive_multiplier_v0317(skill)

                    if special == "upgrade":
                        query = (target_text or "").strip()
                        if not query:
                            active = self.engineer_upgraded_tools_v0317()
                            names = [row["name"] for row in CLASS_SKILLS.get("Inżynier", []) if row.get("id") in active]
                            details=[]
                            for row in CLASS_SKILLS.get("Inżynier", []):
                                if row.get("id") in active:
                                    details.append(f"{row['name']} ({self.engineer_upgrade_effect_text_v0319(row.get('engineer_special',''), True)})")
                            await self.send(
                                f"Upgrade 2.0: sloty {len(active)}/{self.engineer_upgrade_slots_v0317()}. " +
                                ("Ulepszone: " + "; ".join(details) + "." if details else "Brak ulepszonych narzędzi.") +
                                " Użyj: Upgrade <nazwa narzędzia> albo Upgrade reset."
                            )
                            return
                        if normalize_lookup_text(query) in ("reset","clear","wyczysc","wyczyść"):
                            self.server.db.conn.execute("DELETE FROM engineer_tool_upgrades_v0317 WHERE account_id=?",(int(self.account_id),))
                            self.server.db.conn.commit()
                            await self.send("Upgrade: wyczyszczono wszystkie sloty ulepszeń Inżyniera.")
                            await self.grant_skill_use_xp(skill)
                            return
                        candidates=[row for row in CLASS_SKILLS.get("Inżynier", []) if row.get("engineer_tool") and row.get("engineer_special") not in ("upgrade","scanner") and row.get("kind") != "passive"]
                        target=None
                        qn=normalize_lookup_text(query)
                        for row in candidates:
                            if qn in {normalize_lookup_text(row.get("name","")), normalize_lookup_text(row.get("id","")), *[normalize_lookup_text(a) for a in row.get("aliases",[])]}:
                                target=row; break
                        if not target:
                            await self.send("Upgrade: nie rozpoznaję narzędzia Inżyniera do ulepszenia.")
                            return
                        current=self.engineer_upgraded_tools_v0317()
                        if target["id"] in current:
                            await self.send(f"{target['name']} jest już ulepszone.")
                            return
                        if len(current) >= self.engineer_upgrade_slots_v0317():
                            await self.send(f"Brak wolnego slotu Upgrade. Masz {len(current)}/{self.engineer_upgrade_slots_v0317()}. Użyj Upgrade reset albo naucz się Silver Gear / Gold Battery.")
                            return
                        if self.available_recipe_item("engineer_upgrade_kit") <= 0:
                            await self.send("Ulepszenie wymaga 1 Zestawu Upgrade Inżyniera. Wykonaj go przez techcraft zestaw upgrade.")
                            return
                        if not self.consume_recipe_item("engineer_upgrade_kit", 1):
                            await self.send("Nie udało się pobrać Zestawu Upgrade Inżyniera.")
                            return
                        self.server.db.conn.execute("INSERT OR IGNORE INTO engineer_tool_upgrades_v0317(account_id,skill_id) VALUES(?,?)",(int(self.account_id),target["id"]))
                        self.server.db.conn.commit()
                        await self.send(f"Upgrade: {target['name']} zostało ulepszone. Zużyto 1 Zestaw Upgrade Inżyniera. Sloty {len(current)+1}/{self.engineer_upgrade_slots_v0317()}.")
                        await self.grant_skill_use_xp(skill)
                        return

                    if special == "scanner":
                        if not mob:
                            return
                        template=MOB_TEMPLATES[mob.template_id]
                        weaknesses=template.get("weaknesses") or template.get("machine_weaknesses") or ("brak jawnych",)
                        resistances=template.get("resistances") or template.get("machine_resistances") or ("brak jawnych",)
                        await self.send(
                            f"Scanner: {template.get('name',mob.template_id)}. HP {max(0,mob.hp)} z {template.get('max_hp',0)}. "
                            f"Typ: {'Machine' if template.get('machine') else template.get('type','organic')}. "
                            f"Ranga: {template.get('rank','normal')}. Słabości: {', '.join(map(str,weaknesses))}. "
                            f"Odporności: {', '.join(map(str,resistances))}."
                        )
                        await self.grant_skill_use_xp(skill)
                        return

                    if special == "debilitator":
                        if not mob:
                            return
                        elements=("fire","ice","lightning","water","holy","dark")
                        count=3 if upgraded else 1
                        picked=random.sample(elements,count)
                        duration=45 if self.engineer_skill_known_v0317("v0317_engineer_kinematics") else 30
                        mob.v0317_vulnerabilities=set(picked)
                        mob.v0317_vulnerability_until=time.time()+duration
                        await self.send(f"Debilitator: {MOB_TEMPLATES[mob.template_id]['name']} otrzymuje słabość: {', '.join(picked)} na {duration} s.")
                        await self.grant_skill_use_xp(skill)
                        return

                    if special == "launcher":
                        alive=[target for target in aoe_mobs if target.alive]
                        if not alive:
                            return
                        hits=6 if upgraded else 4
                        targets=random.choices(alive,k=hits)
                        total=0; defeated=[]; seen=set()
                        for target in targets:
                            if not target.alive: continue
                            before=max(1,target.hp)
                            damage=max(1,before//2)
                            target.hp-=damage; total+=damage
                            name=MOB_TEMPLATES[target.template_id]['name']
                            await self.send(f"Launcher: {name} traci połowę bieżącego HP: {damage}. HP {max(0,target.hp)}.")
                            if target.hp<=0 and target.key not in seen:
                                seen.add(target.key); defeated.append(target)
                        await self.grant_skill_use_xp(skill)
                        await self.send(f"Launcher: {hits} pocisków, łączne obrażenia {total}.")
                        for target in defeated:
                            await self.mob_defeated(target)
                        if any(x.alive for x in alive): await self.ensure_realtime_combat()
                        return

                    if special in ("auto_crossbow","mako_gun","bio_blaster","flash","drill","napalm","noise_blaster","chainsaw","mega_bomb","air_anchor"):
                        base=max(1,int(skill.get("base_power",100) or 100))
                        upgrade_mult=1.30 if upgraded else 1.0
                        if special in ("drill","chainsaw","air_anchor"): upgrade_mult=1.35 if upgraded else 1.0
                        if special=="mako_gun":
                            element="lightning" if upgraded and mob and MOB_TEMPLATES[mob.template_id].get("machine") else random.choice(("fire","ice","lightning","water","holy","dark"))
                        else:
                            element={"bio_blaster":"bio poison","flash":"holy","napalm":"fire","noise_blaster":"sound"}.get(special,"")
                        if special in ("auto_crossbow","bio_blaster","flash","napalm","noise_blaster","mega_bomb"):
                            targets=[x for x in aoe_mobs if x.alive]
                        else:
                            targets=[mob] if mob else []
                        total=0; defeated=[]; seen=set()
                        for i,target in enumerate(targets):
                            template=MOB_TEMPLATES[target.template_id]
                            # Mega Bomb: full damage main target, reduced splash normally.
                            local_mult=passive_mult*upgrade_mult*skill_power*self.skill_buff_multiplier()
                            if special=="mega_bomb" and i>0 and not upgraded: local_mult*=0.55
                            # Chainsaw can use Demi / upgraded Quarter as a floor effect.
                            if special=="chainsaw":
                                remaining_fraction=0.25 if upgraded else 0.50
                                damage=max(int(base*local_mult), int(max(1,target.hp)*(1.0-remaining_fraction)))
                            else:
                                damage=max(1,int(base*local_mult)+random.randint(-3,3))
                            # Drill bypasses boss defense/protect-shell equivalent.
                            if special!="drill": damage=await self.apply_boss_defense(target,damage)
                            damage=self.v0210_adjust_player_damage(damage)
                            # Debilitator vulnerabilities apply to matching elemental tools.
                            if time.time() < float(getattr(target,"v0317_vulnerability_until",0.0) or 0.0) and element in set(getattr(target,"v0317_vulnerabilities",set()) or set()):
                                damage=int(round(damage*1.50))
                            if time.time() < float(getattr(target,"v0317_oiled_until",0.0) or 0.0) and "fire" in element:
                                damage=int(round(damage*1.25))
                            damage,mnote=v0314_adjust_damage_vs_template(template,damage,element or "physical",skill.get("name",""))
                            target.hp-=damage; total+=damage
                            await self.send(f"{skill['name']}: {template['name']} otrzymuje {damage} obrażeń. HP {max(0,target.hp)}.{mnote}")
                            if special=="napalm" and upgraded:
                                duration=45 if self.engineer_skill_known_v0317("v0317_engineer_kinematics") else 30
                                target.v0317_oiled_until=time.time()+duration
                            if special=="bio_blaster":
                                duration=(40 if upgraded else 25) + (15 if self.engineer_skill_known_v0317("v0317_engineer_kinematics") else 0)
                                target.v0319_poison_until=time.time()+duration
                                target.v0319_poison_power=max(1,int(base*(0.12 if upgraded else 0.07)))
                            if special=="flash" and upgraded:
                                target.v0319_blind_until=time.time()+45
                                target.v0319_guard_break_until=time.time()+25
                            if special=="drill" and upgraded:
                                target.v0319_armor_break_until=time.time()+30
                            if special=="noise_blaster" and upgraded:
                                target.v0319_silence_until=time.time()+45
                                target.v0319_slow_until=time.time()+30
                            if special=="chainsaw" and upgraded:
                                target.v0319_hp_leak_until=time.time()+30
                            if special=="air_anchor":
                                target.v0319_air_anchor_until=time.time()+(45 if upgraded else 30)
                                target.v0319_air_anchor_power=max(1,int(base*(0.16 if upgraded else 0.10)))
                            if target.hp<=0 and target.key not in seen:
                                seen.add(target.key); defeated.append(target)
                        await self.grant_skill_use_xp(skill)
                        await self.send(f"{skill['name']}: łączne obrażenia {total}." + (" ULEPSZONE." if upgraded else ""))
                        for target in defeated: await self.mob_defeated(target)
                        if any(x.alive for x in targets if x): await self.ensure_realtime_combat()
                        return


                # v0.31.9: Full authored Mec mechanics from the supplied UOSSMUD ability list.
                if skill.get("mec_authored"):
                    special=str(skill.get("mec_special","")); branch=str(skill.get("mec_branch",""))
                    vmax=self.mec_vmax_active_v0319()
                    if special=="vmax":
                        if vmax:
                            await self.send("V-MAX jest już aktywny."); return
                        if self.mec_overheat_active_v0319():
                            await self.send(f"V-MAX zablokowany przez Overheat jeszcze przez {int(getattr(self,'v0319_overheat_until',0)-time.time()+.999)} s."); return
                        will=max(1,int(self.effective_willpower()))
                        _vd,_vc=self.server.db.vmax_upgrades_v03114(self.account_id)
                        _skill_progress=(max(1,min(SKILL_MAX_LEVEL,skill_level))-1)/float(max(1, SKILL_MAX_LEVEL-1))
                        _skill_duration_mult=1.0 + 0.80*(_skill_progress**0.90)
                        duration=min(180,int(round((25 + will//8 + 10*_vd)*_skill_duration_mult)))  # v0.33.0: Skill Level V-MAX rozwija czas działania.
                        self.v0319_vmax_until=time.time()+duration
                        recipients = self.apply_party_boost_v03511(
                            skill["id"], "V-MAX", 1.30, self.v0319_vmax_until, self.character.name
                        )
                        for session in recipients:
                            session.v03511_party_vmax_until = max(
                                float(getattr(session, "v03511_party_vmax_until", 0.0) or 0.0),
                                self.v0319_vmax_until,
                            )
                        await self.send(
                            f"V-MAX aktywny przez {duration} s dla {len(recipients)} członków drużyny w tej lokacji. "
                            "Wszyscy otrzymują +30 procent do skilli/spelli oraz Protect, Shell i Regen. "
                            "Mec uruchamiający V-MAX zachowuje też swoje specjalne zmiany skilli."
                        )
                        for session in recipients:
                            if session is self:
                                continue
                            await session.send(
                                f"{self.character.name} aktywuje V-MAX. Przez {duration} s otrzymujesz +30 procent do skilli/spelli oraz Protect, Shell i Regen."
                            )
                        await self.grant_skill_use_xp(skill); return

                    if special in ("cure_beam","heal_beam"):
                        # Reuse Soulbound smart healing. Heal Beam's Support Effect becomes party-wide during V-MAX.
                        if special=="heal_beam" and vmax:
                            recipients=self.server.party_sessions(self.account_id,same_room=self.character.room_id) or [self]
                            total=0
                            for sess in recipients:
                                if sess.closed or not sess.character or sess.current_hp<=0: continue
                                amount=max(1,int(sess.max_hp()*(0.45*skill_power)))
                                before=sess.current_hp; sess.current_hp=min(sess.max_hp(),sess.current_hp+amount); total+=sess.current_hp-before
                            await self.send(f"Heal Beam — Support Effect: cała drużyna odzyskuje łącznie {total} HP.")
                            await self.grant_skill_use_xp(skill); return
                        # let generic heal handler below handle single target

                    if special in ("cosmic_rave","shoot_all","starlight_shower","shock_soldier","pop_knight","range_fire","dispose","uzi_punch","laser_spin","area_bomb","maelstrom","shock"):
                        alive=[x for x in aoe_mobs if x.alive]
                        if not alive: return
                        if special=="cosmic_rave" and vmax:
                            targets=random.choices(alive,k=5)
                        elif special=="starlight_shower" and not vmax:
                            targets=[mob] if mob else [alive[0]]
                        elif special=="uzi_punch":
                            targets=random.choices(alive,k=min(5,max(2,len(alive))))
                        else:
                            targets=list(alive)
                        base=max(1,int(skill.get("base_power",100) or 100)); total=0; defeated=[]; seen=set()
                        mult=skill_power*self.mec_branch_multiplier_v0319(branch)*self.skill_buff_multiplier(exclude_skill_id="v0319_mec_vmax")
                        if special=="shoot_all" and vmax: mult*=1.35
                        if special=="starlight_shower" and vmax: mult*=1.25
                        for target in targets:
                            if not target.alive: continue
                            template=MOB_TEMPLATES[target.template_id]
                            damage=max(1,int(base*mult)+random.randint(-6,6))
                            damage,crit=self.roll_critical_hit(damage)
                            if special=="shoot_all" and vmax and random.random()<0.20:
                                damage=int(damage*1.5); crit=True
                            damage=await self.apply_boss_defense(target,damage); damage=self.v0210_adjust_player_damage(damage)
                            element={"laser_spin":"dark","area_bomb":"fire","maelstrom":"water","shock":"lightning","starlight_shower":"magic"}.get(special,"physical")
                            damage,note=v0314_adjust_damage_vs_template(template,damage,element,skill.get("name",""))
                            target.hp-=damage; total+=damage
                            await self.send(f"{skill['name']}: {template['name']} {damage} obrażeń. HP {max(0,target.hp)}.{note}")
                            if target.hp<=0 and target.key not in seen: seen.add(target.key); defeated.append(target)
                        await self.grant_skill_use_xp(skill)
                        await self.send(f"{skill['name']}: łączne obrażenia {total}, pokonani {len(defeated)}.")
                        for target in defeated: await self.mob_defeated(target)
                        if any(x.alive for x in alive): await self.ensure_realtime_combat()
                        return

                    if special in ("hypno_flash","jammer","logic_bomb"):
                        if not mob: return
                        template=MOB_TEMPLATES[mob.template_id]
                        duration=30
                        if special=="hypno_flash": mob.v0319_sleep_until=time.time()+duration
                        elif special=="jammer":
                            duration=45 if template.get("machine") else 25
                            targets=[x for x in aoe_mobs if x.alive] if vmax else [mob]
                            for t in targets: t.v0319_disabled_until=time.time()+duration
                        else:
                            mob.v0319_silence_until=time.time()+duration; mob.v0319_slow_until=time.time()+duration
                            if vmax: mob.v0319_blind_until=time.time()+duration; mob.v0319_disabled_until=time.time()+duration
                        await self.send(f"{skill['name']}: efekt kontroli na {template['name']} przez {duration} s" + (". Support Effect aktywny." if vmax else "."))
                        await self.grant_skill_use_xp(skill); return

                    if special=="satellite_linker" and mob:
                        mob.v0319_satellite_until=time.time()+45; mob.v0319_satellite_power=max(1,int(skill.get("base_power",1000)*self.mec_branch_multiplier_v0319(branch)))
                    if special=="tiger_rampage" and mob: mob.v0319_armor_break_until=time.time()+30
                    if special=="mec_sonata" and mob and random.random()<0.40: mob.v0319_level_down_until=time.time()+30
                    if special=="magnify" and random.random()<0.25: self.v0319_lock_until=time.time()+12
                    # Other single-target Mec attacks continue through the normal Soulbound damage handler below.

                # v0.31.5: V-MAX is a dedicated Mec state used by Cosmic Rave.
                if skill.get("id") == "v0315_mec_vmax":
                    duration = int(skill.get("duration", 30) or 30)
                    recipients = self.apply_party_boost_v03511(
                        skill["id"], "V-MAX", float(skill.get("boost", 1.0) or 1.0),
                        now + duration, self.character.name
                    )
                    for session in recipients:
                        session.v03511_party_vmax_until = max(
                            float(getattr(session, "v03511_party_vmax_until", 0.0) or 0.0), now + duration
                        )
                    await self.send(f"V-MAX aktywny drużynowo przez {duration} sekund. Cosmic Rave Meca wykona teraz 5 losowych trafień.")
                    await self.grant_skill_use_xp(skill)
                    return

                if skill.get("id") == "v0315_mec_cosmic_rave":
                    # Use the room-wide target list already prepared for AoE.
                    alive = [target for target in aoe_mobs if target.alive]
                    if not alive:
                        await self.send("Nie ma tutaj żywych przeciwników dla Cosmic Rave.")
                        return
                    vmax = self.skill_buff_active("v0315_mec_vmax")
                    targets = random.choices(alive, k=5) if vmax else list(alive)
                    base_power = int(skill.get("base_power", 2000) or 2000)
                    multiplier = skill_power
                    multiplier *= self.character.class_physical_damage_multiplier()
                    multiplier *= self.character.racial_all_damage_multiplier()
                    multiplier *= self.total_set_damage_multiplier()
                    multiplier *= self.equipment_damage_multiplier("physical")
                    multiplier *= self.skill_buff_multiplier(exclude_skill_id="v0315_mec_vmax")
                    defeated_keys = set()
                    defeated = []
                    total_damage = 0
                    await self.send(
                        f"Cosmic Rave. Moc bazowa {base_power}. " +
                        ("V-MAX: 5 losowych trafień." if vmax else f"Cele: wszyscy przeciwnicy ({len(alive)}).")
                    )
                    for target in targets:
                        if not target.alive:
                            continue
                        template = MOB_TEMPLATES[target.template_id]
                        damage = max(1, int(base_power * multiplier) + random.randint(-10, 10))
                        damage, critical = self.roll_critical_hit(damage)
                        damage = await self.apply_boss_defense(target, damage)
                        damage = self.v0210_adjust_player_damage(damage)
                        damage, _ = v0314_adjust_damage_vs_template(template, damage, "physical", "Cosmic Rave")
                        target.hp -= damage
                        total_damage += damage
                        await self.send(f"{template['name']}: Cosmic Rave {damage} obrażeń. HP {max(0,target.hp)} z {template['max_hp']}.")
                        if target.hp <= 0 and target.key not in defeated_keys:
                            defeated_keys.add(target.key); defeated.append(target)
                    await self.grant_skill_use_xp(skill)
                    await self.send(f"Cosmic Rave: łączne obrażenia {total_damage}, pokonani {len(defeated)}.")
                    for target in defeated:
                        owner_name = aoe_reward_owner.get(target.key)
                        reward_session = self.server.find_character_session(owner_name) if owner_name and owner_name != self.character.name else self
                        if reward_session is None or reward_session.closed or not reward_session.character or reward_session.character.room_id != self.character.room_id:
                            reward_session = self
                        await reward_session.mob_defeated(target)
                    survivors = [x for x in alive if x.alive and self.server.engagement_allowed(self, x)]
                    if survivors:
                        self.combat_mob_key = survivors[0].key
                        await self.ensure_realtime_combat()
                    return

                if kind == "boost":
                    base_boost = float(skill.get("boost", 1.0) or 1.0)
                    # v0.8.64: Skill Level rozwija buff wolniej niż bezpośredni damage.
                    base_bonus = max(0.0, base_boost - 1.0)
                    scaled_bonus = base_bonus * (1.0 + max(0.0, skill_power - 1.0) * 0.50)
                    scaled_boost = 1.0 + min(0.90, scaled_bonus)
                    duration = GLOBAL_SKILL_BUFF_DURATION_SECONDS
                    recipients = self.apply_party_boost_v03511(
                        skill["id"], skill["name"], max(1.0, scaled_boost),
                        now + duration, self.character.name
                    )
                    bonus_pct = int(round((max(1.0, scaled_boost) - 1.0) * 100))
                    total_pct = int(round((self.skill_buff_multiplier() - 1.0) * 100))
                    await self.send(
                        f"Buff drużynowy aktywowany: {skill['name']}. "
                        f"Czas działania: {duration} sekund. "
                        f"Wzmocnienie: {bonus_pct} procent. "
                        f"Objęci członkowie: {sum(1 for x in recipients if not x.closed and x.character and x.current_hp > 0)}. "
                        f"Łączne aktywne wzmocnienie: {total_pct} procent."
                    )
                    for session in recipients:
                        if session is self or session.closed or not session.character or session.current_hp <= 0:
                            continue
                        await session.send(
                            f"{self.character.name} aktywuje buff {skill['name']}. "
                            f"Działa na ciebie przez {duration} sekund. "
                            f"Wzmocnienie: {bonus_pct} procent."
                        )
                    await self.grant_skill_use_xp(skill)
                    if self.combat_mob_key:
                        await self.ensure_realtime_combat()
                    return

                if kind == "guard":
                    buff_mult = self.skill_buff_multiplier()
                    scaled_guard = max(
                        1,
                        int(round(skill.get("guard", 0) * skill_power * buff_mult)),
                    )
                    recipients = self.local_party_buff_recipients_v03511()
                    for session in recipients:
                        session.skill_guard = max(session.skill_guard, scaled_guard)
                    await self.send(
                        f"Drużynowy guard {skill['name']} na Skill Level {skill_level}. "
                        f"{len(recipients)} członków w tej lokacji: następne trafienie każdego zostanie dodatkowo zredukowane o {scaled_guard}."
                    )
                    for session in recipients:
                        if session is not self:
                            await session.send(
                                f"{self.character.name} używa {skill['name']}. Twój następny otrzymany cios zostanie dodatkowo zredukowany o {scaled_guard}."
                            )
                    await self.grant_skill_use_xp(skill)
                    if mana_cost:
                        await self.send(f"Mana: {self.current_mana} z {self.max_mana()}.")
                    if self.combat_mob_key:
                        await self.ensure_realtime_combat()
                    return

                if kind == "evade":
                    recipients = self.local_party_buff_recipients_v03511()
                    for session in recipients:
                        session.skill_evade = True
                    await self.send(
                        f"Drużynowy unik {skill['name']} na Skill Level {skill_level}. "
                        f"{len(recipients)} członków w tej lokacji uniknie swojego następnego ataku przeciwnika."
                    )
                    for session in recipients:
                        if session is not self:
                            await session.send(
                                f"{self.character.name} używa {skill['name']}. Twój następny atak przeciwnika zostanie automatycznie uniknięty."
                            )
                    await self.grant_skill_use_xp(skill)
                    if self.combat_mob_key:
                        await self.ensure_realtime_combat()
                    return

                if kind == "group_heal":
                    recipients = self.server.party_sessions(self.account_id, same_room=self.character.room_id)
                    if not recipients:
                        recipients = [self]
                    heal_pct = min(0.45, skill.get("heal_pct", 0.20) * skill_power * self.character.racial_healing_multiplier() * self.character.class_healing_multiplier())
                    heal_pct = min(0.60, heal_pct * self.skill_buff_multiplier())
                    total_healed = 0
                    for session in sorted(recipients, key=lambda target: target.character.name.lower()):
                        target_max = session.max_hp()
                        amount = max(1, int(target_max * heal_pct))
                        before = session.current_hp
                        session.current_hp = min(target_max, session.current_hp + amount)
                        actual = session.current_hp - before
                        total_healed += actual
                        if session is self:
                            await self.send(f"{skill['name']}: odzyskujesz {actual} HP. Masz {session.current_hp} z {target_max} HP.")
                        else:
                            await session.send(f"{self.character.name} używa {skill['name']}. Odzyskujesz {actual} HP. Masz {session.current_hp} z {target_max} HP.")
                    _group_heal_msg = (
                        f"{self.character.name}: {skill['name']} leczy drużynę. "
                        f"Cele {len(recipients)}, przywrócono łącznie {total_healed} HP."
                    )
                    await self.send(f"Leczenie obszarowe obejmuje {len(recipients)} członków drużyny w tej lokacji. Wyleczono łącznie {total_healed} HP.")
                    await self.server.party_combat_broadcast(self, _group_heal_msg)
                    await self.grant_skill_use_xp(skill)
                    if mana_cost:
                        await self.send(f"Mana: {self.current_mana} z {self.max_mana()}.")
                    if self.combat_mob_key:
                        await self.ensure_realtime_combat()
                    return

                if kind == "heal":
                    # v0.31.6: zwykły heal pozostaje single-target, ale automatycznie
                    # wybiera najbardziej rannego żywego członka party w tej samej
                    # lokacji. Solo wybiera gracza. Skill nie marnuje się, gdy nikt
                    # nie potrzebuje leczenia. group_heal nadal leczy całą drużynę.
                    recipients = self.server.party_sessions(
                        self.account_id, same_room=self.character.room_id
                    ) or [self]
                    injured = [
                        session for session in recipients
                        if not session.closed and session.character and session.current_hp > 0
                        and session.current_hp < session.max_hp()
                    ]
                    if not injured:
                        await self.send(
                            f"{skill['name']}: nikt w drużynie w tej lokacji nie potrzebuje leczenia."
                        )
                        return
                    target = min(
                        injured,
                        key=lambda session: (
                            session.current_hp / max(1, session.max_hp()),
                            session.current_hp,
                            session.character.name.lower(),
                        ),
                    )
                    heal_pct = min(
                        0.65,
                        skill.get("heal_pct", 0.25)
                        * skill_power
                        * self.character.racial_healing_multiplier()
                        * self.character.class_healing_multiplier()
                    )
                    heal_pct = min(0.80, heal_pct * self.skill_buff_multiplier())
                    target_max = target.max_hp()
                    heal = max(1, int(target_max * heal_pct))
                    before = target.current_hp
                    target.current_hp = min(target_max, target.current_hp + heal)
                    actual = target.current_hp - before
                    if target is self:
                        await self.send(
                            f"Używasz {skill['name']} na Skill Level {skill_level}. "
                            f"Odzyskujesz {actual} HP. Masz teraz {target.current_hp} z {target_max} HP."
                        )
                    else:
                        await target.send(
                            f"{self.character.name} używa {skill['name']} na tobie. "
                            f"Odzyskujesz {actual} HP. Masz {target.current_hp} z {target_max} HP."
                        )
                        await self.send(
                            f"Używasz {skill['name']} na {target.character.name}. "
                            f"Przywrócono {actual} HP."
                        )
                    await self.server.party_nearby_broadcast(
                        self,
                        f"{self.character.name}: {skill['name']} leczy {target.character.name} za {actual} HP.",
                        exclude=[self, target],
                        detail="normal",
                        history_category="combat",
                    )
                    if self.character.racial_healing_bonus_percent() > 0:
                        await self.send(
                            f"Bonus rasy {self.character.race}: "
                            f"+{self.character.racial_healing_bonus_percent()} procent mocy leczenia."
                        )
                    class_heal_bonus = int(
                        round((self.character.class_healing_multiplier() - 1.0) * 100)
                    )
                    if class_heal_bonus > 0:
                        await self.send(
                            f"Bonus aktywnych klas: +{class_heal_bonus} procent "
                            "mocy leczenia."
                        )
                    await self.grant_skill_use_xp(skill)
                    if mana_cost:
                        await self.send(f"Mana: {self.current_mana} z {self.max_mana()}.")
                    if self.combat_mob_key:
                        await self.ensure_realtime_combat()
                    return

                if kind == "aoe_damage":
                    scale = self.skill_scale_value(skill.get("scale", "intelligence"))
                    multiplier = skill.get("mult", 1.0) * skill_power
                    multiplier *= self.character.class_magic_damage_multiplier()
                    multiplier *= self.character.racial_magic_damage_multiplier()
                    multiplier *= self.character.racial_all_damage_multiplier()
                    multiplier *= self.total_set_damage_multiplier()
                    multiplier *= self.equipment_damage_multiplier("magic")
                    multiplier *= self.skill_buff_multiplier()
                    await self.send(
                        f"Używasz {skill['name']} na Skill Level {skill_level}. "
                        f"Cele w lokacji: {len(aoe_mobs)}."
                    )
                    defeated, survivors = [], []
                    total_damage = 0
                    critical_hits = 0
                    for target in list(aoe_mobs):
                        if not target.alive:
                            continue
                        template = MOB_TEMPLATES[target.template_id]
                        damage = max(1, int((self.character.soul_power() + scale) * multiplier) + random.randint(-2, 3))
                        damage, critical = self.roll_critical_hit(damage)
                        if critical:
                            self.record_social_record_v03051("biggest_crit", damage)
                            critical_hits += 1
                        damage = await self.apply_boss_defense(target, damage)
                        damage = self.v0210_adjust_player_damage(damage)
                        damage, machine_note = v0314_adjust_damage_vs_template(
                            template, damage, "magic", skill.get("name", "")
                        )
                        target.hp -= damage
                        total_damage += damage
                        marker = " Krytyk." if critical else ""
                        await self.send(f"{template['name']}: {damage} obrażeń.{marker} HP {max(0, target.hp)} z {template['max_hp']}.")
                        (defeated if target.hp <= 0 else survivors).append(target)
                    await self.grant_skill_use_xp(skill)
                    if mana_cost:
                        await self.send(f"Mana: {self.current_mana} z {self.max_mana()}.")
                    await self.send(f"{skill['name']}: łączne obrażenia {total_damage}, pokonani przeciwnicy {len(defeated)}.")
                    _party_aoe = (
                        f"{self.character.name}: {skill['name']}, {total_damage} obrażeń łącznie, "
                        f"cele {len(aoe_mobs)}, pokonani {len(defeated)}"
                    )
                    if critical_hits:
                        _party_aoe += f", krytyki {critical_hits}"
                    await self.server.party_combat_broadcast(self, _party_aoe + ".")
                    for target in defeated:
                        owner_name = aoe_reward_owner.get(target.key)
                        reward_session = (
                            self.server.find_character_session(owner_name)
                            if owner_name and owner_name != self.character.name
                            else self
                        )
                        if (
                            reward_session is None
                            or reward_session.closed
                            or not reward_session.character
                            or reward_session.character.room_id != self.character.room_id
                        ):
                            reward_session = self
                        await reward_session.mob_defeated(target)
                    counter = next(
                        (target for target in survivors
                         if target.alive and self.server.engagement_allowed(self, target)),
                        None,
                    )
                    if counter:
                        self.combat_mob_key = counter.key
                        await self.ensure_realtime_combat()
                    elif self.combat_mob_key and not self.server.engagement_allowed(
                        self, self.server.world.mobs.get(self.combat_mob_key)
                    ):
                        self.combat_mob_key = None
                    return

                template = MOB_TEMPLATES[mob.template_id]
                scale = self.skill_scale_value(skill.get("scale", "strength"))
                multiplier = skill.get("mult", 1.0) * skill_power
                skill_class = self.skill_class_name(skill)
                skill_class_type = class_type_for_name(skill_class)
                if skill_class_type == "physical":
                    multiplier *= self.character.class_physical_damage_multiplier()
                    multiplier *= self.character.racial_physical_damage_multiplier()
                else:
                    multiplier *= self.character.class_magic_damage_multiplier()
                    multiplier *= self.character.racial_magic_damage_multiplier()
                multiplier *= self.character.racial_all_damage_multiplier()
                multiplier *= self.total_set_damage_multiplier()
                multiplier *= self.equipment_damage_multiplier(
                    "physical" if skill_class_type == "physical" else "magic"
                )
                multiplier *= self.skill_buff_multiplier()

                if kind == "execute":
                    hp_ratio = mob.hp / max(1, template["max_hp"])
                    execute_threshold = v0863_execute_threshold(template)
                    if hp_ratio <= execute_threshold:
                        multiplier *= min(2.0, float(skill.get("execute_mult", 1.5)))
                        await self.send(
                            f"Egzekucyjny próg aktywny: przeciwnik ma nie więcej niż "
                            f"{int(round(execute_threshold * 100))} procent HP."
                        )

                damage = max(
                    1,
                    int(
                        (self.character.soul_power() + scale) * multiplier
                    ) + random.randint(-2, 3),
                )
                damage, critical = self.roll_critical_hit(damage)
                if critical:
                    self.record_social_record_v03051("biggest_crit", damage)
                    await self.send(
                        f"TRAFIENIE KRYTYCZNE umiejętnością "
                        f"{skill['name']}! Zręczność "
                        f"{self.effective_dexterity()}. "
                        f"Szansa: "
                        f"{int(round(self.critical_chance() * 100))} procent."
                    )
                damage = await self.apply_boss_defense(mob, damage)
                damage = self.v0210_adjust_player_damage(damage)
                damage, machine_note = v0314_adjust_damage_vs_template(
                    template, damage,
                    "physical" if skill_class_type == "physical" else "magic",
                    skill.get("name", ""),
                )
                mob.hp -= damage
                # v0.34.6: cechy Broni Duszy nie modyfikują skilli/spelli.
                # Lifesteal/Mana/execute/boss bonus z Soul Weapon Traits działa wyłącznie
                # w realtime_player_action(), czyli na zwykłym ataku Broni Duszy.
                self._recap52_dealt=int(getattr(self,"_recap52_dealt",0))+max(0,int(damage))
                await self.send(
                    f"Używasz {skill['name']} na {template['name']}. "
                    f"Zadajesz {damage} obrażeń. Przeciwnik: {max(0, mob.hp)} z {template['max_hp']} HP."
                    + machine_note
                )
                _party_skill = (
                    f"{self.character.name}: {skill['name']}, {damage} obrażeń w {template['name']}"
                )
                if critical:
                    _party_skill += ". Krytyk"
                if mob.hp <= 0:
                    _party_skill += ". Pokonany"
                await self.server.party_combat_broadcast(self, _party_skill + ".")

                if kind == "drain":
                    if template.get("machine"):
                        requested_heal = 0
                        await self.send("Machine nie posiada energii życiowej do wyssania.")
                    else:
                        requested_heal = max(
                            1,
                            int(damage * skill.get("drain_pct", 0.4) * self.character.class_drain_healing_multiplier())
                        )
                    # Drain nadal skaluje się z obrażeniami, ale pojedynczy cast nie
                    # może przywrócić więcej niż 25% maksymalnego HP.
                    drain_cap = max(1, int(round(self.max_hp() * 0.25)))
                    heal = min(requested_heal, drain_cap)
                    before = self.current_hp
                    self.current_hp = min(self.max_hp(), self.current_hp + heal)
                    actual = self.current_hp - before
                    await self.send(
                        f"Wysysanie przywraca {actual} HP. Masz {self.current_hp} z {self.max_hp()} HP."
                    )

                self_damage = skill.get("self_damage", 0)
                if skill.get("self_damage_pct"):
                    self_damage += max(1, int(self.max_hp() * skill["self_damage_pct"]))
                if self_damage:
                    self.current_hp -= self_damage
                    if skill.get("mec_branch")=="feedback" and self.mec_skill_known_v0319("v0319_mec_self_repair"):
                        _sr_level=int(self.server.db.skill_progress(self.account_id,"v0319_mec_self_repair")["level"]); _sr_p=(max(1,min(SKILL_MAX_LEVEL,_sr_level))-1)/float(max(1, SKILL_MAX_LEVEL-1))
                        self.v0319_feedback_repair_pool=int(getattr(self,"v0319_feedback_repair_pool",0) or 0)+max(1,int(self_damage*(0.35+0.45*_sr_p)))
                        self.v0319_feedback_repair_at=time.time()+8.0
                    await self.send(
                        f"Koszt umiejętności: tracisz {self_damage} HP. "
                        f"Masz {max(0, self.current_hp)} z {self.max_hp()} HP."
                    )
                    if self.current_hp <= 0:
                        await self.die("własna umiejętność")
                        return

                await self.grant_skill_use_xp(skill)

                if mana_cost:
                    await self.send(f"Mana: {self.current_mana} z {self.max_mana()}.")

                if mob.hp <= 0:
                    await self.mob_defeated(mob)
                    return

                await self.ensure_realtime_combat()

