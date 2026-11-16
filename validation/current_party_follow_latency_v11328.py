# -*- coding: utf-8 -*-
"""Isolated six-player movement/load regression, no production DB or TCP."""
from __future__ import annotations
import asyncio
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from validation.current_party_follow_regression import party


async def main():
    checks = 0
    server, members = party()
    broadcasts = []
    async def record_broadcast(room, message, exclude=None):
        broadcasts.append((room, message, exclude))
    server.broadcast_room = record_broadcast
    leader = members[0]
    assert await leader.walk_room_transition('east', 'middle', guided=True, show_room=True)
    assert len(broadcasts) == 2, 'Follower broadcasts must not multiply network traffic'
    checks += 1
    assert all(s.character.room_id == 'middle' for s in members)
    checks += 1
    assert server.db.commits == 1
    checks += 1
    assert await leader.walk_room_transition('east', 'end', guided=True, show_room=True)
    assert len(broadcasts) == 4
    checks += 1
    assert all(s.character.room_id == 'end' for s in members)
    checks += 1
    assert server.db.commits == 2
    checks += 1
    assert not any('zostali w tyle' in m for m in leader.messages)
    checks += 1
    server, members = party()
    members[-1].blocked = True
    assert not await members[0].walk_room_transition('east','middle',guided=True,show_room=True)
    assert members[-1].character.room_id == 'start'
    checks += 1
    assert members[0]._party_follow_blocked_v1130012
    checks += 1
    # Preserve current movement speed and never turn a blocked exit into a teleport.
    assert abs(leader.movement_delay('east') - .002) < 1e-9
    checks += 1
    print(f'PARTY FOLLOW LATENCY v113.00.28: {checks}/{checks} PASS', flush=True)

if __name__ == '__main__':
    asyncio.run(main())
