"""Authored profession action timing for Soulbound v1.13.16.

Profession tempo is gameplay design, not procedural Generator Core output.
The original eight professions keep their authored timers; newer professions
freeze explicit values instead of deriving them from a name hash.
"""
from __future__ import annotations

from config.balance import PROFESSION_SPEED_CAP_LEVEL

TOOL_ACTION_BASE_SECONDS = {
    "fishing": 16,
    "mining": 40,
    "woodcutting": 24,
    "crafting": 20,
    "cooking": 12,
    "herbalism": 10,
    "alchemy": 18,
    "jewelcrafting": 20,
    "tailoring": 20,
    "leatherworking": 22,
    "carpentry": 25,
    "enchanting": 21,
    "archaeology": 20,
    "cartography_profession": 14,
    "hunting": 22,
    "farming": 28,
    "animal_husbandry": 26,
    "shipbuilding": 38,
    "masonry": 30,
    "engineering": 36,
    "trading": 25,
    "sailing": 40,
}

TOOL_ACTION_MIN_SECONDS = {
    "fishing": 3,
    "mining": 10,
    "woodcutting": 8,
    "crafting": 7,
    "cooking": 4,
    "herbalism": 3,
    "alchemy": 6,
    "jewelcrafting": 7,
    "tailoring": 4,
    "leatherworking": 3,
    "carpentry": 6,
    "enchanting": 7,
    "archaeology": 5,
    "cartography_profession": 3,
    "hunting": 5,
    "farming": 6,
    "animal_husbandry": 6,
    "shipbuilding": 9,
    "masonry": 7,
    "engineering": 9,
    "trading": 5,
    "sailing": 8,
}


def profession_speed_progress(level: int) -> float:
    effective = max(
        1, min(PROFESSION_SPEED_CAP_LEVEL, int(level or 1))
    )
    return (effective - 1) / float(
        max(1, PROFESSION_SPEED_CAP_LEVEL - 1)
    )


def profession_action_seconds(tool_type: str, level: int) -> int:
    tool_type = str(tool_type or "")
    base = int(TOOL_ACTION_BASE_SECONDS.get(tool_type, 20))
    minimum = int(TOOL_ACTION_MIN_SECONDS.get(tool_type, 5))
    progress = profession_speed_progress(level)
    seconds = round(base - (base - minimum) * progress)
    return max(minimum, int(seconds))


if (
    profession_action_seconds("fishing", 1) != 16
    or profession_action_seconds("fishing", PROFESSION_SPEED_CAP_LEVEL) != 3
    or profession_action_seconds("mining", 1) != 40
    or profession_action_seconds("mining", PROFESSION_SPEED_CAP_LEVEL) != 10
):
    raise RuntimeError("Authored profession timing audit failed")
