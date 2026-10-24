# -*- coding: utf-8 -*-
"""One DRAFT transaction repairs both prerequisite IDs and objectives."""
import asyncio
import copy
from types import SimpleNamespace
from validation.v3600_admin_guardian2 import Fake
from systems.live_content_v1204 import LiveContentV1204
from systems.admin_live_integrity_v4900 import _effective

async def main():
    n=0
    def ok(flag,label):
        nonlocal n
        assert flag,label;n+=1
    admin=Fake();db=admin.server.db
    service=LiveContentV1204(SimpleNamespace(conn=db.conn))
    admin.server.live_content_v1204=service
    guest=Fake(False,db);guest.server.live_content_v1204=service
    async def run(command,user=admin):
        await user.admin_command('live '+command)
        return user.messages[-1]
    try:
        previous=copy.deepcopy(service.draft)
        # Stale prerequisite only in draft; no changes to accounts.
        service.draft['quest_edits']['temple_rats']={'requires_quest':'archived_quest_id'}
        starting=copy.deepcopy(service.draft)
        ok('POMOC 51' in await run('pomoc 51'),'help')
        ok('Nieznana komenda' in await run('pomoc 51',guest),'guest blocked')
        ok('Nieznana komenda' in await run('questy napraw kompleks plan kill skeleton temple_rat',guest),'guest plan blocked')
        ok('Nieznana komenda' in await run('questy napraw kompleks zatwierdz POTWIERDZAM',guest),'guest commit blocked')
        raw='questy napraw kompleks plan wymog archived_quest_id bandit_patrol; kill skeleton temple_rat; collect jewel_iron_ring healing_potion'
        answer=await run(raw)
        ok('KOMPLEKS PLAN' in answer,'combined plan')
        ok('3 operacji' in answer,'3 distinct ops')
        ok(service.draft==starting,'planning is read only')
        ok('zatwierdzono' in await run('questy napraw kompleks zatwierdz POTWIERDZAM'),'commit to draft')
        final=_effective(service)
        ok(final['temple_rats']['requires_quest']=='bandit_patrol','stale prerequisite repaired')
        ok(final['soul_tier_2_trial']['target']=='temple_rat','kill target repaired')
        ok(final['mirella_jewel_iron']['target']=='healing_potion','collect target repaired')
        ok(service.active==previous,'ACTIVE protected')
        ok('Cofnieto' in await run('questy napraw kompleks cofnij POTWIERDZAM'),'undo success')
        ok(service.draft==starting,'exact undo')
        for bad in (
            'questy napraw kompleks plan wymog archived_quest_id nonexistent',
            'questy napraw kompleks plan wymog temple_rats soul_tier_1_trial',
            'questy napraw kompleks plan kill skeleton nonexistent',
            'questy napraw kompleks plan kill skeleton temple_rat; kill skeleton goblin',
            'questy napraw kompleks plan collect missing healing_potion',
            'questy napraw kompleks plan wymog archived_quest_id temple_rats',
            'questy napraw kompleks plan foo old new',
        ):
            ok('ADMIN LIVE v93' in await run(bad),'invalid blocked '+bad)
            ok(service.draft==starting,'no partial edits after error')
        # Race: accepted quest after planning must block confirmation.
        ok('KOMPLEKS PLAN' in await run(raw),'planning before quest accepted')
        db.conn.execute("INSERT INTO quests VALUES(2,'temple_rats','active',0,0,0)")
        ok('zablokowane' in (await run('questy napraw kompleks zatwierdz POTWIERDZAM')).lower(),'late active block')
        ok(service.draft==starting,'no saved partial draft')
        db.conn.execute("DELETE FROM quests WHERE quest_id='temple_rats'")
        ok('KOMPLEKS PLAN' in await run(raw),'replan')
        ok('anulowano' in await run('questy napraw kompleks anuluj'),'cancel')
        ok('ADMIN LIVE v93' in await run('questy napraw kompleks zatwierdz POTWIERDZAM'),'cancel invalidates plan')
        # All changes must retain existing population and publish only explicitly.
        ok('KOMPLEKS PLAN' in await run(raw),'replan final')
        ok('zatwierdzono' in await run('questy napraw kompleks zatwierdz POTWIERDZAM'),'commit final')
        ok('PRZEDPUBLIKACJA OK' in await run('aktualizacja publikacja sprawdz'),'publication preflight')
        ok('Aktywowano' in service.apply(admin.server,'tester'),'publish')
        ok(service.revision==1,'revision 1')
        ok(service.conn.execute('PRAGMA integrity_check').fetchone()[0]=='ok','sqlite integrity')
        ok(service.conn.execute('SELECT COUNT(*) FROM quests').fetchone()[0]==0,'player progress unchanged')
        print(f'V93 COMBINED QUEST REPAIRS: {n} PASS',flush=True)
    finally:db.conn.close()

if __name__=='__main__':asyncio.run(main())
