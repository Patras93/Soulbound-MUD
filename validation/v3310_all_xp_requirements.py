# -*- coding: utf-8 -*-
"""v3.31.4: requirement-only 10x over the legacy 3.30 progression.

Does not bootstrap or modify any database, accounts, rewards, equipment, or
Multi Cap. Every check uses the production requirement functions.
"""
from __future__ import annotations

from config.balance import (
    ALL_PROGRESS_XP_REQUIREMENT_MULTIPLIER_V3310 as MULTIPLIER,
    CHARACTER_XP_REQUIREMENT_MULTIPLIER,
    CLASS_MASTERY_XP_REQUIREMENT_MULTIPLIER,
    SOUL_XP_REQUIREMENT_MULTIPLIER,
    SOUL_WEAPON_MASTERY_XP_REQUIREMENT_MULTIPLIER,
    STAT_XP_REQUIREMENT_MULTIPLIER,
    PROFESSION_XP_REQUIREMENT_MULTIPLIERS,
    TOOL_XP_REQUIREMENT_MULTIPLIERS,
    profession_late_requirement_points_v1401,
    player_extra_requirement_points_v1407,
    stat_extra_requirement_points_v1408,
    profession_xp_requirement_v1401,
    tool_xp_requirement_v1402,
    scale_all_progress_requirements_v3310,
)
from core.progression_resources import (
    character_xp_to_next, class_mastery_xp_to_next, soul_xp_to_next,
    skill_xp_to_next, soul_weapon_mastery_xp_to_next, v0190_requirement,
)
from core.player_math import late_game_xp_requirement, SAFE_INT


def run_regression() -> int:
    checks = 0
    assert MULTIPLIER == 10
    checks += 1

    def prior_points(base: int, points: int) -> int:
        return min(SAFE_INT, max(1, (int(base) * int(points) + 5000) // 10000))

    # All 799 next-level requirements, not just a few example checkpoints.
    base_axes = (
        ('character', character_xp_to_next, 'character', CHARACTER_XP_REQUIREMENT_MULTIPLIER, True),
        ('class', class_mastery_xp_to_next, 'class', CLASS_MASTERY_XP_REQUIREMENT_MULTIPLIER, True),
        ('soul', soul_xp_to_next, 'soul', SOUL_XP_REQUIREMENT_MULTIPLIER, True),
        ('skill', skill_xp_to_next, 'skill', 1, False),
        ('weapon', soul_weapon_mastery_xp_to_next, 'skill', SOUL_WEAPON_MASTERY_XP_REQUIREMENT_MULTIPLIER, False),
    )
    for name, func, axis, mult, has_late_math in base_axes:
        previous = 0
        for level in range(1, 800):
            original = max(1, int(round(v0190_requirement(axis, level) * mult)))
            if has_late_math:
                terminal = max(1, int(round(v0190_requirement(axis, 599) * mult)))
                original = late_game_xp_requirement(level, original, terminal)
            before = prior_points(original, player_extra_requirement_points_v1407(level))
            expected = min(SAFE_INT, before * MULTIPLIER)
            actual = func(level)
            assert actual == expected, (name, level, actual, expected)
            assert actual >= previous, (name, level, 'threshold decreased')
            previous = actual
            checks += 2
        assert func(800) == 0, name
        checks += 1

    # Check every profession and tool through the same requirement functions
    # that their save/update methods and NVDA descriptions use.
    from validation.tool_xp_v1402 import TOOL_TYPES_V1402
    assert len(PROFESSION_XP_REQUIREMENT_MULTIPLIERS) == 14
    assert len(TOOL_TYPES_V1402) == 14
    checks += 2
    for name, multiplier in PROFESSION_XP_REQUIREMENT_MULTIPLIERS.items():
        previous = 0
        for level in range(1, 800):
            historical = max(1, int(round(v0190_requirement('profession', level) * multiplier)))
            before = prior_points(historical, profession_late_requirement_points_v1401(level))
            actual = profession_xp_requirement_v1401(v0190_requirement('profession', level), name, level)
            assert actual == min(SAFE_INT, before * MULTIPLIER), (name, level, actual, before)
            assert actual >= previous, (name, level)
            previous = actual
            checks += 2
    for tool in TOOL_TYPES_V1402:
        multiplier = TOOL_XP_REQUIREMENT_MULTIPLIERS.get(tool, 1.0)
        previous = 0
        for level in range(1, 800):
            historical = max(1, int(round(v0190_requirement('tool', level) * multiplier)))
            before = prior_points(historical, profession_late_requirement_points_v1401(level))
            actual = tool_xp_requirement_v1402(v0190_requirement('tool', level), tool, level)
            assert actual == min(SAFE_INT, before * MULTIPLIER), (tool, level, actual, before)
            assert actual >= previous, (tool, level)
            previous = actual
            checks += 2

    # Uncapped stats: canonical requirement stage for each of six stats is
    # identical. Test beyond 800, including safe-int saturation.
    for stat in ('strength', 'dexterity', 'constitution', 'intelligence', 'willpower', 'charisma'):
        for level in (1, 2, 10, 20, 49, 50, 100, 400, 599, 799, 800, 1000, 5000, 1000000):
            historical = max(1, int(round(v0190_requirement('stat', level) * STAT_XP_REQUIREMENT_MULTIPLIER)))
            terminal = max(1, int(round(v0190_requirement('stat', 599) * STAT_XP_REQUIREMENT_MULTIPLIER)))
            historical = late_game_xp_requirement(level, historical, terminal)
            before = prior_points(historical, stat_extra_requirement_points_v1408(level))
            from config.balance import scale_stat_requirement_v1408
            actual = scale_stat_requirement_v1408(historical, level)
            assert actual == min(SAFE_INT, before * MULTIPLIER), (stat, level, actual)
            assert actual > 0
            checks += 2

    # Ascension uses the same canonical player requirement scaler, indexed
    # by rank+1; its own 1000-rank cap is unaffected by this patch.
    for rank in (0, 1, 9, 49, 99, 199, 599, 799, 998):
        historical = 1_000_000 + rank * 1000
        from config.balance import scale_player_requirement_v1407
        actual = scale_player_requirement_v1407(historical, rank+1)
        previous = prior_points(historical, player_extra_requirement_points_v1407(rank+1))
        assert actual == min(SAFE_INT, previous * MULTIPLIER)
        checks += 1

    # No edits to these reward multipliers/axes, and no new cap on stats.
    from core.bootstrap_economy_professions import PROFESSION_XP_GAIN_MULTIPLIER
    from core.balance_math import AXIS_TARGET_ACTIONS
    from core.progression_resources import STAT_MAX_LEVEL
    assert PROFESSION_XP_GAIN_MULTIPLIER == 4
    assert AXIS_TARGET_ACTIONS == {'character':18,'class':16,'soul':25,'skill':18,
                                   'profession':50,'tool':65,'stat':60}
    assert STAT_MAX_LEVEL is None
    assert scale_all_progress_requirements_v3310(SAFE_INT) == SAFE_INT
    checks += 4
    return checks


if __name__ == '__main__':
    print(f'ALL PROGRESSION XP v3.31.0: {run_regression()} checks PASS')
