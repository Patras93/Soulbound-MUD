"""Authored player combat/progression math for Soulbound v1.13.16.

Player identity math is not procedural content. These formulas are explicit,
stable and independent from Generator Core. Generator may expose compatibility
wrappers, but normal character/combat runtime imports this module directly.
"""
from __future__ import annotations

import math

PLAYER_MATH_MAX_LEVEL = 600
SAFE_INT = 9_000_000_000_000_000_000
STAT_XP_CURVE = (100.0, 29.0, 1.70)


LATE_GAME_XP_START_LEVEL = 100
LATE_GAME_XP_TARGET_LEVEL = 599
LATE_GAME_XP_TARGET_REQUIREMENT = 10_000_000_000_000
LATE_GAME_XP_CURVE_POWER = 0.55

def late_game_xp_requirement(
    level: int,
    base_requirement: int,
    terminal_base_requirement: int,
) -> int:
    """Scale a permanent progression axis strongly after level 100.

    The authored requirement is unchanged through level 100. From 101 onward
    it receives a strong exponential multiplier that is already clearly felt at
    level 101, chosen so the requirement at level 599 reaches roughly ten trillion XP. Rewards are not scaled here.
    For uncapped stats the same curve continues beyond 599 until SAFE_INT.
    """
    level = max(1, int(level or 1))
    base_requirement = max(1, int(base_requirement or 1))
    terminal_base = max(1, int(terminal_base_requirement or 1))
    if level <= LATE_GAME_XP_START_LEVEL:
        return base_requirement

    span = float(max(1, LATE_GAME_XP_TARGET_LEVEL - LATE_GAME_XP_START_LEVEL))
    progress = max(0.0, (level - LATE_GAME_XP_START_LEVEL) / span)
    exponent = progress ** LATE_GAME_XP_CURVE_POWER
    terminal_multiplier = max(1.0, LATE_GAME_XP_TARGET_REQUIREMENT / float(terminal_base))
    multiplier = math.exp(math.log(terminal_multiplier) * exponent)
    value = base_requirement * multiplier
    return min(SAFE_INT, max(base_requirement, int(round(value))))


def _clamp(value, low, high):
    return max(low, min(high, value))


def stat_xp_requirement(stat_level: int) -> int:
    level = max(1, int(stat_level or 1))
    base, growth, power = STAT_XP_CURVE
    value = base + growth * (level ** power)
    return min(SAFE_INT, max(1, int(round(value))))


def uncapped_stat_xp_scale(stat_level: int) -> float:
    """Keep current rewards through 600, then scale with the uncapped stat cost."""
    level = max(1, int(stat_level or 1))
    if level <= PLAYER_MATH_MAX_LEVEL:
        return 1.0
    anchor = float(stat_xp_requirement(PLAYER_MATH_MAX_LEVEL))
    current = float(stat_xp_requirement(level))
    return max(1.0, current / max(1.0, anchor))


def uncapped_stat_xp_gain(base_amount: int, stat_level: int) -> int:
    base_amount = max(0, int(base_amount or 0))
    if base_amount <= 0:
        return 0
    return min(
        SAFE_INT,
        max(1, int(round(base_amount * uncapped_stat_xp_scale(stat_level)))),
    )


def character_attribute_power(character_level: int, stat_value: int) -> int:
    """Character Level unlocks content; actual trained/equipped stat gives power."""
    _ = _clamp(int(character_level or 1), 1, PLAYER_MATH_MAX_LEVEL)
    return max(1, int(stat_value or 1))


def character_offensive_build_multiplier(stat_value: int | float) -> float:
    stat_value = max(1.0, float(stat_value or 1.0))
    if stat_value <= 100.0:
        return 1.0
    growth = 1.0 + 0.45 * (((stat_value - 100.0) / 100.0) ** 0.72)
    return round(max(1.0, growth), 6)


def speed_from_dexterity(dexterity: int) -> int:
    dexterity = max(1, int(dexterity or 1))
    return max(1, int(round(8 + dexterity * 1.65)))


def basic_attack_hits_from_speed(speed: int, haste: bool = False) -> int:
    speed = max(1, int(speed or 1))
    raw_hits = math.sqrt(float(speed)) / 5.8
    if haste:
        raw_hits *= 2.0
    return max(1, int(raw_hits))


def basic_attack_hits_from_dexterity(
    dexterity: int, haste: bool = False
) -> int:
    return basic_attack_hits_from_speed(
        speed_from_dexterity(dexterity), haste=haste
    )


def mec_vmax_duration_seconds(skill_level: int, willpower: int) -> int:
    level = _clamp(int(skill_level or 1), 1, PLAYER_MATH_MAX_LEVEL)
    willpower = max(1, int(willpower or 1))
    progress = (level - 1) / float(max(1, PLAYER_MATH_MAX_LEVEL - 1))
    skill_seconds = 200.0 + 400.0 * (progress ** 0.82)
    will_multiplier = max(0.35, (willpower / 175.0) ** 0.50)
    return max(1, int(round(skill_seconds * will_multiplier)))


def dodge_from_dexterity(dexterity: int) -> float:
    dexterity = max(1, int(dexterity or 1))
    value = 0.25 * (
        1.0 - math.exp(-max(0.0, dexterity - 10.0) / 78.0)
    )
    return round(_clamp(value, 0.0, 0.25), 6)


def critical_chance_from_dexterity(dexterity: int) -> float:
    dexterity = max(1, int(dexterity or 1))
    # v1.13.16: authored DEX crit curve with a clean 40% ceiling.
    # DEX remains uncapped; crit itself approaches 40% with soft diminishing returns.
    value = 0.035 + 0.365 * (
        1.0 - math.exp(-max(0.0, dexterity - 8.0) / 105.0)
    )
    return round(_clamp(value, 0.035, 0.40), 6)


def critical_multiplier(character_level: int) -> float:
    level = _clamp(
        int(character_level or 1), 1, PLAYER_MATH_MAX_LEVEL
    )
    return round(
        1.45
        + 0.20
        * ((level - 1) / (PLAYER_MATH_MAX_LEVEL - 1)) ** 0.75,
        6,
    )


def physical_defense_base(character_level: int, constitution: int) -> int:
    level = _clamp(
        int(character_level or 1), 1, PLAYER_MATH_MAX_LEVEL
    )
    constitution = max(1, int(constitution or 1))
    return max(0, int(round(constitution * 0.42 + level * 0.08)))


def magic_defense_base(character_level: int, willpower: int) -> int:
    level = _clamp(
        int(character_level or 1), 1, PLAYER_MATH_MAX_LEVEL
    )
    willpower = max(1, int(willpower or 1))
    return max(0, int(round(willpower * 0.55 + level * 0.10)))


def skill_level_power(level: int) -> float:
    level = _clamp(int(level or 1), 1, PLAYER_MATH_MAX_LEVEL)
    return round(
        1.0
        + 3.0
        * ((level - 1) / (PLAYER_MATH_MAX_LEVEL - 1)) ** 0.82,
        6,
    )


def skill_cooldown_factor(level: int) -> float:
    level = _clamp(int(level or 1), 1, PLAYER_MATH_MAX_LEVEL)
    reduction = (
        0.50
        * ((level - 1) / (PLAYER_MATH_MAX_LEVEL - 1)) ** 0.90
    )
    return round(1.0 - reduction, 6)


_BASIC_ATTACK_AUDIT = {
    "speed_911": basic_attack_hits_from_speed(911, False),
    "speed_911_haste": basic_attack_hits_from_speed(911, True),
    "speed_716_haste": basic_attack_hits_from_speed(716, True),
}
if _BASIC_ATTACK_AUDIT != {
    "speed_911": 5,
    "speed_911_haste": 10,
    "speed_716_haste": 9,
}:
    raise RuntimeError("Player math basic-attack audit failed: " + repr(_BASIC_ATTACK_AUDIT))

_VMAX_AUDIT = {
    "level1_will175": mec_vmax_duration_seconds(1, 175),
    "level600_will175": mec_vmax_duration_seconds(600, 175),
    "level8_will344": mec_vmax_duration_seconds(8, 344),
}
if not (
    _VMAX_AUDIT["level1_will175"] == 200
    and _VMAX_AUDIT["level600_will175"] == 600
    and 285 <= _VMAX_AUDIT["level8_will344"] <= 310
):
    raise RuntimeError("Player math V-MAX audit failed: " + repr(_VMAX_AUDIT))

_CRIT_AUDIT = {
    "dex1": critical_chance_from_dexterity(1),
    "dex175": critical_chance_from_dexterity(175),
    "dex10000": critical_chance_from_dexterity(10_000),
}
if not (
    abs(_CRIT_AUDIT["dex1"] - 0.035) < 0.000001
    and 0.20 < _CRIT_AUDIT["dex175"] < 0.40
    and 0.399 <= _CRIT_AUDIT["dex10000"] <= 0.40
):
    raise RuntimeError("Player math critical-chance audit failed: " + repr(_CRIT_AUDIT))


_SKILL_POWER_AUDIT = {
    level: skill_level_power(level)
    for level in (1, 100, 200, 300, 400, 500, 600)
}
if (
    abs(_SKILL_POWER_AUDIT[1] - 1.0) > 0.000001
    or abs(_SKILL_POWER_AUDIT[600] - 4.0) > 0.000001
    or any(
        _SKILL_POWER_AUDIT[b] <= _SKILL_POWER_AUDIT[a]
        for a, b in zip(
            (1, 100, 200, 300, 400, 500),
            (100, 200, 300, 400, 500, 600),
        )
    )
):
    raise RuntimeError("Player math Skill Level audit failed: " + repr(_SKILL_POWER_AUDIT))
