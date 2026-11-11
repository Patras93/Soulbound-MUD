# -*- coding: utf-8 -*-
"""v69 actual commands, owner gate and read-only output tests."""
import asyncio,copy,random
from types import SimpleNamespace
from validation.v3600_admin_guardian2 import Fake
from systems.live_content_v1204 import LiveContentV1204
from systems.admin_live_v6900 import _ENTRIES,index,search
async def suite():
    n=0
    def ck(x,msg=''):
        nonlocal n
        assert x,msg;n+=1
    admin=Fake(); db=admin.server.db
    srv=LiveContentV1204(SimpleNamespace(conn=db.conn))
    admin.server.live_content_v1204=srv
    guest=Fake(False,db);guest.server.live_content_v1204=srv
    before=(copy.deepcopy(srv.active),copy.deepcopy(srv.draft),db.conn.total_changes,random.getstate())
    async def call(x,who=admin):
        await who.admin_command('live '+x)
        return who.messages[-1]
    ck(len(_ENTRIES)==24)
    for p in range(1,5):
        ck(f'CENTRUM {p}/4' in await call(f'centrum {p}'),str(p))
        ck('centrum' in (await call(f'centrum {p}')).lower())
    ck('CENTRUM 1/4' in await call('centrum'))
    ck('ADMIN LIVE POMOC 24' in await call('pomoc 24'))
    ck('klas 22' in await call('centrum status'))
    ck('questow' in await call('centrum status'))
    for term in ('quest','arena','limity','eq','pomoc','OLC','draft','exp','boss','primm','drop'):
        ck('SZUKAJ' in await call(f'centrum szukaj {term}'),term)
    for x in ('centrum 0','centrum 5','centrum -1','centrum 9999999','centrum abc',
              'centrum szukaj a','centrum szukaj ','centrum szukaj '+'x'*46,'centrum xyz extra'):
        ck('ADMIN LIVE CENTRUM:' in await call(x),x)
    for x in ('pomoc 24','centrum','centrum 2','centrum szukaj quest','centrum status'):
        ck('Nieznana komenda' in await call(x,guest),x)
    ck('ZGODNOSC' in (await call('arena zgodnosc black_rabite')).upper())
    ck(srv.active==before[0]);ck(srv.draft==before[1]);ck(db.conn.total_changes==before[2]);ck(random.getstate()==before[3]);
    return n

def run():return asyncio.run(suite())
if __name__=='__main__':print('V69 ADMIN LIVE CENTRUM',run(),'PASS')
