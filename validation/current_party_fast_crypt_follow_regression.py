# -*- coding: utf-8 -*-
"""Real six-player follow transitions during rapid crypt guidance/combat.

Synthetic sessions and DB: no production port, characters or persistent SQLite.
"""
from __future__ import annotations
import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from validation.current_party_follow_regression import party as make_party, FakeSession
from types import MethodType


def party():
    server, actors = make_party()
    server.db.mercenary_contracts = lambda _account_id: []
    return server, actors


async def run_cases():
    checks = 0

    # A member is still attacking when the leader starts `walk krypta dol`.
    server, actors = party()
    leader = actors[0]
    actors[4].combat_mob_key = 'crypt_mob:5'
    assert not await leader.walk_room_transition('east', 'middle', guided=True, show_room=False)
    assert [a.character.room_id for a in actors] == ['start'] * 6
    checks += 1
    assert not server.db.saves and server.db.commits == 0
    checks += 1
    assert any('Testtcp5' in msg and 'walka' in msg for msg in leader.messages)
    checks += 1
    actors[4].combat_mob_key = None
    assert await leader.walk_room_transition('east', 'middle', guided=True, show_room=True)
    assert [a.character.room_id for a in actors] == ['middle'] * 6
    checks += 1
    assert await leader.walk_room_transition('east', 'end', guided=True, show_room=True)
    assert [a.character.room_id for a in actors] == ['end'] * 6
    checks += 1

    # A follower is on another route / still moving: no premature descent.
    for attr, reason in [('moving', 'ruch'), ('guiding', 'prowadzenie')]:
        server, actors = party()
        setattr(actors[2], attr, True)
        assert not await actors[0].walk_room_transition('east', 'middle', guided=True)
        assert [a.character.room_id for a in actors] == ['start'] * 6
        assert any('Testtcp3' in msg and reason in msg for msg in actors[0].messages)
        checks += 1
        setattr(actors[2], attr, False)
        assert await actors[0].walk_room_transition('east', 'middle', guided=True)
        assert all(a.character.room_id == 'middle' for a in actors)
        checks += 1

    # A per-account gate rejects the follower AFTER the leader's first move.
    # In the old version the leader could then issue another `walk` and leave
    # the blocked member even farther behind. Hold the stop until regrouping.
    server, actors = party()
    leader = actors[0]
    actors[5].blocked = True
    assert not await leader.walk_room_transition('east', 'middle', guided=True)
    assert [a.character.room_id for a in actors] == ['middle'] * 5 + ['start']
    checks += 1
    assert getattr(leader, '_party_follow_blocked_v1130012', False)
    assert not await leader.walk_room_transition('east', 'end', guided=True)
    assert [a.character.room_id for a in actors] == ['middle'] * 5 + ['start']
    checks += 1
    assert any('Testtcp6' in m and 'rozdzielona' in m for m in leader.messages)
    checks += 1
    # The leader can RETURN along the real room edge to the left-behind
    # follower.  Four other members follow backward. No teleport is used.
    async def reverse_move(self, direction):
        if direction == 'west' and self.character.room_id == 'middle':
            await self.walk_room_transition('west', 'start', show_room=True)
        else:
            await FakeSession.move(self, direction)
    for actor in actors[1:]:
        actor.move = MethodType(reverse_move, actor)
    assert await leader.walk_room_transition('west', 'start', show_room=True)
    assert all(a.character.room_id == 'start' for a in actors)
    checks += 1
    assert any('Wracasz po członka drużyny' in m for m in leader.messages)
    checks += 1
    actors[5].blocked = False
    assert await leader.walk_room_transition('east', 'middle', guided=True)
    assert await leader.walk_room_transition('east', 'end', guided=True)
    assert all(a.character.room_id == 'end' for a in actors)
    assert not leader._party_follow_blocked_v1130012
    checks += 1

    # A crypt team has already split across dynamic side rooms (possibly due
    # to an interrupted `walk krypta dol`). This is caught even when the old
    # split flag is absent, and the old locations are not silently overwritten.
    server, actors = party()
    leader = actors[0]
    for actor in actors:
        actor.character.room_id = 'crypt_floor_2_r01'
    actors[4].character.room_id = 'crypt_floor_2_r02'
    assert not await leader.walk_room_transition('down', 'crypt_floor_3', guided=True)
    assert leader.character.room_id == 'crypt_floor_2_r01'
    assert actors[4].character.room_id == 'crypt_floor_2_r02'
    checks += 1
    assert not server.db.saves
    assert any('Testtcp5' in m and 'rozdzielona' in m for m in leader.messages)
    checks += 1

    # No member is teleported by the preflight, including a separate guild
    # member outside the dungeon: only online same-party crypt followers count.
    assert actors[4].character.room_id == 'crypt_floor_2_r02'
    checks += 1

    print(f'FAST CRYPT PARTY FOLLOW: {checks}/{checks} PASS', flush=True)
    return checks


def run():
    return asyncio.run(run_cases())


if __name__ == '__main__':
    run()
