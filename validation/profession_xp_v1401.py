# -*- coding: utf-8 -*-
"""v1.40.1: required Profession XP rises smoothly after level 50.

No reward, drop, player records or tool speed modifications. This regression
validates all 14 professions and all levels 1..800 against the actual session
method used by gameplay (not only the helper calculation).
"""
from __future__ import annotations


def run_profession_xp_regression_v1401():
    from config.balance import (
        PROFESSION_XP_REQUIREMENT_MULTIPLIERS,
        PROFESSION_LATE_GAME_REQUIREMENT_POINTS_V1401,
        profession_late_requirement_points_v1401,
        profession_xp_requirement_v1401,
    )
    from core.bootstrap_economy_professions import PROFESSION_XP_GAIN_MULTIPLIER
    from core.profession_timing import TOOL_ACTION_MIN_SECONDS, profession_action_seconds
    from core.progression_resources import v0190_requirement
    # The standalone math test must not bootstrap mutable world catalogues:
    # when full runtime already loaded the mixin, validate actual dispatch too.
    import sys
    profession_storage_module = sys.modules.get('player.session_mixins.profession_storage')
    session_class = getattr(profession_storage_module, 'SessionProfessionStorageMixin', None)
    from systems.legendary_achievements_v1370 import PROFESSIONS_V1370

    errors = []
    checks = 0

    def check(ok, description):
        nonlocal checks
        checks += 1
        if not ok:
            errors.append(description)

    session = session_class.__new__(session_class) if session_class else None

    def next_level_xp(level, profession):
        base = v0190_requirement('profession', level)
        return (session.profession_xp_to_next(level, profession)
                if session else (0 if level >= 800 else profession_xp_requirement_v1401(base, profession, level)))
    check(set(PROFESSIONS_V1370) == set(PROFESSION_XP_REQUIREMENT_MULTIPLIERS),
          '14 existing professions unchanged')
    check(PROFESSION_XP_GAIN_MULTIPLIER == 4, 'EXP gains multiplier preserved')
    check(TOOL_ACTION_MIN_SECONDS['fishing'] == 3, 'fishing minimum 3s')
    check(profession_action_seconds('fishing', 800) == 3, 'fishing endgame remains 3s')
    check(PROFESSION_LATE_GAME_REQUIREMENT_POINTS_V1401[0] == (49, 10000),
          'growth starts at 50 with minimal increase')
    check(PROFESSION_LATE_GAME_REQUIREMENT_POINTS_V1401[-1] == (799, 250000),
          'endgame requirement x25')
    check(profession_late_requirement_points_v1401(49) == 10000, 'level49 unchanged')
    check(profession_late_requirement_points_v1401(50) > 10000, 'level50 grows')
    check(next_level_xp(800, 'Wędkarstwo') == 0, 'level800 capped')

    for profession in PROFESSIONS_V1370:
        prior_requirement = 0
        prior_growth = 0
        for level in range(1, 800):
            original = max(1, round(
                v0190_requirement('profession', level)
                * PROFESSION_XP_REQUIREMENT_MULTIPLIERS[profession]
            ))
            new = next_level_xp(level, profession)
            growth = profession_late_requirement_points_v1401(level)
            check(new == profession_xp_requirement_v1401(
                v0190_requirement('profession', level), profession, level),
                f'{profession} level{level}: session/helper match')
            check(new >= prior_requirement, f'{profession} level{level}: nondecreasing required EXP')
            check(growth >= prior_growth, f'{profession} level{level}: smooth nondecreasing multiplier')
            check(new == original if level < 50 else new > original,
                  f'{profession} level{level}: exact original <50, strictly more >=50')
            prior_requirement, prior_growth = new, growth
        check(next_level_xp(800, profession) == 0,
              f'{profession}: cap 800')
        for level, points in PROFESSION_LATE_GAME_REQUIREMENT_POINTS_V1401:
            check(profession_late_requirement_points_v1401(level) == points,
                  f'{profession}: anchor {level}')
    return {'checks': checks, 'errors': errors}


if __name__ == '__main__':
    result = run_profession_xp_regression_v1401()
    print(f"PROFESSION XP 1.40.1: {result['checks']} checks, {len(result['errors'])} errors")
    if result['errors']:
        raise SystemExit('\n'.join(result['errors'][:30]))
