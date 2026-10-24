# -*- coding: utf-8 -*-
"""v55 real craft EQ progression, persisted-ID rebuild and Admin Live access."""
import asyncio
import copy
import random
from pathlib import Path
from systems.endless_crafting_v5500 import craft_stage_v5500,endless_crafted_equipment_v5500
from systems.infinite_equipment import (
    parse_infinite_equipment_variant,ensure_infinite_equipment_variant,
    refresh_infinite_equipment_requirements_v5300,
    infinite_equipment_power_multiplier,
)
from systems.crafting_quality import register_crafting_quality_variant_v03054
from core import live_level_caps_v5200 as caps
from data.items import ITEMS
from validation.v3600_admin_guardian2 import Fake


async def suite():
    n=0
    def check(condition,label=''):
        nonlocal n
        assert condition,label
        n+=1
    stored=dict(caps.current())
    old_ids=set(ITEMS)
    rng=random.getstate()
    owner=Fake()
    guest=Fake(False,owner.server.db)
    before_db=list(owner.server.db.conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"))
    try:
        caps._state.update(dict(stored,eq=2000,bieglosc=2000))
        check(craft_stage_v5500(800,2000) is None)
        check(craft_stage_v5500(2000,800) is None)
        check(craft_stage_v5500(801,801)==810)
        check(craft_stage_v5500(850,830)==830)
        check(craft_stage_v5500(930,1000)==930)
        check(craft_stage_v5500(1000,930)==930)
        check(craft_stage_v5500(2001,2001)==2000)
        for left,right in ((0,900),(900,0),(-1,1000),('foo',1000),(1000,'foo'),(None,1000)):
            check(craft_stage_v5500(left,right) is None)
        caps._state['eq']=800
        check(craft_stage_v5500(950,950) is None)
        caps._state['eq']=None
        check(craft_stage_v5500(1000,920)==920)
        caps._state['eq']=2000
        check(endless_crafted_equipment_v5500('soul_shard',1000,1000)=='soul_shard')
        base='leather_vest'
        check(endless_crafted_equipment_v5500(base,800,800)==base)
        crafted=register_crafting_quality_variant_v03054(base,'masterwork','strength',100)
        check(crafted.startswith('craftq_masterwork_strength_a'))
        check(endless_crafted_equipment_v5500(crafted,800,950)==crafted)
        final=endless_crafted_equipment_v5500(crafted,1000,930)
        check(final.startswith('deepq_forge_e_r33_craftq_masterwork_strength_a'))
        check(final in ITEMS)
        desc=ITEMS[final]
        check(desc['source_progression_stage']==930)
        check(desc['required_mastery']==930)
        check(desc['infinite_depth_source']=='forge')
        check(desc['craft_quality_v03054']=='masterwork')
        check(desc['craft_critical_v03054'] is True)
        check(desc['craft_critical_affix_v03054']=='strength')
        check(desc['craft_critical_affix_amount_v03054']>0)
        check(desc['defense']>=ITEMS[crafted]['defense'])
        check(desc['stats']['strength']>=ITEMS[crafted]['stats']['strength'])
        check('Biegłość 930' in desc['desc'])
        check('Rzemioslo Mistrzow' in desc['name'] or 'Rezonans Głębi' in desc['name'])
        check(desc['mastery_requirement_scope']=='active_class')
        check(endless_crafted_equipment_v5500(crafted,1000,930)==final)
        check(parse_infinite_equipment_variant(final)['base_id']==crafted)
        check(infinite_equipment_power_multiplier(34,'e')>infinite_equipment_power_multiplier(33,'e'))
        # An inventory may contain ONLY deepq_forge_... without separate craftq.
        ITEMS.pop(final)
        ITEMS.pop(crafted)
        recovered=ensure_infinite_equipment_variant(final)
        check(recovered is not None)
        check(recovered['required_mastery']==930)
        check(recovered['craft_critical_affix_amount_v03054']==desc['craft_critical_affix_amount_v03054'])
        check(recovered['defense']==desc['defense'])
        # Reducing caps cannot lower an already authored Forge equip gate.
        caps._state['eq']=800
        caps._state['bieglosc']=800
        refresh_infinite_equipment_requirements_v5300()
        check(ITEMS[final]['required_mastery']==930)
        check('Biegłość 930' in ITEMS[final]['desc'])
        ITEMS.pop(final)
        check(ensure_infinite_equipment_variant(final)['required_mastery']==930)
        # Keep v53 historical Rezonans IDs readable with the additional source.
        parsed=parse_infinite_equipment_variant('deepq_crypt_r_r31_leather_vest')
        check(parsed['source']=='crypt' and parsed['effective_stage']==910)
        check(parse_infinite_equipment_variant('deepq_invalid_r_r31_leather_vest') is None)
        # User command read-only with owner permission and bounded values.
        caps._state.update(dict(stored,eq=2000,bieglosc=2000))
        async def run(cmd,session=owner):
            await session.admin_command('live '+cmd)
            return session.messages[-1]
        check('POMOC 10' in await run('pomoc 10'))
        check('REZONANS' in (await run('eq craft 1000 930')).upper())
        check('etap 930' in await run('eq craft 1000 930'))
        check('mistrzowski x' in await run('eq craft 1000 930'))
        check('Bez Rezonansu' in await run('eq craft 1000 800'))
        check('POMOC 10' in await run('eq craft pomoc'))
        check('ADMIN LIVE EQ:' in await run('eq craft -1 900'))
        check('ADMIN LIVE EQ:' in await run('eq craft 900 abc'))
        check('ADMIN LIVE EQ:' in await run('eq craft'))
        check('Nieznana komenda' in await run('pomoc 10',guest))
        check('Nieznana komenda' in await run('eq craft 900 900',guest))
        check('Nieznana komenda' in await run('eq craft pomoc',guest))
        check(caps.current()['eq']==2000)
        check(random.getstate()==rng)
        check(before_db==list(owner.server.db.conn.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")))
        # Gameplay crafting really calls the function BEFORE handing over EQ.
        crafting_file=(Path(__file__).resolve().parents[1]/'player/session_mixins/crafting.py').read_text('utf8')
        check(crafting_file.index('endless_crafted_equipment_v5500(')<crafting_file.index('self.server.db.add_item(\n                self.account_id, crafted_output_id, total_quantity'))
        check('REZONANS RZEMIOSLA:' in crafting_file)
        return n
    finally:
        caps._state.update(stored)
        for item in set(ITEMS)-old_ids:
            ITEMS.pop(item,None)


def run():
    result=asyncio.run(suite())
    print(f'V55 ENDLESS CRAFTING: {result} PASS')
    return result

if __name__=='__main__':run()
