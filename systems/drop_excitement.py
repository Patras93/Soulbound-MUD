# -*- coding: utf-8 -*-
"""Soulbound v1.13.29 - Drop Chance & Reward Excitement helpers.

This pass does not replace authored loot. It only prevents high-value named
boss equipment from inheriting an obsolete low chance and exposes one
auditable rank hierarchy for equipment excitement.
"""
from __future__ import annotations

from data.items import ITEMS

V11329_DROP_EXCITEMENT_VERSION = "1.13.29"

V11329_CLASS_EQ_DROP_CHANCE = {
    "normal": 0.07,
    "elite": 0.18,
    "rare": 0.28,
    "mini_boss": 0.40,
    "boss": 0.55,
    "world_boss": 0.70,
}

V11329_NAMED_EQUIPMENT_DROP_FLOOR = {
    "mini_boss": 0.40,
    "boss": 0.50,
    "world_boss": 0.60,
}


def combat_rank_v11329(template):
    template = template or {}
    if template.get("world_boss"):
        return "world_boss"
    if template.get("mini_boss"):
        return "mini_boss"
    if any(template.get(flag) for flag in (
        "crypt_boss",
        "astral_boss",
        "mythic_crypt_boss",
        "mythic_astral_boss",
        "giant_fortress_boss",
        "dungeon_boss",
        "instance_boss",
        "boss_mechanic",
    )):
        return "boss"
    if any(template.get(flag) for flag in (
        "rare_mob",
        "rare_variant",
        "rare_troll",
    )):
        return "rare"
    if template.get("elite_affix"):
        return "elite"
    return "normal"


def class_equipment_drop_chance_v11329(template):
    return float(V11329_CLASS_EQ_DROP_CHANCE[combat_rank_v11329(template)])


def authored_drop_chance_v11329(template, item_id, authored_chance):
    """Return the effective chance for one authored direct-drop entry.

    Only named equipment from boss-type sources gets a floor. Potions,
    resources, quest items, tokens and ordinary materials keep their exact
    authored chances.
    """
    try:
        chance = max(0.0, min(1.0, float(authored_chance)))
    except (TypeError, ValueError, OverflowError):
        chance = 0.0
    if chance >= 1.0:
        return 1.0

    item = ITEMS.get(str(item_id)) or {}
    source = str(item.get("equipment_identity_source") or "")
    if source not in {
        "world_boss",
        "boss_set",
        "boss_relic",
        "crypt_boss",
    }:
        return chance

    rank = combat_rank_v11329(template)
    floor = V11329_NAMED_EQUIPMENT_DROP_FLOOR.get(rank, 0.0)
    return max(chance, float(floor))


def drop_excitement_audit_v11329():
    errors = []

    order = ("normal", "elite", "rare", "mini_boss", "boss", "world_boss")
    values = [V11329_CLASS_EQ_DROP_CHANCE[key] for key in order]
    if any(values[i] >= values[i + 1] for i in range(len(values) - 1)):
        errors.append("class-EQ chance hierarchy is not strictly increasing")

    if combat_rank_v11329({"rare_mob": True}) != "rare":
        errors.append("rare_mob flag is not recognized as Rare")
    if class_equipment_drop_chance_v11329({"rare_mob": True}) != 0.28:
        errors.append("Rare class-EQ chance mismatch")
    if class_equipment_drop_chance_v11329({"world_boss": True}) != 0.70:
        errors.append("World Boss class-EQ chance mismatch")

    # Use an existing named world-boss unique if present.
    named = next(
        (
            (item_id, item)
            for item_id, item in ITEMS.items()
            if item.get("equipment_identity_source") == "world_boss"
        ),
        None,
    )
    if named:
        item_id, _item = named
        effective = authored_drop_chance_v11329(
            {"world_boss": True}, item_id, 0.10
        )
        if effective < 0.60:
            errors.append("named World Boss equipment floor missing")

    # Non-equipment authored loot must remain exact.
    if authored_drop_chance_v11329(
        {"world_boss": True}, "healing_potion", 0.10
    ) != 0.10:
        errors.append("ordinary authored loot chance was modified")

    return {
        "version": V11329_DROP_EXCITEMENT_VERSION,
        "error_count": len(errors),
        "errors": errors,
    }


DROP_EXCITEMENT_AUDIT_V11329 = drop_excitement_audit_v11329()
if DROP_EXCITEMENT_AUDIT_V11329["error_count"]:
    raise RuntimeError(
        "Drop Excitement Audit v1.13.29 failed: "
        + "; ".join(DROP_EXCITEMENT_AUDIT_V11329["errors"][:50])
    )
