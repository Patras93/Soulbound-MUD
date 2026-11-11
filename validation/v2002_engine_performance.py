# -*- coding: utf-8 -*-
"""Regression guards for v2.00.2 hot paths, on disposable SQLite only."""
import sqlite3
from types import SimpleNamespace

from core import performance_v2002 as perf
from player.session_mixins.era_sky_v1700 import SessionSkyV1700Mixin, ensure_schema
from storage.db_crafting_extensions import DatabaseCraftingExtensionsMixin


def run_regression():
    checks = 0
    # The instrumentation must be completely inert by default.
    def test_sync():
        return 1
    async def test_async():
        return 1
    if not perf._ENABLED:
        assert perf.measure_sync('test')(test_sync) is test_sync
        assert perf.measure_async('test')(test_async) is test_async
    checks += 2

    # Real schema, several classes of summoned creatures, one HP calculation.
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    ensure_schema(conn)
    for kind in ('wojownik', 'mag', 'wilk', 'ogien_maly'):
        if kind not in __import__('player.session_mixins.era_sky_v1700', fromlist=['SUMMONS']).SUMMONS:
            kind = 'sowa'
        conn.execute('INSERT INTO summons_v1700(account_id,summon_type,level,active,soul_rank,hp,max_hp,xp) '
                     'VALUES(42,?,1,1,2,200,1000,77)', (kind,))
    conn.commit()
    class Dummy(SessionSkyV1700Mixin):
        def __init__(self):
            self.account_id = 42
            self.character = SimpleNamespace(character_level=102)
            self.hp_calls = 0
            self.server = SimpleNamespace(db=SimpleNamespace(conn=conn, _v1700_ready=True))
        def max_hp(self):
            self.hp_calls += 1
            return 10000
    session = Dummy()
    changed = session._v1710_refresh_summon_health(conn)
    assert changed == 4
    checks += 1
    assert session.hp_calls == 1, session.hp_calls
    checks += 1
    results = conn.execute('SELECT * FROM summons_v1700 WHERE account_id=42').fetchall()
    assert len(results) == 4 and all(r['level'] == 102 and r['xp'] == 0 and r['soul_rank'] == 2 for r in results)
    checks += 1
    assert all(0 < r['hp'] <= r['max_hp'] for r in results)
    checks += 1
    assert session._v1710_refresh_summon_health(conn) == 0
    checks += 1
    conn.close()

    # A real DB method, not a mock of the SQL, retains exactly the last 40
    # durable messages per account, in order, and does not mix accounts.
    con = sqlite3.connect(':memory:')
    con.execute('CREATE TABLE combat_events_v0320(id INTEGER PRIMARY KEY AUTOINCREMENT, '
                'account_id INTEGER NOT NULL, event_text TEXT, event_kind TEXT, '
                'created_at TEXT DEFAULT CURRENT_TIMESTAMP)')
    con.execute('CREATE INDEX idx_combat_events_v0320_account '
                'ON combat_events_v0320(account_id,id DESC)')
    db = SimpleNamespace(conn=con)
    for idx in range(135):
        DatabaseCraftingExtensionsMixin.add_combat_event_v0320(db, 10, f'attack-{idx}', 'combat')
        if idx % 3 == 0:
            DatabaseCraftingExtensionsMixin.add_combat_event_v0320(db, 20, f'ally-{idx}', 'combat')
    own = [r[0] for r in con.execute('SELECT event_text FROM combat_events_v0320 WHERE account_id=10 ORDER BY id')]
    ally = [r[0] for r in con.execute('SELECT event_text FROM combat_events_v0320 WHERE account_id=20 ORDER BY id')]
    assert own == [f'attack-{n}' for n in range(95,135)]
    checks += 1
    assert ally == [f'ally-{n}' for n in range(15,135,3)]
    checks += 1
    assert con.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
    checks += 1
    con.close()
    return checks
