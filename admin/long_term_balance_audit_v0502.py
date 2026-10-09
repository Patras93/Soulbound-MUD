# -*- coding: utf-8 -*-
"""Soulbound v0.50.2 - long-term progression/stat balance audit."""
from types import SimpleNamespace

from config.balance import (
    CHARACTER_XP_REQUIREMENT_MULTIPLIER,
    CLASS_MASTERY_XP_REQUIREMENT_MULTIPLIER,
    PROFESSION_XP_REQUIREMENT_MULTIPLIERS,
    SOUL_WEAPON_MASTERY_XP_REQUIREMENT_MULTIPLIER,
    SOUL_XP_REQUIREMENT_MULTIPLIER,
    STAT_XP_REQUIREMENT_MULTIPLIER,
    STAT_XP_REWARD_MULTIPLIER,
    TOOL_XP_REQUIREMENT_MULTIPLIERS,
)
from core import balance_math
from core.progression_resources import cap_single_level_xp_gain_v11342
from player.character import Character


def _effective_stat_actions(level: int) -> float:
    level = max(1, int(level))
    dummy = SimpleNamespace(
        STAT_PROGRESS_FIELDS=Character.STAT_PROGRESS_FIELDS,
        strength=level,
    )
    threshold = Character.stat_growth_threshold_for(dummy, "strength")
    if level <= balance_math.MAX_LEVEL:
        gain = balance_math.axis_gain("stat", level, 1.0)
    else:
        anchor_gain = balance_math.axis_gain(
            "stat", balance_math.MAX_LEVEL, 1.0
        )
        gain = balance_math.uncapped_stat_xp_gain(anchor_gain, level)
    effective_gain = float(gain) * float(STAT_XP_REWARD_MULTIPLIER)
    return float(threshold) / max(1.0, effective_gain)


def long_term_balance_audit_v0502():
    errors = []

    expected_multipliers = {
        "character": 4.0,
        "class": 3.0,
        "soul": 3.0,
        "soul_weapon_mastery": 3.0,
        "stat_requirement": 4.0,
        "stat_reward": 4.0,
    }
    actual_multipliers = {
        "character": float(CHARACTER_XP_REQUIREMENT_MULTIPLIER),
        "class": float(CLASS_MASTERY_XP_REQUIREMENT_MULTIPLIER),
        "soul": float(SOUL_XP_REQUIREMENT_MULTIPLIER),
        "soul_weapon_mastery": float(SOUL_WEAPON_MASTERY_XP_REQUIREMENT_MULTIPLIER),
        "stat_requirement": float(STAT_XP_REQUIREMENT_MULTIPLIER),
        "stat_reward": float(STAT_XP_REWARD_MULTIPLIER),
    }
    if actual_multipliers != expected_multipliers:
        errors.append(
            f"long-term progression multipliers mismatch: {actual_multipliers}"
        )
    if float(PROFESSION_XP_REQUIREMENT_MULTIPLIERS.get("Górnictwo", 0.0)) != 2.0:
        errors.append("mining profession multiplier regressed from 2.0")
    if float(TOOL_XP_REQUIREMENT_MULTIPLIERS.get("mining", 0.0)) != 2.0:
        errors.append("pickaxe multiplier regressed from 2.0")

    targets = {
        "character": int(
            balance_math.AXIS_TARGET_ACTIONS["character"]
            * CHARACTER_XP_REQUIREMENT_MULTIPLIER
        ),
        "class": int(
            balance_math.AXIS_TARGET_ACTIONS["class"]
            * CLASS_MASTERY_XP_REQUIREMENT_MULTIPLIER
        ),
        "soul": int(
            balance_math.AXIS_TARGET_ACTIONS["soul"]
            * SOUL_XP_REQUIREMENT_MULTIPLIER
        ),
        "soul_weapon_mastery": int(
            balance_math.AXIS_TARGET_ACTIONS["skill"]
            * SOUL_WEAPON_MASTERY_XP_REQUIREMENT_MULTIPLIER
        ),
        "skill": int(balance_math.AXIS_TARGET_ACTIONS["skill"]),
        "profession": int(balance_math.AXIS_TARGET_ACTIONS["profession"]),
        "tool": int(balance_math.AXIS_TARGET_ACTIONS["tool"]),
        "stat": int(round(
            balance_math.AXIS_TARGET_ACTIONS["stat"]
            * STAT_XP_REQUIREMENT_MULTIPLIER
            / max(0.000001, float(STAT_XP_REWARD_MULTIPLIER))
        )),
        "mining_profession": int(
            balance_math.AXIS_TARGET_ACTIONS["profession"]
            * PROFESSION_XP_REQUIREMENT_MULTIPLIERS["Górnictwo"]
        ),
        "pickaxe": int(
            balance_math.AXIS_TARGET_ACTIONS["tool"]
            * TOOL_XP_REQUIREMENT_MULTIPLIERS["mining"]
        ),
    }
    expected = {
        "character": 72,
        "class": 48,
        "soul": 75,
        "soul_weapon_mastery": 54,
        "skill": 18,
        "profession": 50,
        "tool": 65,
        "stat": 60,
        "mining_profession": 100,
        "pickaxe": 130,
    }
    if targets != expected:
        errors.append(f"unexpected long-term action targets: {targets}")

    # Uncapped stats now target roughly 60 matching-stage kills per permanent
    # point both inside and beyond the capped 1-600 level space.
    stat_action_samples = {}
    for level in (10, 100, 300, 599, 800, 1200):
        actions = _effective_stat_actions(level)
        stat_action_samples[level] = round(actions, 3)
        if not (58.0 <= actions <= 62.0):
            errors.append(
                f"stat pace mismatch at value {level}: {actions:.3f} actions"
            )

    # One combat reward may finish the current level but cannot bank overflow
    # for several later levels.
    cap_samples = {
        "fresh": cap_single_level_xp_gain_v11342(0, 1000, 999999),
        "near": cap_single_level_xp_gain_v11342(750, 1000, 999999),
        "small": cap_single_level_xp_gain_v11342(750, 1000, 100),
        "maxed": cap_single_level_xp_gain_v11342(0, 0, 999999),
    }
    if cap_samples != {
        "fresh": 1000,
        "near": 250,
        "small": 100,
        "maxed": 0,
    }:
        errors.append(f"single-level combat cap regression: {cap_samples}")

    steps = max(1, int(balance_math.MAX_LEVEL) - 1)
    actions_to_600 = {
        "character": targets["character"] * steps,
        "class": targets["class"] * steps,
        "soul": targets["soul"] * steps,
        "soul_weapon_mastery": targets["soul_weapon_mastery"] * steps,
        "skill_one": targets["skill"] * steps,
        "profession_one": targets["profession"] * steps,
        "tool_one": targets["tool"] * steps,
        "mining": targets["mining_profession"] * steps,
        "pickaxe": targets["pickaxe"] * steps,
    }
    minimums = {
        "character": 43_000,
        "class": 28_500,
        "soul": 44_500,
        "soul_weapon_mastery": 32_000,
        "skill_one": 10_000,
        "profession_one": 29_000,
        "tool_one": 38_000,
        "mining": 59_000,
        "pickaxe": 77_000,
    }
    for key, minimum in minimums.items():
        if actions_to_600[key] < minimum:
            errors.append(
                f"{key} progression too short: {actions_to_600[key]} < {minimum}"
            )

    # Character Level itself still gives no hidden offensive stat power.
    level_power_contribution = (
        balance_math.character_attribute_power(600, 1) - 1
    )
    expected_stat_points_during_character_path = (
        actions_to_600["character"] / float(targets["stat"])
    )
    parity = 0.0
    if level_power_contribution != 0:
        errors.append(
            f"Character Level grants hidden attribute power again: "
            f"{level_power_contribution}"
        )
    if expected_stat_points_during_character_path <= 0:
        errors.append("stat growth during Character Level progression disappeared")

    return {
        "version": "0.50.2",
        "error_count": len(errors),
        "errors": errors,
        "target_actions": targets,
        "actions_to_600": actions_to_600,
        "stat_action_samples": stat_action_samples,
        "single_level_cap_samples": cap_samples,
        "character_level_power_contribution": int(level_power_contribution),
        "expected_stat_points_during_character_path": round(
            expected_stat_points_during_character_path, 3
        ),
        "character_stat_power_parity": round(parity, 4),
    }


LONG_TERM_BALANCE_AUDIT_V0502 = long_term_balance_audit_v0502()
if LONG_TERM_BALANCE_AUDIT_V0502["error_count"]:
    raise RuntimeError(
        "Long-Term Balance Audit v0.50.2 failed: "
        + "; ".join(LONG_TERM_BALANCE_AUDIT_V0502["errors"][:100])
    )
