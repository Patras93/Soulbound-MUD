# -*- coding: utf-8 -*-
"""Full command routing for tower portals; disposable in-memory sessions only.

Check both the new Star Tower and the older Astral / Mythic Astral towers.
No checkpoint may be unlocked or moved by this test in a real player DB.
"""
from __future__ import annotations
import asyncio
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
# This file is also executed by path on Windows: validation/events.py must
# never mask the actual top-level events/ package.
if str(ROOT) in sys.path:sys.path.remove(str(ROOT))
sys.path.insert(0,str(ROOT))
import server   # installs the real v11 portal wrapper and command routing
from validation.v2010_unlocked_portals import Server, Dummy
from systems.eternal_glory.infinite import floor_id, gate_id
from systems.dungeons_regions import astral_floor_id, mythic_astral_floor_id
from player.session_mixins.command_registry import COMMAND_REGISTRY, SessionCommandRegistryMixin


async def check():
    n=0
    def ck(cond,what):
        nonlocal n
        assert cond,what
        n+=1

    ck(COMMAND_REGISTRY['portal'][0]=='use_crypt_portal','portal routing changed')
    ck(COMMAND_REGISTRY['astralportal'][0]=='use_astral_portal','astralportal routing changed')
    s=Server();p=Dummy(s,1,gate_id('wieza'));s.group=[p]
    s.db.collection[1,'v1100_checkpoint_wieza'].update(('10','20'))
    await server.Session.use_crypt_portal(p,'10')
    ck(p.character.room_id==floor_id('wieza',10),'portal 10 from Star Tower gate')
    await server.Session.use_crypt_portal(p,'20')
    ck(p.character.room_id==floor_id('wieza',20),'portal 20 between checkpoints')
    await server.Session.use_crypt_portal(p,'wyjdz')
    ck(p.character.room_id==gate_id('wieza'),'portal wyjdz from Star Tower')
    await server.Session.use_astral_portal(p,'10')
    ck(p.character.room_id==floor_id('wieza',10),'old astralportal alias still works')
    await server.Session.use_crypt_portal(p,'30')
    ck(p.character.room_id==floor_id('wieza',10),'locked checkpoint denied')
    ck(any(('nie jest odblokowany' in msg or 'zablokowany' in msg) for msg in p.messages),'accessible denial message')
    await server.Session.use_crypt_portal(p,'status')
    ck(any('Checkpointy: 10, 20' in msg for msg in p.messages),'readable tower portal status')
    p.character.room_id=floor_id('wieza',30)
    await server.Session.use_crypt_portal(p,'wyjdz')
    ck(p.character.room_id==floor_id('wieza',30),'uncleared checkpoint exit denied')
    p.character.room_id=floor_id('wieza',11)
    await server.Session.use_crypt_portal(p,'10')
    ck(p.character.room_id==floor_id('wieza',11),'regular floor cannot jump')
    p.character.room_id=gate_id('wieza')
    p.combat_mob_key='enemy'
    await server.Session.use_crypt_portal(p,'10')
    ck(p.character.room_id==gate_id('wieza'),'combat cannot teleport')
    p.combat_mob_key=None
    p.current_hp=0
    await server.Session.use_crypt_portal(p,'10')
    ck(p.character.room_id==gate_id('wieza'),'dead character cannot teleport')
    p.current_hp=100

    for gate,start,floor_id_fun,kind in (
            ('astral_gate',100,astral_floor_id,'astral'),
            ('mythic_astral_gate',10,mythic_astral_floor_id,'mythic_astral')):
        s=Server();p=Dummy(s,1,gate);s.group=[p]
        s.db.floors[1,kind]={start,start+10}
        await server.Session.use_crypt_portal(p,str(start))
        ck(p.character.room_id==floor_id_fun(start),kind+' portal N via universal command')
        await server.Session.use_crypt_portal(p,str(start+10))
        ck(p.character.room_id==floor_id_fun(start+10),kind+' between checkpoints')
        await server.Session.use_crypt_portal(p,'wyjdz')
        ck(p.character.room_id==gate,kind+' return to gate')
        await server.Session.use_astral_portal(p,str(start))
        ck(p.character.room_id==floor_id_fun(start),kind+' astralportal compatibility')

    # Actual command-registry dispatch (not just calling a portal method),
    # including floor one of all three towers. The crypt must not capture it.
    class RoutedDummy(Dummy, SessionCommandRegistryMixin):
        use_crypt_portal = server.Session.use_crypt_portal
        use_astral_portal = server.Session.use_astral_portal
        checkpoint_portal_origin_v2010 = server.Session.checkpoint_portal_origin_v2010

    async def command(player, value):
        assert await player.dispatch_registered_command('portal', value) is True

    s=Server();p=RoutedDummy(s,1,floor_id('wieza',1));s.group=[p]
    s.db.collection[1,'v1100_checkpoint_wieza'].add('10')
    await command(p,'')
    ck(any('Wieża Spadających Gwiazd. Checkpointy: 10' in msg for msg in p.messages),
       'Star Tower first floor: portal shows tower, not crypt')
    await command(p,'20')
    ck(p.character.room_id==floor_id('wieza',1),'Star Tower first floor: locked 20 denied')
    await command(p,'10')
    ck(p.character.room_id==floor_id('wieza',10),'Star Tower first floor: portal 10')
    p.character.room_id=floor_id('wieza',1)
    await command(p,'wyjdz')
    ck(p.character.room_id==gate_id('wieza'),'Star Tower first floor: portal wyjdz')

    for kind,first,destination,locked in (
            ('astral',astral_floor_id(100),100,110),
            ('mythic_astral',mythic_astral_floor_id(1),10,20)):
        s=Server();p=RoutedDummy(s,1,first);s.group=[p]
        s.db.floors[1,kind]={destination}
        await command(p,'')
        ck(any('Astralny Portal' in msg for msg in p.messages),
           kind+' first floor: portal shows tower list')
        ck(not any('Portal Krypty:' in msg for msg in p.messages),
           kind+' first floor: crypt status must not appear')
        await command(p,str(locked))
        ck(p.character.room_id==first,kind+' first floor: locked checkpoint denied')
        await command(p,str(destination))
        ck(p.character.room_id==(
            astral_floor_id(destination) if kind=='astral' else mythic_astral_floor_id(destination)),
           kind+' first floor: portal to unlocked checkpoint')
        ck(s.db.saves[-1][1]==p.character.room_id,
           kind+' first floor: destination persisted')

    # Crypt remains crypt; from a regular floor in a tower the portal cannot
    # become an arbitrary shortcut even with a previously unlocked checkpoint.
    s=Server();p=RoutedDummy(s,1,'crypt_hall');s.group=[p]
    await command(p,'')
    ck(any('Portal Krypty' in msg for msg in p.messages),
       'crypt status unchanged by universal tower routing')
    s=Server();p=RoutedDummy(s,1,mythic_astral_floor_id(2));s.group=[p]
    s.db.floors[1,'mythic_astral']={10}
    await command(p,'10')
    ck(p.character.room_id==mythic_astral_floor_id(2),
       'ordinary uncheckpointed tower floor cannot teleport')
    # Subrooms on the first floor are recognized as belonging to that floor.
    s=Server();p=RoutedDummy(s,1,mythic_astral_floor_id(1)+'_r1');s.group=[p]
    s.db.floors[1,'mythic_astral']={10}
    await command(p,'10')
    ck(p.character.room_id==mythic_astral_floor_id(10),
       'Mythic Tower first-floor subroom can reach unlocked checkpoint')

    s=Server();leader=Dummy(s,1,gate_id('wieza'))
    ally=Dummy(s,2,gate_id('wieza'))
    unready=Dummy(s,3,gate_id('wieza'))
    ally.party_id=unready.party_id=1
    s.group=[leader,ally,unready]
    s.db.collection[1,'v1100_checkpoint_wieza'].add('10')
    s.db.collection[2,'v1100_checkpoint_wieza'].add('10')
    await server.Session.use_crypt_portal(unready,'10')
    ck(unready.character.room_id==gate_id('wieza'),'nonleader cannot teleport group')
    await server.Session.use_crypt_portal(leader,'10')
    ck(leader.character.room_id==floor_id('wieza',10),'leader moved')
    ck(ally.character.room_id==floor_id('wieza',10),'unlocked local teammate moved')
    ck(unready.character.room_id==gate_id('wieza'),'locked teammate not teleported')
    return n


def run():
    return asyncio.run(check())


if __name__=='__main__':
    print(f'V106 PORTAL W WIEZY: {run()} checks PASS',flush=True)
