"""Soulbound v4.00.1: authored world expansion implementation.

Public entry points remain available from world.expansions.
"""

from data import catalog_mutations as _catalog_mut
# v0.45.0: explicit imports; no compatibility-runtime injection.
from core.bootstrap_economy_professions import QUEST_REPEAT_COOLDOWN_SECONDS
from core.classes_skills import ORE_ATLAS_LEVELS, ORE_MINE_FLOOR_MINIMUMS
from core.mines_threat import CHARACTER_BOUND_TOOL_IDS, EXP_AREAS, GUIDE_DESTINATION_ALIASES, TOOL_SHOP_ROOMS
from core.progression_resources import (
    FISH_ATLAS_ALL,
    FISH_RESOURCE_IDS,
    HERB_ATLAS_ALL,
    HERB_RESOURCE_IDS,
    ORE_ATLAS_ALL,
    ORE_RESOURCE_IDS,
    RIVER_FISHING_ROOMS,
    WOOD_ATLAS_ALL,
    WOOD_RESOURCE_IDS,
)
from systems.content_registry import HELP_TOPICS, HELP_TOPIC_ALIASES, MOB_DESCRIPTIONS
from systems.dungeons_regions import (
    FISHING_ROOMS,
    GIANT_FORTRESS_BOSS_FLOORS,
    GIANT_FORTRESS_BOSS_MECHANICS,
    GIANT_FORTRESS_BOSS_NAMES,
    GIANT_FORTRESS_MAX_FLOOR,
    HERBALISM_ROOMS,
    ITEMS,
    MOB_SPAWNS,
    MOB_TEMPLATES,
    NPCS,
    QUESTS,
    RARE_TROLL_VARIANTS,
    ROOMS,
    WOODCUTTING_ROOMS,
    _register_elite_variants,
    _register_rare_variants,
    giant_fortress_floor_id,
)
from systems.equipment_crafting import (
    FISH_STORAGE_IDS,
    MINING_STORAGE_IDS,
    ORE_STORAGE_IDS,
    SHOPS,
    SHOP_SELLERS,
)
from systems.items_resources import HERB_STORAGE_IDS, WOOD_STORAGE_IDS

def build_world_expansion_i():
    """Compatibility facade; keep EXP_AREAS updates visible to old callers."""
    global EXP_AREAS
    import world.expansion_frontier_north_v407 as _impl
    _impl.EXP_AREAS = EXP_AREAS
    result = _impl.build_world_expansion_i()
    EXP_AREAS = _impl.EXP_AREAS
    return result

def build_world_expansion_ii():
    """Compatibility facade; keep EXP_AREAS updates visible to old callers."""
    global EXP_AREAS
    import world.expansion_frontier_fields_v407 as _impl
    _impl.EXP_AREAS = EXP_AREAS
    result = _impl.build_world_expansion_ii()
    EXP_AREAS = _impl.EXP_AREAS
    return result

def build_forest_wolves_and_quest_balance():
    """Compatibility facade; keep EXP_AREAS updates visible to old callers."""
    global EXP_AREAS
    import world.expansion_frontier_forest_v407 as _impl
    _impl.EXP_AREAS = EXP_AREAS
    result = _impl.build_forest_wolves_and_quest_balance()
    EXP_AREAS = _impl.EXP_AREAS
    return result
