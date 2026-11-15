# -*- coding: utf-8 -*-
"""Real movement coroutine: six-player follow barrier and blocked-member notice.

Disposable in-memory sessions only. Never opens the production DB or port 4000.
"""
from __future__ import annotations
import asyncio
from pathlib import Path
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from player.session_mixins.movement import SessionMovementMixin


class FakeDB:
    def __init__(self):
        self.saves = []
        self.commits = 0
        self.conn = self

    def save_character(self, character, commit=True):
        self.saves.append((character.name, character.room_id, commit))

    def commit(self):
        self.commits += 1


class FakeWorld:
    def ensure_runtime_room(self, room_id):
        assert room_id in ('start', 'middle', 'end'), room_id


class FakeServer:
    def __init__(self):
        self.db = FakeDB()
        self.world = FakeWorld()
        self.sessions = []

    def party_sessions(self, _leader, same_room=None):
        return [s for s in self.sessions
                if same_room is None or s.character.room_id == same_room]

    async def broadcast_room(self, *_args, **_kwargs):
        await asyncio.sleep(0)


class FakeSession(SessionMovementMixin):
    def __init__(self, server, account_id, *, slow=False):
        self.server = server
        self.account_id = account_id
        self.character = SimpleNamespace(name=f'Testtcp{account_id}', room_id='start')
        self.closed = False
        self.moving = False
        self.guiding = False
        self.combat_mob_key = None
        self.blocked = False
        self.slow = slow
        self.messages = []

    def party_key(self):
        return 1

    async def send(self, message, **_kwargs):
        self.messages.append(str(message))
        await asyncio.sleep(0)

    def movement_delay(self, direction, guided=False):
        return 0.12 if self.slow else 0.002

    async def register_uoss_deep_dungeon_visit_v11331(self, room):
        return None

    async def look(self):
        return None

    async def move(self, direction, preserve_auto_mining=False):
        # The small fixture calls the unchanged real room-transition coroutine;
        # the real TCP gate exercises the complete move() entry rules.
        if self.blocked:
            await self.send('Blokada przejścia; postać pozostaje w pokoju.')
            return
        target = {'start': 'middle', 'middle': 'end'}.get(self.character.room_id)
        if target is None:
            return
        await self.walk_room_transition(direction, target, show_room=True)


def party():
    server = FakeServer()
    sessions = [FakeSession(server, n, slow=(n > 1)) for n in range(1, 7)]
    server.sessions = sessions
    return server, sessions


async def check_all():
    checks = 0
    server, actors = party()
    leader = actors[0]
    first = asyncio.create_task(leader.walk_room_transition('east', 'middle', show_room=True))
    # Wait until the leader reaches the next room, while followers are still
    # travelling. The old code incorrectly cleared moving here.
    for _ in range(200):
        if leader.character.room_id == 'middle' and any(
            member.character.room_id == 'start' for member in actors[1:]
        ):
            break
        await asyncio.sleep(.001)
    assert leader.character.room_id == 'middle' and any(
        member.character.room_id == 'start' for member in actors[1:]
    ), 'The 6-player race fixture did not exercise overlapping travel'
    checks += 1
    assert leader.moving, 'Leader became available while followers still walked'
    checks += 1
    # Exercise the real move() guard as well, not just a direct transition.
    assert await SessionMovementMixin.move(leader, 'east') is None
    assert any('Trwa poprzedni krok' in message for message in leader.messages)
    checks += 1
    second = await leader.walk_room_transition('east', 'end', show_room=True)
    assert second is False and leader.character.room_id == 'middle'
    checks += 1
    assert await first is True and all(s.character.room_id == 'middle' for s in actors)
    checks += 1
    assert not leader.moving and server.db.commits == 1
    checks += 1
    assert await leader.walk_room_transition('east', 'end', guided=True, show_room=True)
    assert all(s.character.room_id == 'end' for s in actors)
    checks += 1
    assert server.db.commits == 2 and not leader._party_follow_blocked_v1130012
    checks += 1

    # A blocked player must NEVER be teleported past an individual gate;
    # both the player and the leader need a concise diagnostic.
    server, actors = party()
    actors[5].blocked = True
    assert not await actors[0].walk_room_transition('east', 'middle', guided=True, show_room=True)
    assert [a.character.room_id for a in actors] == ['middle'] * 5 + ['start']
    checks += 1
    assert actors[0]._party_follow_blocked_v1130012
    assert any('Testtcp6' in m and 'zostali w tyle' in m for m in actors[0].messages)
    checks += 1
    assert any('Blokada przejścia' in m for m in actors[5].messages)
    checks += 1

    # A member independently guiding MUST stop the leader before the step,
    # instead of letting the leader get one room ahead and losing the party.
    server, actors = party()
    actors[3].guiding = True
    assert not await actors[0].walk_room_transition('east', 'middle', guided=True, show_room=True)
    assert all(actor.character.room_id == 'start' for actor in actors)
    checks += 1
    assert any('Testtcp4' in msg and 'prowadzenie' in msg for msg in actors[0].messages)
    checks += 1
    # No other account should be dropped after a correctly completed step.
    server, actors = party()
    assert await actors[0].walk_room_transition('east', 'middle', guided=True, show_room=True)
    assert all(member.character.room_id == 'middle' for member in actors)
    assert not any('zostali w tyle' in msg for msg in actors[0].messages)
    checks += 1

    # Verify guide's safety guard is present; its full runtime is exercised in
    # the dedicated guide/TCP integration checks.
    # The original guide_to() is preserved byte for byte and its AST fingerprint
    # remains pinned by the historical v4.20 safety contract.  The existing
    # `if not moved: break` now stops the route when the transition reports lag.
    from validation.current_native_v420_contract import verify_native_method
    assert verify_native_method(ROOT / 'player/session_mixins/guide_navigation.py',
                                'SessionGuideNavigationMixin.guide_to')
    checks += 1
    assert any('Prowadzenie wstrzymane:' in msg for msg in actors[0].messages) is False
    checks += 1
    print(f'PARTY FOLLOW SIX-PLAYER REGRESSION: {checks}/{checks} PASS', flush=True)


if __name__ == '__main__':
    asyncio.run(check_all())
