# -*- coding: utf-8 -*-
"""Soulbound v0.50.2 - long-term progression/stat balance audit."""
from types import SimpleNamespace

from config.balance import (
    CHARACTER_XP_REQUIREMENT_MULTIPLIER,
    PROFESSION_XP_REQUIREMENT_MULTIPLIERS,
    STAT_XP_REQUIREMENT_MULTIPLIER,
    STAT_XP_REWARD_MULTIPLIER,
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
    # v1.13.5: Character.add_stat_progress applies the global stat reward
    # accelerator before race/guild bonuses and uncapped scaling. Long-term
    # balance must audit the effective player-facing pace, not the pre-boost
    # Generator Core source amount.
    effective_gain = float(gain) * float(STAT_XP_REWARD_MULTIPLIER)
    return float(threshold) / max(1.0, effective_gain)


def long_term_balance_audit_v0502():
    errors = []

    # v1.13.1+: uncapped stats intentionally use the natural requirement
    # curve plus a generous global x4 reward multiplier.
    if float(STAT_XP_REQUIREMENT_MULTIPLIER) != 1.0:
        errors.append("stat requirement multiplier must be 1.0")
    if float(STAT_XP_REWARD_MULTIPLIER) != 4.0:
        errors.append("stat reward multiplier must be 4.0")
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
        "stat": int(round(
            generator_core_v027.AXIS_TARGET_ACTIONS["stat"]
            * STAT_XP_REQUIREMENT_MULTIPLIER
            / max(0.000001, float(STAT_XP_REWARD_MULTIPLIER))
        )),
        "mining_profession": int(generator_core_v027.AXIS_TARGET_ACTIONS["profession"] * PROFESSION_XP_REQUIREMENT_MULTIPLIERS["Górnictwo"]),
        "pickaxe": int(generator_core_v027.AXIS_TARGET_ACTIONS["tool"] * TOOL_XP_REQUIREMENT_MULTIPLIERS["mining"]),
    }
    expected = {
        "character": 36, "class": 16, "soul": 25, "skill": 18,
        "profession": 50, "tool": 65, "stat": 15,
        "mining_profession": 100, "pickaxe": 130,
    }
    if targets != expected:
        errors.append(f"unexpected long-term action targets: {targets}")

    # Stats are uncapped. Since v1.13.1 a matching-stage source should stay
    # around 15 effective actions per point both inside and beyond the 1-600
    # capped progression space. The underlying Generator Core source remains
    # ~60 actions, then the global x4 reward accelerator makes it ~15.
    stat_action_samples = {}
    for level in (10, 100, 300, 599, 800, 1200):
        actions = _effective_stat_actions(level)
        stat_action_samples[level] = round(actions, 3)
        if not (14.0 <= actions <= 16.0):
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

    # v1.11.96+: Character Level no longer grants hidden offensive attribute
    # power. STR/DEX/INT/WILL are independent progression axes and must remain
    # valuable on their own. The Character Level journey can still coexist with
    # substantial stat growth, but parity is no longer measured against free
    # level-derived power because that contribution must be exactly zero.
    level_power_contribution = generator_core_v027.character_attribute_power(600, 1) - 1
    expected_stat_points_during_character_path = actions_to_600["character"] / float(targets["stat"])
    parity = 0.0
    if level_power_contribution != 0:
        errors.append(
            f"Character Level grants hidden attribute power again: {level_power_contribution}"
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
