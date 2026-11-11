# -*- coding: utf-8 -*-
"""Atomic quest target repairs using actual OLC, fake accounts, real SQLite."""
import asyncio
import copy
from types import SimpleNamespace
from validation.v3600_admin_guardian2 import Fake
from systems.live_content_v1204 import LiveContentV1204
from systems.admin_live_integrity_v4900 import _effective

async def main():
    checks=0
    def ok(test,label):
        nonlocal checks
        assert test,label
        checks+=1
    a=Fake();db=a.server.db
    service=LiveContentV1204(SimpleNamespace(conn=db.conn));a.server.live_content_v1204=service
    guest=Fake(False,db);guest.server.live_content_v1204=service
    async def cmd(line,session=a):
        await session.admin_command('live '+line)
        return session.messages[-1]
    try:
        ok('POMOC 50' in await cmd('pomoc 50'),'help')
        ok('Nieznana komenda' in await cmd('pomoc 50',guest),'help admin only')
        ok('Nieznana komenda' in await cmd('questy cele znajdz kill skeleton',guest),'read admin only')
        ok('Nieznana komenda' in await cmd('questy cele plan kill skeleton | temple_rat',guest),'write admin only')
        original=copy.deepcopy(service.draft)
        ok('soul_tier_2_trial' in await cmd('questy cele znajdz kill skeleton'),'find real quest')
        ok('BRAK' in await cmd('questy cele znajdz collect not_a_real_id'),'find missing')
        for bad in ('questy cele plan kill skeleton | missing_monster',
                    'questy cele plan kill skeleton | skeleton',
                    'questy cele plan kill skeleton | temple_rat; kill skeleton | goblin',
                    'questy cele plan collect nonsense | healing_potion',
                    'questy cele plan reward healing_potion | nonexist_item',
                    'questy cele plan talk wrong | priest_elor',
                    'questy cele plan kill skeleton temple_rat',
                    'questy cele plan kill skeleton | temple_rat;',
                    'questy cele plan kill skeleton | temple_rat; collect missing | healing_potion'):
            ok('ADMIN LIVE v92' in await cmd(bad),'invalid rejected '+bad)
            ok(service.draft==original,'invalid did not mutate')
        raw='questy cele plan kill skeleton | temple_rat; collect jewel_iron_ring | healing_potion'
        result=await cmd(raw)
        ok('QUEST CELE PLAN' in result,'valid mixed plan')
        ok('2 operacji' in result,'both modes')
        ok(service.draft==original,'plan read only')
        ok('zatwierdzono' in await cmd('questy cele zatwierdz POTWIERDZAM'),'confirmed')
        cat=_effective(service)
        ok(cat['soul_tier_2_trial']['target']=='temple_rat','real kill target')
        ok(cat['mirella_jewel_iron']['target']=='healing_potion','real collect target')
        ok(service.active==original,'active still unchanged')
        ok('Cofnieto' in await cmd('questy cele cofnij POTWIERDZAM'),'undo')
        ok(service.draft==original,'undo exact snapshot')
        ok('QUEST CELE PLAN' in await cmd(raw),'plan again')
        ok('anulowany' in await cmd('questy cele anuluj'),'cancel')
        ok('ADMIN LIVE v92' in await cmd('questy cele zatwierdz POTWIERDZAM'),'cancel prevents commit')
        ok('QUEST CELE PLAN' in await cmd(raw),'plan for concurrency')
        service.draft['quest_edits']['temple_rats']={'reward_gold':25}
        ok('DRAFT/ACTIVE zmienione' in await cmd('questy cele zatwierdz POTWIERDZAM'),'detect stale draft')
        service.draft=copy.deepcopy(original)
        # Active player checks before planning and again at confirmation.
        db.conn.execute("INSERT INTO quests VALUES(2,'soul_tier_2_trial','active',0,0,0)")
        ok('aktyw' in (await cmd(raw)).lower() or 'graczy' in a.messages[-1].lower(),'block active before plan')
        db.conn.execute("DELETE FROM quests WHERE quest_id='soul_tier_2_trial'")
        ok('QUEST CELE PLAN' in await cmd(raw),'plan after active gone')
        db.conn.execute("INSERT INTO quests VALUES(2,'soul_tier_2_trial','active',0,0,0)")
        ok('Quest zostal przyjety' in await cmd('questy cele zatwierdz POTWIERDZAM'),'block active at confirmation')
        db.conn.execute("DELETE FROM quests WHERE quest_id='soul_tier_2_trial'")
        # Reward item move retains count and prevents collision.
        service.draft=copy.deepcopy(original)
        service.draft['quest_edits']['temple_rats']={'reward_items':{'healing_potion':2}}
        before=copy.deepcopy(service.draft)
        ok('QUEST CELE PLAN' in await cmd('questy cele plan reward healing_potion | soul_elixir'),'reward plan')
        ok(service.draft==before,'reward plan read-only')
        ok('zatwierdzono' in await cmd('questy cele zatwierdz POTWIERDZAM'),'reward commit')
        ok(_effective(service)['temple_rats']['reward_items']=={'soul_elixir':2},'reward quantity preserved')
        ok('Cofnieto' in await cmd('questy cele cofnij POTWIERDZAM'),'reward undo')
        ok(service.draft==before,'reward undo exact')
        # NPC resolves ID to actual authored name, not a fake new one.
        ok('QUEST CELE PLAN' in await cmd('questy cele plan npc priest_elor | miner_toren'),'npc remap valid')
        ok('zatwierdzono' in await cmd('questy cele zatwierdz POTWIERDZAM'),'npc commit')
        ok(_effective(service)['temple_rats']['giver']=='Górnik Toren','npc name changed')
        ok('Cofnieto' in await cmd('questy cele cofnij POTWIERDZAM'),'npc undo')
        # Entire mixed package published normally to OLC without progress editing.
        service.draft=copy.deepcopy(original)
        ok('QUEST CELE PLAN' in await cmd(raw),'last plan')
        ok('zatwierdzono' in await cmd('questy cele zatwierdz POTWIERDZAM'),'last draft commit')
        ok('PRZEDPUBLIKACJA OK' in await cmd('aktualizacja publikacja sprawdz'),'normal publication preflight')
        ok('Aktywowano' in service.apply(a.server,'tester'),'published')
        ok(service.revision==1,'revision stored')
        ok(_effective(service)['soul_tier_2_trial']['target']=='temple_rat','published kill')
        ok(_effective(service)['mirella_jewel_iron']['target']=='healing_potion','published collect')
        ok(db.conn.execute('PRAGMA integrity_check').fetchone()[0]=='ok','SQLite integrity')
        ok(db.conn.execute('SELECT COUNT(*) FROM quests').fetchone()[0]==0,'no player quest records changed')
        print(f'V92 QUEST TARGET BUNDLE: {checks} PASS',flush=True)
    finally:
        db.conn.close()

if __name__=='__main__':asyncio.run(main())
