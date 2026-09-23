# -*- coding: utf-8 -*-
"""Soulbound v0.44.0 - Explicit Gameplay Dependencies audit.

Second migration wave: reviewed gameplay/session modules no longer receive the
legacy compatibility namespace.  This audit proves that the migrated cohort
uses ordinary imports and that the measured compatibility debt only shrinks.
"""
from pathlib import Path

from core.runtime_manifest import (
    EXPLICIT_RUNTIME_EXPORTS,
    LEGACY_IMPLICIT_DEPENDENCY_BUDGET,
    RUNTIME_MODULES,
    V044_EXPLICIT_RUNTIME_EXPORTS,
)
from validation.dependencies import (
    legacy_dependency_metrics,
    validate_explicit_runtime_modules,
    validate_layer_imports,
)


def explicit_gameplay_dependencies_audit_v0440():
    root = Path(__file__).resolve().parents[1]
    errors = []

    explicit = validate_explicit_runtime_modules(
        root, EXPLICIT_RUNTIME_EXPORTS, RUNTIME_MODULES
    )
    errors.extend(explicit["errors"])

    layers = validate_layer_imports(root)
    errors.extend(layers["errors"])

    legacy = legacy_dependency_metrics(
        root, RUNTIME_MODULES, EXPLICIT_RUNTIME_EXPORTS
    )
    implicit_total = int(legacy["legacy_implicit_reference_total"])
    if implicit_total > int(LEGACY_IMPLICIT_DEPENDENCY_BUDGET):
        errors.append(
            "legacy implicit dependency budget exceeded: "
            f"{implicit_total} > {LEGACY_IMPLICIT_DEPENDENCY_BUDGET}"
        )

    expected_wave = 26
    if len(V044_EXPLICIT_RUNTIME_EXPORTS) != expected_wave:
        errors.append(
            f"v0.44 explicit migration cohort changed: "
            f"{len(V044_EXPLICIT_RUNTIME_EXPORTS)} != {expected_wave}"
        )
    if len(EXPLICIT_RUNTIME_EXPORTS) < 41:
        errors.append(
            f"explicit runtime module set unexpectedly small: "
            f"{len(EXPLICIT_RUNTIME_EXPORTS)}"
        )
    if implicit_total > 1553:
        errors.append(
            f"v0.44 migration target regressed: {implicit_total} > 1553"
        )

    return {
        "version": "0.44.0",
        "error_count": len(errors),
        "errors": errors,
        "explicit_module_count": len(EXPLICIT_RUNTIME_EXPORTS),
        "v044_migrated_module_count": len(V044_EXPLICIT_RUNTIME_EXPORTS),
        "v044_migrated_modules": tuple(V044_EXPLICIT_RUNTIME_EXPORTS),
        "legacy_compat_module_count": legacy["legacy_module_count"],
        "legacy_implicit_reference_total": implicit_total,
        "legacy_implicit_reference_budget": LEGACY_IMPLICIT_DEPENDENCY_BUDGET,
        "largest_legacy_dependency_users": legacy["largest"],
        "layer_import_errors": tuple(layers["errors"]),
    }


EXPLICIT_GAMEPLAY_DEPENDENCIES_AUDIT_V0440 = explicit_gameplay_dependencies_audit_v0440()
if EXPLICIT_GAMEPLAY_DEPENDENCIES_AUDIT_V0440["error_count"]:
    raise RuntimeError(
        "Explicit Gameplay Dependencies Audit v0.44.0 failed: "
        + "; ".join(EXPLICIT_GAMEPLAY_DEPENDENCIES_AUDIT_V0440["errors"][:100])
    )
