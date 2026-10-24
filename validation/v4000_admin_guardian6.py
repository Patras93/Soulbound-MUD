# -*- coding: utf-8 -*-
"""Guardian 6 tests: owner gate, read-only diagnostics, atomic OLC draft, fallback."""
import asyncio
import copy
import sqlite3
import tempfile
from pathlib import Path
from types import SimpleNamespace
from validation.v3600_admin_guardian2 import Fake
from data.quests import QUESTS
from systems.live_content_v1204 import LiveContentV1204
from systems.live_quest_olc_v1209 import STAT_XP_FIELDS_V3900
from systems.admin_guardian6_v4000 import (
    _batch,_dependencies,_quest_audit,_reward_catalog,_suggestion,_preflight,
    _region_access,_arena_analysis,handle_guardian6)

async def suite():
    n=0
    qid='bandit_patrol'; base=copy.deepcopy(QUESTS[qid]); account=Fake();ownerdb=account.server.db
    stranger=Fake(False,ownerdb)
    await stranger.admin_command('guardian6 pomoc')
    assert 'tylko wlasciciel' in stranger.messages[-1] and not ownerdb.logged;n+=1
    with tempfile.TemporaryDirectory() as folder:
        db=sqlite3.connect(str(Path(folder)/'tests.db'));db.row_factory=sqlite3.Row
        db.execute('CREATE TABLE quests(account_id INTEGER,quest_id TEXT,status TEXT,progress INT,PRIMARY KEY(account_id,quest_id))')
        db.execute("INSERT INTO quests VALUES(1, 'bandit_patrol', 'active', 5)");db.commit()
        svc=LiveContentV1204(SimpleNamespace(conn=db))
        account.server.live_content_v1204=svc
        async def run(arg):
            await account.admin_command('guardian6 '+arg)
            return account.messages[-1]
        assert 'GUARDIAN6' in await run('pomoc');n+=1
        assert 'v40' in await run('status');n+=1
        assert 'bandit_patrol' in await run('nagrody katalog bandit');n+=1
        assert 'bandit_patrol' in await run('questy audyt bandit_patrol');n+=1
        assert 'QUEST ZALEZNOSCI' in await run('questy zaleznosci bandit_patrol');n+=1
        assert 'QUEST PROPOZYCJA' in await run('questy propozycja bandit_patrol');n+=1
        assert 'OLC PREFLIGHT' in await run('olc preflight');n+=1
        assert 'brak questow' in await run('nagrody katalog qwertyuiopnnnn');n+=1
        snap=copy.deepcopy(svc.draft)
        arguments='bandit_patrol | 10000 | 100000 | 20000 | auto | 40000 | 0 | 60000'
        assert 'PLAN BEZ ZMIAN' in await run('nagrody plan '+arguments);n+=1
        assert svc.draft==snap and QUESTS[qid]==base;n+=1
        assert 'Wymagane POTWIERDZAM' in await run('nagrody zestaw '+arguments);n+=1
        assert svc.draft==snap;n+=1
        assert 'DRAFT USTAWIONY' in await run('nagrody zestaw '+arguments+' | POTWIERDZAM');n+=1
        entry=svc.draft['quest_edits'][qid]
        assert entry['olc_reward_stat_xp']==10000;n+=1
        assert entry['olc_reward_stat_strength']==100000 and entry['olc_reward_stat_dexterity']==20000;n+=1
        assert 'olc_reward_stat_constitution' not in entry;n+=1
        assert entry['olc_reward_stat_willpower']==0;n+=1
        assert QUESTS[qid]==base and svc.active['quest_edits']=={};n+=1
        assert db.execute('SELECT progress FROM quests').fetchone()[0]==5;n+=1
        saved=copy.deepcopy(svc.draft)
        assert 'wymagana liczba' in (await run('nagrody zestaw bandit_patrol | 1 | -2 | 1 | 1 | 1 | 1 | 1 | POTWIERDZAM')).lower() or 'zakres' in account.messages[-1].lower();n+=1
        assert svc.draft==saved;n+=1
        assert 'GUARDIAN6' in await run('nagrody plan bandit_patrol | 1 | 2');n+=1
        assert svc.draft==saved;n+=1
        # All AUTO removes overrides without disturbing base rewards or completion history.
        all_auto='bandit_patrol | auto | auto | auto | auto | auto | auto | auto'
        assert 'DRAFT USTAWIONY' in await run('nagrody zestaw '+all_auto+' | POTWIERDZAM');n+=1
        assert qid not in svc.draft['quest_edits'] and QUESTS[qid]==base;n+=1
        assert db.execute('SELECT progress FROM quests').fetchone()[0]==5;n+=1
        assert 'QUEST DRAFT' in await run('questy popraw bandit_patrol needed 2 POTWIERDZAM');n+=1
        assert svc.draft['quest_edits'][qid]['needed']==2;n+=1
        before=copy.deepcopy(svc.draft)
        assert 'GUARDIAN6' in await run('questy popraw bandit_patrol needed 0 POTWIERDZAM');n+=1
        assert svc.draft==before;n+=1
        assert 'GUARDIAN6' in await run('questy popraw bandit_patrol needed 3');n+=1
        assert svc.draft==before;n+=1
        # Detect missing prerequisites and cycles without changing published catalog.
        svc.draft['quests']['live_testquesta']={'name':'Test A','kind':'kill','target':'bandit','needed':1,'requires_quest':'live_testquestb'}
        svc.draft['quests']['live_testquestb']={'name':'Test B','kind':'kill','target':'bandit','needed':1,'requires_quest':'live_testquesta'}
        assert 'cykle 1' in _dependencies(svc,'live_testquesta');n+=1
        assert 'z sygnalami' in _quest_audit(svc,'live_testquesta',1);n+=1
        assert svc.draft['quest_edits'][qid]['needed']==2;n+=1
        del svc.draft['quests']['live_testquesta'];del svc.draft['quests']['live_testquestb']
        assert 'OLC PREFLIGHT' in await run('olc preflight');n+=1
        assert db.execute('SELECT progress FROM quests').fetchone()[0]==5;n+=1
        # Use a separate isolated, valid kraina DRAFT with two rooms.
        svc.stage_room('live_testr_r01',30,'P1','Pokoj jeden','Test')
        svc.stage_room('live_testr_r02',30,'P2','Pokoj dwa','Test')
        assert 'odciete 1' in _region_access(svc,'testr');n+=1
        svc.stage_link('live_testr_r01','east','live_testr_r02')
        svc.stage_link('live_testr_r02','west','live_testr_r01')
        assert 'odciete 0' in _region_access(svc,'testr');n+=1
        assert 'OLC PREFLIGHT' in _preflight(svc);n+=1
        # Static boss analysis uses no combat instance, HP writes or XP grants.
        mob='bandit'
        if mob not in __import__('data.mobs',fromlist=['MOB_TEMPLATES']).MOB_TEMPLATES:
            mob=next(iter(__import__('data.mobs',fromlist=['MOB_TEMPLATES']).MOB_TEMPLATES))
        result=await run(f'arena analiza {mob} 999999 10000')
        assert 'NIE jest test rzeczywistego AI/UOSS' in result;n+=1
        assert account.server.world.mobs=={};n+=1
        assert db.execute('SELECT progress FROM quests').fetchone()[0]==5;n+=1
        assert QUESTS[qid]==base;n+=1
        db.close()
    return n


def run():return asyncio.run(suite())
if __name__=='__main__':print('GUARDIAN6 v40:',run(),'checks PASS')
