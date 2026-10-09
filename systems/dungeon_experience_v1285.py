# -*- coding: utf-8 -*-
"""Explicit, dungeon-only kill XP catch-up for Soulbound v1.28.5.

Past level 100, permanent XP requirements grow exponentially while the
original floor rewards grow polynomially. Keep deeper floors worth playing
without reintroducing Generator Core or touching authored mob/item catalogs.
"""

from __future__ import annotations

import math
from core.progression_resources import (
    character_xp_to_next,
    class_mastery_xp_to_next,
    soul_xp_to_next,
)
from core.player_math import stat_xp_requirement

SAFE_XP = 9_000_000_000_000_000_000
_DUNGEON_FLOOR_KEYS = (
    "crypt_floor", "mythic_crypt_floor",
    "astral_floor", "mythic_astral_floor",
    "magitek_floor", "giant_fortress_floor", "profession_dungeon_floor",
)
_BOSS_KEYS = (
    "crypt_boss", "mythic_crypt_boss", "astral_boss", "mythic_astral_boss",
    "magitek_boss", "giant_fortress_boss", "profession_dungeon_boss",
    "boss", "world_boss", "boss_mechanic", "mini_boss",
)


def authored_dungeon_floor_v1285(template):
    """Only explicit dungeon encounters receive the bonus, not the open world."""
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
    """Deliberately grindy: 48 at 150, 65 at 200, 190 at 800."""
    stage = max(1, int(stage))
    if stage <= 100:
        return 36
    if stage <= 150:
        return 36 + (stage - 100) * (12 / 50)
    if stage <= 200:
        return 48 + (stage - 150) * (17 / 50)
    return 65 + (stage - 200) * (125 / 600)


def dungeon_kill_xp_v1285(template, axis, prior_xp):
    """Final additive reward minimum: no existing drop/reward is reduced.

    Called AFTER legacy crypt, tower and global difficulty rewards. This
    cannot compound on respawn since the result isn't written to mob templates.
    Bosses have a separate, higher floor; they remain special milestones.
    Exact-source UOSS rewards are handled separately by combat_rewards.py.
    """
    prior_xp = max(0, int(prior_xp or 0))
    if axis not in {"character", "class", "soul", "stat"}:
        return prior_xp
    floor = authored_dungeon_floor_v1285(template)
    if floor < 1 or template.get("training_dummy") or template.get("source_xp_exact"):
        return prior_xp
    # Modest boost even on floors 1..100, without modifying progression costs.
    result = min(SAFE_XP, int(round(prior_xp * 1.30)))
    if axis == "stat":
        # Uncapped stat progression scales separately with actual stat level;
        # using Character/Soul requirements here would overfeed every stat.
        return result

    # These axes have a hard level-800 cap. Floor 800+ remains worthwhile for
    # level-799 players, and depth beyond 800 still improves the reward.
    stage = template.get("generator_level", template.get("v019_stage"))
    try:
        stage = min(799, max(1, int(stage if stage is not None else floor)))
    except (ValueError, TypeError, OverflowError):
        stage = min(799, max(1, floor))
    if stage <= 100:
        return result

    requirements = {
        "character": character_xp_to_next,
        "class": class_mastery_xp_to_next,
        "soul": soul_xp_to_next,
    }
    required = int(requirements[axis](stage))
    kills = _target_kills_for_level_v1285(stage)
    boss = any(bool(template.get(key)) for key in _BOSS_KEYS) or str(template.get("rank", "")).lower() in ("boss", "world_boss", "mini")
    if boss:
        kills = max(4.0, kills / 16.0)
    target = math.ceil(required / kills)
    if floor > 799:
        # Progress in truly endless floors must not stall when Level caps at 800.
        target = int(math.ceil(target * (1.0 + (floor - 799) / 500.0)))
    return min(SAFE_XP, max(result, target))


def dungeon_kill_xp_audit_v1285():
    """Cheap standalone numeric audit without a game server or SQLite."""
    failures = []
    for axis in ("character", "class", "soul", "stat"):
        if dungeon_kill_xp_v1285({"crypt_floor": 10, "generator_level": 10}, axis, 100) <= 100:
            failures.append(f"{axis}: early floor missing bonus")
        if dungeon_kill_xp_v1285({"generator_level": 600}, axis, 100) != 100:
            failures.append(f"{axis}: overwrote open world")
        if dungeon_kill_xp_v1285({"crypt_floor": 600, "generator_level": 600, "source_xp_exact": True}, axis, 100) != 100:
            failures.append(f"{axis}: overwrote exact UOSS XP")
    for axis in ("character", "class", "soul"):
        previous = 0
        for floor in range(101, 1101):
            current = dungeon_kill_xp_v1285({"crypt_floor": floor, "generator_level": min(800, floor)}, axis, 100)
            if current < previous:
                failures.append(f"{axis}: floor {floor} lower than previous")
                break
            previous = current
        at_600 = dungeon_kill_xp_v1285({"crypt_floor": 600, "generator_level": 600}, axis, 100)
        at_600_boss = dungeon_kill_xp_v1285({"crypt_floor": 600, "generator_level": 600, "crypt_boss": True}, axis, 100)
        if at_600_boss <= at_600:
            failures.append(f"{axis}: no boss premium")
    return {"ok": not failures, "failures": failures}
