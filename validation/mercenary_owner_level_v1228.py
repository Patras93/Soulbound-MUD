# -*- coding: utf-8 -*-
"""Regression: every hired mercenary follows its owner's level, without EXP."""
import asyncio
import ast
import sqlite3
from pathlib import Path
from types import SimpleNamespace

from systems.mercenary_growth_v1220 import (
    mercenary_owner_level_v1228, mercenary_unlocked, mercenary_attack_multiplier, mercenary_tactic,
)
from storage.db_mercenaries import DatabaseMercenariesMixin
from validation.mercenary_followers_v1226 import _GameSession, _Db
from systems.mercenary_taverns import MERCENARIES


def validate_mercenary_owner_level_v1228():
    checks = 0
    for level in (1, 2, 9, 10, 24, 25, 49, 50, 100, 600, 10000):
        assert mercenary_owner_level_v1228(SimpleNamespace(character_level=level)) == level
        checks += 1
    assert mercenary_owner_level_v1228(SimpleNamespace()) == 1
    checks += 1
    for level in (1, 9, 10, 25, 50):
        for tactic in ('', 'szturm', 'obrona', 'wsparcie'):
            assert 'Taktyka' in mercenary_unlocked(level, tactic)
            checks += 1
    assert mercenary_attack_multiplier(50, 'szturm') > mercenary_attack_multiplier(10, 'szturm')
    checks += 1

    class TestDb(DatabaseMercenariesMixin):
        def __init__(self):
            self.conn = sqlite3.connect(':memory:')
            self.conn.row_factory = sqlite3.Row
            self.create_mercenary_schema()

    db = TestDb()
    db.conn.execute("INSERT INTO mercenary_contracts VALUES(1,'mag',0)")
    db.conn.execute("INSERT INTO mercenary_progress_v1220 VALUES(1,'mag',999999999,'',123)")
    db.conn.commit()
    assert db.mercenary_specialize_v1220(1,'mag','szturm',owner_level=1) == 'ok'
    checks += 1
    assert db.mercenary_specialize_v1220(1,'mag','szturm',owner_level=10) == 'ok'
    checks += 1
    assert db.mercenary_specialize_v1220(1,'mag','wsparcie',owner_level=500) == 'ok'
    checks += 1
    assert db.mercenary_progress_v1220(1,'mag')['xp'] == 999999999
    checks += 1
    db.close = db.conn.close
    db.close()

    # Execute the real session methods from source, not copied gameplay logic.
    path = Path(__file__).resolve().parents[1] / 'player/session_mixins/mercenary_taverns.py'
    src = path.read_text(encoding='utf-8')
    tree = ast.parse(src)
    cls = next(x for x in tree.body if isinstance(x, ast.ClassDef) and x.name == 'SessionMercenaryTavernsMixin')
    method = next(x for x in cls.body if isinstance(x, ast.AsyncFunctionDef) and x.name == 'handle_mercenaries_v1170')
    namespace = {
        'mercenary_owner_level_v1228': mercenary_owner_level_v1228,
        'mercenary_unlocked': mercenary_unlocked,
        'mercenary_tactic': mercenary_tactic,
        'MERCENARIES': MERCENARIES,
        'mercenary_role': lambda text: next((role for role, spec in MERCENARIES.items() if text.lower() in (role, spec['name'].lower())), None),
    }
    exec(compile(ast.fix_missing_locations(ast.Module(body=[method], type_ignores=[])), str(path), 'exec'), namespace)
    _GameSession.handle_mercenaries_v1170 = namespace['handle_mercenaries_v1170']
    harness_db = _Db()
    harness_db.hires = {1: ['mag']}
    harness_db.mercenary_progress_v1220 = lambda _a, _r: {'xp': 999999999, 'specialization': 'szturm', 'actions': 123}
    harness_db.mercenary_gain_xp_v1220 = lambda *_args: (_ for _ in ()).throw(AssertionError('No EXP writes allowed'))
    async def broadcast(*_args, **_kwargs):
        return None
    server = SimpleNamespace(db=harness_db, party_sessions=lambda _a, same_room=None: [], party_combat_broadcast=broadcast)
    owner = _GameSession(server, 1, 'Właściciel', 'room')
    owner.skill_guard = 1
    owner.mob_effective_max_hp_v11330 = lambda mob: 100000
    mob_type = SimpleNamespace(template_id='test_enemy', room_id='room', hp=100000, alive=True)
    async def run_all():
        nonlocal checks
        for level in (1, 9, 10, 24, 25, 49, 50, 150, 600):
            owner.character.character_level = level
            owner.messages.clear()
            await owner.handle_mercenaries_v1170('status')
            assert f'poziom {level}' in '\n'.join(owner.messages)
            checks += 1
            owner.messages.clear()
            await owner.handle_mercenaries_v1170('rozwoj Vael')
            assert f'poziom {level}' in '\n'.join(owner.messages)
            assert 'EXP 999999999' not in '\n'.join(owner.messages)
            checks += 2
            owner.messages.clear()
            owner._mercenary_next_action_v1170 = 0
            mob_type.hp = 100000
            await owner.mercenary_combat_turn_v1170(mob_type)
            assert mob_type.hp < 100000 and owner.messages
            checks += 1
            if level >= 50:
                assert 'Legendarna seria:' not in '\n'.join(owner.messages)
                checks += 1
            if 25 <= level < 50:
                assert 'Mistrzowski atak:' not in '\n'.join(owner.messages)
                checks += 1
        assert harness_db.mercenary_progress_v1220(1, 'mag')['xp'] == 999999999
        checks += 1
    asyncio.run(run_all())
    return checks

if __name__ == '__main__':
    print('MERCENARY OWNER LEVEL v1.22.8:', validate_mercenary_owner_level_v1228(), 'checks PASS')
