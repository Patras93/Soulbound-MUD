# -*- coding: utf-8 -*-
"""Strict runtime regression for the three lazy v11 dungeons.

Tests real World spawn registration after engine scaling, rather than only
checking catalog placeholders. Run late in PLUS gate on disposable data.
"""


def run_regression():
    import server  # all legacy systems and late installers are loaded
    from world.world_state import World, ROOMS, MOB_SPAWNS, MOB_TEMPLATES
    from systems.eternal_glory_infinite_v1100 import (
        ENDLESS, identity, floor_id, gate_id,
    )
    assert getattr(World.ensure_infinite_dungeon_floor,'_v1500_echo',False)
    assert getattr(World.ensure_infinite_dungeon_floor,'_v1100_infinite',False)
    world=World()
    checks=2
    for key in ENDLESS:
        gate=gate_id(key)
        assert gate in ROOMS
        assert ROOMS[gate]['exits']['down']==floor_id(key,1)
        checks+=2
        for n in (2,10,11,100):
            room_id=floor_id(key,n)
            assert identity(room_id)==(key,n)
            assert world.ensure_infinite_dungeon_floor(room_id)
            room=ROOMS[room_id]
            assert room['v1100_no_traps'] is True
            assert room['exploration_ep']==0
            assert room['exits']['down']==floor_id(key,n+1)
            assert room['exits']['up']==floor_id(key,n-1)
            expected=3 if n%10==0 else 2
            catalog=[mid for rid,mid in MOB_SPAWNS if rid==room_id]
            active=[mob for mob in world.mobs.values() if mob.room_id==room_id]
            assert len(catalog)==len(active)==expected, (room_id,catalog)
            assert all(mid in MOB_TEMPLATES for mid in catalog)
            if n%10==0:
                assert any(MOB_TEMPLATES[mid].get('world_boss') for mid in catalog)
            assert world.ensure_infinite_dungeon_floor(room_id)
            assert len([mid for rid,mid in MOB_SPAWNS if rid==room_id])==expected
            assert len([mob for mob in world.mobs.values() if mob.room_id==room_id])==expected
            checks+=12
    return checks


if __name__=='__main__':
    print('V11 INFINITE RUNTIME:',run_regression(),'PASS')
