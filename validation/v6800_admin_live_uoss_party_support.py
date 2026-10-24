# -*- coding: utf-8 -*-
"""v68: full detached party support, real UOSS target choice and safe isolation."""
from __future__ import annotations
import asyncio,copy,random
from types import SimpleNamespace
from validation.v3600_admin_guardian2 import Fake
from systems.live_content_v1204 import LiveContentV1204

async def suite():
    n=0
    def ck(condition,reason=''):
        nonlocal n
        assert condition,reason
        n+=1
    owner=Fake()
    db=owner.server.db
    service=LiveContentV1204(SimpleNamespace(conn=db.conn))
    owner.server.live_content_v1204=service
    outsider=Fake(False,db)
    outsider.server.live_content_v1204=service
    active=copy.deepcopy(service.active);draft=copy.deepcopy(service.draft)
    writes=db.conn.total_changes; rng=random.getstate()
    async def cmd(value,who=owner):
        await who.admin_command('live '+value)
        return who.messages[-1]
    ck('POMOC 23' in await cmd('pomoc 23'))
    for value in ('pomoc 23','arena uoss druzyna wsparcie','arena uoss druzyna stan 1 10 2 POTWIERDZAM'):
        ck('Nieznana komenda' in await cmd(value,outsider),value)
    ck('ADMIN LIVE V68' in await cmd('arena uoss druzyna wsparcie'))
    ck('ARENA11 START' in await cmd('arena start black_rabite 100000 2000 Popoi'))
    ck('ARENA DRUZYNA' in await cmd('arena druzyna dodaj Wojownik 20 50000 1000 300 POTWIERDZAM'))
    ck('ARENA DRUZYNA' in await cmd('arena druzyna dodaj Mag 20 40000 500 200 POTWIERDZAM'))
    ck('ARENA UOSS DRUZYNA TEST' in await cmd('arena uoss druzyna stan 1 20000 15 POTWIERDZAM'))
    ck('ARENA UOSS DRUZYNA TEST' in await cmd('arena uoss druzyna stan 2 40000 0 POTWIERDZAM'))
    def lab_snapshot():
        a=owner.guardian7_lab
        return (a['round'],a['hero_hp'],a['boss'].hp,a['total_dealt'],
                a['total_taken'],copy.deepcopy(a.get('_adminlive46_party',[])),
                a['actor8'].current_hp,a['actor8'].current_mana)
    state_before=lab_snapshot()
    # Real Popoi UOSS selection targets lowest MP ratio across the group.
    res=await cmd('arena uoss druzyna wsparcie 1')
    ck('3 graczy' in res,res)
    ck('Postac 2 +40 MP' in res,res)
    ck('Postac 1: HP 20000/50000, MP 15/300' in res,res)
    ck('Postac 2: HP 40000/40000, MP 40/200' in res,res)
    ck('atak' not in res.split('1: Popoi')[1].split('. Zrodlo')[0],res)
    ck('100000/100000' in res)
    for count in (1,2,3,4,6,12):
        ck('ARENA UOSS DRUZYNA' in await cmd('arena uoss druzyna wsparcie '+str(count)))
    ck('ARENA UOSS DRUZYNA' in await cmd('arena uoss druzyna wsparcie 3 30000 10'))
    for value in ('arena uoss druzyna wsparcie 0','arena uoss druzyna wsparcie 13',
                  'arena uoss druzyna wsparcie -1','arena uoss druzyna wsparcie 1 0 5',
                  'arena uoss druzyna wsparcie 1 100001 5','arena uoss druzyna wsparcie 1 50000 -1',
                  'arena uoss druzyna wsparcie 1 50000 101','arena uoss druzyna wsparcie 1 x 4',
                  'arena uoss druzyna wsparcie 1 50000','arena uoss druzyna wsparcie 1 50000 4 6',
                  'arena uoss druzyna stan 1 0 4 POTWIERDZAM',
                  'arena uoss druzyna stan 1 50001 4 POTWIERDZAM',
                  'arena uoss druzyna stan 1 100 301 POTWIERDZAM',
                  'arena uoss druzyna stan 4 20 20 POTWIERDZAM',
                  'arena uoss druzyna stan 1 10 10',
                  'arena uoss druzyna stan 1 10 10 POTWIERDZAM extra'):
        ck('ADMIN LIVE V68' in await cmd(value),value)
    ck(lab_snapshot() == state_before, 'Preview modified current arena or test party')
    ck('ARENA DRUZYNA' in await cmd('arena druzyna dodaj Druid 20 10000 100 10 POTWIERDZAM'))
    ck('ADMIN LIVE V68' in await cmd('arena uoss druzyna wsparcie'))
    ck('ARENA DRUZYNA' in await cmd('arena druzyna usun 3 POTWIERDZAM'))
    ck('3 graczy' in await cmd('arena uoss druzyna wsparcie'))
    # Primm: when low HP on a party member, selects that member for Cure.
    ck('ARENA11 START' in await cmd('arena start black_rabite 100000 2000 Primm'))
    ck('ARENA DRUZYNA' in await cmd('arena druzyna dodaj Wojownik 20 50000 1000 300 POTWIERDZAM'))
    ck('ARENA DRUZYNA' in await cmd('arena druzyna dodaj Mag 20 40000 500 200 POTWIERDZAM'))
    ck('TEST 2' in await cmd('arena uoss druzyna stan 2 1000 100 POTWIERDZAM'))
    msg=await cmd('arena uoss druzyna wsparcie 1')
    ck('Postac 2 +9200 HP' in msg,msg)
    ck('Postac 2: HP 10200/40000' in msg,msg)
    ck('Postac 1: HP 50000/50000' in msg,msg)
    ck('Cure Water' in msg)
    # Without low HP, source Bubble applies to ALL currently eligible members.
    ck('TEST 2' in await cmd('arena uoss druzyna stan 2 40000 100 POTWIERDZAM'))
    msg=await cmd('arena uoss druzyna wsparcie 1')
    ck('Bubble' in msg,msg)
    ck('Lider 150000 max HP' in msg,msg)
    ck('Postac 1 75000 max HP' in msg,msg)
    ck('Postac 2 60000 max HP' in msg,msg)
    ck('Postac 2: HP 40000/60000' in msg,msg)
    # Repeated preview is deterministic and cannot set flags in live state.
    ck(msg==await cmd('arena uoss druzyna wsparcie 1'))
    ck('Dryad Preach' in await cmd('arena uoss druzyna wsparcie 7'))
    ck('Bubble' in await cmd('arena uoss druzyna wsparcie 3'))
    # Nullify Healing on member must block only that target (not leader).
    # Lab member needs a status marker for this test (replica picks copied data).
    ck('ARENA11 START' in await cmd('arena start serpentarius 100000 2000 Byblos'))
    ck('ARENA DRUZYNA' in await cmd('arena druzyna dodaj Wojownik 20 50000 1000 300 POTWIERDZAM'))
    ck('TEST 1' in await cmd('arena uoss druzyna stan 1 1000 1 POTWIERDZAM'))
    msg=await cmd('arena uoss druzyna wsparcie 1')
    ck('Cure' in msg and 'Postac 1 +11500 HP' in msg,msg)
    # X-Ether source picks the member with lowest MP ratio.
    ck('TEST 1' in await cmd('arena uoss druzyna stan 1 50000 0 POTWIERDZAM'))
    msg=await cmd('arena uoss druzyna wsparcie 1')
    ck('X-Ether' in msg and 'Postac 1 +75 MP' in msg,msg)
    # Montblanc group Bubble and Seifer boss-only breakdown.
    ck('ARENA11 START' in await cmd('arena start yiazmat 100000 2000 Montblanc'))
    ck('ARENA DRUZYNA' in await cmd('arena druzyna dodaj Druid 20 10000 100 50 POTWIERDZAM'))
    msg=await cmd('arena uoss druzyna wsparcie 1')
    ck('Postac 1 15000 max HP' in msg,msg)
    ck('ARENA11 START' in await cmd('arena start odin 100000 2000 Seifer'))
    ck('ARENA DRUZYNA' in await cmd('arena druzyna dodaj Druid 20 10000 100 50 POTWIERDZAM'))
    ck('No Mercy' in await cmd('arena uoss druzyna wsparcie 1'))
    ck('Power Breakdown' in await cmd('arena uoss druzyna wsparcie 3'))
    ck('ARENA11 START' in await cmd('arena start black_rabite 100000 2000 Popoi'))
    state=owner.guardian7_lab
    ck('brak' in (await cmd('arena druzyna sklad')).casefold())
    ck('1 graczy' in await cmd('arena uoss druzyna wsparcie'))
    ck(state['hero_hp']==100000)
    ck(random.getstate()==rng)
    ck(service.active==active and service.draft==draft)
    ck(db.conn.total_changes==writes)
    ck(db.logged==[])
    ck(owner.current_hp==20 and owner.current_mana==10)
    ck(owner.server.world.mobs=={})
    ck('ARENA11' in await cmd('arena wyjdz'))
    ck(owner.guardian7_lab is None)
    db.conn.close()
    return n

def run():return asyncio.run(suite())
if __name__=='__main__':print('V68 UOSS PARTY:',run(),'PASS')
