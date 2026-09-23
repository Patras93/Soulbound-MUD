# -*- coding: utf-8 -*-
"""v0.50.0 maintainable-core architecture guards."""
from __future__ import annotations

import re
from pathlib import Path

from config.legacy_provenance import ACTIVE_MODULE_PROVENANCE
from validation.dependencies import legacy_dependency_metrics

_VERSIONED_FILE = re.compile(r"_v\d+(?:_\d+)?\.py$", re.IGNORECASE)


def _is_history_audit(path: str) -> bool:
    name = Path(path).name.lower()
    return "audit" in name or name.startswith("release_integrity_")


def validate_maintainable_core(root, runtime_modules, explicit_exports, legacy_allowlist, dependency_budget):
    root = Path(root)
    errors = []

    runtime = tuple(runtime_modules)
    runtime_set = set(runtime)
    explicit = set(explicit_exports)
    observed_legacy = tuple(path for path in runtime if path not in explicit)
    allowed_legacy = tuple(legacy_allowlist)

    if observed_legacy != allowed_legacy:
        missing = [p for p in observed_legacy if p not in allowed_legacy]
        stale = [p for p in allowed_legacy if p not in observed_legacy]
        if missing:
            errors.append("new/unreviewed legacy compatibility modules: " + ", ".join(missing))
        if stale:
            errors.append("stale legacy compatibility allowlist entries: " + ", ".join(stale))

    versioned_gameplay = [
        path for path in runtime
        if _VERSIONED_FILE.search(path) and not _is_history_audit(path)
    ]
    if versioned_gameplay:
        errors.append("active gameplay filenames still contain milestone suffixes: " + ", ".join(versioned_gameplay))

    missing_provenance = [path for path in ACTIVE_MODULE_PROVENANCE if path not in runtime_set]
    if missing_provenance:
        errors.append("provenance entries missing from runtime: " + ", ".join(missing_provenance))
    missing_files = [path for path in ACTIVE_MODULE_PROVENANCE if not (root / path).is_file()]
    if missing_files:
        errors.append("provenance paths missing on disk: " + ", ".join(missing_files))

    stale_versioned_files = []
    for path in ACTIVE_MODULE_PROVENANCE:
        parent = (root / path).parent
        stem = Path(path).stem
        for candidate in parent.glob(stem + "_v*.py"):
            stale_versioned_files.append(str(candidate.relative_to(root)))
    if stale_versioned_files:
        errors.append("stale version-suffixed gameplay files remain: " + ", ".join(sorted(stale_versioned_files)))

    metrics = legacy_dependency_metrics(root, runtime, explicit_exports)
    debt = int(metrics["legacy_implicit_reference_total"])
    if debt > int(dependency_budget):
        errors.append(f"legacy dependency debt grew: {debt} > budget {dependency_budget}")

    return {
        "error_count": len(errors),
        "errors": errors,
        "runtime_module_count": len(runtime),
        "explicit_module_count": len(explicit),
        "legacy_module_count": len(observed_legacy),
        "legacy_implicit_reference_total": debt,
        "legacy_dependency_budget": int(dependency_budget),
        "functional_provenance_count": len(ACTIVE_MODULE_PROVENANCE),
        "versioned_gameplay_filename_count": len(versioned_gameplay),
        "stale_versioned_gameplay_file_count": len(stale_versioned_files),
    }
