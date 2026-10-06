# -*- coding: utf-8 -*-
"""Mine, dungeon access, portals and Soul/combat quest progression."""
from data import catalog_mutations as _catalog_mut

# v0.44.0: explicit dependencies; no compatibility-global injection.
import asyncio
import re
from core.bootstrap_economy_professions import profession_for_tool_type
from core.classes_skills import ORE_ATLAS_LEVELS, ORE_MINE_FLOOR_MINIMUMS, ROOMS
from core.mines_threat import ITEMS
from core.progression_600 import PROFESSION_MAX_LEVEL, TOOL_MAX_LEVEL
from core.progression_resources import MINE_MIN_FLOOR, ORE_ATLAS_ALL, mine_floor_id, mine_floor_number
from systems.crafting_quality import player_item_display_name_v0335
from systems.dungeons_regions import (
    ASTRAL_MIN_FLOOR,
    PROF_DUNGEON_TOOL,
    astral_floor_id,
    astral_floor_number,
    crypt_floor_id,
    crypt_floor_number,
    giant_fortress_floor_number,
    is_astral_boss_floor,
    is_crypt_boss_floor,
    mythic_astral_floor_number,
    mythic_crypt_floor_number,
    profession_dungeon_floor,
    profession_dungeon_required_tool_level,
)
from world.economy_quests import v0874_quest_stat_progress_base_grant
from world.uoss_superboss_runtime import superboss_member_entry_error_v11331
from world.uoss_superboss_world import (
    UOSS_DEEP_DUNGEON_APANDA_CLEARS_V11331,
    UOSS_DEEP_DUNGEON_ENTRY_V11331,
    UOSS_DEEP_DUNGEON_FLOOR0_V11331,
    UOSS_DEEP_DUNGEON_SERPENTARIUS_UNLOCK_FLOOR_V11331,
    UOSS_DEEP_DUNGEON_VISITS_V11331,
    uoss_deep_dungeon_floor_id_v11331,
    uoss_deep_dungeon_floor_number_v11331,
)


class SessionDungeonProgressionMixin:

    def uoss_deep_dungeon_max_floor_v11331(self):
            entries = self.server.db.collection_entry_ids(
                self.account_id, UOSS_DEEP_DUNGEON_VISITS_V11331
            )
            floors = []
            for entry in entries:
                try:
                    floors.append(int(entry))
                except (TypeError, ValueError):
                    continue
            return max(floors) if floors else 0

    def uoss_deep_dungeon_apanda_cleared_v11331(self, floor):
            return str(int(floor)) in self.server.db.collection_entry_ids(
                self.account_id, UOSS_DEEP_DUNGEON_APANDA_CLEARS_V11331
            )

    async def register_uoss_deep_dungeon_visit_v11331(self, room_id=None):
            floor = uoss_deep_dungeon_floor_number_v11331(
                room_id if room_id is not None else self.character.room_id
            )
            if floor is None:
                return False

            was_new = self.server.db.add_collection_entry(
                self.account_id,
                UOSS_DEEP_DUNGEON_VISITS_V11331,
                str(floor),
            )
            if was_new:
                await self.send(
                    f"Deep Dungeon: odkrywasz piętro {floor}. "
                    f"Najgłębszy zapisany poziom: {self.uoss_deep_dungeon_max_floor_v11331()}."
                )

            if floor >= UOSS_DEEP_DUNGEON_SERPENTARIUS_UNLOCK_FLOOR_V11331:
                unlocked = self.server.db.add_collection_entry(
                    self.account_id,
                    "deep_dungeon_discovery",
                    "floor_100",
                )
                if unlocked:
                    await self.send(
                        "Deep Dungeon: dotarcie do piętra 100 odblokowuje Floor 0 "
                        "i Super Bossa Serpentarius. Winda: deepelevator 0."
                    )
            return True

    def uoss_deep_dungeon_descent_blocked_v11331(
            self, room_id, direction="down"
    ):
            if direction != "down":
                return False
            floor = uoss_deep_dungeon_floor_number_v11331(room_id)
            if floor is None or floor % 25 != 0:
                return False
            return not self.uoss_deep_dungeon_apanda_cleared_v11331(floor)

    def uoss_serpentarius_room_entry_error_v11331(self, target_room):
            if str(target_room or "") != "uoss_superboss_arena_serpentarius_v11136":
                return ""
            return superboss_member_entry_error_v11331(self, "serpentarius")

    async def show_uoss_deep_dungeon_status_v11331(self, args=""):
            highest = self.uoss_deep_dungeon_max_floor_v11331()
            unlock_floor = UOSS_DEEP_DUNGEON_SERPENTARIUS_UNLOCK_FLOOR_V11331
            unlocks = self.server.db.collection_entry_ids(
                self.account_id, "deep_dungeon_discovery"
            )
            serpentarius_unlocked = "floor_100" in unlocks

            await self.send("UOSS DEEP DUNGEON — BEZ LIMITU")
            await self.send(
                f"Najgłębsze odwiedzone piętro: {highest if highest else 'brak'}."
            )
            if highest:
                next_apanda = ((highest // 25) + 1) * 25
                await self.send(
                    f"Apanda występuje co 25 pięter. Następny próg: {next_apanda}."
                )
            else:
                await self.send("Apanda występuje co 25 pięter: 25, 50, 75, 100 i dalej.")

            if serpentarius_unlocked:
                error = superboss_member_entry_error_v11331(
                    self, "serpentarius"
                )
                if error:
                    await self.send(
                        "Serpentarius: odblokowany przez piętro 100, "
                        f"ale wejście jest teraz niedostępne. {error}"
                    )
                else:
                    await self.send(
                        "Serpentarius: odblokowany. Użyj deepelevator 0 "
                        "albo superboss serpentarius."
                    )
            else:
                await self.send(
                    f"Serpentarius: zablokowany. Musisz osobiście dotrzeć "
                    f"co najmniej do piętra {unlock_floor}."
                )
            await self.send(
                "Wejście: Sala Super Bossów, kierunek down. "
                "Winda: deepelevator <odwiedzone piętro>; Floor 0: deepelevator 0."
            )

    async def use_uoss_deep_dungeon_elevator_v11331(self, raw=""):
            if self.combat_mob_key:
                await self.send("Nie możesz użyć windy Deep Dungeon podczas walki.")
                return

            current = str(self.character.room_id)
            current_floor = uoss_deep_dungeon_floor_number_v11331(current)
            if (
                current != UOSS_DEEP_DUNGEON_ENTRY_V11331
                and current != UOSS_DEEP_DUNGEON_FLOOR0_V11331
                and current_floor is None
            ):
                await self.send(
                    "Winda Deep Dungeon działa tylko wewnątrz Deep Dungeon."
                )
                return

            value = self.normalize_room_query(raw)
            if not value or value in ("status", "lista", "list"):
                await self.show_uoss_deep_dungeon_status_v11331()
                return

            match = re.search(r"(\d+)", value)
            if not match:
                await self.send(
                    "Użycie: deepelevator <odwiedzone piętro> albo deepelevator 0."
                )
                return
            floor = int(match.group(1))

            party_key = self.party_key()
            if party_key is not None and party_key != self.account_id:
                leader = self.server.session_by_account(party_key)
                leader_name = (
                    leader.character.name
                    if leader and getattr(leader, "character", None)
                    else "lider drużyny"
                )
                await self.send(
                    f"Tylko lider uruchamia windę dla drużyny. Lider: {leader_name}."
                )
                return

            candidates = (
                list(
                    self.server.party_sessions(
                        self.account_id,
                        same_room=self.character.room_id,
                    )
                )
                if party_key == self.account_id
                else [self]
            )
            if self not in candidates:
                candidates.append(self)

            target = (
                UOSS_DEEP_DUNGEON_FLOOR0_V11331
                if floor == 0
                else uoss_deep_dungeon_floor_id_v11331(floor)
            )
            if floor > 0:
                self.server.world.ensure_runtime_room(target)

            moved = []
            skipped = []
            for member in candidates:
                if not member or not getattr(member, "character", None):
                    continue
                if member.combat_mob_key:
                    skipped.append(f"{member.character.name}: trwa walka")
                    continue

                member_highest = member.uoss_deep_dungeon_max_floor_v11331()
                if floor == 0:
                    error = superboss_member_entry_error_v11331(
                        member, "serpentarius"
                    )
                    if error:
                        skipped.append(
                            f"{member.character.name}: {error}"
                        )
                        continue
                elif floor < 1 or floor > member_highest:
                    skipped.append(
                        f"{member.character.name}: najwyższe odwiedzone piętro "
                        f"{member_highest if member_highest else 'brak'}"
                    )
                    continue

                member.previous_room_id = member.character.room_id
                member.character.room_id = target
                member.server.db.save_character(member.character)
                moved.append(member)

            if moved:
                destination = "Floor 0" if floor == 0 else f"piętro {floor}"
                for member in moved:
                    await member.send(
                        f"Lider {self.character.name} uruchamia windę Deep Dungeon. "
                        f"Cel: {destination}."
                    )
                    await member.look()
                if len(moved) > 1:
                    await self.send(
                        f"Winda przenosi razem {len(moved)} graczy."
                    )
            if skipped:
                await self.send(
                    "Nie przeniesiono: " + "; ".join(skipped) + "."
                )

    def mine_progress(self):
            return self.server.db.mine_progress(self.account_id)

    def mine_descent_blocked_for_player(self, room_id, direction="down"):
            if direction != "down":
                return False
            floor = mine_floor_number(room_id)
            if floor is None:
                return False
            return (
                floor + 1
                > self.mine_progress()["max_floor_unlocked"]
            )

    async def auto_mine_descend_if_unlocked(self):
            if not self.auto_mining or self.closed:
                return False
            if self.combat_mob_key:
                return False

            current_room = self.character.room_id

            # v0.24.4: auto-kopanie potrafi wejść do Kopalni Głębinowej z całej
            # ręcznej części jaskini zamiast bez końca kopać przy wejściu.
            approach_steps = {
                "cave_entrance": ("down", "cave_tunnel"),
                "cave_tunnel": ("east", "crystal_chamber"),
                "crystal_chamber": ("down", mine_floor_id(MINE_MIN_FLOOR)),
            }
            if current_room in approach_steps:
                direction, target = approach_steps[current_room]
                if target.startswith("mine_floor_"):
                    self.server.world.ensure_infinite_dungeon_floor(target)
                if ROOMS.get(current_room, {}).get("exits", {}).get(direction) != target:
                    _catalog_mut.catalog_setdefault_path('ROOMS', ROOMS, (current_room,), "exits", {})[direction] = target
                old = current_room
                self.previous_room_id = old
                await self.server.broadcast_room(old, f"{self.character.name} odchodzi.", exclude=self)
                self.character.room_id = target
                self.server.db.save_character(self.character)
                await self.discover_room(target, announce=False)
                await self.server.broadcast_room(target, f"{self.character.name} przychodzi.", exclude=self)
                await self.send(f"Auto-kopanie schodzi głębiej: {ROOMS[target]['name']}.")
                return True

            floor = mine_floor_number(current_room)
            if floor is None:
                return False

            expected_target = mine_floor_id(floor + 1)
            self.server.world.ensure_infinite_dungeon_floor(expected_target)
            # Napraw stare runtime-roomy/zapisy, którym brakowało wyjścia down.
            _catalog_mut.catalog_setdefault_path('ROOMS', ROOMS, (current_room,), "exits", {})["down"] = expected_target
            target = ROOMS[current_room]["exits"].get("down")

            if target != expected_target:
                return False

            progress = self.mine_progress()
            if progress["max_floor_unlocked"] < floor + 1:
                return False

            if self.mine_descent_blocked_for_player(
                current_room,
                "down",
            ):
                return False

            old = current_room
            self.previous_room_id = old
            await self.server.broadcast_room(
                old,
                f"{self.character.name} odchodzi.",
                exclude=self,
            )

            self.character.room_id = target
            self.server.db.save_character(
                self.character
            )
            await self.discover_room(target, announce=False)

            await self.server.broadcast_room(
                target,
                f"{self.character.name} przychodzi.",
                exclude=self,
            )

            await self.send(
                f"Ściana w dół jest przebita. "
                f"Auto-kopanie schodzi na poziom {floor + 1}."
            )
            return True

    def nearest_auto_target(self, route):
            best = None
            best_len = None
            for room_id in route:
                path = self.shortest_path(
                    self.character.room_id, room_id
                )
                if path is None:
                    continue
                if best is None or len(path) < best_len:
                    best = room_id
                    best_len = len(path)
            return best

    def next_auto_target(self, route):
            current = self.character.room_id
            dungeon, _floor = profession_dungeon_floor(current)
            if dungeon in {
                "sunken_grotto", "ancient_forest", "alchemy_garden"
            }:
                return current
            if current not in route:
                return self.nearest_auto_target(route)
            index = route.index(current)
            return route[(index + 1) % len(route)]

    async def auto_walk_to_target(self, target, label, flag_attr):
            path = self.shortest_path(
                self.character.room_id, target
            )
            if path is None:
                await self.send(
                    f"{label}: nie udało się znaleźć drogi."
                )
                return False

            for direction, next_room in path:
                if self.closed or not getattr(self, flag_attr, False):
                    return False
                if self.combat_mob_key:
                    await self.send(
                        f"{label} zatrzymane: rozpoczęła się walka."
                    )
                    return False
                if self.mythic_entry_error(next_room):
                    return False
                if self.profession_dungeon_access_error(next_room):
                    return False
                if self.astral_entry_blocked(next_room):
                    return False
                if self.mythic_crypt_descent_blocked_for_player(
                    self.character.room_id, direction
                ):
                    return False
                if self.mythic_astral_ascent_blocked_for_player(
                    self.character.room_id, direction
                ):
                    return False
                if self.giant_fortress_ascent_blocked_for_player(
                    self.character.room_id, direction
                ):
                    return False
                if self.crypt_descent_blocked_for_player(
                    self.character.room_id, direction
                ):
                    return False
                if self.astral_ascent_blocked_for_player(
                    self.character.room_id, direction
                ):
                    return False
                if self.mine_descent_blocked_for_player(
                    self.character.room_id, direction
                ):
                    await self.send(
                        f"{label}: ściana kopalni blokuje zejście."
                    )
                    return False

                old = self.character.room_id
                await self.server.broadcast_room(
                    old,
                    f"{self.character.name} odchodzi.",
                    exclude=self,
                )
                self.character.room_id = next_room
                self.server.db.save_character(self.character)
                await self.discover_room(next_room, announce=False)
                await self.server.broadcast_room(
                    next_room,
                    f"{self.character.name} przychodzi.",
                    exclude=self,
                )
                await self.send(
                    f"{label}: {direction} -> "
                    f"{ROOMS[next_room]['name']}."
                )
                await asyncio.sleep(0.12)

            return self.character.room_id == target

    async def show_mine_info(self):
            """Czytelny status Kopalni Głębinowej dla NVDA."""
            progress = self.mine_progress()
            room_id = self.character.room_id
            floor = mine_floor_number(room_id)
            approach_names = {
                "cave_entrance": "Wejście do Kopalni Głębinowej — przed poziomem 1",
                "cave_tunnel": "Tunel Kryształowej Jaskini — droga do poziomu 1",
                "crystal_chamber": "Komnata Kryształowa — bezpośrednio przed poziomem 1",
            }

            await self.send("KOPALNIA GŁĘBINOWA")
            if floor is not None:
                await self.send(f"Położenie: poziom {floor}.")
            elif room_id in approach_names:
                await self.send(f"Położenie: {approach_names[room_id]}.")
            else:
                room_name = ROOMS.get(room_id, {}).get("name", "nieznana lokacja")
                await self.send(
                    f"Położenie: {room_name}. Nie jesteś teraz w Kopalni Głębinowej. "
                    "Użyj: prowadz kopalnia."
                )

            max_floor = int(progress["max_floor_unlocked"])
            await self.send(
                f"Najgłębiej odblokowany poziom: {max_floor}. "
                "Kopalnia nie ma górnego limitu pięter; moc zasobów skaluje się do progresji 600."
            )

            if floor is not None:
                if floor == max_floor:
                    hits = int(progress["wall_hits"])
                    required = int(progress["wall_required_hits"])
                    missing = max(0, required - hits)
                    await self.send(
                        f"Ściana do poziomu {floor + 1}: {hits}/{required} uderzeń. "
                        f"Brakuje {missing}."
                    )
                elif floor < max_floor:
                    await self.send(
                        f"Zejście do poziomu {floor + 1} jest już odblokowane."
                    )
                else:
                    await self.send(
                        "Uwaga: jesteś głębiej niż zapisany postęp odblokowania; "
                        "użyj ruchu w górę albo zaloguj się ponownie, jeśli to stary zapis."
                    )

            auto_text = "włączone" if self.auto_mining else "wyłączone"
            await self.send(f"Auto-kopanie: {auto_text}.")

            try:
                profession_level = int(self.profession_level_for_tool("mining"))
            except Exception:
                profession_level = 1
            try:
                tool_level = int(self.server.db.tool(self.account_id, "mining")["level"])
            except Exception:
                tool_level = 1
            await self.send(
                f"Górnictwo: {profession_level}/{PROFESSION_MAX_LEVEL}. Kilof: {tool_level}/{TOOL_MAX_LEVEL}."
            )

            # W Kopalni Głębinowej ruda wymaga jednocześnie odpowiedniego Kilofa
            # i głębokości. Pokazujemy kilka najwyższych spełnionych progów zamiast
            # zalewać czytnik ekranu całą tabelą atlasu.
            if floor is not None:
                eligible = []
                for item_id in ORE_ATLAS_ALL:
                    if item_id not in ITEMS:
                        continue
                    need_tool = int(ORE_ATLAS_LEVELS.get(item_id, 1))
                    need_floor = int(ORE_MINE_FLOOR_MINIMUMS.get(item_id, 1))
                    if tool_level >= need_tool and floor >= need_floor:
                        eligible.append((max(need_tool, need_floor), need_tool, need_floor, item_id))
                eligible.sort(key=lambda row: (row[0], row[1], row[2], ITEMS[row[3]].get("name", row[3])))
                best = eligible[-5:]
                if best:
                    await self.send(
                        "Najwyższe dostępne rudy przy tym Kilofie i piętrze: "
                        + ", ".join(player_item_display_name_v0335(item_id) for *_rest, item_id in best)
                        + "."
                    )

                future = []
                for item_id in ORE_ATLAS_ALL:
                    if item_id not in ITEMS:
                        continue
                    need_tool = int(ORE_ATLAS_LEVELS.get(item_id, 1))
                    need_floor = int(ORE_MINE_FLOOR_MINIMUMS.get(item_id, 1))
                    if need_tool > tool_level or need_floor > floor:
                        distance = max(0, need_tool - tool_level) + max(0, need_floor - floor)
                        future.append((distance, max(need_tool, need_floor), item_id, need_tool, need_floor))
                if future:
                    future.sort(key=lambda row: (row[0], row[1], ITEMS[row[2]].get("name", row[2])))
                    _distance, _rank, item_id, need_tool, need_floor = future[0]
                    await self.send(
                        f"Najbliższy kolejny próg rudy: {player_item_display_name_v0335(item_id)} — "
                        f"Kilof {need_tool}, poziom kopalni {need_floor}."
                    )

            if self.auto_mining:
                if floor is None and room_id in approach_names:
                    await self.send(
                        "Auto-kopanie samo przejdzie do poziomu 1 i będzie schodzić po przebiciu kolejnych ścian."
                    )
                elif floor is not None:
                    await self.send(
                        "Auto-kopanie po przebiciu ściany automatycznie schodzi na następny odblokowany poziom."
                    )
            else:
                await self.send("Włącz auto-kopanie komendą: kop on.")

    def mythic_entry_error(self, target_room):
            # v1.13.30: Mityczna Krypta i Mityczna Wieża nie mają level-gate.
            # Realna trudność, bossy pięter i checkpointy pozostają barierą.
            return None

    def profession_dungeon_access_error(self, target_room):
            dungeon, floor = profession_dungeon_floor(target_room)
            if not dungeon:
                return None
            if dungeon == "crystal_mine":
                # v0.25.1: to już zwykłe Kryształowe Groty, nie loch Górnictwa.
                return None

            tool_type, item_id, tool_name = PROF_DUNGEON_TOOL[dungeon]
            if self.server.db.item_qty(self.account_id, item_id) <= 0:
                return (
                    f"Ten loch profesyjny wymaga narzędzia: {tool_name}."
                )

            profession = profession_for_tool_type(tool_type)
            prow = self.server.db.profession(self.account_id, profession)
            profession_level = int(prow["level"])
            required = profession_dungeon_required_tool_level(floor)
            if profession_level < required:
                return (
                    f"Ten poziom lochu profesyjnego wymaga "
                    f"{profession} poziom {required}. Masz poziom {profession_level}. "
                    f"Poziom {tool_name} nie blokuje piętra; odblokowuje lepsze surowce."
                )
            return None

    def giant_fortress_ascent_blocked_for_player(
            self, room_id, direction="up"
        ):
            floor = giant_fortress_floor_number(room_id)
            if floor is not None and self.server.db.boss_floor_cleared(self.account_id, "giant", floor):
                return False
            return self.server.world.giant_fortress_ascent_blocked(room_id, direction)

    def mythic_crypt_descent_blocked_for_player(
            self, room_id, direction="down"
        ):
            floor = mythic_crypt_floor_number(room_id)
            if floor is not None and self.server.db.boss_floor_cleared(self.account_id, "mythic_crypt", floor):
                return False
            return self.server.world.mythic_crypt_descent_blocked(room_id, direction)

    def mythic_astral_ascent_blocked_for_player(
            self, room_id, direction="up"
        ):
            floor = mythic_astral_floor_number(room_id)
            if floor is not None and self.server.db.boss_floor_cleared(self.account_id, "mythic_astral", floor):
                return False
            return self.server.world.mythic_astral_ascent_blocked(room_id, direction)

    def crypt_portal(self):
            return self.server.db.crypt_portal(self.account_id)

    def crypt_portal_floors(self):
            highest = max(0, int(self.crypt_portal()))
            return list(range(10, highest + 1, 10))

    def crypt_descent_blocked_for_player(self, room_id, direction="down"):
            floor = crypt_floor_number(room_id)
            if floor is not None and self.server.db.boss_floor_cleared(self.account_id, "crypt", floor):
                return False
            return self.server.world.crypt_descent_blocked(room_id, direction)

    def astral_portal(self):
            return self.server.db.astral_portal(self.account_id)

    def astral_portal_floors(self):
            highest = max(0, int(self.astral_portal()))
            if highest < ASTRAL_MIN_FLOOR:
                return []
            return list(range(ASTRAL_MIN_FLOOR, highest + 1, 10))

    def astral_ascent_blocked_for_player(self, room_id, direction="up"):
            floor = astral_floor_number(room_id)
            if floor is not None and self.server.db.boss_floor_cleared(self.account_id, "astral", floor):
                return False
            return self.server.world.astral_ascent_blocked(room_id, direction)

    def astral_entry_blocked(self, target_room):
            # v1.13.30: brak minimalnego Soul Level dla Wieży Astralnej.
            return False

    async def grant_combat_quest_stat_xp(self, raw_reward, repeatable=False, source_label="Quest walki"):
            """Przyznaje EXP do każdej z sześciu statystyk z systemu questowego."""
            raw_reward = max(0, int(raw_reward or 0))
            if raw_reward <= 0:
                return []
            applied = []
            for stat_name in self.character.STAT_PROGRESS_FIELDS:
                granted = v0874_quest_stat_progress_base_grant(
                    self.character, stat_name, raw_reward, repeatable
                )
                granted = self.apply_double_xp(granted)
                applied.append(granted)
                for msg in self.character.add_stat_progress(granted, targets=(stat_name,)):
                    await self.send(msg)
            lo = min(applied) if applied else 0
            hi = max(applied) if applied else 0
            amount_text = str(lo) if lo == hi else f"{lo}-{hi}"
            await self.send(
                f"{source_label}: {amount_text} EXP osobno do Siły, Zręczności, "
                "Kondycji, Inteligencji, Siły Woli i Charyzmy."
            )
            return applied

    async def grant_soul_xp(self, amount):
            old_level = self.character.soul_level
            amount = self.apply_double_xp(amount)
            _mentor_pct = self.mentor_bonus_percent_v03050()
            if _mentor_pct:
                amount = max(0, int(round(amount * (1.0 + _mentor_pct / 100.0))))
                self.mentor_record_activity_v03051()

            self.session_summary_add("soul_xp", amount)
            messages = self.character.add_soul_xp(amount)
            for message in messages:
                await self.send(message)

            await self.set_achievement_progress("soul_level", self.character.soul_level)

            if self.character.soul_level > old_level:
                self.current_hp = self.max_hp()
                await self.send(
                    f"Awans Soul Level odnawia całe HP. "
                    f"HP: {self.current_hp} z {self.max_hp()}."
                )

            return self.character.soul_level > old_level

    async def show_astral_portal_status(self):
            highest = self.astral_portal()
            unlocked = self.astral_portal_floors()
            if not highest:
                await self.send(
                    "Astralny Portal nie ma jeszcze odblokowanych checkpointów. "
                    "Pokonaj Strażnika Gwiezdnej Bramy na poziomie 100."
                )
                return

            await self.send(
                f"Najwyższy checkpoint Wieży Astralnej: poziom {highest}."
            )
            await self.send(
                "Odblokowane Astralne Portale: "
                + ", ".join(str(floor) for floor in unlocked)
                + "."
            )
            await self.send(
                "Użycie: astralportal <100/110/120/... bez górnego limitu>. "
                "Portal uruchamia się przy Astralnej Bramie."
            )

    async def use_astral_portal(self, raw):
            if self.combat_mob_key:
                await self.send(
                    "Nie możesz użyć Astralnego Portalu podczas walki."
                )
                return

            value = self.normalize_room_query(raw)
            if not value or value in ("status", "lista", "list"):
                await self.show_astral_portal_status()
                return

            match = re.search(r"(\d+)", value)
            if not match:
                await self.send(
                    "Użycie: astralportal 100, 110, 120, ... bez górnego limitu."
                )
                return

            floor = int(match.group(1))
            if not is_astral_boss_floor(floor):
                await self.send(
                    f"Checkpointy Wieży są co 10 poziomów od {ASTRAL_MIN_FLOOR} bez górnego limitu."
                )
                return

            highest = self.astral_portal()
            if floor > highest:
                await self.send(
                    f"Checkpoint poziomu {floor} jest zablokowany. "
                    f"Najwyższy odblokowany: {highest if highest else 'brak'}."
                )
                return

            if self.character.room_id != "astral_gate":
                await self.send(
                    "Astralny Portal działa tylko przy Astralnej Bramie. "
                    "Wpisz prowadz wieza astralna."
                )
                return

            target = astral_floor_id(floor)
            self.server.world.ensure_infinite_dungeon_floor(target)
            old = self.character.room_id

            party_key = self.party_key()
            if party_key is not None and party_key == self.account_id:
                candidates = list(
                    self.server.party_sessions(
                        self.account_id, same_room=old
                    )
                )
            else:
                candidates = [self]

            moved = []
            skipped = []
            for member in candidates:
                if not member or not getattr(member, "character", None):
                    continue
                if member.combat_mob_key:
                    skipped.append(
                        f"{member.character.name}: trwa walka"
                    )
                    continue
                member_highest = int(member.astral_portal() or 0)
                if floor > member_highest:
                    skipped.append(
                        f"{member.character.name}: najwyższy checkpoint "
                        f"{member_highest if member_highest else 'brak'}"
                    )
                    continue

                member.character.room_id = target
                member.server.db.save_character(member.character)
                moved.append(member)

            await self.server.broadcast_room(
                old,
                f"{self.character.name} uruchamia Astralny Portal.",
                exclude=None,
            )
            if len(moved) > 1:
                names = ", ".join(
                    member.character.name for member in moved
                )
                for member in moved:
                    await member.send(
                        f"Lider {self.character.name} przenosi drużynę "
                        f"Astralnym Portalem na poziom {floor}."
                    )
                await self.send(
                    f"Astralny Portal przenosi razem {len(moved)} graczy: "
                    f"{names}."
                )
            elif moved:
                await moved[0].send(
                    f"Astralny Portal przenosi cię na poziom {floor}."
                )

            if skipped:
                await self.send(
                    "Nie przeniesiono: " + "; ".join(skipped) + "."
                )

            await self.server.broadcast_room(
                target,
                f"{self.character.name} i drużyna wychodzą z Astralnego Portalu."
                if len(moved) > 1
                else f"{self.character.name} wychodzi z Astralnego Portalu.",
                exclude=None,
            )
            for member in moved:
                await member.look()

    async def show_portal_status(self):
            highest = self.crypt_portal()
            unlocked = self.crypt_portal_floors()
            if not unlocked:
                await self.send(
                    "Portale Krypty: brak. "
                    "Pokonaj bossa piętra 10, aby odblokować pierwszy portal."
                )
                return

            await self.send(
                f"Najwyższy odblokowany Portal Krypty: piętro {highest}."
            )
            await self.send(
                "Odblokowane Portale Krypty: "
                + ", ".join(str(floor) for floor in unlocked)
                + "."
            )
            await self.send(
                "Użycie: portal <10/20/30/...>. "
                "Portal można uruchomić w Sali Krypty albo w Przedsionku Krypty."
            )

    async def use_crypt_portal(self, raw):
            if self.combat_mob_key:
                await self.send(
                    "Nie możesz użyć Portalu Krypty podczas walki."
                )
                return

            value = self.normalize_room_query(raw)
            if not value or value in ("status", "lista", "list"):
                await self.show_portal_status()
                return

            match = re.search(r"(\d+)", value)
            if not match:
                await self.send(
                    "Użycie: portal 10, portal 20, portal 30, ... bez górnego limitu."
                )
                return

            floor = int(match.group(1))
            if not is_crypt_boss_floor(floor):
                await self.send(
                    "Portale są co 10 pięter: 10, 20, 30, ... bez górnego limitu."
                )
                return

            highest = self.crypt_portal()
            if floor > highest:
                await self.send(
                    f"Portal piętra {floor} jest jeszcze zablokowany. "
                    f"Najwyższy odblokowany portal: "
                    f"{highest if highest else 'brak'}."
                )
                return

            if self.character.room_id not in ("crypt_hall", "crypt_entrance"):
                await self.send(
                    "Portal Krypty można uruchomić tylko w Sali Krypty "
                    "albo w Przedsionku Krypty. Użyj prowadz Sala Krypty."
                )
                return

            if self.resting or self.rest_task:
                await self.stop_rest(announce=False)
            if self.auto_fishing or self.auto_fishing_task:
                await self.stop_auto_fishing(announce=False)
            if self.auto_mining or self.auto_mining_task:
                await self.stop_auto_mining(announce=False)
            if self.auto_woodcutting or self.auto_woodcutting_task:
                await self.stop_auto_woodcutting(announce=False)
            if self.auto_herbalism or self.auto_herbalism_task:
                await self.stop_auto_herbalism(announce=False)

            target = crypt_floor_id(floor)
            self.server.world.ensure_infinite_dungeon_floor(target)
            old = self.character.room_id

            party_key = self.party_key()
            if party_key is not None and party_key == self.account_id:
                candidates = list(
                    self.server.party_sessions(
                        self.account_id, same_room=old
                    )
                )
            else:
                candidates = [self]

            moved = []
            skipped = []
            for member in candidates:
                if not member or not getattr(member, "character", None):
                    continue
                if member.combat_mob_key:
                    skipped.append(
                        f"{member.character.name}: trwa walka"
                    )
                    continue
                member_highest = int(member.crypt_portal() or 0)
                if floor > member_highest:
                    skipped.append(
                        f"{member.character.name}: najwyższy portal "
                        f"{member_highest if member_highest else 'brak'}"
                    )
                    continue

                if member.resting or member.rest_task:
                    await member.stop_rest(announce=False)
                if member.auto_fishing or member.auto_fishing_task:
                    await member.stop_auto_fishing(announce=False)
                if member.auto_mining or member.auto_mining_task:
                    await member.stop_auto_mining(announce=False)
                if member.auto_woodcutting or member.auto_woodcutting_task:
                    await member.stop_auto_woodcutting(announce=False)
                if member.auto_herbalism or member.auto_herbalism_task:
                    await member.stop_auto_herbalism(announce=False)

                member.character.room_id = target
                member.server.db.save_character(member.character)
                moved.append(member)

            await self.server.broadcast_room(
                old,
                f"{self.character.name} uruchamia Portal Krypty.",
                exclude=None,
            )
            if len(moved) > 1:
                names = ", ".join(
                    member.character.name for member in moved
                )
                for member in moved:
                    await member.send(
                        f"Lider {self.character.name} przenosi drużynę "
                        f"Portalem Krypty na piętro {floor}."
                    )
                await self.send(
                    f"Portal Krypty przenosi razem {len(moved)} graczy: "
                    f"{names}."
                )
            elif moved:
                await moved[0].send(
                    f"Portal Krypty przenosi cię na piętro {floor}."
                )

            if skipped:
                await self.send(
                    "Nie przeniesiono: " + "; ".join(skipped) + "."
                )

            await self.server.broadcast_room(
                target,
                f"{self.character.name} i drużyna wychodzą z Portalu Krypty."
                if len(moved) > 1
                else f"{self.character.name} wychodzi z Portalu Krypty.",
                exclude=None,
            )
            for member in moved:
                await member.look()
