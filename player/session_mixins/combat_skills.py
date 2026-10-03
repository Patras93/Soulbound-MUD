# -*- coding: utf-8 -*-
"""Class-skill execution for Soulbound combat.

v0.47.0: explicit combat architecture; no compatibility-global injection.
"""
import random
import time

from core.classes_skills import CLASS_SKILLS, effective_skill_mana_cost
from core.progression_600 import SKILL_MAX_LEVEL
from core.progression_resources import class_type_for_name, skill_power_multiplier
from core.bootstrap_economy_professions import GLOBAL_SKILL_BUFF_DURATION_SECONDS
from data.mobs import MOB_TEMPLATES
from data.rooms import ROOMS
from network.protocol_gameplay_utils import normalize_lookup_text
from world.machine_expansion import v0314_adjust_damage_vs_template
from world.economy_quests import v0863_execute_threshold
from world.uoss_superboss_runtime import superboss_attack_gate_v11137

class SessionCombatSkillsMixin:
    def offensive_aoe_enabled_v11120(self):
        row = self.server.db.conn.execute(
            "SELECT offensive_aoe_enabled FROM player_combat_settings_v11120 WHERE account_id=?",
            (self.account_id,),
        ).fetchone()
        return True if row is None else bool(row["offensive_aoe_enabled"])

    async def handle_aoe_setting_v11120(self, args=""):
        raw = normalize_lookup_text(str(args or "").strip())
        if raw in ("on", "wlacz", "włącz"):
            enabled = True
        elif raw in ("off", "wylacz", "wyłącz"):
            enabled = False
        elif raw in ("", "status"):
            state = "włączone" if self.offensive_aoe_enabled_v11120() else "wyłączone"
            await self.send(f"Ofensywne AoE: {state}. Użyj: aoe on albo aoe off.")
            return
        else:
            await self.send("Użycie: aoe on, aoe off albo aoe.")
            return
        self.server.db.conn.execute(
            "INSERT INTO player_combat_settings_v11120(account_id,offensive_aoe_enabled) VALUES(?,?) "
            "ON CONFLICT(account_id) DO UPDATE SET offensive_aoe_enabled=excluded.offensive_aoe_enabled",
            (self.account_id, 1 if enabled else 0),
        )
        self.server.db.conn.commit()
        await self.send(
            "Ofensywne AoE włączone: umiejętności obszarowe atakują wszystkie cele w lokacji."
            if enabled else
            "Ofensywne AoE wyłączone: umiejętności obszarowe atakują tylko jeden cel."
        )

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
                # v1.11.40: all ordinary class skills are cooldown-free.
                # Only an explicitly marked mechanic cooldown may block reuse.
                mechanic_lock = bool(skill.get("mechanic_cooldown"))
                effective_cooldown = self.effective_skill_cooldown(skill, skill_level) if mechanic_lock else 0

                now = time.time()
                await self.mec_refresh_vmax_v0319()
                ready_at = self.skill_cooldown_ready_at_v0364(skill) if mechanic_lock else 0.0
                if ready_at > now:
                    await self.send(
                        f"{skill['name']} jest na cooldownie jeszcze {int(ready_at - now + 0.999)} sekund."
                    )
                    return
                mana_cost = effective_skill_mana_cost(skill, skill_class)
                if mana_cost > self.current_mana:
                    await self.send(
                        f"Za mało Many. {skill['name']} wymaga {mana_cost}, a masz {self.current_mana}."
                    )
                    return

                kind = skill["kind"]
                if kind == "passive":
                    await self.send(f"{skill['name']} jest umiejętnością pasywną i działa automatycznie, gdy jest nauczona.")
                    return
                if kind == "boost" and not skill.get("active_special") and str(skill.get("mec_special", "")) != "vmax":
                    await self.send(
                        f"{skill['name']} jest teraz pasywnym wzmocnieniem Automatic. "
                        "Działa stale po nauczeniu i nie wymaga aktywacji."
                    )
                    return
                if kind == "evade" and self.skill_evade:
                    await self.send("Masz już aktywny gwarantowany unik.")
                    return
                offensive = kind in ("damage", "drain", "execute", "aoe_damage")
                mob = None
                aoe_mobs = []
                if kind == "group_heal":
                    recipients=self.server.party_sessions(
                        self.account_id,same_room=self.character.room_id
                    ) or [self]
                    recipients=[
                        session for session in recipients
                        if not session.closed and session.character and session.current_hp>0
                    ]
                    if not recipients:
                        await self.send(f"{skill['name']}: brak żywych sojuszników w tej lokacji.")
                        return
                    # Healing Wind source gives Will + Skill Level influence but no
                    # numeric heal amount. Reuse Soulbound's canonical healing power
                    # calculation instead of adding a new fixed percentage.
                    healed=[]
                    for target in recipients:
                        target_max=target.max_hp()
                        before=target.current_hp
                        if before>=target_max:
                            continue
                        base=max(1,int(self.effective_willpower()))
                        heal=max(1,int(round(base*skill_power)))
                        target.current_hp=min(target_max,before+heal)
                        actual=target.current_hp-before
                        if actual:
                            healed.append((target,actual))
                            if target is not self:
                                await target.send(f"{self.character.name} używa {skill['name']}. Odzyskujesz {actual} HP.")
                    await self.grant_skill_use_xp(skill)
                    total=sum(amount for _target,amount in healed)
                    await self.send(f"{skill['name']}: uleczono {len(healed)} członków drużyny w tej lokacji, łącznie {total} HP.")
                    if mana_cost:
                        await self.send(f"Mana: {self.current_mana} z {self.max_mana()}.")
                    if self.combat_mob_key:
                        await self.ensure_realtime_combat()
                    return

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
                    _allowed_aoe = []
                    for candidate in aoe_mobs:
                        _ok, _reason = superboss_attack_gate_v11137(self, MOB_TEMPLATES[candidate.template_id])
                        if _ok:
                            _allowed_aoe.append(candidate)
                    aoe_mobs = _allowed_aoe
                    if not aoe_mobs:
                        await self.send("Nie ma tutaj żywych przeciwników dla czaru obszarowego.")
                        return
                    if not self.offensive_aoe_enabled_v11120():
                        selected = next(
                            (candidate for candidate in aoe_mobs if candidate.key == self.combat_mob_key),
                            None,
                        )
                        if selected is None and target_text:
                            wanted = normalize_lookup_text(target_text)
                            selected = next(
                                (
                                    candidate for candidate in aoe_mobs
                                    if wanted in normalize_lookup_text(MOB_TEMPLATES[candidate.template_id]["name"])
                                ),
                                None,
                            )
                        aoe_mobs = [selected or aoe_mobs[0]]
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
                        # Każdy mob, który po AoE należy do naszego aggro, ma
                        # kontratakować niezależnie od głównego combat_mob_key.
                        if candidate.engaged_by == self.character.name:
                            candidate.aoe_engaged_by = self.character.name
                    # Realtime target ustawiamy tylko na moba, którego wolno nam normalnie
                    # zaatakować. Samo AoE nadal obejmuje cały pokój.
                    mob = next(
                        (candidate for candidate in available_for_aggro if candidate.key == self.combat_mob_key),
                        available_for_aggro[0] if available_for_aggro else None,
                    )
                    if mob is not None:
                        self.combat_mob_key = mob.key
                        # v1.11.13: KAŻDE AoE rozpoczyna wspólną walkę całej lokalnej
                        # drużyny od razu, zanim dedykowane ścieżki Meca/Engineera
                        # zdążą zakończyć handler przez return. Nie ma znaczenia,
                        # czy AoE uruchomił lider czy zwykły członek party.
                        await self.server.auto_assist_party_combat(self, mob)
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
                    _uoss_ok, _uoss_reason = superboss_attack_gate_v11137(self, MOB_TEMPLATES[mob.template_id])
                    if not _uoss_ok:
                        await self.send(_uoss_reason)
                        return

                self.current_mana -= mana_cost
                if effective_cooldown > 0:
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
                    support_effect=self.mec_support_effect_v11149()
                    if special=="vmax":
                        if vmax:
                            await self.send("V-MAX jest już aktywny."); return
                        if self.mec_overheat_active_v0319():
                            await self.send("V-MAX zablokowany przez Overheat do zakończenia akcji regeneracyjnej."); return
                        will=max(1,int(self.effective_willpower()))
                        _vd,_vc=self.server.db.vmax_upgrades_v03114(self.account_id)
                        _skill_progress=(max(1,min(SKILL_MAX_LEVEL,skill_level))-1)/float(max(1, SKILL_MAX_LEVEL-1))
                        _skill_duration_mult=1.0 + 0.80*(_skill_progress**0.90)
                        duration=min(180,int(round((25 + will//8 + 10*_vd)*_skill_duration_mult)))  # v0.33.0: Skill Level V-MAX rozwija czas działania.
                        self.v0319_vmax_until=time.time()+duration
                        self.v0319_vmax_support_maintained=bool(support_effect)
                        # V-MAX grants its named beneficial package to the Mec only.
                        # Keep each status explicit so Permanence protects the whole
                        # beneficial set from hostile dispels. No unsourced numeric
                        # Protect/Shell/Regen/Praise/Preach values are fabricated.
                        _vmax_statuses=("protect","shell","haste","regen","preach","praise","permanence")
                        for _status in _vmax_statuses:
                            self.active_skill_buffs["v0319_vmax_"+_status]={
                                "name":_status.capitalize(),"boost":1.0,
                                "until":self.v0319_vmax_until,"source":"V-MAX",
                                "beneficial":True,"canonical_status":_status,
                            }
                        self.active_skill_buffs[skill["id"]]={
                            "name":"V-MAX","boost":1.0,"until":self.v0319_vmax_until,
                            "source":self.character.name,
                        }
                        # Source Haste negates Slow when the target is slowed.
                        if hasattr(self,"v0319_slow_until"):
                            self.v0319_slow_until=0.0
                        await self.send(
                            f"V-MAX aktywny przez {duration} s. Protect, Shell, Haste, Regen, "
                            "Preach, Praise i Permanence działają na Meca; Haste neguje Slow, "
                            "a Permanence chroni korzystne efekty przed wrogim dispellem."
                        )
                        await self.grant_skill_use_xp(skill); return

                    if special in ("cure_beam","heal_beam"):
                        # v1.11.45: Cure Beam is a Will-influenced single-target heal.
                        # Soulbound's Support Effect replaces the old separate support weapon:
                        # it heals slightly more and cleanses Blind + Poison.
                        if special=="cure_beam":
                            recipients=self.server.party_sessions(self.account_id,same_room=self.character.room_id) or [self]
                            injured=[s for s in recipients if not s.closed and s.character and s.current_hp>0 and s.current_hp<s.max_hp()]
                            target=min(injured,key=lambda s:(s.current_hp/max(1,s.max_hp()),s.current_hp,s.character.name.lower())) if injured else self
                            _p=(max(1,min(SKILL_MAX_LEVEL,skill_level))-1)/float(max(1,SKILL_MAX_LEVEL-1))
                            _will=max(1,int(self.effective_willpower()))
                            heal_pct=min(0.55,0.14 + min(0.18,_will*0.0015) + 0.16*_p)
                            if support_effect: heal_pct*=float(skill.get("support_heal_multiplier",1.20) or 1.20)
                            amount=max(1,int(target.max_hp()*min(0.65,heal_pct)))
                            before=target.current_hp; target.current_hp=min(target.max_hp(),target.current_hp+amount); actual=target.current_hp-before
                            cleansed=[]
                            if support_effect:
                                for attr,label in (("v0319_blind_until","Blind"),("v0319_poison_until","Poison"),("poison_until","Poison")):
                                    if float(getattr(target,attr,0.0) or 0.0)>time.time():
                                        setattr(target,attr,0.0)
                                        if label not in cleansed: cleansed.append(label)
                            await self.send(
                                f"Cure Beam: {target.character.name} odzyskuje {actual} HP."
                                + (f" Support Effect usuwa: {', '.join(cleansed)}." if cleansed else (" Support Effect zwiększa leczenie." if support_effect else ""))
                            )
                            if target is not self:
                                await target.send(f"{self.character.name} używa Cure Beam. Odzyskujesz {actual} HP." + (f" Usunięto: {', '.join(cleansed)}." if cleansed else ""))
                            await self.grant_skill_use_xp(skill); return
                        # v1.11.46: Heal Beam scales with Will + Skill Level.
                        # With Soulbound's Support Effect it heals the whole local party
                        # and receives the enhanced-healing bonus from the source ability.
                        if special=="heal_beam":
                            _p=(max(1,min(SKILL_MAX_LEVEL,skill_level))-1)/float(max(1,SKILL_MAX_LEVEL-1))
                            _will=max(1,int(self.effective_willpower()))
                            heal_pct=min(0.72,0.30 + min(0.22,_will*0.0018) + 0.20*_p)
                            if support_effect:
                                heal_pct=min(0.80,heal_pct*float(skill.get("support_heal_multiplier",1.20) or 1.20))
                                recipients=self.server.party_sessions(self.account_id,same_room=self.character.room_id) or [self]
                            else:
                                party=self.server.party_sessions(self.account_id,same_room=self.character.room_id) or [self]
                                injured=[s for s in party if not s.closed and s.character and s.current_hp>0 and s.current_hp<s.max_hp()]
                                recipients=[min(injured,key=lambda s:(s.current_hp/max(1,s.max_hp()),s.current_hp,s.character.name.lower()))] if injured else [self]
                            total=0
                            for sess in recipients:
                                if sess.closed or not sess.character or sess.current_hp<=0: continue
                                amount=max(1,int(sess.max_hp()*heal_pct))
                                before=sess.current_hp; sess.current_hp=min(sess.max_hp(),sess.current_hp+amount); actual=sess.current_hp-before; total+=actual
                                if sess is not self:
                                    await sess.send(f"{self.character.name} używa Heal Beam. Odzyskujesz {actual} HP.")
                            if support_effect:
                                await self.send(f"Heal Beam — Support Effect: wzmocnione leczenie całej drużyny, {len(recipients)} celów, łącznie {total} HP.")
                            else:
                                await self.send(f"Heal Beam: {recipients[0].character.name} odzyskuje {total} HP.")
                            await self.grant_skill_use_xp(skill); return

                    if special in ("cosmic_rave","shoot_all","starlight_shower","shock_soldier","pop_knight","range_fire","dispose","uzi_punch","laser_spin","area_bomb","maelstrom","shock"):
                        alive=[x for x in aoe_mobs if x.alive]
                        # v1.11.48: Area Bomb affects only enemies already engaged
                        # in the current combat, matching "All Targetted Enemies".
                        if special=="area_bomb":
                            _engaged_keys=set()
                            if self.combat_mob_key: _engaged_keys.add(self.combat_mob_key)
                            for _sess in (self.server.party_sessions(self.account_id,same_room=self.character.room_id) or [self]):
                                if getattr(_sess,"combat_mob_key",None): _engaged_keys.add(_sess.combat_mob_key)
                            alive=[x for x in alive if x.key in _engaged_keys]
                        if not alive: return
                        if special=="cosmic_rave" and vmax:
                            # Canonical help specifies Random Enemies but no fixed hit count.
                            # One random target is selected per enemy that the normal room-wide
                            # version could have affected, allowing repeats without inventing k=5.
                            targets=random.choices(alive,k=max(1,len(alive)))
                        elif special=="starlight_shower" and not vmax:
                            _engaged=set()
                            if self.combat_mob_key: _engaged.add(self.combat_mob_key)
                            for _sess in (self.server.party_sessions(self.account_id,same_room=self.character.room_id) or [self]):
                                if getattr(_sess,"combat_mob_key",None): _engaged.add(_sess.combat_mob_key)
                            _engaged_alive=[x for x in alive if x.key in _engaged]
                            targets=([mob] if len(_engaged_alive)<=1 and mob else (_engaged_alive or ([mob] if mob else [alive[0]])))
                        elif special=="uzi_punch":
                            targets=random.choices(alive,k=min(5,max(2,len(alive))))
                        else:
                            targets=list(alive)
                        base=max(1,int(skill.get("base_power",100) or 100)); total=0; defeated=[]; seen=set()
                        mult=skill_power*self.mec_branch_multiplier_v0319(branch)*self.skill_buff_multiplier(exclude_skill_id="v0319_mec_vmax")
                        if special=="area_bomb":
                            # Magic Attack influence in Soulbound is Intelligence.
                            mult*=max(0.75,min(3.0,self.effective_intelligence()/100.0))
                        # Cosmic Rave has a lesser Agility influence and V-MAX
                        # strengthens Starlight Shower, but source help supplies no
                        # numeric multiplier for either relation.
                        for target in targets:
                            if not target.alive: continue
                            template=MOB_TEMPLATES[target.template_id]
                            _local_mult=mult
                            if special in ("starlight_shower","shock_soldier","laser_spin","maelstrom","cosmic_rave") and len(targets)>1 and not ((special=="starlight_shower" or special=="cosmic_rave") and vmax):
                                # Canonical diminishing AoE: power falls as more enemies are hit.
                                _local_mult*=max(0.45,1.0-0.12*(len(targets)-1))
                            damage=max(1,int(base*_local_mult)+random.randint(-6,6))
                            # v1.11.47: Pop Knight keeps full AoE damage and receives
                            # the source ability's anti-Flying bonus. The Mec has one
                            # Soul Weapon, so no separate melee weapon gate is required.
                            damage,crit=self.roll_critical_hit(damage)
                            # V-MAX source says Shoot-All gains damage and critical
                            # effectiveness, but gives no numeric increase. Do not
                            # fabricate a percentage here.
                            damage=await self.apply_boss_defense(target,damage); damage=self.v0210_adjust_player_damage(damage)
                            element={"laser_spin":"dark","area_bomb":"fire","maelstrom":"water","shock":"lightning","starlight_shower":"magic"}.get(special,"physical")
                            # Carries Elements is represented through the character's one
                            # Soul Weapon profile; physical remains the safe fallback when
                            # the weapon has no explicit elemental trait.
                            if special in ("pop_knight","shock_soldier","range_fire","dispose","shoot_all"):
                                _sw_element=str(getattr(self.character,"soul_weapon_element","") or "").casefold()
                                if _sw_element: element=_sw_element
                            if special=="shock":
                                # Shock is simultaneously Lightning and Dark. Apply both
                                # elemental interactions instead of collapsing it to one.
                                damage,note_light=v0314_adjust_damage_vs_template(template,damage,"lightning",skill.get("name",""))
                                damage,note_dark=v0314_adjust_damage_vs_template(template,damage,"dark",skill.get("name",""))
                                note=(note_light or "")+(note_dark or "")
                            else:
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
                        _p=(max(1,min(SKILL_MAX_LEVEL,skill_level))-1)/float(max(1,SKILL_MAX_LEVEL-1))
                        _will=max(1,int(self.effective_willpower()))
                        duration=self.skill_effect_duration_v11153(skill,skill_level,base_seconds=16)
                        if special=="hypno_flash":
                            accuracy=min(0.98,0.48+min(0.22,_will*0.002)+0.22*_p+(0.12 if support_effect else 0.0))
                            if random.random()<=accuracy:
                                mob.v0319_sleep_until=max(float(getattr(mob,"v0319_sleep_until",0.0) or 0.0),time.time()+duration)
                            await self.send(f"Hypno Flash: {'Sleep trafia' if time.time()<float(getattr(mob,'v0319_sleep_until',0.0) or 0.0) else 'Sleep nie trafia'} {template['name']}." + (" Support Effect zwiększa celność." if support_effect else ""))
                            await self.grant_skill_use_xp(skill); return
                        elif special=="jammer":
                            # v1.11.44: Jammer is Will-influenced Stop. Soulbound has one
                            # Soul Weapon, so Support Effect/V-MAX replaces the old separate
                            # Cyborg support-weapon requirement and expands Jammer to all enemies.
                            _p=(max(1,min(SKILL_MAX_LEVEL,skill_level))-1)/float(max(1,SKILL_MAX_LEVEL-1))
                            _will=max(1,int(self.effective_willpower()))
                            _support=support_effect
                            if _support:
                                self.server.world.refresh()
                                targets=[
                                    x for x in self.server.world.room_mobs(self.character.room_id)
                                    if x.alive
                                ]
                            else:
                                targets=[mob]
                            affected=0
                            durations=[]
                            for t in targets:
                                tt=MOB_TEMPLATES[t.template_id]
                                machine=bool(tt.get("machine"))
                                accuracy=min(0.98,0.52 + min(0.20,_will*0.002) + 0.20*_p + (0.18 if machine else 0.0))
                                duration=self.skill_effect_duration_v11153(skill,skill_level,base_seconds=18)
                                if random.random() <= accuracy:
                                    t.v0319_disabled_until=max(float(getattr(t,"v0319_disabled_until",0.0) or 0.0),time.time()+duration)
                                    affected+=1; durations.append(duration)
                            await self.send(
                                f"Jammer: Stop trafia {affected} z {len(targets)} celów"
                                + (f", czas do {max(durations)} s." if durations else ".")
                                + (" Support Effect: wszyscy przeciwnicy." if _support else "")
                                + (" Machine ma zwiększoną podatność." if any(MOB_TEMPLATES[t.template_id].get("machine") for t in targets) else "")
                            )
                            await self.grant_skill_use_xp(skill); return
                        else:
                            machine=bool(template.get("machine"))
                            accuracy=min(0.98,0.50+min(0.20,_will*0.002)+0.20*_p+(0.15 if machine else 0.0))
                            if random.random()<=accuracy:
                                until=time.time()+duration
                                mob.v0319_disabled_until=max(float(getattr(mob,"v0319_disabled_until",0.0) or 0.0),until) # Paralyze
                                mob.v0319_silence_until=max(float(getattr(mob,"v0319_silence_until",0.0) or 0.0),until)
                                mob.v0319_slow_until=max(float(getattr(mob,"v0319_slow_until",0.0) or 0.0),until)
                                if support_effect:
                                    mob.v0319_blind_until=max(float(getattr(mob,"v0319_blind_until",0.0) or 0.0),until)
                                    mob.v0319_curse_until=max(float(getattr(mob,"v0319_curse_until",0.0) or 0.0),until)
                                    mob.v0319_immobilize_until=max(float(getattr(mob,"v0319_immobilize_until",0.0) or 0.0),until)
                                hit=True
                            else: hit=False
                            await self.send(f"Logic Bomb: {'wirus trafia' if hit else 'wirus nie trafia'} {template['name']}." + (" Support Effect: Blind, Curse i Immobilize." if hit and support_effect else "") + (" Machine: zwiększona celność." if machine else ""))
                            await self.grant_skill_use_xp(skill); return

                    if special=="satellite_linker" and mob:
                        # Source confirms repeated minor laser damage, Wisdom influence
                        # and Skill-Level duration, but supplies no numeric tick share
                        # or base duration. Do not fabricate either value.
                        pass
                    if special=="tiger_rampage" and mob:
                        # v1.11.50: two heavy blows. One Soul Weapon replaces the
                        # original melee-weapon gate; its element is carried by both hits.
                        template=MOB_TEMPLATES[mob.template_id]
                        base=max(1,int(skill.get("base_power",1800) or 1800))
                        mult=skill_power*self.mec_branch_multiplier_v0319("melee")*self.skill_buff_multiplier(exclude_skill_id="v0319_mec_vmax")
                        total=0
                        _element=str(getattr(self.character,"soul_weapon_element","") or "physical").casefold()
                        for _hit in range(2):
                            if not mob.alive: break
                            damage=max(1,int((base*mult)/2.0)+random.randint(-6,6))
                            damage,crit=self.roll_critical_hit(damage)
                            damage=await self.apply_boss_defense(mob,damage); damage=self.v0210_adjust_player_damage(damage)
                            damage,note=v0314_adjust_damage_vs_template(template,damage,_element,skill.get("name","Tiger Rampage"))
                            mob.hp-=damage; total+=damage
                            await self.send(f"Tiger Rampage: {template['name']} otrzymuje {damage} obrażeń. HP {max(0,mob.hp)}.{note}")
                        broke=False
                        # Source confirms a chance to lower physical and magical
                        # defense, but gives no proc chance or base duration.
                        await self.grant_skill_use_xp(skill)
                        await self.send(f"Tiger Rampage: 2 ciężkie trafienia, łącznie {total} obrażeń." + (" Obrona fizyczna i magiczna celu spada." if broke else ""))
                        if mob.hp<=0: await self.mob_defeated(mob)
                        else: await self.ensure_realtime_combat()
                        return
                    # Mec Sonata may temporarily lower the target's level-equivalent
                    # power, but source help gives neither proc chance nor base duration.
                    # Keep the authored capability in metadata until a canonical
                    # probability/duration source exists; do not fabricate runtime values.
                    if special=="magnify":
                        # Source confirms an Overheat/reboot chance reduced by Skill
                        # Level and improved by Wisdom, but gives no numeric failure
                        # curve or lock duration. Preserve metadata, not invented odds.
                        pass
                    # Other single-target Mec attacks continue through the normal Soulbound damage handler below.

                    # Plural Slash Agility scaling is applied to this use only in the
                    # normal damage calculation below; never mutate the shared skill row.

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
                        # v1.11.6: Area rozpoczyna wspólną walkę tak samo jak
                        # zwykły atak. Dotyczy to także kierunku członek -> lider.
                        await self.server.auto_assist_party_combat(self, counter)
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
                # v1.11.7: wszystkie ofensywne skille Meca korzystają z pasywnej
                # specjalizacji swojej gałęzi. Wcześniej branch multiplier działał
                # głównie w dedykowanej ścieżce AoE, a single-target wpadający do
                # wspólnego handlera omijał Protocol/Mastery.
                if skill.get("mec_authored") and skill.get("mec_branch") in {
                    "melee", "ranged", "feedback", "magic"
                }:
                    multiplier *= self.mec_branch_multiplier_v0319(
                        str(skill.get("mec_branch"))
                    )

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
                _damage_element="physical" if skill_class_type == "physical" else "magic"
                if skill.get("mec_authored") and skill.get("carries_soul_weapon_elements"):
                    _sw_element=str(getattr(self.character,"soul_weapon_element","") or "").casefold()
                    if _sw_element: _damage_element=_sw_element
                damage, machine_note = v0314_adjust_damage_vs_template(
                    template, damage, _damage_element, skill.get("name", ""),
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
                    if skill.get("mec_branch")=="feedback":
                        self.queue_mec_feedback_repair_v11154(self_damage)
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

