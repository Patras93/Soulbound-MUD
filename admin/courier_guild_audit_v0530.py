# -*- coding: utf-8 -*-
"""Soulbound v0.53.0 - Courier Guild and package-class audit."""
from pathlib import Path

from config.postal import (
    COURIER_CITY_ROOM_TO_NAME_V0530,
    COURIER_PACKAGE_CLASSES_V0530,
    COURIER_RANKS_V0530,
    COURIER_REPUTATION_MAX_V0530,
    POSTAL_CITY_HUBS_V0522,
    courier_rank_for_reputation_v0530,
    courier_unlocked_package_keys_v0530,
)

ROOT = Path(__file__).resolve().parents[1]


def courier_guild_audit_v0530():
    errors = []
    expected_types = {"zwykla", "pilna", "ciezka", "delikatna", "tajna", "wartosciowa"}
    if not expected_types.issubset(set(COURIER_PACKAGE_CLASSES_V0530)):
        errors.append("one or more original six courier package classes are missing")
    if COURIER_REPUTATION_MAX_V0530 != 400:
        errors.append(f"courier reputation max={COURIER_REPUTATION_MAX_V0530}, expected 400")
    thresholds = [int(row[0]) for row in COURIER_RANKS_V0530]
    if thresholds != sorted(set(thresholds)) or thresholds[0] != 1 or thresholds[-1] != 400:
        errors.append("courier rank thresholds must be unique, increasing and span 1..400")
    titles = {row[1] for row in COURIER_RANKS_V0530}
    for required in ("Posłaniec", "Kurier Królewski", "Mistrz Szlaków"):
        if required not in titles:
            errors.append(f"missing courier title: {required}")
    if not set(COURIER_PACKAGE_CLASSES_V0530).issubset(set(courier_unlocked_package_keys_v0530(400))):
        errors.append("reputation 400 does not unlock all current package classes")
    if courier_rank_for_reputation_v0530(400)["name"] != "Mistrz Szlaków":
        errors.append("reputation 400 is not Mistrz Szlaków")
    for key, spec in COURIER_PACKAGE_CLASSES_V0530.items():
        if float(spec.get("reward_mult", 0)) <= 0:
            errors.append(f"{key}: invalid reward multiplier")
    if len(set(COURIER_CITY_ROOM_TO_NAME_V0530.values())) != len(POSTAL_CITY_HUBS_V0522):
        errors.append("courier city visit map does not cover all postal settlements")

    schema = (ROOT / "storage/schema_migrate_social.py").read_text(encoding="utf-8")
    db_world = (ROOT / "storage/db_world.py").read_text(encoding="utf-8")
    social = (ROOT / "player/session_mixins/courier_delivery.py").read_text(encoding="utf-8")
    movement = (ROOT / "player/session_mixins/movement.py").read_text(encoding="utf-8")
    guilds = (ROOT / "player/session_mixins/forge_guilds.py").read_text(encoding="utf-8")
    if "courier_guild_state_v0530" not in schema:
        errors.append("courier guild persistence table missing")
    for method in ("courier_guild_state_v0530", "save_courier_guild_state_v0530", "record_courier_city_visit_v0530"):
        if f"def {method}" not in db_world:
            errors.append(f"courier persistence method missing: {method}")
    for token in ("postal_show_guild_v0530", "postal_show_statistics_v0530", "courier_rep_gain_v0530"):
        if token not in social:
            errors.append(f"courier session feature missing: {token}")
    if "record_courier_city_visit_v0530" not in movement:
        errors.append("movement does not record courier city visits")
    if "postal_show_guild_v0530" not in guilds:
        errors.append("gildia kurierow command bridge missing")

    return {
        "version": "0.53.0",
        "rank_count": len(COURIER_RANKS_V0530),
        "package_class_count": len(COURIER_PACKAGE_CLASSES_V0530),
        "city_count": len(POSTAL_CITY_HUBS_V0522),
        "error_count": len(errors),
        "errors": errors,
    }


COURIER_GUILD_AUDIT_V0530 = courier_guild_audit_v0530()
if COURIER_GUILD_AUDIT_V0530["error_count"]:
    raise RuntimeError(
        "Courier Guild Audit v0.53.0 failed: "
        + "; ".join(COURIER_GUILD_AUDIT_V0530["errors"][:100])
    )

__all__ = ["courier_guild_audit_v0530", "COURIER_GUILD_AUDIT_V0530"]
