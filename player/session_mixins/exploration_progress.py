# -*- coding: utf-8 -*-
"""Treasure maps, exploration, progress, achievements and titles."""

import random
# v0.44.0: explicit dependencies; no compatibility-global injection.
from config.postal import GUIDE_CITY_HUBS_V0522, POSTAL_CITY_HUBS_V0522
from core.bootstrap_economy_professions import currency_reading_text
from core.classes_skills import ROOMS
from core.mines_threat import ITEMS
from network.protocol_gameplay_utils import find_by_name, normalize_lookup_text
from systems.content_registry import NPCS, QUESTS, MOB_SPAWNS, MOB_TEMPLATES
from systems.economy_income_balance import v1138_activity_income
from systems.game_feel_rewards import exploration_find_v11324
from world.dynamic_content import (
    ACHIEVEMENT_TRACKS,
    ALL_EXPLORATION_ROOMS,
    COLLECTION_CATALOGS,
    EXPLORATION_REWARD_ITEMS,
    EXPLORATION_ZONE_ROOMS,
    REGION_COLLECTION_ENTRIES,
    TRACKED_EXPLORATION_ZONES,
    _collection_slug,
    _zone_title,
)
from world.economy_quests import (
    COLLECTION_CATEGORY_LABELS,
    EXPLORATION_ZONE_MIN_ROOMS,
    INSTANCE_MAP_DEFS,
    instance_room_identity,
    instance_secret_index,
)
from world.generation_systems import (
    V013_FRONTIER_SIDE,
    V013_FRONTIER_SPECS,
    V018_EXPEDITIONS,
    V020_MEGADUNGEONS,
    _v0140_hash_int,
    v0130_frontier_room_id,
    v0130_frontier_room_identity,
    v0130_frontier_room_ids,
    v0140_has_mini_dungeon,
    v0140_mini_room_id,
    v0140_surface_secret_info,
    v0140_surface_secret_room_ids,
    v0180_archipelago_room_ids,
    v0180_has_great_ruin,
    v0180_ruin_room_id,
)
from world.ocean_expansion import UNDERWATER_DUNGEONS
from world.world_expansion_iv import ZONE_ROOM_IDS as V0800_ZONE_ROOM_IDS
from world.world_expansion_v import ARCHIPELAGO_DUNGEONS_V0900, CATACOMB_LEVELS_V0900


GLOBAL_DISCOVERY_ATLAS_CATEGORIES_V1120 = {
    "regions": {
        "label": "Regiony i Krainy",
        "aliases": ("regiony", "region", "krainy", "kraina", "kontynenty", "kontynent", "podziemne królestwa", "podziemia", "regions"),
        "achievement": ("global_atlas_regions_v1602", "Globalny Atlas: wszystkie regiony", "Gold"),
    },
    "cities": {
        "label": "Miasta",
        "aliases": ("miasta", "miasto", "cities", "city"),
        "achievement": ("global_atlas_cities_v1120", "Globalny Atlas: wszystkie miasta", "Gold"),
    },
    "islands": {
        "label": "Wyspy",
        "aliases": ("wyspy", "wyspa", "islands", "island", "archipelagi", "archipelag"),
        "achievement": ("global_atlas_islands_v1120", "Globalny Atlas: wszystkie wyspy", "Gold"),
    },
    "dungeons": {
        "label": "Lochy",
        "aliases": ("lochy", "loch", "dungeons", "dungeon", "podziemia"),
        "achievement": ("global_atlas_dungeons_v1120", "Globalny Atlas: wszystkie lochy", "Platinum"),
    },
    "platforms": {
        "label": "Platformy oceaniczne",
        "aliases": ("platformy", "platforma", "platformy oceaniczne", "platforma oceaniczna", "platforms"),
        "achievement": ("global_atlas_platforms_v1120", "Globalny Atlas: wszystkie platformy oceaniczne", "Silver"),
    },
    "ruins": {
        "label": "Ruiny",
        "aliases": ("ruiny", "ruina", "ruins", "ruin"),
        "achievement": ("global_atlas_ruins_v1120", "Globalny Atlas: wszystkie ruiny", "Platinum"),
    },
    "superbosses": {
        "label": "Superbossowie",
        "aliases": ("superbossy", "superboss", "superbossowie", "superbosses", "bossowie specjalni"),
        "achievement": ("global_atlas_superbosses_v1120", "Globalny Atlas: wszystkie areny superbossów", "Platinum"),
    },
    "secrets": {
        "label": "Sekretne lokacje",
        "aliases": ("sekrety", "sekret", "sekretne lokacje", "secrets", "secret"),
        "achievement": ("global_atlas_secrets_v1120", "Globalny Atlas: wszystkie sekretne lokacje", "Platinum"),
    },
}
GLOBAL_DISCOVERY_ATLAS_MASTER_V1120 = (
    "global_atlas_complete_v1120",
    "Globalny Atlas: cały odkryty świat",
    "Platinum",
)
GLOBAL_DISCOVERY_ATLAS_MASTER_TITLE_V1120 = "Kartograf Całego Świata"


class SessionExplorationProgressMixin:

    def global_discovery_place_v1120(self, key, name, room_ids=(), prefixes=(), hidden=False, collection=None, collection_key=None):
            return {
                "key": str(key),
                "name": str(name),
                "room_ids": tuple(str(value) for value in room_ids if value),
                "prefixes": tuple(str(value) for value in prefixes if value),
                "hidden": bool(hidden),
                "collection": collection,
                "collection_key": collection_key,
            }

    def global_discovery_atlas_catalog_v1120(self):
            """Finite, source-backed discovery catalog built from the live world registries."""
            catalog = {key: [] for key in GLOBAL_DISCOVERY_ATLAS_CATEGORIES_V1120}

            # Miasta: one discovery per actual courier/city hub. Expansions extend
            # these registries, so new cities automatically join the atlas.
            city_names = tuple(dict.fromkeys(
                tuple(GUIDE_CITY_HUBS_V0522) + tuple(POSTAL_CITY_HUBS_V0522)
            ))
            for city in city_names:
                rooms = tuple(dict.fromkeys((
                    GUIDE_CITY_HUBS_V0522.get(city),
                    POSTAL_CITY_HUBS_V0522.get(city),
                )))
                catalog["cities"].append(self.global_discovery_place_v1120(
                    f"city:{normalize_lookup_text(city)}", city, room_ids=rooms
                ))

            # Current authored territories, including 1.50 and 1.60. These are
            # discovered from actual rooms rather than a static historical list.
            # A single visited room in a region records its discovery.
            region_rooms = {}
            for rid, room in ROOMS.items():
                if (rid.startswith("v1500_") or rid.startswith("v1600_") or rid.startswith("v1700_")
                        or rid.startswith("v1300_orc")) and not rid.startswith("v1500_echo_"):
                    zone = str(room.get("zone") or "").strip()
                    if zone:
                        region_rooms.setdefault(zone, []).append(rid)
            for zone, room_ids in sorted(region_rooms.items(), key=lambda x: normalize_lookup_text(x[0])):
                catalog["regions"].append(self.global_discovery_place_v1120(
                    f"region:authored:{normalize_lookup_text(zone)}", zone, room_ids=room_ids
                ))

            # Fixed Broken Star islands.
            for zone, room_ids in sorted(V0800_ZONE_ROOM_IDS.items(), key=lambda row: normalize_lookup_text(row[0])):
                if "wyspa" not in normalize_lookup_text(zone):
                    continue
                catalog["islands"].append(self.global_discovery_place_v1120(
                    f"island:v0800:{normalize_lookup_text(zone)}", zone, room_ids=room_ids
                ))

            # Deterministic expedition archipelagos.
            for expedition_id, spec in V018_EXPEDITIONS.items():
                catalog["islands"].append(self.global_discovery_place_v1120(
                    f"island:v018:{expedition_id}",
                    spec["name"],
                    room_ids=v0180_archipelago_room_ids(expedition_id),
                ))

            # Major persistent dungeon complexes. A complex is discovered on the
            # first visited room; the atlas does not require clearing every floor.
            dungeon_defs = (
                ("deep_mine", "Kopalnia Głębinowa", (), ("mine_floor_",)),
                ("crypt", "Krypta Nieskończona", (), ("crypt_floor_",)),
                ("astral", "Wieża Astralna", (), ("astral_floor_",)),
                ("mythic_crypt", "Mityczna Krypta", (), ("mythic_crypt_floor_",)),
                ("mythic_astral", "Mityczna Wieża Astralna", (), ("mythic_astral_floor_",)),
                ("giant_fortress", "Twierdza Gigantów", (), ("giant_fortress_",)),
                ("crystal_grotto", "Kryształowe Groty", (), ("prof_crystal_mine_",)),
                ("sunken_grotto", "Zatopiona Grota", (), ("prof_sunken_grotto_",)),
                ("ancient_forest", "Pradawny Las", (), ("prof_ancient_forest_",)),
                ("alchemy_garden", "Ogród Alchemika", (), ("prof_alchemy_garden_",)),
                ("magitek", "Kompleks Magitek 2.0", (), ("magitek_",)),
                ("echo", "Nieskończony Labirynt Echa", ("v1500_echo_entry",), ("v1500_echo_",)),
            )
            for key, name, room_ids, prefixes in dungeon_defs:
                catalog["dungeons"].append(self.global_discovery_place_v1120(
                    f"dungeon:{key}", name, room_ids=room_ids, prefixes=prefixes
                ))

            troll_rooms = tuple(
                rid for rid, room in ROOMS.items()
                if str(room.get("zone") or "") == "Jaskinia Trolli"
            )
            if troll_rooms:
                catalog["dungeons"].append(self.global_discovery_place_v1120(
                    "dungeon:troll_cave", "Jaskinia Trolli", room_ids=troll_rooms
                ))

            catacomb_rooms = tuple(
                rid for floor_rooms in CATACOMB_LEVELS_V0900.values() for rid in floor_rooms
            )
            if catacomb_rooms:
                catalog["dungeons"].append(self.global_discovery_place_v1120(
                    "dungeon:catacombs_v0900", "Katakumby pod Świątynią", room_ids=catacomb_rooms
                ))

            for key, room_ids in ARCHIPELAGO_DUNGEONS_V0900.items():
                first = next(iter(room_ids), None)
                name = str(ROOMS.get(first, {}).get("zone") or key.replace("_", " ").title())
                catalog["dungeons"].append(self.global_discovery_place_v1120(
                    f"dungeon:archipelago:{key}", name, room_ids=room_ids
                ))

            for key, spec in V020_MEGADUNGEONS.items():
                catalog["dungeons"].append(self.global_discovery_place_v1120(
                    f"dungeon:mega:{key}", spec["name"], prefixes=(f"v020_mega_{key}_",)
                ))

            # Every deterministic procedural mini-dungeon is a long-term discovery.
            for kind, spec in V013_FRONTIER_SPECS.items():
                for y in range(V013_FRONTIER_SIDE):
                    for x in range(V013_FRONTIER_SIDE):
                        if not v0140_has_mini_dungeon(kind, x, y):
                            continue
                        prefix = f"v0140_mini_{kind}_{x:02d}_{y:02d}_"
                        catalog["dungeons"].append(self.global_discovery_place_v1120(
                            f"dungeon:mini:{kind}:{x}:{y}",
                            f"Ukryty mini-loch — {spec['zone']}, sektor {x+1}-{y+1}",
                            prefixes=(prefix,), hidden=True,
                        ))

            # Ocean platforms are future-proofed by metadata/name rather than one hardcoded ID.
            for rid, room in ROOMS.items():
                rid_norm = normalize_lookup_text(rid)
                name = str(room.get("name") or rid)
                name_norm = normalize_lookup_text(name)
                zone_norm = normalize_lookup_text(str(room.get("zone") or ""))
                if rid == "ocean_platform" or (
                    "platform" in name_norm
                    and ("ocean" in rid_norm or "ocean" in zone_norm or "wybrzez" in zone_norm)
                ):
                    catalog["platforms"].append(self.global_discovery_place_v1120(
                        f"platform:{rid}", name, room_ids=(rid,)
                    ))

            # Fixed ruin zones (procedural/ocean ruins are catalogued below).
            fixed_ruin_zones = {}
            for rid, room in ROOMS.items():
                if rid.startswith("v018_ruin_") or rid.startswith("v1000_ruin_"):
                    continue
                zone = str(room.get("zone") or "")
                if "ruin" in normalize_lookup_text(zone):
                    fixed_ruin_zones.setdefault(zone, []).append(rid)
            for zone, room_ids in sorted(fixed_ruin_zones.items(), key=lambda row: normalize_lookup_text(row[0])):
                catalog["ruins"].append(self.global_discovery_place_v1120(
                    f"ruin:zone:{normalize_lookup_text(zone)}", zone, room_ids=room_ids
                ))

            # Ocean 2.0 submerged ruins.
            for key, spec in UNDERWATER_DUNGEONS.items():
                catalog["ruins"].append(self.global_discovery_place_v1120(
                    f"ruin:ocean:{key}", spec["name"], room_ids=spec["rooms"]
                ))

            # Deterministic Great Ruins on the procedural frontier.
            for kind, spec in V013_FRONTIER_SPECS.items():
                for y in range(V013_FRONTIER_SIDE):
                    for x in range(V013_FRONTIER_SIDE):
                        if not v0180_has_great_ruin(kind, x, y):
                            continue
                        prefix = f"v018_ruin_{kind}_{x:02d}_{y:02d}_"
                        catalog["ruins"].append(self.global_discovery_place_v1120(
                            f"ruin:great:{kind}:{x}:{y}",
                            f"Wielkie Ruiny — {spec['zone']}, sektor {x+1}-{y+1}",
                            prefixes=(prefix,), hidden=True,
                        ))

            # UOSSMUD superboss arenas are authored later in the runtime, so scan
            # the final live ROOMS registry instead of importing a later module.
            for rid, room in ROOMS.items():
                key = room.get("uoss_superboss_key")
                if not key:
                    continue
                catalog["superbosses"].append(self.global_discovery_place_v1120(
                    f"superboss:{key}",
                    str(room.get("name") or key),
                    room_ids=(rid,),
                ))

            # New authored superboss halls: 1.50 four sanctuaries, the council,
            # and any current 1.60 halls with explicit world-boss encounters.
            for rid, room in ROOMS.items():
                if rid == "v1500_super_council" or (
                    rid.startswith("v1500_") and rid.endswith("_super_room")
                ):
                    catalog["superbosses"].append(self.global_discovery_place_v1120(
                        f"superboss:authored:{rid}", str(room.get("name") or rid), room_ids=(rid,)
                    ))
            # 1.60 superboss sanctuaries and world-boss locations are registered
            # by the expansion. Check real spawn/template flags, not name guesses.
            for boss_room, mob_id in MOB_SPAWNS:
                if not (str(mob_id).startswith('v1600_') or str(mob_id).startswith('v1700_')):
                    continue
                template = MOB_TEMPLATES.get(mob_id, {})
                if not template.get('world_boss') or boss_room not in ROOMS:
                    continue
                catalog['superbosses'].append(self.global_discovery_place_v1120(
                    f'superboss:authored:{mob_id}', str(template.get('name') or mob_id),
                    room_ids=(boss_room,),
                ))

            # Finite surface secrets. Instance secrets remain in the instance map
            # because endless instances do not have a finite "all" target.
            for surface_room in v0140_surface_secret_room_ids():
                info = v0140_surface_secret_info(surface_room)
                if not info:
                    continue
                catalog["secrets"].append(self.global_discovery_place_v1120(
                    f"secret:{surface_room}",
                    info["name"],
                    hidden=True,
                    collection="surface_secrets_v0140",
                    collection_key=surface_room,
                ))

            # Stable ordering and de-duplication make NVDA numbering deterministic.
            for key, rows in catalog.items():
                unique = {}
                for row in rows:
                    unique.setdefault(row["key"], row)
                catalog[key] = sorted(
                    unique.values(), key=lambda row: normalize_lookup_text(row["name"])
                )
            return catalog

    def global_discovery_atlas_state_v1120(self):
            catalog = self.global_discovery_atlas_catalog_v1120()
            discovered = set(self.server.db.discovered_room_ids(self.account_id))
            collection_cache = {}

            def found(place):
                collection = place.get("collection")
                if collection:
                    if collection not in collection_cache:
                        collection_cache[collection] = set(
                            self.server.db.collection_entry_ids(self.account_id, collection)
                        )
                    return str(place.get("collection_key")) in collection_cache[collection]
                if any(rid in discovered for rid in place.get("room_ids", ())):
                    return True
                prefixes = place.get("prefixes", ())
                if prefixes:
                    return any(
                        any(rid.startswith(prefix) for prefix in prefixes)
                        for rid in discovered
                    )
                return False

            state = {}
            for key, places in catalog.items():
                rows = []
                for place in places:
                    row = dict(place)
                    row["found"] = found(place)
                    rows.append(row)
                count = sum(1 for row in rows if row["found"])
                state[key] = {
                    "label": GLOBAL_DISCOVERY_ATLAS_CATEGORIES_V1120[key]["label"],
                    "rows": rows,
                    "found": count,
                    "total": len(rows),
                    "complete": bool(rows) and count == len(rows),
                }
            return state

    async def sync_global_discovery_atlas_v1120(self, announce=False):
            """Retroactive achievement sync; safe for old saves and new discoveries."""
            state = self.global_discovery_atlas_state_v1120()
            for key, category in state.items():
                if not category["complete"]:
                    continue
                achievement_id, name, tier = GLOBAL_DISCOVERY_ATLAS_CATEGORIES_V1120[key]["achievement"]
                if self.server.db.unlock_achievement(self.account_id, achievement_id, name, tier):
                    if announce:
                        await self.send(f"Osiągnięcie: {name}, {tier}.")

            all_complete = bool(state) and all(
                category["complete"] for category in state.values()
            )
            if all_complete:
                achievement_id, name, tier = GLOBAL_DISCOVERY_ATLAS_MASTER_V1120
                if self.server.db.unlock_achievement(
                    self.account_id, achievement_id, name, tier
                ):
                    if announce:
                        await self.send(f"Osiągnięcie: {name}, {tier}.")
                title_id = "global_atlas:master:v1120"
                if self.server.db.unlock_title(
                    self.account_id, title_id, GLOBAL_DISCOVERY_ATLAS_MASTER_TITLE_V1120
                ):
                    if announce:
                        await self.send(
                            f"Nowy tytuł: {GLOBAL_DISCOVERY_ATLAS_MASTER_TITLE_V1120}."
                        )
            return state

    def global_discovery_category_key_v1120(self, query):
            norm = normalize_lookup_text(query)
            for key, definition in GLOBAL_DISCOVERY_ATLAS_CATEGORIES_V1120.items():
                aliases = {normalize_lookup_text(value) for value in definition["aliases"]}
                if norm == normalize_lookup_text(definition["label"]) or norm in aliases:
                    return key
            return None

    async def show_global_discovery_atlas_v1120(self, args=""):
            state = await self.sync_global_discovery_atlas_v1120(announce=False)
            raw = str(args or "").strip()
            if raw:
                key = self.global_discovery_category_key_v1120(raw)
                if not key:
                    await self.send(
                        "Nie rozpoznaję działu Globalnego Atlasu. "
                        "Działy: regiony, miasta, wyspy, lochy, platformy, ruiny, superbossy, sekrety."
                    )
                    return
                category = state[key]
                await self.send(
                    f"GLOBALNY ATLAS — {category['label'].upper()}: "
                    f"{category['found']} z {category['total']}."
                )
                for number, row in enumerate(category["rows"], 1):
                    if row["found"]:
                        await self.send(f"{number}. Odkryte: {row['name']}.")
                    elif row.get("hidden"):
                        await self.send(f"{number}. Nieodkryte: ???.")
                    else:
                        await self.send(f"{number}. Nieodkryte: {row['name']}.")
                return

            total_found = sum(category["found"] for category in state.values())
            total_places = sum(category["total"] for category in state.values())
            complete_count = sum(1 for category in state.values() if category["complete"])
            await self.send("GLOBALNY ATLAS ODKRYĆ")
            await self.send(
                f"Łącznie: {total_found} z {total_places} odkryć. "
                f"Ukończone działy: {complete_count} z {len(state)}."
            )
            for category in state.values():
                marker = " UKOŃCZONE." if category["complete"] else ""
                await self.send(
                    f"{category['label']}: {category['found']} z {category['total']}.{marker}"
                )
            await self.send(
                "Szczegóły: atlas odkrycia miasta / wyspy / lochy / platformy / "
                "ruiny / superbossy / sekrety. Nieodkryte sekrety i proceduralne "
                "ruiny/mini-lochy nie zdradzają nazw ani położenia."
            )

    def v0140_treasure_map_target(self):
            discovered = self.server.db.collection_entry_ids(self.account_id, "surface_secrets_v0140")
            known = self.server.db.collection_entry_ids(self.account_id, "treasure_targets_v0140")
            identity = v0130_frontier_room_identity(self.character.room_id) if self.character else None
            preferred_kind = identity[0] if identity else None
            candidates = [rid for rid in v0140_surface_secret_room_ids(preferred_kind) if rid not in discovered and rid not in known]
            if not candidates:
                candidates = [rid for rid in v0140_surface_secret_room_ids() if rid not in discovered and rid not in known]
            if not candidates:
                return None
            seed = _v0140_hash_int("map-target", self.account_id, len(known), self.character.name if self.character else "")
            return candidates[seed % len(candidates)]

    async def use_v0140_treasure_map(self, item_id):
            target = self.v0140_treasure_map_target()
            if not target:
                await self.send("Mapa nie znajduje już żadnego nieodkrytego sekretu proceduralnych rubieży.")
                return False
            if not self.server.db.remove_item(self.account_id, item_id, 1):
                await self.send("Nie masz tej mapy skarbu.")
                return False
            self.server.db.add_collection_entry(self.account_id, "treasure_targets_v0140", target)
            item = ITEMS.get(item_id, {})
            quest_id = item.get("quest_treasure_map_for")
            if quest_id:
                row = self.server.db.quest(self.account_id, quest_id)
                if row and row["status"] == "active":
                    self.server.db.add_collection_entry(
                        self.account_id, "quest_treasure_targets_v0243", f"{quest_id}|{target}"
                    )
            # v0.24.3: samo użycie mapy przygotowuje bezpieczny korytarz nawigacyjny.
            # Dzięki temu `prowadz skarb` nie wskazuje celu, do którego graf tras jeszcze nie istnieje.
            route_ready = self.materialize_frontier_route_v024(target)
            info = v0140_surface_secret_info(target)
            zone = V013_FRONTIER_SPECS[info["kind"]]["zone"]
            await self.send(
                f"Odczytujesz {item.get('name', 'Mapę Skarbu Rubieży')}. Trop zapisany: {zone}, sektor {info['x']+1}-{info['y']+1}. "
                + ("Trasa została przygotowana. Wpisz prowadz skarb. " if route_ready else "Wpisz mapa skarbu i spróbuj ponownie przygotować trasę. ")
                + "Po dotarciu użyj sekret / secret."
            )
            return True

    async def show_v0140_treasure_targets(self):
            targets = sorted(self.server.db.collection_entry_ids(self.account_id, "treasure_targets_v0140"))
            discovered = self.server.db.collection_entry_ids(self.account_id, "surface_secrets_v0140")
            active = [rid for rid in targets if rid not in discovered and v0140_surface_secret_info(rid)]
            await self.send(f"MAPY SKARBÓW: aktywne tropy {len(active)}, rozwiązane {len(targets)-len(active)}.")
            if not active:
                await self.send("Brak aktywnego tropu. Mapy Skarbu Rubieży wypadają m.in. z rare i skrzyń mini-lochów.")
                return
            for number, rid in enumerate(active, 1):
                info = v0140_surface_secret_info(rid)
                zone = V013_FRONTIER_SPECS[info["kind"]]["zone"]
                await self.send(f"{number}. {zone}, sektor {info['x']+1}-{info['y']+1}. Użyj sekret w tym sektorze.")

    def materialize_frontier_route_v024(self, room_id):
            """Materializuje tylko bezpieczny korytarz od bramy biomu do celu.

            Proceduralne sektory normalnie powstają dopiero przy wejściu. Nawigacja
            do aktywnego tropu mapy potrzebuje jednak skończonego grafu trasy.
            Tworzymy więc tylko prostą trasę 0,0 -> x,0 -> x,y, a nie cały biom.
            """
            identity = v0130_frontier_room_identity(room_id)
            if identity is None:
                return self.server.world.ensure_runtime_room(room_id)
            kind, target_x, target_y = identity
            coords = [(0, 0)]
            coords.extend((x, 0) for x in range(1, target_x + 1))
            coords.extend((target_x, y) for y in range(1, target_y + 1))
            for x, y in coords:
                if not self.server.world.ensure_runtime_room(
                    v0130_frontier_room_id(kind, x, y)
                ):
                    return False
            return room_id in ROOMS

    def active_treasure_targets_v024(self):
            targets = sorted(
                self.server.db.collection_entry_ids(
                    self.account_id, "treasure_targets_v0140"
                )
            )
            discovered = self.server.db.collection_entry_ids(
                self.account_id, "surface_secrets_v0140"
            )
            return [
                rid for rid in targets
                if rid not in discovered and v0140_surface_secret_info(rid)
            ]

    async def show_cartography_v024(self):
            discovered_rooms = self.server.db.discovered_room_ids(self.account_id)
            frontier_rooms = tuple(
                rid
                for kind in V013_FRONTIER_SPECS
                for rid in v0130_frontier_room_ids(kind)
            )
            frontier_known = sum(1 for rid in frontier_rooms if rid in discovered_rooms)
            secrets = self.server.db.collection_entry_ids(
                self.account_id, "surface_secrets_v0140"
            )
            mini = self.server.db.collection_entry_ids(
                self.account_id, "mini_dungeons_v015"
            )
            events = self.server.db.collection_entry_ids(
                self.account_id, "world_events_v0140"
            )
            all_targets = self.server.db.collection_entry_ids(
                self.account_id, "treasure_targets_v0140"
            )
            active = self.active_treasure_targets_v024()
            solved = max(0, len(all_targets) - len(active))
            await self.send("KARTOGRAFIA")
            await self.send(
                f"Rubieże: odkryto {frontier_known} z {len(frontier_rooms)} sektorów. "
                f"Sekrety: {len(secrets)}. Mini-lochy ukończone: {len(mini)}. "
                f"Wydarzenia odwiedzone: {len(events)}."
            )
            await self.send(
                f"Mapy skarbów: aktywne tropy {len(active)}, rozwiązane {solved}."
            )
            if active:
                for number, rid in enumerate(active, 1):
                    info = v0140_surface_secret_info(rid)
                    zone = V013_FRONTIER_SPECS[info["kind"]]["zone"]
                    await self.send(
                        f"Trop {number}: {zone}, sektor {info['x']+1}-{info['y']+1}. "
                        f"Prowadzenie: prowadz skarb {number}."
                    )
            else:
                await self.send(
                    "Brak aktywnego tropu. Użyj Mapy Skarbu Rubieży, aby zapisać nowy cel."
                )

            eren_chain = tuple(NPCS.get("cartographer_eren", {}).get("quest_chain") or ())
            if eren_chain:
                completed = 0
                active_names = []
                for qid in eren_chain:
                    row = self.server.db.quest(self.account_id, qid)
                    if row and (row["status"] == "completed" or int(row["completion_count"] or 0) > 0):
                        completed += 1
                    if row and row["status"] == "active":
                        active_names.append(QUESTS[qid]["name"])
                await self.send(
                    f"Łańcuch Erena: ukończone {completed}/{len(eren_chain)}."
                )
                if active_names:
                    await self.send("Aktywne u Erena: " + "; ".join(active_names) + ".")
            await self.send(
                "Komendy: mapa skarbu, prowadz skarb [numer], quest list Eren, help kartografia."
            )

    async def discover_room(self, room_id, announce=True):
            if room_id not in ROOMS:
                return False

            # v0.9.21: instancje mają niezależną, nieskończoną mapę sektorów po 100 pięter.
            instance_kind, instance_floor = instance_room_identity(room_id)
            if instance_kind and instance_floor is not None:
                instance_new = self.server.db.mark_instance_floor_visited(
                    self.account_id, instance_kind, instance_floor
                )
                info = INSTANCE_MAP_DEFS.get(instance_kind, {})
                if info.get("passive_checkpoints") and instance_floor % 10 == 0:
                    self.server.db.mark_instance_checkpoint(
                        self.account_id, instance_kind, instance_floor
                    )
                if instance_new and instance_secret_index(instance_kind, instance_floor) is not None:
                    if announce:
                        await self.send(
                            "Mapa instancji: wyczuwasz tutaj ukryty ślad. "
                            "Użyj sekret / secret, aby go zbadać."
                        )

            is_new = self.server.db.mark_room_discovered(
                self.account_id, room_id
            )
            if not is_new:
                return False

            self.server.db.add_lifetime_stat(self.account_id, "rooms_discovered", 1)
            room_meta = ROOMS[room_id]

            # v1.11.32: Explorer Points jak w klasycznych MUD-ach.
            # Każda nowa lokacja w terenie daje 1 EP dokładnie raz oraz Character EXP.
            zone_for_ep = str(room_meta.get("zone") or "Nieznany teren")
            room_stage=max(
                1,
                min(
                    600,
                    int(
                        room_meta.get("recommended_mastery")
                        or room_meta.get("recommended_level")
                        or room_meta.get("generator_level")
                        or room_meta.get("level")
                        or 1
                    ),
                ),
            )
            ep_xp = max(50, min(5000, 50 + room_stage * 10))
            for message in self.add_character_xp_with_event(
                ep_xp,
                content_level=room_stage,
                content_scaled=True,
            ):
                if announce:
                    await self.send(message)
            self.server.db.add_lifetime_stat(self.account_id, "explorer_points", 1)
            await self.advance_class_guild_quest_v11132("explore", 1)
            if announce:
                zone_ep_total = len(EXPLORATION_ZONE_ROOMS.get(zone_for_ep, ()))
                zone_ep_now = sum(
                    1 for rid in EXPLORATION_ZONE_ROOMS.get(zone_for_ep, ())
                    if rid in self.server.db.discovered_room_ids(self.account_id)
                )
                await self.send(
                    f"Punkt eksploracji: +1 EP, +{ep_xp} EXP postaci. "
                    f"{zone_for_ep}: {zone_ep_now} z {zone_ep_total} EP."
                )

            _o_kurde_find_v11324 = exploration_find_v11324(
                room_meta,
                int(getattr(self.character, "character_level", 1) or 1),
                random.random(),
            )
            if _o_kurde_find_v11324:
                _o_kurde_coins_v11324 = int(_o_kurde_find_v11324["coins"])
                self.character.silver += _o_kurde_coins_v11324
                self.server.db.save_character(self.character)
                self.server.db.add_lifetime_stat(
                    self.account_id, "exploration_jackpots_v11324", 1
                )
                if announce:
                    await self.send(
                        "O KURDE — UKRYTE ZNALEZISKO: "
                        + currency_reading_text(_o_kurde_coins_v11324, 0, 0)
                        + (
                            ". Sekretna lokacja podwoiła wartość znaleziska."
                            if _o_kurde_find_v11324.get("hidden") else "."
                        )
                    )
            if room_meta.get("v018_archipelago"):
                self.server.db.add_collection_entry(self.account_id, "archipelago_sectors_v018", room_id)
            if room_meta.get("v018_ruin_final"):
                self.server.db.add_collection_entry(self.account_id, "great_ruins_v018", room_meta.get("v018_ruin_parent", room_id))
            if room_meta.get("v018_endless"):
                self.server.db.add_lifetime_stat(self.account_id, "endless_sectors_discovered", 1)
            if room_meta.get("procedural_surface"):
                biome_kind_v015 = room_meta.get("procedural_biome", "any")
                await self.advance_v0140_quest_progress(
                    "explore_frontier", biome_kind_v015, 1
                )
                await self.advance_bounty("explore", biome_kind_v015, 1)
                await self.advance_legendary_contract_v022("explore", 1)
                await self.advance_dynamic_world_quest_v015("explore", biome_kind_v015, 1)
                await self.check_biome_mastery_v015(biome_kind_v015)
                await self.add_faction_reputation_v016("cartographers", 1, reason="exploration")
            if room_meta.get("v0140_mini_final"):
                mini_kind_v015 = room_meta.get("v0140_mini_kind", "any")
                await self.advance_v0140_quest_progress(
                    "mini_dungeon", mini_kind_v015, 1
                )
                await self.advance_bounty("mini", mini_kind_v015, 1)
                await self.advance_dynamic_world_quest_v015("mini", mini_kind_v015, 1)
                self.server.db.add_collection_entry(self.account_id, "mini_dungeons_v015", str(room_id))
            zone = room_meta["zone"]
            zone_rooms = EXPLORATION_ZONE_ROOMS.get(zone, ())
            discovered = self.server.db.discovered_room_ids(self.account_id)
            current = sum(1 for rid in zone_rooms if rid in discovered)
            total = max(1, len(zone_rooms))
            old_count = max(0, current - 1)
            old_pct = int(old_count * 100 / total)
            pct = int(current * 100 / total)

            if announce and len(zone_rooms) >= EXPLORATION_ZONE_MIN_ROOMS:
                milestones = (25, 50, 75, 100)
                crossed = [m for m in milestones if old_pct < m <= pct]
                if crossed:
                    await self.send(
                        f"Eksploracja: {zone} {pct}% odkryta."
                    )

            await self.set_achievement_progress(
                "exploration_rooms",
                len(discovered.intersection(ALL_EXPLORATION_ROOMS)),
            )

            # v1.12.0: Globalny Atlas Odkryć korzysta z istniejącej historii
            # odkrytych pokojów, więc działa również dla starszych save'ów.
            await self.sync_global_discovery_atlas_v1120(announce=announce)

            if (
                zone in TRACKED_EXPLORATION_ZONES
                and current >= total
                and self.server.db.claim_exploration_reward(self.account_id, zone)
            ):
                await self.complete_zone_exploration(zone, total)
            return True

    async def discover_current_room(self, announce=True):
            return await self.discover_room(
                self.character.room_id, announce=announce
            )

    async def complete_zone_exploration(self, zone, room_count):
            title_name = _zone_title(zone)
            reward_item = EXPLORATION_REWARD_ITEMS[zone]
            base_soul_xp = max(250, min(5000, room_count * 50))
            zone_rooms = EXPLORATION_ZONE_ROOMS.get(zone, ())
            stages = []
            for room_id in zone_rooms:
                room = ROOMS.get(room_id, {})
                for key in (
                    "recommended_mastery", "recommended_level",
                    "generator_level", "level",
                ):
                    try:
                        value = int(room.get(key, 0) or 0)
                    except (TypeError, ValueError):
                        value = 0
                    if value > 0:
                        stages.append(value)
            fallback_stage = max(
                1,
                int(getattr(self.character, "character_level", 1) or 1),
                int(getattr(self.character, "soul_level", 1) or 1),
            )
            stage = max(stages) if stages else fallback_stage
            room_factor = 1.0 + min(0.50, max(0, room_count - 10) / 100.0)
            silver = v1138_activity_income(
                stage, "exploration100", room_factor
            )
            gold = 0

            soul_xp=max(
                1,
                int(round(
                    base_soul_xp
                    * self.progression_content_multiplier_v11342(stage)
                )),
            )
            await self.send(f"Eksploracja ukończona: {zone}, 100 procent.")
            await self.grant_soul_xp(
                soul_xp,
                content_level=stage,
                content_scaled=True,
            )
            self.character.silver += silver
            self.server.db.add_item(self.account_id, reward_item, 1)
            self.server.db.save_character(self.character)
            await self.send(
                "Nagroda eksploracyjna: "
                + currency_reading_text(silver, gold, 0) + "."
            )
            await self.send(
                f"Unikalny przedmiot: {ITEMS[reward_item]['name']}."
            )
            await self.unlock_title(
                f"zone:{_collection_slug(zone)}", title_name
            )
            achievement_id = f"exploration100:{_collection_slug(zone)}"
            if self.server.db.unlock_achievement(
                self.account_id,
                achievement_id,
                f"100% eksploracji: {zone}",
                "Gold",
            ):
                await self.send(
                    f"Osiągnięcie: 100% eksploracji: {zone}, Gold."
                )

    def exploration_percent(self, zone):
            room_ids = EXPLORATION_ZONE_ROOMS.get(zone, ())
            if not room_ids:
                return 0, 0, 0
            discovered = self.server.db.discovered_room_ids(self.account_id)
            count = sum(1 for rid in room_ids if rid in discovered)
            return count, len(room_ids), int(count * 100 / len(room_ids))

    async def show_exploration(self, args=""):
            raw = str(args or "").strip()
            norm = normalize_lookup_text(raw)
            discovered = self.server.db.discovered_room_ids(self.account_id)
            world_count = sum(1 for rid in ALL_EXPLORATION_ROOMS if rid in discovered)
            world_pct = int(world_count * 100 / max(1, len(ALL_EXPLORATION_ROOMS)))

            if norm in ("all", "wszystko", "lista", "list"):
                await self.send(
                    f"EKSPLORACJA ŚWIATA: {world_count} z {len(ALL_EXPLORATION_ROOMS)}, {world_pct}%."
                )
                for zone in sorted(TRACKED_EXPLORATION_ZONES, key=normalize_lookup_text):
                    count, total, pct = self.exploration_percent(zone)
                    await self.send(f"{zone}: {count} z {total}, {pct}%.")
                return

            zone = ROOMS[self.character.room_id]["zone"]
            if raw and norm not in ("region", "strefa", "world", "swiat"):
                candidates = {
                    z: {"name": z} for z in EXPLORATION_ZONE_ROOMS
                }
                found = find_by_name(candidates, raw)
                if not found:
                    await self.send("Nie rozpoznaję takiej strefy eksploracji.")
                    return
                zone = found[0]
            count, total, pct = self.exploration_percent(zone)
            await self.send(
                f"{zone}: {pct}% odkryta. {count} z {total} lokacji. "
                f"Punkty eksploracji: {count} z {total} EP, pozostało {max(0, total-count)}."
            )
            await self.send(
                f"Cały świat: {world_pct}% odkryty. {world_count} z {len(ALL_EXPLORATION_ROOMS)} lokacji. "
                f"Łączne EP: {world_count}."
            )

    async def show_region_progress(self, zone=None):
            zone = zone or ROOMS[self.character.room_id]["zone"]
            count, total, pct = self.exploration_percent(zone)
            await self.send(f"{zone}: eksploracja {pct}%, {count} z {total} lokacji.")
            region = REGION_COLLECTION_ENTRIES.get(zone, {})
            for category in ("bosses", "rare", "chests", "named"):
                total_ids = set(region.get(category, set()))
                if not total_ids:
                    continue
                found_ids = self.server.db.collection_entry_ids(
                    self.account_id, category
                )
                found_count = len(total_ids.intersection(found_ids))
                label = COLLECTION_CATEGORY_LABELS[category]
                await self.send(
                    f"{label}: {found_count} z {len(total_ids)}."
                )

    async def show_progress(self, args=""):
            norm = normalize_lookup_text(args)
            if norm in ("region", "strefa", "region progress", "regionprogress"):
                await self.show_region_progress()
                return
            # v0.58.0: pełny widok jest utrzymywany w osobnym, skupionym module.
            await self.show_unified_progress_v0580()

    async def show_achievements(self):
            await self.sync_extended_achievements()
            await self.sync_global_discovery_atlas_v1120(announce=False)
            rows = self.server.db.achievement_rows(self.account_id)
            await self.send(f"ACHIEVEMENTY. Odblokowane: {len(rows)}.")
            for metric, definition in ACHIEVEMENT_TRACKS.items():
                value = self.server.db.achievement_metric(self.account_id, metric)
                next_row = next(
                    ((threshold, tier) for threshold, tier in definition["tiers"] if value < threshold),
                    None,
                )
                if next_row:
                    await self.send(
                        f"{definition['name']}: {value}. Następny próg {next_row[1]}: {next_row[0]}."
                    )
                else:
                    await self.send(
                        f"{definition['name']}: {value}. Najwyższy próg ukończony."
                    )
            if rows:
                await self.send("ODBLOKOWANE:")
                for row in rows[-30:]:
                    await self.send(f"{row['name']}, {row['tier']}.")

    async def show_titles(self):
            await self.sync_titles_v0580(announce=True)
            await self.v0260_sync_museum()
            await self.v0260_check_museum_rewards(announce=False)
            rows = list(self.server.db.title_rows(self.account_id))
            await self.send(f"TYTUŁY. Odblokowane: {len(rows)}.")
            await self.send(
                f"Aktywny: {self.character.active_title or 'brak'}."
            )
            for number, row in enumerate(rows, 1):
                marker = " Aktywny." if row["title_name"] == self.character.active_title else ""
                bonus = self.v0260_title_bonus_text(row["title_name"])
                bonus_text = f" Bonus: {bonus}." if bonus else ""
                await self.send(f"{number}. {row['title_name']}.{marker}{bonus_text}")

    async def set_title(self, args=""):
            raw = str(args or "").strip()
            if not raw:
                await self.show_titles()
                return
            if normalize_lookup_text(raw) in ("off", "wylacz", "brak", "none"):
                self.character.active_title = ""
                self.server.db.save_character(self.character)
                await self.send("Aktywny tytuł wyłączony.")
                return
            rows = list(self.server.db.title_rows(self.account_id))
            chosen = None
            if raw.isdigit():
                index = int(raw) - 1
                if 0 <= index < len(rows):
                    chosen = rows[index]
            if chosen is None:
                q = normalize_lookup_text(raw)
                exact = [row for row in rows if normalize_lookup_text(row["title_name"]) == q]
                partial = [row for row in rows if q and q in normalize_lookup_text(row["title_name"])]
                if exact:
                    chosen = exact[0]
                elif len(partial) == 1:
                    chosen = partial[0]
            if chosen is None:
                await self.send("Nie rozpoznaję odblokowanego tytułu. Wpisz tytuly.")
                return
            self.character.active_title = str(chosen["title_name"])
            self.server.db.save_character(self.character)
            await self.send(f"Aktywny tytuł: {self.character.active_title}.")
            bonus = self.v0260_title_bonus_text()
            if bonus:
                await self.send(f"Bonus aktywnego tytułu: {bonus}.")
