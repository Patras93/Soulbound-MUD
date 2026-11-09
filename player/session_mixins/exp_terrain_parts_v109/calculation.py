# -*- coding: utf-8 -*-
"""Soulbound v109: oryginalne metody, wydzielone bez zmiany kodu."""
from __future__ import annotations
from .dependencies import *

class ExpCalculationV109Mixin:
    def combat_xp_power_v023(self):
            """Generator-based combat power 1-600 across all progression axes."""
            active = self.active_class_names()
            masteries = [self.class_mastery_level(name) for name in active] or [1]
            highest_mastery = max(masteries)
            average_mastery = sum(masteries) / len(masteries)
            combat_stats = (
                self.effective_strength(), self.effective_dexterity(),
                self.effective_constitution(), self.effective_intelligence(),
                self.effective_willpower(),
            )
            average_stats = min(float(CHARACTER_MAX_LEVEL), sum(combat_stats) / len(combat_stats))
            gear_levels = []
            for row in self.server.db.equipment(self.account_id):
                item = ITEMS.get(row["item_id"], {})
                gear_levels.append(int(item.get("generator_level", 1) or 1))
            gear_power = min(float(CHARACTER_MAX_LEVEL), (sum(gear_levels) / len(gear_levels)) if gear_levels else 1.0)
            character_level = max(1, min(CHARACTER_MAX_LEVEL, int(getattr(self.character, "character_level", 1) or 1)))
            # Generated axes share the budget; no historical 1-200 branch remains.
            score = (
                character_level * 0.22
                + highest_mastery * 0.28
                + average_mastery * 0.08
                + min(float(SOUL_MAX_LEVEL), int(self.character.soul_level)) * 0.16
                + average_stats * 0.10
                + gear_power * 0.16
            )
            return max(1, min(CHARACTER_MAX_LEVEL, int(round(score))))

    def dynamic_kill_xp_profile(self, template, room_id=None):
            """Płynnie skaluje CAŁY EXP z zabicia do relacji siły 1-600.

            Mob silniejszy od postaci daje premię za ryzyko. Ten sam przeciwnik
            daje coraz mniej, kiedy postać rozwija Biegłość, Soul Level, staty i
            EQ. Spadek jest stopniowy, a nie progowy, więc nie ma nagłego urwania
            nagrody po przekroczeniu jednego sztucznego progu.
            """
            power = self.combat_xp_power_v023()
            target = v0190_mob_stage(template)
            delta = float(target) - float(power)

            if delta >= 0.0:
                # +40 siły moba ~= x1.25, +80 ~= x1.50, +160 ~= x2.00.
                multiplier = 1.0 + delta / 160.0
            else:
                # Farma przeciwnika słabszego o 30 ~= x0.90, 60 ~= x0.80,
                # 120 ~= x0.60. Minimalnie zostaje 35% bazowego EXP.
                multiplier = 1.0 + delta / 300.0
            multiplier = max(
                DYNAMIC_KILL_XP_MIN_MULTIPLIER,
                min(DYNAMIC_KILL_XP_MAX_MULTIPLIER, multiplier),
            )

            if delta <= -120:
                label = "trywialny"
            elif delta <= -60:
                label = "łatwy"
            elif delta <= -20:
                label = "korzystny"
            elif delta <= 20:
                label = "odpowiedni"
            elif delta <= 60:
                label = "trudny"
            elif delta <= 120:
                label = "śmiertelny"
            else:
                label = "ekstremalny"

            area = self.exp_area_for_room(room_id)
            return {
                "label": label,
                "multiplier": float(multiplier),
                "area": area.get("name") if area else None,
                "target": int(target),
                "power": int(power),
                "delta": int(round(delta)),
            }


    def exp_area_soul_text(self, area):
            minimum, maximum = self.exp_area_character_level_band_v03012(area)
            if minimum == maximum:
                return f"Level postaci {minimum}"
            return f"Level postaci {minimum}-{maximum}"


    def find_exp_area(self, query):
            wanted = self.normalize_description_query(query)
            if not wanted:
                return None

            exact = []
            partial = []

            for area in EXP_AREAS:
                names = (
                    area["id"],
                    area["name"],
                    *area.get("aliases", ()),
                )
                normalized = {
                    self.normalize_description_query(name)
                    for name in names
                }

                if wanted in normalized:
                    exact.append(area)
                elif any(
                    wanted in name
                    for name in normalized
                ):
                    partial.append(area)

            if exact:
                return exact[0]
            if len(partial) == 1:
                return partial[0]
            return None
