# -*- coding: utf-8 -*-
"""Soulbound v0.50.1 - progression pace rebalance audit."""
from config.balance import (
    CHARACTER_XP_REQUIREMENT_MULTIPLIER,
    PROFESSION_XP_REQUIREMENT_MULTIPLIERS,
    TOOL_XP_REQUIREMENT_MULTIPLIERS,
)
from core import generator_core as generator_core_v027
from core.progression_resources import character_xp_to_next
from player.session_mixins.profession_storage import SessionProfessionStorageMixin


def progression_pace_audit_v0501():
    errors = []
    if float(CHARACTER_XP_REQUIREMENT_MULTIPLIER) != 2.0:
        errors.append("Character Level requirement multiplier must be 2.0")
    if float(PROFESSION_XP_REQUIREMENT_MULTIPLIERS.get("Górnictwo", 0.0)) != 2.0:
        errors.append("Górnictwo requirement multiplier must be 2.0")
    if float(TOOL_XP_REQUIREMENT_MULTIPLIERS.get("mining", 0.0)) != 2.0:
        errors.append("Kilof/mining requirement multiplier must be 2.0")

    # Other gathering professions/tools must stay unchanged by this targeted rebalance.
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
        if character_xp_to_next(level) != int(round(char_base * 2.0)):
            errors.append(f"character requirement mismatch at level {level}")

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

    # Effective target actions for equal-stage, unbonused gains.
    expected_actions = {
        "character": generator_core_v027.AXIS_TARGET_ACTIONS["character"] * 2,
        "mining_profession": generator_core_v027.AXIS_TARGET_ACTIONS["profession"] * 2,
        "pickaxe": generator_core_v027.AXIS_TARGET_ACTIONS["tool"] * 2,
    }
    if expected_actions != {"character": 36, "mining_profession": 100, "pickaxe": 130}:
        errors.append(f"unexpected target action model: {expected_actions}")

    return {
        "version": "0.50.1",
        "error_count": len(errors),
        "errors": errors,
        "character_requirement_multiplier": float(CHARACTER_XP_REQUIREMENT_MULTIPLIER),
        "mining_requirement_multiplier": float(PROFESSION_XP_REQUIREMENT_MULTIPLIERS["Górnictwo"]),
        "pickaxe_requirement_multiplier": float(TOOL_XP_REQUIREMENT_MULTIPLIERS["mining"]),
        "target_actions": expected_actions,
    }


PROGRESSION_PACE_AUDIT_V0501 = progression_pace_audit_v0501()
if PROGRESSION_PACE_AUDIT_V0501["error_count"]:
    raise RuntimeError(
        "Progression Pace Audit v0.50.1 failed: "
        + "; ".join(PROGRESSION_PACE_AUDIT_V0501["errors"][:100])
    )
