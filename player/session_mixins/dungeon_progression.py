# v4.20.0: bound, AST-identical method implementations (MRO unchanged)
from core.legacy_method_binding_v4200 import bind_legacy_method_v4200 as _sb420_bind
import player.session_methods_v4200.dungeonprogression_part01 as _sb420_src_01
# SessionDungeonProgressionMixin.portal_requires_local_leader_v12811 -> player/session_methods_v4200/dungeonprogression_part01.py
# SessionDungeonProgressionMixin.register_uoss_deep_dungeon_visit_v11331 -> player/session_methods_v4200/dungeonprogression_part01.py
# SessionDungeonProgressionMixin.show_uoss_deep_dungeon_status_v11331 -> player/session_methods_v4200/dungeonprogression_part01.py
# SessionDungeonProgressionMixin.use_uoss_deep_dungeon_elevator_v11331 -> player/session_methods_v4200/dungeonprogression_part01.py
# SessionDungeonProgressionMixin.auto_mine_descend_if_unlocked -> player/session_methods_v4200/dungeonprogression_part01.py
# SessionDungeonProgressionMixin.auto_walk_to_target -> player/session_methods_v4200/dungeonprogression_part01.py
# SessionDungeonProgressionMixin.command_mineinfo_v1260 -> player/session_methods_v4200/dungeonprogression_part01.py
import player.session_methods_v4200.dungeonprogression_part02 as _sb420_src_02
# SessionDungeonProgressionMixin.show_mine_info -> player/session_methods_v4200/dungeonprogression_part02.py
# SessionDungeonProgressionMixin.profession_dungeon_access_error -> player/session_methods_v4200/dungeonprogression_part02.py
# SessionDungeonProgressionMixin.grant_stat_xp_v11342 -> player/session_methods_v4200/dungeonprogression_part02.py
# SessionDungeonProgressionMixin.grant_combat_quest_stat_xp -> player/session_methods_v4200/dungeonprogression_part02.py
# SessionDungeonProgressionMixin.grant_soul_xp -> player/session_methods_v4200/dungeonprogression_part02.py
# SessionDungeonProgressionMixin.use_catacomb_portal_v2010 -> player/session_methods_v4200/dungeonprogression_part02.py
# SessionDungeonProgressionMixin.show_checkpoint_portal_status_v11331 -> player/session_methods_v4200/dungeonprogression_part02.py
# SessionDungeonProgressionMixin.party_checkpoint_portal_exit_v11331 -> player/session_methods_v4200/dungeonprogression_part02.py
# SessionDungeonProgressionMixin.show_astral_portal_status -> player/session_methods_v4200/dungeonprogression_part02.py
import player.session_methods_v4200.dungeonprogression_part03 as _sb420_src_03
# SessionDungeonProgressionMixin.use_astral_portal -> player/session_methods_v4200/dungeonprogression_part03.py
# SessionDungeonProgressionMixin.show_portal_status -> player/session_methods_v4200/dungeonprogression_part03.py
# SessionDungeonProgressionMixin.use_crypt_portal -> player/session_methods_v4200/dungeonprogression_part03.py

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
from core.mine_tunnels import mine_tunnel_coords, MINE_DIRECTION_LABELS
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
    is_mythic_astral_boss_floor,
    is_mythic_crypt_boss_floor,
    mythic_astral_floor_id,
    mythic_astral_floor_number,
    mythic_crypt_floor_id,
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

    def portal_requires_local_leader_v12811(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method portal_requires_local_leader_v12811")

    async def register_uoss_deep_dungeon_visit_v11331(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method register_uoss_deep_dungeon_visit_v11331")

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

    async def show_uoss_deep_dungeon_status_v11331(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method show_uoss_deep_dungeon_status_v11331")

    async def use_uoss_deep_dungeon_elevator_v11331(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method use_uoss_deep_dungeon_elevator_v11331")

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

    async def auto_mine_descend_if_unlocked(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method auto_mine_descend_if_unlocked")

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

    async def auto_walk_to_target(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method auto_walk_to_target")

    async def command_mineinfo_v1260(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method command_mineinfo_v1260")

    async def show_mine_info(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method show_mine_info")

    def mythic_entry_error(self, target_room):
            # v1.13.30: Mityczna Krypta i Mityczna Wieża nie mają level-gate.
            # Realna trudność, bossy pięter i checkpointy pozostają barierą.
            return None

    def profession_dungeon_access_error(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method profession_dungeon_access_error")

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

    async def grant_stat_xp_v11342(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method grant_stat_xp_v11342")

    async def grant_combat_quest_stat_xp(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method grant_combat_quest_stat_xp")

    async def grant_soul_xp(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method grant_soul_xp")

    async def grant_combat_soul_xp_v11350(
        self, amount, *, content_level=None, content_scaled=True, overcap=False
    ):
            """Stable combat Soul XP gateway immune to late legacy overrides."""
            return await SessionDungeonProgressionMixin.grant_soul_xp(
                self,
                amount,
                single_level_cap=False,
                content_level=content_level,
                content_scaled=content_scaled, overcap=overcap,
            )


    def checkpoint_portal_origin_v2010(self, *, room_id, gate_rooms, kind,
                                         current_floor, is_checkpoint):
            """A cleared checkpoint is a portal origin, not only a way out."""
            if room_id in gate_rooms:
                return True
            return bool(
                current_floor is not None
                and is_checkpoint(current_floor)
                and self.checkpoint_portal_unlocked_v11331(kind, current_floor)
            )

    def catacomb_floor_v2010(self, room_id=None):
            room_id = str(room_id if room_id is not None else self.character.room_id)
            match = re.match(r'^(?:v0900_)?catacomb_f([1-3])_', room_id)
            return int(match.group(1)) if match else None

    def catacomb_unlocked_floors_v2010(self):
            return sorted({
                int(value) for value in self.server.db.collection_entry_ids(
                    self.account_id, 'catacomb_portal_floors_v2010'
                ) if str(value) in ('1', '2', '3')
            })

    def remember_catacomb_floor_v2010(self, room_id):
            floor = self.catacomb_floor_v2010(room_id)
            if floor is None or self.account_id is None:
                return
            # Existing characters already on floor 2 or 3 must not lose
            # access to all preceding levels after updating the server.
            known = self.catacomb_unlocked_floors_v2010()
            for visited in range(1, floor + 1):
                if visited not in known:
                    self.server.db.add_collection_entry(
                        self.account_id, 'catacomb_portal_floors_v2010', str(visited)
                    )

    async def use_catacomb_portal_v2010(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method use_catacomb_portal_v2010")

    def checkpoint_portal_floors_v11331(self, kind):
            floors = self.server.db.instance_checkpoint_floors(
                self.account_id, kind
            )
            if kind == "astral":
                floors = {f for f in floors if f >= ASTRAL_MIN_FLOOR}
            else:
                floors = {f for f in floors if f >= 10}
            return sorted(
                int(f) for f in floors
                if int(f) % 10 == 0
            )

    def checkpoint_portal_unlocked_v11331(self, kind, floor):
            return int(floor) in set(
                self.checkpoint_portal_floors_v11331(kind)
            )

    async def show_checkpoint_portal_status_v11331(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method show_checkpoint_portal_status_v11331")

    async def party_checkpoint_portal_exit_v11331(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method party_checkpoint_portal_exit_v11331")

    async def show_astral_portal_status(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method show_astral_portal_status")

    async def use_astral_portal(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method use_astral_portal")

    async def show_portal_status(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method show_portal_status")

    async def use_crypt_portal(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method use_crypt_portal")

# v4.20.0: exact historical implementations rebound onto original class.
SessionDungeonProgressionMixin.portal_requires_local_leader_v12811 = _sb420_bind(_sb420_src_01.portal_requires_local_leader_v12811, globals(), "SessionDungeonProgressionMixin")
SessionDungeonProgressionMixin.register_uoss_deep_dungeon_visit_v11331 = _sb420_bind(_sb420_src_01.register_uoss_deep_dungeon_visit_v11331, globals(), "SessionDungeonProgressionMixin")
SessionDungeonProgressionMixin.show_uoss_deep_dungeon_status_v11331 = _sb420_bind(_sb420_src_01.show_uoss_deep_dungeon_status_v11331, globals(), "SessionDungeonProgressionMixin")
SessionDungeonProgressionMixin.use_uoss_deep_dungeon_elevator_v11331 = _sb420_bind(_sb420_src_01.use_uoss_deep_dungeon_elevator_v11331, globals(), "SessionDungeonProgressionMixin")
SessionDungeonProgressionMixin.auto_mine_descend_if_unlocked = _sb420_bind(_sb420_src_01.auto_mine_descend_if_unlocked, globals(), "SessionDungeonProgressionMixin")
SessionDungeonProgressionMixin.auto_walk_to_target = _sb420_bind(_sb420_src_01.auto_walk_to_target, globals(), "SessionDungeonProgressionMixin")
SessionDungeonProgressionMixin.command_mineinfo_v1260 = _sb420_bind(_sb420_src_01.command_mineinfo_v1260, globals(), "SessionDungeonProgressionMixin")
SessionDungeonProgressionMixin.show_mine_info = _sb420_bind(_sb420_src_02.show_mine_info, globals(), "SessionDungeonProgressionMixin")
SessionDungeonProgressionMixin.profession_dungeon_access_error = _sb420_bind(_sb420_src_02.profession_dungeon_access_error, globals(), "SessionDungeonProgressionMixin")
SessionDungeonProgressionMixin.grant_stat_xp_v11342 = _sb420_bind(_sb420_src_02.grant_stat_xp_v11342, globals(), "SessionDungeonProgressionMixin")
SessionDungeonProgressionMixin.grant_combat_quest_stat_xp = _sb420_bind(_sb420_src_02.grant_combat_quest_stat_xp, globals(), "SessionDungeonProgressionMixin")
SessionDungeonProgressionMixin.grant_soul_xp = _sb420_bind(_sb420_src_02.grant_soul_xp, globals(), "SessionDungeonProgressionMixin")
SessionDungeonProgressionMixin.use_catacomb_portal_v2010 = _sb420_bind(_sb420_src_02.use_catacomb_portal_v2010, globals(), "SessionDungeonProgressionMixin")
SessionDungeonProgressionMixin.show_checkpoint_portal_status_v11331 = _sb420_bind(_sb420_src_02.show_checkpoint_portal_status_v11331, globals(), "SessionDungeonProgressionMixin")
SessionDungeonProgressionMixin.party_checkpoint_portal_exit_v11331 = _sb420_bind(_sb420_src_02.party_checkpoint_portal_exit_v11331, globals(), "SessionDungeonProgressionMixin")
SessionDungeonProgressionMixin.show_astral_portal_status = _sb420_bind(_sb420_src_02.show_astral_portal_status, globals(), "SessionDungeonProgressionMixin")
SessionDungeonProgressionMixin.use_astral_portal = _sb420_bind(_sb420_src_03.use_astral_portal, globals(), "SessionDungeonProgressionMixin")
SessionDungeonProgressionMixin.show_portal_status = _sb420_bind(_sb420_src_03.show_portal_status, globals(), "SessionDungeonProgressionMixin")
SessionDungeonProgressionMixin.use_crypt_portal = _sb420_bind(_sb420_src_03.use_crypt_portal, globals(), "SessionDungeonProgressionMixin")


