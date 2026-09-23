# -*- coding: utf-8 -*-
"""Soulbound v0.54.0 - risk-free courier and courier achievements audit."""
from pathlib import Path

from config.postal import (
    COURIER_ALL_CITIES_ACHIEVEMENT_V0540,
    COURIER_ALL_PACKAGE_TYPES_ACHIEVEMENT_V0540,
    COURIER_DELIVERY_ACHIEVEMENTS_V0540,
    COURIER_PACKAGE_CLASSES_V0530,
    POSTAL_CITY_HUBS_V0522,
)

ROOT = Path(__file__).resolve().parents[1]


def courier_achievements_audit_v0540():
    errors = []
    expected_thresholds = [10, 100, 1000, 10000]
    thresholds = [int(row[0]) for row in COURIER_DELIVERY_ACHIEVEMENTS_V0540]
    if thresholds != expected_thresholds:
        errors.append(f"courier delivery achievement thresholds={thresholds}, expected {expected_thresholds}")
    original_types = {"zwykla", "pilna", "ciezka", "delikatna", "tajna", "wartosciowa"}
    if not original_types.issubset(set(COURIER_PACKAGE_CLASSES_V0530)):
        errors.append("one or more original v0.54 courier package classes are missing")
    for key, spec in COURIER_PACKAGE_CLASSES_V0530.items():
        forbidden = {"risk", "incident_penalty", "timed"}.intersection(spec)
        if forbidden:
            errors.append(f"{key}: obsolete risk fields remain: {sorted(forbidden)}")
        if float(spec.get("reward_mult", 0)) <= 0:
            errors.append(f"{key}: invalid reward multiplier")

    social = (ROOT / "player/session_mixins/courier_delivery.py").read_text(encoding="utf-8")
    for token in (
        "courier_sync_achievements_v0540",
        "postal_show_achievements_v0540",
        "courier_package_type:",
        "poczta osiągnięcia",
    ):
        if token not in social:
            errors.append(f"missing courier achievement feature: {token}")
    for obsolete in ("risk_probability", "risk_percent", "incident_penalty"):
        # Migration cleanup may name legacy fields only inside pop(...), but no
        # active calculation/display may remain.
        active_lines = [line for line in social.splitlines() if obsolete in line and "legacy_key" not in line]
        if active_lines:
            errors.append(f"active legacy risk token remains: {obsolete}")

    if len(POSTAL_CITY_HUBS_V0522) != 9:
        errors.append("all-cities courier achievement no longer targets 9 settlements")
    if not COURIER_ALL_CITIES_ACHIEVEMENT_V0540[0]:
        errors.append("all-cities achievement id missing")
    if not COURIER_ALL_PACKAGE_TYPES_ACHIEVEMENT_V0540[0]:
        errors.append("all-package-types achievement id missing")

    return {
        "version": "0.54.0",
        "delivery_thresholds": thresholds,
        "package_class_count": len(COURIER_PACKAGE_CLASSES_V0530),
        "city_count": len(POSTAL_CITY_HUBS_V0522),
        "error_count": len(errors),
        "errors": errors,
    }


COURIER_ACHIEVEMENTS_AUDIT_V0540 = courier_achievements_audit_v0540()
if COURIER_ACHIEVEMENTS_AUDIT_V0540["error_count"]:
    raise RuntimeError(
        "Courier Achievements Audit v0.54.0 failed: "
        + "; ".join(COURIER_ACHIEVEMENTS_AUDIT_V0540["errors"][:100])
    )

__all__ = ["courier_achievements_audit_v0540", "COURIER_ACHIEVEMENTS_AUDIT_V0540"]
