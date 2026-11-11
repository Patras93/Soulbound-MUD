# -*- coding: utf-8 -*-
"""v62 regression: combined atomic DRAFT, quest gear grant and mastery over 800."""
from __future__ import annotations
import asyncio
import copy
import random
from pathlib import Path
from core import live_level_caps_v5200 as caps
from systems.live_content_v1204 import LiveContentV1204, blank
from systems.admin_live_bundle_v6200 import (
    plan_bundle,commit_bundle,undo_bundle,skill_unlock_audit,dispatch_v62,
)
from systems.quest_equipment_v6200 import (
    quest_gear_stage_v6200,quest_gear_profile_v6200,
    quest_equipment_id_v6200,preview_quest_equipment_v6200,
)
from systems.infinite_equipment import (
    ensure_infinite_equipment_variant,parse_infinite_equipment_variant,
    refresh_infinite_equipment_requirements_v5300,
)
from systems.admin_guardian11_v4500 import _class_set
from systems.admin_guardian10_v4400 import _lab_start10
from validation.v3600_admin_guardian2 import Fake
from data.items import ITEMS
from types import SimpleNamespace


def strict_service():
    obj=object.__new__(LiveContentV1204)
    obj.active=blank();obj.draft=blank()
    return obj


async def suite():
    n=0
    def ck(ok,why=''):
        nonlocal n
        assert ok,why
        n+=1
    owner=Fake();guest=Fake(False,owner.server.db)
    service=owner.server.live_content_v1204
    old_draft=copy.deepcopy(service.draft);old_active=copy.deepcopy(service.active)
    old_item_ids=set(ITEMS);old_caps=dict(caps.current())
    world_rng=random.getstate();db_changes=owner.server.db.conn.total_changes
    try:
        # High-level, explicitly authored quest reward only (not account level).
        q={'name':'Test quest', 'generator_level':931,'reward_items':{'leather_vest':2}}
        ck(quest_gear_stage_v6200(q)==931)
        ck(quest_gear_stage_v6200({'generator_level':800}) is None)
        ck(quest_gear_stage_v6200({'generator_level':True}) is None)
        ck(quest_gear_stage_v6200({'recommended_level':1000})==1000)
        ck(quest_gear_stage_v6200({'level':1001})==1001)
        ck(quest_gear_stage_v6200({'required_mastery':802})==802)
        ck(quest_gear_stage_v6200({'generator_level':'nan'}) is None)
        ck(quest_gear_stage_v6200({'generator_level':10**18}) is None)
        ck(quest_gear_stage_v6200({'generator_level':1500,'uoss_unique':True}) is None)
        ck(quest_gear_stage_v6200(None) is None)
        ck(quest_gear_profile_v6200('healing_potion',q) is None)
        ck(quest_gear_profile_v6200('missing_v62',q) is None)
        ck(quest_equipment_id_v6200('leather_vest',{'generator_level':800})=='leather_vest')
        ck(quest_equipment_id_v6200('healing_potion',q)=='healing_potion')
        ck(quest_equipment_id_v6200('soul_shard',q)=='soul_shard')
        ck('Tylko podglad' in preview_quest_equipment_v6200('leather_vest',q))
        ck('Bez zmian' in preview_quest_equipment_v6200('healing_potion',q))
        ck('bez zmian' in preview_quest_equipment_v6200('leather_vest',{}))
        ck(random.getstate()==world_rng)
        ck(set(ITEMS)==old_item_ids)  # preview must not register equipment
        caps._state.update(dict(old_caps,eq=2000,bieglosc=2000))
        item_id=quest_equipment_id_v6200('leather_vest',q)
        ck(item_id.startswith('deepq_quest_r_r34_leather_vest'))
        ck(item_id in ITEMS)
        ck(ITEMS[item_id]['infinite_depth_source']=='quest')
        ck(ITEMS[item_id]['required_mastery']==940)
        ck(ITEMS[item_id]['defense']>ITEMS['leather_vest']['defense'])
        ck(parse_infinite_equipment_variant(item_id)['source']=='quest')
        ck(quest_equipment_id_v6200(item_id,q)==item_id)
        saved=copy.deepcopy(ITEMS[item_id]);ITEMS.pop(item_id)
        ck(ensure_infinite_equipment_variant(item_id) is not None)
        ck(ITEMS[item_id]['defense']==saved['defense'])
        ck(ITEMS[item_id]['required_mastery']==saved['required_mastery'])
        caps._state['eq']=800;caps._state['bieglosc']=800
        ck(refresh_infinite_equipment_requirements_v5300()>=1)
        ck(ITEMS[item_id]['required_mastery']>=600)
        ck(parse_infinite_equipment_variant('deepq_quest_r_r0_leather_vest') is None)
        ck(parse_infinite_equipment_variant('deepq_invalid_r_r34_leather_vest') is None)
        # Existing high-level quest does NOT get equipment if there are no authored rewards.
        ck(quest_equipment_id_v6200('temple_rat',q)=='temple_rat')
        ck(ITEMS['leather_vest'].get('infinite_depth_variant') is None)
        # Full-world strict OLC validator, multiple distinct types in one atomic plan.
        live=strict_service();original=copy.deepcopy(live.draft)
        plan=('npc fisher_tomas miner_toren fisher_30_fish ; '
              'surowiec copper_ore gold_ore toren_ore_samples_v0929 ; '
              'nagroda healing_potion greater_healing_potion temple_rats')
        # An authored quest already has an item reward: do not invent a new quest.
        plan=plan.replace('temple_rats','temple_rats')
        original=copy.deepcopy(live.draft)
        ck('PLAN' in plan_bundle(owner,live,plan))
        ck(live.draft==original and live.active==blank())
        ck('3 operacji' in plan_bundle(owner,live,plan))
        ck('DRAFT' in commit_bundle(owner,live))
        patches=live.draft['quest_edits']
        ck(patches['fisher_30_fish']['giver']=='Górnik Toren')
        ck(patches['toren_ore_samples_v0929']['resource_targets']['gold_ore']==5)
        ck(patches['temple_rats']['reward_items']=={'greater_healing_potion':1})
        ck(live.active==blank())
        ck('COFNIETO' in undo_bundle(owner,live))
        ck(live.draft==original)
        # Mixed serial edits on the SAME quest use the latest effective state.
        qid='live_v62_multi_test'
        live.draft['quests'][qid]={
            'name':'Multi quest test','description':'Opis multi testu.','giver':'Rybak Borys','kind':'multi_objective',
            'target':'temple_rat','needed':6,
            'objectives':{'kill':{'temple_rat':2},'collect':{'iron_ore':3},'talk':['fisher_tomas']},
            'reward_silver':25,
        }
        live.validate(live.draft)
        original=copy.deepcopy(live.draft)
        mix=(f'kill temple_rat goblin {qid} ; collect iron_ore gold_ore {qid} ; '
             f'talk fisher_tomas miner_toren {qid}')
        ck('PLAN' in plan_bundle(owner,live,mix))
        ck('DRAFT' in commit_bundle(owner,live))
        patch=live.draft['quest_edits'][qid]
        ck(patch['objectives']=={'kill':{'goblin':2},'collect':{'gold_ore':3},'talk':['miner_toren']})
        ck(live.draft['quests'][qid]['needed']==6)
        ck('COFNIETO' in undo_bundle(owner,live))
        ck(live.draft==original)
        # Unknown references, duplicate or huge batches, and stale DRAFT must fail.
        for bad in ('', 'npc fisher_tomas miner_toren',
                    'npc fisher_tomas miner_toren missing_v62',
                    'npc fisher_tomas faker fisher_30_fish',
                    'other x y fisher_30_fish',
                    f'kill temple_rat gold_ore {qid}',
                    f'kill temple_rat goblin {qid} ; kill temple_rat goblin {qid}',
                    'npc fisher_tomas miner_toren fisher_30_fish ;',
                    'x'*(2701),
                    ' ; '.join('npc fisher_tomas miner_toren fisher_30_fish' for _ in range(17))):
            try:plan_bundle(owner,live,bad)
            except (ValueError,TypeError):ck(True)
            else:ck(False,'accepted invalid '+bad[:50])
            ck(live.draft==original)
        ck('PLAN' in plan_bundle(owner,live,mix))
        live.draft.setdefault('quest_edits',{})['v62_later_test']={'needed':1}
        try:commit_bundle(owner,live)
        except ValueError:ck(True)
        else:ck(False,'overwrote newer DRAFT')
        live.draft=copy.deepcopy(original)
        ck('PLAN' in plan_bundle(owner,live,mix))
        ck('DRAFT' in commit_bundle(owner,live))
        live.draft.setdefault('quest_edits',{})['v62_later_test']={'needed':1}
        try:undo_bundle(owner,live)
        except ValueError:ck(True)
        else:ck(False,'undid another editor')
        live.draft=copy.deepcopy(original)
        # Cap integration above 800 in existing UOSS model class selection.
        caps._state['bieglosc']=1800
        dummy=SimpleNamespace(guardian7_lab=None,guardian9_snapshot=None)
        _lab_start10(dummy,live,'black_rabite','1000000','20000')
        ck('900' in _class_set(dummy,'Wojownik','900','5000'))
        ck('Bieglo' in skill_unlock_audit('900') or 'POZIOM 900' in skill_unlock_audit('900'))
        ck('strona 2/3' in skill_unlock_audit('900','2'))
        ck('22 klas' in skill_unlock_audit('900'))
        for invalid in ('-1','a','99999999999'):
            try:skill_unlock_audit(invalid)
            except ValueError:ck(True)
            else:ck(False,'accepted mastery '+invalid)
        caps._state['bieglosc']=800
        try:_class_set(dummy,'Wojownik','801','5000')
        except ValueError:ck(True)
        else:ck(False,'mastery bypassed cap')
        # Command dispatch owner and guest through production admin live dispatcher.
        owner.server.live_content_v1204=live
        async def run(cmd,who=owner):
            await who.admin_command('live '+cmd)
            return who.messages[-1]
        for command,expect in (
            ('pomoc 17','POMOC 17'),('questy pakiet status','QUEST PAKIET'),
            ('questy pakiet plan '+mix,'PLAN'),
            ('questy pakiet zatwierdz POTWIERDZAM','DRAFT'),
            ('questy pakiet cofnij POTWIERDZAM','COFNIETO'),
            ('questy pakiet anuluj','anulowany'),
            ('eq quest temple_rats leather_vest','bez zmian'),
            ('arena skille poziom 800','22 klas'),
        ):
            ck(expect in await run(command),command)
        for command in ('pomoc 17','questy pakiet plan '+mix,
                        'questy pakiet zatwierdz POTWIERDZAM','eq quest temple_rats leather_vest',
                        'arena skille poziom 800'):
            ck('Nieznana komenda' in await run(command,guest))
        ck(owner.server.db.conn.total_changes==db_changes)
        ck(random.getstate()==world_rng)
        # Exact production reward path is connected, not a preview-only feature.
        path=Path(__file__).resolve().parents[1]
        real=(path/'player/session_mixins/quest_commands.py').read_text('utf8')
        ck(real.count('item_id = quest_equipment_id_v6200(item_id, q)')==2)
        ck(real.index('item_id = quest_equipment_id_v6200(item_id, q)')<real.index('self.server.db.add_item(self.account_id, item_id, qty)'))
        ck('quest' in (path/'systems/infinite_equipment.py').read_text('utf8'))
        return n
    finally:
        service.draft=old_draft;service.active=old_active
        caps._state.update(old_caps)
        for item_id in set(ITEMS)-old_item_ids:ITEMS.pop(item_id,None)


def run():
    count=asyncio.run(suite())
    print(f'V62 ADMIN LIVE BUNDLE QUEST EQUIPMENT: {count} PASS')
    return count

if __name__=='__main__':run()
