# -*- coding: utf-8 -*-
"""Soulbound v0.50.0 - maintainable core baseline audit."""
from pathlib import Path

from core.runtime_manifest import (
    EXPLICIT_RUNTIME_EXPORTS,
    LEGACY_COMPATIBILITY_ALLOWLIST,
    LEGACY_IMPLICIT_DEPENDENCY_BUDGET,
    RUNTIME_MODULES,
)
from validation.maintainable_core import validate_maintainable_core


def maintainable_core_audit_v0500():
    root = Path(__file__).resolve().parents[1]
    result = validate_maintainable_core(
        root,
        RUNTIME_MODULES,
        EXPLICIT_RUNTIME_EXPORTS,
        LEGACY_COMPATIBILITY_ALLOWLIST,
        LEGACY_IMPLICIT_DEPENDENCY_BUDGET,
    )
    result["version"] = "0.50.0"
    return result


MAINTAINABLE_CORE_AUDIT_V0500 = maintainable_core_audit_v0500()
if MAINTAINABLE_CORE_AUDIT_V0500["error_count"]:
    raise RuntimeError(
        "Maintainable Core Audit v0.50.0 failed: "
        + "; ".join(MAINTAINABLE_CORE_AUDIT_V0500["errors"][:100])
    )
