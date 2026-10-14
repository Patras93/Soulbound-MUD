# -*- coding: utf-8 -*-
"""Original Soulbound session/DB method bodies, source-preserving extraction.
Globals are bound to the historical host module at class initialization.
"""
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
    """Canonical physical/magic/feedback scaling channel for damaging skills.

    Mec Feedback is intentionally independent from ordinary physical damage:
    it keeps its own HP/Vitality/Attack mechanics, Feedback Protocol and
    shield interactions instead of inheriting physical-only multipliers.
    """
    if skill.get("mec_authored"):
        branch = str(skill.get("mec_branch", "") or "").strip().lower()
        if branch == "magic":
            return "magic"
        if branch == "feedback":
            return "feedback"
        if branch in {"melee", "ranged"}:
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
    stat_power = character_attribute_power(level, raw_stat)
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
        secondary_power = character_attribute_power(
            int(self.character.character_level), secondary_value
        )

    # A secondary source influence is deliberately smaller than the primary.
    # Cosmic Rave, for example, is Attack-led per source while Agility/DEX
    # from the actual build and equipment contributes to a lesser degree.
    secondary_weight = 0.35 if secondary_name else 0.0
    weighted_stat = primary_value + secondary_value * secondary_weight
    build_multiplier = character_offensive_build_multiplier(weighted_stat)

    soul_power = max(0, int(self.character.soul_power()))
    core = (
        int(authored_base or 0)
        + soul_power
        + stat_power
        + int(round(secondary_power * secondary_weight))
    )
    return max(1, int(round(core * build_multiplier)))


def healing_skill_build_multiplier_v11196(self, skill):
    """Uncapped healing growth from the canonical INT + WILL support build.

    v1.12.5: every healing ability uses the same two healing stats.
    Skill-specific identity still comes from authored heal_pct/base behavior,
    Skill Level, class/race multipliers and special effects; Magic Attack
    remains exclusive to magic damage.
    """
    level = int(self.character.character_level)
    anchor_power = max(
        1,
        int(character_attribute_power(level, 175)),
    )
    canonical_power = max(1, int(self.healing_power_v1125()))
    return max(
        0.20,
        (float(canonical_power) / float(anchor_power)) ** 0.72,
    )


def healing_skill_amount_v11196(self, skill, target, skill_power):
    """Canonical class-heal amount from INT + WILL + Skill Level + EQ.

    Authored percentage heals preserve their identity, but their potency is
    multiplied by the uncapped INT+WILL healing build. Source abilities
    without an authored percentage use the same canonical INT+WILL core.
    """
    racial = float(self.character.racial_healing_multiplier())
    class_mult = float(self.character.class_healing_multiplier())
    heal_type = class_type_for_name(self.skill_class_name(skill))
    buff_mult = float(self.skill_buff_multiplier(target_type=heal_type))
    build_mult = float(self.healing_skill_build_multiplier_v11196(skill))
    total_mult = (
        max(0.0, float(skill_power))
        * racial
        * class_mult
        * buff_mult
        * build_mult
        * party_synergy_healing_multiplier_v11338(self)
    )

    authored_pct = skill.get("heal_pct")
    if authored_pct is not None:
        return max(1, int(round(target.max_hp() * max(0.0, float(authored_pct)) * total_mult)))

    # Flat heals use the same canonical support power as percentage heals:
    # INT + WILL from character progression and all equipped stat bonuses.
    stat_core = max(1, int(self.healing_power_v1125()))
    return max(1, int(round(stat_core * total_mult)))


def regen_tick_power_v11196(self, skill_level):
    """Small periodic support heal from INT + WILL."""
    healing_power=max(1,int(self.healing_power_v1125()))
    power=float(skill_power_multiplier(max(1,min(SKILL_MAX_LEVEL,int(skill_level)))))
    racial=float(self.character.racial_healing_multiplier())
    class_mult=float(self.character.class_healing_multiplier())
    return max(
        1,
        int(round(
            healing_power
            * 0.10
            * power
            * racial
            * class_mult
            * party_synergy_healing_multiplier_v11338(self)
        )),
    )


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
    damage,_reaction_note_v11339,_reaction_element_v11339 = (
        party_synergy2_apply_hit_v11339(
            self, target, self.skill_class_name(skill),
            skill.get("name","Satellite Linker"), damage, "physical"
        )
    )
    note=(note or "")+_reaction_note_v11339
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
    """Global multiplier path with separate physical, magic and Feedback roles.

    Physical receives physical-only class/race/EQ bonuses. Magic receives
    magic-only class/race/EQ bonuses. Mec Feedback is a third channel: its
    authored HP/Vitality/Attack/shield mechanics remain primary, while only
    all-damage/set/general buffs apply here. This prevents Feedback from
    silently becoming ordinary physical damage.
    """
    resolved_type = skill_class_type or self.offensive_skill_damage_type_v11190(skill)
    multiplier = float(skill.get("mult", 1.0))
    if resolved_type == "physical":
        multiplier *= self.character.class_physical_damage_multiplier()
        multiplier *= self.character.racial_physical_damage_multiplier()
    elif resolved_type == "magic":
        multiplier *= self.character.class_magic_damage_multiplier()
        multiplier *= self.character.racial_magic_damage_multiplier()
    multiplier *= self.character.racial_all_damage_multiplier()
    multiplier *= self.total_set_damage_multiplier()
    multiplier *= self.equipment_damage_multiplier(resolved_type)
    multiplier *= self.skill_buff_multiplier(target_type=resolved_type)
    multiplier *= party_synergy_damage_multiplier_v11338(self, resolved_type)
    return multiplier


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

