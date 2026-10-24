# -*- coding: utf-8 -*-
"""v61 Admin Live: owner-only NPC, resource and multi-objective DRAFT repairs."""
import asyncio
import copy
import random
from types import SimpleNamespace

from systems.live_content_v1204 import LiveContentV1204, blank
from systems.admin_live_quest_refs_v6100 import (
    HELP, MODES, find_refs, ref_card, plan_refs, commit_refs, undo_refs,
)
from systems.admin_live_integrity_v4900 import _effective
from validation.v3600_admin_guardian2 import Fake


def _strict_service():
    service=object.__new__(LiveContentV1204)
    service.active=blank()
    service.draft=blank()
    return service


async def _command(session, cmd):
    await session.admin_command('live '+cmd)
    return session.messages[-1]


async def suite():
    owner=Fake();guest=Fake(False,owner.server.db)
    service=owner.server.live_content_v1204
    snap_a=copy.deepcopy(service.active);snap_d=copy.deepcopy(service.draft)
    sql_before=owner.server.db.conn.total_changes
    rng=random.getstate()
    checks=0
    def ck(value, info=''):
        nonlocal checks
        assert value, info
        checks+=1
    try:
        ck('POMOC 16' in HELP)
        ck(len(MODES)==5)
        ck('NPC' in ref_card(service,'fisher_30_fish'))
        ck('surowce' in ref_card(service,'toren_ore_samples_v0929'))
        ck('fisher_30_fish' in find_refs(service,'npc','fisher_tomas'))
        ck('toren_ore_samples_v0929' in find_refs(service,'surowiec','copper_ore'))
        ck('brak' in find_refs(service,'surowiec','missing_resource_v61'))
        ck('strona 1/1' in find_refs(service,'npc','fisher_tomas'))
        for p in ('0','-1','word','99999999999999',' '):
            try:find_refs(service,'npc','fisher_tomas',p)
            except ValueError:ck(True)
            else:ck(False,'accepted page '+p)
        for invalid in ('','?','x '*50,'x'*101,'a\nb'):
            try:ref_card(service,invalid)
            except ValueError:ck(True)
            else:ck(False,'accepted malformed ID')
        for mode in ('other','', 'random'):
            try:find_refs(service,mode,'fisher_tomas')
            except ValueError:ck(True)
            else:ck(False,'accepted invalid mode')
        ck('PLAN' in plan_refs(owner,service,'npc','fisher_tomas','miner_toren',['fisher_30_fish']))
        ck(service.draft==snap_d and service.active==snap_a)
        ck('DRAFT' in commit_refs(owner,service))
        ck(service.draft['quest_edits']['fisher_30_fish']['giver']=='Górnik Toren')
        ck(service.active==snap_a)
        ck('COFNIETO' in undo_refs(owner,service))
        ck(service.draft==snap_d)
        ck('PLAN' in plan_refs(owner,service,'surowiec','copper_ore','gold_ore',['toren_ore_samples_v0929']))
        ck('DRAFT' in commit_refs(owner,service))
        q=service.draft['quest_edits']['toren_ore_samples_v0929']
        ck(q['resource_targets']=={'gold_ore':5,'iron_ore':5,'silver_ore':5})
        ck(q['target']=='gold_ore')
        ck(_effective(service)['toren_ore_samples_v0929']['target']=='gold_ore')
        ck('COFNIETO' in undo_refs(owner,service))
        ck(service.draft==snap_d)
        # Invalid inputs never mutate LIVE state, even if validation rejects later.
        cases=[
            ('npc','fisher_tomas','fisher_tomas',['fisher_30_fish']),
            ('npc','fisher_tomas','missing_npc_v61',['fisher_30_fish']),
            ('npc','missing_npc_v61','miner_toren',['fisher_30_fish']),
            ('npc','fisher_tomas','miner_toren',['temple_rats']),
            ('surowiec','copper_ore','unknown_item_v61',['toren_ore_samples_v0929']),
            ('surowiec','copper_ore','healing_potion',['toren_ore_samples_v0929']),
            ('surowiec','copper_ore','iron_ore',['toren_ore_samples_v0929']),
            ('surowiec','copper_ore','gold_ore',['temple_rats']),
            ('surowiec','copper_ore','gold_ore',['toren_ore_samples_v0929']*2),
            ('surowiec','copper_ore','gold_ore',['toren_ore_samples_v0929']*9),
            ('kill','temple_rat','unknown_mob_v61',['temple_rats']),
            ('talk','fisher_tomas','miner_toren',['fisher_30_fish']),
            ('invalid','fisher_tomas','miner_toren',['fisher_30_fish']),
        ]
        for case in cases:
            try:plan_refs(owner,service,*case)
            except ValueError:ck(True)
            else:ck(False,'invalid plan accepted '+repr(case))
            ck(service.active==snap_a and service.draft==snap_d)
        ck('PLAN' in plan_refs(owner,service,'npc','fisher_tomas','miner_toren',['fisher_30_fish']))
        service.draft.setdefault('quest_edits',{})['something_added']={'needed':2}
        try:commit_refs(owner,service)
        except ValueError:ck(True)
        else:ck(False,'lost concurrent draft edit')
        service.draft=copy.deepcopy(snap_d)
        ck('PLAN' in plan_refs(owner,service,'npc','fisher_tomas','miner_toren',['fisher_30_fish']))
        ck('DRAFT' in commit_refs(owner,service))
        service.draft.setdefault('quest_edits',{})['newer_edit']={'needed':4}
        try:undo_refs(owner,service)
        except ValueError:ck(True)
        else:ck(False,'undo overwrote a later edit')
        service.draft=copy.deepcopy(snap_d)
        for cmd, expected in (
            ('pomoc 16','POMOC 16'),
            ('questy ref karta fisher_30_fish','KARTA'),
            ('questy ref znajdz npc fisher_tomas','trafien'),
            ('questy ref status','QUEST REF'),
            ('questy ref plan npc fisher_tomas miner_toren fisher_30_fish','QUEST REF PLAN'),
            ('questy ref status','gotowy'),
            ('questy ref zatwierdz POTWIERDZAM','DRAFT'),
            ('questy ref cofnij POTWIERDZAM','COFNIETO'),
            ('questy ref plan surowiec copper_ore gold_ore toren_ore_samples_v0929','QUEST REF PLAN'),
            ('questy ref anuluj','anulowany'),
        ):
            ck(expected in await _command(owner,cmd),cmd)
        for cmd in ('questy ref plan npc x x fisher_30_fish',
                    'questy ref zatwierdz', 'questy ref cofnij',
                    'questy ref plan surowiec copper_ore fake toren_ore_samples_v0929',
                    'questy ref karta unknown_v61', 'questy ref abc'):
            ck('ADMIN LIVE REF' in await _command(owner,cmd),cmd)
        for cmd in ('pomoc 16','questy ref karta fisher_30_fish',
                    'questy ref plan npc fisher_tomas miner_toren fisher_30_fish',
                    'questy ref zatwierdz POTWIERDZAM'):
            ck('Nieznana komenda' in await _command(guest,cmd),cmd)
        ck(service.draft==snap_d and service.active==snap_a)
        # Real OLC validation, not merely the permissive legacy Fake validator.
        strict_resource=_strict_service()
        ck('PLAN' in plan_refs(owner,strict_resource,'surowiec','copper_ore','gold_ore',
                              ['toren_ore_samples_v0929']))
        ck('DRAFT' in commit_refs(owner,strict_resource))
        check_patch=strict_resource.draft['quest_edits']['toren_ore_samples_v0929']
        ck(check_patch['target']=='gold_ore')
        ck(sum(check_patch['resource_targets'].values())==15)
        strict_resource.validate(strict_resource.draft)
        ck('COFNIETO' in undo_refs(owner,strict_resource))
        ck(strict_resource.active==blank() and strict_resource.draft==blank())
        # Full authoritative OLC validation of synthetic, uninstalled multi-objective quests.
        real=_strict_service()
        qid='live_ref_test_v61'
        real.draft['quests'][qid]={
            'name':'Testowe cele','giver':'Rybak Borys','kind':'multi_objective',
            'target':'temple_rat','needed':6,
            'objectives':{'kill':{'temple_rat':2},'collect':{'iron_ore':3},'talk':['fisher_tomas']},
            'reward_silver':100, 'description':'Test celow wielocelowych bez zapisu.'}
        real.validate(real.draft)
        initial=copy.deepcopy(real.draft)
        ck('QUEST REF KARTA' in ref_card(real,qid))
        for mode,old,new in (('kill','temple_rat','goblin'),
                             ('collect','iron_ore','gold_ore'),('talk','fisher_tomas','miner_toren')):
            ck(qid in find_refs(real,mode,old))
            ck('PLAN' in plan_refs(owner,real,mode,old,new,[qid]))
            ck(real.draft==initial)
            ck('DRAFT' in commit_refs(owner,real))
            goal=real.draft['quest_edits'][qid]['objectives']
            ck(new in goal[mode] and old not in goal[mode])
            if mode!='talk':ck(sum(goal[mode].values())==(2 if mode=='kill' else 3))
            else:ck(goal[mode]==['miner_toren'])
            ck(real.draft['quests'][qid]['needed']==6)
            ck('COFNIETO' in undo_refs(owner,real))
            ck(real.draft==initial)
        for mode,old,new in (('kill','temple_rat','iron_ore'),('collect','iron_ore','temple_rat'),
                             ('talk','fisher_tomas','missing_npc_v61')):
            try:plan_refs(owner,real,mode,old,new,[qid])
            except ValueError:ck(True)
            else:ck(False,'accepted malformed objective '+mode)
        ck(real.draft==initial and real.active==blank())
        ck(random.getstate()==rng)
        ck(owner.server.db.conn.total_changes==sql_before)
        ck(not owner.server.db.logged)
        return checks
    finally:
        service.active=copy.deepcopy(snap_a)
        service.draft=copy.deepcopy(snap_d)


def run():
    n=asyncio.run(suite())
    print(f'V61 QUEST NPC RESOURCE OBJECTIVES DRAFT: {n} PASS')
    return n

if __name__=='__main__':run()
