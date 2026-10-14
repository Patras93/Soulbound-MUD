# v4.20.0: bound, AST-identical method implementations (MRO unchanged)
from core.legacy_method_binding_v4200 import bind_legacy_method_v4200 as _sb420_bind
import player.session_methods_v4200.guidenavigation_part01 as _sb420_src_01
# SessionGuideNavigationMixin.show_current_city_walk_destinations -> player/session_methods_v4200/guidenavigation_part01.py
# SessionGuideNavigationMixin.room_search_aliases -> player/session_methods_v4200/guidenavigation_part01.py
# SessionGuideNavigationMixin.guide_zone_query_name -> player/session_methods_v4200/guidenavigation_part01.py
# SessionGuideNavigationMixin.rooms_in_exact_zone -> player/session_methods_v4200/guidenavigation_part01.py
# SessionGuideNavigationMixin.find_room_matches -> player/session_methods_v4200/guidenavigation_part01.py
# SessionGuideNavigationMixin.show_guide_destinations -> player/session_methods_v4200/guidenavigation_part01.py
# SessionGuideNavigationMixin.compact_route_directions -> player/session_methods_v4200/guidenavigation_part01.py
# SessionGuideNavigationMixin.cancel_guide -> player/session_methods_v4200/guidenavigation_part01.py
# SessionGuideNavigationMixin.show_guide_status -> player/session_methods_v4200/guidenavigation_part01.py
# SessionGuideNavigationMixin._guide_task_finished -> player/session_methods_v4200/guidenavigation_part01.py
# SessionGuideNavigationMixin.start_guide_task -> player/session_methods_v4200/guidenavigation_part01.py
# SessionGuideNavigationMixin.show_route_next_step -> player/session_methods_v4200/guidenavigation_part01.py
import player.session_methods_v4200.guidenavigation_part02 as _sb420_src_02
# SessionGuideNavigationMixin.show_route -> player/session_methods_v4200/guidenavigation_part02.py
# SessionGuideNavigationMixin.shortest_path -> player/session_methods_v4200/guidenavigation_part02.py
# SessionGuideNavigationMixin.shortest_path_within_floor_v11340 -> player/session_methods_v4200/guidenavigation_part02.py
# SessionGuideNavigationMixin.guide_descending_floor_v1501 -> player/session_methods_v4200/guidenavigation_part02.py
# SessionGuideNavigationMixin.guide_exploration_safe_target -> player/session_methods_v4200/guidenavigation_part02.py
# SessionGuideNavigationMixin.guide_floor_request_label -> player/session_methods_v4200/guidenavigation_part02.py
# SessionGuideNavigationMixin.guide_floor_family_specs -> player/session_methods_v4200/guidenavigation_part02.py
# SessionGuideNavigationMixin.compact_guide_matches -> player/session_methods_v4200/guidenavigation_part02.py
# SessionGuideNavigationMixin.ask_guide_choice -> player/session_methods_v4200/guidenavigation_part02.py
# SessionGuideNavigationMixin.handle_guide_choice_number -> player/session_methods_v4200/guidenavigation_part02.py
# SessionGuideNavigationMixin.find_guide_npc -> player/session_methods_v4200/guidenavigation_part02.py
import player.session_methods_v4200.guidenavigation_part03 as _sb420_src_03
# SessionGuideNavigationMixin.guide_to -> player/session_methods_v4200/guidenavigation_part03.py

# -*- coding: utf-8 -*-
"""Guide, routing and path-finding."""

# v0.44.0: explicit dependencies; no compatibility-global injection.
import asyncio
import re
import sys
import unicodedata
from core.classes_skills import ROOMS
from config.postal import GUIDE_CITY_HUBS_V0522
from core.mines_threat import GUIDE_DESTINATION_ALIASES
from core.progression_resources import MINE_MIN_FLOOR, mine_floor_id, mine_floor_number
from systems.content_registry import MOB_TEMPLATES, NPCS
from systems.dungeons_regions import (
    ASTRAL_MIN_FLOOR,
    MYTHIC_MIN_FLOOR,
    astral_floor_id,
    astral_floor_number,
    crypt_floor_id,
    crypt_floor_number,
    giant_fortress_floor_id,
    giant_fortress_floor_number,
    mythic_astral_floor_id,
    mythic_astral_floor_number,
    mythic_crypt_floor_id,
    mythic_crypt_floor_number,
    profession_dungeon_floor,
    profession_dungeon_room_id,
)
from systems.equipment_crafting import SHOP_SELLERS
from systems.items_resources import CLASS_SHOP_CLASSES_BY_ROOM
from world.generation_systems import V013_FRONTIER_SPECS, v0140_surface_secret_info
from world.uoss_superboss_world import (
    uoss_deep_dungeon_floor_id_v11331,
    uoss_deep_dungeon_floor_number_v11331,
)


class SessionGuideNavigationMixin:

    async def show_location(self):
            room = ROOMS[self.character.room_id]
            await self.send(
                f"Lokalizacja: {room['name']}. Strefa: {room['zone']}."
            )
            await self.show_exits()

    async def show_current_city_walk_destinations(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method show_current_city_walk_destinations")

    def normalize_room_query(self, value):
            text = str(value or "").strip().lower()
            text = text.replace("ł", "l").replace("Ł", "l")
            text = unicodedata.normalize("NFKD", text)
            text = "".join(
                ch for ch in text
                if not unicodedata.combining(ch)
            )
            text = text.replace("_", " ").replace("-", " ")
            text = re.sub(r"[^a-z0-9 ]+", " ", text)
            return " ".join(text.split())

    def room_search_aliases(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method room_search_aliases")

    def guide_zone_query_name(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method guide_zone_query_name")

    def rooms_in_exact_zone(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method rooms_in_exact_zone")

    def find_room_matches(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method find_room_matches")

    def find_room(self, query):
            matches = self.find_room_matches(query)
            return matches[0] if len(matches) == 1 else None

    async def show_guide_destinations(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method show_guide_destinations")

    def guide_task_active(self):
            return bool(self.guide_task and not self.guide_task.done())

    def route_direction_name(self, direction):
            labels = {
                "north": "północ",
                "south": "południe",
                "east": "wschód",
                "west": "zachód",
                "up": "góra",
                "down": "dół",
            }
            return labels.get(direction, str(direction))

    def compact_route_directions(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method compact_route_directions")

    def route_zone_sequence(self, start_room, path):
            room_ids = [start_room] + [next_room for _direction, next_room in path]
            zones = []
            for room_id in room_ids:
                zone = ROOMS.get(room_id, {}).get("zone", "")
                if zone and (not zones or zones[-1] != zone):
                    zones.append(zone)
            return zones

    def estimated_guide_seconds(self, path):
            return sum(self.movement_delay(direction, guided=True) for direction, _ in path)

    async def cancel_guide(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method cancel_guide")

    async def show_guide_status(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method show_guide_status")

    def _guide_task_finished(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method _guide_task_finished")

    async def start_guide_task(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method start_guide_task")

    async def show_route_next_step(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method show_route_next_step")

    async def show_route(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method show_route")

    def shortest_path(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method shortest_path")

    def shortest_path_within_floor_v11340(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method shortest_path_within_floor_v11340")

    def guide_descending_floor_v1501(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method guide_descending_floor_v1501")

    def guide_exploration_safe_target(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method guide_exploration_safe_target")

    def guide_floor_request_label(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method guide_floor_request_label")

    def guide_floor_family_specs(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method guide_floor_family_specs")

    def compact_guide_matches(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method compact_guide_matches")

    async def ask_guide_choice(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method ask_guide_choice")

    async def handle_guide_choice_number(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method handle_guide_choice_number")

    def find_guide_npc(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method find_guide_npc")

    async def guide_to(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method guide_to")

# v4.20.0: exact historical implementations rebound onto original class.
SessionGuideNavigationMixin.show_current_city_walk_destinations = _sb420_bind(_sb420_src_01.show_current_city_walk_destinations, globals(), "SessionGuideNavigationMixin")
SessionGuideNavigationMixin.room_search_aliases = _sb420_bind(_sb420_src_01.room_search_aliases, globals(), "SessionGuideNavigationMixin")
SessionGuideNavigationMixin.guide_zone_query_name = _sb420_bind(_sb420_src_01.guide_zone_query_name, globals(), "SessionGuideNavigationMixin")
SessionGuideNavigationMixin.rooms_in_exact_zone = _sb420_bind(_sb420_src_01.rooms_in_exact_zone, globals(), "SessionGuideNavigationMixin")
SessionGuideNavigationMixin.find_room_matches = _sb420_bind(_sb420_src_01.find_room_matches, globals(), "SessionGuideNavigationMixin")
SessionGuideNavigationMixin.show_guide_destinations = _sb420_bind(_sb420_src_01.show_guide_destinations, globals(), "SessionGuideNavigationMixin")
SessionGuideNavigationMixin.compact_route_directions = _sb420_bind(_sb420_src_01.compact_route_directions, globals(), "SessionGuideNavigationMixin")
SessionGuideNavigationMixin.cancel_guide = _sb420_bind(_sb420_src_01.cancel_guide, globals(), "SessionGuideNavigationMixin")
SessionGuideNavigationMixin.show_guide_status = _sb420_bind(_sb420_src_01.show_guide_status, globals(), "SessionGuideNavigationMixin")
SessionGuideNavigationMixin._guide_task_finished = _sb420_bind(_sb420_src_01._guide_task_finished, globals(), "SessionGuideNavigationMixin")
SessionGuideNavigationMixin.start_guide_task = _sb420_bind(_sb420_src_01.start_guide_task, globals(), "SessionGuideNavigationMixin")
SessionGuideNavigationMixin.show_route_next_step = _sb420_bind(_sb420_src_01.show_route_next_step, globals(), "SessionGuideNavigationMixin")
SessionGuideNavigationMixin.show_route = _sb420_bind(_sb420_src_02.show_route, globals(), "SessionGuideNavigationMixin")
SessionGuideNavigationMixin.shortest_path = _sb420_bind(_sb420_src_02.shortest_path, globals(), "SessionGuideNavigationMixin")
SessionGuideNavigationMixin.shortest_path_within_floor_v11340 = _sb420_bind(_sb420_src_02.shortest_path_within_floor_v11340, globals(), "SessionGuideNavigationMixin")
SessionGuideNavigationMixin.guide_descending_floor_v1501 = _sb420_bind(_sb420_src_02.guide_descending_floor_v1501, globals(), "SessionGuideNavigationMixin")
SessionGuideNavigationMixin.guide_exploration_safe_target = _sb420_bind(_sb420_src_02.guide_exploration_safe_target, globals(), "SessionGuideNavigationMixin")
SessionGuideNavigationMixin.guide_floor_request_label = _sb420_bind(_sb420_src_02.guide_floor_request_label, globals(), "SessionGuideNavigationMixin")
SessionGuideNavigationMixin.guide_floor_family_specs = _sb420_bind(_sb420_src_02.guide_floor_family_specs, globals(), "SessionGuideNavigationMixin")
SessionGuideNavigationMixin.compact_guide_matches = _sb420_bind(_sb420_src_02.compact_guide_matches, globals(), "SessionGuideNavigationMixin")
SessionGuideNavigationMixin.ask_guide_choice = _sb420_bind(_sb420_src_02.ask_guide_choice, globals(), "SessionGuideNavigationMixin")
SessionGuideNavigationMixin.handle_guide_choice_number = _sb420_bind(_sb420_src_02.handle_guide_choice_number, globals(), "SessionGuideNavigationMixin")
SessionGuideNavigationMixin.find_guide_npc = _sb420_bind(_sb420_src_02.find_guide_npc, globals(), "SessionGuideNavigationMixin")
SessionGuideNavigationMixin.guide_to = _sb420_bind(_sb420_src_03.guide_to, globals(), "SessionGuideNavigationMixin")

