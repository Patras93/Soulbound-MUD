# -*- coding: utf-8 -*-
"""Soulbound v0.49.0 - authoritative Commands Registry audit."""
from __future__ import annotations

from pathlib import Path

from core.command_catalog import COMMAND_CATALOG, COMMAND_CATALOG_VERSION
from core.mines_threat import COMMAND_ALIASES
from core.runtime_manifest import RUNTIME_MODULES
from config.command_aliases import COMMAND_ALIAS_DEFINITIONS
from player.session import Session
from player.session_mixins.command_registry import COMMAND_REGISTRY
from validation.commands import validate_command_alias_ownership, validate_command_loop_architecture
from world.equipment_help import HELP_TOPICS, HELP_TOPIC_ALIASES


def command_registry_audit_v0490():
    root = Path(__file__).resolve().parents[1]
    errors = []

    COMMAND_CATALOG.bind_help(HELP_TOPICS, HELP_TOPIC_ALIASES)
    snapshot = COMMAND_CATALOG.snapshot()

    resolved_aliases = COMMAND_CATALOG.aliases()
    if dict(COMMAND_ALIASES) != resolved_aliases:
        errors.append("legacy COMMAND_ALIASES view differs from authoritative command catalog")

    conflicts = COMMAND_CATALOG.conflicts()
    if conflicts:
        errors.append(
            "command alias target conflicts: "
            + "; ".join(
                f"{row['alias']}:{row['old']}->{row['new']}" for row in conflicts[:20]
            )
        )

    alias_ownership = validate_command_alias_ownership(root, RUNTIME_MODULES)
    errors.extend(alias_ownership["errors"])
    if dict(COMMAND_ALIAS_DEFINITIONS) != resolved_aliases:
        errors.append("authoritative config/command_aliases.py differs from resolved alias catalog")

    alias_targets = set(resolved_aliases.values())
    registered = set(COMMAND_REGISTRY)
    missing_specs = sorted(alias_targets - registered)
    if missing_specs:
        errors.append("alias targets without registry handler: " + ", ".join(missing_specs[:50]))

    missing_methods = []
    for canonical, spec in COMMAND_REGISTRY.items():
        handler = spec[0]
        if not hasattr(Session, handler):
            missing_methods.append(f"{canonical}->{handler}")
    if missing_methods:
        errors.append("registered handlers missing on Session: " + ", ".join(missing_methods[:50]))

    definitions = snapshot["commands"]
    missing_metadata = sorted(
        canonical for canonical in registered
        if canonical not in definitions or definitions[canonical].get("handler") != COMMAND_REGISTRY[canonical][0]
    )
    if missing_metadata:
        errors.append("registry commands missing central metadata: " + ", ".join(missing_metadata[:50]))

    architecture = validate_command_loop_architecture(root)
    errors.extend(architecture["errors"])

    # These floors protect the broad public interface from accidental shrinkage.
    if len(resolved_aliases) < 800:
        errors.append(f"command alias surface unexpectedly small: {len(resolved_aliases)}")
    if len(COMMAND_REGISTRY) < 250:
        errors.append(f"registered command surface unexpectedly small: {len(COMMAND_REGISTRY)}")
    if snapshot["help_bound_count"] < 100:
        errors.append(f"too few commands linked to HELP topics: {snapshot['help_bound_count']}")

    return {
        "version": "0.49.0",
        "catalog_version": COMMAND_CATALOG_VERSION,
        "error_count": len(errors),
        "errors": errors,
        "alias_count": len(resolved_aliases),
        "alias_target_count": len(alias_targets),
        "registered_command_count": len(COMMAND_REGISTRY),
        "registered_handler_count": snapshot["handler_count"],
        "help_bound_count": snapshot["help_bound_count"],
        "alias_conflict_count": snapshot["alias_conflict_count"],
        "unexpected_alias_conflict_count": len(conflicts),
        "runtime_alias_mutation_count": alias_ownership["alias_mutation_count"],
        "alias_definition_count": len(COMMAND_ALIAS_DEFINITIONS),
        "missing_handler_count": len(missing_methods),
        "manual_command_branch_count": architecture["manual_command_branch_count"],
        "command_loop_lines": architecture["command_loop_lines"],
    }


COMMAND_REGISTRY_AUDIT_V0490 = command_registry_audit_v0490()
if COMMAND_REGISTRY_AUDIT_V0490["error_count"]:
    raise RuntimeError(
        "Command Registry Audit v0.49.0 failed: "
        + "; ".join(COMMAND_REGISTRY_AUDIT_V0490["errors"][:100])
    )
