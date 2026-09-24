# -*- coding: utf-8 -*-
"""Soulbound v0.61.4 — Crafting Logistics & Mail Escrow audit."""

import inspect

from config.command_aliases import COMMAND_ALIAS_DEFINITIONS
from data.crafting_recipes import CRAFT_RECIPES
from player.session_mixins.command_registry import COMMAND_REGISTRY
from player.session_mixins.crafting_expansion import SessionCraftingExpansionV03114Mixin
from player.session_mixins.crafting_orders import SessionCraftingOrdersV0600Mixin
from player.session_mixins.item_sources import SessionItemSourcesV0610Mixin
from player.session_mixins.mail_attachments import SessionMailAttachmentsV0614Mixin
from storage.db_inventory import DatabaseInventoryMixin
from storage.db_quests import DatabaseQuestMixin
from storage.schema_migrate_social import migrate_social_courier_schema
from storage.schema_world_quests import create_world_quests_schema

V0614_CRAFTING_LOGISTICS_VERSION = "0.61.4"


def crafting_logistics_audit_v0614():
    errors = []
    metrics = {}

    bulk_src = inspect.getsource(SessionCraftingExpansionV03114Mixin.craft_item_v03114)
    many_src = inspect.getsource(SessionCraftingExpansionV03114Mixin.craft_many_v0614)
    metrics["bulk_count_syntax"] = "words[0].isdigit()" in bulk_src and "craft_many_v0614" in bulk_src
    metrics["bulk_all_syntax"] = '"wszystko"' in bulk_src and '"max"' in bulk_src
    metrics["bulk_reuses_single_recipe_engine"] = "perform_recipe" in many_src

    metrics["recipe_route_alias"] = COMMAND_ALIAS_DEFINITIONS.get("recepturadroga") == "reciperoute"
    metrics["recipe_route_handler"] = "reciperoute" in COMMAND_REGISTRY
    route_src = inspect.getsource(SessionItemSourcesV0610Mixin.show_recipe_route_v0614)
    metrics["recipe_route_recursive"] = "_emit_recipe_route_v0614" in route_src

    order_src = inspect.getsource(SessionCraftingOrdersV0600Mixin.handle_crafting_orders_v0600)
    db_order_src = inspect.getsource(DatabaseQuestMixin.finish_crafting_order_v0614)
    world_schema_src = inspect.getsource(create_world_quests_schema)
    metrics["order_history_ui"] = "crafting_order_stats_v0614" in order_src
    metrics["order_history_atomic_write"] = "crafting_order_stats_v0614" in db_order_src and 'self.conn.execute("BEGIN")' in db_order_src
    metrics["order_history_schema"] = "crafting_order_stats_v0614" in world_schema_src

    mail_src = inspect.getsource(SessionMailAttachmentsV0614Mixin.handle_mail_v03051)
    db_mail_send_src = inspect.getsource(DatabaseInventoryMixin.send_mail_attachment_v0614)
    db_mail_claim_src = inspect.getsource(DatabaseInventoryMixin.claim_mail_attachment_v0614)
    mail_schema_src = inspect.getsource(migrate_social_courier_schema)
    metrics["mail_item_attachment"] = "kind='item'" in mail_src
    metrics["mail_currency_attachment"] = "kind='currency'" in mail_src
    metrics["mail_claim_command"] = "claim_mail_attachment_v0614" in mail_src
    metrics["mail_atomic_send"] = 'self.conn.execute("BEGIN")' in db_mail_send_src
    metrics["mail_atomic_claim"] = 'self.conn.execute("BEGIN")' in db_mail_claim_src
    metrics["mail_schema"] = "attachment_kind" in mail_schema_src and "attachment_claimed" in mail_schema_src

    fragment_recipes = [
        (rid, recipe) for rid, recipe in CRAFT_RECIPES.items()
        if "salvage_mithril_fragment" in (recipe.get("ingredients") or {})
    ]
    fragment_eq = [
        (rid, recipe) for rid, recipe in fragment_recipes
        if str(recipe.get("category") or "") == "salvage_forging"
    ]
    metrics["mithril_fragment_recipe_count"] = len(fragment_recipes)
    metrics["mithril_fragment_eq_recipe_count"] = len(fragment_eq)
    metrics["mithril_fragment_refining_count"] = len(fragment_recipes) - len(fragment_eq)
    standard_ingot_eq = [
        (rid, recipe) for rid, recipe in CRAFT_RECIPES.items()
        if str(recipe.get("category") or "") == "smithing"
        and any(str(iid).endswith("_ingot") for iid in (recipe.get("ingredients") or {}))
        and str(recipe.get("output") or "") in __import__("data.items", fromlist=["ITEMS"]).ITEMS
    ]
    metrics["standard_ingot_eq_recipe_count"] = len(standard_ingot_eq)
    metrics["standard_ingot_smithing_preserved"] = len(standard_ingot_eq) >= 6
    if len(fragment_eq) != 6:
        errors.append(f"expected 6 Fragment Mithrilu EQ recipes, got {len(fragment_eq)}")
    if metrics["mithril_fragment_refining_count"] < 2:
        errors.append("missing Fragment Mithrilu refining sinks")
    for rid, recipe in fragment_eq:
        if "forge" not in tuple(recipe.get("stations") or ()):
            errors.append(f"{rid}: Fragment Mithrilu EQ recipe is not forge-only")
        if int(recipe.get("min_profession_level", 0) or 0) != 80:
            errors.append(f"{rid}: expected Kowalstwo level 80")

    for key, value in metrics.items():
        if isinstance(value, bool) and not value:
            errors.append(f"missing v0.61.4 contract: {key}")

    return {
        "version": V0614_CRAFTING_LOGISTICS_VERSION,
        "error_count": len(errors),
        "errors": errors,
        **metrics,
    }


CRAFTING_LOGISTICS_AUDIT_V0614 = crafting_logistics_audit_v0614()
if CRAFTING_LOGISTICS_AUDIT_V0614["error_count"]:
    raise RuntimeError(
        "Crafting Logistics Audit v0.61.4 failed: "
        + "; ".join(CRAFTING_LOGISTICS_AUDIT_V0614["errors"][:100])
    )


__all__ = [
    "V0614_CRAFTING_LOGISTICS_VERSION",
    "crafting_logistics_audit_v0614",
    "CRAFTING_LOGISTICS_AUDIT_V0614",
]
