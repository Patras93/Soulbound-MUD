# -*- coding: utf-8 -*-
"""Voluntary crypt party regrouping; six fake sessions, no production files."""
from __future__ import annotations
import asyncio
import sys
from pathlib import Path
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))
from validation.current_party_follow_regression import party
from player.session_mixins.command_registry import resolve_session_command, COMMAND_REGISTRY


def setup():
    server, players = party()
    server.session_by_account=lambda account: next((p for p in players if p.account_id==account),None)
    server.db.boss_clears=set()
    server.db.boss_floor_cleared=lambda acc,kind,floor: (acc,kind,floor) in server.db.boss_clears
    for player in players:
        player.current_hp=100
        player.is_downed_v0371=lambda:False
    return server,players


async def test():
    checks=0
    assert resolve_session_command('teleport','to leader')=='teleportleader'; checks+=1
    assert resolve_session_command('tp','lider')=='teleportleader'; checks+=1
    assert COMMAND_REGISTRY['teleportleader'][0]=='teleport_to_party_leader'; checks+=1
    server,players=setup(); leader=players[0]; lost=players[5]
    for p in players: p.character.room_id='crypt_floor_5'
    lost.character.room_id='crypt_floor_3'
    assert await lost.teleport_to_party_leader('to leader'); checks+=1
    assert lost.character.room_id==leader.character.room_id=='crypt_floor_5'; checks+=1
    assert server.db.saves==[(lost.character.name,'crypt_floor_5',True)]; checks+=1
    assert lost.previous_room_id=='crypt_floor_3'; checks+=1
    assert any('wrocił' in m or 'wrócił' in m for m in leader.messages); checks+=1
    assert await lost.teleport_to_party_leader('do lidera') and len(server.db.saves)==1; checks+=1
    # A missing party or the leader himself cannot use this as free world travel.
    assert not await leader.teleport_to_party_leader(''); checks+=1
    lost.party_key=lambda: None
    assert not await lost.teleport_to_party_leader(''); checks+=1
    lost.party_key=lambda: 1
    assert not await lost.teleport_to_party_leader('do gracza'); checks+=1

    # Combat and movement are never cancelled by a teleport.
    lost.character.room_id='crypt_floor_4'
    lost.combat_mob_key='crypt_mob:1'
    assert not await lost.teleport_to_party_leader('to leader');checks+=1
    lost.combat_mob_key=None;lost.moving=True
    assert not await lost.teleport_to_party_leader('');checks+=1
    lost.moving=False;lost.current_hp=0
    assert not await lost.teleport_to_party_leader('');checks+=1
    lost.current_hp=100
    leader.guiding=True
    assert not await lost.teleport_to_party_leader('');checks+=1
    leader.guiding=False
    leader.combat_mob_key='crypt_mob:1'
    assert not await lost.teleport_to_party_leader('');checks+=1
    leader.combat_mob_key=None
    assert lost.character.room_id=='crypt_floor_4' and len(server.db.saves)==1; checks+=1

    # Cross-family/public->crypt/private side-room is not legal.
    leader.character.room_id='mythic_crypt_floor_15'
    assert not await lost.teleport_to_party_leader('');checks+=1
    leader.character.room_id='crypt_floor_5_r01'
    assert not await lost.teleport_to_party_leader('');checks+=1
    leader.character.room_id='crypt_floor_5'
    lost.character.room_id='temple'
    assert not await lost.teleport_to_party_leader('');checks+=1
    # A player stranded in a side corridor can rejoin the central floor.
    lost.character.room_id='crypt_floor_4_r02'
    assert await lost.teleport_to_party_leader('to leader');checks+=1
    assert lost.character.room_id=='crypt_floor_5';checks+=1
    lost.character.room_id='crypt_floor_4'
    leader.closed=True
    assert not await lost.teleport_to_party_leader('');checks+=1
    leader.closed=False

    # Personal boss checkpoints: neither party membership nor leader progress
    # may substitute for this player's own cleared gate on floor 10/20.
    lost.character.room_id='crypt_floor_9'
    leader.character.room_id='crypt_floor_11'
    assert not await lost.teleport_to_party_leader('to leader');checks+=1
    assert 'bramę bossa' in lost.messages[-1] and lost.character.room_id=='crypt_floor_9';checks+=1
    server.db.boss_clears.add((6,'crypt',10))
    assert await lost.teleport_to_party_leader('to leader'); checks+=1
    assert lost.character.room_id=='crypt_floor_11';checks+=1
    leader.character.room_id='crypt_floor_25'
    assert not await lost.teleport_to_party_leader('to leader');checks+=1
    server.db.boss_clears.add((6,'crypt',20))
    assert await lost.teleport_to_party_leader('to leader');checks+=1
    assert lost.character.room_id=='crypt_floor_25';checks+=1

    # A leader can now resume guiding when the whole six-player team regroups.
    for p in players[1:]:p.character.room_id='crypt_floor_25'
    assert await leader.party_movement_barrier_v1130020('crypt_floor_26');checks+=1
    # No destination update if db.save_character throws.
    lost.character.room_id='crypt_floor_23'
    before=len(server.db.saves)
    orig=server.db.save_character
    server.db.save_character=lambda *args,**kwargs: (_ for _ in ()).throw(OSError('disk full'))
    expected_save_failure = False
    try:
        await lost.teleport_to_party_leader('to leader')
    except OSError as exc:
        assert str(exc) == 'disk full', f'unexpected save failure: {exc}'
        expected_save_failure = True
    assert expected_save_failure, 'failed save incorrectly succeeded'
    assert lost.character.room_id=='crypt_floor_23' and len(server.db.saves)==before;checks+=1
    server.db.save_character=orig
    print(f'PARTY TELEPORT LEADER: {checks}/{checks} PASS',flush=True)
    return checks


def run():
    return asyncio.run(test())

if __name__=='__main__':run()
