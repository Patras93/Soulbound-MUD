# -*- coding: utf-8 -*-
"""Static architecture audit for Soulbound v0.60.0 crafting orders + EQ compare."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def crafting_orders_compare_audit_v0600():
    errors = []
    required_files = (
        "player/session_mixins/crafting_orders.py",
        "player/session_mixins/equipment_compare.py",
        "storage/schema_world_quests.py",
        "storage/db_quests.py",
        "player/session_mixins/quest_progress.py",
        "player/session_mixins/command_registry.py",
        "config/command_aliases.py",
        "systems/content_registry.py",
        "player/session.py",
        "core/runtime_manifest.py",
    )
    for rel in required_files:
        if not (ROOT / rel).exists():
            errors.append(f"missing file: {rel}")

    def text(rel):
        return (ROOT / rel).read_text(encoding="utf-8")

    try:
        schema = text("storage/schema_world_quests.py")
        if "CREATE TABLE IF NOT EXISTS crafting_orders_v0600" not in schema:
            errors.append("crafting_orders_v0600 schema missing")
        for col in ("completed_cycle_slot", "reward_profession_xp", "reward_tool_xp", "progress"):
            if col not in schema:
                errors.append(f"crafting order schema missing column: {col}")
    except Exception as exc:
        errors.append(f"schema check failed: {exc}")

    try:
        db = text("storage/db_quests.py")
        for method in (
            "crafting_order_v0600", "start_crafting_order_v0600",
            "increment_crafting_order_v0600", "abandon_crafting_order_v0600",
            "finish_crafting_order_v0600",
        ):
            if f"def {method}(" not in db:
                errors.append(f"missing db method: {method}")
    except Exception as exc:
        errors.append(f"db check failed: {exc}")

    try:
        orders = text("player/session_mixins/crafting_orders.py")
        for npc_id in (
            "specialist_crafting", "specialist_cooking", "specialist_alchemy",
            "jeweler_mirella", "tailor_lysa", "leatherworker_soren", "carpenter_edric",
        ):
            if npc_id not in orders:
                errors.append(f"missing crafting order NPC: {npc_id}")
        for token in (
            "CRAFTING_ORDER_REFRESH_SECONDS_V0600 = 3600",
            "handle_crafting_orders_v0600", "announce_crafting_order_progress_v0600",
            "zamowienia oddaj", "Zamówienia nie dają Soul XP",
        ):
            if token not in orders:
                errors.append(f"crafting order contract missing: {token}")
        progress = text("player/session_mixins/quest_progress.py")
        if "await self.announce_crafting_order_progress_v0600(item_id, amount)" not in progress:
            errors.append("craft event is not wired to rotating crafting orders")
    except Exception as exc:
        errors.append(f"crafting orders check failed: {exc}")

    try:
        compare = text("player/session_mixins/equipment_compare.py")
        for token in (
            "compare_equipment_v0600", "equipment_reforge", "equipment_upgrade_level_v03042",
            "equipment_runes_v0925", "socketed_gems", "ring1", "charm1", "earring1",
        ):
            if token not in compare:
                errors.append(f"EQ compare contract missing: {token}")
    except Exception as exc:
        errors.append(f"EQ compare check failed: {exc}")

    try:
        aliases = text("config/command_aliases.py")
        for token in (
            "'zamowienia': 'craftorders'", "'zamówienia': 'craftorders'",
            "'porownaj': 'compareeq'", "'porównaj': 'compareeq'", "'compare': 'compareeq'",
        ):
            if token not in aliases:
                errors.append(f"alias missing: {token}")
        registry = text("player/session_mixins/command_registry.py")
        if "'craftorders': ('handle_crafting_orders_v0600'" not in registry:
            errors.append("craftorders registry handler missing")
        if "'compareeq': ('compare_equipment_v0600'" not in registry:
            errors.append("compareeq registry handler missing")
    except Exception as exc:
        errors.append(f"command routing check failed: {exc}")

    try:
        session = text("player/session.py")
        for cls in ("SessionCraftingOrdersV0600Mixin", "SessionEquipmentCompareV0600Mixin"):
            if session.count(cls) < 2:
                errors.append(f"Session assembly missing {cls}")
        manifest = text("core/runtime_manifest.py")
        for rel in ("player/session_mixins/crafting_orders.py", "player/session_mixins/equipment_compare.py"):
            if rel not in manifest:
                errors.append(f"runtime manifest missing {rel}")
    except Exception as exc:
        errors.append(f"assembly check failed: {exc}")

    return {
        "version": "0.60.0",
        "error_count": len(errors),
        "errors": errors,
    }


CRAFTING_ORDERS_COMPARE_AUDIT_V0600 = crafting_orders_compare_audit_v0600()
if CRAFTING_ORDERS_COMPARE_AUDIT_V0600["error_count"]:
    raise RuntimeError(
        "Crafting Orders & EQ Compare Audit v0.60.0 failed: "
        + "; ".join(CRAFTING_ORDERS_COMPARE_AUDIT_V0600["errors"][:100])
    )

__all__ = ["crafting_orders_compare_audit_v0600", "CRAFTING_ORDERS_COMPARE_AUDIT_V0600"]
