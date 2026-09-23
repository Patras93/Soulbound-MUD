# -*- coding: utf-8 -*-
"""Soulbound v0.47.0 - focused explicit combat architecture audit."""
from __future__ import annotations

import ast
from pathlib import Path

from core.runtime_manifest import (
    EXPLICIT_RUNTIME_EXPORTS,
    LEGACY_IMPLICIT_DEPENDENCY_BUDGET,
    RUNTIME_MODULES,
    V047_EXPLICIT_RUNTIME_EXPORTS,
)
from validation.dependencies import (
    implicit_global_references,
    legacy_dependency_metrics,
    validate_explicit_runtime_modules,
)

_COMBAT_METHODS = {
    "player/session_mixins/combat_skills.py": ("use_class_skill",),
    "player/session_mixins/combat_damage.py": (
        "player_damage", "consider_player_expected_hit", "consider_enemy_expected_hit",
        "consider_rating", "consider_mob",
    ),
    "player/session_mixins/combat_realtime.py": (
        "stop_realtime_combat", "ensure_realtime_combat", "grant_soul_weapon_mastery_hit_xp",
        "realtime_player_action", "realtime_combat_loop", "attack",
    ),
    "player/session_mixins/combat_rewards.py": (
        "class_for_milestone_loot", "grant_milestone_boss_loot", "mob_defeated",
    ),
    "player/session_mixins/combat_survival.py": ("flee", "die"),
}


def _class_methods(path: Path) -> tuple[str, ...]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    names = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            names.extend(
                child.name for child in node.body
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
            )
    return tuple(names)


def combat_architecture_audit_v0470():
    root = Path(__file__).resolve().parents[1]
    errors = []

    explicit = validate_explicit_runtime_modules(root, EXPLICIT_RUNTIME_EXPORTS, RUNTIME_MODULES)
    errors.extend(explicit["errors"])

    expected_explicit = set(_COMBAT_METHODS) | {"player/session_mixins/combat.py"}
    missing = sorted(expected_explicit - set(V047_EXPLICIT_RUNTIME_EXPORTS))
    if missing:
        errors.append("combat modules missing from v0.47 explicit cohort: " + ", ".join(missing))

    for rel, expected_methods in _COMBAT_METHODS.items():
        path = root / rel
        observed = _class_methods(path)
        if observed != expected_methods:
            errors.append(f"combat ownership mismatch {rel}: {observed} != {expected_methods}")
        implicit = implicit_global_references(path)
        if implicit:
            errors.append(f"combat module has implicit globals {rel}: {', '.join(implicit)}")

    aggregate = root / "player/session_mixins/combat.py"
    if len(aggregate.read_text(encoding="utf-8").splitlines()) > 40:
        errors.append("combat.py aggregate grew beyond 40 lines; gameplay belongs in focused mixins")
    if _class_methods(aggregate):
        errors.append("combat.py aggregate contains gameplay methods instead of composition only")

    reward_source = (root / "player/session_mixins/combat_rewards.py").read_text(encoding="utf-8")
    if "from world.global_difficulty_overdrive import v0190_combat_reward" not in reward_source:
        errors.append("final combat reward override is not lazily resolved")
    if "from world.magitek_infinite import boss_floor_identity" not in reward_source:
        errors.append("final Magitek boss identity override is not lazily resolved")

    metrics = legacy_dependency_metrics(root, RUNTIME_MODULES, EXPLICIT_RUNTIME_EXPORTS)
    total = int(metrics["legacy_implicit_reference_total"])
    if total != int(LEGACY_IMPLICIT_DEPENDENCY_BUDGET):
        errors.append(
            f"legacy implicit dependency budget mismatch: {total} != {LEGACY_IMPLICIT_DEPENDENCY_BUDGET}"
        )
    if total > 1086:
        errors.append(f"v0.47 dependency target regressed: {total} > 1086")

    return {
        "version": "0.47.0",
        "error_count": len(errors),
        "errors": errors,
        "focused_combat_module_count": len(_COMBAT_METHODS),
        "combat_method_count": sum(len(v) for v in _COMBAT_METHODS.values()),
        "v047_explicit_module_count": len(V047_EXPLICIT_RUNTIME_EXPORTS),
        "explicit_module_count": len(EXPLICIT_RUNTIME_EXPORTS),
        "legacy_compat_module_count": metrics["legacy_module_count"],
        "legacy_implicit_reference_total": total,
        "legacy_implicit_reference_budget": LEGACY_IMPLICIT_DEPENDENCY_BUDGET,
    }


COMBAT_ARCHITECTURE_AUDIT_V0470 = combat_architecture_audit_v0470()
if COMBAT_ARCHITECTURE_AUDIT_V0470["error_count"]:
    raise RuntimeError(
        "Combat Architecture Audit v0.47.0 failed: "
        + "; ".join(COMBAT_ARCHITECTURE_AUDIT_V0470["errors"][:100])
    )
