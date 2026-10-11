# -*- coding: utf-8 -*-
"""v2.00.11: XP bank saved in SQLite, per-axis, deterministic and bounded."""

import asyncio
import os
import sqlite3
import tempfile
from types import SimpleNamespace

from systems.experience_cap_v2009 import KINDS, experience_cap_v2009
from systems.experience_bank_v2011 import banked_experience_v2011
from storage.db_experience_bank_v2011 import DatabaseExperienceBankV2011Mixin


class _TempBank(DatabaseExperienceBankV2011Mixin):
    def __init__(self, path):
        self.conn = sqlite3.connect(path)
        self.conn.execute('CREATE TABLE IF NOT EXISTS accounts (id INTEGER PRIMARY KEY)')
        self.conn.execute('INSERT OR IGNORE INTO accounts(id) VALUES (1), (2)')
        self.conn.commit()
        self.create_experience_bank_schema_v2011()


def run_regression():
    checks = 0
    with tempfile.TemporaryDirectory(prefix='soulbound_xp_bank_') as folder:
        path = os.path.join(folder, 'bank.db')
        db = _TempBank(path)
        cap = experience_cap_v2009('character', 15)
        assert banked_experience_v2011(db, 1, cap * 8, 'character', 15) == cap
        assert db.experience_bank_rows_v2011(1) == [('character', '', cap * 7)]
        checks += 2
        assert banked_experience_v2011(db, 1, 20, 'character', 15) == cap
        assert db.experience_bank_rows_v2011(1)[0][2] == cap * 6 + 20
        checks += 2
        # When the award is larger than cap, a bank cannot pay anything extra.
        assert banked_experience_v2011(db, 1, cap * 3, 'character', 15) == cap
        assert db.experience_bank_rows_v2011(1)[0][2] == cap * 8 + 20
        checks += 2
        assert banked_experience_v2011(db, 2, 1, 'character', 15) == 1
        assert db.experience_bank_rows_v2011(2) == []
        checks += 2
        double = experience_cap_v2009('soul', 15) * 2
        assert banked_experience_v2011(db, 1, double * 4, 'soul', 15, overcap=True) == double
        assert db.experience_bank_rows_v2011(1)[1] == ('soul', '', double * 3)
        checks += 2
        for kind in KINDS:
            key = ('Siła' if kind == 'stat' else 'Mag' if kind == 'class' else
                   'mining' if kind == 'profession' else 'pickaxe' if kind == 'tool' else
                   'fireball' if kind == 'skill' else '')
            limit = experience_cap_v2009(kind, 50)
            paid = banked_experience_v2011(db, 1, limit * 2, kind, 50, source_key=key)
            assert paid == limit
            assert (kind, key, limit) in db.experience_bank_rows_v2011(1) or kind in ('character','soul')
            checks += 2
        # XP is not mixed between distinct stats, skills, classes and players.
        for kind, k1, k2 in (('stat', 'INT', 'WIS'), ('skill', 'fire', 'ice'),
                             ('class', 'MagNow', 'Wojownik'),
                             ('profession', 'fishing', 'mining_now'),
                             ('tool', 'rod', 'pickaxe_now')):
            lvl = 25
            limit = experience_cap_v2009(kind, lvl)
            assert banked_experience_v2011(db, 1, limit * 3, kind, lvl, source_key=k1) == limit
            assert banked_experience_v2011(db, 1, 2, kind, lvl, source_key=k2) == 2
            assert (kind, k1, limit * 2) in db.experience_bank_rows_v2011(1)
            checks += 3
        # SQLite signed int cannot store 10**40, TEXT bank must.
        huge = 10 ** 40
        assert banked_experience_v2011(db, 1, huge, 'character', 800) == experience_cap_v2009('character', 800)
        assert db.experience_bank_rows_v2011(1)[0][2] > 10 ** 39
        checks += 2
        db.conn.close()
        reopened = _TempBank(path)
        assert reopened.experience_bank_rows_v2011(1)[0][2] > 10 ** 39
        assert reopened.experience_bank_rows_v2011(2) == []
        checks += 2
        reopened.conn.close()
    # Commands readable using a minimal session, without a live world or network.
    import server as _server_ready_v2011
    from player.session_mixins.character_profile import SessionCharacterProfileMixin
    class _Dummy(SessionCharacterProfileMixin):
        def __init__(self):
            self.messages = []
            self.account_id = 1
            self.server = SimpleNamespace(db=_TempBank(':memory:'))
        async def send(self, msg):
            self.messages.append(str(msg))
    d = _Dummy()
    asyncio.run(d.show_exp_bank_v2011())
    assert any('pusty' in x for x in d.messages)
    d.server.db.allocate_experience_bank_v2011(1, 999999, 'character', '', 100)
    d.messages.clear()
    asyncio.run(d.show_exp_bank_v2011())
    assert any('Postać' in x and 'banku' in x for x in d.messages)
    assert any('nigdy nie przekracza' in x for x in d.messages)
    checks += 3
    d.server.db.conn.close()
    return checks


if __name__ == '__main__':
    print(f'EXP BANK v2.00.11: {run_regression()} checks PASS')
