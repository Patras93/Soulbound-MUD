# -*- coding: utf-8 -*-
"""v70 release audit: never claims 60/60, read-only, no accidental publication."""
import asyncio,copy,random
from types import SimpleNamespace
from validation.v3600_admin_guardian2 import Fake
from systems.live_content_v1204 import LiveContentV1204
from systems.admin_live_v7000 import readiness,differences
async def suite():
    n=0
    def ck(x,msg=''):
        nonlocal n
        assert x,msg;n+=1
    admin=Fake();db=admin.server.db
    srv=LiveContentV1204(SimpleNamespace(conn=db.conn))
    admin.server.live_content_v1204=srv
    guest=Fake(False,db);guest.server.live_content_v1204=srv
    orig=(copy.deepcopy(srv.active),copy.deepcopy(srv.draft),db.conn.total_changes,random.getstate())
    async def call(x,who=admin):
        await who.admin_command('live '+x)
        return who.messages[-1]
    ck('POMOC 25' in await call('pomoc 25'))
    for command in ('odbior','odbior sprawdz'):
        answer=await call(command)
        for term in ('v70','questow','NIEPOTWIERDZONY','NIEUKONCZONA','NIE zatwierdza','walidacja DRAFT'):
            ck(term in answer,(term,answer))
    ck('brak zmian OLC' in await call('odbior roznice'))
    ck('strona 1/1' in await call('odbior roznice 1'))
    ck('ODB IOR' not in await call('odbior bramki'))
    ck('60/60 PLUS' in await call('odbior bramki'))
    ck('WDROZ_PO_PREDEPLOY' in await call('odbior bramki'))
    ck('NVDA' in await call('odbior bramki'))
    for cmd in ('odbior roznice 0','odbior roznice 2','odbior roznice x',
                'odbior roznice '+'8'*100,'odbior extra','odbior roznice 1 extra'):
        ck('ADMIN LIVE ODBIOR:' in await call(cmd),cmd)
    for cmd in ('pomoc 25','odbior','odbior bramki','odbior roznice'):
        ck('Nieznana komenda' in await call(cmd,guest),cmd)
    # Ensure it reports staged-only changes, without validating/publishing them.
    srv.draft['balances']['live_demo']=dict(max_hp=300)
    ck('sekcji zmienionych 1' in await call('odbior roznice'))
    ck('balances' in await call('odbior roznice'))
    ck('walidacja DRAFT:' in await call('odbior'))
    ck('DRAFT rozni sie od aktywnego: TAK' in await call('odbior'))
    ck('brak zmian' not in await call('odbior roznice'))
    ck('CENTRUM 1/4' in await call('centrum 1'))
    ck(srv.active==orig[0]);ck(db.conn.total_changes==orig[2]);ck(random.getstate()==orig[3]);
    return n

def run():return asyncio.run(suite())
if __name__=='__main__':print('V70 ADMIN LIVE ODBIOR',run(),'PASS')
