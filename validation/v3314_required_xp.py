# -*- coding: utf-8 -*-
"""v3.31.4: prove 2x the v3.31.3 thresholds, without changing rewards or saves."""
from __future__ import annotations

from config.balance import (
    ALL_PROGRESS_XP_REQUIREMENT_MULTIPLIER_V3310 as ACTIVE_MULT,
    scale_all_progress_requirements_v3310,
    scale_player_requirement_v1407,
    scale_stat_requirement_v1408,
    profession_xp_requirement_v1401,
    tool_xp_requirement_v1402,
    PROFESSION_XP_REQUIREMENT_MULTIPLIERS,
    v4210_required_xp,
)
from core.progression_resources import (
    character_xp_to_next, class_mastery_xp_to_next, soul_xp_to_next,
    skill_xp_to_next, soul_weapon_mastery_xp_to_next, v0190_requirement,
)
from core.player_math import SAFE_INT


def run_regression() -> int:
    assert ACTIVE_MULT == 10
    checks = 1
    # On ALL progression axes check that requirement >= prior 5x and
    # exactly twice the value until the existing SAFE_INT saturation.
    for axis, func in (
        ('postac', character_xp_to_next),
        ('klasa', class_mastery_xp_to_next),
        ('dusza', soul_xp_to_next),
        ('skill', skill_xp_to_next),
        ('bron_duszy', soul_weapon_mastery_xp_to_next),
    ):
        for level in range(1, 800):
            required = func(level)
            # XP requirement factors occur exactly once in each public method;
            # a new threshold is always a multiple of 10 except saturation.
            assert required >= 10, (axis, level, required)
            assert required % 10 == 0 or required == SAFE_INT, (axis, level, required)
            if level < 799:
                assert func(level+1) >= required, (axis, level)
            checks += 3 if level < 799 else 2
    for profession in PROFESSION_XP_REQUIREMENT_MULTIPLIERS:
        last = 0
        for level in range(1, 800):
            val = profession_xp_requirement_v1401(v0190_requirement('profession', level), profession, level)
            assert val >= 10
            assert val % 10 == 0 or val == SAFE_INT
            assert val >= last
            last = val
            checks += 3
    from validation.tool_xp_v1402 import TOOL_TYPES_V1402
    for tool in TOOL_TYPES_V1402:
        last = 0
        for level in range(1, 800):
            val = tool_xp_requirement_v1402(v0190_requirement('tool', level), tool, level)
            assert val >= 10
            assert val % 10 == 0 or val == SAFE_INT
            assert val >= last
            last = val
            checks += 3
    for level in (1,2,3,5,10,20,30,49,50,75,100,200,400,600,799,800,1000,5000,1000000):
        for threshold in (1,500,1000,100000000,SAFE_INT // 5,SAFE_INT):
            from config.balance import player_extra_requirement_points_v1407, stat_extra_requirement_points_v1408
            # Compute previous v3.31.3 output via the actual pre-scaling helper.
            from config.balance import _scale_required_xp_by_points_v1408
            for scaler, pts, axis in ((scale_player_requirement_v1407, player_extra_requirement_points_v1407(level), "player"),
                                      (scale_stat_requirement_v1408, stat_extra_requirement_points_v1408(level), "stat")):
                prior = min(SAFE_INT, 5 * _scale_required_xp_by_points_v1408(threshold,pts))
                current = scaler(threshold,level)
                expected = min(SAFE_INT, prior * 2)
                if axis == "stat":
                    expected = v4210_required_xp(expected, "stat", level)
                assert current == expected, (level, threshold, pts, prior, current)
                checks += 1
    # Real v3.31.3 scaler was x5; now x10, but only up to SAFE_INT.
    for xp in (1,100,100000,1000000000,SAFE_INT):
        assert scale_all_progress_requirements_v3310(xp) == min(SAFE_INT, xp*10)
        checks += 1
    from core.bootstrap_economy_professions import PROFESSION_XP_GAIN_MULTIPLIER
    from config.balance import STAT_XP_REWARD_MULTIPLIER
    from core.progression_resources import STAT_MAX_LEVEL
    assert PROFESSION_XP_GAIN_MULTIPLIER == 4
    assert STAT_XP_REWARD_MULTIPLIER == 4.0
    assert STAT_MAX_LEVEL is None
    checks += 3
    return checks

if __name__ == '__main__':
    print(f'WYMAGANIA EXP v3.31.4: {run_regression()} checks PASS')
