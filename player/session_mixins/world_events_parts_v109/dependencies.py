# -*- coding: utf-8 -*-
"""Jawne historyczne zaleznosci systemow swiata v109.

Kod importow/aliasow zachowany z world_events_endgame.py.
"""
# -*- coding: utf-8 -*-
"""Weather, factions, events, ascension and endgame systems."""
from core.bootstrap_economy_professions import currency_price_text
# v0.45.0: explicit imports; no compatibility-runtime injection.
import random
import time
from core.bootstrap_economy_professions import CURRENCY_SQLITE_SAFE_TOTAL, currency_unit_multiplier
from network.protocol_gameplay_utils import find_by_name
from player.session_mixins.equipment_stats import CLASS_MASTERY_MAX_LEVEL, REGIONAL_SET_BONUSES, v0210_world_tier_multipliers
from player.session_mixins.io_auth_character import CLASSES
from player.session_mixins.museum_bounty import (
    ITEMS,
    MOB_TEMPLATES,
    QUESTS,
    ROOMS,
    currency_reading_text,
    normalize_lookup_text,
    player_item_display_name_v0335,
)
from storage.db_schema import FISH_RESOURCE_IDS, legacy_currency_to_coins
from systems.items_resources import fish_rarity_label, format_fish_length, format_fish_weight
from world.generation_systems import (
    V013_FRONTIER_ROOMS_PER_BIOME,
    V013_FRONTIER_SPECS,
    V014_EVENT_DEFS as V014_WORLD_EVENT_DEFS,
    V014_TREASURE_MAP_ITEM,
    V015_BIOME_MASTERY_THRESHOLDS,
    V015_WEATHER_POOLS,
    V016_FACTIONS,
    V016_FACTION_THRESHOLDS,
    V016_TRAVELERS,
    V017_ARTIFACTS,
    V017_BIOME_SET_NAMES,
    V017_FACTION_STORIES,
    V017_FACTION_STORY_QUESTS,
    V018_ENDLESS_POWER_CAP_BAND,
    V018_EXPEDITIONS,
    V018_TRANSPORT_HUBS,
    V018_TRANSPORT_ORIGINS,
    V020_ARTIFACT_MAX_TIER,
    V020_ARTIFACT_UPGRADE_COSTS,
    V020_ARTIFACT_VARIANTS,
    V020_ENDGAME_GOALS,
    V020_GAUNTLETS,
    V020_GAUNTLET_LOBBY,
    V020_MEGADUNGEONS,
    v0130_frontier_room_id,
    v0130_frontier_room_identity,
    v0130_frontier_room_ids,
    v0140_active_world_events,
    v0140_event_for_room,
    v0140_surface_secret_room_ids,
    v0150_biome_mastery_title,
    v0150_dynamic_world_offer,
    v0150_environment_bonus,
    v0150_time_state,
    v0150_weather_state,
    v0160_active_legendary_rares,
    v0160_active_world_bosses,
    v0160_faction_rank,
    v0160_traveler_room,
    v0180_active_legendary_events,
    v0180_all_great_ruins,
    v0180_archipelago_room_id,
    v0180_endless_band,
    v0180_endless_identity,
    v0180_season_state,
    v0200_active_mythic_world_bosses,
    v0200_artifact_owned_tier,
    v0200_mega_gate_id,
    v0200_mega_identity,
    v0200_mega_is_boss_index,
)
from world.runtime_progression import (
    V021_ASCENSION_MAX_RANK,
    V021_MYTHIC_SET_NAMES,
    V021_WORLD_TIER_ASCENSION_REQUIREMENT,
    V021_WORLD_TIER_MAX,
    V022_LEGENDARY_KINDS,
    V022_PROJECT_CATEGORY_LABELS,
    V022_PROJECT_RESOURCE_SOURCES,
    V022_WORLD_PROJECTS,
    V027_LEGENDARY_MIN_MASTERY,
    v0210_ascension_xp_to_next,
    v0210_endless_gauntlet_identity,
    v0210_endless_gauntlet_room_id,
    v022_fish_rarity_score,
    v022_legendary_contract_offer,
    v022_project_reward,
)
from world.world_state import v0290_active_world_events
from world.uoss_superbosses import UOSS_SUPERBOSS_ENCOUNTERS_V11134
from world.uoss_superboss_runtime import (
    superboss_cleared_v11135,
    superboss_member_entry_error_v11331,
    superboss_series_progress_v11138,
    weapon_pair_exchange_ready_v11141,
)


