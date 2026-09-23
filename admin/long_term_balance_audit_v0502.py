# -*- coding: utf-8 -*-
"""Soulbound v0.50.2 - long-term progression/stat balance audit."""
from types import SimpleNamespace

from config.balance import (
    CHARACTER_XP_REQUIREMENT_MULTIPLIER,
    PROFESSION_XP_REQUIREMENT_MULTIPLIERS,
    STAT_XP_REQUIREMENT_MULTIPLIER,
    TOOL_XP_REQUIREMENT_MULTIPLIERS,
)
from core import generator_core as generator_core_v027
from player.character import Character


def _effective_stat_actions(level: int) -> float:
    level = max(1, int(level))
    dummy = SimpleNamespace(
        STAT_PROGRESS_FIELDS=Character.STAT_PROGRESS_FIELDS,
        strength=level,
    )
    threshold = Character.stat_growth_threshold_for(dummy, "strength")
    if level <= generator_core_v027.MAX_LEVEL:
        gain = generator_core_v027.axis_gain("stat", level, 1.0)
    else:
        anchor_gain = generator_core_v027.axis_gain("stat", generator_core_v027.MAX_LEVEL, 1.0)
        gain = generator_core_v027.uncapped_stat_xp_gain(anchor_gain, level)
    return float(threshold) / max(1.0, float(gain))


def long_term_balance_audit_v0502():
    errors = []

    if float(STAT_XP_REQUIREMENT_MULTIPLIER) != 2.0:
        errors.append("stat requirement multiplier must be 2.0")
    if float(CHARACTER_XP_REQUIREMENT_MULTIPLIER) != 2.0:
        errors.append("character requirement multiplier regressed from 2.0")
    if float(PROFESSION_XP_REQUIREMENT_MULTIPLIERS.get("Górnictwo", 0.0)) != 2.0:
        errors.append("mining profession multiplier regressed from 2.0")
    if float(TOOL_XP_REQUIREMENT_MULTIPLIERS.get("mining", 0.0)) != 2.0:
        errors.append("pickaxe multiplier regressed from 2.0")

    targets = {
        "character": int(generator_core_v027.AXIS_TARGET_ACTIONS["character"] * CHARACTER_XP_REQUIREMENT_MULTIPLIER),
        "class": int(generator_core_v027.AXIS_TARGET_ACTIONS["class"]),
        "soul": int(generator_core_v027.AXIS_TARGET_ACTIONS["soul"]),
        "skill": int(generator_core_v027.AXIS_TARGET_ACTIONS["skill"]),
        "profession": int(generator_core_v027.AXIS_TARGET_ACTIONS["profession"]),
        "tool": int(generator_core_v027.AXIS_TARGET_ACTIONS["tool"]),
        "stat": int(generator_core_v027.AXIS_TARGET_ACTIONS["stat"] * STAT_XP_REQUIREMENT_MULTIPLIER),
        "mining_profession": int(generator_core_v027.AXIS_TARGET_ACTIONS["profession"] * PROFESSION_XP_REQUIREMENT_MULTIPLIERS["Górnictwo"]),
        "pickaxe": int(generator_core_v027.AXIS_TARGET_ACTIONS["tool"] * TOOL_XP_REQUIREMENT_MULTIPLIERS["mining"]),
    }
    expected = {
        "character": 36, "class": 16, "soul": 25, "skill": 18,
        "profession": 50, "tool": 65, "stat": 120,
        "mining_profession": 100, "pickaxe": 130,
    }
    if targets != expected:
        errors.append(f"unexpected long-term action targets: {targets}")

    # Stats are uncapped. A matching-stage source should stay around 120 actions
    # per point both inside and beyond the 1-600 capped progression space.
    stat_action_samples = {}
    for level in (10, 100, 300, 599, 800, 1200):
        actions = _effective_stat_actions(level)
        stat_action_samples[level] = round(actions, 3)
        if not (117.0 <= actions <= 123.0):
            errors.append(f"stat pace mismatch at value {level}: {actions:.3f} actions")

    # Long-form axes: approximate equal-stage actions from level 1 to 600.
    steps = max(1, int(generator_core_v027.MAX_LEVEL) - 1)
    actions_to_600 = {
        "character": targets["character"] * steps,
        "class": targets["class"] * steps,
        "soul": targets["soul"] * steps,
        "skill_one": targets["skill"] * steps,
        "profession_one": targets["profession"] * steps,
        "tool_one": targets["tool"] * steps,
        "mining": targets["mining_profession"] * steps,
        "pickaxe": targets["pickaxe"] * steps,
    }
    minimums = {
        "character": 20_000,
        "class": 9_000,
        "soul": 14_000,
        "skill_one": 10_000,
        "profession_one": 29_000,
        "tool_one": 38_000,
        "mining": 59_000,
        "pickaxe": 77_000,
    }
    for key, minimum in minimums.items():
        if actions_to_600[key] < minimum:
            errors.append(f"{key} progression too short: {actions_to_600[key]} < {minimum}")

    # At Character Level 600 the level component contributes +180 attribute power.
    # With 36 equal-stage rewards/level and 120 rewards/stat point, the same journey
    # yields about +180 base points in each stat. Neither axis runs away from the other.
    level_power_contribution = generator_core_v027.character_attribute_power(600, 1) - 1
    expected_stat_points_during_character_path = actions_to_600["character"] / float(targets["stat"])
    parity = expected_stat_points_during_character_path / max(1.0, float(level_power_contribution))
    if not (0.90 <= parity <= 1.10):
        errors.append(
            f"character/stat power pace diverged: level contribution={level_power_contribution}, "
            f"expected stat points={expected_stat_points_during_character_path:.2f}, ratio={parity:.3f}"
        )

    return {
        "version": "0.50.2",
        "error_count": len(errors),
        "errors": errors,
        "target_actions": targets,
        "actions_to_600": actions_to_600,
        "stat_action_samples": stat_action_samples,
        "character_level_power_contribution": int(level_power_contribution),
        "expected_stat_points_during_character_path": round(expected_stat_points_during_character_path, 3),
        "character_stat_power_parity": round(parity, 4),
    }


LONG_TERM_BALANCE_AUDIT_V0502 = long_term_balance_audit_v0502()
if LONG_TERM_BALANCE_AUDIT_V0502["error_count"]:
    raise RuntimeError(
        "Long-Term Balance Audit v0.50.2 failed: "
        + "; ".join(LONG_TERM_BALANCE_AUDIT_V0502["errors"][:100])
    )
