# v4.20.0: bound, AST-identical method implementations (MRO unchanged)
from core.legacy_method_binding_v4200 import bind_legacy_method_v4200 as _sb420_bind
import player.session_methods_v4200.gathering_part01 as _sb420_src_01
# SessionGatheringMixin.stop_auto_fishing -> player/session_methods_v4200/gathering_part01.py
# SessionGatheringMixin.auto_fishing_loop -> player/session_methods_v4200/gathering_part01.py
# SessionGatheringMixin.set_auto_fishing -> player/session_methods_v4200/gathering_part01.py
# SessionGatheringMixin.stop_auto_mining -> player/session_methods_v4200/gathering_part01.py
# SessionGatheringMixin.auto_mining_loop -> player/session_methods_v4200/gathering_part01.py
# SessionGatheringMixin.set_auto_mining -> player/session_methods_v4200/gathering_part01.py
# SessionGatheringMixin.stop_auto_woodcutting -> player/session_methods_v4200/gathering_part01.py
# SessionGatheringMixin.auto_woodcutting_loop -> player/session_methods_v4200/gathering_part01.py
# SessionGatheringMixin.set_auto_woodcutting -> player/session_methods_v4200/gathering_part01.py
# SessionGatheringMixin.stop_auto_herbalism -> player/session_methods_v4200/gathering_part01.py
# SessionGatheringMixin.auto_herbalism_loop -> player/session_methods_v4200/gathering_part01.py
# SessionGatheringMixin.set_auto_herbalism -> player/session_methods_v4200/gathering_part01.py
import player.session_methods_v4200.gathering_part02 as _sb420_src_02
# SessionGatheringMixin.show_profession_ranks -> player/session_methods_v4200/gathering_part02.py
# SessionGatheringMixin.show_professions -> player/session_methods_v4200/gathering_part02.py
# SessionGatheringMixin.show_tool_tiers -> player/session_methods_v4200/gathering_part02.py
# SessionGatheringMixin.tool_info_definition -> player/session_methods_v4200/gathering_part02.py
# SessionGatheringMixin.tool_bonus_label -> player/session_methods_v4200/gathering_part02.py
# SessionGatheringMixin.tool_action_label -> player/session_methods_v4200/gathering_part02.py
# SessionGatheringMixin.show_single_tool -> player/session_methods_v4200/gathering_part02.py
# SessionGatheringMixin.show_tools -> player/session_methods_v4200/gathering_part02.py
# SessionGatheringMixin.fishing_water_type -> player/session_methods_v4200/gathering_part02.py
# SessionGatheringMixin.fishing_ecology_pool -> player/session_methods_v4200/gathering_part02.py
# SessionGatheringMixin.fishing_loot -> player/session_methods_v4200/gathering_part02.py
# SessionGatheringMixin.show_water_info -> player/session_methods_v4200/gathering_part02.py
import player.session_methods_v4200.gathering_part03 as _sb420_src_03
# SessionGatheringMixin.show_fish_journal -> player/session_methods_v4200/gathering_part03.py
# SessionGatheringMixin.mining_loot -> player/session_methods_v4200/gathering_part03.py
# SessionGatheringMixin.mining_gem_drop -> player/session_methods_v4200/gathering_part03.py
# SessionGatheringMixin.woodcutting_loot -> player/session_methods_v4200/gathering_part03.py
# SessionGatheringMixin.herbalism_loot -> player/session_methods_v4200/gathering_part03.py

# -*- coding: utf-8 -*-
"""Auto gathering, profession views and gathering loot."""
# v0.44.0: explicit dependencies; no compatibility-global injection.
from core.mine_tunnels import HORIZONTAL_MINE_DIRECTIONS
import asyncio
import random
from core.bootstrap_economy_professions import (
    PROFESSION_RANK_NAMES,
    TOOL_TIER_NAMES,
    balance_math,
    profession_for_tool_type,
    profession_max_level,
    profession_max_rank,
    profession_rank,
    profession_rank_name,
    profession_rank_thresholds,
    tool_max_level,
    tool_tier,
    tool_tier_access_level,
    tool_tier_bonus_chance,
    tool_tier_name,
)
from core.classes_skills import ORE_ATLAS_LEVELS, ORE_MINE_FLOOR_MINIMUMS, ROOMS
from core.mines_threat import ITEMS
from core.progression_600 import (
    PROFESSION_MAX_LEVEL,
    TOOL_MAX_LEVEL,
    TOOL_MAX_TIER,
    TOOL_TIER_BONUS_CHANCES,
    TOOL_TIER_THRESHOLDS,
)
from core.progression_resources import (
    FISHING_ECOLOGY_PREFERRED_IDS,
    FISHING_HABITAT_LABELS,
    FISHING_ROOMS,
    FISHING_WATER_TYPE_OVERRIDES,
    FISH_RESOURCE_IDS,
    HERBALISM_ROOMS,
    HERB_RESOURCE_IDS,
    LAKE_FISHING_ROOMS,
    LAKE_FISH_ATLAS,
    OCEAN_FISHING_ROOMS,
    OCEAN_FISH_ATLAS,
    ORE_RESOURCE_IDS,
    RIVER_FISHING_ROOMS,
    RIVER_FISH_ATLAS,
    SEA_FISHING_ROOMS,
    SEA_FISH_ATLAS,
    WOODCUTTING_ROOMS,
    WOOD_RESOURCE_IDS,
    is_mining_room,
    mine_floor_number,
    mining_ore_weights,
)
from core.profession_timing import profession_action_seconds as authored_profession_action_seconds
from network.protocol_gameplay_utils import find_by_name, normalize_lookup_text
from systems.dungeons_regions import profession_dungeon_floor
from systems.equipment_crafting import roll_mined_gem_quality
from systems.items_resources import (
    base_fish_species_id,
    fish_rarity_label,
    fish_species_habitats,
    fish_species_rarity,
    format_fish_length,
    format_fish_weight,
)
class SessionGatheringMixin:
    def active_event_fishery_v3312(self):
            from world.generation_systems import active_profession_event_for_room
            return bool(self.character and active_profession_event_for_room(self.character.room_id, "fishing"))

    def active_profession_event_v3312(self, tool_type):
            from world.generation_systems import active_profession_event_for_room
            return bool(self.character and active_profession_event_for_room(self.character.room_id, tool_type))

    async def stop_auto_fishing(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method stop_auto_fishing")
    async def auto_fishing_loop(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method auto_fishing_loop")
    async def set_auto_fishing(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method set_auto_fishing")
    async def stop_auto_mining(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method stop_auto_mining")
    async def auto_mining_loop(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method auto_mining_loop")
    async def set_auto_mining(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method set_auto_mining")
    async def stop_auto_woodcutting(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method stop_auto_woodcutting")
    async def auto_woodcutting_loop(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method auto_woodcutting_loop")
    async def set_auto_woodcutting(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method set_auto_woodcutting")

    async def stop_auto_herbalism(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method stop_auto_herbalism")

    async def auto_herbalism_loop(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method auto_herbalism_loop")

    async def set_auto_herbalism(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method set_auto_herbalism")

    async def show_profession_ranks(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method show_profession_ranks")

    async def show_professions(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method show_professions")

    async def show_tool_tiers(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method show_tool_tiers")

    def tool_info_definition(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method tool_info_definition")

    def tool_bonus_label(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method tool_bonus_label")

    def profession_level_for_tool(self, tool_type):
            profession = profession_for_tool_type(tool_type)
            if not profession:
                return 1
            row = self.server.db.profession(self.account_id, profession)
            return max(1, min(profession_max_level(profession), int(row["level"])))

    def profession_action_seconds(self, tool_type, profession_level):
            return authored_profession_action_seconds(tool_type, profession_level)

    def tool_action_seconds(self, tool_type, profession_level):
            """Alias zgodności: od v0.8.66 argument oznacza poziom PROFESJI, nie narzędzia."""
            return self.profession_action_seconds(tool_type, profession_level)

    def recipe_action_seconds(self, tool_type, profession_level, recipe):
            """Authored profession tempo plus recipe-stage complexity."""
            base = authored_profession_action_seconds(tool_type, profession_level)
            required = max(1, min(PROFESSION_MAX_LEVEL, int(recipe.get("generator_level", 1) or 1)))
            progress_gap = max(0, required - int(profession_level))
            generated_penalty = int(round(3.0 * progress_gap / float(PROFESSION_MAX_LEVEL)))
            return max(1, int(base + generated_penalty))

    def tool_action_label(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method tool_action_label")

    def tool_xp_remaining_to_level(self, level, xp, tool_type=None):
            max_level = tool_max_level(tool_type)
            if level >= max_level:
                return 0
            return max(
                0,
                self.tool_xp_to_next(level, tool_type) - int(xp),
            )

    def tool_xp_remaining_to_next_tier(self, level, xp, tool_type=None):
            tier = tool_tier(level)
            if tier >= TOOL_MAX_TIER:
                return 0, 0

            target_level = TOOL_TIER_THRESHOLDS[tier]
            levels_remaining = max(0, target_level - level)

            total_xp = self.tool_xp_remaining_to_level(level, xp, tool_type)
            for current_level in range(level + 1, target_level):
                total_xp += self.tool_xp_to_next(current_level, tool_type)

            return levels_remaining, total_xp

    async def show_single_tool(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method show_single_tool")

    async def show_tools(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method show_tools")

    def fishing_water_type(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method fishing_water_type")

    def fishing_habitat(self, room_id=None):
            room_id = room_id or self.character.room_id
            if room_id in RIVER_FISHING_ROOMS: return "river"
            if room_id in LAKE_FISHING_ROOMS: return "lake"
            if room_id in SEA_FISHING_ROOMS: return "sea"
            if room_id in OCEAN_FISHING_ROOMS: return "ocean"
            # Temporary fish events on procedural frontiers are real fisheries.
            from world.generation_systems import active_profession_event_for_room
            event = active_profession_event_for_room(room_id, "fishing")
            if event:
                return {"river":"river", "lake":"lake", "coast":"sea",
                        "ocean":"ocean", "void":"ocean"}.get(event["kind"], "river")
            return None

    def fishing_available_pool(self, tool_level, habitat=None):
            habitat = habitat or self.fishing_habitat()
            tool_level = max(1, min(TOOL_MAX_LEVEL, int(tool_level)))
            access_level = tool_tier_access_level(tool_level)
            habitat_ids = {
                "river": tuple(RIVER_FISH_ATLAS),
                "lake": tuple(LAKE_FISH_ATLAS),
                "sea": tuple(SEA_FISH_ATLAS),
                "ocean": tuple(OCEAN_FISH_ATLAS),
            }.get(habitat, ())
            return balance_math.resource_pool(
                habitat_ids, ITEMS, access_level, f"fishing:{habitat or 'unknown'}"
            )

    def fishing_ecology_pool(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method fishing_ecology_pool")

    def fishing_loot(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method fishing_loot")

    async def show_water_info(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method show_water_info")

    async def show_fish_journal(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method show_fish_journal")

    def mining_loot(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method mining_loot")

    def mining_gem_drop(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method mining_gem_drop")

    def woodcutting_loot(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method woodcutting_loot")

    def herbalism_loot(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method herbalism_loot")

# v4.20.0: exact historical implementations rebound onto original class.
SessionGatheringMixin.stop_auto_fishing = _sb420_bind(_sb420_src_01.stop_auto_fishing, globals(), "SessionGatheringMixin")
SessionGatheringMixin.auto_fishing_loop = _sb420_bind(_sb420_src_01.auto_fishing_loop, globals(), "SessionGatheringMixin")
SessionGatheringMixin.set_auto_fishing = _sb420_bind(_sb420_src_01.set_auto_fishing, globals(), "SessionGatheringMixin")
SessionGatheringMixin.stop_auto_mining = _sb420_bind(_sb420_src_01.stop_auto_mining, globals(), "SessionGatheringMixin")
SessionGatheringMixin.auto_mining_loop = _sb420_bind(_sb420_src_01.auto_mining_loop, globals(), "SessionGatheringMixin")
SessionGatheringMixin.set_auto_mining = _sb420_bind(_sb420_src_01.set_auto_mining, globals(), "SessionGatheringMixin")
SessionGatheringMixin.stop_auto_woodcutting = _sb420_bind(_sb420_src_01.stop_auto_woodcutting, globals(), "SessionGatheringMixin")
SessionGatheringMixin.auto_woodcutting_loop = _sb420_bind(_sb420_src_01.auto_woodcutting_loop, globals(), "SessionGatheringMixin")
SessionGatheringMixin.set_auto_woodcutting = _sb420_bind(_sb420_src_01.set_auto_woodcutting, globals(), "SessionGatheringMixin")
SessionGatheringMixin.stop_auto_herbalism = _sb420_bind(_sb420_src_01.stop_auto_herbalism, globals(), "SessionGatheringMixin")
SessionGatheringMixin.auto_herbalism_loop = _sb420_bind(_sb420_src_01.auto_herbalism_loop, globals(), "SessionGatheringMixin")
SessionGatheringMixin.set_auto_herbalism = _sb420_bind(_sb420_src_01.set_auto_herbalism, globals(), "SessionGatheringMixin")
SessionGatheringMixin.show_profession_ranks = _sb420_bind(_sb420_src_02.show_profession_ranks, globals(), "SessionGatheringMixin")
SessionGatheringMixin.show_professions = _sb420_bind(_sb420_src_02.show_professions, globals(), "SessionGatheringMixin")
SessionGatheringMixin.show_tool_tiers = _sb420_bind(_sb420_src_02.show_tool_tiers, globals(), "SessionGatheringMixin")
SessionGatheringMixin.tool_info_definition = _sb420_bind(_sb420_src_02.tool_info_definition, globals(), "SessionGatheringMixin")
SessionGatheringMixin.tool_bonus_label = _sb420_bind(_sb420_src_02.tool_bonus_label, globals(), "SessionGatheringMixin")
SessionGatheringMixin.tool_action_label = _sb420_bind(_sb420_src_02.tool_action_label, globals(), "SessionGatheringMixin")
SessionGatheringMixin.show_single_tool = _sb420_bind(_sb420_src_02.show_single_tool, globals(), "SessionGatheringMixin")
SessionGatheringMixin.show_tools = _sb420_bind(_sb420_src_02.show_tools, globals(), "SessionGatheringMixin")
SessionGatheringMixin.fishing_water_type = _sb420_bind(_sb420_src_02.fishing_water_type, globals(), "SessionGatheringMixin")
SessionGatheringMixin.fishing_ecology_pool = _sb420_bind(_sb420_src_02.fishing_ecology_pool, globals(), "SessionGatheringMixin")
SessionGatheringMixin.fishing_loot = _sb420_bind(_sb420_src_02.fishing_loot, globals(), "SessionGatheringMixin")
SessionGatheringMixin.show_water_info = _sb420_bind(_sb420_src_02.show_water_info, globals(), "SessionGatheringMixin")
SessionGatheringMixin.show_fish_journal = _sb420_bind(_sb420_src_03.show_fish_journal, globals(), "SessionGatheringMixin")
SessionGatheringMixin.mining_loot = _sb420_bind(_sb420_src_03.mining_loot, globals(), "SessionGatheringMixin")
SessionGatheringMixin.mining_gem_drop = _sb420_bind(_sb420_src_03.mining_gem_drop, globals(), "SessionGatheringMixin")
SessionGatheringMixin.woodcutting_loot = _sb420_bind(_sb420_src_03.woodcutting_loot, globals(), "SessionGatheringMixin")
SessionGatheringMixin.herbalism_loot = _sb420_bind(_sb420_src_03.herbalism_loot, globals(), "SessionGatheringMixin")

