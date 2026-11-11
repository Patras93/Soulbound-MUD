# -*- coding: utf-8 -*-
"""Private arena/source hooks & validated, atomic, undoable OLC quest repairs."""
import asyncio
import copy
import sqlite3
from types import SimpleNamespace
from validation.v3600_admin_guardian2 import Fake
from data.quests import QUESTS
from data.mobs import MOB_TEMPLATES
from systems.live_content_v1204 import LiveContentV1204
from systems.admin_guardian7_v4100 import (
    _lab_start,_lab_turn,_lab_status,_lab_report,_repair,_repair_preview,_audit_one,
    _audit_page,_undo,_olc_guard,handle_guardian7)

async def suite():
    count=0
    s=Fake();db=s.server.db
    stranger=Fake(False,db)
    await stranger.admin_command('guardian7 pomoc 1')
    assert 'tylko wlasciciel' in stranger.messages[-1] and not db.logged;count+=1
    service=LiveContentV1204(SimpleNamespace(conn=db.conn))
    s.server.live_content_v1204=service
    original_draft=copy.deepcopy(service.draft)
    orig_boss=copy.deepcopy(MOB_TEMPLATES['uoss_superboss_black_rabite_v11136'])
    orig_quest=copy.deepcopy(QUESTS['bandit_patrol'])
    db.conn.execute("INSERT INTO quests(account_id,quest_id,status,progress,completion_count) VALUES(1,'bandit_patrol','active',4,0)")
    db.conn.commit()
    db_state=list(db.conn.execute('SELECT * FROM quests'))
    async def run(text):
        await s.admin_command('guardian7 '+text)
        return s.messages[-1]
    for page in (1,2,3):
        assert f'{page}/3' in await run('pomoc '+str(page));count+=1
    assert 'GUARDIAN7' in await run('pomoc 4');count+=1
    # Real source templates are exercised with a private clone, never live World.
    assert 'ARENA7 START' in await run('arena start black_rabite 900000 20000');count+=1
    assert s.guardian7_lab['key']=='black_rabite' and s.current_hp==20;count+=1
    assert s.server.world.mobs=={} and not db.logged;count+=1
    assert service.draft==original_draft;count+=1
    assert 'tura 1' in await run('arena atak');count+=1
    assert s.guardian7_lab['boss'].hp==orig_boss['max_hp']-20000;count+=1
    assert 'Summon Greater Demon' in await run('arena obrona');count+=1
    assert 'tura 3' in await run('arena atak');count+=1
    assert 'RAPORT' in await run('arena wynik');count+=1
    assert 'HP' in await run('arena status');count+=1
    assert 'DZIENNIK' in await run('arena dziennik 1');count+=1
    assert 'pomocnicy strona 2' in await run('arena status 2');count+=1
    assert 'GUARDIAN7' in await run('arena atak 99');count+=1
    assert 'GUARDIAN7' in await run('arena magia ogien 99');count+=1
    assert 'ARENA7' in await run('arena wyjdz') and s.guardian7_lab is None;count+=1
    assert 'brak aktywnego testu' in await run('arena status');count+=1
    assert 'GUARDIAN7' in await run('arena atak');count+=1
    # Exact Sourced percent-HP ability and status tracking for UOSS.
    assert 'ARENA7 START' in await run('arena start serpentarius 500000 1000 Byblos');count+=1
    # Source script summons after round four.
    for _ in range(3):await run('arena atak')
    assert 'Summon Zodiac Sentinel' in await run('arena atak');count+=1
    assert service.draft==original_draft and db.logged==[];count+=1
    await run('arena wyjdz')
    assert 'ARENA7 START' in await run('arena start odin 100000 10000 Seifer');count+=1
    assert s.guardian7_lab['helper']=='Seifer';count+=1
    assert 'GUARDIAN7' in await run('arena start odin 100000 10000 Primm');count+=1
    assert s.guardian7_lab['helper']=='Seifer';count+=1
    assert 'GUARDIAN7' in await run('arena start missing_boss 10000 10000');count+=1
    from world.uoss_superbosses import UOSS_SUPERBOSS_ENCOUNTERS_V11134
    from systems.admin_guardian7_v4100 import _template
    for bosskey in UOSS_SUPERBOSS_ENCOUNTERS_V11134:
        mid,meta,origin=_template(service,bosskey)
        assert meta['uoss_unique_superboss_key']==bosskey;count+=1
    assert 'GUARDIAN7' in await run('arena start odin -2 900');count+=1
    assert service.draft==original_draft and db.logged==[];count+=1
    await run('arena wyjdz')
    # Repair is a REVIEW then VALIDATED DRAFT then explicit publication elsewhere.
    assert 'QUEST7 PLAN' in await run('questy plan bandit_patrol | needed | 3');count+=1
    assert service.draft==original_draft;count+=1
    assert 'POTWIERDZAM' in await run('questy zmien bandit_patrol | needed | 3');count+=1
    assert service.draft==original_draft;count+=1
    assert 'QUEST7 DRAFT' in await run('questy zmien bandit_patrol | needed | 3 | POTWIERDZAM');count+=1
    assert service.draft['quest_edits']['bandit_patrol']['needed']==3;count+=1
    assert service.active['quest_edits']=={} and QUESTS['bandit_patrol']==orig_quest;count+=1
    assert db.conn.execute("SELECT progress FROM quests WHERE quest_id='bandit_patrol'").fetchone()[0]==4;count+=1
    assert 'QUEST7 AUDYT' in await run('questy audyt bandit_patrol');count+=1
    assert 'QUEST7 PRZEGLAD' in await run('questy przeglad 1');count+=1
    assert 'QUEST7 SKAN GLOBAL' in await run('questy skan');count+=1
    assert 'OLC7' in await run('olc kontrola');count+=1
    after=copy.deepcopy(service.draft)
    assert 'GUARDIAN7' in await run('questy zmien bandit_patrol | needed | 0 | POTWIERDZAM');count+=1
    assert service.draft==after;count+=1
    assert 'GUARDIAN7' in await run('questy plan bandit_patrol | target | not_a_real_mob');count+=1
    assert service.draft==after;count+=1
    assert 'GUARDIAN7' in await run('questy plan bandit_patrol | needed | 7 | needed | 8');count+=1
    assert service.draft==after;count+=1
    assert 'GUARDIAN7' in await run('questy plan bandit_patrol | kind | talk_npc');count+=1
    assert service.draft==after;count+=1
    assert 'GUARDIAN7' in await run('questy plan unknown_blah | needed | 3');count+=1
    assert service.draft==after;count+=1
    assert 'GUARDIAN7' in await run('questy przeglad 9999');count+=1
    assert service.draft==after;count+=1
    assert 'QUEST7 COFNIETO' in await run('questy cofnij POTWIERDZAM');count+=1
    assert service.draft==original_draft;count+=1
    assert 'GUARDIAN7' in await run('questy cofnij POTWIERDZAM');count+=1
    assert service.draft==original_draft;count+=1
    assert 'DRAFT' in await run('questy zmien bandit_patrol | reward_stat_xp | 25000 | POTWIERDZAM');count+=1
    assert 'olc_reward_stat_xp' in service.draft['quest_edits']['bandit_patrol'];count+=1
    # Undo refuses other user's intermediate change: no corruption of concurrent DRAFT edits.
    service.draft['quest_edits']['bandit_patrol']['needed']=6
    assert 'DRAFT zmienil sie' in await run('questy cofnij POTWIERDZAM');count+=1
    assert service.draft['quest_edits']['bandit_patrol']['needed']==6;count+=1
    assert service.active['quest_edits']=={};count+=1
    assert MOB_TEMPLATES['uoss_superboss_black_rabite_v11136']==orig_boss;count+=1
    assert QUESTS['bandit_patrol']==orig_quest;count+=1
    assert s.current_hp==20 and s.current_mana==10 and s.server.world.mobs=={};count+=1
    assert list(db.conn.execute('SELECT * FROM quests'))==db_state;count+=1
    db.conn.close()
    return count

def run():return asyncio.run(suite())
if __name__=='__main__':print('GUARDIAN7 v41:',run(),'checks PASS')
