# -*- coding: utf-8 -*-
"""v2.00.9: personal cap, unique boss Fame and real stair route regressions."""
import asyncio
import sqlite3
from types import SimpleNamespace

from systems.experience_cap_v2009 import (
    KINDS, experience_cap_v2009, capped_experience_v2009,
    combat_overcap_v2009,
)
from systems.fame_v1702 import (
    _is_fame_target, _fame_target_identity, fame_region, record_fame_kill,
)
import server as _server_initialized_v2009
from player.session_mixins import movement


def run_regression():
    checks = 0
    for kind in KINDS:
        previous = 0
        for level in (1, 2, 13, 15, 50, 150, 300, 600, 799, 800):
            cap = experience_cap_v2009(kind, level)
            assert cap >= 100 and cap >= previous, (kind, level, cap, previous)
            assert capped_experience_v2009(cap + 123, kind, level) == cap
            assert capped_experience_v2009(cap + 123, kind, level, True) == min(cap + 123, cap * 2)
            assert capped_experience_v2009(cap * 4, kind, level, True) == cap * 2
            assert capped_experience_v2009(10, kind, level) == 10
            previous = cap
            checks += 5
    assert combat_overcap_v2009({'boss': True, 'v019_stage': 25}, 15)
    assert not combat_overcap_v2009({'boss': False, 'v019_stage': 700}, 15)
    assert not combat_overcap_v2009({'boss': True, 'v019_stage': 10}, 15)
    checks += 3
    assert _is_fame_target({'crypt_boss': True})
    assert _is_fame_target({'astral_boss': True})
    assert _is_fame_target({'mythic_crypt_boss': True})
    assert _is_fame_target({'mythic_astral_boss': True})
    assert _is_fame_target({'v0900_miniboss': True})
    assert not _is_fame_target({'max_hp': 40000, 'damage': 100})
    assert not _is_fame_target({'boss': True, 'uoss_superboss_add': True})
    checks += 7
    template = {'crypt_boss': True, 'crypt_floor': 10, 'name': 'Boss Fame Test',
                'soul_reward': 2000}
    mob = SimpleNamespace(template_id='v2009_fame_test_boss_floor',
                          home_room_id='crypt_floor_10', room_id='crypt_floor_10')
    zone = fame_region('crypt_floor_10')
    assert zone != 'Nieznana kraina'
    assert _fame_target_identity(mob, {}, template) == (zone, mob.template_id)
    conn = sqlite3.connect(':memory:')
    player = SimpleNamespace(account_id=101)
    first = record_fame_kill(conn, [player], mob, template)
    second = record_fame_kill(conn, [player], mob, template)
    assert first == [(player, zone)] and second == []
    assert conn.execute('SELECT COUNT(*) FROM fame_bosses_v1702').fetchone()[0] == 1
    assert conn.execute('SELECT COUNT(*) FROM fame_pending_v1703').fetchone()[0] == 1
    elite_meta = dict(template, elite_base_template=mob.template_id)
    elite_mob = SimpleNamespace(template_id='v2009_fame_elite_variant',
                                home_room_id='crypt_floor_10', room_id='crypt_floor_10')
    assert _fame_target_identity(elite_mob, {}, elite_meta) == (zone, mob.template_id)
    assert record_fame_kill(conn, [player], elite_mob, elite_meta) == []
    checks += 7
    conn.close()
    # This mock uses the REAL stair router; it substitutes only regular
    # move() with a deterministic recording function so no live DB is touched.
    stairs = {
        'catacomb_f1_start': {'name': 'start', 'exits': {'east': 'catacomb_f1_end'}},
        'catacomb_f1_end': {'name': 'end', 'exits': {'west': 'catacomb_f1_start', 'down': 'catacomb_f2_start'}},
        'catacomb_f2_start': {'name': 'bottom', 'exits': {'up': 'catacomb_f1_end'}},
    }
    old = {rid: movement.ROOMS.get(rid) for rid in stairs}
    movement.ROOMS.update(stairs)
    class Dummy(movement.SessionMovementMixin):
        def __init__(self):
            self.character = SimpleNamespace(room_id='catacomb_f1_start')
            self.combat_mob_key = None
            self.moving = False
            self.guiding = False
            self.messages = []
            self.steps = []
            self.block_down = False
        async def send(self, text):
            self.messages.append(str(text))
        async def move(self, direction):
            self.steps.append(direction)
            if direction == 'down' and self.block_down:
                await self.send('Boss blokuje zejście')
                return
            self.character.room_id = movement.ROOMS[self.character.room_id]['exits'][direction]
    async def walk_tests():
        d = Dummy()
        await d.change_dungeon_floor_v2009('dol')
        assert d.character.room_id == 'catacomb_f2_start' and d.steps == ['east', 'down']
        d.steps.clear()
        await d.change_dungeon_floor_v2009('gora')
        assert d.character.room_id == 'catacomb_f1_end' and d.steps == ['up']
        d.character.room_id = 'catacomb_f1_start'
        d.steps.clear()
        d.block_down = True
        await d.change_dungeon_floor_v2009('dol')
        assert d.character.room_id == 'catacomb_f1_end' and d.steps == ['east', 'down']
        assert any('zatrzymane' in m for m in d.messages)
        return 4
    try:
        checks += asyncio.run(walk_tests())
    finally:
        for rid, previous in old.items():
            if previous is None:
                movement.ROOMS.pop(rid, None)
            else:
                movement.ROOMS[rid] = previous
    # Real three-floor catacombs: the dungeon already has 24 authored rooms
    # per floor. The new command must find the actual stair from a side room.
    from world.world_expansion_v import CATACOMB_LEVELS_V0900
    async def real_catacomb_route():
        d = Dummy()
        d.character.room_id = CATACOMB_LEVELS_V0900[1][0]
        await d.change_dungeon_floor_v2009('dol')
        assert d.character.room_id in CATACOMB_LEVELS_V0900[2], d.messages
        assert len(d.steps) > 1 and d.steps[-1] == 'down'
        d.steps.clear()
        await d.change_dungeon_floor_v2009('gora')
        assert d.character.room_id in CATACOMB_LEVELS_V0900[1], d.messages
        assert d.steps[-1] == 'up'
        return 4
    checks += asyncio.run(real_catacomb_route())
    return checks

if __name__ == '__main__':
    print(f'EXPCAP FAME STAIRS v2.00.9: {run_regression()} checks PASS')
