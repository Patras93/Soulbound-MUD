# -*- coding: utf-8 -*-
"""v3.10.2 contract: old war-front officers retain short independent access."""
from __future__ import annotations
from collections import deque
from systems.era_legends_v1600 import FRONTS
from validation.v1600_era_legends import run_era_legends_v1600


def run_regression(server):
    result=run_era_legends_v1600(server)
    errors=[e for e in result['errors'] if e.startswith('front NPC ')]
    assert not errors,errors
    checks=len(FRONTS)
    rooms,npcs=server.ROOMS,server.NPCS
    for slug,_,original_room,_,_ in FRONTS:
        npc_id='v1600_war_npc_'+slug
        npc=npcs[npc_id]
        room=npc['room']
        assert original_room in rooms and room in rooms
        assert sum(int(n.get('room')==room) for n in npcs.values())==1
        assert room==original_room or room.startswith('npc_v3101_private_')
        checks+=3
    # Prove the historical validator still blocks missing, disconnected and
    # duplicate NPCs (reverts entirely in-memory mutations, never live DB).
    for slug,_,_,_,_ in FRONTS:
        npc_id='v1600_war_npc_'+slug
        npc=npcs[npc_id]
        current=npc['room']
        npc['room']='not_a_room_v3102'
        try:
            assert 'front NPC '+slug in run_era_legends_v1600(server)['errors']
        finally:
            npc['room']=current
        checks+=1
        # Only moved officers have an annex to disconnect. Originals staying
        # on their existing front should not be forced into a private room.
        original_room=next(row for key,_,row,_,_ in FRONTS if key==slug)
        if current!=original_room:
            entrance=rooms[original_room]['exits']
            doorway=next((direction for direction,destination in entrance.items()
                           if destination==current or
                           (destination.startswith('npc_v3101_') and
                            current in rooms[destination].get('exits',{}).values())),None)
            assert doorway is not None,('NPC annex not adjacent to original front',slug)
            destination=entrance.pop(doorway)
            try:
                assert 'front NPC '+slug in run_era_legends_v1600(server)['errors']
            finally:
                entrance[doorway]=destination
            checks+=1
        # A second NPC using the same office must likewise be rejected.
        other_id=next(k for k in npcs if k!=npc_id)
        other=npcs[other_id]
        old_other=other.get('room')
        other['room']=current
        try:
            assert 'front NPC '+slug in run_era_legends_v1600(server)['errors']
        finally:
            other['room']=old_other
        checks+=1
    return checks


if __name__=='__main__':
    import server
    print('FRONTY ERA LEGEND v3.10.2:',run_regression(server),'PASS')
