# -*- coding: utf-8 -*-
"""Regression for dynamic 10-level curve across ALL persisted EXP axes.

No real player SQLite is opened. Includes 14 classes, professions, tools,
learned-skills filter, Soul, long-game and XP Bank overdraft safety.
"""
import asyncio
import ast
from pathlib import Path
from types import SimpleNamespace

from systems.multi_cap_v23215 import (
    multi_cap_calculation_v23217,
    multi_cap_experience_v23215,
    multi_cap_level_increment_v23217,
    multi_cap_level_value_v23217,
)
from systems.experience_bank_v2011 import banked_experience_v2011
from systems.level_overview_v23216 import level_overview_lines_v23216
from validation.v23215_multi_cap import TestDB


def run_regression():
    checks = 0
    bands = {
        1: 500, 10: 500, 11: 1000, 20: 1000,
        21: 5000, 30: 5000, 31: 7500, 40: 7500,
        41: 10000, 50: 10000, 51: 12500, 100: 22500,
        101: 25000, 200: 47500, 201: 50000,
        400: 97500, 401: 100000, 800: 197500,
        801: 200000, 1000: 247500,
    }
    for level, expected in bands.items():
        assert multi_cap_level_increment_v23217(level) == expected, level
        assert multi_cap_level_value_v23217(level) - (
            multi_cap_level_value_v23217(level - 1) if level > 1 else 0
        ) == expected, level
        checks += 2
    for level in range(1, 1100):
        assert multi_cap_level_value_v23217(level) - (
            multi_cap_level_value_v23217(level - 1) if level > 1 else 0
        ) == multi_cap_level_increment_v23217(level), level
        checks += 1
    for level in (5000, 50000, 1_000_000):
        assert multi_cap_level_value_v23217(level) > 0
        assert multi_cap_level_value_v23217(level+1) > multi_cap_level_value_v23217(level)
        checks += 2

    db = TestDB()
    baseline = multi_cap_experience_v23215(db.conn, 1)
    assert baseline == 5500
    assert multi_cap_experience_v23215(db.conn, 2) is None
    checks += 2

    # Character, soul, tier, soul weapon, stat, class, profession, tool,
    # learned skill and earned ascension are independently counted.
    db.conn.execute('UPDATE characters SET character_level=400, soul_level=31, '
                    'soul_tier=11, soul_weapon_mastery_level=101, strength=21 WHERE account_id=1')
    for idx in range(14):
        db.conn.execute('INSERT INTO class_progress VALUES (?, ?, ?, ?, ?)',
                        (1, 'class'+str(idx), 20+idx, 0, 1 if idx == 0 else None))
    db.conn.execute('INSERT INTO professions VALUES(1, ?, ?)', ('gornictwo', 41))
    db.conn.execute('INSERT INTO tools VALUES(1, ?, ?)', ('kilof', 51))
    db.conn.execute('INSERT INTO learned_skills VALUES(1, ?)', ('fireball',))
    db.conn.execute('INSERT INTO skill_progress VALUES(1, ?, ?)', ('fireball', 201))
    db.conn.execute('INSERT INTO skill_progress VALUES(1, ?, ?)', ('unknown', 1_000_000))
    db.conn.execute('INSERT INTO ascension_progress_v021 VALUES(1, ?, ?)', ('soul', 31))
    db.conn.commit()
    result = multi_cap_calculation_v23217(db.conn, 1)
    cap, levels, levels_by_kind, cap_by_kind = result
    expected_lvls = {
        'postać': [400], 'dusza': [31], 'soul tier': [11],
        'broń duszy': [101], 'statystyki': [21,1,1,1,1,1],
        'klasy': [20], 'profesje': [41],
        'narzędzia': [51], 'skille': [201], 'wzniesienia': [31]
    }
    expected_cap = sum(multi_cap_level_value_v23217(v)
                       for arr in expected_lvls.values() for v in arr)
    assert cap == expected_cap == multi_cap_experience_v23215(db.conn, 1)
    assert levels == sum(sum(arr) for arr in expected_lvls.values())
    for kind, arr in expected_lvls.items():
        assert levels_by_kind[kind] == sum(arr), kind
        assert cap_by_kind[kind] == sum(multi_cap_level_value_v23217(v) for v in arr), kind
        checks += 2
    checks += 2

    db.conn.execute('UPDATE tools SET level=52 WHERE account_id=1 AND tool_type=?', ('kilof',))
    assert multi_cap_experience_v23215(db.conn, 1) == cap + 12500
    checks += 1
    assert banked_experience_v2011(db, 1, 10**30, 'soul', 31) == cap + 12500
    assert banked_experience_v2011(db, 1, 10**30, 'profession', 41, source_key='gornictwo', overcap=True) == (cap + 12500)*2
    checks += 2
    assert level_overview_lines_v23216(db.conn, 1, 'class0')[-1] == f'Your experience cap is {cap+12500} EXP.'
    checks += 1

    # A locked Soul tier does NOT hide the XP threshold or remaining XP.
    source = Path(__file__).resolve().parents[1]/'player/session_mixins/character_profile.py'
    tree = ast.parse(source.read_text(encoding='utf-8'))
    mixin = next(node for node in tree.body if isinstance(node, ast.ClassDef)
                 and node.name == 'SessionCharacterProfileMixin')
    method = next(node for node in mixin.body if isinstance(node, ast.AsyncFunctionDef)
                  and node.name == 'show_character_level')
    namespace = {'CHARACTER_MAX_LEVEL': 800, 'SOUL_MAX_LEVEL': 800,
                 'character_xp_to_next': lambda level: 778}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[method], type_ignores=[])),
                 str(source), 'exec'), namespace)
    messages = []
    async def send(message): messages.append(message)
    char = SimpleNamespace(character_level=1, character_xp=100, class_name='class0',
                           soul_level=8, soul_xp=200, soul_xp_to_next=lambda: 1125,
                           soul_progress_is_tier_locked=lambda: True)
    session = SimpleNamespace(character=char, account_id=1,
                              server=SimpleNamespace(db=db), send=send)
    asyncio.run(namespace['show_character_level'](session))
    assert 'Soul XP 200 z 1125. Brakuje 925 Soul XP do poziomu 9.' in messages[1]
    assert 'zablokowany' in messages[2].lower()
    assert messages[-1] == f'Your experience cap is {cap+12500} EXP.'
    checks += 3
    messages.clear()
    char.soul_level = 800
    asyncio.run(namespace['show_character_level'](session))
    assert 'maksimum' in messages[1]
    assert messages[-1] == f'Your experience cap is {cap+12500} EXP.'
    checks += 2
    db.conn.close()
    return checks


if __name__ == '__main__':
    print('MULTI CAP 10-LEVEL CURVE / SOUL LEVEL v2.32.17:', run_regression(), 'PASS')
