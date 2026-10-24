# -*- coding: utf-8 -*-
"""v89: test exact production prepublication checks without writes to world/SQLite."""
import asyncio
import copy
import random
from types import SimpleNamespace
from validation.v3600_admin_guardian2 import Fake
from systems.live_content_v1204 import LiveContentV1204

async def run():
    n=0
    def ok(test,reason=''):
        nonlocal n
        assert test,reason
        n+=1
    owner=Fake(); db=owner.server.db
    service=LiveContentV1204(SimpleNamespace(conn=db.conn))
    owner.server.live_content_v1204=service
    guest=Fake(False,db);guest.server.live_content_v1204=service
    async def cmd(value,s=owner):
        await s.admin_command('live '+value)
        return s.messages[-1]
    baseline=copy.deepcopy(service.active)
    rng=random.getstate();changes=db.conn.total_changes
    try:
        ok('POMOC 47' in await cmd('pomoc 47'))
        ok('Nieznana komenda' in await cmd('pomoc 47',guest))
        ok('Nieznana komenda' in await cmd('aktualizacja porownaj',guest))
        ok('Nieznana komenda' in await cmd('aktualizacja publikacja sprawdz',guest))
        ok('BRAK' in await cmd('aktualizacja porownaj'))
        ok('Nie ma nowych zmian' in await cmd('aktualizacja publikacja sprawdz'))
        ok('ADMIN LIVE V89' in await cmd('aktualizacja porownaj XYZ'))
        ok('ADMIN LIVE V89' in await cmd('aktualizacja porownaj 99'))
        ok('aktualizacja' in await cmd('pomoc 46'))
        multi=('aktualizacja plan quest temple_rats reward_gold | 100; '
               'mob temple_rat damage | 5; '
               'item leather_vest price | 90; '
               'uoss black_rabite furia | 3:115:4')
        ok('4 pol' in await cmd(multi))
        ok('zatwierdzono' in await cmd('aktualizacja zatwierdz POTWIERDZAM'))
        ok('UOSS/v34_rules' in await cmd('aktualizacja status'))
        comparison=await cmd('aktualizacja porownaj')
        for key in ('QUEST temple_rats.reward_gold','MOB temple_rat.damage','EQ leather_vest.price','UOSS black_rabite.FURIA'):
            ok(key in comparison,key+' missing in '+comparison)
        ok('zmienionych pol' in comparison)
        ok('DRAFT=100' in comparison)
        ok('DRAFT=5' in comparison)
        ok('DRAFT=90' in comparison)
        ok('inne sekcje OLC' not in comparison)

        previous=copy.deepcopy(service.draft)
        check=await cmd('aktualizacja publikacja sprawdz')
        ok('PRZEDPUBLIKACJA OK' in check,check)
        ok('Odcisk DRAFT' in check)
        ok('BEZ ZAPISU' in check)
        ok(service.active==baseline and service.draft==previous)
        ok(db.conn.total_changes==changes)
        ok(random.getstate()==rng)
        ok('Cofnieto' in await cmd('aktualizacja cofnij POTWIERDZAM'))
        ok(service.draft==baseline)
        # Many changes; verify page ordering, page bounds, no uncontrolled output.
        for i in range(14):
            service.draft['quest_edits'][f'quest_fake_{i:02d}']={'needed':i}
        first=await cmd('aktualizacja porownaj 1')
        second=await cmd('aktualizacja porownaj 2')
        ok('1/2' in first)
        ok('2/2' in second)
        ok('quest_fake_00' in first and 'quest_fake_07' in second)
        ok('ADMIN LIVE V89' in await cmd('aktualizacja porownaj 3'))
        service.draft=copy.deepcopy(baseline)
        # Real fight in session: exact publication guard must block UOSS changes.
        service.draft['v34_rules']['uoss']['black_rabite']={'every':3,'stack_percent':115,'max_stacks':4}
        owner.server.world.mobs['in_combat']=SimpleNamespace(engaged_by={1},aoe_engaged_by=set(),
            template_id='temple_rat',home_room_id='temple',room_id='temple')
        blocked=await cmd('aktualizacja publikacja sprawdz')
        ok('OLC24' in blocked and 'walki' in blocked,blocked)
        ok(service.active==baseline and db.conn.total_changes==changes)
        owner.server.world.mobs.clear()
        ok('PRZEDPUBLIKACJA OK' in await cmd('aktualizacja publikacja sprawdz'))
        service.draft=copy.deepcopy(baseline)
        # Active player quest: normal live_content_v1204.apply must block objective change.
        db.conn.execute("INSERT INTO quests VALUES (2,'temple_rats','active',0,0,0)")
        start=db.conn.total_changes
        service.draft['quest_edits']['temple_rats']={'target':'bandit'}
        blocked=await cmd('aktualizacja publikacja sprawdz')
        ok('Quest temple_rats' in blocked and 'aktywny' in blocked,blocked)
        ok(db.conn.total_changes==start and service.active==baseline)
        service.draft=copy.deepcopy(baseline)
        ok('Nie ma nowych zmian' in await cmd('aktualizacja publikacja sprawdz'))
        # Actual activation shares precisely the same path as dry-run.
        service.draft['quest_edits']['temple_rats']={'reward_gold':123}
        ok('PRZEDPUBLIKACJA OK' in await cmd('aktualizacja publikacja sprawdz'))
        revision=service.revision
        ok('Aktywowano rewizję' in service.apply(owner.server,'owner'))
        ok(service.revision==revision+1)
        ok(service.active['quest_edits']['temple_rats']['reward_gold']==123)
        persisted=db.conn.execute('SELECT revision,payload FROM live_content_v1204 WHERE id=1').fetchone()
        ok(persisted['revision']==service.revision and '123' in persisted['payload'])
        ok(service.draft==service.active)
        ok('Nie ma nowych zmian' in await cmd('aktualizacja publikacja sprawdz'))
        print(f'ADMIN LIVE v89 PREFLIGHT: {n} PASS',flush=True)
    finally:
        db.conn.close()
    return n

if __name__=='__main__':
    asyncio.run(run())
