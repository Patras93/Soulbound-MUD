# -*- coding: utf-8 -*-
"""v106: jedna informacja o wylogowaniu dla wszystkich postaci online.

Real methods extracted from release source. All recipients and DB writes are
synthetic; no production DB or real client is accessed.
"""
from __future__ import annotations

import ast
import asyncio
from pathlib import Path
import sys
import types
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def _real_class(relpath, name, method_names, env):
    tree = ast.parse((ROOT / relpath).read_text(encoding='utf-8'))
    source_class = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == name)
    methods = []
    for node in source_class.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name in method_names:
            node.decorator_list = []
            methods.append(node)
    assert {m.name for m in methods} == set(method_names), name
    cls = ast.ClassDef(name=name, bases=[], keywords=[], body=methods, decorator_list=[])
    unit = ast.fix_missing_locations(ast.Module(body=[cls], type_ignores=[]))
    exec(compile(unit, str(ROOT / relpath), 'exec'), env)
    return env[name]


MudServer = _real_class('server/mud_server.py', 'MudServer',
                        {'broadcast_all'}, {'asyncio': asyncio})
CommandLoop = _real_class('player/session_mixins/command_loop.py',
                          'SessionCommandLoopMixin',
                          {'close', 'leave_current_character_for_selection'}, {})


class FakeDB:
    def __init__(self):
        self.saved = []
        self.logouts = []

    def save_character(self, character):
        self.saved.append(character.name)

    def mark_player_logout_v0363(self, account_id):
        self.logouts.append(account_id)


class FakeWriter:
    def __init__(self):
        self.closed = False
        self.waited = False

    def close(self):
        self.closed = True

    async def wait_closed(self):
        self.waited = True


class Player(CommandLoop):
    def __init__(self, server, name, room='city', account_id=1, *, in_world=True):
        self.server = server
        self.character = SimpleNamespace(name=name, room_id=room) if in_world else None
        self.account_id = account_id if in_world else None
        self.closed = False
        self.writer = FakeWriter()
        self.received = []
        self.resting = False
        self.rest_task = None
        self.auto_fishing = False
        self.auto_fishing_task = None
        self.auto_mining = False
        self.auto_mining_task = None
        self.auto_woodcutting = False
        self.auto_woodcutting_task = None
        self.auto_herbalism = False
        self.auto_herbalism_task = None
        self.current_hp = 100
        self.current_mana = 50
        self.guide_choice_state = None

    async def send(self, text, **kwargs):
        self.received.append((text, kwargs))

    def clear_downed_v0371(self, **kwargs):
        return None

    def guide_task_active(self):
        return False

    async def cancel_guide(self, *args, **kwargs):
        return None

    async def stop_rest(self, *args, **kwargs):
        return None

    async def stop_smelt_v1124(self, *args, **kwargs):
        return None

    async def stop_standing_regen_v1124(self):
        return None

    async def stop_auto_fishing(self, **kwargs):
        return None

    async def stop_auto_mining(self, **kwargs):
        return None

    async def stop_auto_woodcutting(self, **kwargs):
        return None

    async def stop_auto_herbalism(self, **kwargs):
        return None

    async def leave_party(self, **kwargs):
        return None

    async def stop_realtime_combat(self):
        return None

    async def show_session_summary(self):
        return None


async def check():
    count = 0
    server = object.__new__(MudServer)
    server.db = FakeDB()
    server.release_all_engagements_for_session = lambda session: None

    async def disconnect(session):
        return None

    fake_bridge = types.ModuleType('systems.admin_live_bridge_v10200')
    fake_bridge.disconnect = disconnect

    with patch.dict(sys.modules, {'systems.admin_live_bridge_v10200': fake_bridge}):
        owner = Player(server, 'Sympatyczna', 'tower_floor_1', 1)
        near = Player(server, 'Ragnar', 'tower_floor_1', 2)
        far = Player(server, 'Lili', 'temple', 3)
        unauth = Player(server, 'Logowanie', in_world=False)
        offline = Player(server, 'Offline', 'city', 5)
        offline.closed = True
        server.sessions = {owner, near, far, unauth, offline}

        await server.broadcast_all('Próba ogłoszenia', history_category='system', exclude=owner)
        assert owner.received == []
        assert near.received == [('Próba ogłoszenia', {'history_category': 'system'})]
        assert far.received == near.received
        assert unauth.received == [] and offline.received == []
        count += 5
        near.received.clear()
        far.received.clear()

        # `quit` to return to character selection, even though TCP remains alive.
        await owner.leave_current_character_for_selection()
        expected = ('Gracz Sympatyczna wylogował się.', {'history_category': 'system'})
        assert near.received == [expected] and far.received == [expected]
        assert not owner.received and not unauth.received and not offline.received
        assert server.db.saved == ['Sympatyczna'] and server.db.logouts == [1]
        assert owner.character is None and owner.account_id is None and not owner.closed
        count += 4

        # A subsequent physical disconnect must NOT repeat the notification.
        await owner.close()
        await owner.close()
        assert near.received == [expected] and far.received == [expected]
        assert owner.writer.closed and owner.writer.waited
        assert server.db.saved == ['Sympatyczna'] and server.db.logouts == [1]
        count += 3

        # Sudden TCP drop from another room: same message, one time only.
        far.received.clear()
        guest = Player(server, 'Testtcp3', 'crypt', 6)
        server.sessions.add(guest)
        await guest.close()
        expected_guest = ('Gracz Testtcp3 wylogował się.', {'history_category': 'system'})
        assert near.received == [expected, expected_guest]
        assert far.received == [expected_guest]
        assert not guest.received
        assert server.db.saved[-1] == 'Testtcp3' and server.db.logouts[-1] == 6
        count += 4
        await guest.close()
        assert near.received == [expected, expected_guest]
        count += 1

        # No announcement for connection that never selected a character.
        before = near.received[:]
        await unauth.close()
        assert near.received == before and unauth.writer.closed
        count += 1

        # Old `broadcast_all(text)` behavior remains compatible.
        await server.broadcast_all('Test globalny')
        assert near.received[-1] == ('Test globalny', {'history_category': None})
        assert far.received[-1] == ('Test globalny', {'history_category': None})
        assert not unauth.received and not offline.received
        count += 3

    print(f'V106 WYLOGOWANIE: {count} kontroli PASS – nazwa postaci, globalny odbior, brak duplikatow, TCP.')
    return count


if __name__ == '__main__':
    asyncio.run(check())
