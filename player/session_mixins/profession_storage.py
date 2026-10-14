# v4.20.0: bound, AST-identical method implementations (MRO unchanged)
from core.legacy_method_binding_v4200 import bind_legacy_method_v4200 as _sb420_bind
import player.session_methods_v4200.professionstorage_part01 as _sb420_src_01
# SessionProfessionStorageMixin.valid_tool_type -> player/session_methods_v4200/professionstorage_part01.py
# SessionProfessionStorageMixin.tool_display_name_v11343 -> player/session_methods_v4200/professionstorage_part01.py
# SessionProfessionStorageMixin.tool_progress_state -> player/session_methods_v4200/professionstorage_part01.py
# SessionProfessionStorageMixin.profession_content_level_v11342 -> player/session_methods_v4200/professionstorage_part01.py
# SessionProfessionStorageMixin.profession_content_xp_floor_v11342 -> player/session_methods_v4200/professionstorage_part01.py
# SessionProfessionStorageMixin.profession_content_xp_multiplier_v11342 -> player/session_methods_v4200/professionstorage_part01.py
# SessionProfessionStorageMixin.grant_profession_progress -> player/session_methods_v4200/professionstorage_part01.py
# SessionProfessionStorageMixin.grant_tool_progress -> player/session_methods_v4200/professionstorage_part01.py
import player.session_methods_v4200.professionstorage_part02 as _sb420_src_02
# SessionProfessionStorageMixin.store_profession_resource -> player/session_methods_v4200/professionstorage_part02.py
# SessionProfessionStorageMixin.category_ids -> player/session_methods_v4200/professionstorage_part02.py
# SessionProfessionStorageMixin.profession_storage_definition -> player/session_methods_v4200/professionstorage_part02.py
# SessionProfessionStorageMixin.profession_storage_summary -> player/session_methods_v4200/professionstorage_part02.py
# SessionProfessionStorageMixin.show_craftbox_v0925 -> player/session_methods_v4200/professionstorage_part02.py
# SessionProfessionStorageMixin.show_container -> player/session_methods_v4200/professionstorage_part02.py
# SessionProfessionStorageMixin.put_in_container -> player/session_methods_v4200/professionstorage_part02.py
# SessionProfessionStorageMixin.take_from_container -> player/session_methods_v4200/professionstorage_part02.py
# SessionProfessionStorageMixin.grant_tool_reward_xp -> player/session_methods_v4200/professionstorage_part02.py
import player.session_methods_v4200.professionstorage_part03 as _sb420_src_03
# SessionProfessionStorageMixin.grant_profession_reward_xp -> player/session_methods_v4200/professionstorage_part03.py

# -*- coding: utf-8 -*-
"""Profession XP, tools and profession storage."""
from core.bootstrap_economy_professions import currency_price_text

# v0.44.0: explicit dependencies; no compatibility-global injection.
from config.balance import (
    PROFESSION_XP_REQUIREMENT_MULTIPLIERS,
    TOOL_XP_REQUIREMENT_MULTIPLIERS,
    profession_xp_requirement_v1401,
    tool_xp_requirement_v1402,
)
from core.bootstrap_economy_professions import (
    PROFESSION_XP_GAIN_MULTIPLIER,
    currency_reading_text,
    balance_math,
    profession_max_level,
    profession_max_rank,
    profession_rank,
    profession_rank_name,
    tool_max_level,
    tool_tier,
    tool_tier_bonus_chance,
    tool_tier_name,
)
from core.mines_threat import ITEMS
from data.quests import QUESTS
from core.progression_600 import CHARACTER_MAX_LEVEL, PROFESSION_MAX_LEVEL, TOOL_MAX_TIER
from core.profession_batch_v1176 import profession_batch_effort_v1176
from core.progression_resources import (
    FISH_RESOURCE_IDS,
    HERB_RESOURCE_IDS,
    ORE_RESOURCE_IDS,
    WOOD_RESOURCE_IDS,
    v0190_requirement,
    v0190_resource_sale_coins,
    v0190_scaled_gain,
)
from network.protocol_gameplay_utils import (
    V0925_CRAFTBOX_ALIASES,
    V0925_CRAFTBOX_CATEGORIES,
    find_by_name,
    normalize_lookup_text,
    v0925_craftbox_category,
)
from systems.crafting_expansion import CRAFT_MATERIAL_STORAGE_IDS
from systems.crafting_quality import player_item_display_name_v0335
from systems.equipment_crafting import MINING_STORAGE_IDS, RAW_GEM_IDS
from systems.items_resources import FISH_STORAGE_IDS, HERB_STORAGE_IDS, ORE_STORAGE_IDS, WOOD_STORAGE_IDS, profession_resource_market_value_v1148


class SessionProfessionStorageMixin:

    def profession_xp_to_next(self, level, profession=None):
            max_level = (
                profession_max_level(profession)
                if profession is not None
                else PROFESSION_MAX_LEVEL
            )
            if level >= max_level:
                return 0
            base = v0190_requirement("profession", level)
            return profession_xp_requirement_v1401(base, profession, level)

    def tool_xp_to_next(self, level, tool_type=None):
            max_level = tool_max_level(tool_type)
            if level >= max_level:
                return 0

            base = v0190_requirement("tool", level)
            return tool_xp_requirement_v1402(base, tool_type, level)

    def valid_tool_type(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method valid_tool_type")

    def profession_xp_status_text_v11343(self, profession):
            row=self.server.db.profession(self.account_id,profession)
            level=int(row["level"])
            maximum=profession_max_level(profession)
            if level>=maximum:
                return "maksimum"
            needed=self.profession_xp_to_next(level,profession)
            return f"{int(row['xp'])} z {needed}"

    def tool_xp_status_text_v11343(self, tool_type):
            row=self.server.db.tool(self.account_id,tool_type)
            level=int(row["level"])
            maximum=tool_max_level(tool_type)
            if level>=maximum:
                return "maksimum"
            needed=self.tool_xp_to_next(level,tool_type)
            return f"{int(row['xp'])} z {needed}"

    def tool_display_name_v11343(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method tool_display_name_v11343")

    def tool_progress_state(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method tool_progress_state")

    def profession_content_level_v11342(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method profession_content_level_v11342")

    def profession_content_xp_floor_v11342(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method profession_content_xp_floor_v11342")

    def profession_content_xp_multiplier_v11342(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method profession_content_xp_multiplier_v11342")

    def profession_authored_xp_multiplier_v11343(self, raw_xp, baseline_xp):
            raw=max(0,int(raw_xp or 0))
            baseline=max(1,int(baseline_xp or 1))
            if raw<=0:
                return 0.0
            return max(1.0,min(2.5,raw/float(baseline)))

    def grant_profession_progress(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method grant_profession_progress")

    def grant_tool_progress(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method grant_tool_progress")

    def store_profession_resource(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method store_profession_resource")

    def migrate_raw_mining_gems_to_bag_v0867(self):
            moved = 0
            for item_id in RAW_GEM_IDS:
                qty = self.server.db.item_qty(self.account_id, item_id)
                if qty <= 0:
                    continue
                if self.server.db.remove_item(self.account_id, item_id, qty):
                    self.server.db.add_storage_item(
                        self.account_id, "bag", item_id, qty
                    )
                    moved += qty
            return moved

    def migrate_craft_materials_to_casket_v0915(self):
            moved = 0
            for item_id in CRAFT_MATERIAL_STORAGE_IDS:
                qty = self.server.db.item_qty(self.account_id, item_id)
                if qty <= 0:
                    continue
                if self.server.db.remove_item(self.account_id, item_id, qty):
                    self.server.db.add_storage_item(
                        self.account_id, "craftbox", item_id, qty
                    )
                    moved += qty
            return moved

    def container_label(self, container):
            return {
                "net": "Siatka na ryby",
                "bag": "Sakwa górnicza",
                "woodpile": "Stos drewna",
                "herbbag": "Torba Zielarska",
                "craftbox": "Szkatułka Rzemieślnicza",
            }.get(container, container)

    def normalize_container(self, token):
            t = token.strip().lower()
            if t in ("net", "siatka", "siatkę", "siatke"):
                return "net"
            if t in ("bag", "sakwa", "sakwe", "sakwę", "worek"):
                return "bag"
            if t in ("woodpile", "stos", "drewno", "sterta"):
                return "woodpile"
            if t in ("herbbag", "ziola", "zioła", "herbs", "torba"):
                return "herbbag"
            if t in ("craftbox", "szkatulka", "szkatułka", "materialy", "materiały"):
                return "craftbox"
            return None

    def category_ids(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method category_ids")

    def profession_storage_definition(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method profession_storage_definition")

    def profession_storage_summary(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method profession_storage_summary")

    def fish_net_summary(self, rows=None):
            generic = self.profession_storage_summary(
                "net", rows
            )
            return {
                "fish": generic["count"],
                "species": generic["types"],
                "silver": generic["silver"],
                "gold": generic["gold"],
                "mithril": generic["mithril"],
            }

    def profession_storage_value_text(self, summary):
            return currency_reading_text(
                summary["silver"], summary["gold"], summary["mithril"]
            )

    def fish_net_value_text(self, summary):
            return self.profession_storage_value_text(summary)

    async def show_craftbox_v0925(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method show_craftbox_v0925")

    async def show_container(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method show_container")

    async def put_in_container(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method put_in_container")

    async def take_from_container(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method take_from_container")

    async def grant_tool_reward_xp(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method grant_tool_reward_xp")

    async def grant_profession_reward_xp(self, *args, **kwargs):
        """Compatibility method; rebound to the original implementation."""
        raise RuntimeError("Unbound Soulbound method grant_profession_reward_xp")

# v4.20.0: exact historical implementations rebound onto original class.
SessionProfessionStorageMixin.valid_tool_type = _sb420_bind(_sb420_src_01.valid_tool_type, globals(), "SessionProfessionStorageMixin")
SessionProfessionStorageMixin.tool_display_name_v11343 = _sb420_bind(_sb420_src_01.tool_display_name_v11343, globals(), "SessionProfessionStorageMixin")
SessionProfessionStorageMixin.tool_progress_state = _sb420_bind(_sb420_src_01.tool_progress_state, globals(), "SessionProfessionStorageMixin")
SessionProfessionStorageMixin.profession_content_level_v11342 = _sb420_bind(_sb420_src_01.profession_content_level_v11342, globals(), "SessionProfessionStorageMixin")
SessionProfessionStorageMixin.profession_content_xp_floor_v11342 = _sb420_bind(_sb420_src_01.profession_content_xp_floor_v11342, globals(), "SessionProfessionStorageMixin")
SessionProfessionStorageMixin.profession_content_xp_multiplier_v11342 = _sb420_bind(_sb420_src_01.profession_content_xp_multiplier_v11342, globals(), "SessionProfessionStorageMixin")
SessionProfessionStorageMixin.grant_profession_progress = _sb420_bind(_sb420_src_01.grant_profession_progress, globals(), "SessionProfessionStorageMixin")
SessionProfessionStorageMixin.grant_tool_progress = _sb420_bind(_sb420_src_01.grant_tool_progress, globals(), "SessionProfessionStorageMixin")
SessionProfessionStorageMixin.store_profession_resource = _sb420_bind(_sb420_src_02.store_profession_resource, globals(), "SessionProfessionStorageMixin")
SessionProfessionStorageMixin.category_ids = _sb420_bind(_sb420_src_02.category_ids, globals(), "SessionProfessionStorageMixin")
SessionProfessionStorageMixin.profession_storage_definition = _sb420_bind(_sb420_src_02.profession_storage_definition, globals(), "SessionProfessionStorageMixin")
SessionProfessionStorageMixin.profession_storage_summary = _sb420_bind(_sb420_src_02.profession_storage_summary, globals(), "SessionProfessionStorageMixin")
SessionProfessionStorageMixin.show_craftbox_v0925 = _sb420_bind(_sb420_src_02.show_craftbox_v0925, globals(), "SessionProfessionStorageMixin")
SessionProfessionStorageMixin.show_container = _sb420_bind(_sb420_src_02.show_container, globals(), "SessionProfessionStorageMixin")
SessionProfessionStorageMixin.put_in_container = _sb420_bind(_sb420_src_02.put_in_container, globals(), "SessionProfessionStorageMixin")
SessionProfessionStorageMixin.take_from_container = _sb420_bind(_sb420_src_02.take_from_container, globals(), "SessionProfessionStorageMixin")
SessionProfessionStorageMixin.grant_tool_reward_xp = _sb420_bind(_sb420_src_02.grant_tool_reward_xp, globals(), "SessionProfessionStorageMixin")
SessionProfessionStorageMixin.grant_profession_reward_xp = _sb420_bind(_sb420_src_03.grant_profession_reward_xp, globals(), "SessionProfessionStorageMixin")

