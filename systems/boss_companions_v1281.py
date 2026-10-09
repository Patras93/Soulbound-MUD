# -*- coding: utf-8 -*-
"""Boss companions: unbounded guardian waves for non-unique bosses.

The source-authored UOSS encounters have their own, independent summon
scripts; a summon is a real kill worth progression XP, but never repeatable
quest credit, equipment or gold.
"""

_BOSS_MARKERS = (
    "boss", "world_boss", "mini_boss", "crypt_boss", "mythic_crypt_boss",
    "astral_boss", "mythic_astral_boss", "guild_boss",
    "profession_dungeon_boss", "v018_legendary_event_boss",
    "v020_mythic_world_boss", "uoss_superboss",
)


def boss_companion_due_v1281(mob, template):
    if not mob or not getattr(mob, "alive", False) or not getattr(mob, "engaged_by", None):
        return False
    if any(template.get(flag) for flag in (
        "uoss_unique_superboss_key", "uoss_superboss_add", "training_dummy",
        "ai_ephemeral_summon_v1160", "boss_companion_v1281",
    )) or getattr(mob, "monster_ai_summoned_v1160", False):
        return False
    # v1.28.12: exceptionally rare legendary/mythic normal monsters
    # may call for help without pretending to be bosses (which would
    # incorrectly grant boss keys, chest access and quest credit).
    if not (any(template.get(marker) for marker in _BOSS_MARKERS)
            or template.get('elite_legend_rank_v1250')):
        return False
    turn = int(getattr(mob, "combat_turn", 0) or 0)
    return turn >= 4 and (turn - 4) % 7 == 0 and int(getattr(mob, "boss_last_summon_turn_v1281", -1)) != turn


def boss_guardian_identity_v1281(template):
    name = str(template.get("name") or "Bossa")
    magic = str(template.get("damage_type") or "").lower() == "magic"
    return (("Arkaniczny Strażnik " if magic else "Zbrojny Strażnik ") + name,
            "magic" if magic else "physical")


# Jammer is a Stop-only action; its boss immunity is shared by single-target
# and Support Effect (area) casts. Ordinary and summoned *non-boss* mobs
# remain valid targets. Classify using the same boss marker family as the
# existing elite exclusion rule, including scripted/legacy floor bosses.
def boss_jammer_immune_v1281(template):
    if not isinstance(template, dict):
        return False
    markers = (
        "boss", "world_boss", "v016_world_boss", "v020_mythic_world_boss",
        "mini_boss", "v0140_mini_boss", "crypt_boss", "mythic_crypt_boss",
        "astral_boss", "mythic_astral_boss", "giant_fortress_boss",
        "magitek_boss", "machine_boss", "guild_boss", "milestone_boss",
        "profession_dungeon_boss", "boss_mechanic", "uoss_superboss",
        "uoss_superboss_key", "uoss_unique_superboss_key",
        "v018_legendary_event_boss", "v018_great_ruin_guardian",
        "v020_megadungeon_boss",
    )
    if any(template.get(key) for key in markers):
        return True
    return str(template.get("rank") or "").strip().casefold() in {
        "boss", "world_boss", "mini", "miniboss", "mini_boss",
    }


GUARDIAN_ROLES_V12811 = (
    ("zbrojny", "Zbrojny", "physical", 1.0, 1.0),
    ("arkaniczny", "Arkaniczny", "magic", 0.85, 1.15),
    ("obronca", "Tarczownik", "physical", 1.65, 0.75),
    ("furia", "Berserker", "physical", 0.78, 1.50),
    ("uzdrowiciel", "Uzdrowiciel", "magic", 0.9, 0.85),
)


def boss_guardian_role_v12811(template, boss_mob, sequence):
    """Rotate summon combat roles; later HP phases change the lineup."""
    stage = max(0, min(3, int(getattr(boss_mob, 'v1230_boss_phase', 0) or 0)))
    index = (max(1, int(sequence)) - 1 + stage * 2) % len(GUARDIAN_ROLES_V12811)
    return GUARDIAN_ROLES_V12811[index]
