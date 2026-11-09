"""Wydzielone metody oryginalne v109 — bez zmian mechaniki.

Testy zgodnosci porownuja AST z poprzednia paczka, nie tylko nazwy.
"""
# -*- coding: utf-8 -*-
"""Damage and combat-consider calculations.

v0.47.0: explicit combat architecture; no compatibility-global injection.
"""
import math
import random
import sys

from core.progression_600 import CHARACTER_MAX_LEVEL
from core.player_math import (
    character_attribute_power,
    character_offensive_build_multiplier,
)
from systems.equipment_crafting import class_equipment_base_stat_pair
from systems.v106_combat_encounter_level import effective_encounter_level_v106
from systems.adaptive_combat import (
    adaptive_combat_rank_v11330,
    adaptive_reward_multiplier_v11330,
    adaptive_target_incoming_fraction_v11330,
    adaptive_target_max_hp_v11330,
    adaptive_beginner_incoming_target_v2005,
    adaptive_encounter_stage_v2325,
)
from systems.elite_variants import elite_average_enemy_multiplier_v11338
from systems.elemental_combat import elemental_expected_incoming_multiplier_v11339
from systems.party_synergies import party_synergy_damage_multiplier_v11338
from data.mobs import MOB_TEMPLATES
from data.rooms import ROOMS  # v2.00.7: CONSIDER region stage (SB-30B15AD1)

MEC_COMBAT_MASTERY_DAMAGE_MULTIPLIER_V1124 = 1.20


class CombatMasteryV109Mixin:
    def mec_combat_mastery_active_v1124(self):
                """Selected Mec inherent adapted to Soulbound's one-Soul-Weapon model."""
                c = self.character
                if not c or c.class_name != "Mec":
                    return False
                # Source explicitly says Combat Mastery does not work unarmed.
                if not str(getattr(c, "soul_weapon", "") or "").strip():
                    return False
                return self.job_ability_selected(
                    "inherent", "v0319_mec_combat_mastery"
                )

    def basic_attack_inherent_multiplier_v1124(self):
                if self.mec_combat_mastery_active_v1124():
                    return MEC_COMBAT_MASTERY_DAMAGE_MULTIPLIER_V1124
                return 1.0

    def basic_attack_build_v11196(self):
                """Return (power, raw stat, channel) for the active class build."""
                c = self.character
                flat = self.equipment_flat_power_totals_v11187()
                if c.class_type == "physical":
                    # UOSS Combat Mastery only works with a purely STR melee weapon.
                    # Soulbound has one persistent Mec Soul Weapon instead of separate
                    # axe/claw/greatsword/etc. slots, so selecting Combat Mastery makes
                    # the ordinary Mec Soul Weapon attack use its melee/STR role.
                    if self.mec_combat_mastery_active_v1124():
                        raw_stat = max(1, int(self.effective_strength()))
                        power = self.physical_power()
                    else:
                        primary, _secondary = class_equipment_base_stat_pair(c.class_name)
                        if primary == "dexterity":
                            raw_stat = max(1, int(self.effective_dexterity()))
                            power = (
                                character_attribute_power(
                                    c.character_level, raw_stat
                                )
                                + int(flat["attack"])
                                + int(flat["weapon_power"])
                            )
                        else:
                            raw_stat = max(1, int(self.effective_strength()))
                            power = self.physical_power()
                    return max(1, int(power)), raw_stat, "physical"

                raw_stat = max(1, int(self.effective_intelligence()))
                return max(1, int(self.spell_power())), raw_stat, "magic"

