# -*- coding: utf-8 -*-
"""Soulbound v0.55.0 - prestige courier achievements and tavern hourlies audit."""
from pathlib import Path

from config.postal import (
    COURIER_CITY_DELIVERY_ACHIEVEMENTS_V0550,
    COURIER_PACKAGE_CLASSES_V0530,
    COURIER_PACKAGE_TYPE_ACHIEVEMENTS_V0550,
    POSTAL_CITY_HUBS_V0522,
    courier_unlocked_package_keys_v0530,
)
from data.quests import QUESTS

ROOT = Path(__file__).resolve().parents[1]


def courier_prestige_tavern_audit_v0550():
    errors = []
    prestige = COURIER_PACKAGE_CLASSES_V0530.get("prestizowa")
    if not prestige:
        errors.append("prestige package class missing")
    else:
        if int(prestige.get("unlock_rep", 0)) != 360:
            errors.append("prestige package must unlock at reputation 360")
        if float(prestige.get("reward_mult", 0)) < 4.0:
            errors.append("prestige package payout multiplier is not high enough")
        forbidden = {"risk", "incident_penalty", "timed", "risk_probability"}.intersection(prestige)
        if forbidden:
            errors.append(f"prestige package contains risk fields: {sorted(forbidden)}")
    if "prestizowa" in courier_unlocked_package_keys_v0530(359):
        errors.append("prestige package unlocks before reputation 360")
    if "prestizowa" not in courier_unlocked_package_keys_v0530(360):
        errors.append("prestige package not unlocked at reputation 360")

    if set(COURIER_CITY_DELIVERY_ACHIEVEMENTS_V0550) != set(POSTAL_CITY_HUBS_V0522):
        errors.append("100-delivery city achievements do not cover every postal city")
    if set(COURIER_PACKAGE_TYPE_ACHIEVEMENTS_V0550) != set(COURIER_PACKAGE_CLASSES_V0530):
        errors.append("100-delivery package achievements do not cover every package class")

    tavern_ids = ("elia_hourly_fish", "elia_hourly_herbs", "elia_hourly_bandits")
    for quest_id in tavern_ids:
        quest = QUESTS.get(quest_id)
        if not quest:
            errors.append(f"missing tavern quest: {quest_id}")
            continue
        if quest.get("giver") != "Karczmarka Elia":
            errors.append(f"{quest_id}: wrong giver")
        if not quest.get("repeatable") or int(quest.get("repeat_cooldown", 0)) != 3600:
            errors.append(f"{quest_id}: not independently hourly repeatable")

    social = (ROOT / "player/session_mixins/courier_delivery.py").read_text(encoding="utf-8")
    for token in (
        "courier_destination_count:",
        "courier_package_type_count:",
        "prestige_unlocked",
        "COURIER_CITY_DELIVERY_ACHIEVEMENTS_V0550",
        "COURIER_PACKAGE_TYPE_ACHIEVEMENTS_V0550",
    ):
        if token not in social:
            errors.append(f"missing v0.55 courier feature: {token}")

    npc_source = (ROOT / "data/npcs.py").read_text(encoding="utf-8")
    if "elia_hourly_fish" not in npc_source or "elia_hourly_bandits" not in npc_source:
        errors.append("Karczmarka Elia is not wired to the new hourly quests")

    return {
        "version": "0.55.0",
        "city_achievement_count": len(COURIER_CITY_DELIVERY_ACHIEVEMENTS_V0550),
        "package_achievement_count": len(COURIER_PACKAGE_TYPE_ACHIEVEMENTS_V0550),
        "tavern_hourly_count": len(tavern_ids),
        "error_count": len(errors),
        "errors": errors,
    }


COURIER_PRESTIGE_TAVERN_AUDIT_V0550 = courier_prestige_tavern_audit_v0550()
if COURIER_PRESTIGE_TAVERN_AUDIT_V0550["error_count"]:
    raise RuntimeError(
        "Courier Prestige & Tavern Audit v0.55.0 failed: "
        + "; ".join(COURIER_PRESTIGE_TAVERN_AUDIT_V0550["errors"][:100])
    )

__all__ = ["courier_prestige_tavern_audit_v0550", "COURIER_PRESTIGE_TAVERN_AUDIT_V0550"]
