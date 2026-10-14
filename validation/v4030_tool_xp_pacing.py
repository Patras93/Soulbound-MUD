# -*- coding: utf-8 -*-
"""v4.00.3 regression: all 14 tool next-level thresholds only, no reward nerfs.

Historical x10 v4.00.2 baseline: fishing x1, mining x2, 12 other tools x1.
The safe old levels/XP remain in SQLite; this module never opens player DB.
"""
from config.balance import (
    TOOL_XP_REQUIREMENT_MULTIPLIERS,
    PROFESSION_XP_REQUIREMENT_MULTIPLIERS,
    ALL_PROGRESS_XP_REQUIREMENT_MULTIPLIER_V3310,
    v4210_required_xp,
    profession_late_requirement_points_v1401,
    profession_xp_requirement_v1401,
    tool_xp_requirement_v1402,
)
from core.progression_resources import (
    GATHER_TOOL_LEVELING_MULTIPLIERS,
    balanced_gather_tool_xp,
    v0190_requirement,
)
from core.bootstrap_economy_professions import PROFESSION_XP_GAIN_MULTIPLIER
from validation.tool_xp_v1402 import TOOL_TYPES_V1402


def run_regression():
    assert len(TOOL_TYPES_V1402) == 14
    assert set(TOOL_TYPES_V1402) == set(TOOL_XP_REQUIREMENT_MULTIPLIERS)
    expected = {tool: 3.0 for tool in TOOL_TYPES_V1402}
    expected.update(fishing=5.0, mining=4.0)
    assert TOOL_XP_REQUIREMENT_MULTIPLIERS == expected
    assert len(PROFESSION_XP_REQUIREMENT_MULTIPLIERS) == 14
    assert PROFESSION_XP_GAIN_MULTIPLIER == 4
    assert ALL_PROGRESS_XP_REQUIREMENT_MULTIPLIER_V3310 == 10
    assert GATHER_TOOL_LEVELING_MULTIPLIERS == {
        'fishing': 1.50, 'mining': 3.00,
        'woodcutting': 2.40, 'herbalism': 1.00,
    }
    for kind, value in GATHER_TOOL_LEVELING_MULTIPLIERS.items():
        assert balanced_gather_tool_xp(kind, 100) == round(value * 100)
    checks = 10
    for tool in TOOL_TYPES_V1402:
        previous = 0
        old_mult = 2 if tool == 'mining' else 1
        new_mult = int(expected[tool])
        for level in range(1, 800):
            base = v0190_requirement('tool', level)
            points = profession_late_requirement_points_v1401(level)
            before_points = base * old_mult if points == 10000 else (base * old_mult * points + 5000) // 10000
            previous_release_requirement = min(9_000_000_000_000_000_000, before_points * 10)
            current_points = base * new_mult if points == 10000 else (base * new_mult * points + 5000) // 10000
            expected_requirement = min(9_000_000_000_000_000_000, current_points * 10)
            actual = tool_xp_requirement_v1402(base, tool, level)
            assert actual == v4210_required_xp(expected_requirement, "tool", level), (tool, level, actual, expected_requirement)
            assert actual >= previous_release_requirement, (tool, level, actual, previous_release_requirement)
            assert actual >= previous, (tool, level, actual, previous)
            if level <= 49:
                assert actual > previous_release_requirement, (tool, level)
            previous = actual
            checks += 4
    # Fishing level 7 against profession level 4 is the reported scenario.
    fish_prof_requirement = profession_xp_requirement_v1401(
        v0190_requirement('profession', 4), 'Wędkarstwo', 4)
    old_rod_requirement = v0190_requirement('tool', 7) * 10
    new_rod_requirement = tool_xp_requirement_v1402(v0190_requirement('tool', 7), 'fishing', 7)
    assert new_rod_requirement == v4210_required_xp(old_rod_requirement * 5, "tool", 7)
    assert fish_prof_requirement == v4210_required_xp(25480, "profession", 4)
    checks += 2
    return checks

if __name__ == '__main__':
    print(f'NARZEDZIA XP v4.00.3: {run_regression()} checks PASS')
