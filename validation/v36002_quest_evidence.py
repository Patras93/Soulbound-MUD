# -*- coding: utf-8 -*-
"""Quest incident evidence: read-only, bounded, no rewards or world mutation."""
import asyncio
import copy
from core.bootstrap_economy_professions import ADMIN_ACCOUNT_NAMES
from validation.v3600_admin_guardian2 import Fake, DB
from systems.admin_quest_diagnostics_v36002 import scan_quests, trace_quest, npc_quest

async def _suite():
    db=DB()
    db.conn.execute('CREATE TABLE inventory(account_id INTEGER,item_id TEXT,quantity INTEGER)')
    db.conn.execute("INSERT INTO inventory VALUES(2,'soul_shard',7)")
    db.conn.execute('''CREATE TABLE admin_errors_v1224(
      id TEXT PRIMARY KEY,created_at TEXT DEFAULT CURRENT_TIMESTAMP,
      exception TEXT NOT NULL,file TEXT NOT NULL,line INT NOT NULL,
      subsystem TEXT NOT NULL,handler TEXT NOT NULL,
      resolved_at TEXT NOT NULL DEFAULT '',resolved_by TEXT NOT NULL DEFAULT '')''')
    s=Fake(True,db)
    baseline=copy.deepcopy(s.server.live_content_v1204.draft)
    checks=0
    await s.admin_command('blad trop Friend temple_rats')
    assert any('NIEPRZYJETY' in line for line in s.messages); checks+=1
    assert any('temple_rat' in line for line in s.messages); checks+=1
    assert any('priest_elor' in line for line in s.messages); checks+=1
    assert any('Zapis zabojstwa' in line for line in s.messages); checks+=1
    await s.admin_command('blad npc temple_rats')
    assert any('Kapłan Elor' in line or 'priest_elor' in line for line in s.messages); checks+=1
    await s.admin_command('blad npc BAD_QUEST')
    assert 'Nieznany QUEST_ID' in s.messages[-1]; checks+=1
    await s.admin_command('blad trop Friend BAD_QUEST')
    assert 'ID questu nie istnieje' in s.messages[-1]; checks+=1
    await s.admin_command('blad trop BAD_PLAYER temple_rats')
    assert 'Nie znaleziono postaci' in s.messages[-1]; checks+=1
    # Actual saved quest + no synthetic grant.
    db.conn.execute("INSERT INTO quests VALUES(2,'temple_rats','active',2,0,0)")
    await s.admin_command('blad trop Friend temple_rats')
    assert any('postep 2' in line for line in s.messages); checks+=1
    assert db.quest(2,'temple_rats')['progress']==2; checks+=1
    assert not db.logged; checks+=1
    await s.admin_command('blad skan Friend')
    assert '0 wymagajacych sprawdzenia' in s.messages[-2]; checks+=1
    await s.admin_command('blad skan Friend 100')
    assert 'zakres 1-30' in s.messages[-1] or 'zakres 1' in s.messages[-1]; checks+=1
    await s.admin_command('blad skan NOBODY')
    assert 'Nie znaleziono postaci' in s.messages[-1]; checks+=1
    db.conn.execute("UPDATE quests SET progress=-6 WHERE account_id=2 AND quest_id='temple_rats'")
    db.conn.execute("INSERT INTO quests VALUES(2,'missing_fake_quest','active',0,0,0)")
    db.conn.execute("INSERT INTO quests VALUES(2,'bandit_patrol','strange',1,0,-2)")
    await s.admin_command('blad skan Friend')
    assert '3 wymagajacych sprawdzenia' in s.messages[-5]; checks+=1
    assert any('UJEMNY POSTEP' in x for x in s.messages[-5:]); checks+=1
    assert any('NIE MA ID' in x for x in s.messages[-5:]); checks+=1
    assert any('NIETYPOWY STATUS' in x for x in s.messages[-5:]); checks+=1
    assert any('UJEMNA LICZBA UKONCZEN' in x for x in s.messages[-5:]); checks+=1
    await s.admin_command('blad skan Friend 1')
    assert 'Pokazuje do 1' in s.messages[-4]; checks+=1
    assert 'Wiecej wpisow' in s.messages[-2]; checks+=1
    await s.admin_command('blad trop Friend temple_rats')
    assert any('BLAD DANYCH' in x for x in s.messages[-9:]); checks+=1
    await s.admin_command('blad trop Friend soul_shards')
    assert any('w plecaku 7' in x for x in s.messages[-9:]); checks+=1
    await s.admin_command('blad trop Friend fisher_30_fish')
    assert any('stan plecaka nie jest dowodem' in x for x in s.messages[-9:]); checks+=1
    # Simulate a recorded error: trace is still read-only.
    db.conn.execute("INSERT INTO admin_errors_v1224(id,exception,file,line,subsystem,handler) VALUES('SB-CCCC0001','ValueError','player/quests.py',15,'quest','quest')")
    await s.admin_command('blad diagnoza 1')
    assert 'Obszar QUEST' in s.messages[-1]; checks+=1
    assert db.quest(2,'temple_rats')['progress']==-6; checks+=1
    assert not db.logged; checks+=1
    assert s.server.live_content_v1204.draft==baseline; checks+=1
    # Ordinary player cannot reach admin blad, including the new read-only branches.
    player=Fake(False,db)
    await player.admin_command('blad trop Friend temple_rats')
    assert 'Nieznana komenda' in player.messages[-1];checks+=1
    return checks

def run():
    ADMIN_ACCOUNT_NAMES.add('owner')
    try: return asyncio.run(_suite())
    finally: ADMIN_ACCOUNT_NAMES.discard('owner')

if __name__=='__main__':
    print('V36.00.2 QUEST EVIDENCE:',run(),'checks PASS')
