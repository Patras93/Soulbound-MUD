# -*- coding: utf-8 -*-
"""EXP area recommendations and terrain information."""

# v0.44.0: explicit dependencies; no compatibility-global injection.
import re
from core.classes_skills import ROOMS
from core.mines_threat import (
    DYNAMIC_KILL_XP_MAX_MULTIPLIER,
    DYNAMIC_KILL_XP_MIN_MULTIPLIER,
    EXP_AREA_BASE_CATEGORY,
    EXP_AREA_TARGET_POWER,
    EXP_ZONE_AREA_ID,
    ITEMS,
    v0866_room_threat_profile,
    v0866_threat_label,
    v0866_zone_threat_profile,
)
from core.progression_600 import CHARACTER_MAX_LEVEL, SOUL_MAX_LEVEL
from core.progression_resources import FISHING_ROOMS, HERBALISM_ROOMS, WOODCUTTING_ROOMS, is_mining_room, v0190_mob_stage
from systems.content_registry import MOB_SPAWNS, MOB_TEMPLATES, NPCS, QUESTS
from world.dynamic_content import EXP_AREAS


class SessionExpTerrainMixin:

    def character_progression_power(self):
            """Generated combat progression estimate 1-600, including Character Level."""
            return self.combat_xp_power_v023()

    def combat_power_explanation_v110016(self):
            """Separate actual level from the estimate; never present it as a level."""
            level = max(1, int(getattr(self.character, "character_level", 1) or 1))
            power = self.character_progression_power()
            return (
                f"Poziom postaci: {level}. "
                f"Orientacyjna siła bojowa: {power}/{CHARACTER_MAX_LEVEL}. "
                "Siła bojowa uwzględnia biegłości, Duszę, statystyki i wyposażenie; "
                "nie zastępuje poziomu postaci ani nie gwarantuje wygranej."
            )

    def exp_area_safety_summary_v110016(self, area, room_id=None):
            """Show entry danger against real character level, not just combat score."""
            level = max(1, int(getattr(self.character, "character_level", 1) or 1))
            target = max(1, int(self.exp_area_target_power(area, room_id=room_id)))
            area_id = str(area.get("id", ""))
            target = max(target, int(EXP_AREA_TARGET_POWER.get(area_id, 1)))
            if area_id == "trening":
                return "Zagrożenie: bezpieczny plac treningowy."
            if area_id == "mythic_crypt":
                target = max(target, 130)
            elif area_id == "mythic_astral":
                target = max(target, 150)
            elif area_id == "astral":
                target = max(target, 110)
            elif area_id == "krypta":
                target = max(target, 30)
            gap = target - level
            if gap >= 20:
                label = "ekstremalnie niebezpieczny — NIEPOLECANY"
            elif gap > 8:
                label = "zbyt trudny — niepolecany"
            elif gap > 0:
                label = "trudny — zachowaj ostrożność"
            elif gap >= -15:
                label = "odpowiedni do rozważenia"
            else:
                label = "raczej łatwy na wejściu"
            return (
                f"Zagrożenie wejścia: {label}. "
                f"Orientacyjny próg przeciwników: {target}, "
                f"poziom postaci: {level}. "
                "Bossowie i głębsze piętra mogą być trudniejsze."
            )

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

    def exp_area_soul_text(self, area):
            minimum, maximum = self.exp_area_character_level_band_v03012(area)
            if minimum == maximum:
                return f"Level postaci {minimum}"
            return f"Level postaci {minimum}-{maximum}"

    def exp_area_category_text(self, area, room_id=None):
            base = EXP_AREA_BASE_CATEGORY.get(area.get("id"), "Umiarkowany")
            dynamic, target, power = self.exp_area_dynamic_threat(area, room_id=room_id)
            if area.get("id") == "trening":
                dynamic, target = "Treningowy (bezpieczny)", 1
            return (
                f"Kategoria bazowa: {base}. "
                f"Dla twojej obecnej postaci: {dynamic}. "
                f"Poziom postaci {self.character.character_level}, orientacyjna siła bojowa {power}/{CHARACTER_MAX_LEVEL}, "
                f"próg terenu około {target}/{CHARACTER_MAX_LEVEL}. "
                f"{self.exp_area_safety_summary_v110016(area, room_id=room_id)}"
            )

    def resolve_terrain_zone(self, query):
            raw = str(query or "").strip()
            q = self.normalize_description_query(raw)
            if q.startswith("info "):
                raw = raw.split(maxsplit=1)[1]
                q = self.normalize_description_query(raw)
            elif q == "info":
                return None, []

            if not q:
                return None, []

            # Najpierw dokładna nazwa strefy.
            exact_zones = []
            for room in ROOMS.values():
                zone = room.get("zone", "")
                if q == self.normalize_description_query(zone):
                    exact_zones.append(zone)
            exact_zones = sorted(set(exact_zones))
            if len(exact_zones) == 1:
                return exact_zones[0], exact_zones

            matches = self.find_room_matches(raw)
            zones = sorted({
                ROOMS[room_id].get("zone", "Nieznany teren")
                for room_id in matches
                if room_id in ROOMS
            })
            if len(zones) == 1:
                return zones[0], zones

            area = self.find_exp_area(raw)
            if area:
                guide_matches = self.find_room_matches(area["guide"])
                area_zones = sorted({
                    ROOMS[room_id].get("zone", "Nieznany teren")
                    for room_id in guide_matches
                    if room_id in ROOMS
                })
                if len(area_zones) == 1:
                    return area_zones[0], area_zones
                if area_zones:
                    return None, area_zones

            return None, zones

    def terrain_exp_areas(self, zone):
            result = []
            for area in EXP_AREAS:
                matches = self.find_room_matches(area["guide"])
                zones = {
                    ROOMS[room_id].get("zone")
                    for room_id in matches
                    if room_id in ROOMS
                }
                if zone in zones:
                    result.append(area)
            return result

    def terrain_professions(self, room_ids):
            room_ids = set(room_ids)
            result = []
            checks = (
                ("Wędkarstwo", FISHING_ROOMS),
                ("Drwalstwo", WOODCUTTING_ROOMS),
                ("Zielarstwo", HERBALISM_ROOMS),
            )
            for name, rooms in checks:
                if room_ids & set(rooms):
                    result.append(name)
            if any(is_mining_room(room_id) for room_id in room_ids):
                result.append("Górnictwo")
            if "alchemy_lab" in room_ids:
                result.append("Alchemia")
            if "crafting_workshop" in room_ids or "forge" in room_ids:
                result.append("Kowalstwo i Rzemiosło")
            if "blue_flame_kitchen" in room_ids or "inn" in room_ids:
                result.append("Gotowanie")
            if "jeweler_workshop" in room_ids:
                result.append("Jubilerstwo")
            return result

    async def show_terrain_info(self, query=""):
            raw = str(query or "").strip()
            if not raw or self.normalize_description_query(raw) == "info":
                zones = sorted(
                    {room.get("zone", "") for room in ROOMS.values() if room.get("zone")},
                    key=self.normalize_description_query,
                )
                await self.send("INFORMACJE O TERENIE")
                await self.send(
                    "Użycie: teren info <nazwa>. Przykład: teren info bagna."
                )
                await self.send(
                    f"Dostępnych stref: {len(zones)}. "
                    "Pełną listę lokacji nadal pokazuje mapa, a expowiska pokazują zakresy expienia."
                )
                return

            zone, candidates = self.resolve_terrain_zone(raw)
            if not zone:
                if candidates:
                    await self.send(
                        "Nazwa pasuje do kilku terenów: " + ", ".join(candidates) + ". "
                        "Podaj dokładniejszą nazwę."
                    )
                else:
                    await self.send(
                        "Nie rozpoznaję terenu. Przykład: teren info bagna, teren info góry."
                    )
                return

            room_ids = [
                room_id for room_id, room in ROOMS.items()
                if room.get("zone") == zone
            ]
            room_set = set(room_ids)
            npcs = sorted(
                {
                    npc.get("name", npc_id)
                    for npc_id, npc in NPCS.items()
                    if npc.get("room") in room_set
                },
                key=self.normalize_description_query,
            )
            giver_names = set(npcs)
            quests = sorted(
                {
                    quest.get("name", quest_id)
                    for quest_id, quest in QUESTS.items()
                    if quest.get("giver") in giver_names
                },
                key=self.normalize_description_query,
            )
            spawned_mobs = {
                mob_id
                for spawn_room, mob_id in MOB_SPAWNS
                if spawn_room in room_set
            }
            boss_ids = self.codex_boss_ids()
            bosses = sorted(
                {
                    MOB_TEMPLATES[mob_id]["name"]
                    for mob_id in spawned_mobs
                    if mob_id in boss_ids and mob_id in MOB_TEMPLATES
                },
                key=self.normalize_description_query,
            )
            enemy_names = sorted(
                {
                    MOB_TEMPLATES[mob_id]["name"]
                    for mob_id in spawned_mobs
                    if mob_id in MOB_TEMPLATES
                },
                key=self.normalize_description_query,
            )
            professions = self.terrain_professions(room_ids)
            areas = self.terrain_exp_areas(zone)

            await self.send(f"INFORMACJE O TERENIE: {zone}")
            await self.send(f"Lokacje w strefie: {len(room_ids)}.")
            balance_profile = v0866_zone_threat_profile(zone)
            if balance_profile.get("median") is not None:
                await self.send(
                    f"Realna siła zwykłych części terenu: od {balance_profile['min']} "
                    f"do {balance_profile['max']} na skali 1-600. "
                    f"Mediana {balance_profile['median']}, górne 20 procent około {balance_profile['p80']}."
                )
            if balance_profile.get("boss_max") is not None:
                await self.send(
                    f"Bossowie tej strefy: orientacyjna siła od {balance_profile['boss_min']} "
                    f"do {balance_profile['boss_max']} na skali 1-600."
                )
            if areas:
                soul_min = min(int(area["soul_min"]) for area in areas)
                soul_max = max(int(area["soul_max"]) for area in areas)
                difficulty = ", ".join(dict.fromkeys(area["difficulty"] for area in areas))
                # v0.8.54: bazowa kategoria + dynamiczna ocena względem bieżącej postaci.
                dynamic_labels = [self.exp_area_category_text(area) for area in areas]
                await self.send(
                    f"Orientacyjny Soul: {soul_min}-{soul_max}. Dawna trudność: {difficulty}."
                )
                for text in dict.fromkeys(dynamic_labels):
                    await self.send(text + ".")
                descriptions = list(dict.fromkeys(area["description"] for area in areas))
                await self.send("Opis: " + " ".join(descriptions))
            else:
                await self.send(
                    "Orientacyjny Soul: brak osobnego zakresu w expowiska; teren może pełnić funkcję huba lub strefy specjalnej."
                )

            await self.send(
                "NPC: " + (", ".join(npcs) if npcs else "brak stałych NPC") + "."
            )
            await self.send(
                "Questy: " + (", ".join(quests) if quests else "brak questów przypisanych do NPC tej strefy") + "."
            )
            await self.send(
                "Bossowie: " + (", ".join(bosses) if bosses else "brak wykrytych bossów") + "."
            )
            await self.send(
                f"Przeciwnicy: {len(enemy_names)} typów" +
                ((": " + ", ".join(enemy_names) + ".") if enemy_names and len(enemy_names) <= 12 else ".")
            )
            await self.send(
                "Profesje i aktywności: " +
                (", ".join(professions) if professions else "brak osobnej aktywności profesyjnej") + "."
            )
            await self.send(f"Dojście: prowadz {zone}.")
            await self.send(
                "Dodatkowo: expowiska <nazwa> pokazuje szczegóły expienia, a mapa pokazuje lokacje."
            )

    async def show_exp_area_details(self, area):
            recommended = (
                " Polecane dla ciebie."
                if self.exp_area_recommended(area)
                else ""
            )

            await self.send(
                f"{area['name']}. "
                f"{self.exp_area_soul_text(area)}. "
                f"{self.exp_area_category_text(area)}."
                f"{recommended}"
            )
            await self.send(
                f"Opis: {area['description']}"
            )
            await self.send(
                f"Przeciwnicy: {area['enemies']}."
            )
            await self.send(
                f"Uwagi: {area['note']}"
            )
            await self.send(
                f"Prowadzenie: prowadz {area['guide']}."
            )

    async def show_exp_areas(self, query=""):
            query = str(query or "").strip()
            normalized = (
                self.normalize_description_query(query)
                if query
                else ""
            )

            # v31: krotki podglad wielkich szescioczesciowych kronik 401-800.
            if normalized in {"kroniki", "kronika", "fabula 401-800", "saga"}:
                from world.v3100_endgame_chronicles import CHAPTERS
                await self.send('KRONIKI KRAIN 401-800. Po jednym NPC na krainę; przyjmij 1.')
                for slug, zone, low, high, mentor, camp, *_rest in CHAPTERS:
                    ids=[f'v3100_{slug}_quest_{i}' for i in range(1,7)]
                    completed=0
                    active=0
                    try:
                        for qid in ids:
                            state=self.server.db.quest(self.account_id,qid)
                            if state and state['status']=='completed':
                                completed+=1
                            elif state and state['status']=='active':
                                active+=1
                    except (AttributeError, TypeError, KeyError):  # AUDIT_INTENTIONAL_PASS: optional quest status overlay
                        # Katalog nadal dziala w sesji bez odczytu postepow.
                        pass
                    suffix=('ukończona' if completed==6 else
                            f'{completed}/6 ukończonych'+(', 1 aktywne' if active else ''))
                    await self.send(f'{zone}, Level {low}-{high}: {suffix}. '
                                    f'NPC: {mentor}, {camp}. Wejście: prowadz {zone.lower()}, '
                                    'potem trzeci pokój i wschód.')
                return

            recommendation_query = (
                normalized in {"polecane", "recommended", "dla mnie"}
                or normalized.startswith("polecane ")
                or normalized.startswith("recommended ")
                or normalized.startswith("dla mnie ")
            )
            if recommendation_query:
                parts = normalized.split()
                final = parts[-1] if parts else ""
                if final in {"wszystkie", "all", "wszystko"}:
                    limit = len(EXP_AREAS)
                elif final.isdigit():
                    limit = max(1, min(len(EXP_AREAS), int(final)))
                elif normalized in {"polecane", "recommended", "dla mnie"}:
                    limit = 5
                else:
                    await self.send("Użycie: expowiska polecane; expowiska polecane 10; expowiska polecane wszystkie.")
                    return
                areas = self.recommended_exp_areas_v2910()
                await self.send(
                    f"POLECANE EXPOWISKA. "
                    f"Level postaci: {self.character.character_level}. "
                    f"Orientacyjna siła bojowa: {self.character_progression_power()}/{CHARACTER_MAX_LEVEL}. "
                    "Lista jest liczona od nowa przy każdym wywołaniu, także po awansie. "
                    "Bossowie i głębsze piętra mogą być dużo trudniejsze."
                )
                if not areas:
                    await self.send(
                        "Brak terenu dokładnie w twoim "
                        "orientacyjnym zakresie. "
                        "Wpisz expowiska, aby zobaczyć wszystko."
                    )
                    return
                for index, area in enumerate(areas[:limit], 1):
                    level = int(self.character.character_level)
                    _, maximum = self.exp_area_character_level_band_v03012(area)
                    deep = str(area.get('id')) in {'krypta', 'astral', 'mythic_crypt', 'mythic_astral'} and level > maximum
                    warning = (' Skalowany loch: dobierz odblokowane piętro do swojej siły.' if deep else '')
                    await self.send(
                        f"{index}. {area['name']}. "
                        f"{self.exp_area_category_text(area)}. "
                        f"Prowadzenie: prowadz {area['guide']}.{warning}"
                    )
                if len(areas) > limit:
                    await self.send(
                        f"Pokazano {limit} z {len(areas)}. "
                        "Więcej: expowiska polecane 10 albo expowiska polecane wszystkie."
                    )
                return

            if query:
                area = self.find_exp_area(query)
                if not area:
                    await self.send(
                        "Nie rozpoznaję expowiska. "
                        "Wpisz expowiska, aby usłyszeć pełną listę."
                    )
                    return
                await self.show_exp_area_details(area)
                return

            await self.send(
                f"EXPOWISKA. Soul Level: {self.character.soul_level}. "
                f"Poziom postaci: {self.character.character_level}. Orientacyjna siła bojowa: {self.character_progression_power()}/{CHARACTER_MAX_LEVEL}."
            )
            await self.send(
                "Tereny mają kategorię bazową: Początkujący, Umiarkowany, Trudny, "
                "Śmiertelny lub Endgame. Ocena 'dla ciebie' zmienia się automatycznie "
                "wraz z Biegłością klas, Soul Levelem, statystykami i wyposażeniem."
            )

            for number, area in enumerate(
                EXP_AREAS,
                1,
            ):
                marker = (
                    " Polecane dla ciebie."
                    if self.exp_area_recommended(area)
                    else ""
                )
                await self.send(
                    f"{number}. {area['name']}. "
                    f"{self.exp_area_category_text(area)}. "
                    f"{area['description']}"
                    f"{marker}"
                )

            await self.send(
                "Szczegóły: expowiska nazwa. "
                "Tylko polecane: expowiska polecane. Więcej: expowiska polecane 10."
            )
