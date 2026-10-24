# -*- coding: utf-8 -*-
"""v43 Guardian9: replay, reversible lab and quest-read isolation checks."""
import asyncio
import copy
import random
from types import SimpleNamespace
from validation.v3600_admin_guardian2 import Fake
from systems.live_content_v1204 import LiveContentV1204
from data.mobs import MOB_TEMPLATES
from data.quests import QUESTS
from systems.admin_guardian9_v4300 import _state, _sync_actor, _simulation, _dependencies

async def suite():
    checks=0
    s=Fake();db=s.server.db
    s.server.live_content_v1204=LiveContentV1204(SimpleNamespace(conn=db.conn))
    service=s.server.live_content_v1204
    draft=copy.deepcopy(service.draft)
    template=copy.deepcopy(MOB_TEMPLATES['uoss_superboss_serpentarius_v11136'])
    quests=copy.deepcopy(QUESTS['bandit_patrol'])
    db.conn.execute("INSERT INTO quests(account_id,quest_id,status,progress,completion_count) VALUES(1,'bandit_patrol','active',4,0)")
    db.conn.commit()
    quest_rows=list(db.conn.execute('SELECT * FROM quests'))
    guest=Fake(False,db)
    async def run(cmd):
        await s.admin_command('guardian9 '+cmd)
        return s.messages[-1]
    for i in range(1,4):
        assert 'GUARDIAN9' in await run(f'pomoc {i}');checks+=1
    assert 'GUARDIAN9' in await run('pomoc 4');checks+=1
    await guest.admin_command('guardian9 arena start serpentarius 90000 1000')
    assert 'tylko' in guest.messages[-1] and not hasattr(guest,'guardian7_lab');checks+=1
    assert 'GUARDIAN9' in await run('arena prognoza 2');checks+=1
    assert 'ARENA9 START' in await run('arena start serpentarius 400000 1000 Byblos');checks+=1
    state=_state(s)
    assert state['actor8'].current_hp==400000;checks+=1
    assert state['actor8'].server.party_sessions()[0] is state['actor8'];checks+=1
    assert service.draft==draft and s.server.world.mobs=={};checks+=1
    prng=random.getstate();existing=(state["round"],state["boss"].hp,state["hero_hp"],len(state["adds"]),list(state["notes"]),list(state["statuses"]))
    for count in (1,3,20):
        message=await run(f'arena prognoza {count}')
        assert 'ARENA9 PROGNOZA' in message and 'BEZ ZMIAN' in message;checks+=1
        assert (state["round"],state["boss"].hp,state["hero_hp"],len(state["adds"]),list(state["notes"]),list(state["statuses"]))==existing;checks+=1
        assert random.getstate()==prng;checks+=1
        assert state['actor8'].server.party_sessions()[0] is state['actor8'];checks+=1
    assert 'GUARDIAN9' in await run('arena prognoza 21');checks+=1
    assert 'GUARDIAN9' in await run('arena prognoza 0');checks+=1
    assert 'GUARDIAN9' in await run('arena prognoza 3 dowolna');checks+=1
    assert 'ARENA9 MIGAWKA' in await run('arena migawka');checks+=1
    assert 'ARENA9 SERIA' in await run('arena seria 4');checks+=1
    assert s.guardian7_lab['round']==4;checks+=1
    assert len(s.guardian7_lab['adds'])==1;checks+=1
    assert s.guardian7_lab['actor8'].current_hp==s.guardian7_lab['hero_hp'];checks+=1
    assert 'ARENA9' in await run('arena status');checks+=1
    assert 'ARENA9' in await run('arena dziennik');checks+=1
    assert 'ARENA9 RAPORT' in await run('arena raport');checks+=1
    assert 'GUARDIAN9' in await run('arena przywroc NIE');checks+=1
    assert s.guardian7_lab['round']==4;checks+=1
    assert 'ARENA9 PRZYWROCONO' in await run('arena przywroc POTWIERDZAM');checks+=1
    assert s.guardian7_lab['round']==0;checks+=1
    assert s.guardian7_lab['actor8'].server.party_sessions()[0] is s.guardian7_lab['actor8'];checks+=1
    assert 'ARENA9' in await run('arena atak');checks+=1
    assert 'ARENA9' in await run('arena magia ogien');checks+=1
    assert 'ARENA9' in await run('arena lecz');checks+=1
    assert 'ARENA9' in await run('arena oczysc');checks+=1
    assert 'ARENA9' in await run('arena obrona');checks+=1
    assert 'GUARDIAN9' in await run('arena atak 44');checks+=1
    assert 'GUARDIAN9' in await run('arena seria 55');checks+=1
    assert 'ARENA9' in await run('arena wyjdz');checks+=1
    assert s.guardian7_lab is None and s.guardian9_snapshot is None;checks+=1
    assert 'GUARDIAN9' in await run('arena przywroc POTWIERDZAM');checks+=1
    # Independent tests on Black Rabite; never spawn in live world.
    assert 'ARENA9 START' in await run('arena start black_rabite 100000000 1000');checks+=1
    assert 'ARENA9 SERIA' in await run('arena seria 3');checks+=1
    assert len(s.guardian7_lab['adds'])>=1;checks+=1
    assert 'ARENA9' in await run('arena wyjdz');checks+=1
    payload='bandit_patrol | needed | 12 ; temple_rats | needed | 10'
    assert 'ROZNICE' in await run('questy seria roznice '+payload);checks+=1
    assert service.draft==draft;checks+=1
    assert 'GUARDIAN9' in await run('questy seria roznice '+payload+' ; noquest_q | needed | 4');checks+=1
    assert service.draft==draft;checks+=1
    assert 'DRAFT' in await run('questy draft');checks+=1
    assert 'QUEST9 ZALEZNOSCI' in await run('questy zaleznosci bandit_patrol');checks+=1
    assert 'GUARDIAN9' in await run('questy zaleznosci missing_123');checks+=1
    # Preview before and after an independently staged DRAFT; still no commit.
    await s.admin_command('guardian8 questy seria zmien '+payload+' | POTWIERDZAM')
    assert 'SERIA DRAFT' in s.messages[-1];checks+=1
    assert 'bandit_patrol' in await run('questy draft');checks+=1
    assert 'Brak zmiany wartosci' in await run('questy seria roznice '+payload);checks+=1
    draft_after=copy.deepcopy(service.draft)
    assert 'GUARDIAN9' in await run('questy draft 100');checks+=1
    assert service.draft==draft_after;checks+=1
    assert 'QUEST7 COFNIETO' in (await _guardian8_undo(s));checks+=1
    assert service.draft==draft;checks+=1
    # Source templates, player quest and SQLite remain unchanged.
    assert MOB_TEMPLATES['uoss_superboss_serpentarius_v11136']==template;checks+=1
    assert QUESTS['bandit_patrol']==quests;checks+=1
    assert list(db.conn.execute('SELECT * FROM quests'))==quest_rows;checks+=1
    assert s.server.world.mobs=={} and s.current_hp==20 and s.current_mana==10;checks+=1
    assert not any('guardian9' in str(row) for row in db.logged);checks+=1
    db.conn.close()
    return checks

async def _guardian8_undo(s):
    await s.admin_command('guardian8 questy cofnij POTWIERDZAM')
    return s.messages[-1]

def run():return asyncio.run(suite())
if __name__=='__main__':print('GUARDIAN9 v43:',run(),'checks PASS')
