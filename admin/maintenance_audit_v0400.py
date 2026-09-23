# -*- coding: utf-8 -*-
"""Soulbound v0.40.0 maintenance architecture audit."""


def maintenance_architecture_audit_v0400():
    import ast
    from pathlib import Path
    from core.maintenance_catalog import MAINTENANCE_AREAS
    from core.runtime_manifest import EXPECTED_SESSION_METHOD_DUPLICATES, RUNTIME_MODULES

    root = Path(globals().get("_ROOT", Path.cwd()))
    errors = []
    metrics = {}

    required = (
        "storage/db_schema.py", "storage/schema_core.py", "storage/schema_progression.py", "storage/schema_world_quests.py", "storage/schema_social_guilds.py", "storage/db_accounts.py", "storage/db_world.py",
        "storage/db_inventory.py", "storage/db_progression.py", "storage/db_quests.py",
        "storage/db_guilds.py", "player/session_mixins/skill_learning.py",
        "player/session_mixins/skill_queue_buffs.py", "player/session_mixins/combat.py",
        "player/session_mixins/profession_storage.py", "player/session_mixins/guide_navigation.py",
        "player/session_mixins/gathering.py", "player/session_mixins/crafting.py",
        "player/session_mixins/inventory_equipment.py", "player/session_mixins/shops_teachers.py",
        "player/session_mixins/movement.py", "player/session_mixins/party.py",
        "player/session_mixins/exp_terrain.py", "player/session_mixins/social_base.py",
        "player/session_mixins/banking_charisma.py", "player/session_mixins/quest_progress.py",
        "player/session_mixins/quest_offers.py", "player/session_mixins/quest_turnin.py",
        "player/session_mixins/quest_npc.py", "player/session_mixins/quest_commands.py",
        "player/session_mixins/museum_bounty.py", "player/session_mixins/world_events_endgame.py",
        "player/session_mixins/exploration_progress.py", "player/session_mixins/collection_loot_records.py",
        "player/session_mixins/help_system.py", "player/session_mixins/atlas_codex.py",
        "player/session_mixins/character_profile.py", "player/session_mixins/class_guild_progress.py",
        "player/session_mixins/admin_tools.py", "player/session_mixins/gathering_actions.py",
        "player/session_mixins/sales.py", "player/session_mixins/session_runtime_state.py",
        "player/session_mixins/dungeon_progression.py", "player/session_mixins/rest_mana.py",
        "player/session_mixins/class_progression.py",
        "core/maintenance_catalog.py", "core/runtime_diagnostics.py",
    )
    missing = [rel for rel in required if not (root / rel).is_file()]
    if missing:
        errors.append("missing maintenance files: " + ", ".join(missing))

    db_facade = root / "storage/database.py"
    db_lines = len(db_facade.read_text(encoding="utf-8").splitlines()) if db_facade.is_file() else 999999
    if db_lines > 100:
        errors.append(f"database facade grew to {db_lines} lines; expected <=100")

    focused_limits = {
        "player/session_mixins/combat.py": 2300,
        "player/session_mixins/skill_learning.py": 1800,
        "player/session_mixins/skill_queue_buffs.py": 800,
        "player/session_mixins/guide_navigation.py": 1700,
        "player/session_mixins/gathering.py": 1300,
        "player/session_mixins/crafting.py": 1000,
        "player/session_mixins/inventory_equipment.py": 2000,
        "player/session_mixins/shops_teachers.py": 600,
        "player/session_mixins/movement.py": 600,
        "player/session_mixins/party.py": 1100,
        "player/session_mixins/exp_terrain.py": 700,
        "player/session_mixins/social_base.py": 550,
        "player/session_mixins/banking_charisma.py": 650,
        "player/session_mixins/quest_progress.py": 800,
        "player/session_mixins/quest_offers.py": 950,
        "player/session_mixins/quest_turnin.py": 800,
        "player/session_mixins/quest_npc.py": 650,
        "player/session_mixins/quest_commands.py": 400,
        "player/session_mixins/museum_bounty.py": 1100,
        "player/session_mixins/world_events_endgame.py": 950,
        "player/session_mixins/exploration_progress.py": 650,
        "player/session_mixins/collection_loot_records.py": 900,
        "player/session_mixins/help_system.py": 650,
        "player/session_mixins/atlas_codex.py": 1500,
        "player/session_mixins/character_profile.py": 500,
        "player/session_mixins/class_guild_progress.py": 400,
        "player/session_mixins/admin_tools.py": 300,
        "player/session_mixins/gathering_actions.py": 800,
        "player/session_mixins/sales.py": 1000,
        "player/session_mixins/session_runtime_state.py": 400,
        "player/session_mixins/dungeon_progression.py": 850,
        "player/session_mixins/rest_mana.py": 400,
        "player/session_mixins/class_progression.py": 450,
    }
    for rel, limit in focused_limits.items():
        path = root / rel
        if not path.is_file():
            continue
        count = len(path.read_text(encoding="utf-8").splitlines())
        if count > limit:
            errors.append(f"focused module too large: {rel}={count}, limit={limit}")

    # New accidental duplicate Session methods are dangerous because MRO silently
    # chooses one. Keep the compatibility exceptions explicit.
    observed = {}
    for rel in RUNTIME_MODULES:
        path = root / rel
        if not path.is_file():
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except Exception as exc:
            errors.append(f"parse failed: {rel}: {exc}")
            continue
        for cls in (node for node in tree.body if isinstance(node, ast.ClassDef)):
            if not (cls.name.startswith("Session") and cls.name.endswith("Mixin")):
                continue
            for node in cls.body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    observed.setdefault(node.name, []).append(f"{rel}:{cls.name}")
    duplicates = {name: owners for name, owners in observed.items() if len(owners) > 1}
    if duplicates != EXPECTED_SESSION_METHOD_DUPLICATES:
        errors.append(f"session method duplicate policy mismatch: {duplicates}")

    registry_source = (root / "player/session_mixins/command_registry.py").read_text(encoding="utf-8")
    server_source = (root / "server/mud_server.py").read_text(encoding="utf-8")
    if "report_runtime_error" not in registry_source:
        errors.append("registered commands do not have a runtime error boundary")
    if "while not session.closed:" not in server_source or "report_runtime_error" not in server_source:
        errors.append("custom command/session error recovery boundary is missing")

    required_areas = {"combat", "quests", "skills", "gathering", "navigation/guide", "crafting", "inventory/equipment", "commands"}
    if not required_areas.issubset(MAINTENANCE_AREAS):
        errors.append("maintenance catalog is missing core repair areas")

    metrics.update({
        "database_facade_lines": db_lines,
        "focused_module_count": len(focused_limits),
        "maintenance_area_count": len(MAINTENANCE_AREAS),
        "intentional_session_method_collisions": len(duplicates),
        "runtime_module_count": len(RUNTIME_MODULES),
    })
    return {"version": "0.40.0", "error_count": len(errors), "errors": errors, "metrics": metrics}


MAINTENANCE_ARCHITECTURE_AUDIT_V0400 = maintenance_architecture_audit_v0400()
if MAINTENANCE_ARCHITECTURE_AUDIT_V0400["error_count"]:
    raise RuntimeError(
        "Maintenance Architecture Audit v0.40.0 failed: "
        + "; ".join(MAINTENANCE_ARCHITECTURE_AUDIT_V0400["errors"][:100])
    )
