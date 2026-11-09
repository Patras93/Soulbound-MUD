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


class CombatHealthReadOnlyV109Mixin:
    def mob_effective_max_hp_v11330(self, mob, template=None):
                if mob is None:
                    return 1
                template = template or MOB_TEMPLATES.get(mob.template_id, {})
                return max(
                    1,
                    int(
                        getattr(mob, "adaptive_max_hp_v11330", 0)
                        or template.get("max_hp", 1)
                        or 1
                    ),
                )

