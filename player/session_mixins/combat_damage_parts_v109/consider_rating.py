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


class CombatRatingV109Mixin:
    def consider_rating(self, mob, template):
                preview = self.consider_adaptive_preview_v11331(mob, template)
                player_hit = preview["player_hit"]
                player_action = preview["player_action"]
                party_action = preview["party_action"]
                enemy_hit = preview["enemy_hit"]

                mob_hp = max(1, int(preview["current_hp"]))
                player_hp = max(1, int(self.current_hp))

                # In party play the encounter scales from total local party output,
                # so danger must be judged against the same local party rather than
                # pretending that the player fights the scaled target alone.
                actions_to_kill = mob_hp / max(1.0, party_action)
                enemy_actions_to_die = player_hp / max(1.0, enemy_hit)
                ratio = enemy_actions_to_die / max(0.01, actions_to_kill)

                # Boss mechanics are deliberately treated as extra danger.
                if template.get("boss_mechanic"):
                    ratio *= 0.82
                if (
                    template.get("crypt_boss")
                    or template.get("astral_boss")
                    or template.get("mythic_crypt_boss")
                    or template.get("mythic_astral_boss")
                ):
                    ratio *= 0.90
                if template.get("world_boss"):
                    ratio *= 0.90

                if ratio >= 3.0:
                    label = "bardzo słaby"
                    advice = "Powinien być dla ciebie łatwy."
                elif ratio >= 1.9:
                    label = "słaby"
                    advice = "Masz wyraźną przewagę."
                elif ratio >= 1.25:
                    label = "korzystny"
                    advice = "Masz przewagę, ale przeciwnik może zranić."
                elif ratio >= 0.80:
                    label = "porównywalny"
                    advice = "Walka może być wyrównana."
                elif ratio >= 0.50:
                    label = "niebezpieczny"
                    advice = "Przeciwnik ma przewagę. Przygotuj leczenie lub skille."
                elif ratio >= 0.28:
                    label = "bardzo niebezpieczny"
                    advice = "Ryzyko śmierci jest wysokie."
                else:
                    label = "śmiertelnie groźny"
                    advice = "Bez mocnego przygotowania lepiej go teraz nie atakować."

                return {
                    "label": label,
                    "advice": advice,
                    "player_hit": max(1, int(round(player_hit))),
                    "player_hits": int(preview["player_hits"]),
                    "player_action": max(1, int(round(player_action))),
                    "party_action": max(1, int(round(party_action))),
                    "enemy_hit": max(1, int(round(enemy_hit))),
                    "turns_to_kill": max(1, int(math.ceil(actions_to_kill))),
                    "turns_to_die": max(1, int(math.ceil(enemy_actions_to_die))),
                    "adaptive": preview,
                }

