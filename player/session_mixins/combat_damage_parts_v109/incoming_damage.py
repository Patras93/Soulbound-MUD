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


class CombatIncomingV109Mixin:
    def consider_enemy_expected_hit(self, template):
                damage_type = template.get("damage_type", "physical")
                raw = max(1.0, float(template.get("damage", 1)))

                if damage_type == "magic":
                    reduction = float(self.magic_defense())
                else:
                    reduction = float(self.defense())

                # Match real combat: flat Defense can strongly reward equipment,
                # but cannot erase enemy attacks completely. Bosses retain the
                # stricter 60% cap; ordinary enemies can be reduced by up to 75%.
                is_boss = bool(
                    template.get("boss")
                    or template.get("world_boss")
                    or template.get("crypt_boss")
                    or template.get("mythic_crypt_boss")
                    or template.get("astral_boss")
                    or template.get("mythic_astral_boss")
                    or template.get("boss_mechanic")
                )
                defense_cap_ratio = 0.60 if is_boss else 0.75
                reduction = min(reduction, raw * defense_cap_ratio)
                incoming = max(1.0, raw - reduction)

                if damage_type == "physical":
                    physical_race_percent = (
                        self.character.racial_physical_damage_reduction_percent()
                    )
                    incoming *= max(
                        0.0,
                        1.0 - physical_race_percent / 100.0,
                    )

                racial_percent = (
                    self.character.racial_damage_reduction_percent()
                )
                incoming *= max(
                    0.0,
                    1.0 - racial_percent / 100.0,
                )

                class_percent = (
                    self.character.class_damage_reduction_percent()
                )
                incoming *= max(
                    0.0,
                    1.0 - class_percent / 100.0,
                )

                # Unik obniża średnie obrażenia w dłuższej walce.
                incoming *= max(
                    0.0,
                    1.0 - self.dodge_chance(),
                )

                incoming *= elemental_expected_incoming_multiplier_v11339(template)
                return max(1.0, incoming)

