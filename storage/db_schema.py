# -*- coding: utf-8 -*-
"""Database schema orchestration. Focused schema/migration modules own the details."""

from core.bootstrap_economy_professions import legacy_currency_to_coins, normalize_currency_values
from core.classes_skills import (
    CLASSES,
    CLASS_STARTING_STAT_BONUSES,
    RACES,
    V0876_CLASS_STARTING_STAT_BONUSES,
    V0876_RACE_BASE_STATS,
)
from core.mines_threat import CHARACTER_BOUND_TOOL_IDS
from core.progression_resources import FISH_RESOURCE_IDS
from network.protocol_gameplay_utils import V0926_GUILD_DEFAULT_ROLES, V0927_GUILD_CONTRACTS, canonical_profession_resource_id
from systems.content_registry import MOB_TEMPLATES
from systems.items_resources import base_fish_species_id
from world.dynamic_content import (
    BOSS_COLLECTION_CATALOG,
    FISH_COLLECTION_CATALOG,
    GEM_COLLECTION_CATALOG,
    HERB_COLLECTION_CATALOG,
    MATERIAL_COLLECTION_CATALOG,
    MINERAL_COLLECTION_CATALOG,
    UNIQUE_ITEM_COLLECTION_CATALOG,
    canonical_bestiary_template_id,
)

from storage.schema_core import create_core_schema
from storage.schema_progression import create_progression_schema
from storage.schema_world_quests import create_world_quests_schema
from storage.schema_social_guilds import create_social_guilds_schema
from storage.schema_migrate_social import migrate_social_courier_schema
from storage.schema_migrate_character import migrate_character_columns, migrate_character_legacy
from storage.schema_migrate_guilds import migrate_guild_schema
from storage.schema_migrate_tools import migrate_stats_and_tools
from storage.schema_migrate_economy import migrate_accounts_and_economy
from storage.schema_migrate_history import migrate_history_and_collections


class DatabaseSchemaMixin:
    def create_schema(self):
        create_core_schema(self)
        create_progression_schema(self)
        create_world_quests_schema(self)
        create_social_guilds_schema(self)
        self.conn.commit()

    def migrate_schema(self):
        migrate_social_courier_schema(self)
        character_level_was_new = migrate_character_columns(self)
        migrate_guild_schema(self, V0926_GUILD_DEFAULT_ROLES, V0927_GUILD_CONTRACTS)
        migrate_character_legacy(self, character_level_was_new)
        migrate_stats_and_tools(self, CHARACTER_BOUND_TOOL_IDS)
        migrate_accounts_and_economy(
            self, legacy_currency_to_coins, normalize_currency_values, CLASSES,
            CLASS_STARTING_STAT_BONUSES, RACES, V0876_CLASS_STARTING_STAT_BONUSES,
            V0876_RACE_BASE_STATS,
        )
        migrate_history_and_collections(
            self, FISH_RESOURCE_IDS, canonical_profession_resource_id, MOB_TEMPLATES,
            base_fish_species_id, BOSS_COLLECTION_CATALOG, FISH_COLLECTION_CATALOG,
            GEM_COLLECTION_CATALOG, HERB_COLLECTION_CATALOG, MATERIAL_COLLECTION_CATALOG,
            MINERAL_COLLECTION_CATALOG, UNIQUE_ITEM_COLLECTION_CATALOG, canonical_bestiary_template_id,
        )
        self.conn.commit()
