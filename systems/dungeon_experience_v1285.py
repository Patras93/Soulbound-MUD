# -*- coding: utf-8 -*-
"""Dungeon combat XP balance, v1.28.6.

The v1.28.5 dungeon minimum used the *mob's* level-800 XP requirement
for every character, allowing a low-level player to jump many levels after
one high-floor kill. Keep per-level requirements unchanged and calculate the
actual payout individually at combat resolution, after party/adaptive bonuses.
No Generator Core, catalog mutation or database migration is required.
"""
from __future__ import annotations

import math

from core.progression_resources import (
    character_xp_to_next,
    class_mastery_xp_to_next,
    soul_xp_to_next,
)

SAFE_XP = 9_000_000_000_000_000_000
_DUNGEON_FLOOR_KEYS = (
    "crypt_floor", "mythic_crypt_floor", "astral_floor", "mythic_astral_floor",
    "magitek_floor", "giant_fortress_floor", "profession_dungeon_floor",
)
_BOSS_KEYS = (
    "crypt_boss", "mythic_crypt_boss", "astral_boss", "mythic_astral_boss",
    "magitek_boss", "giant_fortress_boss", "profession_dungeon_boss",
    "boss", "world_boss", "boss_mechanic", "mini_boss",
)
_REQUIREMENTS = {
    "character": character_xp_to_next,
    "class": class_mastery_xp_to_next,
    "soul": soul_xp_to_next,
}
_RANK_BONUS = {"normal": 1.0, "elite": 1.7, "rare": 2.6,
               "mini": 4.5, "boss": 8.5, "world_boss": 12.0}


def authored_dungeon_floor_v1285(template):
    """Avoid modifying ordinary world encounters and exact UOSS source XP."""
    if not isinstance(template, dict):
        return 0
    for key in _DUNGEON_FLOOR_KEYS:
        value = template.get(key)
        if value is not None:
            try:
                return max(0, int(value))
            except (ValueError, TypeError, OverflowError):
                return 0
    return 0


def _target_kills_for_level_v1285(stage):
    """Long-term 36 -> 48 -> 65 -> 190 ordinary kills per level, before bonuses."""
    stage = max(1, int(stage))
    if stage <= 100:
        return 36.0
    if stage <= 150:
        return 36.0 + (stage - 100) * 12 / 50
    if stage <= 200:
        return 48.0 + (stage - 150) * 17 / 50
    return 65.0 + (stage - 200) * 125 / 600


def _encounter_rank_v1286(template):
    if (template.get("world_boss") or template.get("v016_world_boss")
            or template.get("mythic_crypt_boss") or template.get("mythic_astral_boss")
            or str(template.get("rank", "")).lower() == "world_boss"):
        return "world_boss"
    if any(template.get(k) for k in _BOSS_KEYS if k not in ("mini_boss", "world_boss", "mythic_crypt_boss", "mythic_astral_boss")) or str(template.get("rank", "")).lower() == "boss":
        return "boss"
    if template.get("mini_boss") or str(template.get("rank", "")).lower() in ("mini", "mini_boss", "miniboss"):
        return "mini"
    if any(template.get(k) for k in ("rare_mob", "rare_variant", "rare_troll", "v016_legendary_rare")) or str(template.get("rank", "")).lower() == "rare":
        return "rare"
    if any(template.get(k) for k in ("elite", "elite_affix")) or str(template.get("rank", "")).lower() == "elite":
        return "elite"
    return "normal"


def dungeon_kill_xp_v1285(template, axis, prior_xp):
    """Compatibility hook: 30% extra in dungeons, never a floor-level XP minimum.

    The final per-recipient correction runs after the combat multipliers.
    """
    prior_xp = max(0, int(prior_xp or 0))
    if axis not in ("character", "class", "soul", "stat"):
        return prior_xp
    if (not authored_dungeon_floor_v1285(template)
            or template.get("training_dummy") or template.get("source_xp_exact")):
        return prior_xp
    return min(SAFE_XP, int(round(prior_xp * 1.30)))


def dungeon_recipient_xp_v1286(template, axis, prior_xp, player_level,
                                 *, combat_multiplier=1.0, downstream_multiplier=1.0):
    """Normalize generated dungeon kill XP to the ACTUAL recipient level.

    Prior XP includes party/adaptive multipliers. These still matter (capped to
    a bounded bonus), but never get to scale against the mob's XP requirement.
    Only dungeon combat kill payouts are affected: not quests, professions,
    open-world kills, uncapped stats or explicit source_xp_exact UOSS rewards.
    The downstream guard reserves enough headroom for x2 EXP / class guild /
    mentor bonuses without allowing a multi-level kill.
    """
    prior_xp = max(0, min(SAFE_XP, int(prior_xp or 0)))
    if (axis not in _REQUIREMENTS or not authored_dungeon_floor_v1285(template)
            or template.get("training_dummy") or template.get("source_xp_exact")):
        return prior_xp
    level = max(1, min(800, int(player_level or 1)))
    required = int(_REQUIREMENTS[axis](level))
    if required <= 0:  # Progression cap reached.
        return prior_xp
    try:
        downstream = max(1.0, min(16.0, float(downstream_multiplier)))
    except (ValueError, TypeError, OverflowError):
        downstream = 1.0
    # 42% of one requirement at most AFTER all multiplicative downstream XP
    # bonuses. Even with a player at 99.9% progress, only one level can pass.
    hard_cap = max(1, int(required * 0.42 / downstream))
    rank = _encounter_rank_v1286(template)
    if level <= 100:
        # Preserve the original early-game reward (including its +30%), but
        # never hand low-level players a near-complete level for one mob.
        early_limit = {
            "normal": .06, "elite": .10, "rare": .14,
            "mini": .18, "boss": .25, "world_boss": .30,
        }[rank]
        return min(prior_xp, hard_cap, max(1, int(required * early_limit / downstream)))

    try:
        stage = int(template.get("generator_level", template.get("v019_stage", 0)) or 0)
        if stage <= 0:
            stage = authored_dungeon_floor_v1285(template)
    except (ValueError, TypeError, OverflowError):
        stage = authored_dungeon_floor_v1285(template)
    stage = max(1, min(800, stage))
    gap = stage - level
    if gap >= 0:
        challenge = 1.0 + min(150, gap) / 600.0  # risk premium up to +25%
    else:
        challenge = max(0.25, 1.0 + max(-400, gap) / 500.0)
    try:
        mult = max(0.25, min(1.75, float(combat_multiplier)))
    except (ValueError, TypeError, OverflowError):
        mult = 1.0
    expected = max(1, math.ceil(
        required / _target_kills_for_level_v1285(level)
        * _RANK_BONUS[rank] * challenge * mult
    ))
    # Preserve up to 20% of additional authored/rare reward variance, but
    # never grant the old floor-800 exponential reward to a level-150 player.
    payout = max(expected, min(prior_xp, math.ceil(expected * 1.20)))
    return min(SAFE_XP, hard_cap, payout)


def dungeon_kill_xp_audit_v1285():
    failures = []
    normal = {"crypt_floor": 600, "generator_level": 600}
    boss = {**normal, "crypt_boss": True}
    for axis in ("character", "class", "soul", "stat"):
        if dungeon_kill_xp_v1285({"crypt_floor": 10}, axis, 100) != 130:
            failures.append(f"{axis}: 30% early bonus broken")
        if dungeon_kill_xp_v1285({"generator_level": 600}, axis, 100) != 100:
            failures.append(f"{axis}: open world modified")
        if dungeon_kill_xp_v1285({**normal, "source_xp_exact": True}, axis, 100) != 100:
            failures.append(f"{axis}: exact reward modified")
    for axis, requirement in _REQUIREMENTS.items():
        for lvl in (1, 50, 100, 101, 150, 200, 400, 600, 799):
            value = dungeon_recipient_xp_v1286(normal, axis, SAFE_XP, lvl,
                                               combat_multiplier=50,
                                               downstream_multiplier=4)
            needed = requirement(lvl)
            if not 0 < value * 4 <= math.ceil(needed * .42) + 4:
                failures.append(f"{axis}: explosion at level {lvl}: {value}")
        for lvl in (150, 200, 400, 600, 799):
            a = dungeon_recipient_xp_v1286(normal, axis, 1, lvl)
            b = dungeon_recipient_xp_v1286(boss, axis, 1, lvl)
            if b <= a:
                failures.append(f"{axis}: no boss premium at {lvl}")
    if dungeon_recipient_xp_v1286(normal, "character", 123, 150) <= 123:
        failures.append("high-level floor missing catch-up reward")
    if dungeon_recipient_xp_v1286({**normal, "source_xp_exact": True}, "character", 12345, 150) != 12345:
        failures.append("UOSS exact changed")
    if dungeon_recipient_xp_v1286({"generator_level": 600}, "character", 12345, 150) != 12345:
        failures.append("open-world changed")
    return {"ok": not failures, "failures": failures}
