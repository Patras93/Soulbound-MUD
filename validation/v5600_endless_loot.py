# -*- coding: utf-8 -*-
"""Focused v56 actual normal-drop branch, single party roll, persistent variants."""
import asyncio
import random
from pathlib import Path
from data.items import ITEMS
from core import live_level_caps_v5200 as caps
from systems.endless_loot_v5600 import (
    eligible_normal_equipment_drop_v5600,convert_normal_equipment_drop_v5600,
    preview_normal_equipment_drop_v5600,source_template_v5600,
)
from systems.infinite_equipment import ensure_infinite_equipment_variant
from validation.v3600_admin_guardian2 import Fake

async def suite():
    owner=Fake(); guest=Fake(False,owner.server.db)
    start_ids=set(ITEMS)
    original_caps=dict(caps.current())
    original_rng=random.getstate()
    checks=0
    def check(condition,reason=''):
        nonlocal checks
        assert condition,reason
        checks+=1
    try:
        template={'crypt_floor':901}
        preview=preview_normal_equipment_drop_v5600('leather_vest',template)
        check('etap 910' in preview)
        check('moc x' in preview)
        check('deepq_crypt_r_r31_leather_vest' in preview)
        check('leather_vest' in preview)
        check('szanse dropu' in preview.lower())
        check(set(ITEMS)==start_ids,'read-only preview mutated catalog')
        check(eligible_normal_equipment_drop_v5600('leather_vest',template))
        check(not eligible_normal_equipment_drop_v5600('soul_shard',template))
        check(not eligible_normal_equipment_drop_v5600('leather_vest',{'crypt_floor':600}))
        check(not eligible_normal_equipment_drop_v5600('leather_vest',{'crypt_floor':901,'uoss_superboss':True}))
        check(not eligible_normal_equipment_drop_v5600('unknown_v56',template))
        check(convert_normal_equipment_drop_v5600('soul_shard',template)=='soul_shard')
        check(convert_normal_equipment_drop_v5600('leather_vest',{'crypt_floor':600})=='leather_vest')
        check(convert_normal_equipment_drop_v5600('leather_vest',{'crypt_floor':901,'uoss_unique':True})=='leather_vest')
        check(convert_normal_equipment_drop_v5600('deepq_crypt_r_r31_leather_vest',template)=='deepq_crypt_r_r31_leather_vest')
        variant=convert_normal_equipment_drop_v5600('leather_vest',template)
        check(variant=='deepq_crypt_r_r31_leather_vest',variant)
        check(ITEMS[variant]['infinite_depth_variant'] is True)
        check(ITEMS[variant]['infinite_depth_source']=='crypt')
        check(ITEMS[variant]['source_progression_stage']==910)
        check(ITEMS[variant]['defense']>ITEMS['leather_vest']['defense'])
        check(convert_normal_equipment_drop_v5600('leather_vest',template)==variant)
        # Boss/elite grades only when the template says so; no random new rolls.
        boss=convert_normal_equipment_drop_v5600('leather_vest',{'crypt_floor':901,'crypt_boss':True})
        check(boss.startswith('deepq_crypt_b_r31_'))
        check(ITEMS[boss]['defense']>=ITEMS[variant]['defense'])
        elite=convert_normal_equipment_drop_v5600('leather_vest',{'astral_floor':910,'elite':True})
        check(elite.startswith('deepq_tower_e_'))
        # Five real sources supported by existing infinite gear system.
        cases=[('krypta',901,'crypt'),('mityczna_krypta',901,'mythiccrypt'),
               ('astral',910,'tower'),('mityczny_astral',901,'mythictower'),
               ('magitek',150,'magitek')]
        for kind,floor,source in cases:
            meta=source_template_v5600(kind,str(floor))
            check(isinstance(meta,dict))
            res=convert_normal_equipment_drop_v5600('leather_vest',meta)
            check(res.startswith('deepq_'+source+'_'),kind+' '+res)
            check('DROP EQ:' in preview_normal_equipment_drop_v5600('leather_vest',meta))
        for kind in ('bad','','uoss'):
            try:source_template_v5600(kind,'901')
            except ValueError:check(True)
            else:check(False,'unknown kind')
        for floor in ('-1','0','abc','1.4','99999999999'):
            try:source_template_v5600('krypta',floor)
            except ValueError:check(True)
            else:check(False,'invalid floor '+floor)
        check('Bez zmian' in preview_normal_equipment_drop_v5600('leather_vest',{'crypt_floor':100}))
        check('nie jest zwyklym EQ' in preview_normal_equipment_drop_v5600('soul_shard',template))
        # Persisted ID must rebuild without a stale runtime catalog entry.
        old=dict(ITEMS[variant]); ITEMS.pop(variant)
        rebuilt=ensure_infinite_equipment_variant(variant)
        check(rebuilt is not None)
        check(rebuilt['defense']==old['defense'])
        check(rebuilt['required_mastery']==old['required_mastery'])
        check(rebuilt['source_progression_stage']==910)
        check(random.getstate()==original_rng,'loot helper rolled RNG')
        # Owner-only, compact NVDA-friendly command.
        async def run(command,who=owner):
            await who.admin_command('live '+command)
            return who.messages[-1]
        check('POMOC 11' in await run('pomoc 11'))
        check('etap 910' in await run('eq drop krypta 901 leather_vest'))
        check('POMOC 11' in await run('eq drop pomoc'))
        check('ADMIN LIVE DROP:' in await run('eq drop invalid 901 leather_vest'))
        check('ADMIN LIVE DROP:' in await run('eq drop krypta nope leather_vest'))
        check('ADMIN LIVE DROP:' in await run('eq drop krypta'))
        check('Nieznana komenda' in await run('eq drop krypta 901 leather_vest',guest))
        check('Nieznana komenda' in await run('pomoc 11',guest))
        check(random.getstate()==original_rng,'admin preview rolled RNG')
        check(caps.current()==original_caps)
        # Assert actual post-roll, pre-recipient combat branch, not merely a stub.
        root=Path(__file__).resolve().parents[1]
        combat=(root/'player/session_mixins/combat_rewards.py').read_text('utf8')
        anchor=combat.index('_awarded_item_v5600 = convert_normal_equipment_drop_v5600')
        section=combat[anchor:combat.index('# v1.15.0:',anchor)]
        check('random.random()' not in section,'unexpected reroll')
        check('party_drop_recipients_v0359(item_id, recipients)' in section)
        check('add_item(winner.account_id, _awarded_item_v5600, 1)' in section)
        check('_awarded_item_v5600, source=template["name"], announce=True' in section)
        check('add_boss_codex_drop(\n                                    party_session.account_id, boss_id_for_drop, item_id' in section)
        check('loot_message_allowed(_awarded_item_v5600)' in section)
        check('for item_id, chance in template["drops"].items():' in combat)
        check(combat.index('if random.random() <= _effective_drop_chance_v11329:')<anchor)
        return checks
    finally:
        caps._state.update(original_caps)
        for added in set(ITEMS)-start_ids:
            ITEMS.pop(added,None)

def run():
    count=asyncio.run(suite())
    print(f'V56 ENDLESS NORMAL LOOT: {count} PASS')
    return count
if __name__=='__main__':run()
