# -*- coding: utf-8 -*-
"""Fast checks for player-configured tactics without specialization or EXP."""
import asyncio
import ast
import sqlite3
from pathlib import Path
from types import SimpleNamespace
from systems.mercenary_taverns import MERCENARIES, mercenary_role
from systems.mercenary_growth_v1220 import mercenary_tactic, mercenary_owner_level_v1228, mercenary_unlocked
from storage.db_mercenaries import DatabaseMercenariesMixin
from validation.mercenary_followers_v1226 import _GameSession

class Db(DatabaseMercenariesMixin):
    def __init__(self):
        self.conn = sqlite3.connect(':memory:')
        self.conn.row_factory = sqlite3.Row
        self.create_mercenary_schema()


def validate_mercenary_tactics_v1229():
    checks = 0
    db = Db()
    for account in (1, 2):
        for role in ('mag', 'wojownik', 'paladyn'):
            db.conn.execute('INSERT INTO mercenary_contracts VALUES(?,?,0)', (account,role))
    db.conn.execute('INSERT INTO mercenary_progress_v1220 VALUES(1,\'mag\',77777,\'szturm\',123)')
    db.conn.commit()
    assert mercenary_tactic(db.mercenary_progress_v1220(1,'mag')['specialization']) == 'szturm'; checks += 1
    for owner_level in (1, 9, 10, 24, 25, 49, 50, 600):
        for name in ('automatyczna','szturm','obrona','wsparcie'):
            assert db.mercenary_set_tactic_v1229(1,'mag',name) == 'ok'; checks += 1
            row = db.mercenary_progress_v1220(1,'mag')
            assert mercenary_tactic(row['specialization']) == name; checks += 1
            assert (row['xp'],row['actions']) == (77777,123); checks += 1
            assert mercenary_owner_level_v1228(SimpleNamespace(character_level=owner_level)) == owner_level; checks += 1
            assert 'Taktyka' in mercenary_unlocked(owner_level,row['specialization']); checks += 1
    assert db.mercenary_set_tactic_v1229(1,'mag','nieznana') == 'unknown'; checks += 1
    assert db.mercenary_set_tactic_v1229(1,'nekromanta','szturm') == 'not_hired'; checks += 1
    assert db.mercenary_progress_v1220(2,'mag')['specialization'] == ''; checks += 1
    assert db.mercenary_set_tactic_v1229(1,'wojownik','obrona') == 'ok'; checks += 1
    assert db.mercenary_set_tactic_v1229(1,'paladyn','wsparcie') == 'ok'; checks += 1
    assert mercenary_tactic(db.mercenary_progress_v1220(1,'wojownik')['specialization']) == 'obrona'; checks += 1
    assert mercenary_tactic(db.mercenary_progress_v1220(1,'paladyn')['specialization']) == 'wsparcie'; checks += 1
    # Round-trip in a fresh connection snapshot simulates restart without any schema changes.
    copy = sqlite3.connect(':memory:')
    copy.row_factory = sqlite3.Row
    db.conn.backup(copy)
    assert copy.execute("SELECT specialization FROM mercenary_progress_v1220 WHERE character_account_id=1 AND role='mag'").fetchone()[0] == 'wsparcie'; checks += 1
    assert copy.execute("SELECT specialization FROM mercenary_progress_v1220 WHERE character_account_id=2 AND role='mag'").fetchone() is None; checks += 1
    copy.close()

    # Invoke the actual session method in isolation, no copied command behavior.
    path = Path(__file__).resolve().parents[1] / 'player/session_mixins/mercenary_taverns.py'
    tree = ast.parse(path.read_text(encoding='utf-8'))
    cls = next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='SessionMercenaryTavernsMixin')
    method = next(n for n in cls.body if isinstance(n,ast.AsyncFunctionDef) and n.name=='handle_mercenaries_v1170')
    namespace = dict(mercenary_role=mercenary_role, MERCENARIES=MERCENARIES, mercenary_owner_level_v1228=mercenary_owner_level_v1228,
                     mercenary_unlocked=mercenary_unlocked, mercenary_tactic=mercenary_tactic)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[method],type_ignores=[])),str(path),'exec'),namespace)
    _GameSession.handle_mercenaries_v1170 = namespace['handle_mercenaries_v1170']
    server = SimpleNamespace(db=db)
    owner = _GameSession(server,1,'Test','room')
    owner.character.character_level = 1
    async def commands():
        nonlocal checks
        for tactic in ('szturm','obrona','wsparcie','automatyczna','szturm'):
            owner.messages.clear()
            await owner.handle_mercenaries_v1170(f'taktyka Vael {tactic}')
            assert f'taktykę {tactic}' in ''.join(owner.messages); checks += 1
            assert mercenary_tactic(db.mercenary_progress_v1220(1,'mag')['specialization'])==tactic; checks += 1
        owner.messages.clear()
        await owner.handle_mercenaries_v1170('status')
        assert 'taktyka szturm' in ''.join(owner.messages); checks += 1
        owner.messages.clear()
        await owner.handle_mercenaries_v1170('rozwoj Vael')
        assert 'taktyka szturm' in ''.join(owner.messages) and 'specjalizacja' not in ''.join(owner.messages); checks += 1
        owner.messages.clear()
        await owner.handle_mercenaries_v1170('specjalizacja Vael obrona')
        assert 'Nie ma już specjalizacji' in ''.join(owner.messages); checks += 1
        owner.messages.clear()
        await owner.handle_mercenaries_v1170('taktyka Vael xxx')
        assert 'Taktyki:' in ''.join(owner.messages); checks += 1
    asyncio.run(commands())
    db.conn.close()
    return checks

if __name__ == '__main__':
    print('MERCENARY TACTICS v1.22.9:',validate_mercenary_tactics_v1229(),'checks PASS')
