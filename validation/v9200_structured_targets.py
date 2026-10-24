# -*- coding: utf-8 -*-
"""Test authored multi-objective and resource-set quests in the real OLC schema."""
import asyncio
import copy
from types import SimpleNamespace
from systems.live_content_v1204 import LiveContentV1204
from systems.admin_live_integrity_v4900 import _effective
from validation.v3600_admin_guardian2 import Fake

async def run():
    n=0
    def ok(value,label):
        nonlocal n
        assert value,label
        n+=1
    user=Fake()
    db=user.server.db
    service=LiveContentV1204(SimpleNamespace(conn=db.conn))
    user.server.live_content_v1204=service
    async def command(text):
        await user.admin_command('live '+text)
        return user.messages[-1]
    try:
        # Two new quests, one with 3 objective kinds, one with real resources.
        service.draft['quests']['live_multi92']={
            'name':'Test trzech celow', 'giver':'Kapłan Elor', 'kind':'multi_objective',
            'target':'temple_rat','needed':4,'description':'Test izolowany',
            'reward_silver':1,'objectives':{'kill':{'temple_rat':2},
                      'collect':{'healing_potion':1},'talk':['priest_elor']},
        }
        service.draft['quests']['live_resource92']={
            'name':'Zestaw testowy','giver':'Kapłan Elor','kind':'collect_resource_set',
            'target':'nettle','needed':5,'description':'Test izolowany',
            'reward_silver':1,'resource_targets':{'nettle':2,'mint':3},
        }
        service.validate(service.draft)
        ok(True,'baseline OLC')
        previous=copy.deepcopy(service.draft)
        # Test isolated helper with explicit destination catalogs, all paths validated.
        from systems.admin_live_v9200 import _patch,_apply_patch
        from systems.admin_live_quest_refs_v6100 import _names
        names=_names(service)
        candidate=copy.deepcopy(previous)
        local=copy.deepcopy(_effective(service))
        for mode,old,new,qid in (
            ('kill','temple_rat','goblin','live_multi92'),
            ('collect','healing_potion','soul_elixir','live_multi92'),
            ('talk','priest_elor','miner_toren','live_multi92'),
            ('surowiec','nettle','chamomile','live_resource92'),
        ):
            patch=_patch(local[qid],mode,old,new,names)
            _apply_patch(candidate,qid,patch)
            local[qid].update(patch)
            ok(bool(patch),f'patch {mode}')
        service.validate(candidate)
        ok(candidate['quests']['live_multi92']['objectives'] == {
            'kill':{'goblin':2},'collect':{'soul_elixir':1},'talk':['miner_toren']},
            'retains 3 objectives')
        ok(candidate['quests']['live_multi92']['needed']==4,'total unchanged')
        ok(candidate['quests']['live_resource92']['resource_targets'] == {
           'chamomile':2,'mint':3},'resource mapping')
        ok(candidate['quests']['live_resource92']['target']=='chamomile','resource top-level target')
        ok(candidate['quests']['live_resource92']['needed']==5,'resource quantity unchanged')
        ok(service.draft==previous,'read-only preparation')
        # An active quest in the same set cannot be remapped by standard planner.
        result=await command('questy cele znajdz talk priest_elor')
        ok('live_multi92' in result,'find talk exact')
        # A real persisted active quest blocks editing the accepted objectives.
        db.conn.execute("INSERT INTO quests VALUES(2,'live_multi92','active',0,0,0)")
        ok('graczy' in (await command('questy cele plan talk priest_elor | miner_toren')).lower(),
           'active objective changes blocked')
        db.conn.execute("DELETE FROM quests WHERE quest_id='live_multi92'")
        ok(db.conn.execute('SELECT COUNT(*) FROM quests').fetchone()[0]==0,'no progress modified')
        ok(service.draft==previous,'blocked plan preserved DRAFT')
        package=('questy cele plan kill temple_rat | goblin; collect healing_potion | soul_elixir; '
                 'talk priest_elor | miner_toren; surowiec nettle | chamomile')
        ok('QUEST CELE PLAN' in await command(package),'four-mode integrated plan')
        ok(service.draft==previous,'integrated plan no DRAFT write')
        ok('zatwierdzono' in await command('questy cele zatwierdz POTWIERDZAM'),'integrated commit')
        merged=_effective(service)
        ok(merged['live_multi92']['objectives']==candidate['quests']['live_multi92']['objectives'],
           'all mixed objectives committed')
        ok(merged['live_resource92']['resource_targets']==candidate['quests']['live_resource92']['resource_targets'],
           'resource changes committed')
        ok(merged['live_resource92']['target']=='chamomile','resource target committed')
        ok('Cofnieto' in await command('questy cele cofnij POTWIERDZAM'),'integrated undo')
        ok(service.draft==previous,'integrated exact undo')
        print(f'V92 STRUCTURED TARGETS: {n} PASS',flush=True)
    finally: db.conn.close()
if __name__=='__main__':asyncio.run(run())
