# -*- coding: utf-8 -*-
"""Soulbound v0.57.0 - Courier and database schema modularization audit."""
from pathlib import Path

from core.runtime_manifest import EXPLICIT_RUNTIME_EXPORTS, RUNTIME_MODULES

ROOT = Path(__file__).resolve().parents[1]

SCHEMA_MODULES_V0570 = (
    "storage/schema_core.py",
    "storage/schema_progression.py",
    "storage/schema_world_quests.py",
    "storage/schema_social_guilds.py",
    "storage/schema_migrate_social.py",
    "storage/schema_migrate_character.py",
    "storage/schema_migrate_guilds.py",
    "storage/schema_migrate_tools.py",
    "storage/schema_migrate_economy.py",
    "storage/schema_migrate_history.py",
)


def modular_refactor_audit_v0570():
    errors = []
    social_path = ROOT / "player/session_mixins/social_expansion.py"
    courier_path = ROOT / "player/session_mixins/courier_delivery.py"
    schema_path = ROOT / "storage/db_schema.py"
    session_path = ROOT / "player/session.py"

    social = social_path.read_text(encoding="utf-8")
    courier = courier_path.read_text(encoding="utf-8")
    schema = schema_path.read_text(encoding="utf-8")
    session = session_path.read_text(encoding="utf-8")

    social_lines = len(social.splitlines())
    courier_lines = len(courier.splitlines())
    schema_lines = len(schema.splitlines())
    if social_lines > 500:
        errors.append(f"social_expansion grew back above 500 lines: {social_lines}")
    if courier_lines > 550:
        errors.append(f"courier_delivery unexpectedly large: {courier_lines}")
    if schema_lines > 100:
        errors.append(f"db_schema orchestration grew above 100 lines: {schema_lines}")

    for token in ("postal_offers_v0522", "postal_deliver_v0522", "courier_sync_achievements_v0540"):
        if token not in courier:
            errors.append(f"courier module missing {token}")
        if token in social:
            errors.append(f"courier method leaked back into social_expansion: {token}")
    if "SessionCourierDeliveryMixin" not in session or "courier_delivery" not in session:
        errors.append("Session does not compose SessionCourierDeliveryMixin")

    required_calls = (
        "create_core_schema", "create_progression_schema", "create_world_quests_schema",
        "create_social_guilds_schema", "migrate_social_courier_schema",
        "migrate_character_columns", "migrate_guild_schema", "migrate_character_legacy",
        "migrate_stats_and_tools", "migrate_accounts_and_economy",
        "migrate_history_and_collections",
    )
    for token in required_calls:
        if token not in schema:
            errors.append(f"db_schema orchestrator missing {token}")

    schema_line_counts = {}
    for rel in SCHEMA_MODULES_V0570:
        path = ROOT / rel
        if not path.is_file():
            errors.append(f"missing focused schema module: {rel}")
            continue
        count = len(path.read_text(encoding="utf-8").splitlines())
        schema_line_counts[rel] = count
        if count > 350:
            errors.append(f"focused schema module too large: {rel}={count}")
        if rel not in RUNTIME_MODULES:
            errors.append(f"schema module not in runtime manifest: {rel}")
        if rel not in EXPLICIT_RUNTIME_EXPORTS:
            errors.append(f"schema module not explicit: {rel}")

    if "player/session_mixins/courier_delivery.py" not in RUNTIME_MODULES:
        errors.append("courier_delivery missing from runtime manifest")
    if "player/session_mixins/courier_delivery.py" not in EXPLICIT_RUNTIME_EXPORTS:
        errors.append("courier_delivery is not an explicit runtime module")

    required_schema_tokens = {
        "storage/schema_core.py": ("CREATE TABLE IF NOT EXISTS characters", "CREATE TABLE IF NOT EXISTS inventory"),
        "storage/schema_world_quests.py": ("CREATE TABLE IF NOT EXISTS quests", "CREATE TABLE IF NOT EXISTS achievements"),
        "storage/schema_migrate_social.py": ("postal_delivery_state_v0522", "courier_guild_state_v0530", "activity_journal_v0560"),
        "storage/schema_migrate_character.py": ("soul_weapon_mastery_level", "character_level"),
    }
    for rel, tokens in required_schema_tokens.items():
        text = (ROOT / rel).read_text(encoding="utf-8")
        for token in tokens:
            if token not in text:
                errors.append(f"{rel}: missing preserved schema token {token}")

    return {
        "version": "0.57.0",
        "social_lines": social_lines,
        "courier_lines": courier_lines,
        "db_schema_lines": schema_lines,
        "focused_schema_module_count": len(SCHEMA_MODULES_V0570),
        "largest_schema_module_lines": max(schema_line_counts.values(), default=0),
        "error_count": len(errors),
        "errors": errors,
    }


MODULAR_REFACTOR_AUDIT_V0570 = modular_refactor_audit_v0570()
if MODULAR_REFACTOR_AUDIT_V0570["error_count"]:
    raise RuntimeError(
        "Modular Refactor Audit v0.57.0 failed: "
        + "; ".join(MODULAR_REFACTOR_AUDIT_V0570["errors"][:100])
    )

__all__ = ["modular_refactor_audit_v0570", "MODULAR_REFACTOR_AUDIT_V0570", "SCHEMA_MODULES_V0570"]
