# -*- coding: utf-8 -*-
"""Isolated performance regression: no real player DB, no GitHub mutations."""
import contextlib
import io
import os
import socket
import sqlite3
import tempfile
import time
import sys
from pathlib import Path
from unittest.mock import patch
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) in sys.path: sys.path.remove(str(ROOT))
sys.path.insert(0, str(ROOT))


def run():
    checks = 0
    from systems.relic_runtime_index_v11320 import relic_candidates_v11320
    from data.catalog_mutations import catalog_assign, catalog_pop_path
    from core.perf_diagnostics_v11320 import begin, finish, current
    from storage.database import _DeferredCommitConnection

    # 203k item entries like actual Soulbound runtime, with 12 relics.
    items = {f'item_{i}': {'type': 'material'} for i in range(203100)}
    for i in range(12):
        items[f'relic_{i}'] = {'type':'soul_weapon_relic', 'name': f'Relikt {i}'}
    before = time.perf_counter()
    for _ in range(30):
        old = tuple(item_id for item_id,item in items.items() if item.get('type') == 'soul_weapon_relic')
    old_time = time.perf_counter() - before
    before = time.perf_counter()
    for _ in range(30):
        new = tuple(item_id for item_id,_ in relic_candidates_v11320(items))
    new_time = time.perf_counter() - before
    assert old == new and len(new) == 12; checks += 1
    assert new_time < old_time; checks += 1
    catalog_assign({'type':'soul_weapon_relic'},'ITEMS',items,('added',))
    assert len(list(relic_candidates_v11320(items))) == 13; checks += 1
    catalog_pop_path('ITEMS',items,(), 'added')
    assert len(list(relic_candidates_v11320(items))) == 12; checks += 1
    # Same-length change: controlled mutation invalidates the index immediately.
    catalog_assign({'type':'soul_weapon_relic'},'ITEMS',items,('item_2',))
    assert len(list(relic_candidates_v11320(items))) == 13; checks += 1
    catalog_assign({'type':'material'},'ITEMS',items,('item_2',))
    assert len(list(relic_candidates_v11320(items))) == 12; checks += 1
    # Same-ID dictionary replacement is read live, not a stale object.
    before_relic = dict(items['relic_0'])
    items['relic_0'] = {'type':'soul_weapon_relic','name':'Nowy relikt'}
    assert dict(relic_candidates_v11320(items))['relic_0']['name'] == 'Nowy relikt'; checks += 1
    items['relic_0'] = before_relic

    # SQLite instrumentation preserves real cursor, commit, and transaction.
    conn = sqlite3.connect(':memory:')
    db = _DeferredCommitConnection(conn)
    scope, token = begin('use')
    db.execute('CREATE TABLE x(a INTEGER)')
    db.executemany('INSERT INTO x VALUES(?)', [(1,), (2,), (3,)])
    db.commit()
    assert db.execute('SELECT COUNT(*) FROM x').fetchone()[0] == 3; checks += 1
    assert scope.sql_queries == 3 and scope.sql_commits == 1; checks += 1
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf): finish(scope,token,minimum=0)
    output=buf.getvalue()
    assert '[PERF DETAIL] use:' in output and 'SQLite=3 zapytan' in output; checks += 1
    assert current() is None; checks += 1
    # Nested SAVEPOINT errors still rollback without partial progress.
    with db.deferred_commits():
        db.execute('INSERT INTO x VALUES (4)')
        expected_rollback_failure = False
        try:
            with db.deferred_commits():
                db.execute('INSERT INTO x VALUES (99)')
                raise RuntimeError('simulated failure')
        except RuntimeError as exc:
            assert str(exc) == 'simulated failure', f'unexpected rollback error: {exc}'
            expected_rollback_failure = True
        assert expected_rollback_failure, 'injected failure was not raised'
    assert [r[0] for r in db.execute('SELECT a FROM x ORDER BY a')] == [1,2,3,4];checks += 1
    assert not conn.in_transaction; checks += 1
    conn.close()

    # Load the real Session MRO only with a verified isolated, private test DB.
    with tempfile.TemporaryDirectory(prefix='sb-current-perf-profile_') as td:
        os.environ['SOULBOUND_UNIVERSAL_STAGING'] = '1'
        os.environ['SOULBOUND_HOST'] = '127.0.0.1'
        os.environ['SOULBOUND_DB'] = td+'/test.sqlite'
        with socket.socket() as s:
            s.bind(('127.0.0.1',0))
            os.environ['SOULBOUND_PORT'] = str(s.getsockname()[1])
        import server
        from player.session import Session
        from player.session_mixins.equipment_stats import SessionEquipmentStatsMixin
        assert super(Session,Session).max_hp.__qualname__ == 'SessionEquipmentStatsMixin.max_hp';checks += 1
        assert super(Session,Session).max_mana.__qualname__ == 'SessionEquipmentStatsMixin.max_mana';checks += 1
        assert len(server.ITEMS) >= 200000;checks += 1
        class Stub(Session):
            pass
        actor = Stub.__new__(Stub)
        snapshots = []
        def fake_calculate(self):
            cache = self.__dict__['_read_only_equipment_cache_v1262']
            snapshots.append(cache)
            cache['thing'] = 1
            return 999
        with patch.object(SessionEquipmentStatsMixin, 'max_hp', fake_calculate), patch.object(SessionEquipmentStatsMixin, 'max_mana', fake_calculate):
            assert actor.max_hp() == 999 and actor.max_mana() == 999;checks += 1
            assert len(snapshots) == 2 and snapshots[0] is not snapshots[1];checks += 1
            assert '_read_only_equipment_cache_v1262' not in actor.__dict__; checks += 1
            actor._read_only_equipment_cache_v1262 = {'external':'marker'}
            assert actor.max_hp() == 999;checks += 1
            assert actor._read_only_equipment_cache_v1262 == {'external':'marker','thing':1};checks += 1
            actor.__dict__.pop('_read_only_equipment_cache_v1262')
        # Actual current world items: relic candidates must mirror direct filtering.
        actual = tuple(relic_candidates_v11320(server.ITEMS))
        ground_truth = tuple((k,v) for k,v in server.ITEMS.items()
                            if isinstance(v,dict) and v.get('type') == 'soul_weapon_relic')
        assert actual == ground_truth;checks += 1

    print(f'CURRENT PERF 113.00.20: {checks}/{checks} PASS. '
          f'203k item synthetic scan 30x: old={old_time*1000:.1f}ms '
          f'new={new_time*1000:.1f}ms',flush=True)
    return checks

if __name__=='__main__':run()
