# -*- coding: utf-8 -*-
"""End-to-end draft and SQLite controls for migration of stale quest IDs."""
import asyncio
import copy
from types import SimpleNamespace
from validation.v3600_admin_guardian2 import Fake
from systems.live_content_v1204 import LiveContentV1204
from systems.admin_live_integrity_v4900 import _effective

async def run():
    count=0
    def ok(test,label):
        nonlocal count
        assert test,label
        count+=1
    user=Fake(); db=user.server.db
    service=LiveContentV1204(SimpleNamespace(conn=db.conn));user.server.live_content_v1204=service
    guest=Fake(False,db);guest.server.live_content_v1204=service
    async def cmd(line,who=user):
        await who.admin_command('live '+line)
        return who.messages[-1]
    try:
        ok('POMOC 49' in await cmd('pomoc 49'),'help')
        ok('Nieznana komenda' in await cmd('pomoc 49',guest),'guest help')
        ok('Nieznana komenda' in await cmd('questy zaleznosci migracja skan',guest),'guest scan')
        ok('Nieznana komenda' in await cmd('questy zaleznosci migracja plan Stary | temple_rats',guest),'guest plan')
        old=copy.deepcopy(service.draft)
        # A realistic imported OLC anomaly: two quests refer to an obsolete ID.
        service.draft['quest_edits']['mirella_jewel_iron']={'requires_quest':'stary_blad_id'}
        service.draft['quest_edits']['mirella_jewel_gold']={'requires_quests':['stary_blad_id']}
        before=copy.deepcopy(service.draft)
        ok('stary_blad_id' in await cmd('questy zaleznosci migracja skan'),'scan finds broken')
        for bad in ('questy zaleznosci migracja plan stary_blad_id | niezdefiniowany',
                    'questy zaleznosci migracja plan mirella_jewel_iron | temple_rats',
                    'questy zaleznosci migracja plan stary_blad_id | stary_blad_id',
                    'questy zaleznosci migracja plan stary_blad_id | mirella_jewel_gold',
                    'questy zaleznosci migracja plan stary_blad_id | temple_rats; stary_blad_id | temple_rats',
                    'questy zaleznosci migracja plan stary_blad_id | temple_rats;'):
            ok('ADMIN LIVE v91' in await cmd(bad),'blocked '+bad)
            ok(service.draft==before,'bad plan no mutation')
        plan='questy zaleznosci migracja plan stary_blad_id | temple_rats'
        answer=await cmd(plan)
        ok('MIGRACJA PLAN' in answer,'valid plan')
        ok('poprawionych questow 2' in answer,'both references')
        ok(service.draft==before,'plan no draft write')
        ok('zatwierdzono' in await cmd('questy zaleznosci migracja zatwierdz POTWIERDZAM'),'commit')
        after=_effective(service)
        ok(after['mirella_jewel_iron']['requires_quest']=='temple_rats','single replaced')
        ok(after['mirella_jewel_gold']['requires_quests']==['temple_rats'],'list replaced')
        ok(service.active==old,'active unchanged')
        ok('Cofnieto' in await cmd('questy zaleznosci migracja cofnij POTWIERDZAM'),'undo')
        ok(service.draft==before,'undo restored draft')
        ok('MIGRACJA PLAN' in await cmd(plan),'plan again')
        ok('anulowany' in await cmd('questy zaleznosci migracja anuluj'),'cancel')
        ok('ADMIN LIVE v91' in await cmd('questy zaleznosci migracja zatwierdz POTWIERDZAM'),'cancel forbids commit')
        # Concurrent draft edits must invalidate a previous plan.
        ok('MIGRACJA PLAN' in await cmd(plan),'plan for stale check')
        service.draft['quest_edits']['temple_rats']={'reward_gold':34}
        ok('DRAFT/ACTIVE zmienione' in await cmd('questy zaleznosci migracja zatwierdz POTWIERDZAM'),'stale commit blocked')
        service.draft=copy.deepcopy(before)
        # Quest is active (in the database) => no retroactive remapping.
        db.conn.execute("INSERT INTO quests VALUES(2,'mirella_jewel_iron','active',0,0,0)")
        ok('ADMIN LIVE v91' in await cmd(plan),'active quest blocked')
        db.conn.execute("DELETE FROM quests WHERE quest_id='mirella_jewel_iron'")
        ok('MIGRACJA PLAN' in await cmd(plan),'plan when inactive')
        db.conn.execute("INSERT INTO quests VALUES(2,'mirella_jewel_iron','active',0,0,0)")
        ok('Quest zostal przyjety' in await cmd('questy zaleznosci migracja zatwierdz POTWIERDZAM'),'active after plan blocks')
        db.conn.execute("DELETE FROM quests WHERE quest_id='mirella_jewel_iron'")
        # Verify direct publication also blocks a different edit path when active.
        service.draft=copy.deepcopy(service.active)
        service.draft['quest_edits']['mirella_jewel_iron']={'requires_quest':'temple_rats'}
        db.conn.execute("INSERT INTO quests VALUES(2,'mirella_jewel_iron','active',0,0,0)")
        try:service.apply(user.server,'testadmin',dry_run=True)
        except ValueError as exc:ok('poprzednikow' in str(exc),'global preflight rejects active')
        else:ok(False,'active preflight incorrectly accepted')
        try:service.apply(user.server,'testadmin')
        except ValueError as exc:ok('poprzednikow' in str(exc),'global publisher rejects active')
        else:ok(False,'active publisher incorrectly accepted')
        ok(service.revision==0,'no publication')
        ok(service.active==old,'no active drift')
        db.conn.execute("DELETE FROM quests WHERE quest_id='mirella_jewel_iron'")
        service.draft=copy.deepcopy(before)
        ok('MIGRACJA PLAN' in await cmd(plan),'good plan after remove')
        ok('zatwierdzono' in await cmd('questy zaleznosci migracja zatwierdz POTWIERDZAM'),'good commit')
        ok('PRZEDPUBLIKACJA OK' in await cmd('aktualizacja publikacja sprawdz'),'production preflight')
        ok('Aktywowano' in service.apply(user.server,'testadmin'),'real publication')
        ok(service.revision==1,'revision advanced')
        ok(_effective(service)['mirella_jewel_iron']['requires_quest']=='temple_rats','published single')
        ok(_effective(service)['mirella_jewel_gold']['requires_quests']==['temple_rats'],'published multiple')
        ok('AUDYT OK' in await cmd('rewizje audyt'),'revision history valid')
        ok(db.conn.execute('PRAGMA integrity_check').fetchone()[0]=='ok','SQLite integrity')
        print(f'V91 QUEST ID MIGRATION: {count} PASS',flush=True)
    finally:
        db.conn.close()

if __name__=='__main__':asyncio.run(run())
