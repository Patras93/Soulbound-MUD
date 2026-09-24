# -*- coding: utf-8 -*-
"""Soulbound v0.60.1 - fast Railway predeploy audit.

This audit intentionally does not assemble the whole gameplay runtime.  It
checks the deployment-critical surface that can make Railway fail before the
server becomes usable: Docker packaging, runtime manifest completeness,
Python syntax, critical imports, command catalog shape and SQLite bootstrap
schema.  The exhaustive historical gate remains available in predeploy_full.py.
"""
from __future__ import annotations

import ast
import importlib
import sqlite3
import tempfile
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
REQUIRED_RUNTIME_PACKAGES = (
    "core", "systems", "world", "network", "storage", "player", "server", "admin",
    "config", "data", "events", "validation",
)
ESSENTIAL_TABLES = {
    "accounts", "characters", "inventory", "equipment", "professions", "tools",
    "quests", "achievements", "player_clans", "postal_delivery_state_v0522",
    "courier_guild_state_v0530", "activity_journal_v0560", "crafting_orders_v0600",
}


def _assignment_dict_key_count(path: Path, variable: str) -> int:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(isinstance(target, ast.Name) and target.id == variable for target in node.targets):
            continue
        if isinstance(node.value, ast.Dict):
            keys = [key for key in node.value.keys if isinstance(key, ast.Constant) and isinstance(key.value, str)]
            return len(keys)
    return 0


def fast_predeploy_audit_v0571():
    errors: list[str] = []

    # 1. Runtime/Docker packaging.  This protects the v0.52.1 Railway regression.
    docker_path = ROOT / "Dockerfile"
    docker = docker_path.read_text(encoding="utf-8", errors="replace") if docker_path.is_file() else ""
    if not docker:
        errors.append("Dockerfile missing")
    if "COPY server.py /app/server.py" not in docker:
        errors.append("Dockerfile does not copy server.py")
    if 'CMD ["python", "-u", "/app/server.py"]' not in docker:
        errors.append("Dockerfile CMD does not start /app/server.py with unbuffered Python")
    if "COPY predeploy_check.py /app/predeploy_check.py" not in docker:
        errors.append("Dockerfile does not copy the fast predeploy gate")
    if "RUN python /app/predeploy_check.py" not in docker:
        errors.append("Dockerfile does not execute the fast predeploy gate during build")

    missing_docker_copy_sources = []
    for raw_line in docker.splitlines():
        line = raw_line.strip()
        if not line.upper().startswith("COPY "):
            continue
        parts = line.split()
        # Current Soulbound Dockerfile uses the plain `COPY src /app/dst` form.
        # Skip option-based/stage copies instead of guessing their build context.
        if len(parts) < 3 or any(part.startswith("--") for part in parts[1:-1]):
            continue
        for source in parts[1:-1]:
            if any(ch in source for ch in "*?["):
                continue
            if not (ROOT / source).exists():
                missing_docker_copy_sources.append(source)
                errors.append(f"Dockerfile COPY source missing from release root: {source}")

    missing_packages = []
    for package in REQUIRED_RUNTIME_PACKAGES:
        if not (ROOT / package).is_dir():
            missing_packages.append(package)
            errors.append(f"missing runtime package directory: {package}/")
        expected = f"COPY {package} /app/{package}"
        if expected not in docker:
            errors.append(f"Dockerfile missing: {expected}")

    # 2. Explicit runtime manifest: every declared file must exist and compile.
    try:
        from core.runtime_manifest import RUNTIME_MODULES, EXPECTED_OVERRIDE_ORDER
    except Exception as exc:  # pragma: no cover - fatal deployment guard
        RUNTIME_MODULES = []
        errors.append(f"runtime manifest import failed: {type(exc).__name__}: {exc}")

    missing_manifest_files = []
    syntax_errors = []
    seen = set()
    duplicate_manifest_files = []
    for rel in RUNTIME_MODULES:
        if rel in seen:
            duplicate_manifest_files.append(rel)
        seen.add(rel)
        path = ROOT / rel
        if not path.is_file():
            missing_manifest_files.append(rel)
            continue
        try:
            compile(path.read_text(encoding="utf-8"), str(path), "exec")
        except Exception as exc:
            syntax_errors.append(f"{rel}: {type(exc).__name__}: {exc}")

    if not (ROOT / "server.py").is_file():
        missing_manifest_files.append("server.py")
    else:
        try:
            compile((ROOT / "server.py").read_text(encoding="utf-8"), str(ROOT / "server.py"), "exec")
        except Exception as exc:
            syntax_errors.append(f"server.py: {type(exc).__name__}: {exc}")

    for rel in missing_manifest_files:
        errors.append(f"runtime manifest file missing: {rel}")
    for rel in duplicate_manifest_files:
        errors.append(f"runtime manifest duplicate: {rel}")
    errors.extend(f"Python syntax failure: {item}" for item in syntax_errors)

    # 2a. Mirror native_runtime's top-level symbol ownership guard without
    # executing the full world. This catches deployment crashes such as v0.58.2
    # defining the same helper function name in two audit modules.
    symbol_owners: dict[str, list[str]] = {}
    for rel in RUNTIME_MODULES:
        path = ROOT / rel
        if not path.is_file():
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        except Exception:
            continue  # syntax failure is already reported above
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                symbol_owners.setdefault(node.name, []).append(rel)

    unexpected_symbol_overrides = []
    expected_order_mismatches = []
    for symbol, owners in sorted(symbol_owners.items()):
        if len(owners) < 2:
            continue
        expected = list(EXPECTED_OVERRIDE_ORDER.get(symbol, ()))
        if not expected:
            unexpected_symbol_overrides.append(f"{symbol}: {' -> '.join(owners)}")
        elif owners != expected:
            expected_order_mismatches.append(
                f"{symbol}: observed {' -> '.join(owners)}; expected {' -> '.join(expected)}"
            )
    for item in unexpected_symbol_overrides:
        errors.append(f"unexpected runtime symbol override: {item}")
    for item in expected_order_mismatches:
        errors.append(f"runtime override order mismatch: {item}")


    # 2b. Late living-NPC reconciliation must run after late NPC creators and
    # before the v0.56.0 coverage audit. This protects the Railway regression
    # fixed in v0.58.2, where class EQ shopkeepers were added after the first
    # living-NPC pass.
    try:
        finalizer = "world/living_npcs_finalize.py"
        living_audit = "admin/living_npcs_activity_audit_v0560.py"
        late_creator = "admin/audits.py"
        if finalizer not in RUNTIME_MODULES:
            errors.append("living NPC late finalizer missing from runtime manifest")
        elif living_audit not in RUNTIME_MODULES:
            errors.append("living NPC coverage audit missing from runtime manifest")
        elif RUNTIME_MODULES.index(finalizer) > RUNTIME_MODULES.index(living_audit):
            errors.append("living NPC late finalizer runs after the coverage audit")
        if finalizer in RUNTIME_MODULES and late_creator in RUNTIME_MODULES and RUNTIME_MODULES.index(finalizer) < RUNTIME_MODULES.index(late_creator):
            errors.append("living NPC late finalizer runs before admin/audits.py late NPC creation")
    except Exception as exc:
        errors.append(f"living NPC runtime-order check failed: {type(exc).__name__}: {exc}")

    # 3. Critical import that caused the real Railway crash in v0.52.0.
    critical_import_ok = False
    try:
        balance = importlib.import_module("config.balance")
        getattr(balance, "BLACKSMITH_QUEST_COOLDOWN_SECONDS")
        getattr(balance, "QUEST_REPEAT_COOLDOWN_SECONDS")
        critical_import_ok = True
    except Exception as exc:
        errors.append(f"critical config.balance import failed: {type(exc).__name__}: {exc}")

    # 4. Fast SQLite smoke test using focused schema modules only.  No world/runtime load.
    schema_tables: set[str] = set()
    schema_object_count = 0
    try:
        from storage.schema_core import create_core_schema
        from storage.schema_progression import create_progression_schema
        from storage.schema_world_quests import create_world_quests_schema
        from storage.schema_social_guilds import create_social_guilds_schema
        from storage.schema_migrate_social import migrate_social_courier_schema

        with tempfile.TemporaryDirectory(prefix="soulbound-fast-predeploy-") as tmp:
            conn = sqlite3.connect(str(Path(tmp) / "smoke.db"))
            holder = SimpleNamespace(conn=conn)
            create_core_schema(holder)
            create_progression_schema(holder)
            create_world_quests_schema(holder)
            create_social_guilds_schema(holder)
            migrate_social_courier_schema(holder)
            conn.commit()
            rows = conn.execute("SELECT type,name FROM sqlite_master WHERE name NOT LIKE 'sqlite_%'").fetchall()
            schema_object_count = len(rows)
            schema_tables = {name for kind, name in rows if kind == "table"}
            conn.close()
        missing_tables = sorted(ESSENTIAL_TABLES - schema_tables)
        for table in missing_tables:
            errors.append(f"fast schema smoke missing table: {table}")
    except Exception as exc:
        errors.append(f"fast SQLite bootstrap failed: {type(exc).__name__}: {exc}")

    # 5. Static command/alias sanity without importing the legacy world runtime.
    alias_count = 0
    registry_count = 0
    try:
        alias_count = _assignment_dict_key_count(ROOT / "config/command_aliases.py", "COMMAND_ALIAS_DEFINITIONS")
        registry_count = _assignment_dict_key_count(ROOT / "player/session_mixins/command_registry.py", "COMMAND_REGISTRY")
        if alias_count < 800:
            errors.append(f"command alias catalog unexpectedly small: {alias_count}")
        if registry_count < 220:
            errors.append(f"command registry unexpectedly small: {registry_count}")
    except Exception as exc:
        errors.append(f"command catalog static check failed: {type(exc).__name__}: {exc}")

    # 6. Bootstrap contract: Railway port is opened before the heavy runtime loader.
    try:
        server_source = (ROOT / "server.py").read_text(encoding="utf-8")
        listen_pos = server_source.find("_BOOT_SOCKET.listen")
        runtime_pos = server_source.find("load_native_runtime(_ROOT, globals())")
        if listen_pos < 0 or runtime_pos < 0 or listen_pos > runtime_pos:
            errors.append("server.py no longer opens bootstrap socket before loading the runtime")
        for token in ("RAILWAY_TCP_APPLICATION_PORT", '"PORT"', "SOULBOUND_PORT"):
            if token not in server_source:
                errors.append(f"server.py missing port bootstrap token: {token}")
    except Exception as exc:
        errors.append(f"server bootstrap contract check failed: {type(exc).__name__}: {exc}")

    return {
        "version": "0.60.1",
        "runtime_module_count": len(RUNTIME_MODULES),
        "missing_runtime_packages": missing_packages,
        "missing_docker_copy_sources": missing_docker_copy_sources,
        "missing_manifest_files": missing_manifest_files,
        "duplicate_manifest_files": duplicate_manifest_files,
        "syntax_error_count": len(syntax_errors),
        "unexpected_symbol_overrides": unexpected_symbol_overrides,
        "expected_override_order_mismatches": expected_order_mismatches,
        "critical_import_ok": critical_import_ok,
        "schema_object_count": schema_object_count,
        "schema_table_count": len(schema_tables),
        "alias_count": alias_count,
        "registered_command_count": registry_count,
        "error_count": len(errors),
        "errors": errors,
    }


FAST_PREDEPLOY_AUDIT_V0571 = fast_predeploy_audit_v0571()

__all__ = ["fast_predeploy_audit_v0571", "FAST_PREDEPLOY_AUDIT_V0571"]
