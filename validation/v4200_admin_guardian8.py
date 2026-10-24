# -*- coding: utf-8 -*-
"""Isolation and optimistic concurrency tests for v42 Guardian8."""
import asyncio
import copy
from types import SimpleNamespace
from validation.v3600_admin_guardian2 import Fake
from systems.live_content_v1204 import LiveContentV1204
from data.mobs import MOB_TEMPLATES
from data.quests import QUESTS
from systems.admin_guardian8_v4200 import _batch_preview

async def suite():
    checks=0
    s=Fake();db=s.server.db
    s.server.live_content_v1204=LiveContentV1204(SimpleNamespace(conn=db.conn))
    service=s.server.live_content_v1204
    snap=copy.deepcopy(service.draft)
    runtime_mob=copy.deepcopy(MOB_TEMPLATES['uoss_superboss_serpentarius_v11136'])
    runtime_quest=copy.deepcopy(QUESTS['bandit_patrol'])
    db.conn.execute("INSERT INTO quests(account_id,quest_id,status,progress,completion_count) VALUES(1,'bandit_patrol','active',4,0)")
    db.conn.commit()
    rows=list(db.conn.execute('SELECT * FROM quests'))
    guest=Fake(False,db)
    async def run(command):
        await s.admin_command('guardian8 '+command)
        return s.messages[-1]
    for page in (1,2,3):
        assert 'GUARDIAN8' in await run('pomoc '+str(page));checks+=1
    assert 'GUARDIAN8' in await run('pomoc 7');checks+=1
    await guest.admin_command('guardian8 arena start serpentarius 10000 1000')
    assert 'tylko administrator' in guest.messages[-1];checks+=1
    assert not hasattr(guest,'guardian7_lab') and not db.logged;checks+=1
    assert 'ARENA8 START' in await run('arena start serpentarius 400000 1000 Byblos');checks+=1
    a=s.guardian7_lab;actor=a['actor8']
    assert actor is not s and actor.server is not s.server;checks+=1
    assert s.current_hp==20 and s.current_mana==10;checks+=1
    assert service.draft==snap and s.server.world.mobs=={} and db.logged==[];checks+=1
    # Source-known 9999 damage, timed effects and summon rotations.
    for _ in range(3):assert 'ARENA8 tura' in await run('arena atak');checks+=1
    assert 'Summon Zodiac Sentinel' in await run('arena atak');checks+=1
    assert len(a['adds'])==1 and a['adds'][0]['hp']>0;checks+=1
    assert 'pomocnika' in await run('arena atak 1');checks+=1
    assert 'GUARDIAN8' in await run('arena atak 99');checks+=1
    assert 'GUARDIAN8' in await run('arena magia ogien 99');checks+=1
    assert 'ARENA8' in await run('arena status');checks+=1
    assert 'ARENA8' in await run('arena dziennik');checks+=1
    assert 'ARENA8 RAPORT' in await run('arena wynik');checks+=1
    assert 'ARENA8' in await run('arena obrona');checks+=1
    # Force a sourced three-round healing block *on the private actor*.
    from world.uoss_superboss_runtime import superboss_source_timed_effect_v11179
    superboss_source_timed_effect_v11179(actor,a['template'],'Nullify Healing')
    assert actor.uoss_nullify_healing_rounds_v11179==3;checks+=1
    assert 'zablokowane' in await run('arena lecz');checks+=1
    assert actor.uoss_nullify_healing_rounds_v11179==2;checks+=1
    assert 'zablokowane' in await run('arena lecz');checks+=1
    assert 'zablokowane' in await run('arena lecz');checks+=1
    assert actor.uoss_nullify_healing_rounds_v11179==0;checks+=1
    assert 'Leczenie MODELOWE' in await run('arena lecz');checks+=1
    assert 'ARENA8' in await run('arena oczysc');checks+=1
    assert 'ARENA8' in await run('arena wyjdz');checks+=1
    assert s.guardian7_lab is None;checks+=1
    assert 'GUARDIAN8' in await run('arena lecz');checks+=1
    # Test source phases and summons for distinct bosses without DB writes.
    assert 'ARENA8 START' in await run('arena start black_rabite 1000000000 2000');checks+=1
    assert 'Protect' in ' '.join(s.guardian7_lab['notes']);checks+=1
    await run('arena atak')
    assert 'Summon Greater Demon' in await run('arena atak');checks+=1
    assert 'ARENA8' in await run('arena wyjdz');checks+=1
    assert 'ARENA8 START' in await run('arena start odin 900000 1000 Seifer');checks+=1
    assert s.guardian7_lab['boss'].uoss_power_breakdown_v11174;checks+=1
    assert 'ARENA8' in await run('arena wyjdz');checks+=1
    assert 'GUARDIAN8' in await run('arena start odin -1 100');checks+=1
    assert 'GUARDIAN8' in await run('arena start odin 100000 1000 Primm');checks+=1
    # Draft atomic batch; no side effects on invalid entries.
    payload='bandit_patrol | needed | 12 ; temple_rats | needed | 10'
    assert 'SERIA PLAN' in await run('questy seria plan '+payload);checks+=1
    assert service.draft==snap;checks+=1
    assert 'GUARDIAN8' in await run('questy seria zmien '+payload);checks+=1
    assert service.draft==snap;checks+=1
    assert 'SERIA DRAFT' in await run('questy seria zmien '+payload+' | POTWIERDZAM');checks+=1
    assert service.draft['quest_edits']['bandit_patrol']['needed']==12;checks+=1
    assert service.draft['quest_edits']['temple_rats']['needed']==10;checks+=1
    after=copy.deepcopy(service.draft)
    assert 'GUARDIAN8' in await run('questy seria zmien bandit_patrol | needed | 3 ; missing_qqq | needed | 6 | POTWIERDZAM');checks+=1
    assert service.draft==after;checks+=1
    assert 'GUARDIAN8' in await run('questy seria zmien bandit_patrol | needed | 3 ; bandit_patrol | needed | 4 | POTWIERDZAM');checks+=1
    assert service.draft==after;checks+=1
    assert 'QUEST7 COFNIETO' in await run('questy cofnij POTWIERDZAM');checks+=1
    assert service.draft==snap;checks+=1
    assert 'GUARDIAN8' in await run('questy cofnij POTWIERDZAM');checks+=1
    assert service.draft==snap;checks+=1
    assert 'SERIA DRAFT' in await run('questy seria zmien '+payload+' | POTWIERDZAM');checks+=1
    service.draft['quest_edits']['bandit_patrol']['needed']=13
    assert 'DRAFT zmienil sie' in await run('questy cofnij POTWIERDZAM');checks+=1
    assert service.draft['quest_edits']['bandit_patrol']['needed']==13;checks+=1
    assert 'QUEST7 AUDYT' in await run('questy audyt bandit_patrol');checks+=1
    assert 'QUEST7 SKAN' in await run('questy skan');checks+=1
    assert 'OLC7' in await run('olc kontrola');checks+=1
    assert MOB_TEMPLATES['uoss_superboss_serpentarius_v11136']==runtime_mob;checks+=1
    assert QUESTS['bandit_patrol']==runtime_quest;checks+=1
    assert list(db.conn.execute('SELECT * FROM quests'))==rows;checks+=1
    assert s.server.world.mobs=={} and all('guardian8' in str(row) for row in db.logged);checks+=1
    assert s.current_hp==20 and s.current_mana==10;checks+=1
    db.conn.close()
    return checks

def run():return asyncio.run(suite())
if __name__=='__main__':print('GUARDIAN8 v42:',run(),'checks PASS')
