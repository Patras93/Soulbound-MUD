# -*- coding: utf-8 -*-
"""v66: helper AI selector and exact source utility, detached/no global side-effects."""
from __future__ import annotations
import asyncio,copy,random
from types import SimpleNamespace
from validation.v3600_admin_guardian2 import Fake
from systems.live_content_v1204 import LiveContentV1204
from systems.admin_live_v6600 import _preview
from systems.admin_live_v6500 import _replica
from world.uoss_superboss_runtime import superboss_helper_action_v1146
from data.mobs import MOB_TEMPLATES

async def suite():
    total=0
    def ck(value,label=''):
        nonlocal total
        assert value,label
        total+=1
    user=Fake();db=user.server.db
    user.server.live_content_v1204=LiveContentV1204(SimpleNamespace(conn=db.conn))
    nonadmin=Fake(False,db);nonadmin.server.live_content_v1204=user.server.live_content_v1204
    draft_before=copy.deepcopy(user.server.live_content_v1204.draft)
    active_before=copy.deepcopy(user.server.live_content_v1204.active)
    writes_before=db.conn.total_changes
    rng_before=random.getstate()
    boss_before=copy.deepcopy(MOB_TEMPLATES['uoss_superboss_black_rabite_v11136'])
    async def cmd(raw,session=user):
        await session.admin_command('live '+raw)
        return session.messages[-1]
    ck('POMOC 21' in await cmd('pomoc 21'))
    for raw in ('pomoc 21','arena uoss pomocnik','arena uoss pomocnik tura 3',
                'arena uoss pomocnik prognoza 100 10','arena uoss pomocnik seria 3'):
        ck('Nieznana komenda' in await cmd(raw,nonadmin),raw)
    ck('ADMIN LIVE V66' in await cmd('arena uoss pomocnik'))
    ck('ADMIN LIVE V66' in await cmd('arena uoss pomocnik tura 4'))
    ck('ARENA11 START' in await cmd('arena start black_rabite 100000 2000 Popoi'))
    state=user.guardian7_lab;lab_rng=state['_guardian10_rng']
    before=(state['round'],state['hero_hp'],state['boss'].hp,state['total_dealt'],state['total_taken'])
    ck('Popoi' in await cmd('arena uoss pomocnik'))
    ck('Faerie Walnut' in await cmd('arena uoss pomocnik prognoza 90000 10'))
    ck('odnowiono na kopii 20 many' in await cmd('arena uoss pomocnik prognoza 90000 10'))
    ck('mana 30/100' in await cmd('arena uoss pomocnik prognoza 90000 10'))
    ck('Earth Slide' in await cmd('arena uoss pomocnik tura 1'))
    ck('Popoi' in await cmd('arena uoss pomocnik seria 5'))
    ck('tury 5-7' in await cmd('arena uoss pomocnik seria 3 5'))
    ck('ADMIN LIVE V66' in await cmd('arena uoss pomocnik seria 13'))
    ck('ADMIN LIVE V66' in await cmd('arena uoss pomocnik seria 0'))
    ck('ADMIN LIVE V66' in await cmd('arena uoss pomocnik seria 4 249'))
    ck('ADMIN LIVE V66' in await cmd('arena uoss pomocnik tura 0'))
    ck('ADMIN LIVE V66' in await cmd('arena uoss pomocnik tura 251'))
    ck('ADMIN LIVE V66' in await cmd('arena uoss pomocnik prognoza 0 10'))
    ck('ADMIN LIVE V66' in await cmd('arena uoss pomocnik prognoza 100001 10'))
    ck('ADMIN LIVE V66' in await cmd('arena uoss pomocnik prognoza 100 -1'))
    ck('ADMIN LIVE V66' in await cmd('arena uoss pomocnik prognoza 100 101'))
    ck('ADMIN LIVE V66' in await cmd('arena uoss pomocnik prognoza x 10'))
    ck('ADMIN LIVE V66' in await cmd('arena uoss pomocnik prognoza 100 xyz'))
    ck('ADMIN LIVE V66' in await cmd('arena uoss pomocnik zle'))
    ck('ADMIN LIVE V65' in await cmd('arena uoss status Mini'))  # unrelated ability not on Black Rabite
    ck(random.getstate()==rng_before)
    ck(state['_guardian10_rng']==lab_rng)
    ck((state['round'],state['hero_hp'],state['boss'].hp,state['total_dealt'],state['total_taken'])==before)
    ck('ARENA11 KLASA' in await cmd('arena klasa Wojownik 10 0 POTWIERDZAM'))
    ck('mana 0/0' in await cmd('arena uoss pomocnik'))
    ck('ADMIN LIVE V66' in await cmd('arena uoss pomocnik prognoza 90000 10'))
    ck('ARENA11 KLASA' in await cmd('arena klasa Wojownik 10 300 POTWIERDZAM'))
    ck('mana 300/300' in await cmd('arena uoss pomocnik'))
    ck('Faerie Walnut' in await cmd('arena uoss pomocnik prognoza 90000 20'))
    ck('odnowiono na kopii 60 many' in await cmd('arena uoss pomocnik prognoza 90000 20'))
    ck('ARENA11 START' in await cmd('arena start black_rabite 100000 2000 Primm'))
    ck('Bubble' in await cmd('arena uoss pomocnik'))
    ck('max HP x1.50' in await cmd('arena uoss pomocnik'))
    ck('Cure Water' in await cmd('arena uoss pomocnik prognoza 10000 10'))
    report=await cmd('arena uoss pomocnik seria 4')
    ck('Bubble' in report and 'Dryad Preach' in report)
    ck(report.count('Bubble')==1)
    ck('Cure Water' in await cmd('arena uoss pomocnik prognoza 10000 10 5'))
    ck('ARENA11 START' in await cmd('arena start serpentarius 100000 2000 Byblos'))
    ck('Byblos' in await cmd('arena uoss pomocnik'))
    ck('Cure' in await cmd('arena uoss pomocnik prognoza 10000 10'))
    ck('X-Ether' in await cmd('arena uoss pomocnik prognoza 90000 10'))
    ck('ARENA11 START' in await cmd('arena start yiazmat 100000 2000 Montblanc'))
    ck('Montblanc' in await cmd('arena uoss pomocnik'))
    ck('Bubble' in await cmd('arena uoss pomocnik'))
    ck('ARENA11 START' in await cmd('arena start odin 100000 2000 Seifer'))
    ck('Seifer' in await cmd('arena uoss pomocnik'))
    ck('No Mercy' in await cmd('arena uoss pomocnik tura 2'))
    ck('ARENA11 START' in await cmd('arena start odin 100000 2000'))
    ck('brak pomocnika' in await cmd('arena uoss pomocnik'))
    ck('brak pomocnika' in await cmd('arena uoss pomocnik seria 10'))
    # Source selector guards one selection per exact turn on the detached boss.
    ck('ARENA11 START' in await cmd('arena start black_rabite 100000 2000 Popoi'))
    clone=_replica(user);clone['boss'].combat_turn=3
    choice=superboss_helper_action_v1146(clone['actor8'],clone['template'],clone['boss'])
    ck(choice is not None)
    ck(superboss_helper_action_v1146(clone['actor8'],clone['template'],clone['boss']) is None)
    ck('Earth Slide' in await cmd('arena uoss pomocnik tura 1'))
    ck(random.getstate()==rng_before)
    ck(user.server.live_content_v1204.draft==draft_before)
    ck(user.server.live_content_v1204.active==active_before)
    ck(db.conn.total_changes==writes_before)
    ck(MOB_TEMPLATES['uoss_superboss_black_rabite_v11136']==boss_before)
    ck(user.current_hp==20 and user.current_mana==10)
    ck(user.server.world.mobs=={})
    ck(not db.logged)
    ck('ARENA11:' in await cmd('arena wyjdz'))
    ck(user.guardian7_lab is None)
    db.conn.close()
    return total

def run():return asyncio.run(suite())
if __name__=='__main__':print('V66 UOSS HELPER SOURCE:',run(),'PASS')
