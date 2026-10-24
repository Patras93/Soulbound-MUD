# -*- coding: utf-8 -*-
"""v59 normal world EQ, admin previews and safe OLC dependency patching."""
import asyncio,copy,random
from pathlib import Path
from data.items import ITEMS
from systems.infinite_equipment import ensure_infinite_equipment_variant,infinite_source_profile
from systems.endless_loot_v5600 import eligible_normal_equipment_drop_v5600, convert_normal_equipment_drop_v5600
from systems.admin_live_v5900 import world_equipment_preview, plan_replace_dependency,commit_replace_dependency,undo_replace_dependency
from systems.admin_live_integrity_v4900 import _effective
from validation.v3600_admin_guardian2 import Fake
from core import live_level_caps_v5200 as caps
from systems.live_quest_olc_v1209 import parse_quest_edit
from systems.live_content_v1204 import _integer,_live_level_bound_v5900

async def suite():
    owner=Fake();guest=Fake(False,owner.server.db)
    svc=owner.server.live_content_v1204
    start_active=copy.deepcopy(svc.active);start_draft=copy.deepcopy(svc.draft)
    start_items=set(ITEMS);rng=random.getstate();saved_caps=caps.current();checks=0
    def ok(value,why=''):
        nonlocal checks
        assert value,why
        checks+=1
    try:
        for level in (801,805,850,901,1000,3000):
            p=infinite_source_profile({'level':level})
            ok(p is not None,(level,p))
            ok(p['source']=='world')
            ok(p['effective_stage']>=level)
            text=world_equipment_preview(str(level),'leather_vest')
            ok('DROP EQ:' in text)
            ok('wymagana bieglosc' in text)
            ok('deepq_world_r_' in text)
        # Dynamic OLC ceilings: baseline 800, higher only if owner changes cap.
        for axis in ('postac','profesje','narzedzia'):caps._state[axis]=800
        for field in ('generator_level','min_profession_level','min_tool_level'):
            try:parse_quest_edit(field,'1200')
            except ValueError:ok(True)
            else:ok(False,'default OLC 800 must still apply')
        for axis in ('postac','profesje','narzedzia'):caps._state[axis]=2000
        for field in ('generator_level','min_profession_level','min_tool_level'):
            ok(parse_quest_edit(field,'1200')[1]==1200)
        ok(_integer(1200,1,_live_level_bound_v5900('postac'),'mob')==1200)
        caps._state['postac']=800
        try:_integer(1200,1,_live_level_bound_v5900('postac'),'mob')
        except ValueError:ok(True)
        else:ok(False,'room 800 baseline')
        caps._state.update(saved_caps)
        ok(infinite_source_profile({'generator_level':901})['source']=='world')
        ok(set(ITEMS)==start_items,'preview mutated items')
        for template in ({'level':800},{'level':0},{'level':'abc'}, {'level':True},{'level':1000000001}, {'level':901,'uoss_unique':True}, {'level':901,'uoss_superboss':True}, {'level':901,'uoss_superboss_id':'br'}):
            ok(not eligible_normal_equipment_drop_v5600('leather_vest',template),str(template))
        for item in ('soul_shard','healing_potion','unknown_v5900'):
            ok(not eligible_normal_equipment_drop_v5600(item,{'level':901}))
        for template in ({'crypt_floor':901,'level':1000},{'mythic_crypt_floor':901,'level':1000},{'astral_floor':901,'level':1000},{'magitek_floor':901,'level':1000}):
            ok(infinite_source_profile(template)['source']!='world')
        boss=convert_normal_equipment_drop_v5600('leather_vest',{'level':901,'boss':True})
        ordinary=convert_normal_equipment_drop_v5600('leather_vest',{'level':901})
        elite=convert_normal_equipment_drop_v5600('leather_vest',{'level':901,'elite':True})
        ok(boss.startswith('deepq_world_b_'))
        ok(ordinary.startswith('deepq_world_r_'))
        ok(elite.startswith('deepq_world_e_'))
        ok(ITEMS[boss]['defense']>=ITEMS[elite]['defense']>=ITEMS[ordinary]['defense'])
        ok(ITEMS[boss]['source_progression_stage']>=901)
        old=copy.deepcopy(ITEMS[boss]); ITEMS.pop(boss)
        rebuilt=ensure_infinite_equipment_variant(boss)
        ok(rebuilt is not None)
        ok(rebuilt['defense']==old['defense'])
        ok(rebuilt['required_mastery']==old['required_mastery'])
        ok(convert_normal_equipment_drop_v5600('leather_vest',{'level':901,'uoss_superboss':True})=='leather_vest')
        ok('DROP EQ' in world_equipment_preview('901','leather_vest','boss'))
        ok('Nie jest' not in world_equipment_preview('901','leather_vest','elite'))
        for invalid in ('0','-2','x','1000000001'):
            try:world_equipment_preview(invalid,'leather_vest')
            except ValueError:ok(True)
            else:ok(False,'invalid level')
        try:world_equipment_preview('901','leather_vest','admin')
        except ValueError:ok(True)
        else:ok(False,'unknown grade')
        # An actual quest with a simple authored prerequisite; prefer one without
        # existing mutable quest edit to avoid touching any real player state.
        catalog=_effective(svc)
        sources=[(qid,q.get('requires_quest')) for qid,q in catalog.items()
                 if isinstance(q.get('requires_quest'),str) and q['requires_quest'] in catalog and qid != q['requires_quest']]
        ok(bool(sources),'no quest dependency to test')
        qid,old_id=sources[0]
        new_id=next(x for x in catalog if x!=qid and x!=old_id and not catalog[x].get('requires_quest'))
        # New prerequisite cannot create a cycle; if it does, search a safer root.
        for candidate in catalog:
            if candidate in (qid,old_id):continue
            try:
                proposal=plan_replace_dependency(owner,svc,old_id,candidate,[qid]);new_id=candidate;break
            except ValueError:continue
        else:raise AssertionError('Cannot find valid ID replacement')
        ok('PLAN:' in proposal)
        ok(qid in proposal)
        ok(old_id in proposal and new_id in proposal)
        ok(svc.draft==start_draft)
        ok(svc.active==start_active)
        ok(getattr(owner,'adminlive59_plan',None) is not None)
        ok('gotowy' in (await _do(owner,'questy zamien status')))
        result=commit_replace_dependency(owner,svc)
        ok('DRAFT:' in result)
        ok(svc.draft!=start_draft)
        ok(svc.active==start_active)
        ok(svc.draft['quest_edits'][qid]['requires_quest']==new_id)
        ok('COFNIETO' in undo_replace_dependency(owner,svc))
        ok(svc.draft==start_draft)
        ok(svc.active==start_active)
        try:commit_replace_dependency(owner,svc)
        except ValueError:ok(True)
        else:ok(False,'double apply allowed')
        plan_replace_dependency(owner,svc,old_id,new_id,[qid])
        svc.draft=copy.deepcopy(svc.draft)
        svc.draft.setdefault('quest_edits',{})['fake_v5900']={'needed':1}
        try:commit_replace_dependency(owner,svc)
        except ValueError:ok(True)
        else:ok(False,'concurrent modification allowed')
        svc.draft=copy.deepcopy(start_draft)
        try:plan_replace_dependency(owner,svc,old_id,qid,[qid])
        except ValueError:ok(True)
        else:ok(False,'self-cycle allowed')
        try:plan_replace_dependency(owner,svc,old_id,'unknown_v5900',[qid])
        except ValueError:ok(True)
        else:ok(False,'unknown new ID allowed')
        try:plan_replace_dependency(owner,svc,old_id,new_id,['fake_v5900'])
        except ValueError:ok(True)
        else:ok(False,'non-matching quest allowed')
        # End-to-end admin live dispatch.
        ok('POMOC 14' in await _do(owner,'pomoc 14'))
        ok('deepq_world' in await _do(owner,'eq swiat 901 leather_vest boss'))
        ok('PLAN:' in await _do(owner,f'questy zamien plan {old_id} {new_id} {qid}'))
        ok('DRAFT:' in await _do(owner,'questy zamien zatwierdz POTWIERDZAM'))
        ok('COFNIETO' in await _do(owner,'questy zamien cofnij POTWIERDZAM'))
        for command in ('pomoc 14','eq swiat 901 leather_vest','questy zamien status'):
            ok('Nieznana komenda' in await _do(guest,command))
        ok(random.getstate()==rng,'global RNG touched')
        ok(svc.draft==start_draft and svc.active==start_active)
        root=Path(__file__).resolve().parents[1]
        rewards=(root/'player/session_mixins/combat_rewards.py').read_text('utf8')
        ok('convert_normal_equipment_drop_v5600(item_id, template)' in rewards)
        ok(rewards.index('if random.random() <= _effective_drop_chance_v11329:') < rewards.index('convert_normal_equipment_drop_v5600(item_id, template)'))
        ok('party_drop_recipients_v0359(item_id, recipients)' in rewards)
        return checks
    finally:
        caps._state.update(saved_caps)
        svc.draft=copy.deepcopy(start_draft);svc.active=copy.deepcopy(start_active)
        for added in set(ITEMS)-start_items:ITEMS.pop(added,None)

async def _do(session,command):
    await session.admin_command('live '+command)
    return session.messages[-1]

def run():
    count=asyncio.run(suite());print(f'V59 EQ SWIAT/ZAMIAN ZALEZNOSCI: {count} PASS');return count
if __name__=='__main__':run()
