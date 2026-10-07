# -*- coding: utf-8 -*-
"""Soulbound v0.50.1 - progression pace rebalance audit."""
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
from core import generator_core as generator_core_v027
from core.progression_resources import (
    character_xp_to_next,
    class_mastery_xp_to_next,
    soul_weapon_mastery_xp_to_next,
    soul_xp_to_next,
)
from player.session_mixins.profession_storage import SessionProfessionStorageMixin


def progression_pace_audit_v0501():
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
        errors.append("Górnictwo requirement multiplier must be 2.0")
    if float(TOOL_XP_REQUIREMENT_MULTIPLIERS.get("mining", 0.0)) != 2.0:
        errors.append("Kilof/mining requirement multiplier must be 2.0")

    # Other gathering professions/tools stay unchanged by this player-axis rebalance.
    for profession in ("Wędkarstwo", "Drwalstwo", "Zielarstwo"):
        if float(PROFESSION_XP_REQUIREMENT_MULTIPLIERS.get(profession, 1.0)) != 1.0:
            errors.append(f"unexpected profession pace override: {profession}")
    for tool_type in ("fishing", "woodcutting", "herbalism"):
        if float(TOOL_XP_REQUIREMENT_MULTIPLIERS.get(tool_type, 1.0)) != 1.0:
            errors.append(f"unexpected tool pace override: {tool_type}")

    dummy = SessionProfessionStorageMixin.__new__(SessionProfessionStorageMixin)
    samples = (1, 10, 100, 300, 599)
    for level in samples:
        char_base = generator_core_v027.axis_requirement("character", level)
        if character_xp_to_next(level) != int(round(char_base * 4.0)):
            errors.append(f"character requirement mismatch at level {level}")

        class_base = generator_core_v027.axis_requirement("class", level)
        if class_mastery_xp_to_next(level) != int(round(class_base * 3.0)):
            errors.append(f"class requirement mismatch at level {level}")

        soul_base = generator_core_v027.axis_requirement("soul", level)
        if soul_xp_to_next(level) != int(round(soul_base * 3.0)):
            errors.append(f"soul requirement mismatch at level {level}")

        skill_base = generator_core_v027.axis_requirement("skill", level)
        if soul_weapon_mastery_xp_to_next(level) != int(round(skill_base * 3.0)):
            errors.append(f"soul weapon mastery requirement mismatch at level {level}")

        prof_base = generator_core_v027.axis_requirement("profession", level)
        if dummy.profession_xp_to_next(level, "Górnictwo") != int(round(prof_base * 2.0)):
            errors.append(f"mining profession requirement mismatch at level {level}")
        if dummy.profession_xp_to_next(level, "Wędkarstwo") != prof_base:
            errors.append(f"non-mining profession changed at level {level}")

        tool_base = generator_core_v027.axis_requirement("tool", level)
        if dummy.tool_xp_to_next(level, "mining") != int(round(tool_base * 2.0)):
            errors.append(f"pickaxe requirement mismatch at level {level}")
        if dummy.tool_xp_to_next(level, "fishing") != tool_base:
            errors.append(f"non-mining tool changed at level {level}")

    # Effective equal-stage pace before race/guild/event bonuses.
    expected_actions = {
        "character": generator_core_v027.AXIS_TARGET_ACTIONS["character"] * 4,
        "class": generator_core_v027.AXIS_TARGET_ACTIONS["class"] * 3,
        "soul": generator_core_v027.AXIS_TARGET_ACTIONS["soul"] * 3,
        "soul_weapon_mastery": generator_core_v027.AXIS_TARGET_ACTIONS["skill"] * 3,
        "stat": int(round(
            generator_core_v027.AXIS_TARGET_ACTIONS["stat"]
            * STAT_XP_REQUIREMENT_MULTIPLIER
            / STAT_XP_REWARD_MULTIPLIER
        )),
        "mining_profession": generator_core_v027.AXIS_TARGET_ACTIONS["profession"] * 2,
        "pickaxe": generator_core_v027.AXIS_TARGET_ACTIONS["tool"] * 2,
    }
    if expected_actions != {
        "character": 72,
        "class": 48,
        "soul": 75,
        "soul_weapon_mastery": 54,
        "stat": 60,
        "mining_profession": 100,
        "pickaxe": 130,
    }:
        errors.append(f"unexpected target action model: {expected_actions}")

    return {
        "version": "0.50.1",
        "error_count": len(errors),
        "errors": errors,
        "requirement_multipliers": actual_multipliers,
        "mining_requirement_multiplier": float(
            PROFESSION_XP_REQUIREMENT_MULTIPLIERS["Górnictwo"]
        ),
        "pickaxe_requirement_multiplier": float(
            TOOL_XP_REQUIREMENT_MULTIPLIERS["mining"]
        ),
        "target_actions": expected_actions,
    }


PROGRESSION_PACE_AUDIT_V0501 = progression_pace_audit_v0501()
if PROGRESSION_PACE_AUDIT_V0501["error_count"]:
    raise RuntimeError(
        "Progression Pace Audit v0.50.1 failed: "
        + "; ".join(PROGRESSION_PACE_AUDIT_V0501["errors"][:100])
    )
