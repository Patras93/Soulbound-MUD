# -*- coding: utf-8 -*-
"""Regression: `level` lists all actual earned levels; Multi Cap last."""
import asyncio
import ast
from pathlib import Path
from types import SimpleNamespace

from systems.level_overview_v23216 import level_overview_lines_v23216
from systems.multi_cap_v23215 import multi_cap_experience_v23215
from validation.v23215_multi_cap import TestDB


def run_regression():
    checks = 0
    db = TestDB()
    db.conn.execute('''INSERT INTO class_progress(account_id,class_name,level,active_slot)
                       VALUES(1,'Wojownik',4,1)''')
    db.conn.execute('''INSERT INTO class_progress(account_id,class_name,level,active_slot)
                       VALUES(1,'Mag',6,NULL)''')
    db.conn.execute('INSERT INTO professions VALUES(1, ?, ?)', ('gornictwo', 7))
    db.conn.execute('INSERT INTO tools VALUES(1, ?, ?)', ('kilof', 8))
    db.conn.execute('INSERT INTO learned_skills VALUES(1, ?)', ('fireball',))
    db.conn.execute('INSERT INTO skill_progress VALUES(1, ?, ?)', ('fireball', 9))
    db.conn.execute('INSERT INTO skill_progress VALUES(1, ?, ?)', ('not_learned', 1000000))
    db.conn.execute('INSERT INTO ascension_progress_v021 VALUES(1, ?, ?)', ('soul', 3))
    db.conn.commit()

    before = db.conn.total_changes
    lines = level_overview_lines_v23216(db.conn, 1, 'Wojownik')
    checks += 1
    assert lines[0] == 'WSZYSTKIE POZIOMY POSTACI — MULTI CAP'
    checks += 1
    assert lines[-1] == f'Your experience cap is {multi_cap_experience_v23215(db.conn, 1)} EXP.'
    checks += 1
    full = '\n'.join(lines)
    for item in ('Dusza: poziom 1', 'Soul Tier: poziom 1', 'Broń Duszy — biegłość: poziom 1',
                 'Wojownik: poziom 4 (główna)', 'Mag: poziom 6 (archiwalna, bez umiejętności klasy)',
                 'Siła: poziom 1', 'Charyzma: poziom 1', 'fireball: poziom 9',
                 'gornictwo: poziom 7', 'kilof: poziom 8', 'soul: poziom 3'):
        assert item in full, item
        checks += 1
    assert 'not_learned' not in full
    checks += 1
    assert db.conn.total_changes == before
    checks += 1

    # The readout must work for a character that has not yet learned any skills/classes.
    empty = level_overview_lines_v23216(db.conn, 2, 'Wojownik')
    assert empty == ['Nie można odczytać Multi Cap z bazy postaci.']
    checks += 1
    db.conn.execute('DELETE FROM class_progress WHERE account_id=1')
    fallback = '\n'.join(level_overview_lines_v23216(db.conn, 1, 'Wojownik'))
    assert 'Wojownik: poziom 1 (główna)' in fallback
    assert f'Your experience cap is {multi_cap_experience_v23215(db.conn, 1)} EXP.' in fallback
    checks += 2

    # Real command entry point: character XP first, cap on the absolutely LAST line.
    # Compile the actual async handler without importing large world runtime
    # (the full server imports content_registry after its bootstrap).
    source = Path(__file__).resolve().parents[1] / 'player' / 'session_mixins' / 'character_profile.py'
    tree = ast.parse(source.read_text(encoding='utf-8'))
    mixin = next(n for n in tree.body if isinstance(n, ast.ClassDef)
                 and n.name == 'SessionCharacterProfileMixin')
    method = next(n for n in mixin.body if isinstance(n, ast.AsyncFunctionDef)
                  and n.name == 'show_character_level')
    namespace = {'CHARACTER_MAX_LEVEL': 800, 'SOUL_MAX_LEVEL': 800, 'character_xp_to_next': lambda level: 776}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[method], type_ignores=[])),
                 str(source), 'exec'), namespace)
    outputs = []
    async def send(text):
        outputs.append(text)
    instance = SimpleNamespace(
        character=SimpleNamespace(character_level=1, character_xp=0, class_name='Wojownik',
                                  soul_level=3, soul_xp=275, soul_xp_to_next=lambda: 1200,
                                  soul_progress_is_tier_locked=lambda: False),
        account_id=1, server=SimpleNamespace(db=db), send=send,
    )
    asyncio.run(namespace['show_character_level'](instance))
    assert outputs[0].startswith('Poziom postaci: 1/')
    assert 'Soul XP 275 z 1200. Brakuje 925 Soul XP do poziomu 4.' in outputs[1]
    checks += 1
    assert outputs[-1] == f'Your experience cap is {multi_cap_experience_v23215(db.conn, 1)} EXP.'
    checks += 2

    # 45 learned skills: all are shown, not cut off after a few entries.
    db.conn.executemany('INSERT INTO learned_skills VALUES(1, ?)',
                        ((f'skill_{i:03d}',) for i in range(45)))
    many = '\n'.join(level_overview_lines_v23216(db.conn, 1, 'Wojownik'))
    assert 'skill_000: poziom 1' in many and 'skill_044: poziom 1' in many
    assert f'Your experience cap is {multi_cap_experience_v23215(db.conn, 1)} EXP.' in many
    checks += 2
    db.conn.close()
    return checks


if __name__ == '__main__':
    print('LEVEL OVERVIEW v2.32.16:', run_regression(), 'checks PASS')
