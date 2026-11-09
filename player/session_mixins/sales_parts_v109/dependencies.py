# -*- coding: utf-8 -*-
"""Item/resource sale rules, bulk selling and sale XP."""
from core.bootstrap_economy_professions import currency_price_text

# v0.44.0: explicit dependencies; no compatibility-global injection.
import re
from core.bootstrap_economy_professions import (
    PROFESSION_XP_GAIN_MULTIPLIER,
    currency_reading_text,
    legacy_currency_to_coins,
    profession_max_level,
    profession_max_rank,
    profession_rank,
    profession_rank_name,
)
from core.mines_threat import EQUIPMENT_SLOT_ALIASES, ITEMS, is_character_bound_item
from core.progression_resources import (
    v0190_resource_sale_coins,
    v0190_resource_stage,
    v096_fishing_reward_scale,
    v1138_resource_sale_base_coins,
)
from network.protocol_gameplay_utils import find_by_name, normalize_lookup_text
from systems.content_registry import NPCS
from systems.crafting_expansion import CRAFT_MATERIAL_STORAGE_IDS
from systems.equipment_crafting import MINING_STORAGE_IDS, SHOPS, SHOP_SELLERS
from systems.legacy_value_sweep import legacy_explicit_sale_value_v11325
from systems.items_resources import (
    BLACKSMITH_SLOT_DEFS,
    BLACKSMITH_TIERS,
    FISH_STORAGE_IDS,
    HERB_STORAGE_IDS,
    WOOD_STORAGE_IDS,
    economy_stage_anchor_v11314,
    fish_trophy_value_multiplier_v1138,
    v096_fish_price_scale,
    profession_resource_market_value_v1148,
)
from world.economy_quests import V0863_MATERIAL_SALE_BASE_SILVER


V11314_ARMOR_RESALE_QUEST_FRACTION = {
    "common": 0.025, "crafted": 0.035, "uncommon": 0.035,
    "rare": 0.050, "epic": 0.070, "legendary": 0.100,
    "mythic": 0.140, "unique": 0.160, "eternal": 0.180,
}
