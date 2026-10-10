# -*- coding: utf-8 -*-
"""Deterministic 2.00.3 regressions; temporary SQLite and synthetic actors only."""
import asyncio
import ast
from pathlib import Path
import sqlite3
import time
from types import SimpleNamespace

from core.promotion_patterns_v2003 import is_level_promotion_v2003

_ROOT = Path(__file__).resolve().parent.parent


def _real_methods(relative_file, class_name, names, env):
    """Execute unmodified methods extracted from actual code without full world boot."""
    tree = ast.parse((_ROOT / relative_file).read_text(encoding='utf-8'))
    found = next(node for node in tree.body if isinstance(node, ast.ClassDef)
                 and node.name == class_name)
    methods=[]
    for method in found.body:
        if isinstance(method, (ast.FunctionDef, ast.AsyncFunctionDef)) and method.name in names:
            method.decorator_list = []
            methods.append(method)
    assert len(methods) == len(names), (class_name, names)
    cls = ast.ClassDef(name=class_name, bases=[], keywords=[], body=methods,
                       decorator_list=[])
    module = ast.fix_missing_locations(ast.Module(body=[cls], type_ignores=[]))
    exec(compile(module, str(_ROOT / relative_file), 'exec'), env)
    return env[class_name]


World = _real_methods('world/world_state.py', 'World', {'refresh', 'room_mobs'},
                      {'time': time, 'MOB_TEMPLATES': {}})
MudServer = _real_methods('server/mud_server.py', 'MudServer',
    {'party_nearby_broadcast', 'broadcast_room', 'broadcast_all'}, {'asyncio': asyncio})
DatabaseCraftingExtensionsMixin = _real_methods('storage/db_crafting_extensions.py',
    'DatabaseCraftingExtensionsMixin', {'add_combat_event_v0320'}, {})


class _FakeSession:
    def __init__(self, account_id, room='a'):
        self.account_id = account_id
        self.character = SimpleNamespace(room_id=room)
        self.closed = False
        self.received = []
        self.barrier = None
        self.entered = None

    async def send(self, message, **kwargs):
        if self.barrier is not None:
            self.entered.append(self.account_id)
            if len(self.entered) == 3:
                self.barrier.set()
            await asyncio.wait_for(self.barrier.wait(), 2.0)
        self.received.append((message, kwargs))


async def _check_network():
    checks = 0
    server = object.__new__(MudServer)
    users = [_FakeSession(i) for i in (10, 20, 30)]
    outsider = _FakeSession(40, 'other')
    server.sessions = set(users + [outsider])
    server.party_key_for_account = lambda account: 1
    server.party_sessions = lambda account, same_room=None: [
        u for u in users if same_room is None or u.character.room_id == same_room
    ]
    barrier = asyncio.Event()
    entered = []
    for u in users:
        u.barrier = barrier
        u.entered = entered
    # Serial writes deadlock on this barrier: all receivers must start first.
    sent = await asyncio.wait_for(server.party_nearby_broadcast(users[0], 'Trafienie 123',
        detail='essential', history_category='combat'), 3.0)
    assert sent == 3 and len(entered) == 3
    checks += 2
    for u in users:
        assert u.received == [('Trafienie 123', {'combat_detail':'essential', 'history_category':'combat'})]
        checks += 1
    assert not outsider.received
    checks += 1
    for u in users:
        u.barrier = None
    await server.broadcast_room('a', 'Arena', exclude=users[0], history_category='world')
    assert len(users[0].received) == 1
    assert users[1].received[-1] == ('Arena', {'history_category': 'world'})
    assert not outsider.received
    checks += 3
    await server.broadcast_all('Serwer działa')
    assert all(u.received[-1][0] == 'Serwer działa' for u in users + [outsider])
    checks += 1
    return checks


def run_regression():
    checks = 0
    for message, expected in (
        ('Level postaci wzrasta do 8', True),
        ('Broń Duszy osiąga Soul Level 123', True),
        ('Kowalstwo: Biegłość rośnie do 5', True),
        ('Kowalstwo osiąga poziom 12', True),
        ('Boss ginie! Fame +1', False),
        ('Wilk trafia za 120 obrażeń', False),
        ('Level postaci wzrasta do ABC', False),
    ):
        assert bool(is_level_promotion_v2003(message)) is expected, message
        checks += 1

    world = object.__new__(World)
    world.mobs = {}
    world.corpses = {}
    world._last_refresh_at = 0.0
    world._refresh_min_interval = .25
    world._last_live_counts = {}
    world._last_live_by_room = {}
    for i in range(5000):
        room = 'arena' if i < 50 else 'distant'
        mob = SimpleNamespace(key=str(i), room_id=room, template_id='synthetic', hp=100,
                              alive=True, engaged_by=None, respawn_at=0,
                              home_room_id=room, next_wander_at=time.time()+999999)
        world.mobs[mob.key] = mob
    elapsed=[]
    for _ in range(4):
        world._last_refresh_at = 0.0
        start=time.perf_counter()
        counts=world.refresh()
        elapsed.append((time.perf_counter()-start)*1000)
        assert counts['arena']==50 and counts['distant']==4950
        checks += 1
        assert len(world.room_mobs('arena')) == 50
        checks += 1
    # No threshold on the user's CPU; raw timing is for comparisons only.
    print('ENGINE v2.00.3: 5000 synthetic mobs, 50 in AoE room; '
          f'refresh_avg_ms={sum(elapsed)/len(elapsed):.3f}', flush=True)
    # Expiry semantics must remain exact with multiple timer sources.
    now = time.time()
    expired = SimpleNamespace(key='expired', room_id='arena', alive=True,
        template_id='synthetic', hp=10, engaged_by=None, respawn_at=0,
        v016_expires_at=now-10)
    protected = SimpleNamespace(key='protected', room_id='arena', alive=True,
        template_id='synthetic', hp=10, engaged_by=None, respawn_at=0,
        v016_expires_at=now-10, v029_expires_at=now+100)
    negative = SimpleNamespace(key='negative', room_id='arena', alive=True,
        template_id='synthetic', hp=10, engaged_by=None, respawn_at=0,
        v016_expires_at=-1)
    world.mobs['expired'] = expired
    world.mobs['protected'] = protected
    world.mobs['negative'] = negative
    world._last_refresh_at = 0.0
    world.refresh()
    assert 'expired' not in world.mobs
    checks += 1
    assert 'protected' in world.mobs and protected in world.room_mobs('arena')
    checks += 1
    assert 'negative' in world.mobs and negative in world.room_mobs('arena')
    checks += 1
    world.mobs.clear()
    checks += 1

    conn=sqlite3.connect(':memory:')
    conn.execute('CREATE TABLE combat_events_v0320(id INTEGER PRIMARY KEY AUTOINCREMENT, '
                 'account_id INTEGER NOT NULL,event_text TEXT NOT NULL,event_kind TEXT, '
                 'created_at TEXT DEFAULT CURRENT_TIMESTAMP)')
    conn.execute('CREATE INDEX idx_combat_events_v0320_account ON combat_events_v0320(account_id,id DESC)')
    db=SimpleNamespace(conn=conn)
    for j in range(100):
        DatabaseCraftingExtensionsMixin.add_combat_event_v0320(db, 1, f'Hit {j}')
        if j % 2 == 0:
            DatabaseCraftingExtensionsMixin.add_combat_event_v0320(db, 2, f'Ally {j}')
    assert [r[0] for r in conn.execute('SELECT event_text FROM combat_events_v0320 WHERE account_id=1 ORDER BY id')] == [f'Hit {j}' for j in range(60,100)]
    checks += 1
    assert conn.execute('SELECT count(*) FROM combat_events_v0320 WHERE account_id=2').fetchone()[0] == 40
    checks += 1
    assert conn.execute('PRAGMA integrity_check').fetchone()[0] == 'ok'
    checks += 1
    conn.close()

    checks += asyncio.run(_check_network())
    return checks

if __name__=='__main__':
    print('ENGINE v2.00.3:',run_regression(), 'checks PASS')
