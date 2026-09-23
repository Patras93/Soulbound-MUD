# -*- coding: utf-8 -*-
"""Treasure maps, exploration, progress, achievements and titles."""

# v0.44.0: explicit dependencies; no compatibility-global injection.
from core.bootstrap_economy_professions import currency_reading_text
from core.classes_skills import ROOMS
from core.mines_threat import ITEMS
from network.protocol_gameplay_utils import find_by_name, normalize_lookup_text
from systems.content_registry import NPCS, QUESTS
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
    V013_FRONTIER_SPECS,
    _v0140_hash_int,
    v0130_frontier_room_id,
    v0130_frontier_room_identity,
    v0130_frontier_room_ids,
    v0140_surface_secret_info,
    v0140_surface_secret_room_ids,
)


class SessionExplorationProgressMixin:

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
            soul_xp = max(250, min(5000, room_count * 50))
            silver = max(500, room_count * 100)
            gold = max(1, room_count // 10)

            await self.send(f"Eksploracja ukończona: {zone}, 100 procent.")
            await self.grant_soul_xp(soul_xp)
            self.character.silver += silver
            self.character.gold += gold
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
            await self.send(f"{zone}: {pct}% odkryta. {count} z {total} lokacji.")
            await self.send(
                f"Cały świat: {world_pct}% odkryty. {world_count} z {len(ALL_EXPLORATION_ROOMS)} lokacji."
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
