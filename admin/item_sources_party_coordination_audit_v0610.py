# -*- coding: utf-8 -*-
"""Feature audit for Soulbound v0.61.0-v0.61.2 item guidance, party coordination and memory efficiency."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def item_sources_party_coordination_audit_v0610():
    errors = []

    required_files = (
        "player/session_mixins/item_sources.py",
        "player/session_mixins/party.py",
        "player/session_mixins/command_registry.py",
        "config/command_aliases.py",
        "player/session.py",
        "server/mud_server.py",
        "core/runtime_manifest.py",
        "admin/help_refresh.py",
    )
    for rel in required_files:
        if not (ROOT / rel).is_file():
            errors.append(f"missing file: {rel}")

    def text(rel):
        return (ROOT / rel).read_text(encoding="utf-8")

    try:
        src = text("player/session_mixins/item_sources.py")
        for token in (
            'V0610_ITEM_SOURCE_VERSION = "0.61.0"',
            'V0611_CRAFT_GUIDANCE_VERSION = "0.61.1"',
            "def resolve_item_query_v0610(",
            "def item_source_entries_v0610(",
            "def item_use_entries_v0611(",
            "def resolve_recipe_query_v0611(",
            "def live_recipe_rows_v0611(",
            "async def show_item_sources_v0610(",
            "async def show_item_uses_v0611(",
            "async def show_recipe_gaps_v0611(",
            "async def show_available_recipes_v0611(",
            "SHOPS", "CRAFT_RECIPES", "QUESTS", "MOB_TEMPLATES", "MOB_SPAWNS",
            "FISH_RESOURCE_IDS", "ORE_RESOURCE_IDS", "WOOD_RESOURCE_IDS", "HERB_RESOURCE_IDS",
            "crafted_base_id_v03054", "base_resource_id",
            "RUNE_CRAFT_COSTS_V03114", "TECH_SET_UPGRADE_COSTS_V0320", "V03053_ENCHANTS",
        ):
            if token not in src:
                errors.append(f"item source finder contract missing: {token}")
    except Exception as exc:
        errors.append(f"item source finder check failed: {exc}")

    try:
        registry = text("player/session_mixins/command_registry.py")
        if "'itemsource': ('show_item_sources_v0610'" not in registry:
            errors.append("itemsource registry handler missing")
        if 'raw in ("gdzie", "where")' not in registry or 'return "itemsource"' not in registry:
            errors.append("multi-word gdzie zdobyc resolver missing")
        for token in (
            "'itemuses': ('show_item_uses_v0611'",
            "'recipegaps': ('show_recipe_gaps_v0611'",
            "'availablerecipes': ('show_available_recipes_v0611'",
            'return "itemuses"',
            'return "recipegaps"',
            'return "availablerecipes"',
        ):
            if token not in registry:
                errors.append(f"v0.61.1 command routing missing: {token}")
        aliases = text("config/command_aliases.py")
        for token in (
            "'gdziezdobyc': 'itemsource'",
            "'gdziezdobyć': 'itemsource'",
            "'whereget': 'itemsource'",
            "'doczego': 'itemuses'",
            "'brakireceptura': 'recipegaps'",
            "'recepturymozliwe': 'availablerecipes'",
            "'craftmozliwe': 'availablerecipes'",
        ):
            if token not in aliases:
                errors.append(f"itemsource alias missing: {token}")
        session = text("player/session.py")
        if session.count("SessionItemSourcesV0610Mixin") < 2:
            errors.append("Session assembly missing SessionItemSourcesV0610Mixin")
    except Exception as exc:
        errors.append(f"item source routing check failed: {exc}")

    try:
        party = text("player/session_mixins/party.py")
        for token in (
            "async def set_party_goal_v0610(",
            "async def show_party_ready_v0610(",
            "async def handle_party_ready_v0610(",
            "async def set_party_not_ready_v0610(",
            "party_goals", "party_ready_checks",
            'action in ("cel", "goal", "objective")',
            'action in ("gotowi", "ready", "readycheck")',
            'action in ("niegotowy", "notready", "unready")',
            "WSZYSCY GOTOWI",
        ):
            if token not in party:
                errors.append(f"party coordination contract missing: {token}")
        server = text("server/mud_server.py")
        for token in ("self.party_goals = {}", "self.party_ready_checks = {}"):
            if token not in server:
                errors.append(f"party server state missing: {token}")
        # Goal/readiness must migrate on leader handoff and be cleared on party teardown.
        if "goal = self.server.party_goals.pop(key, None)" not in party:
            errors.append("party goal is not migrated on leader handoff")
        if party.count("self.server.party_goals.pop(key, None)") < 3:
            errors.append("party goal cleanup is incomplete")
        if party.count("self.server.party_ready_checks.pop(key, None)") < 4:
            errors.append("ready-check cleanup/reset is incomplete")
    except Exception as exc:
        errors.append(f"party coordination check failed: {exc}")

    try:
        manifest = text("core/runtime_manifest.py")
        for rel in (
            "player/session_mixins/item_sources.py",
            "admin/item_sources_party_coordination_audit_v0610.py",
        ):
            if rel not in manifest:
                errors.append(f"runtime manifest missing {rel}")
    except Exception as exc:
        errors.append(f"runtime manifest check failed: {exc}")

    return {
        "version": "0.61.1",
        "error_count": len(errors),
        "errors": errors,
    }


ITEM_SOURCES_PARTY_COORDINATION_AUDIT_V0610 = item_sources_party_coordination_audit_v0610()
if ITEM_SOURCES_PARTY_COORDINATION_AUDIT_V0610["error_count"]:
    raise RuntimeError(
        "Item Sources & Party Coordination Audit v0.61.1 failed: "
        + "; ".join(ITEM_SOURCES_PARTY_COORDINATION_AUDIT_V0610["errors"][:100])
    )


def memory_efficiency_audit_v0612():
    errors = []
    def text(rel):
        return (ROOT / rel).read_text(encoding="utf-8")
    checks = {
        "systems/equipment_crafting.py": ("opis zwykłego klasowego EQ jest składany na żądanie",),
        "systems/dungeons_regions.py": ("opis wariantu Krypty jest generowany przy wyświetleniu",),
        "systems/items_resources.py": ("opis materiałowego EQ jest składany na żądanie",),
        "player/session_mixins/atlas_codex.py": ("def item_runtime_description(", "crypt_set_tier", "corpse_random_variant", "class_shop_item"),
        "admin/help_refresh.py": ("stara nazwa pozostaje w aliases",),
    }
    for rel, tokens in checks.items():
        try:
            src = text(rel)
            for token in tokens:
                if token not in src:
                    errors.append(f"memory efficiency contract missing in {rel}: {token}")
        except Exception as exc:
            errors.append(f"memory efficiency check failed for {rel}: {exc}")
    return {"version":"0.61.2", "error_count":len(errors), "errors":errors}


V0612_MEMORY_EFFICIENCY_AUDIT = memory_efficiency_audit_v0612()
if V0612_MEMORY_EFFICIENCY_AUDIT["error_count"]:
    raise RuntimeError(
        "Memory Efficiency Audit v0.61.2 failed: "
        + "; ".join(V0612_MEMORY_EFFICIENCY_AUDIT["errors"][:100])
    )

__all__ = [
    "item_sources_party_coordination_audit_v0610",
    "ITEM_SOURCES_PARTY_COORDINATION_AUDIT_V0610",
    "memory_efficiency_audit_v0612",
    "V0612_MEMORY_EFFICIENCY_AUDIT",
]
