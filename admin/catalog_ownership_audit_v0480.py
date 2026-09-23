# -*- coding: utf-8 -*-
"""Soulbound v0.48.0 - controlled world/data ownership audit."""
from __future__ import annotations

from pathlib import Path

from core.runtime_manifest import (
    EXPLICIT_RUNTIME_EXPORTS,
    LEGACY_IMPLICIT_DEPENDENCY_BUDGET,
    RUNTIME_MODULES,
)
from data.catalog_mutations import KNOWN_CATALOGS, catalog_mutation_summary
from validation.catalog_ownership import validate_runtime_catalog_ownership
from validation.dependencies import legacy_dependency_metrics


def catalog_ownership_audit_v0480():
    root = Path(__file__).resolve().parents[1]
    errors = []

    ownership = validate_runtime_catalog_ownership(root, RUNTIME_MODULES)
    errors.extend(ownership["errors"])

    summary = catalog_mutation_summary()
    touched = set(summary.get("by_catalog", {}))
    missing_catalogs = sorted(set(KNOWN_CATALOGS) - touched)
    if missing_catalogs:
        errors.append("catalog mutation provenance missing catalogs: " + ", ".join(missing_catalogs))

    mutation_count = int(summary.get("mutation_count", 0) or 0)
    tracked_key_count = int(summary.get("tracked_key_count", 0) or 0)
    if mutation_count < 1000:
        errors.append(f"catalog provenance unexpectedly small: mutations={mutation_count}")
    if tracked_key_count < 1000:
        errors.append(f"catalog provenance tracks too few keys: {tracked_key_count}")

    metrics = legacy_dependency_metrics(root, RUNTIME_MODULES, EXPLICIT_RUNTIME_EXPORTS)
    implicit_total = int(metrics["legacy_implicit_reference_total"])
    if implicit_total != int(LEGACY_IMPLICIT_DEPENDENCY_BUDGET):
        errors.append(
            f"legacy implicit dependency budget mismatch: {implicit_total} != {LEGACY_IMPLICIT_DEPENDENCY_BUDGET}"
        )

    return {
        "version": "0.48.0",
        "error_count": len(errors),
        "errors": errors,
        "raw_direct_catalog_writes": int(ownership["violation_count"]),
        "raw_direct_catalog_write_modules": int(ownership["violating_module_count"]),
        "controlled_mutation_count": mutation_count,
        "tracked_key_count": tracked_key_count,
        "catalogs_with_provenance": tuple(sorted(touched)),
        "legacy_implicit_reference_total": implicit_total,
    }


CATALOG_OWNERSHIP_AUDIT_V0480 = catalog_ownership_audit_v0480()
if CATALOG_OWNERSHIP_AUDIT_V0480["error_count"]:
    raise RuntimeError(
        "Catalog Ownership Audit v0.48.0 failed: "
        + "; ".join(CATALOG_OWNERSHIP_AUDIT_V0480["errors"][:100])
    )
