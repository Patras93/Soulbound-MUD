# -*- coding: utf-8 -*-
"""Soulbound v0.36.9 - cumulative release integrity guard.

This file intentionally changes no gameplay. It verifies that recent milestone
features are still present after assembling the final runtime.
"""

_RELEASE_AUDITS_V0369 = [
    ("v0.35.5 party temple/shards", "PARTY_TEMPLE_SHARD_AUDIT_V0355"),
    ("v0.35.6 salvage all", "SALVAGE_ALL_AUDIT_V0356"),
    ("v0.35.7 bulk smelting/ingot smithing", "BULK_SMELTING_INGOT_SMITHING_AUDIT_V0357"),
    ("v0.35.8 no PvP", "NO_PVP_PLAYER_SAFETY_AUDIT_V0358"),
    ("v0.35.9 shared mob drops", "ALL_PARTY_MOB_DROPS_SHARED_AUDIT_V0359"),
    ("v0.35.10 shared corpse loot", "ALL_PARTY_CORPSE_LOOT_SHARED_AUDIT_V03510"),
    ("v0.35.11 local party combat buffs", "ALL_LOCAL_PARTY_BUFFS_AUDIT_V03511"),
    ("v0.36.0 progression 600/leader disband", "PROGRESSION_600_AND_LEADER_DISBAND_AUDIT_V0360"),
    ("v0.36.1 party quest accept", "PARTY_QUEST_ACCEPT_SYNC_AUDIT_V0361"),
    ("v0.36.2 terrain threat", "TERRAIN_THREAT_REBALANCE_AUDIT_V0362"),
    ("v0.36.3 offline profiles", "OFFLINE_PLAYER_PROFILES_AUDIT_V0363"),
    ("v0.36.4 independent cooldowns", "INDEPENDENT_SKILL_COOLDOWNS_AUDIT_V0364"),
    ("v0.36.5 Soul Tier 7 cemetery density", "SOUL_TIER7_CEMETERY_SPAWN_AUDIT_V0365"),
    ("v0.36.6 named UOSSMUD superbosses", "UOSS_SUPERBOSS_AUDIT_V0366"),
    ("v0.36.8 crypt/EXP/same-room exit/local Soul Tier", "CRYPT_PARTY_REBALANCE_AUDIT_V0368"),
    ("v0.36.10 every crypt floor harder", "CRYPT_EVERY_FLOOR_PROGRESSION_AUDIT_V03610"),
    ("v0.37.0 Crypt Overdrive", "CRYPT_OVERDRIVE_AUDIT_V0370"),
    ("v0.36.11 troll shaman density", "TROLL_SHAMAN_DENSITY_AUDIT_V03611"),
    ("v0.37.0 public records/hall/key salvage", "PUBLIC_RECORDS_AUDIT_V0370"),
    ("v0.37.1 local party revive", "PARTY_REVIVE_AUDIT_V0371"),
    ("v0.38.0 party combo/ultimate/dungeon summary", "PARTY_SYSTEMS_AUDIT_V0380"),
    ("v0.38.1 Tower Overdrive", "TOWER_OVERDRIVE_AUDIT_V0381"),
    ("v0.38.2 Infinite Unified Magitek", "MAGITEK_INFINITE_AUDIT_V0382"),
    ("v0.38.3 hourly Magitek contracts", "MAGITEK_HOURLY_QUESTS_AUDIT_V0383"),
    ("v0.38.4 global world threat", "WORLD_THREAT_OVERDRIVE_AUDIT_V0384"),
]

def cumulative_release_integrity_audit_v0369():
    errors=[]
    preserved=[]
    for label, varname in _RELEASE_AUDITS_V0369:
        value=globals().get(varname)
        if not isinstance(value, dict):
            errors.append(f"missing audit: {label} ({varname})")
            continue
        count=int(value.get("error_count",0) or 0)
        if count:
            errors.append(f"regression in {label}: {count} errors")
            continue
        preserved.append(label)

    # Direct release-line checks for the exact milestones the user flagged.
    if str(globals().get("VERSION","")) != "0.38.4":
        errors.append(f"VERSION={globals().get('VERSION')!r}, expected 0.38.4")
    if str(globals().get("GENERATOR_CORE_VERSION","")) != "0.38.4":
        errors.append(f"Generator Core={globals().get('GENERATOR_CORE_VERSION')!r}, expected 0.38.4")

    return {
        "version":"0.38.4",
        "checked":len(_RELEASE_AUDITS_V0369),
        "preserved":preserved,
        "preserved_count":len(preserved),
        "error_count":len(errors),
        "errors":errors,
    }

CUMULATIVE_RELEASE_INTEGRITY_AUDIT_V0369=cumulative_release_integrity_audit_v0369()
if CUMULATIVE_RELEASE_INTEGRITY_AUDIT_V0369["error_count"]:
    raise RuntimeError(
        "Cumulative Release Integrity Audit v0.38.4 failed: "
        + "; ".join(CUMULATIVE_RELEASE_INTEGRITY_AUDIT_V0369["errors"][:100])
    )

HELP_TOPICS.setdefault("wersja", []).append(
    "v0.38.4: Cumulative Release Integrity — zachowuje wszystkie wcześniejsze milestone'y i dodaje Global World Threat Overdrive."
)
LATEST_CHANGES_TITLE = "Soulbound v0.38.4 - Global World Threat Overdrive"
LATEST_CHANGES = [
    "Globalnie wzmocniono otwarty świat, Elite/Rare, bossów, World Bossów, Nemesis i dynamiczne eventy.",
    "HP, obrażenia i nagrody rosną wraz z etapem świata; bossowie i Nemesis mają dodatkowe mnożniki.",
    "Krypty, Wieże i Nieskończony Magitek zachowują własne mocniejsze warstwy trudności.",
    "Zachowano wszystkie wcześniejsze audytowane milestone'y.",
]
