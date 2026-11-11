# -*- coding: utf-8 -*-
"""Regression: real helper selection and Soulbound support math on detached clones."""
from __future__ import annotations
import asyncio,copy,random
from types import SimpleNamespace
from validation.v3600_admin_guardian2 import Fake
from systems.live_content_v1204 import LiveContentV1204
from data.mobs import MOB_TEMPLATES

async def suite():
    n=0
    def ck(cond,detail=''):
        nonlocal n
        assert cond,detail
        n+=1
    user=Fake();db=user.server.db
    user.server.live_content_v1204=LiveContentV1204(SimpleNamespace(conn=db.conn))
    other=Fake(False,db);other.server.live_content_v1204=user.server.live_content_v1204
    active=copy.deepcopy(user.server.live_content_v1204.active)
    draft=copy.deepcopy(user.server.live_content_v1204.draft)
    writes=db.conn.total_changes
    rng=random.getstate()
    template=copy.deepcopy(MOB_TEMPLATES['uoss_superboss_black_rabite_v11136'])
    async def cmd(s,session=user):
        await session.admin_command('live '+s)
        return session.messages[-1]
    ck('POMOC 22' in await cmd('pomoc 22'))
    for arg in ('pomoc 22','arena uoss pomocnik skutki','arena uoss pomocnik skutki 2 10000 1'):
        ck('Nieznana komenda' in await cmd(arg,other),arg)
    ck('ADMIN LIVE V67' in await cmd('arena uoss pomocnik skutki'))
    ck('ARENA11 START' in await cmd('arena start black_rabite 100000 2000 Popoi'))
    lab=user.guardian7_lab
    first=copy.deepcopy((lab['round'],lab['hero_hp'],lab['boss'].hp,lab['total_dealt'],lab['total_taken']))
    ck('ARENA UOSS SKUTKI Popoi' in await cmd('arena uoss pomocnik skutki'))
    ck('Earth Slide' in await cmd('arena uoss pomocnik skutki 1'))
    ck('Faerie Walnut' in await cmd('arena uoss pomocnik skutki 3 90000 10'))
    ck('+20 MP' in await cmd('arena uoss pomocnik skutki 3 90000 10'))
    ck('MP 50/100' in await cmd('arena uoss pomocnik skutki 3 90000 10'))
    ck('NIEOBLICZONE' in await cmd('arena uoss pomocnik skutki 3 90000 10'))
    for raw in ('arena uoss pomocnik skutki 0','arena uoss pomocnik skutki 13',
                'arena uoss pomocnik skutki abc','arena uoss pomocnik skutki 1 0 10',
                'arena uoss pomocnik skutki 1 100001 10',
                'arena uoss pomocnik skutki 1 10000 -1',
                'arena uoss pomocnik skutki 1 10000 101',
                'arena uoss pomocnik skutki 1 10000 x',
                'arena uoss pomocnik skutki 1 10000',
                'arena uoss pomocnik skutki 1 10000 10 3'):
        ck('ADMIN LIVE V67' in await cmd(raw),raw)
    ck('ARENA11 KLASA' in await cmd('arena klasa Wojownik 10 0 POTWIERDZAM'))
    ck('MP 0/0' in await cmd('arena uoss pomocnik skutki 2'))
    ck('ADMIN LIVE V67' in await cmd('arena uoss pomocnik skutki 1 90000 10'))
    ck('ARENA11 KLASA' in await cmd('arena klasa Wojownik 10 300 POTWIERDZAM'))
    ck('+60 MP' in await cmd('arena uoss pomocnik skutki 1 90000 10'))
    ck('ARENA11 START' in await cmd('arena start black_rabite 100000 2000 Primm'))
    ck('Bubble' in await cmd('arena uoss pomocnik skutki'))
    ck('max HP 150000' in await cmd('arena uoss pomocnik skutki'))
    ck('HP 100000/150000' in await cmd('arena uoss pomocnik skutki'))
    ck('Dryad Preach' in await cmd('arena uoss pomocnik skutki 3'))
    ck('Bubble' in await cmd('arena uoss pomocnik skutki 2'))
    ck('Dryad Preach' in await cmd('arena uoss pomocnik skutki 3 90000 50'))
    ck('+8 MP' in await cmd('arena uoss pomocnik skutki 3 90000 50'))
    ck('Cure Water' in await cmd('arena uoss pomocnik skutki 2 10000 10'))
    ck('+23000 HP' in await cmd('arena uoss pomocnik skutki 2 10000 10'))
    ck('leczenie 46000 HP' in await cmd('arena uoss pomocnik skutki 2 10000 10'))
    user.guardian7_lab['actor8'].uoss_nullify_healing_rounds_v11179=3
    ck('leczenie zablokowane' in await cmd('arena uoss pomocnik skutki 2 10000 10'))
    ck('leczenie 0 HP' in await cmd('arena uoss pomocnik skutki 2 10000 10'))
    user.guardian7_lab['actor8'].uoss_nullify_healing_rounds_v11179=0
    ck('ARENA11 START' in await cmd('arena start serpentarius 100000 2000 Byblos'))
    ck('Cure' in await cmd('arena uoss pomocnik skutki 1 10000 10'))
    ck('+23000 HP' in await cmd('arena uoss pomocnik skutki 1 10000 10'))
    ck('X-Ether' in await cmd('arena uoss pomocnik skutki 1 90000 10'))
    ck('+25 MP' in await cmd('arena uoss pomocnik skutki 1 90000 10'))
    ck('ARENA11 START' in await cmd('arena start yiazmat 100000 2000 Montblanc'))
    ck('Bubble' in await cmd('arena uoss pomocnik skutki 2'))
    ck('max HP 150000' in await cmd('arena uoss pomocnik skutki 2'))
    ck('ARENA11 START' in await cmd('arena start odin 100000 2000 Seifer'))
    ck('No Mercy' in await cmd('arena uoss pomocnik skutki'))
    ck('ataki bez obliczen 1' in await cmd('arena uoss pomocnik skutki'))
    ck('ARENA11 START' in await cmd('arena start odin 100000 2000'))
    ck('brak aktywnego pomocnika' in await cmd('arena uoss pomocnik skutki'))
    ck('ARENA11 START' in await cmd('arena start black_rabite 100000 2000 Popoi'))
    lab=user.guardian7_lab
    ck((lab['round'],lab['hero_hp'],lab['boss'].hp,lab['total_dealt'],lab['total_taken'])==first)
    ck(random.getstate()==rng)
    ck(user.server.live_content_v1204.active==active)
    ck(user.server.live_content_v1204.draft==draft)
    ck(db.conn.total_changes==writes)
    ck(MOB_TEMPLATES['uoss_superboss_black_rabite_v11136']==template)
    ck(user.current_hp==20 and user.current_mana==10)
    ck(user.server.world.mobs=={})
    ck(not db.logged)
    ck('ARENA11:' in await cmd('arena wyjdz'))
    ck(user.guardian7_lab is None)
    db.conn.close()
    return n

def run():return asyncio.run(suite())
if __name__=='__main__':print('V67 UOSS SOURCE SUPPORT:',run(),'PASS')
