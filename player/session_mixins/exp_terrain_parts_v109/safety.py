# -*- coding: utf-8 -*-
"""Soulbound v109: oryginalne metody, wydzielone bez zmiany kodu."""
from __future__ import annotations
from .dependencies import *

class ExpSafetyV109Mixin:
    def character_progression_power(self):
            """Generated combat progression estimate 1-600, including Character Level."""
            return self.combat_xp_power_v023()

    def exp_area_target_power(self, area, room_id=None):
            static_target = int(
                EXP_AREA_TARGET_POWER.get(
                    area.get("id"),
                    max(1, int(area.get("soul_min", 1))),
                )
            )
            room_id = room_id or ""

            # v0.8.66: jeśli konkretny pokój ma spawny, realne moby mają
            # pierwszeństwo przed szeroką etykietą biomu. Naprawia to m.in.
            # Pradawny Szlak Bestii / Otchłań Trolli / Grobowiec Słońca.
            if room_id:
                profile = v0866_room_threat_profile(room_id, fallback=static_target)
                if profile["normal_count"] or profile["variant_count"] or profile["boss_count"]:
                    return max(1, min(CHARACTER_MAX_LEVEL, int(profile["target"])))

            # v0.8.66: dla listy expowisk bez konkretnego pokoju bierzemy
            # realny próg wejściowy z lokacji wskazanych przez guide. Dzięki temu
            # szeroka strefa z endgame odnogą (np. Dzicz) nie udaje w całości
            # poziomu 200, ale też Kanały/Cmentarz nie są zaniżane starą etykietą.
            guide = str(area.get("guide", "") or "").strip()
            if guide:
                matches = self.find_room_matches(guide)
                direct_targets = []
                zones = set()
                for target_room in matches:
                    room = ROOMS.get(target_room, {})
                    if room.get("zone"):
                        zones.add(room.get("zone"))
                    profile = v0866_room_threat_profile(
                        target_room, fallback=static_target
                    )
                    if profile["normal_count"] or profile["variant_count"]:
                        direct_targets.append(int(profile["target"]))
                if direct_targets:
                    return max(1, min(CHARACTER_MAX_LEVEL, min(direct_targets)))
                zone_entries = []
                for zone in zones:
                    profile = v0866_zone_threat_profile(zone)
                    if profile.get("min") is not None:
                        zone_entries.append(int(profile["min"]))
                if zone_entries:
                    return max(1, min(CHARACTER_MAX_LEVEL, min(zone_entries)))

            return max(1, min(CHARACTER_MAX_LEVEL, static_target))

    def exp_area_dynamic_threat(self, area, room_id=None):
            power = self.character_progression_power()
            target = self.exp_area_target_power(area, room_id=room_id)
            label = v0866_threat_label(target, power)
            return label, target, power

    def exp_area_character_level_band_v03012(self, area):
            """Zwraca zakres Levelu postaci właściwy dla terenu.

            Stare pola soul_min/mastery_min są traktowane tylko jako dane zgodności.
            Dla nazwanych regionów endgame zachowujemy jawne zakresy 300-600
            zapisane w ich kategorii difficulty.
            """
            difficulty = str(area.get("difficulty") or "")
            match = re.search(r"(\d{1,3})\s*[-–]\s*(\d{1,3})", difficulty)
            if match:
                minimum = max(1, min(CHARACTER_MAX_LEVEL, int(match.group(1))))
                maximum = max(minimum, min(CHARACTER_MAX_LEVEL, int(match.group(2))))
                return minimum, maximum
            minimum = max(1, int(area.get("soul_min", 1) or 1))
            maximum = max(minimum, int(area.get("soul_max", minimum) or minimum))
            return min(CHARACTER_MAX_LEVEL, minimum), min(CHARACTER_MAX_LEVEL, maximum)

