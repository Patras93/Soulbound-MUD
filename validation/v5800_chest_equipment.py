# -*- coding: utf-8 -*-
"""v58 test real chest gear reward and safe quest reward ID audit."""
import asyncio
import random
import copy
from pathlib import Path
from types import SimpleNamespace
from data.items import ITEMS
from systems.endless_chest_equipment_v5800 import (
    chest_equipment_profile_v5800, enhance_boss_chest_equipment_v5800,
    preview_chest_equipment_v5800, _BASE_ITEMS,
)
from systems.infinite_equipment import ensure_infinite_equipment_variant
from systems.admin_live_quest_items_v5800 import quest_item_audit_v5800
from validation.v3600_admin_guardian2 import Fake

class ControlledRng:
    def __init__(self,number=0.0):self.number=number;self.rolls=0;self.choices=0
    def random(self):self.rolls+=1;return self.number
    def choice(self,items):self.choices+=1;return items[0]

async def suite():
    count=0
    def ok(value,why=''):
        nonlocal count
        assert value,why
        count+=1
    owner=Fake()
    guest=Fake(False,owner.server.db)
    before_active=copy.deepcopy(owner.server.live_content_v1204.active)
    before_draft=copy.deepcopy(owner.server.live_content_v1204.draft)
    rng_before=random.getstate()
    root=Path(__file__).resolve().parents[1]
    initial_items=set(ITEMS)
    try:
        for kind,floor in [('crypt',901),('mythic_crypt',901),('astral',901),('mythic_astral',901)]:
            profile=chest_equipment_profile_v5800(kind,floor)
            ok(profile is not None,(kind,floor))
            ok(profile['profile']['effective_stage']>800)
            ok(profile['chance']==25)
            base={'gold':700,'items':['soul_shard','healing_potion'],'flag':'preserved'}
            rs=ControlledRng()
            new=enhance_boss_chest_equipment_v5800(kind,floor,base,rng=rs)
            ok(rs.rolls==1 and rs.choices==1)
            ok(new is not base)
            ok(new['gold']==base['gold'] and new['flag']=='preserved')
            ok(base['items']==['soul_shard','healing_potion'])
            ok(new['items'][:2]==base['items'])
            ok(len(new['items'])==3)
            ok(new['items'][-1].startswith('deepq_'))
            ok(new['items'][-1] in ITEMS)
            ok(ITEMS[new['items'][-1]]['required_mastery']>=600)
            # Self-describing item ID survives reboot-like deletion/rebuild.
            item=new['items'][-1]
            saved=copy.deepcopy(ITEMS[item]);del ITEMS[item]
            again=ensure_infinite_equipment_variant(item)
            ok(again is not None)
            ok(again['name']==saved['name'])
            ok(again['required_mastery']==saved['required_mastery'])
            rs=ControlledRng(.250001)
            unchanged=enhance_boss_chest_equipment_v5800(kind,floor,base,rng=rs)
            ok(unchanged is base)
            ok(rs.rolls==1 and rs.choices==0)
            ok('25%' in preview_chest_equipment_v5800(kind, floor))
        for kind,floor in [('crypt',100),('mythic_crypt',100),('astral',100),('mythic_astral',100),
                           ('uoss',900),('magitek',900),('giant',900),('crypt',0),('crypt',1000001)]:
            obj={'gold':11,'items':['healing_potion']};rng=ControlledRng()
            ok(enhance_boss_chest_equipment_v5800(kind,floor,obj,rng=rng) is obj,(kind,floor))
            ok(rng.rolls==0 and rng.choices==0)
        for original in (None,{},'not_a_reward',{'items':()}, {'items':None}):
            rng=ControlledRng()
            ok(enhance_boss_chest_equipment_v5800('crypt',901,original,rng=rng) is original)
            ok(rng.rolls==0)
        for base_id in _BASE_ITEMS:
            ok(base_id in ITEMS)
            ok(ITEMS[base_id]['type']=='armor')
            ok(not ITEMS[base_id].get('uoss_unique'))
        for bad in [('nieznany',901),('krypta',0),('krypta',1000001),('krypta','abc')]:
            try:preview_chest_equipment_v5800(*bad)
            except ValueError:ok(True)
            else:ok(False,str(bad))
        ok('ponizej' in preview_chest_equipment_v5800('krypta',100))
        # Quest audit: never auto-delete item IDs, read OLC-defined items too.
        svc=SimpleNamespace(
            active={'quest_edits':{},'items':{'olc_defined_item':{'name':'OC'}}},
            draft={'quest_edits':{},'items':{}},
        )
        # Use a test service with correct _combined() facade from real service;
        # patch its DRAFT temporarily and restore after test.
        live=owner.server.live_content_v1204
        qid=next(iter(__import__('systems.admin_live_integrity_v4900',fromlist=['_effective'])._effective(live)))
        fake=copy.deepcopy(live.draft)
        try:
            fake.setdefault('quest_edits',{}).setdefault(qid,{})['reward_items']={'invented_item_999':1}
            live.draft=fake
            report=quest_item_audit_v5800(live,qid)
            ok(qid in report)
            ok('nieznane ID invented_item_999' in report)
            ok('Nic nie usunieto' in report)
            ok('QUEST ITEMY' in quest_item_audit_v5800(live,'1'))
        finally:live.draft=copy.deepcopy(before_draft)
        async def cmd(raw, session=owner):
            await session.admin_command('live '+raw)
            return session.messages[-1]
        ok('POMOC 13' in await cmd('pomoc 13'))
        ok('25%' in await cmd('skrzynie eq krypta 901'))
        ok('25%' in await cmd('skrzynie eq wieza 901'))
        ok('POMOC 13' in await cmd('skrzynie eq'))
        ok('SKRZYNIA EQ:' in await cmd('skrzynie eq nieznany 901'))
        ok('QUEST ITEMY' in await cmd('questy itemy 1'))
        ok('Nieznana komenda' in await cmd('pomoc 13',guest))
        ok('Nieznana komenda' in await cmd('skrzynie eq krypta 901',guest))
        ok('Nieznana komenda' in await cmd('questy itemy 1',guest))
        ok(random.getstate()==rng_before, 'Global RNG changed by preview/tests')
        ok(owner.server.live_content_v1204.draft==before_draft)
        ok(owner.server.live_content_v1204.active==before_active)
        source=(root/'player/session_mixins/admin_tools.py').read_text('utf8')
        segment=source[source.index('            rewarded = []'):source.index('            if len(rewarded) > 1:',source.index('            rewarded = []'))]
        ok('reward = boss_chest_reward_roll(kind, floor, power)' in segment)
        ok('reward = extend_boss_chest_reward_v5700(kind, floor, reward)' in segment)
        ok('reward = enhance_boss_chest_equipment_v5800(kind, floor, reward)' in segment)
        ok(segment.index('boss_chest_reward_roll(kind') < segment.index('extend_boss_chest_reward_v5700(kind') < segment.index('enhance_boss_chest_equipment_v5800(kind') < segment.index('member.character.gold +='))
        ok('for member in recipients:' in segment)
        ok('for item_id in reward["items"]:' in segment)
        ok('self.server.db.add_item(member.account_id, item_id, 1)' in segment)
        ok('self.server.db.save_character(member.character)' in segment)
        ok('consumed_member_key' in segment)
        ok('boss_floor_chest_state_id(kind, floor)' in segment)
        return count
    finally:
        for key in set(ITEMS)-initial_items:
            ITEMS.pop(key,None)

def run():
    result=asyncio.run(suite())
    print(f'V58 EQ SKRZYNIE/QUESTY: {result} PASS')
    return result
if __name__=='__main__':run()
