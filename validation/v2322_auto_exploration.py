# -*- coding: utf-8 -*-
"""Regression: automatic EP on room arrival, not on manually requested exploration."""
from __future__ import annotations
import ast
import asyncio
from contextlib import closing
from pathlib import Path
import sqlite3
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def run_regression():
    # Make the important navigation path a release-blocking gate: guided
    # transitions can omit look(), yet must never omit discovering the room.
    content = (ROOT / "player/session_mixins/movement.py").read_text(encoding="utf-8")
    tree = ast.parse(content)
    movement = next(c for c in tree.body if isinstance(c, ast.ClassDef)
                    and c.name == "SessionMovementMixin")
    transition = next(f for f in movement.body if isinstance(f, ast.AsyncFunctionDef)
                      and f.name == "walk_room_transition")
    calls = [(getattr(n, 'lineno', 0), n) for n in ast.walk(transition)
             if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
             and n.func.attr == 'discover_current_room']
    assert len(calls) == 1, "Missing/duplicate EP trigger for quiet guided movement"
    checks = 1
    gate = [n for n in ast.walk(transition) if isinstance(n, ast.If)
            and isinstance(n.test, ast.UnaryOp) and isinstance(n.test.op, ast.Not)
            and isinstance(n.test.operand, ast.Name) and n.test.operand.id == 'show_room'
            and any(n.lineno <= lineno <= n.end_lineno for lineno, _ in calls)]
    assert len(gate) >= 1, "Quiet guided movement must trigger discovery"
    checks += 1

    # Compile the exact production methods in a small isolated namespace;
    # the historical mixin cannot be imported until the complete world has booted.
    from systems.milestone_cap_rewards_v2103 import exploration_point_xp_v2103
    from systems.exploration_point_values_v2322 import room_explorer_points_v2322, zone_explorer_points_v2322
    progress_src = (ROOT / "player/session_mixins/exploration_progress.py").read_text(encoding="utf-8")
    progress_tree = ast.parse(progress_src)
    progress_class = next(node for node in progress_tree.body if isinstance(node, ast.ClassDef)
                          and node.name == "SessionExplorationProgressMixin")
    real_methods = [node for node in progress_class.body if isinstance(node, ast.AsyncFunctionDef)
                    and node.name in ('discover_room', 'discover_current_room')]
    assert len(real_methods) == 2
    checks += 1
    source_class = ast.ClassDef(name='SessionExplorationProgressMixin', bases=[], keywords=[],
                                body=real_methods, decorator_list=[])
    ast.fix_missing_locations(source_class)
    namespace = {
        'ROOMS': {'ep2322_room': {'name': 'Testowa lokacja', 'zone': 'Test EP', 'level': 184},
                  'ep2322_hard': {'name': 'Trudny szczyt', 'zone': 'Test EP', 'level': 450}},
        'INSTANCE_MAP_DEFS': {}, 'instance_room_identity': lambda room: (None, None),
        'instance_secret_index': lambda *args: None,
        'EXPLORATION_ZONE_ROOMS': {'Test EP': ('ep2322_room', 'ep2322_hard')},
        'EXPLORATION_ZONE_MIN_ROOMS': 3,
        'ALL_EXPLORATION_ROOMS': {'ep2322_room', 'ep2322_hard'}, 'TRACKED_EXPLORATION_ZONES': set(),
        'exploration_find_v11324': lambda *args: None,
        'random': __import__('random'),
    }
    exec(compile(ast.Module(body=[source_class], type_ignores=[]), str(ROOT), 'exec'), namespace)
    RealMixin = namespace['SessionExplorationProgressMixin']

    class DB:
        def __init__(self):
            self.conn = sqlite3.connect(':memory:')
            self.conn.execute('CREATE TABLE exploration_rooms (account_id INTEGER, room_id TEXT, '
                              'PRIMARY KEY (account_id,room_id))')
            self.counters = {}
            self.awards = {}
        def mark_room_discovered_with_points_v2322(self, account_id, room_id, points):
            cursor = self.conn.execute('INSERT OR IGNORE INTO exploration_rooms VALUES (?, ?)',
                                       (account_id, room_id))
            if not cursor.rowcount:
                return False
            self.awards[(account_id, room_id)] = points
            self.add_lifetime_stat(account_id, 'rooms_discovered', 1)
            self.add_lifetime_stat(account_id, 'explorer_points', points)
            self.conn.commit()
            return True
        def exploration_room_point_awards_v2322(self, account_id):
            return {room: value for (who, room), value in self.awards.items() if who == account_id}
        def discovered_room_ids(self, account_id):
            return {row[0] for row in self.conn.execute(
                'SELECT room_id FROM exploration_rooms WHERE account_id=?', (account_id,))}
        def add_lifetime_stat(self, account_id, key, amount):
            self.counters[(account_id, key)] = self.counters.get((account_id, key), 0) + amount
        def claim_exploration_reward(self, account_id, zone):
            return False

    class Session(RealMixin):
        def __init__(self, db, account_id):
            self.server = SimpleNamespace(db=db)
            self.account_id = account_id
            self.character = SimpleNamespace(room_id='ep2322_room', character_level=184, silver=0)
            self.awards = []
            self.messages = []
        def add_character_xp_with_event(self, amount, **kwargs):
            assert kwargs.get('content_scaled') is True
            self.awards.append(int(amount))
            return []
        async def send(self, message):
            self.messages.append(str(message))
        async def advance_class_guild_quest_v11132(self, *args):
            return None
        async def set_achievement_progress(self, *args):
            return None
        async def sync_global_discovery_atlas_v1120(self, **kwargs):
            return None

    db = DB()
    a = Session(db, 111)
    b = Session(db, 222)
    async def scenarios():
        assert await a.discover_current_room(announce=True) is True
        assert await a.discover_current_room(announce=True) is False
        assert await a.discover_room('ep2322_room', announce=False) is False
        assert await b.discover_current_room(announce=True) is True
        assert await b.discover_current_room(announce=True) is False
    try:
        asyncio.run(scenarios())
    finally:
        db.conn.close()
    expected_ep = room_explorer_points_v2322(namespace['ROOMS']['ep2322_room'])
    assert expected_ep == 3
    checks += 1
    assert len(a.awards) == expected_ep and len(b.awards) == expected_ep
    checks += 1
    cap = exploration_point_xp_v2103(a.character)
    assert a.awards == [cap] * expected_ep and b.awards == [cap] * expected_ep
    checks += 1
    assert a.messages.count(next(m for m in a.messages if 'Odkrycie lokacji: +3 EP' in m)) == 1
    checks += 1
    assert db.counters[(111, 'explorer_points')] == expected_ep
    assert db.counters[(222, 'explorer_points')] == expected_ep
    checks += 1
    assert room_explorer_points_v2322({'level': 401}) == 6
    assert room_explorer_points_v2322({'level': 401, 'v0140_secret_room': True}) == 8
    assert room_explorer_points_v2322({'level': 99999}) == 8
    assert room_explorer_points_v2322({'level': 401, 'exploration_ep': 13}) == 13
    checks += 4
    earned, maximum = zone_explorer_points_v2322(
        ('ep2322_room', 'ep2322_hard'), {'ep2322_room'},
        {'ep2322_room': expected_ep}, namespace['ROOMS'])
    assert earned == expected_ep and maximum == expected_ep + 6
    checks += 1
    # Existing discoveries with no new ledger entry retain historic 1 EP.
    assert zone_explorer_points_v2322(('ep2322_hard',), {'ep2322_hard'}, {},
                                       namespace['ROOMS']) == (1, 1)
    checks += 1
    # Test the production atomic SQLite methods directly, without importing
    # the full runtime or touching a production database.
    storage_tree = ast.parse((ROOT / 'storage/db_world.py').read_text('utf8'))
    storage_class = next(n for n in storage_tree.body if isinstance(n, ast.ClassDef)
                         and n.name == 'DatabaseWorldMixin')
    method_names = {'mark_room_discovered_with_points_v2322',
                    'exploration_room_point_awards_v2322'}
    methods = [n for n in storage_class.body if isinstance(n, ast.FunctionDef)
               and n.name in method_names]
    assert len(methods) == 2
    code = ast.ClassDef(name='RealWorldDB', bases=[], keywords=[],
                        body=methods, decorator_list=[])
    ast.fix_missing_locations(code)
    db_ns = {}
    exec(compile(ast.Module(body=[code], type_ignores=[]), str(ROOT), 'exec'), db_ns)
    class LiveDB(db_ns['RealWorldDB']):
        def __init__(self, connection):
            self.conn = connection
    import tempfile
    with tempfile.TemporaryDirectory(prefix='ep2322-') as scratch:
        file_name = str(Path(scratch) / 'real.sqlite')
        # sqlite3.Connection.__exit__ commits but DOES NOT close the handle.
        # On Windows this locks real.sqlite when TemporaryDirectory cleans up.
        # Keep both transactional exit and guaranteed close, even on errors.
        with closing(sqlite3.connect(file_name)) as conn, conn:
            conn.row_factory = sqlite3.Row
            conn.executescript('''CREATE TABLE exploration_rooms(account_id INTEGER,room_id TEXT,PRIMARY KEY(account_id,room_id));
                CREATE TABLE exploration_room_points_v2322(account_id INTEGER,room_id TEXT,ep_points INTEGER,PRIMARY KEY(account_id,room_id));
                CREATE TABLE lifetime_statistics(account_id INTEGER,stat_key TEXT,value INTEGER,updated_at TEXT,
                    PRIMARY KEY(account_id,stat_key));''')
            first_connection = conn
            # Old room must not be awarded again or re-weighted.
            conn.execute('INSERT INTO exploration_rooms VALUES (?, ?)', (44, 'old_room'))
            conn.execute('INSERT INTO lifetime_statistics(account_id,stat_key,value) VALUES(?,?,?)',
                         (44, 'explorer_points', 1))
            conn.commit()
            live = LiveDB(conn)
            assert live.mark_room_discovered_with_points_v2322(44, 'old_room', 6) is False
            assert live.mark_room_discovered_with_points_v2322(44, 'new_room', 6) is True
            assert live.mark_room_discovered_with_points_v2322(44, 'new_room', 6) is False
            assert live.exploration_room_point_awards_v2322(44) == {'new_room': 6}
            assert conn.execute("SELECT value FROM lifetime_statistics WHERE account_id=44 AND stat_key='explorer_points'").fetchone()[0] == 7
        # sqlite3.Connection.__exit__ commits but DOES NOT close the handle.
        # On Windows this locks real.sqlite when TemporaryDirectory cleans up.
        # Keep both transactional exit and guaranteed close, even on errors.
        with closing(sqlite3.connect(file_name)) as conn, conn:
            conn.row_factory = sqlite3.Row
            assert LiveDB(conn).exploration_room_point_awards_v2322(44) == {'new_room': 6}
        checks += 6
        # A successful commit is not proof of releasing the Windows file lock.
        # Both real SQLite handles must reject further work after their blocks.
        def assert_sqlite_closed(connection):
            try:
                connection.execute('SELECT 1')
            except sqlite3.ProgrammingError:
                return
            raise AssertionError('SQLite handle still open after regression block')

        assert_sqlite_closed(conn)
        checks += 1
        # The two connection blocks both close. First connection also must stay closed.
        assert_sqlite_closed(first_connection)
        checks += 1
        # Windows does not allow deleting an open database. Check the cleanup
        # now, before TemporaryDirectory.__exit__, so failures are actionable.
        Path(file_name).unlink()
        assert not Path(file_name).exists()
        checks += 1
    return checks


if __name__ == '__main__':
    print(f'AUTO EP v2.32.2: {run_regression()} checks PASS')
