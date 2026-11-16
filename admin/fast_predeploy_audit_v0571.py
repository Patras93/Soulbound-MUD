# -*- coding: utf-8 -*-
"""Soulbound v0.61.0 - fast Railway predeploy audit.

This audit intentionally does not assemble the whole gameplay runtime.  It
checks the deployment-critical surface that can make Railway fail before the
server becomes usable: Docker packaging, runtime manifest completeness,
Python syntax, critical imports, command catalog shape and SQLite bootstrap
schema.  The exhaustive historical gate remains available in predeploy_full.py.
"""
from __future__ import annotations

import ast
import importlib
import io
import sqlite3
import tokenize
import tempfile
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
from core.source_contracts import read_actual_refactored_source_v4200 as _sb420_read

REQUIRED_RUNTIME_PACKAGES = (
    "core", "systems", "world", "network", "storage", "player", "server", "admin",
    "config", "data", "events", "validation",
)
ESSENTIAL_TABLES = {
    "accounts", "characters", "inventory", "equipment", "professions", "tools",
    "quests", "achievements", "player_clans", "postal_delivery_state_v0522",
    "courier_guild_state_v0530", "activity_journal_v0560", "crafting_orders_v0600",
    "ocean_ship_v1000", "ocean_treasure_map_v1000", "ocean_trade_contract_v1000",
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



def _current_profession_help_contract_errors_v11320(help_source: str, truth_source: str) -> list[str]:
    """Check active dynamic profession HELP without requiring old 14-tool prose.

    Pure source contract: safe in the fast audit without bootstrapping the full
    game. The full runtime/atlas HELP is additionally exercised by the existing
    current_help_atlas_regression and universal tests.
    """
    contracts = (
        ("active HELP catalogue binding", "HELP_TOPICS = _current_help_catalogs()[0]", help_source),
        ("active HELP dispatcher", "async def show_help(", help_source),
        ("dynamic profession registry", "profession_count = len(set(TOOL_PROFESSION_MAP.values()))", truth_source),
        ("dynamic profession HELP count", 'f"Soulbound ma {profession_count} profesji', truth_source),
        ("current profession topic", 'HELP_TOPICS["profesje"]', truth_source),
        ("Archeologia and Kartografia in public HELP", "Eksploracja: Archeologia i Kartografia.", truth_source),
        ("Archeologia HELP topic", 'HELP_TOPICS["archeologia"]', truth_source),
        ("Kartografia HELP topic", 'HELP_TOPICS["kartografia"]', truth_source),
        ("final HELP binding to registry", "COMMAND_CATALOG.bind_help(HELP_TOPICS, HELP_TOPIC_ALIASES)", truth_source),
    )
    return [f"current profession HELP contract missing: {label}"
            for label, token, source in contracts if token not in source]

def fast_predeploy_audit_v0571():
    errors: list[str] = []
    warnings: list[str] = []

    # 1. Runtime/Docker packaging.  This protects the v0.52.1 Railway regression.
    docker_path = ROOT / "Dockerfile"
    docker = docker_path.read_text(encoding="utf-8", errors="replace") if docker_path.is_file() else ""
    if not docker:
        errors.append("Dockerfile missing")
    current_copy = "COPY . /candidate" in docker
    if "COPY server.py /app/server.py" not in docker and not current_copy:
        errors.append("Dockerfile does not copy server.py")
    if 'CMD ["python", "-u", "/app/server.py"]' not in docker:
        errors.append("Dockerfile CMD does not start /app/server.py with unbuffered Python")
    if "COPY predeploy_check.py /app/predeploy_check.py" not in docker and not current_copy:
        errors.append("Dockerfile does not copy the fast predeploy gate")
    if ("RUN python /app/predeploy_check.py" not in docker
            and "RUN python -m systems.current_install install --target /app" not in docker):
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
        if expected not in docker and not current_copy:
            errors.append(f"Dockerfile missing: {expected}")

    # 2. Explicit runtime manifest: every declared file must exist and compile.
    try:
        from core.runtime_manifest import (
            RUNTIME_MODULES, FULL_RUNTIME_MODULES, EXPECTED_OVERRIDE_ORDER,
        )
    except Exception as exc:  # pragma: no cover - fatal deployment guard
        RUNTIME_MODULES = []
        FULL_RUNTIME_MODULES = []
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

    # 2c. Verify *every* Python source without re-reading/re-parsing the same
    # tree in three independent sweeps. No result is cached between runs:
    # this pass scans each file from the current candidate on every PREDEPLOY.
    # Store only one AST at a time, avoiding excessive Windows memory use.
    all_python_files = sorted(
        path for path in ROOT.rglob("*.py")
        if "__pycache__" not in path.parts
    )
    all_source_syntax_errors = []
    duplicate_literal_keys = []
    swallowed_exception_sites = []
    intentional_swallowed_exception_sites = []
    todo_sites = []
    runtime_module_symbols: dict[str, list[str]] = {}
    runtime_rel_names = set(RUNTIME_MODULES)
    for path in all_python_files:
        rel = path.relative_to(ROOT).as_posix()
        source = path.read_text(encoding="utf-8")
        try:
            # CPython compilation also detects invalid control flow which
            # ast.parse alone does not catch (e.g. a top-level 'return').
            compile(source, str(path), "exec")
        except Exception as exc:
            all_source_syntax_errors.append(
                f"{rel}: {type(exc).__name__}: {exc}"
            )
        try:
            tree = ast.parse(source, filename=str(path))
        except Exception:
            tree = None  # Syntax failure was already reported above.
        if tree is not None:
            # Identical top-level override-order check, but reuse this AST.
            if rel in runtime_rel_names:
                runtime_module_symbols[rel] = [
                    node.name for node in tree.body
                    if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
                ]
            source_lines = None
            for node in ast.walk(tree):
                if isinstance(node, ast.Dict):
                    seen_keys = set()
                    for key in node.keys:
                        if isinstance(key, ast.Constant) and isinstance(key.value, (str, int, float, bytes)):
                            marker = (type(key.value).__name__, key.value)
                            if marker in seen_keys:
                                duplicate_literal_keys.append(f"{rel}:{getattr(key, 'lineno', '?')}: {key.value!r}")
                            seen_keys.add(marker)
                if isinstance(node, ast.ExceptHandler):
                    body = list(node.body or ())
                    if len(body) == 1 and isinstance(body[0], ast.Pass):
                        exc_name = "bare except"
                        if node.type is not None:
                            try:
                                exc_name = ast.unparse(node.type)
                            except Exception:
                                exc_name = "except"
                        site = f"{rel}:{getattr(node, 'lineno', '?')}: {exc_name}: pass"
                        if source_lines is None:
                            source_lines = source.splitlines()
                        handler_line = source_lines[max(0, int(getattr(node, "lineno", 1)) - 1)]
                        if "AUDIT_INTENTIONAL_PASS" in handler_line:
                            intentional_swallowed_exception_sites.append(site)
                        else:
                            swallowed_exception_sites.append(site)
        # Scanning every token in 1800 files is expensive (millions of tokens).
        # A case-insensitive substring filter cannot miss these markers;
        # tokenize matching sources to distinguish comments from strings.
        # to reject mentions in strings and match comments precisely.
        upper_source = source.upper()
        if "TODO" in upper_source or "FIXME" in upper_source:
            try:
                for token in tokenize.generate_tokens(io.StringIO(source).readline):
                    if token.type != tokenize.COMMENT:
                        continue
                    upper = token.string.upper()
                    if "TODO" in upper or "FIXME" in upper:
                        todo_sites.append(f"{rel}:{token.start[0]}: {token.string.strip()}")
            except (tokenize.TokenError, IndentationError):  # AUDIT_INTENTIONAL_PASS: syntax failures are reported separately
                pass
    errors.extend(
        f"Repository Python syntax failure: {item}"
        for item in all_source_syntax_errors
    )
    for item in duplicate_literal_keys:
        warnings.append(f"duplicate literal dict key: {item}")
    for item in swallowed_exception_sites[:200]:
        warnings.append(f"swallowed exception: {item}")
    for item in todo_sites[:200]:
        warnings.append(f"source TODO/FIXME: {item}")

    # 2a. Assemble symbols in manifest order, not sorted filename order.
    # This preserves the exact override semantics of the original audit.
    symbol_owners: dict[str, list[str]] = {}
    for rel in RUNTIME_MODULES:
        for symbol in runtime_module_symbols.get(rel, ()):
            symbol_owners.setdefault(symbol, []).append(rel)
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
        late_creator = "world/runtime_gameplay_finalize.py"
        if finalizer not in RUNTIME_MODULES:
            errors.append("living NPC late finalizer missing from production runtime manifest")
        if late_creator not in RUNTIME_MODULES:
            errors.append("world/runtime_gameplay_finalize.py functional late NPC creator missing from production runtime")
        elif finalizer in RUNTIME_MODULES and RUNTIME_MODULES.index(finalizer) < RUNTIME_MODULES.index(late_creator):
            errors.append("living NPC late finalizer runs before world/runtime_gameplay_finalize.py late NPC creation")
        if living_audit not in FULL_RUNTIME_MODULES:
            errors.append("living NPC coverage audit missing from full predeploy manifest")
        elif finalizer in FULL_RUNTIME_MODULES and FULL_RUNTIME_MODULES.index(finalizer) > FULL_RUNTIME_MODULES.index(living_audit):
            errors.append("living NPC late finalizer runs after the full-predeploy coverage audit")
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

    # 5a. v1.10.6 cross-feature regression guards for 14 professions and quest rewards.
    try:
        orders_source = (ROOT / "player" / "session_mixins" / "crafting_orders.py").read_text(encoding="utf-8")
        for token in (
            '"specialist_archaeology"',
            '"specialist_cartography"',
            '"tool_type": "archaeology"',
            '"tool_type": "cartography_profession"',
        ):
            if token not in orders_source:
                errors.append(f"14-profession rotating order contract missing: {token}")

        exploration_source = (ROOT / "player" / "session_mixins" / "exploration_professions.py").read_text(encoding="utf-8")
        for token in (
            'announce_profession_action_order_progress_v0713("archaeology", 1)',
            'announce_profession_action_order_progress_v0713("cartography_profession", 1)',
        ):
            if token not in exploration_source:
                errors.append(f"exploration order progress hook missing: {token}")

        quest_commands_source = (ROOT / "player" / "session_mixins" / "quest_commands.py").read_text(encoding="utf-8")
        if "validate_quest_rewards_v1106" not in quest_commands_source:
            errors.append("quest reward preflight missing")
        if 'q["reward_items"]' in quest_commands_source:
            errors.append("unsafe direct q[reward_items] access remains in quest completion")

        gathering_source = _sb420_read(ROOT / "player/session_mixins/gathering.py")
        for token in (
            '"tailoring": ("tailor_kit", "Zestaw Krawiecki")',
            '"leatherworking": ("tanning_knife", "Nóż Garbarski")',
            '"carpentry": ("carpenter_tools", "Narzędzia Ciesielskie")',
            '"enchanting": ("runic_focus", "Fokus Runiczny")',
            '"archaeology": ("archaeology_brush", "Pędzel Archeologa")',
            '"cartography_profession": ("surveyor_compass", "Kompas Mierniczy")',
        ):
            if token not in gathering_source:
                errors.append(f"14-tool info definition missing: {token}")
        if '"Archeolożka Mira"' in gathering_source:
            errors.append("stale Archaeologist Mira remains in active tool UI")
        if '"Archeolożka Elara"' not in gathering_source:
            errors.append("Archaeologist Elara missing from active tool UI")

        registry_source = (ROOT / "player" / "session_mixins" / "command_registry.py").read_text(encoding="utf-8")
        for command in (
            "toolinfo_tailoring", "toolinfo_leatherworking",
            "toolinfo_carpentry", "toolinfo_enchanting",
            "toolinfo_archaeology", "toolinfo_cartography",
        ):
            if f"'{command}'" not in registry_source:
                errors.append(f"profession tool info command missing: {command}")

        completion_source = (ROOT / "player" / "session_mixins" / "progression_accessibility.py").read_text(encoding="utf-8")
        if "len(PROFESSIONS_V0580)*PROFESSION_MAX_LEVEL" not in completion_source:
            errors.append("completion profession denominator is not fixed to all 14 professions")

        # Current public HELP is assembled from the live profession registry.
        # The historical v1.10.6 guard expected literal "14 tools" phrases in
        # help_system.py. That text was removed correctly when the catalog grew.
        # Verify the actual contemporary binding, dynamic count and both
        # exploration professions instead of requiring obsolete player text.
        help_source = (ROOT / "player" / "session_mixins" / "help_system.py").read_text(encoding="utf-8")
        truth_source = (ROOT / "admin" / "help_truth_current.py").read_text(encoding="utf-8")
        errors.extend(_current_profession_help_contract_errors_v11320(help_source, truth_source))

        progress_source = (ROOT / "player" / "session_mixins" / "progress_titles.py").read_text(encoding="utf-8")
        if "COURIER_REPUTATION_MAX_V0530" not in progress_source:
            errors.append("progress summary does not use current Courier reputation cap")
        if 'Reputacja Kurierów: {courier_rep}/400' in progress_source:
            errors.append("stale Courier /400 cap remains in current progress summary")
    except Exception as exc:
        errors.append(f"v1.10.6 regression guard failed: {type(exc).__name__}: {exc}")

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
        "version": "0.61.0",
        "runtime_module_count": len(RUNTIME_MODULES),
        "missing_runtime_packages": missing_packages,
        "missing_docker_copy_sources": missing_docker_copy_sources,
        "missing_manifest_files": missing_manifest_files,
        "duplicate_manifest_files": duplicate_manifest_files,
        "syntax_error_count": len(syntax_errors),
        "all_python_source_count": len(all_python_files),
        "all_source_syntax_error_count": len(all_source_syntax_errors),
        "duplicate_literal_key_count": len(duplicate_literal_keys),
        "swallowed_exception_count": len(swallowed_exception_sites),
        "swallowed_exception_sites": tuple(swallowed_exception_sites),
        "intentional_swallowed_exception_count": len(intentional_swallowed_exception_sites),
        "intentional_swallowed_exception_sites": tuple(intentional_swallowed_exception_sites),
        "todo_fixme_count": len(todo_sites),
        "todo_sites": tuple(todo_sites),
        "unexpected_symbol_overrides": unexpected_symbol_overrides,
        "expected_override_order_mismatches": expected_order_mismatches,
        "critical_import_ok": critical_import_ok,
        "schema_object_count": schema_object_count,
        "schema_table_count": len(schema_tables),
        "alias_count": alias_count,
        "registered_command_count": registry_count,
        "error_count": len(errors),
        "errors": errors,
        "warning_count": len(warnings),
        "warnings": warnings,
    }


FAST_PREDEPLOY_AUDIT_V0571 = fast_predeploy_audit_v0571()

__all__ = ["fast_predeploy_audit_v0571", "FAST_PREDEPLOY_AUDIT_V0571"]
