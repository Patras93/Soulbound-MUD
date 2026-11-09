# -*- coding: utf-8 -*-
"""Soulbound v109: oryginalne metody, wydzielone bez zmiany kodu."""
from __future__ import annotations
from .dependencies import *

class ExpTerrainUIV109Mixin:
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

