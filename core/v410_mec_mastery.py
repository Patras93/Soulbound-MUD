# -*- coding: utf-8 -*-
"""Authored historical functions; bound to their original globals by the facade.

No gameplay data or runtime namespace is instantiated in this module.
"""

def _v0319_install_full_mec_kit():
    rows = CLASS_SKILLS.get("Mec", [])
    specs = [
        # Melee
        ("Hammer Crush",1,"damage",200,"melee","hammer_crush","Attack-based heavy smash against one enemy. Carries the active Soul Weapon element and uses the Mec melee Soul Weapon role."),
        ("Shock Soldier",14,"aoe_damage",600,"melee","shock_soldier","Attack-based melee barrage against all enemies with diminishing damage. Carries the active Soul Weapon element and uses the Mec melee Soul Weapon role."),
        ("Plural Slash",32,"damage",900,"melee","plural_slash","Attack-led multi-slash against one enemy. Agility/DEX adds a smaller damage contribution to every slash even for strength-oriented melee builds. Carries the active Soul Weapon element."),
        ("Pop Knight",46,"aoe_damage",1500,"melee","pop_knight","Attack-based non-diminishing melee attack on all enemies. Carries the active Soul Weapon element and deals extra damage to enemies explicitly marked Flying."),
        ("Tiger Rampage",80,"damage",1800,"melee","tiger_rampage","Attack-based two-hit melee assault against one enemy. Carries the active Soul Weapon element and can lower both physical and magical defenses; the defense break is Extendable."),
        ("Cosmic Rave",110,"aoe_damage",2000,"melee","cosmic_rave","Hits all enemies with diminishing damage; during V-MAX targets random enemies instead. Attack is the primary influence and Agility provides a lesser secondary damage contribution."),
        # Ranged
        ("Crosshair",1,"damage",200,"ranged","crosshair","One-enemy ranged attack influenced by Attack and Critical Hit Chance. It attempts to deliver a critical hit and carries the active Soul Weapon element."),
        ("Range Fire",8,"aoe_damage",500,"ranged","range_fire","Attack-based ranged barrage against all enemies at full non-diminishing power. Carries the active Soul Weapon element."),
        ("Dispose",32,"aoe_damage",1000,"ranged","dispose","Attack-based heavy-duty laser barrage against all enemies at full non-diminishing power. Carries the active Soul Weapon element and inflicts Feedback damage on the Mec after the attack."),
        ("Satellite Linker",44,"damage",1200,"ranged","satellite_linker","Laser bits hover around one enemy and repeatedly deal minor damage for a short period. Attack and Wisdom influence damage; higher Skill Level makes the bits operate longer."),
        ("Magnify",90,"damage",1500,"ranged","magnify","One-enemy weapon-overload attack influenced by Attack and Wisdom. Wisdom magnifies damage; Skill Level and Wisdom reduce the chance of systems failure. Failure causes weapon Overheat/reboot. Requires the Mec ranged Soul Weapon role."),
        ("Shoot-All",110,"aoe_damage",2000,"ranged","shoot_all","Fires all ammunition at all enemies; V-MAX increases damage and crit."),
        # Feedback
        ("Destroy",1,"damage",200,"feedback","destroy","One-enemy Feedback attack influenced by HP, Vitality and Attack. A shield improves damage and the attack becomes stronger as HP decreases."),
        ("Robo Tackle",20,"damage",500,"feedback","robo_tackle","One-enemy tackle influenced by HP before use, Vitality and Attack. Damage falls as current HP falls; a shield improves damage. V-MAX increases both attack power and Feedback damage."),
        ("Compress",30,"damage",600,"feedback","compress","One-enemy compression attempt influenced by Vitality and HP. On success it deals a percentage of the target current HP; full HP and an equipped shield increase compression power. Skill Level increases accuracy and the attack causes Feedback."),
        ("Crush",46,"damage",1000,"feedback","crush","One-enemy Feedback attack based on the difference between maximum and current HP. Character Level limits the damage capacity, Skill Level raises the maximum possible damage, and an equipped shield increases that capacity."),
        ("Uzi Punch",95,"aoe_damage",1400,"feedback","uzi_punch","Random-enemy machinegun punch influenced by HP, Vitality and Attack. Feedback damages the Mec, a shield improves damage, and the attack becomes stronger as HP decreases."),
        ("Kamikaze Crush",110,"damage",2000,"feedback","kamikaze_crush","One-enemy lethal divebomb influenced by HP before use, Vitality and Attack. Damage falls as current HP falls; an equipped shield improves damage. V-MAX increases both attack power and Feedback damage."),
        # Magic
        ("Laser Spin",1,"aoe_damage",200,"magic","laser_spin","Magic Attack-based Dark laser assault against all enemies with diminishing damage. Source requirements: none; Properties: none."),
        ("Area Bomb",8,"aoe_damage",300,"magic","area_bomb","Magic Attack-based Fire explosion against all targeted enemies currently engaged in combat. Source Properties: none; no separate Burn status is specified."),
        ("Mec Sonata",20,"damage",1000,"magic","mec_sonata","One-enemy Magic Attack song with a chance to lower the target level-equivalent power temporarily. The level-lowering effect is Extendable."),
        ("Maelstrom",44,"aoe_damage",1500,"magic","maelstrom","Magic Attack-based Water vortex against all enemies with diminishing damage. Source Properties: none."),
        ("Shock",95,"aoe_damage",1800,"magic","shock","Magic Attack-based Lightning + Dark surge against all enemies with diminishing damage. Source Properties: none."),
        ("Starlight Shower",110,"damage",2000,"magic","starlight_shower","Magic Attack laser barrage: one enemy when fighting one target; diminishing damage to all combat targets when fighting several; V-MAX hits all enemies without diminishing."),
        # Support
        ("Cure Beam",1,"heal",100,"support","cure_beam","Single-target healing beam available from the start. Willpower and Skill Level increase healing. Support Effect increases healing and removes Blind and Poison."),
        ("Hypno Flash",16,"damage",300,"support","hypno_flash","Attempts to put one enemy to Sleep. Will and Skill Level improve accuracy and duration; the Mec support weapon improves hit chance. Sleep is Cleanseable and Extendable."),
        ("Jammer",32,"damage",750,"support","jammer","Attempts to Stop one enemy, or all enemies while the Mec support weapon is active. Will and Skill Level improve accuracy and duration; mechanical enemies are easier to affect. Stop is Cleanseable and Extendable. Soulbound bosses and minibosses are immune to Jammer Stop."),
        ("Heal Beam",54,"heal",1000,"support","heal_beam","Significant Willpower-based healing. Normally heals one target; Support Effect heals the entire local party for an enhanced amount."),
        ("Logic Bomb",92,"damage",1200,"support","logic_bomb","Attempts to infect one enemy with Paralyze, Silence and Slow. With the Mec support weapon it also attempts Blind, Curse and Immobilize. Will and Skill Level improve accuracy and duration; Machine targets are easier to affect."),
        ("V-MAX",130,"boost",2000,"support","vmax","Will-influenced core overdrive: Protect, Shell, Haste, Regen, Preach, Praise, Permanence; changes several Mec skills. When it ends, Overheat is prevented while the Mec's Soul Weapon remains the active support weapon."),
        # Counter
        ("Intercept System",75,"passive",1000,"counter","intercept_system","Selected Counter that interrupts an incoming enemy attack and answers with laser-guided damage using the highest available offensive stat. Skill Level increases counter damage."),
        # Inherent
        ("Self-Repair",1,"passive",1000,"inherent","self_repair","Automatically restores Feedback self-damage after 3 owner rounds. Source also grants Auto-Regen, but no numeric Auto-Regen amount is supplied, so Soulbound does not fabricate one."),
        ("Combat Mastery",30,"passive",1000,"inherent","combat_mastery","Selected inherent. Increases ordinary Mec Soul Weapon attack damage in its pure Strength/melee role; does not work unarmed. Source: stronger than Attack UP but weaker than Two Hands."),
        ("Maxwell Program",30,"passive",1000,"inherent","maxwell_program","Augments Magic Attack and regenerates 1% of maximum MP every 6 seconds."),
        ("Shooting Mastery",30,"passive",1000,"inherent","shooting_mastery","Automatic inherent from Level 30. Soulbound uses one Soul Weapon: Shooting Mastery strengthens its Dexterity/ranged damage component without requiring a separate ranged weapon; stronger than ordinary Attack UP."),
        # Passive protocols
        ("Strength Protocol",1,"passive",2000,"passive","strength_protocol","Passively increases damage of Mec melee/Strength skills. Scales with this skill level."),
        ("Ranged Protocol",1,"passive",2000,"passive","ranged_protocol","Passively increases damage of Mec ranged/Dexterity shooting skills. Scales with this skill level."),
        ("Feedback Protocol",1,"passive",2000,"passive","feedback_protocol","Automatic protocol. Skill Level increases damage of Destroy, Robo Tackle, Uzi Punch and Kamikaze Crush."),
        ("Magic Protocol",1,"passive",2000,"passive","magic_protocol","Passively increases damage of Mec magic/Intelligence skills. Scales with this skill level."),
    ]
    if len(rows) < len(specs):
        return
    for idx,(name,unlock,kind,source_ap,branch,special,desc) in enumerate(specs):
        row=rows[idx]
        row.clear()
        row.update({
            "id":f"v0319_mec_{special}", "name":name, "aliases":[name.casefold()],
            "unlock":unlock, "kind":kind, "cooldown":0, "mana":0,
            "base_power":0,
            "source_ap_cost":source_ap,
            "source_ap_semantics":"learning_points",
            "source_ap_is_damage_power":False,
            "mec_authored":True, "mec_branch":branch,
            "mec_special":special, "desc":desc,
        })
        if branch in ("inherent","counter"):
            row["mec_role"]=branch
        if kind in ("damage","aoe_damage"):
            row["scale"] = (
                "intelligence" if branch=="magic"
                else "dexterity" if branch=="ranged"
                else "willpower" if branch=="support"
                else "strength"
            )
            row["mult"] = 1.0
            if kind=="aoe_damage": row["aoe"]=True
        if kind=="heal": row["healing_power_from_will_and_skill_level"]=True
        if special in {"strength_protocol","ranged_protocol","feedback_protocol","magic_protocol"}:
            row.update({
                "automatic":True,
                "level_effect":"increases_mapped_skill_damage",
                "protocol_multiplier_level1":1.05,
                "protocol_multiplier_level600":1.75,
                "protocol_numeric_source_defined":False,
                "protocol_balance_curve":"soulbound_1.05_to_1.75_power_0.82",
            })
        if special=="feedback_protocol":
            row.update({
                "source_level_effect_skills":[
                    "destroy","robo_tackle","uzi_punch","kamikaze_crush"
                ],
            })
        if special=="destroy":
            row.update({
                "scale":"attack",
                "secondary_scale":"constitution",
                "source_stat_influence":["hp","vitality","attack"],
                "source_properties":[],
                "target_mode":"one_enemy",
                "feedback_damage":True,
                "feedback_cost_source_defined":False,
                "shield_improves_damage":True,
                "power_increases_as_hp_decreases":True,
                "numeric_source_defined":False,
                "missing_hp_max_damage_bonus":0.50,
                "shield_damage_multiplier":1.10,
                "feedback_max_hp_pct":0.06,
                "balance_model":"soulbound_missinghp50_shield110_feedback6pct",
                "single_soul_weapon":True,
            })
        if special=="robo_tackle":
            row.update({
                "scale":"attack",
                "secondary_scale":"constitution",
                "source_stat_influence":["hp","vitality","attack"],
                "source_properties":[],
                "target_mode":"one_enemy",
                "damage_from_current_hp":True,
                "vitality_influence":True,
                "feedback_damage":True,
                "feedback_cost_source_defined":False,
                "shield_improves_damage":True,
                "vmax_power_and_feedback":True,
                "numeric_source_defined":False,
                "current_hp_power_ratio":0.12,
                "shield_damage_multiplier":1.15,
                "vmax_damage_multiplier":1.20,
                "feedback_current_hp_pct":0.10,
                "vmax_feedback_current_hp_pct":0.25,
                "balance_model":"soulbound_hp12_shield115_vmax120_feedback10_25",
                "single_soul_weapon":True,
            })
        if special=="compress":
            row.update({
                "scale":"target_current_hp_percent",
                "source_stat_influence":["vitality","hp"],
                "source_properties":[],
                "target_mode":"one_enemy",
                "percentage_target_hp_damage":True,
                "percentage_uses_current_hp":True,
                "level_effect":"increases_accuracy",
                "vitality_influence":True,
                "full_hp_increases_power":True,
                "shield_increases_compressing_power":True,
                "feedback_damage":True,
                "feedback_cost_source_defined":False,
                "numeric_source_defined":False,
                "base_accuracy":0.65,
                "skill_level_accuracy_bonus_max":0.30,
                "vitality_accuracy_bonus_anchor":0.05,
                "base_target_current_hp_pct":0.20,
                "full_hp_damage_pct_bonus":0.10,
                "shield_damage_pct_bonus":0.10,
                "vitality_damage_pct_anchor":0.05,
                "max_target_current_hp_pct":0.60,
                "feedback_max_hp_pct":0.08,
                "balance_model":"soulbound_currenthp20_fullhp10_shield10_vit5_cap60_acc65_95_feedback8",
                "single_soul_weapon":True,
            })
        if special=="uzi_punch":
            row.update({
                "scale":"attack",
                "secondary_scale":"constitution",
                "source_stat_influence":["hp","vitality","attack"],
                "source_properties":[],
                "target_mode":"random_enemies",
                "feedback_damage":True,
                "feedback_cost_source_defined":False,
                "shield_improves_damage":True,
                "power_increases_as_hp_decreases":True,
                "numeric_source_defined":False,
                "random_target_count_source_defined":False,
                "random_target_fraction":0.50,
                "missing_hp_max_damage_bonus":0.75,
                "shield_damage_multiplier":1.20,
                "feedback_max_hp_pct":0.12,
                "balance_model":"soulbound_random_half_missinghp75_shield120_feedback12pct",
                "single_soul_weapon":True,
            })
        if special=="crush":
            row.update({
                "scale":"hp_difference",
                "source_stat_influence":["hp","level"],
                "source_properties":[],
                "target_mode":"one_enemy",
                "damage_from_missing_hp":True,
                "level_caps_damage":True,
                "level_effect":"increases_maximum_possible_damage",
                "shield_increases_capacity":True,
                "feedback_damage":True,
                "feedback_cost_source_defined":False,
                "numeric_source_defined":False,
                "capacity_per_character_level":100,
                "capacity_per_skill_level":25,
                "shield_capacity_multiplier":1.25,
                "feedback_source_damage_pct":0.15,
                "balance_model":"soulbound_cap_level100_skill25_shield125_feedback15pct",
                "single_soul_weapon":True,
            })
        if special=="kamikaze_crush":
            row.update({
                "scale":"attack",
                "secondary_scale":"constitution",
                "source_stat_influence":["hp","vitality","attack"],
                "source_properties":[],
                "target_mode":"one_enemy",
                "damage_from_current_hp":True,
                "vitality_influence":True,
                "shield_improves_damage":True,
                "vmax_power_and_feedback":True,
                "numeric_source_defined":False,
                "current_hp_power_ratio":0.20,
                "shield_damage_multiplier":1.20,
                "vmax_damage_multiplier":1.30,
                "feedback_current_hp_pct":0.20,
                "vmax_feedback_current_hp_pct":0.45,
                "balance_model":"soulbound_hp20_shield120_vmax130_feedback20_45",
                "single_soul_weapon":True,
            })
        if special=="self_repair": row.update({"feedback_repair_rounds":3,"auto_regen_source_defined":True,"auto_regen_amount_source_defined":False})
        if special=="maxwell_program": row.update({"magic_attack_augmentation":True,"mp_regen_percent":1.0,"mp_regen_seconds":6.0})
        if special=="combat_mastery":
            row.update({
                "ordinary_soul_weapon_attack_only":True,
                "strength_based_only":True,
                "requires_soul_weapon":True,
                "source_weapon_types":[
                    "axe","claw","greatsword","hammer","katana",
                    "lance","rod","staff","sword"
                ],
                "does_not_work_unarmed":True,
                "stronger_than":"Attack UP",
                "weaker_than":"Two Hands",
                "numeric_source_defined":False,
                "soulbound_damage_multiplier":1.20,
                "soulbound_weapon_model":"mec_soul_weapon_melee_strength_role",
                "balance_model":"soulbound_x1.20_relative_between_attack_up_and_two_hands",
                "single_soul_weapon":True,
            })
        if special=="hammer_crush":
            row.update({
                "scale":"attack",
                "source_stat_influence":["attack"],
                "source_properties":["carries_elements"],
                "target_mode":"one_enemy",
                "attack_influence":True,
                "carries_soul_weapon_elements":True,
                "requires_soul_weapon":"melee",
                "single_soul_weapon":True,
            })
        if special=="cosmic_rave": row.update({"aoe_diminishing":True,"vmax_random_enemies":True,"agility_secondary_influence":True,"carries_soul_weapon_elements":True,"single_soul_weapon":True})
        if special=="plural_slash":
            row.update({
                "scale":"attack",
                "secondary_scale":"dexterity",
                "source_stat_influence":["attack","agility"],
                "source_properties":["carries_elements"],
                "target_mode":"one_enemy",
                "multi_slash":True,
                "multi_hit_count_source_defined":False,
                "agility_secondary_influence":True,
                "secondary_numeric_weight_source_defined":False,
                "carries_soul_weapon_elements":True,
                "requires_soul_weapon":"melee",
                "single_soul_weapon":True,
                "balance_model":"attack_primary_plus_global_secondary_dex35pct",
            })
        if special=="shock_soldier":
            row.update({
                "scale":"attack",
                "source_stat_influence":["attack"],
                "source_properties":["carries_elements"],
                "target_mode":"all_enemies_diminishing",
                "aoe_diminishing":True,
                "diminishing_numeric_source_defined":False,
                "soulbound_diminishing_model":"inverse_sqrt_target_count",
                "carries_soul_weapon_elements":True,
                "requires_soul_weapon":"melee",
                "single_soul_weapon":True,
            })
        if special=="range_fire":
            row.update({
                "scale":"attack",
                "source_stat_influence":["attack"],
                "source_properties":["carries_elements"],
                "target_mode":"all_enemies_non_diminishing",
                "aoe_non_diminishing":True,
                "carries_soul_weapon_elements":True,
                "requires_soul_weapon":"ranged",
                "single_soul_weapon":True,
            })
        if special=="dispose":
            row.update({
                "scale":"attack",
                "source_stat_influence":["attack"],
                "source_properties":["carries_elements"],
                "target_mode":"all_enemies_non_diminishing",
                "aoe_non_diminishing":True,
                "carries_soul_weapon_elements":True,
                "requires_soul_weapon":"ranged",
                "feedback_damage":True,
                "feedback_cost_source_defined":False,
                "soulbound_feedback_max_hp_pct":0.08,
                "feedback_once_per_cast":True,
                "feedback_repair_eligible":True,
                "single_soul_weapon":True,
                "balance_model":"soulbound_feedback_8pct_maxhp_once_per_cast",
            })
        if special=="crosshair":
            row.update({
                "scale":"attack",
                "source_stat_influence":["attack","critical_hit_chance"],
                "source_properties":["carries_elements"],
                "target_mode":"one_enemy",
                "critical_chance_influence":True,
                "attempts_critical":True,
                "critical_model":"character_critical_hit_chance",
                "carries_soul_weapon_elements":True,
                "requires_soul_weapon":"ranged",
                "single_soul_weapon":True,
            })
        if special=="magnify":
            row.update({
                "scale":"attack",
                "secondary_scale":"intelligence",
                "source_stat_influence":["attack","wisdom"],
                "source_properties":["cooldown"],
                "target_mode":"one_enemy",
                "wisdom_magnifies_damage":True,
                "skill_level_reduces_system_failure":True,
                "wisdom_reduces_system_failure":True,
                "systems_failure_causes_overheat_reboot":True,
                "requires_soul_weapon":"ranged",
                "single_soul_weapon":True,
                "numeric_cooldown_source_defined":False,
                "source_cooldown_property_runtime_reuse_timer":False,
                "systems_failure_numeric_source_defined":False,
                "soulbound_failure_base_chance":0.35,
                "soulbound_skill_failure_reduction_max":0.20,
                "soulbound_wisdom_failure_reduction_anchor":0.06,
                "soulbound_wisdom_failure_reduction_max":0.12,
                "soulbound_failure_chance_floor":0.02,
                "soulbound_reboot_recovery_actions":1,
                "balance_model":"soulbound_failure35_skillminus20_wisminus12_floor2_one_recovery_action",
            })
        if special=="satellite_linker":
            row.update({
                "scale":"attack",
                "secondary_scale":"intelligence",
                "source_stat_influence":["attack","wisdom"],
                "source_properties":[],
                "target_mode":"one_enemy",
                "periodic_damage":True,
                "minor_damage_over_time":True,
                "wisdom_increases_damage":True,
                "level_effect":"increases_duration",
                "duration_source_defined":False,
                "tick_cadence_source_defined":False,
                "tick_damage_source_defined":False,
                "soulbound_tick_every_owner_rounds":1,
                "soulbound_duration_rounds_level1":3,
                "soulbound_duration_rounds_level600":8,
                "soulbound_tick_damage_multiplier":0.20,
                "soulbound_single_active_link":True,
                "balance_model":"soulbound_tick20pct_every_round_duration3_to_8",
                "single_soul_weapon":True,
            })
        if special=="shoot_all":
            row.update({
                "scale":"attack",
                "source_stat_influence":["attack","critical_hit_chance"],
                "target_mode":"all_enemies_non_diminishing",
                "aoe_non_diminishing":True,
                "critical_chance_influence":True,
                "attempts_critical":True,
                "vmax_increases_critical_and_damage":True,
                "vmax_numeric_source_defined":False,
                "vmax_damage_multiplier":1.25,
                "vmax_critical_chance_bonus":0.15,
                "vmax_balance_model":"soulbound_damage_x1.25_crit_plus15pp",
                "carries_soul_weapon_elements":True,
                "requires_soul_weapon":"ranged",
                "single_soul_weapon":True,
            })
        if special=="laser_spin":
            row.update({
                "scale":"intelligence",
                "source_stat_influence":["magic_attack"],
                "magic_attack_influence":True,
                "source_properties":[],
                "source_requirements":[],
                "source_requires_none":True,
                "target_mode":"all_enemies_diminishing",
                "aoe_diminishing":True,
                "element":"dark",
                "uoss_mp_cost":25,
            })
        if special=="mec_sonata":
            row.update({
                "scale":"intelligence",
                "source_stat_influence":["magic_attack"],
                "magic_attack_influence":True,
                "uoss_mp_cost":50,
                "source_properties":["extendable"],
                "target_mode":"one_enemy",
                "soulbound_target_scope":"enemy_only",
                "soulbound_harmful_debuff":True,
                "enemy_debuffs":["level_equivalent_power_down"],
                "temporary_level_reduction_chance":True,
                "level_reduction_extendable":True,
                "level_reduction_numeric_source_defined":False,
                "level_reduction_duration_source_defined":False,
                "level_reduction_chance_source_defined":False,
                "soulbound_level_reduction_proc_chance":0.30,
                "soulbound_level_equivalent_power_multiplier":0.90,
                "soulbound_level_reduction_rounds":3,
                "balance_model":"soulbound_proc30_levelpower90_3rounds_extendable",
            })
        if special=="maelstrom":
            row.update({
                "scale":"intelligence",
                "source_stat_influence":["magic_attack"],
                "magic_attack_influence":True,
                "source_properties":[],
                "source_requirement_level":44,
                "source_requirement_maps_to":"class_mastery",
                "target_mode":"all_enemies_diminishing",
                "aoe_diminishing":True,
                "diminishing_numeric_source_defined":False,
                "soulbound_diminishing_model":"inverse_sqrt_target_count",
                "element":"water",
                "uoss_mp_cost":80,
            })
        if special=="shock":
            row.update({
                "scale":"intelligence",
                "source_stat_influence":["magic_attack"],
                "magic_attack_influence":True,
                "source_properties":[],
                "source_requirement_level":95,
                "source_requirement_maps_to":"class_mastery",
                "target_mode":"all_enemies_diminishing",
                "aoe_diminishing":True,
                "diminishing_numeric_source_defined":False,
                "soulbound_diminishing_model":"inverse_sqrt_target_count",
                "elements":["lightning","dark"],
                "uoss_mp_cost":150,
            })
        if special=="tiger_rampage":
            row.update({
                "scale":"attack",
                "source_stat_influence":["attack"],
                "source_properties":["carries_elements","extendable"],
                "hits":2,
                "target_mode":"one_enemy",
                "soulbound_target_scope":"enemy_only",
                "soulbound_harmful_debuff":True,
                "enemy_debuffs":["physical_defense_down","magic_defense_down"],
                "carries_soul_weapon_elements":True,
                "requires_soul_weapon":"melee",
                "single_soul_weapon":True,
                "extendable":True,
                "defense_break_physical":True,
                "defense_break_magical":True,
                "defense_break_chance_source_defined":False,
                "defense_break_duration_source_defined":False,
                "defense_break_amount_source_defined":False,
                "soulbound_defense_break_proc_chance":0.35,
                "soulbound_defense_break_rounds":4,
                "soulbound_defense_break_damage_multiplier":1.15,
                "balance_model":"soulbound_proc35_break4_incoming_damage_x1.15_extendable",
            })
        if special=="area_bomb":
            row.update({
                "scale":"intelligence",
                "source_stat_influence":["magic_attack"],
                "magic_attack_influence":True,
                "source_properties":[],
                "source_requirement_level":8,
                "source_requirement_maps_to":"class_mastery",
                "target_mode":"all_targetted_enemies",
                "engaged_only":True,
                "aoe_diminishing":False,
                "element":"fire",
                "uoss_mp_cost":35,
                "burn_status_source_defined":False,
            })
        if special=="pop_knight":
            row.update({
                "scale":"attack",
                "source_stat_influence":["attack"],
                "source_properties":["carries_elements"],
                "target_mode":"all_enemies_non_diminishing",
                "aoe_non_diminishing":True,
                "carries_soul_weapon_elements":True,
                "requires_soul_weapon":"melee",
                "bonus_vs_flying":True,
                "flying_template_flag":"flying",
                "bonus_vs_flying_source_defined":True,
                "flying_bonus_numeric_source_defined":False,
                "soulbound_flying_damage_multiplier":1.25,
                "single_soul_weapon":True,
                "balance_model":"soulbound_flying_x1.25",
            })
        if special=="hypno_flash":
            row.update({
                "scale":"willpower",
                "source_stat_influence":["will"],
                "uoss_mp_cost":15,
                "source_properties":["cleanseable","extendable"],
                "target_mode":"one_enemy",
                "soulbound_target_scope":"enemy_only",
                "soulbound_harmful_debuff":True,
                "enemy_debuffs":["sleep"],
                "control_effect":"sleep",
                "level_effect":"increases_accuracy_and_duration",
                "support_weapon_improves_accuracy":True,
                "cleanseable":True,
                "extendable":True,
                "accuracy_numeric_source_defined":False,
                "duration_numeric_source_defined":False,
                "soulbound_base_accuracy":0.55,
                "soulbound_skill_accuracy_bonus_max":0.25,
                "soulbound_will_accuracy_bonus_max":0.15,
                "soulbound_support_accuracy_bonus":0.10,
                "soulbound_accuracy_cap":0.98,
                "soulbound_duration_rounds_level1":2,
                "soulbound_duration_rounds_level600":6,
                "soulbound_will_duration_bonus_max":2,
                "balance_model":"soulbound_acc55_skill25_will15_support10_cap98_duration2_to_6_plus_will2",
            })
        if special=="heal_beam":
            row.update({
                "scale":"willpower",
                "source_stat_influence":["will"],
                "source_properties":[],
                "source_requirement_level":54,
                "source_requirement_maps_to":"class_mastery",
                "source_target_mode":["one_target","party"],
                "uoss_mp_cost":36,
                "uoss_support_mp_cost":72,
                "target_mode":"one_ally_or_support_party",
                "soulbound_enemy_heal_disabled":True,
                "level_effect":"increases_healing_power",
                "heal_pct":0.50,
                "healing_numeric_source_defined":False,
                "support_weapon_expands_to_party":True,
                "support_heal_multiplier":1.20,
                "support_heal_numeric_source_defined":False,
                "support_effect_requires_support_weapon":True,
                "healing_balance_model":"uncapped_will_skill_eq",
            })
        if special=="cure_beam":
            row.update({
                "scale":"willpower",
                "source_stat_influence":["will"],
                "source_properties":[],
                "source_requirements":[],
                "source_requires_none":True,
                "uoss_mp_cost":10,
                "source_target_mode":["self","one_ally","one_enemy"],
                "target_mode":"self_or_one_ally",
                "soulbound_enemy_heal_disabled":True,
                "level_effect":"increases_healing_power",
                "heal_pct":0.30,
                "healing_numeric_source_defined":False,
                "support_heal_multiplier":1.20,
                "support_heal_numeric_source_defined":False,
                "support_cleanses":["blind","poison"],
                "support_effect_requires_support_weapon":True,
                "healing_balance_model":"uncapped_will_skill_eq",
            })
        if special=="jammer":
            row.update({
                "scale":"willpower",
                "source_stat_influence":["will"],
                "control_effect":"stop",
                "source_properties":["cleanseable","extendable"],
                "cleanseable":True,
                "extendable":True,
                "uoss_mp_cost":20,
                "uoss_support_mp_cost":40,
                "target_mode":"one_or_support_all_enemies",
                "soulbound_target_scope":"enemy_only",
                "soulbound_harmful_debuff":True,
                "enemy_debuffs":["stop"],
                "support_weapon_expands_to_all_enemies":True,
                "uoss_superboss_stop_immune":True,
                "machine_accuracy_bonus":True,
                "level_effect":"increases_accuracy_and_duration",
                "accuracy_numeric_source_defined":False,
                "duration_numeric_source_defined":False,
                "machine_bonus_numeric_source_defined":False,
                "soulbound_base_accuracy":0.50,
                "soulbound_skill_accuracy_bonus_max":0.25,
                "soulbound_will_accuracy_bonus_max":0.15,
                "soulbound_machine_accuracy_bonus":0.15,
                "soulbound_accuracy_cap":0.98,
                "soulbound_duration_rounds_level1":8,
                "soulbound_duration_rounds_level600":16,
                "soulbound_will_duration_bonus_max":4,
                "duration_user_benchmark":{"skill_level":9,"observed_actions":8},
                "balance_model":"user_anchor_skill9_about8_then_soulbound_8_to_16_plus_will4",
            })
        if special=="logic_bomb":
            row.update({
                "scale":"willpower",
                "source_stat_influence":["will"],
                "uoss_mp_cost":155,
                "source_properties":["cleanseable","extendable"],
                "target_mode":"one_enemy",
                "soulbound_target_scope":"enemy_only",
                "soulbound_harmful_debuff":True,
                "enemy_debuffs":[
                    "paralyze","silence","slow","blind",
                    "curse_damage_down","immobilize"
                ],
                "control_effects":["paralyze","silence","slow"],
                "support_weapon_extra_effects":["blind","curse","immobilize"],
                "support_weapon_adds_extra_effects":True,
                "machine_accuracy_bonus":True,
                "level_effect":"increases_accuracy_and_duration",
                "cleanseable":True,
                "extendable":True,
                "accuracy_numeric_source_defined":False,
                "duration_numeric_source_defined":False,
                "machine_bonus_numeric_source_defined":False,
                "status_numeric_source_defined":False,
                "soulbound_base_accuracy":0.45,
                "soulbound_skill_accuracy_bonus_max":0.30,
                "soulbound_will_accuracy_bonus_max":0.15,
                "soulbound_machine_accuracy_bonus":0.15,
                "soulbound_accuracy_cap":0.98,
                "soulbound_duration_rounds_level1":3,
                "soulbound_duration_rounds_level600":10,
                "soulbound_will_duration_bonus_max":2,
                "soulbound_paralyze_skip_chance":0.50,
                "soulbound_slow_skip_every_actions":2,
                "soulbound_blind_miss_chance":0.35,
                "soulbound_curse_damage_multiplier":0.80,
                "balance_model":"soulbound_acc45_skill30_will15_machine15_duration3_to_10_statuses",
            })
        if special=="starlight_shower":
            row.update({
                "scale":"intelligence",
                "source_stat_influence":["magic_attack"],
                "magic_attack_influence":True,
                "uoss_mp_cost":225,
                "uoss_vmax_mp_cost":300,
                "source_properties":[],
                "target_mode":"single_or_diminishing_aoe",
                "aoe_diminishing":True,
                "vmax_target_mode":"all_enemies_non_diminishing",
                "vmax_aoe_non_diminishing":True,
                "diminishing_numeric_source_defined":False,
                "diminishing_balance_model":"soulbound_inverse_sqrt_target_count",
            })
        if special=="cosmic_rave":
            row.update({"scale":"attack", "secondary_scale":"dexterity",
                        "source_stat_influence":["attack","agility"],
                        "secondary_scale_weight":"lesser",
                        "carries_soul_weapon_elements":True, "requires_soul_weapon":"melee",
                        "target_mode":"diminishing_aoe_or_vmax_random",
                        "vmax_random_hits":5,
                        "vmax_random_hits_evidence":"user_uoss_combat_log"})
        if special=="intercept_system":
            row.update({
                "source_stat_influence":["variable"],
                "source_properties":[],
                "usage_mode":"job_set_counter",
                "interrupts_incoming_attack":True,
                "counter_damage":True,
                "highest_offensive_stat":True,
                "offensive_stat_candidates":[
                    "strength","dexterity","intelligence","willpower"
                ],
                "level_effect":"increases_damage",
                "numeric_damage_curve_source_defined":False,
                "skill_level_damage_curve":"global_soulbound_skill_power_1_to_600",
                "counter_trigger_chance_source_defined":False,
                "counter_trigger_model":"selected_counter_interrupts_incoming_attack",
            })
        if special=="vmax":
            row.update({"scale":"willpower","source_stat_influence":["will"],
                        "boost":1.0,"cooldown":0,
                        "duration_scales_with_skill_level":True,
                        "duration_scales_with_will":True,
                        "duration_balance_model":"soulbound_200_to_600_plus_uncapped_will",
                        "support_weapon_model":"mec_soul_weapon",
                        "vmax_status_sources":{
                            "praise":{"effect":"attack_power_up","numeric_source_defined":False},
                            "preach":{"effect":"magic_attack_up","numeric_source_defined":False,
                                      "source_stat_influence":["will"],
                                      "level_effect":"increases_duration"},
                            "protect":{"effect":"incoming_physical_damage_down",
                                       "numeric_source_defined":False,
                                       "source_stat_influence":["will"],
                                       "level_effect":"increases_duration",
                                       "properties":["dispelable","extendable","silenceable"]},
                            "shell":{"effect":"incoming_magic_damage_down",
                                     "numeric_source_defined":False,
                                     "source_stat_influence":["will"],
                                     "level_effect":"increases_duration",
                                     "properties":["dispelable","extendable","silenceable"]},
                            "regen":{"effect":"periodic_small_hp_heal",
                                     "numeric_source_defined":False,
                                     "source_stat_influence":["will"],
                                     "level_effect":"increases_duration",
                                     "tick_cadence_source_defined":False,
                                     "heal_amount_source_defined":False,
                                     "soulbound_tick_every_rounds":3,
                                     "soulbound_heal_model":"small_will_scaled_periodic_heal",
                                     "duration_source":"vmax_timer",
                                     "properties":["dispelable","extendable","reflectable","silenceable"]}
                        }})
    CLASS_SKILLS["Mec"] = rows


def _mec_contract_audit_v11149():
    rows={s.get("mec_special"):s for s in CLASS_SKILLS.get("Mec",[]) if s.get("mec_special")}
    errors=[]
    protocol_by_special={
        special:protocol_id
        for protocol_id,specials in MEC_PROTOCOL_SKILLS_V11155.items()
        for special in specials
    }
    source_mp_costs={
        "laser_spin":25,"area_bomb":35,"mec_sonata":50,"maelstrom":80,
        "shock":150,"starlight_shower":225,"cure_beam":10,"hypno_flash":15,
        "jammer":20,"heal_beam":36,"logic_bomb":155,
    }
    source_support_mp_costs={"jammer":40,"heal_beam":72}
    for _sid,_row in rows.items():
        if str(_row.get("source_ap_semantics",""))!="learning_points":
            errors.append(f"{_sid}: source AP must mean learning points")
        if bool(_row.get("source_ap_is_damage_power")):
            errors.append(f"{_sid}: source AP cannot be damage power")
        if "source_ap_cost" in _row and int(_row.get("base_power",0) or 0)!=0:
            errors.append(f"{_sid}: authored Mec base_power must not be sourced from AP")

    feedback_protocol=rows.get("feedback_protocol")
    if feedback_protocol:
        _feedback_expected=["destroy","robo_tackle","uzi_punch","kamikaze_crush"]
        if not bool(feedback_protocol.get("automatic")):
            errors.append("feedback_protocol: must be Automatic")
        if str(feedback_protocol.get("level_effect"))!="increases_mapped_skill_damage":
            errors.append("feedback_protocol: Level Effect must increase mapped skill damage")
        if list(feedback_protocol.get("source_level_effect_skills") or [])!=_feedback_expected:
            errors.append("feedback_protocol: source skill list mismatch")
        if list(MEC_PROTOCOL_SKILLS_V11155.get("v0319_mec_feedback_protocol") or ())!=_feedback_expected:
            errors.append("feedback_protocol: runtime mapping must exclude Compress and Crush")
        if bool(feedback_protocol.get("protocol_numeric_source_defined")):
            errors.append("feedback_protocol: numeric curve must remain marked unsourced")

    heal_beam=rows.get("heal_beam")
    if heal_beam:
        if int(heal_beam.get("unlock",0) or 0)!=54:
            errors.append("heal_beam: source Level 54 must map to Biegłość Mec 54")
        if int(heal_beam.get("source_ap_cost",0) or 0)!=1000:
            errors.append("heal_beam: source Base AP cost must remain 1000 learning points")
        if str(heal_beam.get("source_ap_semantics",""))!="learning_points":
            errors.append("heal_beam: AP must remain learning points")
        if int(heal_beam.get("source_requirement_level",0) or 0)!=54:
            errors.append("heal_beam: source requirement must remain Level 54")
        if str(heal_beam.get("source_requirement_maps_to"))!="class_mastery":
            errors.append("heal_beam: source Level must map to class mastery")
        if list(heal_beam.get("source_stat_influence") or [])!=["will"]:
            errors.append("heal_beam: source influence must be Will only")
        if list(heal_beam.get("source_properties") or [])!=[]:
            errors.append("heal_beam: source Properties must be None")
        if list(heal_beam.get("source_target_mode") or [])!=["one_target","party"]:
            errors.append("heal_beam: source target must remain One Target or Party")
        if str(heal_beam.get("target_mode"))!="one_ally_or_support_party":
            errors.append("heal_beam: Soulbound target mode must be one ally or support party")
        if not bool(heal_beam.get("soulbound_enemy_heal_disabled")):
            errors.append("heal_beam: healing combat enemies must remain disabled")
        if int(heal_beam.get("uoss_mp_cost",0) or 0)!=36:
            errors.append("heal_beam: normal MP cost must remain 36")
        if int(heal_beam.get("uoss_support_mp_cost",0) or 0)!=72:
            errors.append("heal_beam: support MP cost must remain 72")
        if str(heal_beam.get("level_effect"))!="increases_healing_power":
            errors.append("heal_beam: Level Effect must increase Healing Power")
        if not bool(heal_beam.get("support_weapon_expands_to_party")):
            errors.append("heal_beam: Support Effect must expand healing to party")

    cure_beam=rows.get("cure_beam")
    if cure_beam:
        if int(cure_beam.get("unlock",0) or 0)!=1:
            errors.append("cure_beam: Reqs None must map to Biegłość Mec 1")
        if int(cure_beam.get("source_ap_cost",0) or 0)!=100:
            errors.append("cure_beam: source Base AP cost must remain 100 learning points")
        if str(cure_beam.get("source_ap_semantics",""))!="learning_points":
            errors.append("cure_beam: AP must remain learning points")
        if list(cure_beam.get("source_requirements") or [])!=[] or not bool(cure_beam.get("source_requires_none")):
            errors.append("cure_beam: source requirements must be None")
        if list(cure_beam.get("source_stat_influence") or [])!=["will"]:
            errors.append("cure_beam: source influence must be Will only")
        if list(cure_beam.get("source_properties") or [])!=[]:
            errors.append("cure_beam: source Properties must be None")
        if list(cure_beam.get("source_target_mode") or [])!=["self","one_ally","one_enemy"]:
            errors.append("cure_beam: source target card must remain Self/One Ally/One Enemy")
        if str(cure_beam.get("target_mode"))!="self_or_one_ally":
            errors.append("cure_beam: Soulbound target mode must be self or one ally")
        if not bool(cure_beam.get("soulbound_enemy_heal_disabled")):
            errors.append("cure_beam: healing combat enemies must remain disabled")
        if str(cure_beam.get("level_effect"))!="increases_healing_power":
            errors.append("cure_beam: Level Effect must increase Healing Power")
        if list(cure_beam.get("support_cleanses") or [])!=["blind","poison"]:
            errors.append("cure_beam: Support Effect must cleanse Blind and Poison")

    shock=rows.get("shock")
    if shock:
        if int(shock.get("unlock",0) or 0)!=95:
            errors.append("shock: source Level 95 must map to Biegłość Mec 95")
        if int(shock.get("source_ap_cost",0) or 0)!=1800:
            errors.append("shock: source Base AP cost must remain 1800 metadata")
        if bool(shock.get("source_ap_is_damage_power")) or int(shock.get("base_power",0) or 0)!=0:
            errors.append("shock: source AP must not be used as combat base power")
        if int(shock.get("source_requirement_level",0) or 0)!=95:
            errors.append("shock: source requirement must remain Level 95")
        if str(shock.get("source_requirement_maps_to"))!="class_mastery":
            errors.append("shock: source Level must map to class mastery")
        if list(shock.get("source_stat_influence") or [])!=["magic_attack"]:
            errors.append("shock: source influence must be Magic Attack only")
        if list(shock.get("source_properties") or [])!=[]:
            errors.append("shock: source Properties must be None")
        if str(shock.get("target_mode"))!="all_enemies_diminishing":
            errors.append("shock: target mode must be All Enemies (Diminishing)")
        if not bool(shock.get("aoe_diminishing")):
            errors.append("shock: diminishing flag missing")
        if bool(shock.get("diminishing_numeric_source_defined")):
            errors.append("shock: numeric diminishing curve must remain marked unsourced")
        if str(shock.get("soulbound_diminishing_model"))!="inverse_sqrt_target_count":
            errors.append("shock: Soulbound diminishing model mismatch")
        if list(shock.get("elements") or [])!=["lightning","dark"]:
            errors.append("shock: elements must be Lightning + Dark")

    maelstrom=rows.get("maelstrom")
    if maelstrom:
        if int(maelstrom.get("unlock",0) or 0)!=44:
            errors.append("maelstrom: source Level 44 must map to Biegłość Mec 44")
        if int(maelstrom.get("source_ap_cost",0) or 0)!=1500:
            errors.append("maelstrom: source Base AP cost must remain 1500 metadata")
        if bool(maelstrom.get("source_ap_is_damage_power")) or int(maelstrom.get("base_power",0) or 0)!=0:
            errors.append("maelstrom: source AP must not be used as combat base power")
        if int(maelstrom.get("source_requirement_level",0) or 0)!=44:
            errors.append("maelstrom: source requirement must remain Level 44")
        if str(maelstrom.get("source_requirement_maps_to"))!="class_mastery":
            errors.append("maelstrom: source Level must map to class mastery")
        if list(maelstrom.get("source_stat_influence") or [])!=["magic_attack"]:
            errors.append("maelstrom: source influence must be Magic Attack only")
        if list(maelstrom.get("source_properties") or [])!=[]:
            errors.append("maelstrom: source Properties must be None")
        if str(maelstrom.get("target_mode"))!="all_enemies_diminishing":
            errors.append("maelstrom: target mode must be All Enemies (Diminishing)")
        if not bool(maelstrom.get("aoe_diminishing")):
            errors.append("maelstrom: diminishing flag missing")
        if bool(maelstrom.get("diminishing_numeric_source_defined")):
            errors.append("maelstrom: numeric diminishing curve must remain marked unsourced")
        if str(maelstrom.get("soulbound_diminishing_model"))!="inverse_sqrt_target_count":
            errors.append("maelstrom: Soulbound diminishing model mismatch")
        if str(maelstrom.get("element","")).casefold()!="water":
            errors.append("maelstrom: element must be Water")

    area_bomb=rows.get("area_bomb")
    if area_bomb:
        if int(area_bomb.get("unlock",0) or 0)!=8:
            errors.append("area_bomb: source Level 8 must map to Biegłość Mec 8")
        if int(area_bomb.get("source_ap_cost",0) or 0)!=300:
            errors.append("area_bomb: source Base AP cost must remain 300 metadata")
        if bool(area_bomb.get("source_ap_is_damage_power")) or int(area_bomb.get("base_power",0) or 0)!=0:
            errors.append("area_bomb: source AP must not be used as combat base power")
        if int(area_bomb.get("source_requirement_level",0) or 0)!=8:
            errors.append("area_bomb: source requirement must remain Level 8")
        if str(area_bomb.get("source_requirement_maps_to"))!="class_mastery":
            errors.append("area_bomb: source Level must map to class mastery")
        if list(area_bomb.get("source_stat_influence") or [])!=["magic_attack"]:
            errors.append("area_bomb: source influence must be Magic Attack only")
        if list(area_bomb.get("source_properties") or [])!=[]:
            errors.append("area_bomb: source Properties must be None")
        if str(area_bomb.get("target_mode"))!="all_targetted_enemies":
            errors.append("area_bomb: target mode must be All Targetted Enemies")
        if not bool(area_bomb.get("engaged_only")):
            errors.append("area_bomb: must hit engaged targets only")
        if bool(area_bomb.get("aoe_diminishing")):
            errors.append("area_bomb: source does not mark this attack Diminishing")
        if str(area_bomb.get("element","")).casefold()!="fire":
            errors.append("area_bomb: element must be Fire")
        if bool(area_bomb.get("burn_status_source_defined")):
            errors.append("area_bomb: no separate Burn status may be invented")

    laser_spin=rows.get("laser_spin")
    if laser_spin:
        if int(laser_spin.get("unlock",0) or 0)!=1:
            errors.append("laser_spin: Reqs None must map to Biegłość Mec 1")
        if int(laser_spin.get("source_ap_cost",0) or 0)!=200:
            errors.append("laser_spin: source Base AP cost must remain 200 metadata")
        if bool(laser_spin.get("source_ap_is_damage_power")) or int(laser_spin.get("base_power",0) or 0)!=0:
            errors.append("laser_spin: source AP must not be used as combat base power")
        if list(laser_spin.get("source_requirements") or [])!=[] or not bool(laser_spin.get("source_requires_none")):
            errors.append("laser_spin: source requirements must be None")
        if list(laser_spin.get("source_stat_influence") or [])!=["magic_attack"]:
            errors.append("laser_spin: source influence must be Magic Attack only")
        if list(laser_spin.get("source_properties") or [])!=[]:
            errors.append("laser_spin: source Properties must be None")
        if str(laser_spin.get("target_mode"))!="all_enemies_diminishing":
            errors.append("laser_spin: target mode must be All Enemies (Diminishing)")
        if not bool(laser_spin.get("aoe_diminishing")):
            errors.append("laser_spin: diminishing flag missing")
        if str(laser_spin.get("element","")).casefold()!="dark":
            errors.append("laser_spin: element must be Dark")

    cosmic=rows.get("cosmic_rave")
    if cosmic:
        if str(cosmic.get("scale"))!="attack":
            errors.append(f"cosmic_rave:scale={cosmic.get('scale')} expected=attack")
        if str(cosmic.get("secondary_scale"))!="dexterity":
            errors.append(
                f"cosmic_rave:secondary={cosmic.get('secondary_scale')} expected=dexterity"
            )
        if int(cosmic.get("vmax_random_hits",0) or 0)!=5:
            errors.append(
                f"cosmic_rave:vmax_random_hits={cosmic.get('vmax_random_hits')} expected=5"
            )
    intercept=rows.get("intercept_system")
    if intercept:
        if list(intercept.get("source_stat_influence") or [])!=["variable"]:
            errors.append("intercept_system: source influence must be Variable")
        if list(intercept.get("source_properties") or [])!=[]:
            errors.append("intercept_system: source Properties must be None")
        if str(intercept.get("usage_mode"))!="job_set_counter":
            errors.append("intercept_system: must use job set counter")
        if not bool(intercept.get("interrupts_incoming_attack")):
            errors.append("intercept_system: must interrupt incoming attack")
        if not bool(intercept.get("highest_offensive_stat")):
            errors.append("intercept_system: must use highest offensive stat")
        if list(intercept.get("offensive_stat_candidates") or [])!=[
            "strength","dexterity","intelligence","willpower"
        ]:
            errors.append("intercept_system: offensive stat candidates mismatch")
        if str(intercept.get("level_effect"))!="increases_damage":
            errors.append("intercept_system: Skill Level must increase Damage")
        if bool(intercept.get("numeric_damage_curve_source_defined")):
            errors.append("intercept_system: numeric Skill Level curve must remain marked unsourced")
        if bool(intercept.get("counter_trigger_chance_source_defined")):
            errors.append("intercept_system: no source trigger chance may be invented")

    tiger_rampage=rows.get("tiger_rampage")
    if tiger_rampage:
        if str(tiger_rampage.get("scale"))!="attack":
            errors.append("tiger_rampage: primary scale must be Attack")
        if list(tiger_rampage.get("source_stat_influence") or [])!=["attack"]:
            errors.append("tiger_rampage: source influence must be Attack")
        if list(tiger_rampage.get("source_properties") or [])!=["carries_elements","extendable"]:
            errors.append("tiger_rampage: source Properties must be Carries Elements + Extendable")
        if int(tiger_rampage.get("hits",0) or 0)!=2:
            errors.append("tiger_rampage: source requires exactly two heavy blows")
        if str(tiger_rampage.get("target_mode"))!="one_enemy":
            errors.append("tiger_rampage: target mode must be One Enemy")
        if not bool(tiger_rampage.get("defense_break_physical")):
            errors.append("tiger_rampage: physical defense break missing")
        if not bool(tiger_rampage.get("defense_break_magical")):
            errors.append("tiger_rampage: magical defense break missing")
        if not bool(tiger_rampage.get("extendable")):
            errors.append("tiger_rampage: defense break must be Extendable")
        if bool(tiger_rampage.get("defense_break_chance_source_defined")):
            errors.append("tiger_rampage: proc chance must remain marked unsourced")
        if bool(tiger_rampage.get("defense_break_duration_source_defined")):
            errors.append("tiger_rampage: break duration must remain marked unsourced")
        if bool(tiger_rampage.get("defense_break_amount_source_defined")):
            errors.append("tiger_rampage: defense reduction amount must remain marked unsourced")
        if not bool(tiger_rampage.get("carries_soul_weapon_elements")):
            errors.append("tiger_rampage: must carry Soul Weapon elements")
        if str(tiger_rampage.get("requires_soul_weapon"))!="melee":
            errors.append("tiger_rampage: melee weapon requirement must map to Soul Weapon")

    pop_knight=rows.get("pop_knight")
    if pop_knight:
        if str(pop_knight.get("scale"))!="attack":
            errors.append("pop_knight: primary scale must be Attack")
        if list(pop_knight.get("source_stat_influence") or [])!=["attack"]:
            errors.append("pop_knight: source influence must be Attack")
        if list(pop_knight.get("source_properties") or [])!=["carries_elements"]:
            errors.append("pop_knight: source Properties must be Carries Elements")
        if str(pop_knight.get("target_mode"))!="all_enemies_non_diminishing":
            errors.append("pop_knight: target mode must be All Enemies non-diminishing")
        if not bool(pop_knight.get("aoe_non_diminishing")):
            errors.append("pop_knight: non-diminishing AoE flag missing")
        if not bool(pop_knight.get("bonus_vs_flying")):
            errors.append("pop_knight: Flying bonus missing")
        if str(pop_knight.get("flying_template_flag"))!="flying":
            errors.append("pop_knight: Flying detection must use canonical template flag")
        if not bool(pop_knight.get("bonus_vs_flying_source_defined")):
            errors.append("pop_knight: source confirms extra damage against Flying")
        if bool(pop_knight.get("flying_bonus_numeric_source_defined")):
            errors.append("pop_knight: numeric Flying bonus must remain marked unsourced")
        if not bool(pop_knight.get("carries_soul_weapon_elements")):
            errors.append("pop_knight: must carry Soul Weapon elements")
        if str(pop_knight.get("requires_soul_weapon"))!="melee":
            errors.append("pop_knight: melee weapon requirement must map to Soul Weapon")

    plural_slash=rows.get("plural_slash")
    if plural_slash:
        if str(plural_slash.get("scale"))!="attack":
            errors.append("plural_slash: primary scale must be Attack")
        if str(plural_slash.get("secondary_scale"))!="dexterity":
            errors.append("plural_slash: Agility must map to Dexterity")
        if list(plural_slash.get("source_stat_influence") or [])!=["attack","agility"]:
            errors.append("plural_slash: source influence must be Attack + Agility")
        if list(plural_slash.get("source_properties") or [])!=["carries_elements"]:
            errors.append("plural_slash: source Properties must be Carries Elements")
        if str(plural_slash.get("target_mode"))!="one_enemy":
            errors.append("plural_slash: target mode must be One Enemy")
        if not bool(plural_slash.get("multi_slash")):
            errors.append("plural_slash: multi-slash identity missing")
        if bool(plural_slash.get("multi_hit_count_source_defined")):
            errors.append("plural_slash: hit count must remain marked unsourced")
        if not bool(plural_slash.get("agility_secondary_influence")):
            errors.append("plural_slash: Agility secondary influence missing")
        if bool(plural_slash.get("secondary_numeric_weight_source_defined")):
            errors.append("plural_slash: Agility numeric weight must remain marked unsourced")
        if not bool(plural_slash.get("carries_soul_weapon_elements")):
            errors.append("plural_slash: must carry Soul Weapon elements")
        if str(plural_slash.get("requires_soul_weapon"))!="melee":
            errors.append("plural_slash: melee weapon requirement must map to Soul Weapon")

    shock_soldier=rows.get("shock_soldier")
    if shock_soldier:
        if str(shock_soldier.get("scale"))!="attack":
            errors.append("shock_soldier: primary scale must be Attack")
        if list(shock_soldier.get("source_stat_influence") or [])!=["attack"]:
            errors.append("shock_soldier: source influence must be Attack")
        if list(shock_soldier.get("source_properties") or [])!=["carries_elements"]:
            errors.append("shock_soldier: source Properties must be Carries Elements")
        if str(shock_soldier.get("target_mode"))!="all_enemies_diminishing":
            errors.append("shock_soldier: target mode must be All Enemies diminishing")
        if not bool(shock_soldier.get("aoe_diminishing")):
            errors.append("shock_soldier: diminishing AoE flag missing")
        if bool(shock_soldier.get("diminishing_numeric_source_defined")):
            errors.append("shock_soldier: numeric diminishing curve must remain marked unsourced")
        if str(shock_soldier.get("soulbound_diminishing_model"))!="inverse_sqrt_target_count":
            errors.append("shock_soldier: Soulbound diminishing model mismatch")
        if not bool(shock_soldier.get("carries_soul_weapon_elements")):
            errors.append("shock_soldier: must carry Soul Weapon elements")
        if str(shock_soldier.get("requires_soul_weapon"))!="melee":
            errors.append("shock_soldier: melee weapon requirement must map to Soul Weapon")

    hammer_crush=rows.get("hammer_crush")
    if hammer_crush:
        if str(hammer_crush.get("scale"))!="attack":
            errors.append("hammer_crush: primary scale must be Attack")
        if list(hammer_crush.get("source_stat_influence") or [])!=["attack"]:
            errors.append("hammer_crush: source influence must be Attack")
        if list(hammer_crush.get("source_properties") or [])!=["carries_elements"]:
            errors.append("hammer_crush: source Properties must be Carries Elements")
        if str(hammer_crush.get("target_mode"))!="one_enemy":
            errors.append("hammer_crush: target mode must be One Enemy")
        if not bool(hammer_crush.get("carries_soul_weapon_elements")):
            errors.append("hammer_crush: must carry Soul Weapon elements")
        if str(hammer_crush.get("requires_soul_weapon"))!="melee":
            errors.append("hammer_crush: melee weapon requirement must map to Soul Weapon")

    dispose=rows.get("dispose")
    if dispose:
        if str(dispose.get("scale"))!="attack":
            errors.append("dispose: primary scale must be Attack")
        if list(dispose.get("source_stat_influence") or [])!=["attack"]:
            errors.append("dispose: source influence must be Attack")
        if list(dispose.get("source_properties") or [])!=["carries_elements"]:
            errors.append("dispose: source Properties must be Carries Elements")
        if str(dispose.get("target_mode"))!="all_enemies_non_diminishing":
            errors.append("dispose: target mode must be All Enemies non-diminishing")
        if not bool(dispose.get("aoe_non_diminishing")):
            errors.append("dispose: area damage must remain non-diminishing")
        if not bool(dispose.get("carries_soul_weapon_elements")):
            errors.append("dispose: must carry Soul Weapon elements")
        if str(dispose.get("requires_soul_weapon"))!="ranged":
            errors.append("dispose: ranged weapon requirement must map to Soul Weapon")
        if not bool(dispose.get("feedback_damage")):
            errors.append("dispose: Feedback self-damage missing")
        if bool(dispose.get("feedback_cost_source_defined")):
            errors.append("dispose: Feedback numeric cost must remain marked unsourced")
        if not bool(dispose.get("feedback_once_per_cast")):
            errors.append("dispose: Feedback must be applied once per cast")
        if not bool(dispose.get("feedback_repair_eligible")):
            errors.append("dispose: Feedback must be eligible for Self-Repair")

    range_fire=rows.get("range_fire")
    if range_fire:
        if str(range_fire.get("scale"))!="attack":
            errors.append("range_fire: primary scale must be Attack")
        if list(range_fire.get("source_stat_influence") or [])!=["attack"]:
            errors.append("range_fire: source influence must be Attack")
        if list(range_fire.get("source_properties") or [])!=["carries_elements"]:
            errors.append("range_fire: source Properties must be Carries Elements")
        if str(range_fire.get("target_mode"))!="all_enemies_non_diminishing":
            errors.append("range_fire: target mode must be All Enemies non-diminishing")
        if not bool(range_fire.get("aoe_non_diminishing")):
            errors.append("range_fire: area damage must remain non-diminishing")
        if not bool(range_fire.get("carries_soul_weapon_elements")):
            errors.append("range_fire: must carry Soul Weapon elements")
        if str(range_fire.get("requires_soul_weapon"))!="ranged":
            errors.append("range_fire: ranged weapon requirement must map to Soul Weapon")

    crosshair=rows.get("crosshair")
    if crosshair:
        if str(crosshair.get("scale"))!="attack":
            errors.append("crosshair: primary scale must be Attack")
        if list(crosshair.get("source_stat_influence") or [])!=[
            "attack","critical_hit_chance"
        ]:
            errors.append("crosshair: source influence must be Attack + Critical Hit Chance")
        if list(crosshair.get("source_properties") or [])!=["carries_elements"]:
            errors.append("crosshair: source Properties must be Carries Elements")
        if str(crosshair.get("target_mode"))!="one_enemy":
            errors.append("crosshair: target mode must be One Enemy")
        if not bool(crosshair.get("critical_chance_influence")):
            errors.append("crosshair: Critical Hit Chance influence missing")
        if not bool(crosshair.get("attempts_critical")):
            errors.append("crosshair: critical attempt contract missing")
        if str(crosshair.get("critical_model"))!="character_critical_hit_chance":
            errors.append("crosshair: must roll the character's real Critical Hit Chance")
        if not bool(crosshair.get("carries_soul_weapon_elements")):
            errors.append("crosshair: must carry Soul Weapon elements")
        if str(crosshair.get("requires_soul_weapon"))!="ranged":
            errors.append("crosshair: ranged weapon requirement must map to Soul Weapon")

    logic_bomb=rows.get("logic_bomb")
    if logic_bomb:
        if list(logic_bomb.get("source_stat_influence") or [])!=["will"]:
            errors.append("logic_bomb: source influence must be Will")
        if str(logic_bomb.get("scale"))!="willpower":
            errors.append("logic_bomb: scale must be Willpower")
        if int(logic_bomb.get("uoss_mp_cost",0) or 0)!=155:
            errors.append("logic_bomb: MP cost must be 155")
        if str(logic_bomb.get("target_mode"))!="one_enemy":
            errors.append("logic_bomb: target mode must be One Enemy")
        if list(logic_bomb.get("source_properties") or [])!=["cleanseable","extendable"]:
            errors.append("logic_bomb: source Properties must be Cleanseable + Extendable")
        if list(logic_bomb.get("control_effects") or [])!=["paralyze","silence","slow"]:
            errors.append("logic_bomb: base statuses must be Paralyze + Silence + Slow")
        if list(logic_bomb.get("support_weapon_extra_effects") or [])!=["blind","curse","immobilize"]:
            errors.append("logic_bomb: support statuses must be Blind + Curse + Immobilize")
        if str(logic_bomb.get("level_effect"))!="increases_accuracy_and_duration":
            errors.append("logic_bomb: Skill Level must increase Accuracy and Duration")
        if not bool(logic_bomb.get("machine_accuracy_bonus")):
            errors.append("logic_bomb: Machine targets must have increased hit rate")
        if bool(logic_bomb.get("accuracy_numeric_source_defined")):
            errors.append("logic_bomb: accuracy curve must remain marked unsourced")
        if bool(logic_bomb.get("duration_numeric_source_defined")):
            errors.append("logic_bomb: duration curve must remain marked unsourced")
        if bool(logic_bomb.get("machine_bonus_numeric_source_defined")):
            errors.append("logic_bomb: Machine bonus must remain marked unsourced")
        if bool(logic_bomb.get("status_numeric_source_defined")):
            errors.append("logic_bomb: status numeric behavior must remain marked unsourced")

    jammer=rows.get("jammer")
    if jammer:
        if list(jammer.get("source_stat_influence") or [])!=["will"]:
            errors.append("jammer: source influence must be Will")
        if str(jammer.get("scale"))!="willpower":
            errors.append("jammer: scale must be Willpower")
        if int(jammer.get("uoss_mp_cost",0) or 0)!=20:
            errors.append("jammer: normal MP cost must be 20")
        if int(jammer.get("uoss_support_mp_cost",0) or 0)!=40:
            errors.append("jammer: support MP cost must be 40")
        if str(jammer.get("target_mode"))!="one_or_support_all_enemies":
            errors.append("jammer: target mode must be one or support-all enemies")
        if list(jammer.get("source_properties") or [])!=["cleanseable","extendable"]:
            errors.append("jammer: source Properties must be Cleanseable + Extendable")
        if str(jammer.get("control_effect"))!="stop":
            errors.append("jammer: control effect must be Stop")
        if str(jammer.get("level_effect"))!="increases_accuracy_and_duration":
            errors.append("jammer: Skill Level must increase Accuracy and Duration")
        if not bool(jammer.get("machine_accuracy_bonus")):
            errors.append("jammer: mechanical enemies must be easier to affect")
        if not bool(jammer.get("support_weapon_expands_to_all_enemies")):
            errors.append("jammer: support weapon must expand effect to all enemies")
        if not bool(jammer.get("uoss_superboss_stop_immune")):
            errors.append("jammer: UOSS Super Bosses must remain immune to Stop")
        if bool(jammer.get("accuracy_numeric_source_defined")):
            errors.append("jammer: accuracy curve must remain marked unsourced")
        if bool(jammer.get("duration_numeric_source_defined")):
            errors.append("jammer: duration curve must remain marked unsourced")
        if bool(jammer.get("machine_bonus_numeric_source_defined")):
            errors.append("jammer: machine accuracy bonus must remain marked unsourced")

    hypno=rows.get("hypno_flash")
    if hypno:
        if list(hypno.get("source_stat_influence") or [])!=["will"]:
            errors.append("hypno_flash: source influence must be Will")
        if str(hypno.get("scale"))!="willpower":
            errors.append("hypno_flash: scale must be Willpower")
        if int(hypno.get("uoss_mp_cost",0) or 0)!=15:
            errors.append("hypno_flash: MP cost must be 15")
        if str(hypno.get("target_mode"))!="one_enemy":
            errors.append("hypno_flash: target mode must be One Enemy")
        if list(hypno.get("source_properties") or [])!=["cleanseable","extendable"]:
            errors.append("hypno_flash: source Properties must be Cleanseable + Extendable")
        if str(hypno.get("control_effect"))!="sleep":
            errors.append("hypno_flash: control effect must be Sleep")
        if str(hypno.get("level_effect"))!="increases_accuracy_and_duration":
            errors.append("hypno_flash: Skill Level must increase Accuracy and Duration")
        if not bool(hypno.get("support_weapon_improves_accuracy")):
            errors.append("hypno_flash: support weapon must improve hit chance")
        if bool(hypno.get("accuracy_numeric_source_defined")):
            errors.append("hypno_flash: accuracy curve must remain marked unsourced")
        if bool(hypno.get("duration_numeric_source_defined")):
            errors.append("hypno_flash: duration curve must remain marked unsourced")

    mec_sonata=rows.get("mec_sonata")
    if mec_sonata:
        if list(mec_sonata.get("source_stat_influence") or [])!=["magic_attack"]:
            errors.append("mec_sonata: source influence must be Magic Attack only")
        if str(mec_sonata.get("scale"))!="intelligence":
            errors.append("mec_sonata: Magic Attack must use the magic/INT core")
        if int(mec_sonata.get("uoss_mp_cost",0) or 0)!=50:
            errors.append("mec_sonata: MP cost must be 50")
        if str(mec_sonata.get("target_mode"))!="one_enemy":
            errors.append("mec_sonata: target mode must be One Enemy")
        if list(mec_sonata.get("source_properties") or [])!=["extendable"]:
            errors.append("mec_sonata: source Properties must be Extendable")
        if not bool(mec_sonata.get("temporary_level_reduction_chance")):
            errors.append("mec_sonata: temporary level reduction chance missing")
        if not bool(mec_sonata.get("level_reduction_extendable")):
            errors.append("mec_sonata: level reduction must be Extendable")
        if bool(mec_sonata.get("level_reduction_numeric_source_defined")):
            errors.append("mec_sonata: level reduction amount must remain marked unsourced")
        if bool(mec_sonata.get("level_reduction_duration_source_defined")):
            errors.append("mec_sonata: duration must remain marked unsourced")
        if bool(mec_sonata.get("level_reduction_chance_source_defined")):
            errors.append("mec_sonata: proc chance must remain marked unsourced")

    magnify=rows.get("magnify")
    if magnify:
        if list(magnify.get("source_stat_influence") or [])!=["attack","wisdom"]:
            errors.append("magnify: source influence must be Attack + Wisdom")
        if str(magnify.get("scale"))!="attack":
            errors.append("magnify: primary scale must be Attack")
        if str(magnify.get("secondary_scale"))!="intelligence":
            errors.append("magnify: Wisdom must map to Intelligence")
        if str(magnify.get("target_mode"))!="one_enemy":
            errors.append("magnify: target mode must be One Enemy")
        if list(magnify.get("source_properties") or [])!=["cooldown"]:
            errors.append("magnify: source Properties must be Cooldown")
        if not bool(magnify.get("wisdom_magnifies_damage")):
            errors.append("magnify: Wisdom must magnify damage")
        if not bool(magnify.get("skill_level_reduces_system_failure")):
            errors.append("magnify: Skill Level must reduce systems failure")
        if not bool(magnify.get("wisdom_reduces_system_failure")):
            errors.append("magnify: Wisdom must reduce systems failure")
        if not bool(magnify.get("systems_failure_causes_overheat_reboot")):
            errors.append("magnify: systems failure must cause Overheat/reboot")
        if str(magnify.get("requires_soul_weapon"))!="ranged":
            errors.append("magnify: ranged weapon requirement must map to Soul Weapon")
        if bool(magnify.get("numeric_cooldown_source_defined")):
            errors.append("magnify: numeric cooldown duration must remain marked unsourced")
        if bool(magnify.get("mechanic_cooldown")) or int(magnify.get("cooldown",0) or 0)!=0:
            errors.append("magnify: source Cooldown property must not become a Soulbound reuse timer")
        if bool(magnify.get("systems_failure_numeric_source_defined")):
            errors.append("magnify: numeric failure curve must remain marked unsourced")

    satellite=rows.get("satellite_linker")
    if satellite:
        if list(satellite.get("source_stat_influence") or [])!=["attack","wisdom"]:
            errors.append("satellite_linker: source influence must be Attack + Wisdom")
        if str(satellite.get("scale"))!="attack":
            errors.append("satellite_linker: primary scale must be Attack")
        if str(satellite.get("secondary_scale"))!="intelligence":
            errors.append("satellite_linker: Wisdom must map to Intelligence")
        if str(satellite.get("target_mode"))!="one_enemy":
            errors.append("satellite_linker: target mode must be One Enemy")
        if not bool(satellite.get("periodic_damage")):
            errors.append("satellite_linker: periodic damage missing")
        if str(satellite.get("level_effect"))!="increases_duration":
            errors.append("satellite_linker: Skill Level must increase duration")
        if bool(satellite.get("duration_source_defined")):
            errors.append("satellite_linker: numeric duration must remain marked unsourced")
        if bool(satellite.get("tick_cadence_source_defined")):
            errors.append("satellite_linker: tick cadence must remain marked unsourced")
        if bool(satellite.get("tick_damage_source_defined")):
            errors.append("satellite_linker: tick damage must remain marked unsourced")
        if list(satellite.get("source_properties") or [])!=[]:
            errors.append("satellite_linker: source Properties must remain None")

    shoot_all=rows.get("shoot_all")
    if shoot_all:
        if str(shoot_all.get("scale"))!="attack":
            errors.append(f"shoot_all:scale={shoot_all.get('scale')} expected=attack")
        if list(shoot_all.get("source_stat_influence") or [])!=["attack","critical_hit_chance"]:
            errors.append("shoot_all: source influence must be Attack + Critical Hit Chance")
        if str(shoot_all.get("target_mode"))!="all_enemies_non_diminishing":
            errors.append("shoot_all: target mode must be all enemies non-diminishing")
        if not bool(shoot_all.get("carries_soul_weapon_elements")):
            errors.append("shoot_all: must carry Soul Weapon elements")
        if not bool(shoot_all.get("vmax_increases_critical_and_damage")):
            errors.append("shoot_all: missing V-MAX crit/damage increase")
        if bool(shoot_all.get("vmax_numeric_source_defined")):
            errors.append("shoot_all: V-MAX numeric bonus must remain marked unsourced")
    compress=rows.get("compress")
    if compress:
        if list(compress.get("source_stat_influence") or [])!=["vitality","hp"]:
            errors.append("compress: source influence must be Vitality + HP")
        if str(compress.get("scale"))!="target_current_hp_percent":
            errors.append("compress: damage must be percentage of target current HP")
        if str(compress.get("target_mode"))!="one_enemy":
            errors.append("compress: target mode must be One Enemy")
        if str(compress.get("level_effect"))!="increases_accuracy":
            errors.append("compress: Skill Level must increase Accuracy")
        if not bool(compress.get("percentage_target_hp_damage")):
            errors.append("compress: percentage HP damage flag missing")
        if not bool(compress.get("full_hp_increases_power")):
            errors.append("compress: full HP must increase compressing power")
        if not bool(compress.get("shield_increases_compressing_power")):
            errors.append("compress: shield must increase compressing power")
        if not bool(compress.get("feedback_damage")):
            errors.append("compress: Feedback self-damage missing")
        if bool(compress.get("feedback_cost_source_defined")):
            errors.append("compress: Feedback numeric cost must remain marked unsourced")
        if bool(compress.get("numeric_source_defined")):
            errors.append("compress: numeric percentage/accuracy curve must remain marked unsourced")
        if list(compress.get("source_properties") or [])!=[]:
            errors.append("compress: source Properties must remain None")

    destroy=rows.get("destroy")
    if destroy:
        if list(destroy.get("source_stat_influence") or [])!=["hp","vitality","attack"]:
            errors.append("destroy: source influence must be HP + Vitality + Attack")
        if str(destroy.get("scale"))!="attack":
            errors.append("destroy: primary scale must be Attack")
        if str(destroy.get("secondary_scale"))!="constitution":
            errors.append("destroy: Vitality must map to Constitution")
        if str(destroy.get("target_mode"))!="one_enemy":
            errors.append("destroy: target mode must be One Enemy")
        if not bool(destroy.get("feedback_damage")):
            errors.append("destroy: Feedback self-damage missing")
        if not bool(destroy.get("shield_improves_damage")):
            errors.append("destroy: equipped shield must improve damage")
        if not bool(destroy.get("power_increases_as_hp_decreases")):
            errors.append("destroy: lower HP must increase attack power")
        if bool(destroy.get("feedback_cost_source_defined")):
            errors.append("destroy: Feedback numeric cost must remain marked unsourced")
        if bool(destroy.get("numeric_source_defined")):
            errors.append("destroy: numeric modifiers must remain marked unsourced")
        if list(destroy.get("source_properties") or [])!=[]:
            errors.append("destroy: source Properties must remain None")

    robo_tackle=rows.get("robo_tackle")
    if robo_tackle:
        if list(robo_tackle.get("source_stat_influence") or [])!=["hp","vitality","attack"]:
            errors.append("robo_tackle: source influence must be HP + Vitality + Attack")
        if str(robo_tackle.get("scale"))!="attack":
            errors.append("robo_tackle: primary scale must be Attack")
        if str(robo_tackle.get("secondary_scale"))!="constitution":
            errors.append("robo_tackle: Vitality must map to Constitution")
        if str(robo_tackle.get("target_mode"))!="one_enemy":
            errors.append("robo_tackle: target mode must be One Enemy")
        if not bool(robo_tackle.get("damage_from_current_hp")):
            errors.append("robo_tackle: current HP must influence damage")
        if not bool(robo_tackle.get("shield_improves_damage")):
            errors.append("robo_tackle: equipped shield must improve damage")
        if not bool(robo_tackle.get("vmax_power_and_feedback")):
            errors.append("robo_tackle: V-MAX must increase power and Feedback")
        if not bool(robo_tackle.get("feedback_damage")):
            errors.append("robo_tackle: Feedback self-damage missing")
        if bool(robo_tackle.get("feedback_cost_source_defined")):
            errors.append("robo_tackle: Feedback numeric cost must remain marked unsourced")
        if bool(robo_tackle.get("numeric_source_defined")):
            errors.append("robo_tackle: numeric modifiers must remain marked unsourced")
        if list(robo_tackle.get("source_properties") or [])!=[]:
            errors.append("robo_tackle: source Properties must remain None")

    uzi=rows.get("uzi_punch")
    if uzi:
        if list(uzi.get("source_stat_influence") or [])!=["hp","vitality","attack"]:
            errors.append("uzi_punch: source influence must be HP + Vitality + Attack")
        if str(uzi.get("scale"))!="attack":
            errors.append("uzi_punch: primary scale must be Attack")
        if str(uzi.get("secondary_scale"))!="constitution":
            errors.append("uzi_punch: Vitality must map to Constitution")
        if str(uzi.get("target_mode"))!="random_enemies":
            errors.append("uzi_punch: target mode must be Random Enemies")
        if not bool(uzi.get("feedback_damage")):
            errors.append("uzi_punch: Feedback self-damage missing")
        if not bool(uzi.get("shield_improves_damage")):
            errors.append("uzi_punch: equipped shield must improve damage")
        if not bool(uzi.get("power_increases_as_hp_decreases")):
            errors.append("uzi_punch: lower HP must increase attack power")
        if bool(uzi.get("feedback_cost_source_defined")):
            errors.append("uzi_punch: Feedback numeric cost must remain marked unsourced")
        if bool(uzi.get("numeric_source_defined")):
            errors.append("uzi_punch: numeric modifiers must remain marked unsourced")
        if bool(uzi.get("random_target_count_source_defined")):
            errors.append("uzi_punch: Random Enemies hit count must remain marked unsourced")
        if list(uzi.get("source_properties") or [])!=[]:
            errors.append("uzi_punch: source Properties must remain None")

    crush=rows.get("crush")
    if crush:
        if list(crush.get("source_stat_influence") or [])!=["hp","level"]:
            errors.append("crush: source influence must be HP + Level")
        if str(crush.get("scale"))!="hp_difference":
            errors.append("crush: damage source must be max HP minus current HP")
        if str(crush.get("target_mode"))!="one_enemy":
            errors.append("crush: target mode must be one enemy")
        if not bool(crush.get("damage_from_missing_hp")):
            errors.append("crush: missing HP must drive damage")
        if not bool(crush.get("level_caps_damage")):
            errors.append("crush: Character Level must limit damage capacity")
        if str(crush.get("level_effect"))!="increases_maximum_possible_damage":
            errors.append("crush: Skill Level must increase maximum possible damage")
        if not bool(crush.get("shield_increases_capacity")):
            errors.append("crush: equipped shield must increase capacity")
        if not bool(crush.get("feedback_damage")):
            errors.append("crush: Feedback self-damage missing")
        if bool(crush.get("feedback_cost_source_defined")):
            errors.append("crush: Feedback numeric cost must remain marked unsourced")
        if bool(crush.get("numeric_source_defined")):
            errors.append("crush: numeric cap curve must remain marked unsourced")
        if list(crush.get("source_properties") or [])!=[]:
            errors.append("crush: source Properties must remain None")

    kamikaze=rows.get("kamikaze_crush")
    if kamikaze:
        if list(kamikaze.get("source_stat_influence") or [])!=["hp","vitality","attack"]:
            errors.append("kamikaze_crush: source influence must be HP + Vitality + Attack")
        if str(kamikaze.get("scale"))!="attack":
            errors.append("kamikaze_crush: primary scale must be Attack")
        if str(kamikaze.get("secondary_scale"))!="constitution":
            errors.append("kamikaze_crush: Vitality must map to Constitution")
        if str(kamikaze.get("target_mode"))!="one_enemy":
            errors.append("kamikaze_crush: target mode must be one enemy")
        if not bool(kamikaze.get("damage_from_current_hp")):
            errors.append("kamikaze_crush: current HP must influence damage")
        if not bool(kamikaze.get("shield_improves_damage")):
            errors.append("kamikaze_crush: equipped shield must improve damage")
        if not bool(kamikaze.get("vmax_power_and_feedback")):
            errors.append("kamikaze_crush: V-MAX must increase power and Feedback")
        if bool(kamikaze.get("numeric_source_defined")):
            errors.append("kamikaze_crush: numeric modifiers must remain marked unsourced")
        if list(kamikaze.get("source_properties") or [])!=[]:
            errors.append("kamikaze_crush: source Properties must remain None")

    starlight=rows.get("starlight_shower")
    if starlight:
        if list(starlight.get("source_stat_influence") or [])!=["magic_attack"]:
            errors.append("starlight_shower: source influence must be Magic Attack")
        if int(starlight.get("uoss_mp_cost",0) or 0)!=225:
            errors.append("starlight_shower: normal MP cost must be 225")
        if int(starlight.get("uoss_vmax_mp_cost",0) or 0)!=300:
            errors.append("starlight_shower: V-MAX MP cost must be 300")
        if str(starlight.get("target_mode"))!="single_or_diminishing_aoe":
            errors.append("starlight_shower: normal target mode must be single or diminishing AoE")
        if not bool(starlight.get("aoe_diminishing")):
            errors.append("starlight_shower: normal multi-target mode must diminish")
        if str(starlight.get("vmax_target_mode"))!="all_enemies_non_diminishing":
            errors.append("starlight_shower: V-MAX must target all enemies non-diminishing")
        if not bool(starlight.get("vmax_aoe_non_diminishing")):
            errors.append("starlight_shower: V-MAX non-diminishing flag missing")
        if bool(starlight.get("diminishing_numeric_source_defined")):
            errors.append("starlight_shower: diminishing numeric curve must remain marked unsourced")
        if list(starlight.get("source_properties") or [])!=[]:
            errors.append("starlight_shower: source Properties must remain None")

    vmax=rows.get("vmax")
    if vmax:
        if str(vmax.get("scale"))!="willpower":
            errors.append(f"vmax:scale={vmax.get('scale')} expected=willpower")
        if str(vmax.get("support_weapon_model"))!="mec_soul_weapon":
            errors.append(
                f"vmax:support_weapon_model={vmax.get('support_weapon_model')} expected=mec_soul_weapon"
            )
        if not bool(vmax.get("duration_scales_with_skill_level")):
            errors.append("vmax:missing skill-level duration scaling")
        if not bool(vmax.get("duration_scales_with_will")):
            errors.append("vmax:missing WILL duration scaling")
        if int(vmax.get("cooldown",0) or 0)!=0 or bool(vmax.get("mechanic_cooldown")):
            errors.append("vmax: reuse cooldown must remain disabled")
        _praise=((vmax.get("vmax_status_sources") or {}).get("praise") or {})
        if str(_praise.get("effect"))!="attack_power_up":
            errors.append("vmax:praise must raise Attack power")
        _preach=((vmax.get("vmax_status_sources") or {}).get("preach") or {})
        if str(_preach.get("effect"))!="magic_attack_up":
            errors.append("vmax:preach must raise Magic Attack")
        if "will" not in list(_preach.get("source_stat_influence") or []):
            errors.append("vmax:preach missing WILL influence metadata")
        _protect=((vmax.get("vmax_status_sources") or {}).get("protect") or {})
        if str(_protect.get("effect"))!="incoming_physical_damage_down":
            errors.append("vmax:protect must reduce incoming physical damage")
        if "will" not in list(_protect.get("source_stat_influence") or []):
            errors.append("vmax:protect missing WILL influence metadata")
        _shell=((vmax.get("vmax_status_sources") or {}).get("shell") or {})
        if str(_shell.get("effect"))!="incoming_magic_damage_down":
            errors.append("vmax:shell must reduce incoming magic damage")
        if "will" not in list(_shell.get("source_stat_influence") or []):
            errors.append("vmax:shell missing WILL influence metadata")
        _regen=((vmax.get("vmax_status_sources") or {}).get("regen") or {})
        if str(_regen.get("effect"))!="periodic_small_hp_heal":
            errors.append("vmax:regen must be periodic HP healing")
        if "will" not in list(_regen.get("source_stat_influence") or []):
            errors.append("vmax:regen missing WILL influence metadata")
        if bool(_regen.get("tick_cadence_source_defined")):
            errors.append("vmax:regen cadence must remain unsourced until exact data exists")
        if bool(_regen.get("heal_amount_source_defined")):
            errors.append("vmax:regen heal amount must remain unsourced until exact data exists")
    for protocol_id,specials in MEC_PROTOCOL_SKILLS_V11155.items():
        protocol_row=next((row for row in CLASS_SKILLS.get("Mec",[]) if row.get("id")==protocol_id),None)
        if not protocol_row:
            errors.append(f"missing protocol row:{protocol_id}")
            continue
        if not bool(protocol_row.get("automatic")):
            errors.append(f"{protocol_id}:not automatic")
        if str(protocol_row.get("level_effect"))!="increases_mapped_skill_damage":
            errors.append(f"{protocol_id}:bad level effect")
        if float(protocol_row.get("protocol_multiplier_level1",0.0) or 0.0)!=1.05:
            errors.append(f"{protocol_id}:bad level1 multiplier")
        if float(protocol_row.get("protocol_multiplier_level600",0.0) or 0.0)!=1.75:
            errors.append(f"{protocol_id}:bad level600 multiplier")
    support_contract=MEC_CANONICAL_CONTRACT_V11149["branches"]["support"]
    if str(support_contract.get("support_weapon"))!="soul_weapon":
        errors.append(
            f"support:weapon={support_contract.get('support_weapon')} expected=soul_weapon"
        )
    for sid,(unlock,branch) in _MEC_EXPECTED_V11149.items():
        row=rows.get(sid)
        if not row: errors.append(f"missing:{sid}"); continue
        if int(row.get("unlock",0))!=unlock: errors.append(f"{sid}:unlock={row.get('unlock')} expected={unlock}")
        if str(row.get("mec_branch"))!=branch: errors.append(f"{sid}:branch={row.get('mec_branch')} expected={branch}")
        if int(row.get("cooldown",0) or 0)!=0:
            errors.append(f"{sid}:cooldown={row.get('cooldown')} expected=0")
        if row.get("mechanic_cooldown"):
            errors.append(f"{sid}:mechanic cooldown flag is forbidden")
        expected_protocol=protocol_by_special.get(sid)
        if expected_protocol:
            actual=MEC_CANONICAL_CONTRACT_V11149["branches"][branch].get("protocol")
            if actual!=expected_protocol:
                errors.append(f"{sid}:protocol={actual} expected={expected_protocol}")
        if sid in source_mp_costs and int(row.get("uoss_mp_cost",0) or 0)!=source_mp_costs[sid]:
            errors.append(f"{sid}:mp={row.get('uoss_mp_cost')} expected={source_mp_costs[sid]}")
        if sid in source_support_mp_costs and int(row.get("uoss_support_mp_cost",0) or 0)!=source_support_mp_costs[sid]:
            errors.append(f"{sid}:support_mp={row.get('uoss_support_mp_cost')} expected={source_support_mp_costs[sid]}")
    return {"version":"1.11.49","checked":len(_MEC_EXPECTED_V11149),"errors":errors,"error_count":len(errors)}


def _v0317_install_engineer_toolkit():
    rows = CLASS_SKILLS.get("Inżynier", [])
    if len(rows) < 19:
        return
    specs = [
      # name, unlock, kind, source_ap_cost, special, category, description
      ("Auto Crossbow",1,"aoe_damage",100,"auto_crossbow","area","Automatyczna kusza ostrzeliwuje wszystkich przeciwników. Ulepszenie zwiększa obrażenia."),
      ("Mako Gun",1,"damage",100,"mako_gun","single","Losowy atak żywiołowy. Ulepszenie zwiększa obrażenia i dobiera skuteczniejszy element."),
      ("Bio Blaster",1,"aoe_damage",200,"bio_blaster","area","Fala toksycznego gazu na wszystkich przeciwników. Ulepszenie zwiększa obrażenia i siłę efektu biologicznego."),
      ("Scanner",1,"damage",500,"scanner","utility","Skanuje cel i podaje HP, rangę, typ, odporności oraz słabości. Nie podlega Upgrade."),
      ("Flash",8,"aoe_damage",800,"flash","area","Święte światło uderza wszystkich przeciwników. Ulepszenie zwiększa obrażenia i wzmacnia efekt oślepienia/Guard Break."),
      ("Debilitator",8,"damage",1000,"debilitator","utility","Nadaje celowi losową słabość żywiołową. Ulepszenie nadaje trzy słabości jednocześnie."),
      ("Hypercharge",8,"passive",500,"hypercharge","passive","Pasywnie wzmacnia pojedyncze ofensywne narzędzia Inżyniera, w tym Mega Bomb."),
      ("Lindblum Assembly",8,"passive",500,"lindblum","passive","Pasywnie wzmacnia obszarowe narzędzia Inżyniera."),
      ("Improved Kinematics",8,"passive",500,"kinematics","passive","Pasywnie wydłuża efekty statusowe narzędzi Inżyniera."),
      ("Drill",12,"damage",1500,"drill","single","Wiertło przebija ochronę celu. Ulepszenie zwiększa obrażenia i wzmacnia przebicie ochrony."),
      ("Napalm",12,"aoe_damage",1500,"napalm","area","Ognista bomba uderza wszystkich przeciwników. Ulepszenie zwiększa obrażenia i pokrywa cele łatwopalnym olejem."),
      ("Launcher",14,"aoe_damage",2500,"launcher","area","Do czterech pocisków trafia losowe cele, każdy redukuje bieżące HP celu o połowę. Ulepszenie: do sześciu pocisków."),
      ("Upgrade",16,"utility",15000,"upgrade","utility","Trwałe narzędzie użytkowe Inżyniera: ulepsza wybrane narzędzie. Nie jest buffem bojowym. Bazowo 1 slot; Silver Gear i Gold Battery zwiększają limit."),
      ("Noise Blaster",18,"aoe_damage",2500,"noise_blaster","area","Fala dźwięku uderza i ucisza przeciwników. Ulepszenie zwiększa obrażenia i efekt kontroli."),
      ("Chainsaw",20,"damage",5000,"chainsaw","single","Piła łańcuchowa zadaje ciężkie obrażenia albo efekt Demi. Ulepszenie wzmacnia Demi do Quarter."),
      ("Mega Bomb",21,"aoe_damage",5000,"mega_bomb","single","Potężna eksplozja: główny cel otrzymuje pełne obrażenia, pozostali mniejsze. Ulepszenie zwiększa obrażenia wszystkim celom."),
      ("Silver Gear",21,"passive",15000,"silver_gear","passive","Pasywnie dodaje drugi slot systemu Upgrade."),
      ("Air Anchor",23,"damage",7500,"air_anchor","single","Kotwica wbija się w cel i zadaje obrażenia. Ulepszenie zwiększa moc efektu."),
      ("Gold Battery",23,"passive",15000,"gold_battery","passive","Pasywnie dodaje trzeci slot systemu Upgrade."),
    ]
    # Replace only 19 generated entries so total class skill count remains 123.
    for index, spec in enumerate(specs):
        name,unlock,kind,source_ap,special,category,desc = spec
        row=rows[index]
        row.clear()
        row.update({
          "id":f"v0317_engineer_{special}","name":name,
          "aliases":[name.casefold()],"unlock":unlock,"kind":kind,"cooldown":4,"mana":0,
          "base_power":0,
          "source_ap_cost":source_ap,
          "source_ap_semantics":"learning_points",
          "source_ap_is_damage_power":False,
          "engineer_tool":True,"engineer_special":special,
          "engineer_category":category,"desc":desc,
        })
        if kind in ("damage","aoe_damage"):
            row.update({"scale":"dexterity","mult":1.0})
            if kind=="aoe_damage": row["aoe"]=True
        _harmful_engineer_effects={
            "bio_blaster":["poison"],
            "flash":["blind","guard_break"],
            "debilitator":["elemental_vulnerability"],
            "drill":["armor_break"],
            "napalm":["flammable_oil"],
            "noise_blaster":["silence","slow"],
            "chainsaw":["hp_leak"],
            "air_anchor":["air_anchor"],
        }
        if special in _harmful_engineer_effects:
            row.update({
                "soulbound_target_scope":"enemy_only",
                "soulbound_harmful_debuff":True,
                "enemy_debuffs":list(_harmful_engineer_effects[special]),
            })
        if special=="upgrade": row.update({"boost":1.0,"duration":1})
    CLASS_SKILLS["Inżynier"] = rows

