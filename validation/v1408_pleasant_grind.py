# -*- coding: utf-8 -*-
"""v1.40.8: smooth, stronger requirement-only XP curves (stats gentler)."""
from __future__ import annotations

from config.balance import (
    PROFESSION_LATE_GAME_REQUIREMENT_POINTS_V1401,
    PLAYER_EXTRA_REQUIREMENT_POINTS_V1407,
    STAT_EXTRA_REQUIREMENT_POINTS_V1408,
    profession_late_requirement_points_v1401,
    player_extra_requirement_points_v1407,
    stat_extra_requirement_points_v1408,
    profession_xp_requirement_v1401,
    tool_xp_requirement_v1402,
    scale_player_requirement_v1407,
    scale_stat_requirement_v1408,
)
from core.progression_resources import v0190_requirement
from core.player_math import SAFE_INT

EXPECTED_ANCHORS = {
    'profession': {49: 10000, 50: 10100, 75: 15000, 100: 20000, 150: 30000,
                   200: 40000, 300: 60000, 400: 80000, 500: 120000,
                   600: 160000, 700: 205000, 799: 250000},
    'player': {49: 10000, 50: 10100, 75: 15000, 100: 20000, 150: 30000,
               200: 40000, 300: 60000, 400: 80000, 500: 110000,
               600: 140000, 700: 180000, 799: 220000},
    'stat': {49: 10000, 50: 10100, 75: 12500, 100: 15000, 150: 17500,
             200: 20000, 300: 27000, 400: 35000, 500: 45000,
             600: 55000, 700: 68000, 799: 80000},
}


def run_pleasant_grind_v1408():
    errors, checks = [], 0

    def check(condition, message):
        nonlocal checks
        checks += 1
        if not condition:
            errors.append(message)

    sources = (
        ('profession', PROFESSION_LATE_GAME_REQUIREMENT_POINTS_V1401,
         profession_late_requirement_points_v1401),
        ('player', PLAYER_EXTRA_REQUIREMENT_POINTS_V1407, player_extra_requirement_points_v1407),
        ('stat', STAT_EXTRA_REQUIREMENT_POINTS_V1408, stat_extra_requirement_points_v1408),
    )
    for name, checkpoints, points_at in sources:
        check(tuple(checkpoints) == tuple(EXPECTED_ANCHORS[name].items()),
              f'{name}: all authored anchors exact')
        prev = 0
        for level in range(1, 800):
            pts = points_at(level)
            check(pts >= prev, f'{name}: level {level} nondecreasing')
            check(pts == 10000 if level < 50 else pts > 10000,
                  f'{name}: unchanged 1-49, harder 50+')
            prev = pts
        for level, point in EXPECTED_ANCHORS[name].items():
            check(points_at(level) == point, f'{name}: level {level} target')
    check(stat_extra_requirement_points_v1408(1000) > stat_extra_requirement_points_v1408(799),
          'uncapped stats continue to grow after 799')
    check(stat_extra_requirement_points_v1408(1000000) == 120000,
          'uncapped stats do not overflow the multiplier')

    # No stacking: compare with historical required XP, not v1.40.7 XP.
    for level in (49, 50, 75, 100, 150, 200, 400, 600, 799):
        original_prof = v0190_requirement('profession', level) * 2
        actual_prof = profession_xp_requirement_v1401(
            v0190_requirement('profession', level), 'Górnictwo', level)
        expected_prof = (original_prof * profession_late_requirement_points_v1401(level) + 5000) // 10000
        check(actual_prof == expected_prof, f'profession {level}: one multiplier only')
        original_tool = v0190_requirement('tool', level) * 2
        actual_tool = tool_xp_requirement_v1402(v0190_requirement('tool', level), 'mining', level)
        expected_tool = (original_tool * profession_late_requirement_points_v1401(level) + 5000) // 10000
        check(actual_tool == expected_tool, f'tool {level}: one multiplier only')

        baseline = 100000000
        # Test both progression scalers independently, no side-effect on XP rewards.
        check(scale_player_requirement_v1407(baseline, level) ==
              (baseline * player_extra_requirement_points_v1407(level) + 5000) // 10000,
              f'player {level}: one multiplier')
        check(scale_stat_requirement_v1408(baseline, level) ==
              (baseline * stat_extra_requirement_points_v1408(level) + 5000) // 10000,
              f'stat {level}: one gentler multiplier')
        check(stat_extra_requirement_points_v1408(level) <= player_extra_requirement_points_v1407(level),
              f'stat {level}: not harder than player')
    check(scale_stat_requirement_v1408(SAFE_INT, 1000000) == SAFE_INT,
          'stat cap on XP requirement arithmetic only, not on stat value')
    return {'checks': checks, 'errors': errors}


if __name__ == '__main__':
    result = run_pleasant_grind_v1408()
    print(f'PLEASANT GRIND v1.40.8: {result["checks"]} checks, {len(result["errors"])} errors')
    if result['errors']:
        raise SystemExit('\n'.join(result['errors'][:25]))
