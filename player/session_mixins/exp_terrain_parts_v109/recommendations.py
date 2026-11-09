# -*- coding: utf-8 -*-
"""Soulbound v109: oryginalne metody, wydzielone bez zmiany kodu."""
from __future__ import annotations
from .dependencies import *

class ExpRecommendationsV109Mixin:
    def exp_area_recommended(self, area, *, level=None, soul_level=None):
            """Recommend the ENTRY encounter, never just an obsolete soul range.

            Recommended zones must be plausible at the character's own level,
            even when multiclass equipment or high stats inflate combat power.
            Entry danger is computed from actual room spawns when possible;
            an empty entry room cannot mask the area's minimum danger.
            """
            # v29.10: zawsze biezacy Level postaci; 'level' sluzy tylko
            # porownaniu przed/po awansie, nie zapisujemy cache w bazie.
            level = max(1, min(CHARACTER_MAX_LEVEL, int(
                level if level is not None else
                (getattr(self.character, "character_level", 1) or 1)
            )))
            area_id = str(area.get("id", ""))
            soul_level = max(1, int(
                soul_level if soul_level is not None else
                (getattr(self.character, "soul_level", 1) or 1)
            ))
            if area_id in {"astral", "mythic_astral"} and soul_level < 100:
                return False
            minimum, maximum = self.exp_area_character_level_band_v03012(area)
            target = self.exp_area_target_power(area)
            # An open portal is not a recommendation. Explicit minimum danger
            # wins over misleading legacy fields (mythic crypt soul_min=1).
            target = max(target, int(EXP_AREA_TARGET_POWER.get(area_id, 1)))
            if area_id == "trening":
                return level <= 12
            # v30: fizyczne regiony 401-800 polecamy w ich wlasnym zakresie.
            # Dojscia sa otwarte; dotyczy jedynie listy sugerowanych expowisk.
            if area_id.startswith("v3000_"):
                return minimum <= level <= maximum
            # Otwarte krainy maja zakres do ok. 400, ale lochy pietrowe
            # skaluja sie dalej. Oceniaj osobno dostep do wejscia i glebie;
            # nie polecaj astralu bez wymaganej Duszy.
            scalable = {"krypta", "astral", "mythic_crypt", "mythic_astral"}
            if area_id in scalable and level > maximum:
                return True
            if area_id == "mythic_crypt":
                target = max(target, 130)
            elif area_id == "mythic_astral":
                target = max(target, 150)
            elif area_id == "astral":
                target = max(target, 110)
            elif area_id == "krypta":
                # Recommendation refers only to the first floor, not every
                # level of the infinite crypt or its tenth-floor bosses.
                target = max(target, 30)
            if level < max(1, minimum) and target > level + 8:
                return False
            if target >= level + 20:
                return False
            if target > level + 8:
                return False
            # Avoid suggesting trivial entry content as the primary grind.
            # Jawne zakresy endgame sa zamkniete (np. 390-400).
            # Po osiagnieciu 401 nie polecamy dalej Korony Swiata
            # jako swiezego terenu exp, tylko skalowane lochy.
            difficulty = str(area.get("difficulty") or "").lower()
            if "endgame" in difficulty and re.search(r"\d+\s*[-–]\s*\d+", difficulty):
                if level > maximum:
                    return False
            if level > max(maximum, target + 40):
                return False
            return True

    def recommended_exp_areas_v2910(self, level=None, *, soul_level=None):
            """Zawsze przeliczaj z aktualnego Levelu, bez starych snapshotow.

            Wybieraj najblizszy prog w normalnych obszarach. Przy levelach
            ponad udokumentowane zakresy preferuj lochy skalowane pietrami.
            """
            level = max(1, min(CHARACTER_MAX_LEVEL, int(
                level if level is not None else
                (getattr(self.character, "character_level", 1) or 1)
            )))
            selected = [
                area for area in EXP_AREAS
                if self.exp_area_recommended(area, level=level, soul_level=soul_level)
            ]
            scalable = {"krypta", "astral", "mythic_crypt", "mythic_astral"}

            def rating(area):
                area_id = str(area.get("id", ""))
                minimum, maximum = self.exp_area_character_level_band_v03012(area)
                target = max(minimum, self.exp_area_target_power(area))
                if minimum <= level <= maximum and area_id.startswith('v3000_'):
                    # v30: prawdziwa strefa 401-800 ma pierwszenstwo przed
                    # informacja o mozliwosci grindzenia pietrowych lochow.
                    return (-10, 0, area['name'])
                if level > maximum and area_id in scalable:
                    # Wejscie moze byc proste; wskaz odpowiednia glebokosc,
                    # nie oznaczaj pietra pierwszego jako przeciwnika Level 800.
                    return (20 + scalable_order.get(area_id, 9), 0, area['name'])
                distance = abs(level - target)
                if area_id == 'trening':
                    distance += 15
                if level > maximum:
                    distance += level - maximum
                return (distance, 0 if area_id not in scalable else 1, area['name'])

            scalable_order = {'krypta': 0, 'astral': 1, 'mythic_crypt': 2, 'mythic_astral': 3}
            return sorted(selected, key=rating)

    def exp_area_level_up_hint_v2910(self, old_level, new_level):
            """Jeden komunikat przy zmianie zestawu po kilku awansach naraz."""
            old_level, new_level = int(old_level), int(new_level)
            if new_level <= old_level:
                return None
            before = {str(a.get('id')) for a in self.recommended_exp_areas_v2910(old_level)}
            after = self.recommended_exp_areas_v2910(new_level)
            after_ids = {str(a.get('id')) for a in after}
            if before == after_ids:
                return None
            names = ', '.join(a['name'] for a in after[:3]) or 'brak bezpiecznych obszarów w katalogu'
            return (
                f'Polecane expowiska odświeżone po awansie na Level {new_level}: '
                f'{names}. Wpisz expowiska polecane, aby zobaczyc aktualna liste.'
            )

    def exp_area_soul_level_up_hint_v2910(self, old_soul_level, new_soul_level):
            """Oglos zmiane obszarow przy odblokowaniu poziomu Soul 100."""
            if int(new_soul_level) <= int(old_soul_level):
                return None
            before = {str(a.get('id')) for a in self.recommended_exp_areas_v2910(soul_level=old_soul_level)}
            after = self.recommended_exp_areas_v2910(soul_level=new_soul_level)
            if before == {str(a.get('id')) for a in after}:
                return None
            names = ', '.join(a['name'] for a in after[:3])
            return (
                f'Polecane expowiska odświeżone po awansie Soul Level {new_soul_level}: '
                f'{names}. Wpisz expowiska polecane.'
            )

    def exp_area_for_room(self, room_id=None):
            room_id = room_id or (self.character.room_id if self.character else "")
            if room_id == "training_ground":
                area_id = "trening"
            else:
                zone = ROOMS.get(room_id, {}).get("zone")
                area_id = EXP_ZONE_AREA_ID.get(zone)
            if not area_id:
                return None
            return next((a for a in EXP_AREAS if a.get("id") == area_id), None)

