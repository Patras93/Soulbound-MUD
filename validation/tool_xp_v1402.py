# -*- coding: utf-8 -*-
"""v1.40.2: all 14 tools require progressively more XP after level 100.

Checks actual session dispatch when imported by full runtime, and standalone
requirement helper otherwise. Only requirements change, never rewards.
"""
from __future__ import annotations

TOOL_TYPES_V1402 = (
    'fishing', 'mining', 'woodcutting', 'crafting', 'cooking', 'herbalism',
    'alchemy', 'jewelcrafting', 'tailoring', 'leatherworking', 'carpentry',
    'enchanting', 'archaeology', 'cartography_profession',
)


def run_tool_xp_regression_v1402():
    import sys
    from config.balance import (
        TOOL_XP_REQUIREMENT_MULTIPLIERS,
        profession_late_requirement_points_v1401,
        tool_xp_requirement_v1402,
    )
    from core.progression_resources import v0190_requirement
    from core.profession_timing import TOOL_ACTION_MIN_SECONDS, profession_action_seconds
    from core.bootstrap_economy_professions import tool_max_level

    errors = []
    checks = 0

    def check(condition, name):
        nonlocal checks
        checks += 1
        if not condition:
            errors.append(name)

    mixin_module = sys.modules.get('player.session_mixins.profession_storage')
    klass = getattr(mixin_module, 'SessionProfessionStorageMixin', None)
    session = klass.__new__(klass) if klass else None

    def required(level, kind):
        if session:
            return session.tool_xp_to_next(level, kind)
        if level >= tool_max_level(kind):
            return 0
        return tool_xp_requirement_v1402(v0190_requirement('tool', level), kind, level)

    check(len(TOOL_TYPES_V1402) == len(set(TOOL_TYPES_V1402)) == 14,
          'exactly 14 distinct tools')
    check(set(TOOL_XP_REQUIREMENT_MULTIPLIERS) == {'mining'},
          'preserved historical per-tool requirement differences')
    check(TOOL_XP_REQUIREMENT_MULTIPLIERS['mining'] == 2.0,
          'pickaxe multiplier remains x2')
    check(TOOL_ACTION_MIN_SECONDS['fishing'] == 3,
          'fishing has unchanged minimum 3s')
    check(profession_action_seconds('fishing', 800) == 3,
          'fishing at level 800 still takes 3s')
    check(profession_late_requirement_points_v1401(100) == 10000,
          'level 100 untouched')
    check(profession_late_requirement_points_v1401(101) > 10000,
          'level 101 increases smoothly')

    # Existing mixin exposes exactly these tools to characters.
    if session:
        for kind in TOOL_TYPES_V1402:
            check(session.valid_tool_type(kind), f'{kind}: valid tool type')

    checkpoints = {100: 10000, 150: 11200, 200: 13000,
                   300: 18000, 400: 26000, 500: 40000,
                   600: 60000, 700: 85000, 799: 120000}
    for level, points in checkpoints.items():
        check(profession_late_requirement_points_v1401(level) == points,
              f'growth checkpoint {level}')

    for kind in TOOL_TYPES_V1402:
        prior_required = 0
        prior_points = 0
        old_multiplier = TOOL_XP_REQUIREMENT_MULTIPLIERS.get(kind, 1.0)
        check(tool_max_level(kind) == 800, f'{kind}: 800 maximum')
        for level in range(1, 800):
            base = v0190_requirement('tool', level)
            old = max(1, int(round(base * old_multiplier)))
            got = required(level, kind)
            point = profession_late_requirement_points_v1401(level)
            check(got == tool_xp_requirement_v1402(base, kind, level),
                  f'{kind} level {level}: actual session/helper match')
            check(got >= prior_required,
                  f'{kind} level {level}: no decreased next-level XP')
            check(point >= prior_points,
                  f'{kind} level {level}: monotonically increasing scaling')
            check(got == old if level <= 100 else got > old,
                  f'{kind} level {level}: exact original until level 100, higher afterward')
            prior_required, prior_points = got, point
        check(required(800, kind) == 0, f'{kind}: maximum has no next level')

    for level in (1, 50, 100, 101, 150, 200, 400, 600, 799):
        ordinary = required(level, 'crafting')
        mining = required(level, 'mining')
        # The current base level is integer and the original 2x pickaxe
        # multiplier must remain 2x; rounding of the late curve can differ 1.
        check(abs(mining - ordinary * 2) <= 1,
              f'level{level}: mining difficulty remains x2')

    return {'checks': checks, 'errors': errors,
            'tools': len(TOOL_TYPES_V1402)}


if __name__ == '__main__':
    result = run_tool_xp_regression_v1402()
    print(f'TOOL XP v1.40.2: {result["checks"]} checks, {len(result["errors"])} errors')
    if result['errors']:
        raise SystemExit('\n'.join(result['errors'][:30]))
