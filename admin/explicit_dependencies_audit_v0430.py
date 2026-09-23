# -*- coding: utf-8 -*-
"""Soulbound v0.43.0 - Explicit Dependencies Architecture audit.

This milestone does not alter gameplay.  It makes the migration away from the
historical shared-global runtime measurable and enforceable.
"""
from pathlib import Path

from core.runtime_manifest import (
    EXPLICIT_RUNTIME_EXPORTS,
    LEGACY_IMPLICIT_DEPENDENCY_BUDGET,
    RUNTIME_MODULES,
)
from validation.dependencies import (
    legacy_dependency_metrics,
    validate_explicit_runtime_modules,
    validate_layer_imports,
)


def explicit_dependencies_audit_v0430():
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

    # v0.43.0 starts by removing the assembly/facade layer from symbol sync.
    if len(EXPLICIT_RUNTIME_EXPORTS) < 14:
        errors.append(
            f"explicit runtime module set unexpectedly small: {len(EXPLICIT_RUNTIME_EXPORTS)}"
        )

    return {
        "version": "0.43.0",
        "error_count": len(errors),
        "errors": errors,
        "explicit_module_count": len(EXPLICIT_RUNTIME_EXPORTS),
        "explicit_modules": tuple(EXPLICIT_RUNTIME_EXPORTS),
        "legacy_compat_module_count": legacy["legacy_module_count"],
        "legacy_implicit_reference_total": implicit_total,
        "legacy_implicit_reference_budget": LEGACY_IMPLICIT_DEPENDENCY_BUDGET,
        "largest_legacy_dependency_users": legacy["largest"],
        "layer_import_errors": tuple(layers["errors"]),
    }


EXPLICIT_DEPENDENCIES_AUDIT_V0430 = explicit_dependencies_audit_v0430()
if EXPLICIT_DEPENDENCIES_AUDIT_V0430["error_count"]:
    raise RuntimeError(
        "Explicit Dependencies Audit v0.43.0 failed: "
        + "; ".join(EXPLICIT_DEPENDENCIES_AUDIT_V0430["errors"][:100])
    )
