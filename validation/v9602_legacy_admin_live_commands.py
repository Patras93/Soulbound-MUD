# -*- coding: utf-8 -*-
"""v96.00.2: both historical and modern admin live grammars must remain usable."""
import asyncio
import copy
from types import SimpleNamespace
from validation.v3600_admin_guardian2 import Fake
from systems.live_content_v1204 import LiveContentV1204


async def suite():
    owner=Fake()
    service=LiveContentV1204(SimpleNamespace(conn=owner.server.db.conn))
    owner.server.live_content_v1204=service
    guest=Fake(False,owner.server.db)
    guest.server.live_content_v1204=service
    base_draft=copy.deepcopy(service.draft)
    base_active=copy.deepcopy(service.active)
    changes=owner.server.db.conn.total_changes
    checks=0

    def ck(ok,label):
        nonlocal checks
        assert ok,label
        checks+=1

    async def send(who, command):
        await who.admin_command('live '+command)
        return who.messages[-1]

    # v54 no-argument overview and v70 detailed item request are separate.
    ck('EQ POKRYCIE' in await send(owner,'eq pokrycie'),'v54 legacy EQ')
    ck('5 zrodel' in await send(owner,'eq pokrycie'),'v54 legacy source count')
    ck('krypta: etap' in await send(owner,'eq pokrycie leather_vest 900'),'v70 detailed EQ')
    ck('Nieznana komenda' in await send(guest,'eq pokrycie'),'EQ admin rights')

    # v62 also owns its status; v64 owns its multi-objective counter.
    ck('QUEST PAKIET' in await send(owner,'questy pakiet status'),'v62 status')
    ck('ADMIN LIVE V64' in await send(owner,'questy pakiet licznik temple_rats'),'v64 counter validation')
    old='questy pakiet plan pole temple_rats reward_gold 100'
    ck('PLAN' in await send(owner,old),'v62 plan')
    ck('QUEST PAKIET' in await send(owner,'questy pakiet status'),'v62 status after plan')
    ck('DRAFT' in await send(owner,'questy pakiet zatwierdz POTWIERDZAM'),'v62 commit')
    ck('COFNIETO' in await send(owner,'questy pakiet cofnij POTWIERDZAM'),'v62 undo')
    ck(service.draft==base_draft,'v62 exact undo')

    # v94 final-state | grammar uses an independent plan, commit and undo.
    ck('QUEST PAKIET PLAN' in await send(owner,'questy pakiet plan temple_rats reward_gold | 100'),'v94 plan')
    ck('zatwierdzono' in await send(owner,'questy pakiet zatwierdz POTWIERDZAM'),'v94 commit')
    ck('Cofnieto' in await send(owner,'questy pakiet cofnij POTWIERDZAM'),'v94 undo')
    ck(service.draft==base_draft,'v94 exact undo')
    ck('Nieznana komenda' in await send(guest,'questy pakiet plan temple_rats reward_gold | 100'),'v94 rights')
    ck(service.active==base_active,'ACTIVE unchanged')
    ck(owner.server.db.conn.total_changes==changes,'SQLite unchanged')
    return checks


def run():
    return asyncio.run(suite())

if __name__=='__main__':
    print('ADMIN LIVE v96.00.2 HISTORICAL ROUTING: %d PASS' % run())
