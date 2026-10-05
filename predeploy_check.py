#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Fast Railway predeploy gate for Soulbound v1.12.8.

This is the normal deploy check.  It intentionally avoids assembling the full
world/runtime.  Use predeploy_full.py when an exhaustive historical audit is
wanted before a major release.
"""
from __future__ import annotations

import re
import traceback

# Railway/admin tools import the database facade directly. Keep this as an
# explicit smoke test so direct-import regressions fail the deploy gate.
try:
    from storage.database import Database as _DatabaseImportSmoke
except Exception as exc:
    print(f"Soulbound v1.12.8 FAST PREDEPLOY FAILED: database import: {type(exc).__name__}: {exc}")
    traceback.print_exc()
    raise SystemExit(1)

from admin.fast_predeploy_audit_v0571 import FAST_PREDEPLOY_AUDIT_V0571 as audit

# v1.11.96 semantic gameplay gates. These import only the static class/skill
# catalog and are intentionally kept out of the full world/runtime loader.
try:
    from core.classes_skills import (
        MEC_CONTRACT_AUDIT_V11149,
        ENGINEER_AP_SEMANTICS_AUDIT_V11196,
        ALL_CLASS_SKILL_TARGET_AUDIT_V11196,
        CLASS_HEALING_SCALE_AUDIT_V11196,
        HARMFUL_DEBUFF_TARGET_AUDIT_V11196,
        PRIEST_HEALING_CONTRACT_AUDIT_V11196,
        UOSS_STATUS_SOURCE_CONTRACT_AUDIT_V11196,
        ALL_CLASS_ENDGAME_DAMAGE_AUDIT_V11196,
    )
except Exception as exc:
    print(
        "Soulbound v1.12.8 FAST PREDEPLOY FAILED: "
        f"skill semantic import: {type(exc).__name__}: {exc}"
    )
    traceback.print_exc()
    raise SystemExit(1)

_semantic_audits = {
    "mec_contract": MEC_CONTRACT_AUDIT_V11149,
    "engineer_ap": ENGINEER_AP_SEMANTICS_AUDIT_V11196,
    "all_class_targets": ALL_CLASS_SKILL_TARGET_AUDIT_V11196,
    "healing_scales": CLASS_HEALING_SCALE_AUDIT_V11196,
    "harmful_debuff_targets": HARMFUL_DEBUFF_TARGET_AUDIT_V11196,
    "priest_healing": PRIEST_HEALING_CONTRACT_AUDIT_V11196,
    "uoss_status_contracts": UOSS_STATUS_SOURCE_CONTRACT_AUDIT_V11196,
    "endgame_damage": ALL_CLASS_ENDGAME_DAMAGE_AUDIT_V11196,
}
_semantic_errors = []
for _name, _result in _semantic_audits.items():
    if int(_result.get("error_count", 0) or 0):
        for _error in _result.get("errors", ()):
            _semantic_errors.append(f"{_name}: {_error}")

# AP is a learning-point cost, never authored combat power. Keep a small
# source-level regression guard around the two runtime files that previously
# leaked UOSS Base AP into Mec/Engineer damage.
from pathlib import Path as _Path
_root = _Path(__file__).resolve().parent

# Release identity guard: the login banner uses VERSION from bootstrap, while
# CHANGELOG_PL.txt announces the current package. Reject deploys when those two
# sources drift apart so the public banner cannot lag behind the shipped build.
_bootstrap_source = (_root / "core/bootstrap_economy_professions.py").read_text(encoding="utf-8")
_changelog_source = (_root / "CHANGELOG_PL.txt").read_text(encoding="utf-8")
_version_match = re.search(r'^VERSION\s*=\s*"([^"]+)"', _bootstrap_source, re.MULTILINE)
_package_match = re.search(r'^Aktualna paczka:\s*v([^\s]+)', _changelog_source, re.MULTILINE)
if not _version_match:
    _semantic_errors.append("release identity: missing canonical VERSION in bootstrap")
elif not _package_match:
    _semantic_errors.append("release identity: missing current package in CHANGELOG_PL.txt")
elif _version_match.group(1) != _package_match.group(1):
    _semantic_errors.append(
        "release identity mismatch: "
        f"VERSION={_version_match.group(1)} vs changelog={_package_match.group(1)}"
    )
_forbidden_ap_runtime = {
    "player/session_mixins/combat_skills.py": (
        'skill.get("base_power"',
    ),
    "player/session_mixins/skill_learning.py": (
        '_intercept.get("base_power"',
    ),
}
for _rel, _needles in _forbidden_ap_runtime.items():
    _source = (_root / _rel).read_text(encoding="utf-8")
    for _needle in _needles:
        if _needle in _source:
            _semantic_errors.append(
                f"AP semantics regression: {_rel} contains forbidden {_needle}"
            )

# v1.12.8 regression guard: Heal Beam target preparation checks support_effect
# before the authored-Mec execution block. The variable must therefore be
# resolved earlier in use_class_skill, otherwise combat crashes at runtime.
_combat_skills_source = (_root / "player/session_mixins/combat_skills.py").read_text(encoding="utf-8")
_support_init_pos = _combat_skills_source.find(
    "support_effect = bool(\n                    skill.get(\"mec_authored\")"
)
_heal_beam_precheck_pos = _combat_skills_source.find("_heal_beam_targets = []")
if (
    _support_init_pos < 0
    or _heal_beam_precheck_pos < 0
    or _support_init_pos > _heal_beam_precheck_pos
):
    _semantic_errors.append(
        "Heal Beam support regression: support_effect must be initialized before target preparation"
    )

# v1.12.8 regression guard: authored troll quest stat rewards must bypass
# Generator Core's generated reward_stat_progress so the explicit balance
# values remain exact and visible to players.
_progression_source = (_root / "core/progression_resources.py").read_text(encoding="utf-8")
_troll_rewards_source = (_root / "world/troll_shaman_density.py").read_text(encoding="utf-8")
if 'manual_reward = quest.get("manual_stat_progress")' not in _progression_source:
    _semantic_errors.append(
        "troll stat reward regression: manual_stat_progress override missing"
    )
_troll_reward_needles = (
    '"mountain_troll_hunt": 15_000',
    '"mountain_trail_patrol": 15_000',
    '"stolen_mountain_ores": 15_000',
    '"troll_shaman_hunt": 18_000',
    '"deep_troll_clearance": 20_000',
    '"troll_king_hunt": 25_000',
)
for _needle in _troll_reward_needles:
    if _needle not in _troll_rewards_source:
        _semantic_errors.append(
            "troll stat reward regression: missing " + _needle
        )

if _semantic_errors:
    print("Soulbound v1.12.8 FAST PREDEPLOY FAILED: semantic contracts")
    for _error in _semantic_errors:
        print(f"ERROR: {_error}")
    raise SystemExit(1)

if audit["error_count"]:
    print("Soulbound v1.12.8 FAST PREDEPLOY FAILED")
    for error in audit["errors"]:
        print(f"ERROR: {error}")
    raise SystemExit(1)

print("Soulbound v1.12.8 FAST PREDEPLOY PASS")
print(
    "Semantic contracts: "
    f"{len(_semantic_audits)} audits PASS; AP runtime guards PASS"
)
print(f"Runtime manifest: {audit['runtime_module_count']} modules; {len(audit['missing_manifest_files'])} missing; {audit['syntax_error_count']} syntax errors")
print(
    f"Whole repo Python: {audit['all_python_source_count']} files; "
    f"{audit['all_source_syntax_error_count']} syntax errors; "
    f"{audit['duplicate_literal_key_count']} duplicate dict keys; "
    f"{audit['swallowed_exception_count']} swallowed exceptions; "
    f"{audit.get('intentional_swallowed_exception_count', 0)} intentional passes; "
    f"{audit['todo_fixme_count']} TODO/FIXME"
)
print(f"Docker COPY sources: {len(audit['missing_docker_copy_sources'])} missing")
print(f"Railway critical import: {'PASS' if audit['critical_import_ok'] else 'FAIL'}")
print(f"SQLite smoke: {audit['schema_table_count']} tables; {audit['schema_object_count']} objects")
print(f"Commands: {audit['alias_count']} aliases; {audit['registered_command_count']} registered handlers")
if audit.get("warning_count"):
    print(f"FAST PREDEPLOY WARNINGS: {audit['warning_count']}")
    for warning in audit.get("warnings", ())[:50]:
        print(f"WARNING: {warning}")
print("Full historical audit remains available with: python predeploy_full.py")
