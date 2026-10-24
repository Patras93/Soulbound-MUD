# -*- coding: utf-8 -*-
"""v60 regression: typed item/target corrections, DRAFT-only isolation."""
import asyncio
import copy
import random
from data.items import ITEMS
from data.mobs import MOB_TEMPLATES
from systems.admin_live_integrity_v4900 import _effective
from systems.admin_live_quest_id_v6000 import (
    HELP, find_quest_ids, quest_id_card, plan_quest_id_change,
    commit_quest_id_change, undo_quest_id_change,
)
from validation.v3600_admin_guardian2 import Fake

async def _cmd(s, cmd):
    await s.admin_command('live '+cmd)
    return s.messages[-1]

async def suite():
    owner=Fake();guest=Fake(False,owner.server.db)
    service=owner.server.live_content_v1204
    initial_active=copy.deepcopy(service.active)
    initial_draft=copy.deepcopy(service.draft)
    rng=random.getstate();items=set(ITEMS);mobs=set(MOB_TEMPLATES)
    count=0
    def ck(ok,msg=''):
        nonlocal count
        assert ok,msg
        count+=1
    try:
        catalog=_effective(service)
        ck(len(catalog)>=100)
        quest='temple_rats';old='healing_potion';new='greater_healing_potion'
        ck(quest in catalog)
        ck(catalog[quest]['reward_items'][old]==1)
        ck(old in ITEMS and new in ITEMS)
        ck('nagrody EQ' in quest_id_card(service,quest))
        ck('healing_potion' in quest_id_card(service,quest))
        ck('trafienia' in find_quest_ids(service,'nagroda',old))
        ck('strona' in find_quest_ids(service,'nagroda',old))
        ck('Brak trafien' in find_quest_ids(service,'nagroda','item_missing_xyz'))
        ck('temple_rats' in find_quest_ids(service,'cel','temple_rat'))
        ck('POMOC 15' in HELP)
        for invalid in ('','?', 'a'*101,'\n','a b'):
            for fun,args in ((quest_id_card,(service,invalid)),(find_quest_ids,(service,'nagroda',invalid))):
                try:fun(*args)
                except ValueError:ck(True)
                else:ck(False,'invalid id accepted')
        for invalid in ('0','-1','ABC','999999999999999999999'):
            try:find_quest_ids(service,'nagroda',old,invalid)
            except ValueError:ck(True)
            else:ck(False,'invalid page accepted')
        for invalid in ('kill','objectives','resource',''):
            try:find_quest_ids(service,invalid,old)
            except ValueError:ck(True)
            else:ck(False,'invalid mode accepted')
        ck('PLAN:' in plan_quest_id_change(owner,service,'nagroda',old,new,[quest]))
        ck(service.active==initial_active and service.draft==initial_draft)
        ck('gotowy' in await _cmd(owner,'questy id status'))
        ck('DRAFT:' in commit_quest_id_change(owner,service))
        ck(service.active==initial_active)
        ck(service.draft['quest_edits'][quest]['reward_items']=={new:1})
        ck('COFNIETO' in undo_quest_id_change(owner,service))
        ck(service.draft==initial_draft)
        ck(service.active==initial_active)
        try:undo_quest_id_change(owner,service)
        except ValueError:ck(True)
        else:ck(False,'double undo')
        try:commit_quest_id_change(owner,service)
        except ValueError:ck(True)
        else:ck(False,'double commit')
        # Multi-quest atomic rewrites, all amounts preserved.
        selected=['temple_rats','goblin_problem','bandit_patrol']
        ck(all(old in catalog[x].get('reward_items',{}) for x in selected))
        ck('3 questow' in plan_quest_id_change(owner,service,'nagroda',old,new,selected))
        ck('DRAFT' in commit_quest_id_change(owner,service))
        for qid in selected:
            ck(service.draft['quest_edits'][qid]['reward_items'][new]==catalog[qid]['reward_items'][old])
            ck(old not in service.draft['quest_edits'][qid]['reward_items'])
        ck('COFNIETO' in undo_quest_id_change(owner,service))
        ck(service.draft==initial_draft)
        # 'target' is restricted to actual simple kill/collect authored targets.
        ck('PLAN' in plan_quest_id_change(owner,service,'cel','temple_rat','goblin',['temple_rats']))
        ck('DRAFT' in commit_quest_id_change(owner,service))
        ck(service.draft['quest_edits']['temple_rats']['target']=='goblin')
        ck('COFNIETO' in undo_quest_id_change(owner,service))
        ck(service.draft==initial_draft)
        ck('PLAN' in plan_quest_id_change(owner,service,'cel','soul_shard','iron_ore',['soul_shards']))
        ck('DRAFT' in commit_quest_id_change(owner,service))
        ck(service.draft['quest_edits']['soul_shards']['target']=='iron_ore')
        ck('COFNIETO' in undo_quest_id_change(owner,service))
        ck(service.draft==initial_draft)
        # Invalid/duplicate/unknown targets cannot trigger any mutation.
        for kwargs in [
            ('nagroda',old,old,[quest]),
            ('nagroda',old,'invalid_item_v6000',[quest]),
            ('cel','temple_rat','invalid_mob_v6000',['temple_rats']),
            ('cel','temple_rat','iron_ore',['temple_rats']),
            ('nagroda',old,new,['invalid_quest_v6000']),
            ('nagroda',old,new,[quest,quest]),
            ('nagroda',old,new,[quest]*9),
            ('cel','temple_rat','goblin',['soul_shards']),
            ('skill',old,new,[quest]),
        ]:
            try:plan_quest_id_change(owner,service,*kwargs)
            except ValueError:ck(True)
            else:ck(False,'invalid plan accepted: '+repr(kwargs))
            ck(service.active==initial_active and service.draft==initial_draft)
        # Caller must narrow broad changes to max eight IDs.
        try:plan_quest_id_change(owner,service,'nagroda',old,new)
        except ValueError as exc:ck('maksymalnie 8' in str(exc))
        else:ck(False,'mass replacement accepted')
        ck('PLAN' in plan_quest_id_change(owner,service,'nagroda',old,new,[quest]))
        service.draft=copy.deepcopy(initial_draft)
        service.draft.setdefault('quest_edits',{})['unrelated_v6000']={'needed':1}
        try:commit_quest_id_change(owner,service)
        except ValueError:ck(True)
        else:ck(False,'concurrent DRAFT edit overwritten')
        service.draft=copy.deepcopy(initial_draft)
        ck('PLAN' in plan_quest_id_change(owner,service,'nagroda',old,new,[quest]))
        ck('DRAFT' in commit_quest_id_change(owner,service))
        service.draft.setdefault('quest_edits',{})['unrelated_v6000']={'needed':2}
        try:undo_quest_id_change(owner,service)
        except ValueError:ck(True)
        else:ck(False,'concurrent DRAFT undo allowed')
        service.draft=copy.deepcopy(initial_draft)
        ck('anulowany' in await _cmd(owner,'questy id anuluj'))
        ck('PLAN:' in await _cmd(owner,'questy id plan nagroda healing_potion greater_healing_potion temple_rats'))
        ck('DRAFT' in await _cmd(owner,'questy id zatwierdz POTWIERDZAM'))
        ck('COFNIETO' in await _cmd(owner,'questy id cofnij POTWIERDZAM'))
        ck('POMOC 15' in await _cmd(owner,'pomoc 15'))
        ck('QUEST ID KARTA' in await _cmd(owner,'questy id karta temple_rats'))
        ck('QUEST ID ZNAJDZ' in await _cmd(owner,'questy id znajdz nagroda healing_potion'))
        ck('QUEST ID STATUS' in await _cmd(owner,'questy id status'))
        for cmd in ['questy id plan nagroda healing_potion undefined temple_rats',
                    'questy id zatwierdz', 'questy id unknown', 'questy id karta unknown_v6000']:
            ck('ADMIN LIVE ID' in await _cmd(owner,cmd))
        for cmd in ['pomoc 15','questy id karta temple_rats',
                    'questy id znajdz nagroda healing_potion',
                    'questy id plan nagroda healing_potion greater_healing_potion temple_rats',
                    'questy id zatwierdz POTWIERDZAM']:
            ck('Nieznana komenda' in await _cmd(guest,cmd))
        ck(random.getstate()==rng,'RNG touched')
        ck(set(ITEMS)==items and set(MOB_TEMPLATES)==mobs)
        ck(service.active==initial_active and service.draft==initial_draft)
        return count
    finally:
        service.draft=copy.deepcopy(initial_draft)
        service.active=copy.deepcopy(initial_active)

def run():
    n=asyncio.run(suite())
    print(f'V60 QUEST ID DRAFT REPAIRS: {n} PASS')
    return n

if __name__=='__main__':run()
