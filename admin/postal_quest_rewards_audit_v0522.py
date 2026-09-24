# -*- coding: utf-8 -*-
"""Soulbound v0.52.2 - city courier and quest reward audit."""
from __future__ import annotations

from pathlib import Path

from config.command_aliases import COMMAND_ALIAS_DEFINITIONS
from config.postal import (
    GUIDE_CITY_HUBS_V0522, POSTAL_CITY_HUBS_V0522,
    POSTAL_OFFERS_PER_CITY_V0522, POSTAL_REFRESH_SECONDS_V0522,
)
from data.catalogs import ROOMS
from core.progression_resources import (
    v0522_combat_quest_class_reward, v0522_is_profession_quest,
)

ROOT = Path(__file__).resolve().parents[1]



def postal_quest_rewards_audit_v0522():
    errors = []
    if POSTAL_REFRESH_SECONDS_V0522 != 900:
        errors.append(f"postal refresh={POSTAL_REFRESH_SECONDS_V0522}, expected 900")
    if POSTAL_OFFERS_PER_CITY_V0522 != 5:
        errors.append(f"postal offers={POSTAL_OFFERS_PER_CITY_V0522}, expected 5")
    if len(POSTAL_CITY_HUBS_V0522) < 9:
        errors.append(f"postal settlements={len(POSTAL_CITY_HUBS_V0522)}, expected at least original 9")
    if set(POSTAL_CITY_HUBS_V0522) != set(GUIDE_CITY_HUBS_V0522):
        errors.append("postal and guide city catalogs differ")

    # Reachability of the v0.51/v0.52 settlement hubs is already guarded by
    # the two preceding World Expansion audits.  Here we additionally make sure
    # every postal/guide hub is still authored somewhere in the world sources,
    # including the older Miasto Dusz courier office.
    world_source = "\n".join(
        p.read_text(encoding="utf-8", errors="replace")
        for p in (ROOT / "world").glob("*.py")
    )
    for city, hub in POSTAL_CITY_HUBS_V0522.items():
        if hub not in ROOMS and hub not in world_source:
            errors.append(f"postal hub is neither loaded nor authored in world sources: {city}->{hub}")
    for city, hub in GUIDE_CITY_HUBS_V0522.items():
        if hub not in ROOMS and hub not in world_source:
            errors.append(f"guide city hub is neither loaded nor authored in world sources: {city}->{hub}")

    for alias in ("poczta", "paczka", "paczki", "postal", "package", "packages"):
        if COMMAND_ALIAS_DEFINITIONS.get(alias) != "postal":
            errors.append(f"postal alias {alias!r} does not resolve to postal")
    if COMMAND_ALIAS_DEFINITIONS.get("walk") != "guide" or COMMAND_ALIAS_DEFINITIONS.get("prowadz") != "guide":
        errors.append("walk/prowadz does not resolve to guide")

    if v0522_combat_quest_class_reward({"kind":"kill", "needed":5}) <= 0:
        errors.append("combat quest does not grant Biegłość XP")
    if v0522_combat_quest_class_reward({"kind":"gather", "needed":5}) != 0:
        errors.append("non-combat quest grants Biegłość XP")
    profession_probe = {"kind":"gather", "reward_profession_xp":10, "reward_profession":"Górnictwo"}
    if not v0522_is_profession_quest(profession_probe):
        errors.append("profession quest is not recognized for Soul XP suppression")

    quest_source = (ROOT / "player/session_mixins/quest_commands.py").read_text(encoding="utf-8")
    if "reward_soul_xp = 0 if is_profession_quest else" not in quest_source:
        errors.append("profession quest Soul XP suppression missing")
    if "await self.grant_class_xp(reward_class_xp)" not in quest_source:
        errors.append("combat quest Biegłość reward grant missing")
    schema_source = (ROOT / "storage/schema_migrate_social.py").read_text(encoding="utf-8")
    if "postal_delivery_state_v0522" not in schema_source:
        errors.append("postal persistence schema missing")
    guide_source = (ROOT / "player/session_mixins/guide_navigation.py").read_text(encoding="utf-8")
    if 'selected == "miasta"' not in guide_source:
        errors.append("walk/prowadz city list missing")

    return {
        "version":"0.52.2",
        "settlement_count":len(POSTAL_CITY_HUBS_V0522),
        "refresh_seconds":POSTAL_REFRESH_SECONDS_V0522,
        "offers_per_city":POSTAL_OFFERS_PER_CITY_V0522,
        "declared_postal_hubs":sum(1 for hub in POSTAL_CITY_HUBS_V0522.values() if hub in world_source),
        "error_count":len(errors),
        "errors":errors,
    }


POSTAL_QUEST_REWARDS_AUDIT_V0522 = postal_quest_rewards_audit_v0522()
if POSTAL_QUEST_REWARDS_AUDIT_V0522["error_count"]:
    raise RuntimeError(
        "Postal & Quest Rewards Audit v0.52.2 failed: "
        + "; ".join(POSTAL_QUEST_REWARDS_AUDIT_V0522["errors"][:100])
    )

__all__ = ["postal_quest_rewards_audit_v0522", "POSTAL_QUEST_REWARDS_AUDIT_V0522"]
