# -*- coding: utf-8 -*-
"""Class-skill execution for Soulbound combat.

v0.47.0: explicit combat architecture; no compatibility-global injection.
"""
import random
import time

from world.uoss_superboss_runtime import superboss_healing_blocked_v11179
from core.classes_skills import CLASS_SKILLS, effective_skill_mana_cost
from core.progression_600 import SKILL_MAX_LEVEL
from core.progression_resources import class_type_for_name, skill_power_multiplier
from core.bootstrap_economy_professions import GLOBAL_SKILL_BUFF_DURATION_SECONDS, generator_core_v027
from data.mobs import MOB_TEMPLATES
from data.rooms import ROOMS
from network.protocol_gameplay_utils import normalize_lookup_text
from world.machine_expansion import v0314_adjust_damage_vs_template
from world.economy_quests import v0863_execute_threshold
from world.uoss_superboss_runtime import superboss_attack_gate_v11137, superboss_helper_profile_v11137

class SessionCombatSkillsMixin:
    def combat_skill_mana_cost_v11191(self, skill, class_name):
        """Resolve exact skill MP, including authored Mec state-dependent costs."""
        cost = effective_skill_mana_cost(skill, class_name)
        if skill.get("mec_authored"):
            if (
                str(skill.get("mec_special", "")) == "starlight_shower"
                and self.mec_vmax_active_v0319()
                and skill.get("uoss_vmax_mp_cost") is not None
            ):
                cost = max(0, int(skill.get("uoss_vmax_mp_cost") or 0))
            elif (
                str(skill.get("mec_branch", "")) == "support"
                and self.mec_support_effect_v11149()
                and skill.get("uoss_support_mp_cost") is not None
            ):
                cost = max(0, int(skill.get("uoss_support_mp_cost") or 0))
        return cost

    def offensive_skill_damage_type_v11190(self, skill):
        """Canonical physical/magic channel for every damaging class skill."""
        if skill.get("mec_authored"):
            branch = str(skill.get("mec_branch", "") or "").strip().lower()
            if branch == "magic":
                return "magic"
            if branch in {"melee", "ranged", "feedback"}:
                return "physical"
        return class_type_for_name(self.skill_class_name(skill))

    def offensive_skill_effective_stat_value_v11196(self, scale_name):
        """Raw effective combat stat after equipment; this is the late-game driver."""
        scale_name = str(scale_name or "strength").lower()
        if scale_name in ("attack", "physical_attack"):
            # Source-facing Attack influence maps to Soulbound's complete derived
            # physical attack power: trained STR plus flat Attack/Weapon Power EQ.
            return max(1, int(self.physical_power()))
        if scale_name in ("intelligence", "wisdom", "magic"):
            return max(1, int(self.effective_intelligence()))
        if scale_name in ("dexterity", "agility", "ranged"):
            return max(1, int(self.effective_dexterity()))
        if scale_name in ("will", "willpower"):
            return max(1, int(self.effective_willpower()))
        if scale_name in ("constitution", "vitality", "vit"):
            return max(1, int(self.effective_constitution()))
        return max(1, int(self.effective_strength()))

    def offensive_skill_core_stat_power_v11188(self, skill):
        """Effective offensive stat power including source-faithful flat EQ power."""
        scale_name = str(skill.get("scale", "strength") or "strength").lower()
        flat = self.equipment_flat_power_totals_v11187()
        level = int(self.character.character_level)
        raw_stat = self.offensive_skill_effective_stat_value_v11196(scale_name)
        if scale_name in ("attack", "physical_attack"):
            # physical_power() already contains trained STR + flat Attack +
            # Weapon Power, so never add those flat values a second time.
            return max(1, int(raw_stat))
        stat_power = generator_core_v027.character_attribute_power(level, raw_stat)
        if scale_name in ("intelligence", "wisdom", "magic", "will", "willpower"):
            stat_power += int(flat["magic_attack"])
        else:
            stat_power += int(flat["attack"]) + int(flat["weapon_power"])
        return max(1, int(stat_power))

    def offensive_skill_core_power_v11185(self, skill, authored_base=0):
        """Global offensive core driven primarily by real character stats + EQ.

        Character Level alone never grants the late-game multiplier. The large
        progression step comes from the effective primary stat after equipment,
        runes, set bonuses and relics. Skills that explicitly declare a secondary
        stat also receive a smaller Soulbound contribution from that stat.

        authored_base is reserved for an explicit Soulbound/source damage value.
        AP/learning costs must never be passed here as attack power.
        """
        scale_name = str(skill.get("scale", "strength") or "strength").lower()
        primary_value = self.offensive_skill_effective_stat_value_v11196(scale_name)
        stat_power = self.offensive_skill_core_stat_power_v11188(skill)

        secondary_name = str(skill.get("secondary_scale", "") or "").lower()
        secondary_value = 0
        secondary_power = 0
        if secondary_name:
            secondary_value = self.offensive_skill_effective_stat_value_v11196(secondary_name)
            secondary_power = generator_core_v027.character_attribute_power(
                int(self.character.character_level), secondary_value
            )

        # A secondary source influence is deliberately smaller than the primary.
        # Cosmic Rave, for example, is Attack-led per source while Agility/DEX
        # from the actual build and equipment contributes to a lesser degree.
        secondary_weight = 0.35 if secondary_name else 0.0
        weighted_stat = primary_value + secondary_value * secondary_weight
        build_multiplier = generator_core_v027.character_offensive_build_multiplier(weighted_stat)

        soul_power = max(0, int(self.character.soul_power()))
        core = (
            int(authored_base or 0)
            + soul_power
            + stat_power
            + int(round(secondary_power * secondary_weight))
        )
        return max(1, int(round(core * build_multiplier)))

    def healing_skill_build_multiplier_v11196(self, skill):
        """Uncapped healing growth from the skill's real effective stats.

        Healing stats level independently from Character Level. Equipment feeds
        this through effective_*(), exactly like offensive builds. A fixed
        Level-175 stat anchor keeps the existing midgame scale while allowing
        unlimited stats to keep improving healing with soft diminishing returns.
        """
        scale_name = str(skill.get("scale", "") or "").strip().lower()
        secondary_name = str(skill.get("secondary_scale", "") or "").strip().lower()
        if not scale_name:
            class_name = self.skill_class_name(skill)
            if class_name in {"Kapłan", "Druid"}:
                scale_name, secondary_name = "intelligence", "willpower"
            elif class_name == "Mnich":
                scale_name, secondary_name = "dexterity", "willpower"
            else:
                scale_name = "willpower"

        primary = float(self.offensive_skill_effective_stat_value_v11196(scale_name))
        primary_growth = max(0.01, primary / 175.0) ** 0.72
        if not secondary_name:
            return max(0.20, primary_growth)

        secondary = float(self.offensive_skill_effective_stat_value_v11196(secondary_name))
        secondary_growth = max(0.01, secondary / 175.0) ** 0.72
        return max(0.20, 0.70 * primary_growth + 0.30 * secondary_growth)

    def healing_skill_amount_v11196(self, skill, target, skill_power):
        """Canonical class-heal amount from stats + Skill Level + EQ.

        Authored percentage heals preserve their identity, but their potency is
        multiplied by the uncapped healing build. Source abilities without an
        authored percentage (e.g. Healing Wind) use their explicit stat as a
        flat healing core. Effective stats already include equipment.
        """
        racial = float(self.character.racial_healing_multiplier())
        class_mult = float(self.character.class_healing_multiplier())
        heal_type = class_type_for_name(self.skill_class_name(skill))
        buff_mult = float(self.skill_buff_multiplier(target_type=heal_type))
        build_mult = float(self.healing_skill_build_multiplier_v11196(skill))
        total_mult = max(0.0, float(skill_power)) * racial * class_mult * buff_mult * build_mult

        authored_pct = skill.get("heal_pct")
        if authored_pct is not None:
            return max(1, int(round(target.max_hp() * max(0.0, float(authored_pct)) * total_mult)))

        scale_name = str(skill.get("scale", "willpower") or "willpower").lower()
        primary = self.offensive_skill_effective_stat_value_v11196(scale_name)
        secondary_name = str(skill.get("secondary_scale", "") or "").lower()
        secondary = (
            self.offensive_skill_effective_stat_value_v11196(secondary_name)
            if secondary_name else 0
        )
        stat_core = primary + int(round(secondary * 0.35))
        return max(1, int(round(stat_core * total_mult)))

    def regen_duration_seconds_v11196(self, skill_level):
        """Soulbound adaptation for source-defined 'short period' Regen duration.

        UOSS supplies no seconds. Keep the existing 30-second buff scale as the
        low-level anchor and extend it to 90 seconds at Skill Level 600.
        This is Soulbound balance, not a claimed UOSS number.
        """
        level=max(1,min(SKILL_MAX_LEVEL,int(skill_level)))
        progress=(level-1)/float(max(1,SKILL_MAX_LEVEL-1))
        return max(1,int(round(30.0+60.0*(progress ** 0.82))))

    def regen_tick_power_v11196(self, skill_level):
        """Small periodic WILL heal for Regen; explicit Soulbound balance."""
        will=max(1,int(self.effective_willpower()))
        power=float(skill_power_multiplier(max(1,min(SKILL_MAX_LEVEL,int(skill_level)))))
        racial=float(self.character.racial_healing_multiplier())
        class_mult=float(self.character.class_healing_multiplier())
        return max(1,int(round(will*0.10*power*racial*class_mult)))

    def satellite_linker_duration_rounds_v11196(self, skill_level, skill):
        """Explicit Soulbound duration adaptation for source-defined short duration."""
        level=max(1,min(SKILL_MAX_LEVEL,int(skill_level)))
        progress=(level-1)/float(max(1,SKILL_MAX_LEVEL-1))
        start=max(1,int(skill.get("soulbound_duration_rounds_level1",3) or 3))
        end=max(start,int(skill.get("soulbound_duration_rounds_level600",8) or 8))
        return max(1,int(round(start+(end-start)*(progress ** 0.82))))

    async def apply_satellite_linker_round_v11196(self):
        """Tick the Mec's one active Satellite Linker effect once per owner round."""
        state=getattr(self,"v11196_satellite_linker",None)
        if not state or not self.character or self.current_hp<=0:
            return 0
        target_key=str(state.get("target_key","") or "")
        target=self.server.world.mobs.get(target_key) if target_key else None
        if (
            not target
            or not target.alive
            or target.room_id!=self.character.room_id
        ):
            self.v11196_satellite_linker=None
            return 0

        skill=next(
            (
                row for row in CLASS_SKILLS.get("Mec",[])
                if str(row.get("mec_special",""))=="satellite_linker"
            ),
            None,
        )
        if not skill:
            self.v11196_satellite_linker=None
            return 0

        # UOSS Base AP is a learning/AP cost, not damage power.
        # Satellite Linker damage comes from Soulbound stats/EQ/Soul Power,
        # Skill Level, Ranged Protocol and its authored tick multiplier.
        base=0
        tick_mult=max(
            0.01,float(skill.get("soulbound_tick_damage_multiplier",0.20) or 0.20)
        )
        mult=(
            self.mec_branch_multiplier_v0319("ranged","satellite_linker")
            * self.offensive_skill_damage_multiplier_v11186(skill,"physical")
        )
        damage=max(
            1,
            int(round(
                self.offensive_skill_core_power_v11185(skill,base)
                * mult
                * tick_mult
            )),
        )
        damage=await self.apply_boss_defense(target,damage)
        damage=self.v0210_adjust_player_damage(damage)
        template=MOB_TEMPLATES[target.template_id]
        damage,note=v0314_adjust_damage_vs_template(
            template,damage,"physical",skill.get("name","Satellite Linker")
        )
        target.hp-=damage
        self._recap52_dealt=int(getattr(self,"_recap52_dealt",0) or 0)+max(0,int(damage))

        remaining=max(0,int(state.get("remaining_rounds",1) or 1)-1)
        state["remaining_rounds"]=remaining
        await self.send(
            f"Satellite Linker: bity trafiają {template['name']} za {damage} obrażeń. "
            f"HP {max(0,target.hp)}.{note}"
        )

        if target.hp<=0:
            self.v11196_satellite_linker=None
            await self.mob_defeated(target)
            return damage
        if remaining<=0:
            self.v11196_satellite_linker=None
            await self.send("Satellite Linker: bity kończą działanie.")
        return damage

    async def apply_active_regen_round_v11196(self):
        """Advance canonical Regen by one owner combat round.

        UOSS says 'every few rounds' without an exact cadence. Soulbound uses
        every 3 owner rounds as an explicit balance adaptation. Multiple Regen
        sources do not stack their healing; the strongest due pulse wins.
        """
        now=time.time()
        due=[]
        expired=[]
        for key,buff in list(self.active_skill_buffs.items()):
            if str(buff.get("canonical_status",""))!="regen":
                continue
            until=float(buff.get("until",0.0) or 0.0)
            if until and now>=until:
                expired.append(key)
                continue
            cadence=max(1,int(buff.get("tick_every_rounds",3) or 3))
            rounds=int(buff.get("regen_round_counter",0) or 0)+1
            buff["regen_round_counter"]=rounds
            if rounds % cadence == 0:
                due.append(max(0,int(buff.get("regen_power",0) or 0)))
        for key in expired:
            self.active_skill_buffs.pop(key,None)
        if not due or self.current_hp<=0 or self.current_hp>=self.max_hp():
            return 0
        if superboss_healing_blocked_v11179(self):
            return 0
        amount=max(due)
        actual=min(max(0,self.max_hp()-self.current_hp),amount)
        if actual<=0:
            return 0
        self.current_hp+=actual
        self._recap52_heal=int(getattr(self,"_recap52_heal",0) or 0)+actual
        await self.send_combat(
            f"Regen odnawia {actual} HP. HP {self.current_hp} z {self.max_hp()}.",
            "full",
        )
        return actual

    def offensive_skill_damage_multiplier_v11186(self, skill, skill_class_type=None):
        """One global offensive multiplier path for current and future equipment.

        Equipment source is deliberately irrelevant: shop, drop, crafting and future
        catalog items all contribute through equipment_property_totals() while their
        primary stats already feed skill_scale_value() via effective_*().
        """
        resolved_type = skill_class_type or self.offensive_skill_damage_type_v11190(skill)
        damage_type = "physical" if resolved_type == "physical" else "magic"
        multiplier = float(skill.get("mult", 1.0))
        if resolved_type == "physical":
            multiplier *= self.character.class_physical_damage_multiplier()
            multiplier *= self.character.racial_physical_damage_multiplier()
        else:
            multiplier *= self.character.class_magic_damage_multiplier()
            multiplier *= self.character.racial_magic_damage_multiplier()
        multiplier *= self.character.racial_all_damage_multiplier()
        multiplier *= self.total_set_damage_multiplier()
        multiplier *= self.equipment_damage_multiplier(damage_type)
        multiplier *= self.skill_buff_multiplier(target_type=resolved_type)
        return multiplier

    async def apply_superboss_helper_skill_damage_v11189(self, target):
        """Helper joins damaging skill actions against its sourced superboss.

        Uses the same build-scaled helper strike as realtime combat. No cadence,
        ability multiplier or source percentage is invented.
        """
        if not target or not target.alive:
            return 0
        template = MOB_TEMPLATES[target.template_id]
        profile = superboss_helper_profile_v11137(self, template)
        if not profile:
            return 0
        name = str(profile.get("name", "Pomocnik"))
        magic = name in {"Popoi", "Primm", "Montblanc", "Byblos"}
        kind = "magic" if magic else "physical"
        stat = self.spell_power() if magic else self.physical_power()
        raw_stat = (
            max(self.effective_intelligence(), self.effective_willpower())
            if magic else
            max(self.effective_strength(), self.effective_dexterity())
        )
        mult = self.equipment_damage_multiplier(kind) * self.total_set_damage_multiplier()
        mult *= generator_core_v027.character_offensive_build_multiplier(raw_stat)
        damage = max(1, int(round((self.character.soul_power() + stat) * 0.65 * mult)))
        damage = await self.apply_boss_defense(target, damage)
        damage = self.v0210_adjust_player_damage(damage)
        damage, note = v0314_adjust_damage_vs_template(template, damage, kind, name)
        damage = min(max(0, target.hp), max(0, int(damage)))
        if damage <= 0:
            return 0
        target.hp -= damage
        self._recap52_dealt = int(getattr(self, "_recap52_dealt", 0) or 0) + damage
        await self.send(
            f"{name} dołącza do umiejętności: {damage} obrażeń. "
            f"Przeciwnik: {max(0, target.hp)} z {template['max_hp']} HP." + note
        )
        return damage

    async def apply_superboss_helper_after_skill_v11192(self, targets):
        """Let the sourced helper join once per damaging skill action.

        Multi-hit and AoE skills still trigger only one helper strike. The first
        living target that actually belongs to the helper's Superboss encounter
        is selected.
        """
        seen = set()
        for target in list(targets or ()):
            if not target or not target.alive or target.key in seen:
                continue
            seen.add(target.key)
            template = MOB_TEMPLATES[target.template_id]
            if not superboss_helper_profile_v11137(self, template):
                continue
            damage = await self.apply_superboss_helper_skill_damage_v11189(target)
            return target, damage
        return None, 0

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
                mana_cost = self.combat_skill_mana_cost_v11191(skill, skill_class)
                if mana_cost > 0:
                    mana_cost = int(round(mana_cost * self.equipment_mp_cost_multiplier_v11176()))
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
                    recipients=list(
                        self.server.party_sessions(
                            self.account_id,same_room=self.character.room_id
                        ) or []
                    )
                    if self not in recipients:
                        recipients.append(self)
                    recipients=[
                        session for session in recipients
                        if not session.closed and session.character
                        and session.current_hp>0
                    ]
                    injured=[
                        session for session in recipients
                        if session.current_hp < session.max_hp()
                    ]
                    if not injured:
                        await self.send(
                            f"{skill['name']}: nikt w drużynie w tej lokacji "
                            "nie potrzebuje leczenia."
                        )
                        return
                    healable=[
                        session for session in injured
                        if not superboss_healing_blocked_v11179(session)
                    ]
                    if not healable:
                        await self.send(
                            f"{skill['name']}: Nullify Healing blokuje leczenie "
                            "wszystkich rannych celów."
                        )
                        return

                    # Group-heal used to return before the shared mana deduction,
                    # making Healing Wind / Mass Restoration effectively free.
                    self.current_mana -= mana_cost

                    healed=[]
                    blocked_count=len(injured)-len(healable)
                    for target in healable:
                        target_max=target.max_hp()
                        before=target.current_hp
                        heal=self.healing_skill_amount_v11196(
                            skill,target,skill_power
                        )
                        target.current_hp=min(target_max,before+heal)
                        actual=target.current_hp-before
                        if actual:
                            healed.append((target,actual))
                            if target is not self:
                                await target.send(
                                    f"{self.character.name} używa {skill['name']}. "
                                    f"Odzyskujesz {actual} HP."
                                )
                    await self.grant_skill_use_xp(skill)
                    total=sum(amount for _target,amount in healed)
                    await self.send(
                        f"{skill['name']}: uleczono {len(healed)} członków drużyny "
                        f"w tej lokacji, łącznie {total} HP."
                        + (
                            f" Nullify Healing zablokował {blocked_count} cel(e)."
                            if blocked_count else ""
                        )
                    )
                    if mana_cost:
                        await self.send(
                            f"Mana: {self.current_mana} z {self.max_mana()}."
                        )
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

                    # Area Bomb ma źródłowy target "All Targetted Enemies": nie może
                    # tworzyć nowego aggro na mobach tylko dlatego, że stoją w pokoju.
                    # W Soulbound lokalna drużyna automatycznie współdzieli walkę, więc
                    # za targetted uznajemy cele już związane z Mecem lub jego lokalnym
                    # party PRZED użyciem Area Bomb.
                    _area_bomb_targeted_only = (
                        str(skill.get("mec_special", "") or "") == "area_bomb"
                    )
                    if _area_bomb_targeted_only:
                        _local_party = (
                            self.server.party_sessions(
                                self.account_id, same_room=self.character.room_id
                            )
                            or [self]
                        )
                        _party_names = {
                            str(sess.character.name)
                            for sess in _local_party
                            if not sess.closed and sess.character
                        }
                        _targetted_keys = {
                            str(sess.combat_mob_key)
                            for sess in _local_party
                            if getattr(sess, "combat_mob_key", None)
                        }
                        for candidate in aoe_mobs:
                            if (
                                str(candidate.engaged_by or "") in _party_names
                                or str(getattr(candidate, "aoe_engaged_by", "") or "") in _party_names
                            ):
                                _targetted_keys.add(str(candidate.key))
                        aoe_mobs = [
                            candidate for candidate in aoe_mobs
                            if str(candidate.key) in _targetted_keys
                        ]
                        if not aoe_mobs:
                            await self.send(
                                "Area Bomb: brak już zaangażowanych przeciwników. "
                                "Ten skill nie rozpoczyna nowej walki."
                            )
                            return

                    # Zachowujemy właściciela aggro sprzed AoE. Obszarówka może zranić
                    # moba walczącego z obcym graczem, ale nie kradnie jego aggro/nagród.
                    aoe_reward_owner = {candidate.key: candidate.engaged_by for candidate in aoe_mobs}
                    available_for_aggro = [
                        candidate for candidate in aoe_mobs
                        if self.server.engagement_allowed(self, candidate)
                    ]
                    for candidate in available_for_aggro:
                        if not _area_bomb_targeted_only and not candidate.engaged_by:
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

                _generic_heal_target = None
                if kind == "heal" and not skill.get("mec_authored"):
                    _heal_party=list(
                        self.server.party_sessions(
                            self.account_id,same_room=self.character.room_id
                        ) or []
                    )
                    if self not in _heal_party:
                        _heal_party.append(self)
                    _heal_party=[
                        sess for sess in _heal_party
                        if not sess.closed and sess.character and sess.current_hp>0
                    ]
                    if target_text:
                        _wanted=normalize_lookup_text(target_text)
                        if _wanted in {"self","me","ja","siebie"}:
                            _generic_heal_target=self
                        else:
                            _generic_heal_target=next(
                                (
                                    sess for sess in _heal_party
                                    if sess is not self
                                    and (
                                        _wanted==normalize_lookup_text(sess.character.name)
                                        or _wanted in normalize_lookup_text(sess.character.name)
                                    )
                                ),
                                None,
                            )
                        if _generic_heal_target is None:
                            await self.send(
                                f"{skill['name']} leczy tylko ciebie albo żywego "
                                "sojusznika w tej lokacji. Przeciwnik nie może być celem."
                            )
                            return
                        if _generic_heal_target.current_hp>=_generic_heal_target.max_hp():
                            await self.send(
                                f"{skill['name']}: {_generic_heal_target.character.name} "
                                "ma już pełne HP."
                            )
                            return
                    else:
                        _injured=[
                            sess for sess in _heal_party
                            if sess.current_hp<sess.max_hp()
                        ]
                        if not _injured:
                            await self.send(
                                f"{skill['name']}: nikt w drużynie w tej lokacji "
                                "nie potrzebuje leczenia."
                            )
                            return
                        _generic_heal_target=min(
                            _injured,
                            key=lambda sess: (
                                sess.current_hp/max(1,sess.max_hp()),
                                sess.current_hp,
                                sess.character.name.lower(),
                            ),
                        )
                    if superboss_healing_blocked_v11179(_generic_heal_target):
                        await self.send(
                            f"Nullify Healing blokuje {skill['name']} na tym celu."
                        )
                        return

                _regen_target = None
                if kind == "regen":
                    target=_regen_target or self
                    # UOSS does not expose the exact cadence, HP/tick or seconds.
                    # Soulbound adaptation: small WILL-based pulse every 3 owner
                    # combat rounds, with 30->90 s duration from Skill Level 1->600.
                    _regen_duration=self.regen_duration_seconds_v11196(skill_level)
                    _regen_power=self.regen_tick_power_v11196(skill_level)
                    target.active_skill_buffs["priest_regen"]={
                        "name":"Regen","boost":1.0,
                        "until":time.time()+_regen_duration,
                        "source":self.character.name,"beneficial":True,
                        "canonical_status":"regen",
                        "source_effect":"periodic_small_hp_heal",
                        "source_stat_influence":["will"],
                        "source_duration_scales_with_level":True,
                        "properties":["dispelable","extendable","reflectable","silenceable"],
                        "tick_cadence_source_defined":False,
                        "heal_amount_source_defined":False,
                        "base_duration_source_defined":False,
                        "tick_every_rounds":3,
                        "regen_power":_regen_power,
                        "regen_round_counter":0,
                        "soulbound_balance_adaptation":True,
                    }
                    await self.grant_skill_use_xp(skill)
                    await self.send(
                        f"Regen: {target.character.name} otrzymuje okresową regenerację "
                        f"na {_regen_duration} s. Soulbound: impuls co 3 rundy; "
                        "dokładne liczby UOSS nie są dostępne."
                    )
                    if target is not self:
                        await target.send(
                            f"{self.character.name} nakłada na ciebie Regen "
                            f"na {_regen_duration} s."
                        )
                    if self.combat_mob_key:
                        await self.ensure_realtime_combat()
                    return


                if kind == "heal":
                    target=_generic_heal_target
                    if target is None:
                        await self.send(
                            f"{skill['name']}: brak prawidłowego celu leczenia."
                        )
                        return
                    target_max=target.max_hp()
                    heal=self.healing_skill_amount_v11196(
                        skill,target,skill_power
                    )
                    before=target.current_hp
                    target.current_hp=min(target_max,target.current_hp+heal)
                    actual=target.current_hp-before
                    if target is self:
                        await self.send(
                            f"Używasz {skill['name']} na Skill Level {skill_level}. "
                            f"Odzyskujesz {actual} HP. Masz teraz "
                            f"{target.current_hp} z {target_max} HP."
                        )
                    else:
                        await target.send(
                            f"{self.character.name} używa {skill['name']} na tobie. "
                            f"Odzyskujesz {actual} HP. Masz teraz "
                            f"{target.current_hp} z {target_max} HP."
                        )
                        await self.send(
                            f"Używasz {skill['name']} na {target.character.name}. "
                            f"Przywrócono {actual} HP."
                        )
                    await self.server.party_nearby_broadcast(
                        self,
                        f"{self.character.name}: {skill['name']} leczy "
                        f"{target.character.name} za {actual} HP.",
                        exclude=[self,target],
                        detail="normal",
                        history_category="combat",
                    )
                    if self.character.racial_healing_bonus_percent()>0:
                        await self.send(
                            f"Bonus rasy {self.character.race}: "
                            f"+{self.character.racial_healing_bonus_percent()} procent "
                            "mocy leczenia."
                        )
                    class_heal_bonus=int(
                        round((self.character.class_healing_multiplier()-1.0)*100)
                    )
                    if class_heal_bonus>0:
                        await self.send(
                            f"Bonus aktywnych klas: +{class_heal_bonus} procent "
                            "mocy leczenia."
                        )
                    await self.grant_skill_use_xp(skill)
                    if mana_cost:
                        await self.send(
                            f"Mana: {self.current_mana} z {self.max_mana()}."
                        )
                    if self.combat_mob_key:
                        await self.ensure_realtime_combat()
                    return


                if kind == "aoe_damage":
                    aoe_class_type = self.offensive_skill_damage_type_v11190(skill)
                    multiplier = self.offensive_skill_damage_multiplier_v11186(skill, aoe_class_type) * skill_power
                    core_power = self.offensive_skill_core_power_v11185(skill)
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
                        damage = max(1, int(core_power * multiplier) + random.randint(-2, 3))
                        damage, critical = self.roll_critical_hit(damage)
                        if critical:
                            self.record_social_record_v03051("biggest_crit", damage)
                            critical_hits += 1
                        damage = await self.apply_boss_defense(target, damage)
                        damage = self.v0210_adjust_player_damage(damage)
                        damage, machine_note = v0314_adjust_damage_vs_template(
                            template, damage, aoe_class_type, skill.get("name", "")
                        )
                        target.hp -= damage
                        total_damage += damage
                        marker = " Krytyk." if critical else ""
                        await self.send(f"{template['name']}: {damage} obrażeń.{marker} HP {max(0, target.hp)} z {template['max_hp']}.")
                        (defeated if target.hp <= 0 else survivors).append(target)
                    helper_target, _helper_damage = await self.apply_superboss_helper_after_skill_v11192(survivors)
                    if helper_target is not None and helper_target.hp <= 0:
                        if helper_target not in defeated:
                            defeated.append(helper_target)
                        survivors = [target for target in survivors if target.key != helper_target.key]
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
                skill_class_type = self.offensive_skill_damage_type_v11190(skill)
                multiplier = self.offensive_skill_damage_multiplier_v11186(skill, skill_class_type) * skill_power
                core_power = self.offensive_skill_core_power_v11185(skill)
                # v1.11.7: wszystkie ofensywne skille Meca korzystają z pasywnej
                # specjalizacji swojej gałęzi. Wcześniej branch multiplier działał
                # głównie w dedykowanej ścieżce AoE, a single-target wpadający do
                # wspólnego handlera omijał Protocol/Mastery.
                if skill.get("mec_authored") and skill.get("mec_branch") in {
                    "melee", "ranged", "feedback", "magic"
                }:
                    multiplier *= self.mec_branch_multiplier_v0319(
                        str(skill.get("mec_branch")), str(skill.get("mec_special",""))
                    )

                _mec_feedback_self_damage=0
                _mec_damage_override=None
                _mec_disable_critical=False
                _mec_compress_missed=False
                _mec_percent_damage_exact=False
                if skill.get("mec_authored"):
                    _mec_special=str(skill.get("mec_special",""))
                    if _mec_special=="compress":
                        # Source contract: percentage damage based on target HP.
                        # Vitality/HP influence compression power, Skill Level raises
                        # Accuracy, full HP and a shield improve compression power.
                        # UOSS supplies no numeric formula, so all values below are
                        # explicit Soulbound balance metadata.
                        _compress_max_hp=max(1,int(self.max_hp()))
                        _compress_current_hp=max(0,int(self.current_hp))
                        _compress_hp_ratio=max(
                            0.0,min(1.0,_compress_current_hp/float(_compress_max_hp))
                        )
                        _compress_vit=max(1,int(self.effective_constitution()))
                        _compress_vit_ratio=max(0.01,_compress_vit/175.0)
                        _compress_level=max(1,min(SKILL_MAX_LEVEL,int(skill_level)))
                        _compress_progress=(
                            (_compress_level-1)/float(max(1,SKILL_MAX_LEVEL-1))
                        )
                        _compress_accuracy=(
                            float(skill.get("base_accuracy",0.65) or 0.65)
                            + _compress_progress
                            * float(skill.get("skill_level_accuracy_bonus_max",0.30) or 0.30)
                            + min(
                                0.10,
                                float(skill.get("vitality_accuracy_bonus_anchor",0.05) or 0.05)
                                * (_compress_vit_ratio ** 0.50),
                            )
                        )
                        _compress_accuracy=max(0.05,min(0.98,_compress_accuracy))
                        _compress_pct=float(
                            skill.get("base_target_current_hp_pct",0.20) or 0.20
                        )
                        if _compress_hp_ratio>=0.999999:
                            _compress_pct += float(
                                skill.get("full_hp_damage_pct_bonus",0.10) or 0.10
                            )
                        _compress_shield=bool(
                            self.server.db.equipped_item(self.account_id,"shield")
                        )
                        if _compress_shield:
                            _compress_pct += float(
                                skill.get("shield_damage_pct_bonus",0.10) or 0.10
                            )
                            await self.send(
                                "Compress: założona tarcza zwiększa siłę kompresji."
                            )
                        _compress_pct += min(
                            0.15,
                            float(skill.get("vitality_damage_pct_anchor",0.05) or 0.05)
                            * (_compress_vit_ratio ** 0.50),
                        )
                        _compress_pct=min(
                            float(skill.get("max_target_current_hp_pct",0.60) or 0.60),
                            max(0.01,_compress_pct),
                        )
                        _mec_disable_critical=True
                        _mec_percent_damage_exact=True
                        if random.random() < _compress_accuracy:
                            _mec_damage_override=max(
                                1,int(round(max(1,int(mob.hp))*_compress_pct))
                            )
                            await self.send(
                                f"Compress trafia. Siła kompresji: "
                                f"{int(round(_compress_pct*100))} procent bieżącego HP celu. "
                                f"Celność: {int(round(_compress_accuracy*100))} procent."
                            )
                        else:
                            _mec_damage_override=0
                            _mec_compress_missed=True
                            await self.send(
                                f"Compress nie trafia. Celność: "
                                f"{int(round(_compress_accuracy*100))} procent."
                            )
                        _mec_feedback_self_damage=max(
                            1,int(round(
                                _compress_max_hp
                                * float(skill.get("feedback_max_hp_pct",0.08) or 0.08)
                            ))
                        )
                    elif _mec_special=="destroy":
                        # Source contract: Attack + Vitality + HP, with power rising
                        # as HP falls. Shield improves damage. Numeric coefficients
                        # are not supplied by UOSS, so these are explicit Soulbound
                        # balance values recorded in skill metadata.
                        _destroy_max_hp=max(1,int(self.max_hp()))
                        _destroy_current_hp=max(0,int(self.current_hp))
                        _destroy_missing_ratio=max(
                            0.0,min(
                                1.0,
                                (_destroy_max_hp-_destroy_current_hp)
                                / float(_destroy_max_hp),
                            )
                        )
                        multiplier *= 1.0 + _destroy_missing_ratio * float(
                            skill.get("missing_hp_max_damage_bonus",0.50) or 0.50
                        )
                        _shield_equipped=bool(
                            self.server.db.equipped_item(self.account_id,"shield")
                        )
                        if _shield_equipped:
                            multiplier *= float(
                                skill.get("shield_damage_multiplier",1.10) or 1.10
                            )
                            await self.send("Destroy: założona tarcza wzmacnia atak.")
                        _mec_feedback_self_damage=max(
                            1,int(round(
                                _destroy_max_hp
                                * float(skill.get("feedback_max_hp_pct",0.06) or 0.06)
                            ))
                        )
                    elif _mec_special=="crush":
                        # Source contract: raw attack power is the difference between
                        # max HP and current HP, capped by experience/Character Level;
                        # Skill Level raises the maximum possible damage and a shield
                        # increases that capacity. The source supplies no numeric curve.
                        _missing_hp=max(0,int(self.max_hp())-int(self.current_hp))
                        _capacity=(
                            int(self.character.character_level)
                            * int(skill.get("capacity_per_character_level",100) or 100)
                            + int(skill_level)
                            * int(skill.get("capacity_per_skill_level",25) or 25)
                        )
                        _shield_equipped=bool(
                            self.server.db.equipped_item(self.account_id,"shield")
                        )
                        if _shield_equipped:
                            _capacity=max(
                                1,int(round(
                                    _capacity
                                    * float(skill.get("shield_capacity_multiplier",1.25) or 1.25)
                                ))
                            )
                            await self.send("Crush: założona tarcza zwiększa limit obrażeń.")
                        _source_crush_damage=min(_missing_hp,max(0,_capacity))
                        _crush_external_mult=(
                            self.offensive_skill_damage_multiplier_v11186(
                                skill,skill_class_type
                            )
                            * self.mec_branch_multiplier_v0319("feedback", "crush")
                        )
                        _mec_damage_override=max(
                            0,int(round(_source_crush_damage*_crush_external_mult))
                        )
                        if _source_crush_damage>0:
                            _mec_feedback_self_damage=max(
                                1,int(round(
                                    _source_crush_damage
                                    * float(skill.get("feedback_source_damage_pct",0.15) or 0.15)
                                ))
                            )
                    elif _mec_special=="robo_tackle":
                        # Source contract: HP before use + Vitality + Attack determine
                        # damage. Lower current HP means lower power; a shield improves
                        # damage; V-MAX raises both attack power and Feedback.
                        #
                        # UOSS supplies no numeric coefficients. These are explicit
                        # Soulbound balance values, intentionally below Kamikaze Crush.
                        _hp_before=max(1,int(self.current_hp))
                        _hp_power_ratio=float(
                            skill.get("current_hp_power_ratio",0.12) or 0.12
                        )
                        core_power += max(0,int(round(_hp_before*_hp_power_ratio)))
                        _shield_equipped=bool(
                            self.server.db.equipped_item(self.account_id,"shield")
                        )
                        if _shield_equipped:
                            multiplier *= float(
                                skill.get("shield_damage_multiplier",1.15) or 1.15
                            )
                            await self.send("Robo Tackle: założona tarcza wzmacnia atak.")
                        if vmax:
                            multiplier *= float(
                                skill.get("vmax_damage_multiplier",1.20) or 1.20
                            )
                        _feedback_pct=float(
                            skill.get(
                                "vmax_feedback_current_hp_pct" if vmax else "feedback_current_hp_pct",
                                0.25 if vmax else 0.10,
                            )
                            or (0.25 if vmax else 0.10)
                        )
                        _mec_feedback_self_damage=max(
                            1,int(round(_hp_before*_feedback_pct))
                        )
                        if vmax:
                            await self.send(
                                "Robo Tackle: V-MAX zwiększa moc ataku i obrażenia Feedback."
                            )
                    elif _mec_special=="kamikaze_crush":
                        # Source contract: HP before use + Vitality + Attack determine
                        # damage; lower current HP means lower power. A shield improves
                        # damage, while V-MAX raises both attack power and Feedback.
                        #
                        # UOSS supplies no numeric coefficients. The values below are
                        # explicit Soulbound balance adaptations recorded in metadata,
                        # not claimed source numbers.
                        _hp_before=max(1,int(self.current_hp))
                        _hp_power_ratio=float(skill.get("current_hp_power_ratio",0.20) or 0.20)
                        core_power += max(0,int(round(_hp_before*_hp_power_ratio)))
                        _shield_equipped=bool(
                            self.server.db.equipped_item(self.account_id,"shield")
                        )
                        if _shield_equipped:
                            multiplier *= float(skill.get("shield_damage_multiplier",1.20) or 1.20)
                        if vmax:
                            multiplier *= float(skill.get("vmax_damage_multiplier",1.30) or 1.30)
                        _feedback_pct=float(
                            skill.get(
                                "vmax_feedback_current_hp_pct" if vmax else "feedback_current_hp_pct",
                                0.45 if vmax else 0.20,
                            )
                            or (0.45 if vmax else 0.20)
                        )
                        _mec_feedback_self_damage=max(
                            1,int(round(_hp_before*_feedback_pct))
                        )
                        if _shield_equipped:
                            await self.send("Kamikaze Crush: założona tarcza wzmacnia atak.")
                        if vmax:
                            await self.send("Kamikaze Crush: V-MAX zwiększa moc ataku i obrażenia Feedback.")

                if kind == "execute":
                    hp_ratio = mob.hp / max(1, template["max_hp"])
                    execute_threshold = v0863_execute_threshold(template)
                    if hp_ratio <= execute_threshold:
                        multiplier *= min(2.0, float(skill.get("execute_mult", 1.5)))
                        await self.send(
                            f"Egzekucyjny próg aktywny: przeciwnik ma nie więcej niż "
                            f"{int(round(execute_threshold * 100))} procent HP."
                        )

                if _mec_damage_override is not None:
                    damage=max(0,int(_mec_damage_override))
                    if damage>0 and not _mec_disable_critical:
                        damage, critical = self.roll_critical_hit(damage)
                    else:
                        critical=False
                else:
                    damage = max(
                        1,
                        int(core_power * multiplier) + random.randint(-2, 3),
                    )
                    damage, critical = self.roll_critical_hit(damage)
                if critical:
                    self.record_social_record_v03051("biggest_crit", damage)
                    if (
                        skill.get("mec_authored")
                        and str(skill.get("mec_special",""))=="crosshair"
                    ):
                        await self.send(
                            f"TRAFIENIE KRYTYCZNE umiejętnością Crosshair! "
                            f"Szansa krytyka: "
                            f"{int(round(self.critical_chance() * 100))} procent."
                        )
                    else:
                        await self.send(
                            f"TRAFIENIE KRYTYCZNE umiejętnością "
                            f"{skill['name']}! Zręczność "
                            f"{self.effective_dexterity()}. "
                            f"Szansa: "
                            f"{int(round(self.critical_chance() * 100))} procent."
                        )
                if damage>0 and not _mec_percent_damage_exact:
                    damage = await self.apply_boss_defense(mob, damage)
                    damage = self.v0210_adjust_player_damage(damage)
                    _damage_element="physical" if skill_class_type == "physical" else "magic"
                    if skill.get("mec_authored") and skill.get("carries_soul_weapon_elements"):
                        _sw_element=str(getattr(self.character,"soul_weapon_element","") or "").casefold()
                        if _sw_element: _damage_element=_sw_element
                    damage, machine_note = v0314_adjust_damage_vs_template(
                        template, damage, _damage_element, skill.get("name", ""),
                    )
                elif damage>0:
                    # Compress is explicitly percentage-of-target-HP damage. Do not
                    # turn that percentage into ordinary STR/Attack damage afterward.
                    machine_note=""
                else:
                    machine_note=""
                mob.hp -= damage
                if (
                    skill.get("mec_authored")
                    and str(skill.get("mec_special",""))=="mec_sonata"
                    and mob.hp>0
                ):
                    # Source confirms only a chance to temporarily lower target level
                    # and Extendable. Chance, amount and duration are not numeric in
                    # UOSS, so these are explicit Soulbound balance values.
                    _sonata_proc=float(
                        skill.get("soulbound_level_reduction_proc_chance",0.30) or 0.30
                    )
                    if random.random() < _sonata_proc:
                        _sonata_rounds=max(
                            1,int(skill.get("soulbound_level_reduction_rounds",3) or 3)
                        )
                        _existing=max(
                            0,int(getattr(mob,"v11196_mec_sonata_rounds",0) or 0)
                        )
                        mob.v11196_mec_sonata_rounds=_existing+_sonata_rounds
                        mob.v11196_mec_sonata_power_mult=max(
                            0.01,min(
                                1.0,
                                float(
                                    skill.get(
                                        "soulbound_level_equivalent_power_multiplier",0.90
                                    ) or 0.90
                                ),
                            )
                        )
                        await self.send(
                            f"Mec Sonata: poziomowa moc {template['name']} spada tymczasowo. "
                            f"Efekt potrwa {mob.v11196_mec_sonata_rounds} akcji przeciwnika."
                        )
                _helper_skill_damage = 0
                if mob.hp > 0:
                    _helper_skill_damage = await self.apply_superboss_helper_skill_damage_v11189(mob)
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

                self_damage = int(_mec_feedback_self_damage or 0) + skill.get("self_damage", 0)
                if skill.get("self_damage_pct"):
                    self_damage += max(1, int(self.max_hp() * skill["self_damage_pct"]))
                if self_damage:
                    self.current_hp -= self_damage
                    if skill.get("mec_branch")=="feedback" or skill.get("feedback_damage"):
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

