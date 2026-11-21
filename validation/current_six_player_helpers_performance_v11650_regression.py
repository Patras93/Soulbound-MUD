# -*- coding: utf-8 -*-
"""Six players, 18 real mercenary contracts and six active companions.

A wholly isolated performance+behavior regression. Never opens production data
or the public TCP port. The authenticated TCP deployment gate remains separate.
"""
from __future__ import annotations
import asyncio
import sqlite3
import sys
import time
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) in sys.path:
    sys.path.remove(str(ROOT))
sys.path.insert(0, str(ROOT))


def run():
    from data import catalog_mutations as mutations
    import data.npcs as npc_data
    from world.generation_systems import (
        v0160_static_npcs_in_room_v11650, v0160_npcs_in_room,
    )
    from player.session_mixins.movement import SessionMovementMixin
    from player.session_mixins.mercenary_taverns import SessionMercenaryTavernsMixin
    from systems.v115.vampire_mercenary import MERCENARIES
    from systems.visible_companions_v1801 import nearby_companions_v1801

    checks = 0
    # Reproduce 30,000 ordinary NPCs plus instructors in several regions.
    # Indexed lookup must return real source mappings, never stale duplicates.
    fake = {f'person_{n:05d}': {'name': f'Person {n}', 'room': f'area_{n%1000}'}
            for n in range(30000)}
    fake['trainer'] = {'name': 'Mentor', 'room': 'area_5', 'teacher_class': 'Nekromanta'}
    with patch.object(npc_data, 'NPCS', fake):
        started = time.perf_counter()
        for player in range(6):
            for step in range(20):
                found = v0160_static_npcs_in_room_v11650(f'area_{step}')
                assert len(found) == (31 if step == 5 else 30)
                checks += 1
        indexed = time.perf_counter()-started
        started = time.perf_counter()
        for player in range(6):
            for step in range(20):
                expected = {k:v for k,v in fake.items() if v.get('room') == f'area_{step}'}
                assert len(expected) == (31 if step == 5 else 30)
        linear = time.perf_counter()-started
        assert indexed < linear * .5, (indexed, linear)
        checks += 1
        old = v0160_static_npcs_in_room_v11650('area_5')
        assert 'trainer' in old
        checks += 1
        # Same-size update MUST invalidate the index. Mutations use the
        # canonical authoring API, never a hidden versioned migration.
        mutations.catalog_assign({'name':'Mentor', 'room':'area_9',
                                  'teacher_class':'Nekromanta'}, 'NPCS', fake, ('trainer',))
        assert 'trainer' not in v0160_static_npcs_in_room_v11650('area_5')
        assert 'trainer' in v0160_static_npcs_in_room_v11650('area_9')
        checks += 1
        # A second call cannot mutate cached source by modifying returned data.
        outside = v0160_static_npcs_in_room_v11650('area_9')
        outside.pop('trainer')
        assert 'trainer' in v0160_static_npcs_in_room_v11650('area_9')
        checks += 1
        assert 'trainer' in v0160_npcs_in_room('area_9')
        checks += 1

    class FakeDB:
        def __init__(self):
            self.conn = sqlite3.connect(':memory:')
            self.conn.row_factory = sqlite3.Row
            self.conn.execute('CREATE TABLE summons_v1700 ('
                              'account_id INTEGER, summon_type TEXT, level INTEGER, '
                              'soul_rank INTEGER, stance TEXT, hp INTEGER, max_hp INTEGER, '
                              'active INTEGER)')
            self.conn.executemany('INSERT INTO summons_v1700 VALUES(?,?,?,?,?,?,?,?)',
                [(i, 'pajak', 4, 1, 'assist', 40, 40, 1) for i in range(1,7)])
            self.conn.commit()
            self.saves = []
        def save_character(self, character, commit=True):
            self.saves.append((character.name, character.room_id, commit))
        def mercenary_contracts(self, account_id):
            return [dict(role=role) for role in ('wojownik', 'mag', 'paladyn')]

    class FakeServer:
        def __init__(self):
            self.sessions = []
            self.db = FakeDB()
            self.world = SimpleNamespace(ensure_runtime_room=lambda room: room in ('start','end'))
        def party_sessions(self, _leader, same_room=None):
            return [s for s in self.sessions if same_room is None or s.character.room_id == same_room]
        async def broadcast_room(self, *args, **kwargs):
            return None

    class Player(SessionMovementMixin, SessionMercenaryTavernsMixin):
        def __init__(self, server, i):
            self.server=server;self.account_id=i
            self.character=SimpleNamespace(name=f'Player{i}',room_id='start')
            self.closed=False;self.moving=False;self.guiding=False
            self.combat_mob_key=None;self.messages=[];self._party_follow_blocked_v1130012=False
        def party_key(self):
            return 1
        def movement_delay(self, direction, guided=False):
            return .001
        def active_class_names(self):
            return ['Nekromanta']
        async def send(self, message, **kwargs):
            self.messages.append(message)
        async def register_uoss_deep_dungeon_visit_v11331(self, room):
            return None
        async def look(self):
            # Exercise actual visibility of all three hired roles and all six
            # persistent summons, not a synthetic count that bypasses SQLite.
            mercs = self.nearby_mercenaries_v1226()
            summons = nearby_companions_v1801(self.server, self.character.room_id)
            assert len(mercs)%3==0 and 3<=len(mercs)<=18
            assert 1<=len(summons)<=6
        async def move(self, direction, preserve_auto_mining=False):
            return await self.walk_room_transition(direction, 'end', show_room=True)

    async def test_party():
        server=FakeServer()
        sessions=[Player(server,i) for i in range(1,7)]
        server.sessions=sessions
        result=await sessions[0].walk_room_transition('east','end',guided=False,show_room=True)
        assert result is True
        assert all(s.character.room_id=='end' for s in sessions)
        assert len(server.db.saves)==6
        assert {row[0] for row in server.db.saves} == {f'Player{i}' for i in range(1,7)}
        assert all(len([x for x in s.messages if 'zostali w tyle' in x])==0 for s in sessions)
        assert all(len(s.nearby_mercenaries_v1226())==18 for s in sessions)
        assert len(nearby_companions_v1801(server,'end'))==6
        assert all(not s.moving for s in sessions)
        server.db.conn.close()
        return 6
    checks += asyncio.run(test_party())
    print(f'V116.00.50 SIX PLAYERS + 18 HIRES + 6 SUMMONS: {checks} PASS',flush=True)
    return checks

if __name__ == '__main__':
    run()
