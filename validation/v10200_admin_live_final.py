# -*- coding: utf-8 -*-
"""v102 focused tests: fail-closed loopback transport, OLC and read-only audit."""
from __future__ import annotations
import asyncio
import copy
import json
import logging
from pathlib import Path
from types import SimpleNamespace
from validation.v3600_admin_guardian2 import Fake
from systems.live_content_v1204 import LiveContentV1204
from systems import live_mechanics_v10100 as mechanics
from systems import admin_live_native_arena_v8600 as native
from systems import admin_live_bridge_v10200 as bridge
from systems.admin_live_audit_v10200 import audit_routes, audit_olc, audit_full_router_static
from world.uoss_superbosses import UOSS_SUPERBOSS_ENCOUNTERS_V11134


async def main():
    checks=0
    def ok(x,msg):
        nonlocal checks
        assert x,msg
        checks+=1
    admin=Fake(); guest=Fake(False,admin.server.db)
    admin.server.sessions=[admin,guest]
    guest.server=admin.server
    admin.server.live_content_v1204=LiveContentV1204(SimpleNamespace(conn=admin.server.db.conn))
    async def call(value,who=admin):
        await who.admin_command('live '+value)
        return who.messages[-1]
    for page in ('74','75','76'):
        ok('POMOC '+page in await call('pomoc '+page),'help'+page)
        ok('Nieznana' in await call('pomoc '+page,guest),'role'+page)
    ok(audit_routes()==(10,[]),'10 modules routed')
    ok(audit_full_router_static()==(60,[]),'all 60 historical handler routes defined')
    ok(audit_olc(admin.server.live_content_v1204)==[],'active and draft valid')
    ok('60 wszystkich historycznych' in await call('audyt komendy'),'routes audit')
    ok('ACTIVE/DRAFT' in await call('audyt olc'),'olc audit')
    ok('izolacj' in (await call('audyt arena')).lower() or 'STOP' in admin.messages[-1],'arena audit')
    combined=await call('audyt')
    ok('ADMIN LIVE AUDYT' in combined,'summary')
    ok('Walidacja PASS' in combined and 'OLC AUDYT' in combined,
       'legacy OLC validation preserved in combined admin live audyt')
    for v in ('audyt bad','audyt raport jeszcze','audyt komendy xyz'):
        ok('ADMIN LIVE v102:' in await call(v),'invalid audit '+v)
    ok('Nieznana' in await call('audyt raport',guest),'no admin read access')
    from unittest.mock import patch
    with patch.object(native,'_current',None):
        ok('ADMIN LIVE v102' in await call('arena real tunel POTWIERDZAM'),'no arena no connect')
    ok('Nieznana' in await call('arena real tunel POTWIERDZAM',guest),'no bridge access')

    boss=next(iter(UOSS_SUPERBOSS_ENCOUNTERS_V11134))
    phases={'phases':[{'below_hp':100,'every':2,'target':'all',
             'actions':[{'type':'restore_health','percent':5}],
             'conditions':{'target_hp_below':60,'target_mana_below':50,'min_party':2},
             'label':'Tchnienie'}]}
    ok(mechanics.validate({boss:phases}),'new schema valid')
    for bad in ({'conditions':{'min_party':0}},{'conditions':{'target_hp_below':True}},
                {'conditions':{'python':'exec'}},{'conditions':{'target_mana_below':101}},
                {'actions':[{'type':'exec','percent':4}]}):
        spec=copy.deepcopy(phases)
        spec['phases'][0].update(bad)
        try:mechanics.validate({boss:spec})
        except ValueError:checks+=1
        else:raise AssertionError('bad rule accepted')
    ok('MECHANIKI PLAN' in await call('mechaniki plan '+boss+' | '+json.dumps(phases)),'mechanics v102 plan')
    ok('zatwierdzono' in await call('mechaniki zatwierdz POTWIERDZAM'),'mechanics draft commit')
    ok(boss not in mechanics.ACTIVE,'draft not live')
    service=admin.server.live_content_v1204
    ok('PRZEDPUBLIKACJA OK' in service.apply(admin.server,'admin',dry_run=True),'dry-run')
    ok(boss not in mechanics.ACTIVE,'no early publish')
    ok('Aktywowano rewizję' in service.apply(admin.server,'admin'),'publish')
    ok(audit_olc(service)==[],'OLC active synchronized')
    mob=SimpleNamespace(hp=80,max_hp=100,combat_turn=2,alive=True)
    t1=SimpleNamespace(account_id=4,closed=False,current_hp=40,current_mana=30,max_hp=lambda:100,max_mana=lambda:100)
    t2=SimpleNamespace(account_id=5,closed=False,current_hp=80,current_mana=10,max_hp=lambda:100,max_mana=lambda:100)
    event=mechanics.on_boss_turn(mob,{'uoss_unique_superboss_key':boss},[t1,t2])
    ok(event and event['selected']==frozenset({4}),'conditions select only eligible')
    ok(mechanics.apply_to_target(t1,event)=={'restore_health':5},'healing applied')
    ok(t1.current_hp==45 and t2.current_hp==80,'no production session crossed')
    ok(mechanics.apply_to_target(t1,event) is None,'not applied twice')
    mob.combat_turn=4
    ok(mechanics.on_boss_turn(mob,{'uoss_unique_superboss_key':boss},[t1]) is None,'requires 2 players')
    service.draft['v101_rules'].clear()
    service.apply(admin.server,'admin')
    ok(boss not in mechanics.ACTIVE,'hot revocation')

    # Real local mock TCP server exercises forwarding; unlike actual arena,
    # this does not claim production combat coverage.
    traffic=[]; arrival=asyncio.Event()
    async def private_connection(reader,writer):
        writer.write(b'PRIVATE WORLD READY\r\n');await writer.drain()
        try:
            packet=await reader.readline()
            if packet:
                traffic.append(packet);arrival.set()
                writer.write(b'PRIVATE ACK\r\n');await writer.drain()
                await reader.read()
        except (ConnectionResetError,BrokenPipeError) as exc:
            logging.getLogger(__name__).debug('Test peer disconnected: %s', exc)
        finally:
            writer.close()
            try:await writer.wait_closed()
            except (ConnectionResetError,BrokenPipeError) as exc:
                logging.getLogger(__name__).debug('Test peer already closed: %s', exc)
    import tempfile
    from unittest.mock import patch
    with tempfile.TemporaryDirectory() as tmp:
        stop=Path(tmp)/'stop'
        server=await asyncio.start_server(private_connection,'127.0.0.1',0)
        mock_port=server.sockets[0].getsockname()[1]
        class Proc:
            def poll(self):return None
        previous=native._current
        native._current={'process':Proc(),'port':4900,'stop':stop}
        class Writer:
            def __init__(self):self.data=[]
            def write(self,bytes_):self.data.append(bytes_)
            async def drain(self):pass
        admin.writer=Writer()
        def mock_available():
            if stop.exists():raise ValueError('isolated instance stopped')
            return native._current,mock_port
        try:
          with patch.object(bridge,'available_port',mock_available):
            ok('polaczono' in await call('arena real tunel POTWIERDZAM'),'admin connected')
            await asyncio.sleep(0.02)
            ok(any(b'PRIVATE WORLD READY' in x for x in admin.writer.data),'stream incoming')
            ok(await bridge.forward_if_connected(admin,'look') is True,'private command consumed')
            await asyncio.wait_for(arrival.wait(),1)
            ok(traffic==[b'look\r\n'],'forwarded solely to private TCP')
            await asyncio.sleep(0.02)
            ok(any(b'PRIVATE ACK' in x for x in admin.writer.data),'reply streamed')
            ok('AKTYWNY' in await call('arena real tunel status'),'status active')
            ok(await bridge.forward_if_connected(admin,'arena wyjdz'),'local exit')
            ok(admin._v102_tunnel is None,'private stream detached')
            ok(not await bridge.forward_if_connected(admin,'look'),'production parser restored')
            ok('WYLACZONY' in await call('arena real tunel status'),'status inactive')
            ok('polaczono' in await call('arena real tunel POTWIERDZAM'),'reconnect')
            stop.write_text('STOP')
            ok(await bridge.forward_if_connected(admin,'postac test'),'private stop fails closed')
            ok(admin._v102_tunnel is None,'private stop cleanup')
        finally:
            await bridge.disconnect(admin)
            native._current=previous
            server.close();await server.wait_closed()
    return checks

if __name__=='__main__':
    print('ADMIN LIVE v102:',asyncio.run(main()),'checks PASS')
