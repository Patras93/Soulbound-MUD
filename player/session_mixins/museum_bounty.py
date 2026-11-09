# -*- coding: utf-8 -*-
"""Museum, achievements, collection recording and bounty board."""

# v0.44.0: explicit dependencies; no compatibility-global injection.
import math
import random
from core.bootstrap_economy_professions import SILVER_PER_GOLD, TOOL_PROFESSION_MAP, currency_reading_text, profession_max_level
from core.classes_skills import ROOMS
from core.mines_threat import ITEMS
from core.progression_resources import (
    V019_QUEST_COIN,
    V019_SOUL_KILL_NORMAL,
    v0190_log_curve,
    v0190_mob_stage,
    v0190_quest_stage,
    v096_fishing_workload_scale,
)
from network.protocol_gameplay_utils import canonical_profession_resource_id, normalize_lookup_text, v0929_kill_drop_item
from systems.content_registry import MOB_TEMPLATES, QUESTS
from systems.crafting_quality import player_item_display_name_v0335
from systems.equipment_crafting import CUT_GEM_IDS, RAW_GEM_IDS
from systems.items_resources import RARE_FISH_VARIANT_IDS
from world.dynamic_content import (
    ACHIEVEMENT_TITLE_REWARDS,
    ACHIEVEMENT_TRACKS,
    ALL_EXPLORATION_ROOMS,
    BESTIARY_CATALOG,
    BESTIARY_SPAWN_ROOMS,
    BOSS_COLLECTION_CATALOG,
    BOUNTY_KINDS,
    BOUNTY_OFFER_COUNT,
    BOUNTY_RESOURCE_LABELS,
    BOUNTY_RESOURCE_NEEDS,
    COLLECTION_CATALOGS,
    EQUIPMENT_COLLECTION_CATALOG,
    FISH_COLLECTION_CATALOG,
    GEM_COLLECTION_CATALOG,
    HERB_COLLECTION_CATALOG,
    MATERIAL_COLLECTION_CATALOG,
    MINERAL_COLLECTION_CATALOG,
    MINI_BOSS_IDS,
    NAMED_LOOT_CATALOG,
    SET_COLLECTION_CATALOG,
    SET_ENTRY_BY_ITEM,
    UNIQUE_ITEM_COLLECTION_CATALOG,
    canonical_bestiary_template_id,
    loot_filter_allows,
    loot_rarity_rank,
)
from world.economy_quests import (
    COLLECTION_CATEGORY_LABELS,
    INSTANCE_MAP_DEFS,
    instance_secret_index,
    v0863_is_boss_template,
    v0914_combat_quest_stat_reward,
)
from world.world_state import (
    V0260_GLOBAL_MUSEUM_TITLES,
    V0260_INSTANCE_SECRET_CATALOG,
    V0260_LEGENDARY_ITEM_CATALOG,
    V0260_MUSEUM_ALIASES,
    V0260_MUSEUM_CATALOGS,
    V0260_MUSEUM_CATEGORY_TITLES,
    V0260_MUSEUM_LABELS,
    V0260_SET_PIECE_GROUPS,
    V0260_SURFACE_SECRET_CATALOG,
    V0260_TITLE_BONUSES,
    V0260_WOOD_CATALOG,
    v0260_museum_rank,
)



from .museum_parts_v109 import (
    MuseumTitlesV109Mixin,
    MuseumMuseumV109Mixin,
    MuseumAchievementsV109Mixin,
    MuseumBountyCatalogV109Mixin,
    MuseumBountyBoardV109Mixin,
    MuseumCollectionV109Mixin,
    MuseumKillProgressV109Mixin,
)

class SessionMuseumBountyMixin(
    MuseumTitlesV109Mixin,
    MuseumMuseumV109Mixin,
    MuseumAchievementsV109Mixin,
    MuseumBountyCatalogV109Mixin,
    MuseumBountyBoardV109Mixin,
    MuseumCollectionV109Mixin,
    MuseumKillProgressV109Mixin,
):
    """Stara nazwa klasy i komplet metod; MRO zgodne z v108."""
    pass
