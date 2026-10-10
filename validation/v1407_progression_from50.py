# -*- coding: utf-8 -*-
"""v1.40.7: XP requirements grow after level 50; XP awards/saves do not change."""
from __future__ import annotations

import ast
from pathlib import Path
from types import SimpleNamespace


def _source_function(path, class_name, method_name, namespace):
    """Read the actual authored function without importing mutable world catalogs."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    source_class = next(
        node for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name == class_name
    )
    method = next(
        node for node in source_class.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == method_name
    )
    module = ast.Module(body=[method], type_ignores=[])
    exec(compile(ast.fix_missing_locations(module), str(path), "exec"), namespace)
    return namespace[method_name]


def run_progression_from50_regression_v1407():
    from config.balance import (
        PLAYER_EXTRA_REQUIREMENT_POINTS_V1407,
        PROFESSION_LATE_GAME_REQUIREMENT_POINTS_V1401,
        STAT_XP_REQUIREMENT_MULTIPLIER,
        PROFESSION_XP_REQUIREMENT_MULTIPLIERS,
        player_extra_requirement_points_v1407,
        profession_late_requirement_points_v1401,
        profession_xp_requirement_v1401,
        tool_xp_requirement_v1402,
        scale_player_requirement_v1407,
        scale_stat_requirement_v1408,
    )
    from core import balance_math
    from core.player_math import late_game_xp_requirement, SAFE_INT
    from core.progression_resources import (
        character_xp_to_next, class_mastery_xp_to_next,
        soul_xp_to_next, skill_xp_to_next,
        soul_weapon_mastery_xp_to_next, v0190_requirement,
    )
    from validation.tool_xp_v1402 import TOOL_TYPES_V1402
    root = Path(__file__).resolve().parents[1]
    errors, checks = [], 0

    def check(condition, message):
        nonlocal checks
        checks += 1
        if not condition:
            errors.append(message)

    check(PROFESSION_LATE_GAME_REQUIREMENT_POINTS_V1401[0] == (49, 10000),
          "professions start at 50")
    check(PLAYER_EXTRA_REQUIREMENT_POINTS_V1407[0] == (49, 10000),
          "all other player axes start at 50")
    for i in range(1, 800):
        old = v0190_requirement
        reqs = {
            'character': (character_xp_to_next, 'character', 4),
            'class': (class_mastery_xp_to_next, 'class', 3),
            'soul': (soul_xp_to_next, 'soul', 3),
            'skill': (skill_xp_to_next, 'skill', 1),
            'weapon': (soul_weapon_mastery_xp_to_next, 'skill', 3),
        }
        for name, (func, axis, multiple) in reqs.items():
            required = func(i)
            historical = int(round(old(axis, i) * multiple))
            if axis in ('character', 'class', 'soul'):
                historical = late_game_xp_requirement(
                    i, historical, int(round(old(axis, 599) * multiple))
                )
            check(required == scale_player_requirement_v1407(historical, i),
                  f'{name} level{i}: authoritative formula')
            check(required == historical if i < 50 else required > historical,
                  f'{name} level{i}: original <50, harder from 50')
            check(required <= func(i + 1) if i < 799 else required > 0,
                  f'{name} level{i}: requirements grow')
        check(profession_late_requirement_points_v1401(i) == 10000 if i < 50
              else profession_late_requirement_points_v1401(i) > 10000,
              f'profession multiplier: level{i}')
    for name, (func, _, _) in reqs.items():
        check(func(800) == 0, f'{name}: level 800 still maximum')

    for kind in PROFESSION_XP_REQUIREMENT_MULTIPLIERS:
        previous = 0
        for i in range(1, 800):
            requirement = profession_xp_requirement_v1401(
                old('profession', i), kind, i)
            check(requirement >= previous, f'{kind}: level{i} monotonic')
            previous = requirement
    for kind in TOOL_TYPES_V1402:
        previous = 0
        for i in range(1, 800):
            requirement = tool_xp_requirement_v1402(old('tool', i), kind, i)
            check(requirement >= previous, f'{kind} tool: level{i} monotonic')
            previous = requirement

    # Check actual stat method while avoiding the mutable world-loader's
    # historical import-order constraints in stand-alone fast predeploy.
    stat_fields = {x: (x, x, x + '_progress') for x in (
        'strength', 'dexterity', 'constitution', 'intelligence',
        'willpower', 'charisma')}
    method = _source_function(
        root / 'player' / 'character.py', 'Character',
        'stat_growth_threshold_for', {
            'v0190_requirement': v0190_requirement,
            'STAT_XP_REQUIREMENT_MULTIPLIER': STAT_XP_REQUIREMENT_MULTIPLIER,
            'late_game_xp_requirement': late_game_xp_requirement,
            'scale_stat_requirement_v1408': scale_stat_requirement_v1408,
        })
    for stat in stat_fields:
        previous = 0
        for value in range(1, 1001):
            probe = SimpleNamespace(STAT_PROGRESS_FIELDS=stat_fields, **{stat: value})
            required = method(probe, stat)
            historical_base = max(1, round(old('stat', value) * STAT_XP_REQUIREMENT_MULTIPLIER))
            terminal = max(1, round(old('stat', 599) * STAT_XP_REQUIREMENT_MULTIPLIER))
            historical = late_game_xp_requirement(value, historical_base, terminal)
            check(required == scale_stat_requirement_v1408(historical, value),
                  f'{stat}: stat {value} uses requirement-only scaling')
            check(required == historical if value < 50 else required >= historical,
                  f'{stat}: stat {value} original <50, never less from 50')
            check(required >= previous, f'{stat}: no decrease at stat {value}')
            previous = required
        for very_high in (1001, 5000, 1000000):
            probe = SimpleNamespace(STAT_PROGRESS_FIELDS=stat_fields, **{stat: very_high})
            check(0 < method(probe, stat) <= SAFE_INT,
                  f'{stat}: stat {very_high} does not hit a level cap or overflow')

    # Actual Ascension requirement function, with isolated legacy world globals.
    asc_tree = ast.parse((root / 'world' / 'runtime_progression.py').read_text(encoding='utf-8'))
    asc_func = next(node for node in asc_tree.body if isinstance(node, ast.FunctionDef)
                    and node.name == 'v0210_ascension_xp_to_next')
    namespace = {'V021_ASCENSION_MAX_RANK': 1000,
                 'V021_ASCENSION_REQ': (),
                 'v0190_log_curve': lambda level, _: 1000000 + level * 1000}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[asc_func], type_ignores=[])),
                 '<ascension-req>', 'exec'), namespace)
    ascension = namespace['v0210_ascension_xp_to_next']
    for rank in (0, 10, 48, 49, 50, 99, 150, 799, 999):
        historical = 1000000 + (rank + 1) * 1000
        check(ascension(rank) == scale_player_requirement_v1407(historical, rank + 1),
              f'ascension rank{rank}: changed only XP requirement')
    check(ascension(1000) == 0, 'ascension retains rank 1000 cap')

    # Mechanical proof that the 1.40.7 change adds no edits to reward constants
    # and that it did not remove saved-progress entry points.
    check(balance_math.AXIS_TARGET_ACTIONS == {
        'character':18,'class':16,'soul':25,'skill':18,
        'profession':50,'tool':65,'stat':60}, 'historical XP reward model intact')
    actual_player = (root / 'player' / 'character.py').read_text(encoding='utf-8')
    check('def add_stat_progress(' in actual_player, 'stat XP accounting preserved')
    check('STAT_MAX_LEVEL = None' in (root / 'core' / 'progression_resources.py').read_text(encoding='utf-8'),
          'stat levels have no maximum')
    return {'checks': checks, 'errors': errors}


if __name__ == '__main__':
    result = run_progression_from50_regression_v1407()
    print(f"LEVELS FROM 50 v1.40.7: {result['checks']} checks, {len(result['errors'])} errors")
    if result['errors']:
        raise SystemExit('\n'.join(result['errors'][:30]))
