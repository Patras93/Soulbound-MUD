# -*- coding: utf-8 -*-
"""v70.00.2: source UOSS trace, EQ coverage, atomic goal-count fixes, owner/DB safety."""
from __future__ import annotations
import asyncio,copy,random
from types import SimpleNamespace
from validation.v3600_admin_guardian2 import Fake
from systems.live_content_v1204 import LiveContentV1204
from systems.admin_live_v7002 import equipment_coverage,quest_scan,_scan
from data.items import ITEMS

async def suite():
    checks=0
    def ck(value, reason=''):
        nonlocal checks
        assert value,reason
        checks+=1
    owner=Fake();db=owner.server.db
    service=LiveContentV1204(SimpleNamespace(conn=db.conn));owner.server.live_content_v1204=service
    guest=Fake(False,db);guest.server.live_content_v1204=service
    before_active=copy.deepcopy(service.active);before_draft=copy.deepcopy(service.draft)
    before_items=len(ITEMS);before_rng=random.getstate();before_changes=db.conn.total_changes
    async def cmd(value,who=owner):
        await who.admin_command('live '+value)
        return who.messages[-1]
    ck('POMOC 26' in await cmd('pomoc 26'))
    for command in ('pomoc 26','arena uoss reguly','eq pokrycie leather_vest','questy automaty skan',
                    'questy automaty plan','questy automaty zatwierdz POTWIERDZAM'):
        ck('Nieznana komenda' in await cmd(command,guest),command)
    ck('V70.00.2' in await cmd('arena uoss reguly'))
    ck('ARENA11 START' in await cmd('arena start ruby_weapon 100000 2000'))
    trace=await cmd('arena uoss reguly 6 1')
    ck('ARENA UOSS REGULY' in trace,trace)
    ck('6: faza' in trace and 'Big Swing' in trace,trace)
    ck('status=Noact' in trace,trace)
    ck('nieokreslone' in trace or 'NIE:' in trace)
    ck(trace==await cmd('arena uoss reguly 6 1'))
    for command in ('arena uoss reguly 0','arena uoss reguly 13','arena uoss reguly -1',
                    'arena uoss reguly 2 250','arena uoss reguly 3 abc',
                    'arena uoss reguly 2 1 9','arena uoss reguly '+'8'*100):
        ck('ADMIN LIVE V70.00.2' in await cmd(command),command)
    ck('ARENA11 START' in await cmd('arena start serpentarius 100000 2000 Byblos'))
    ck('Resisted Gravija' in await cmd('arena uoss reguly 6'))
    ck('current_hp_fraction=0.1' in await cmd('arena uoss reguly 6'))
    ck('Limit 100 rund' in await cmd('arena uoss reguly 2 101'))
    ck('ARENA11 START' in await cmd('arena start yiazmat 100000 2000 Montblanc'))
    ck('Summon Dragon Guardian' in await cmd('arena uoss reguly 4 4'))
    ck('ARENA11 START' in await cmd('arena start odin 100000 2000 Seifer'))
    ck('current_hp_fraction=' in await cmd('arena uoss reguly 6 1'))
    ck('ARENA11' in await cmd('arena wyjdz'))
    for lvl in (801,900,1000,9999):
        out=await cmd(f'eq pokrycie leather_vest {lvl}')
        for term in ('krypta: etap','mityczna_krypta: etap','wieza_astralna: etap',
                     'mityczna_wieza: etap','magitek: etap','swiat: etap',
                     'quest: etap','rzemioslo:','Skrzynie:','Sklepy','brak zmian bazy'):
            ck(term in out,(lvl,term,out))
        ck(out==await cmd(f'eq pokrycie leather_vest {lvl}'))
    ck('25% losowania 1 dodatkowego EQ' in await cmd('eq pokrycie leather_vest 900'))
    ck('NIE jest w puli bonusowej' in await cmd('eq pokrycie oak_iron_charm 900'))
    ck('EQ POKRYCIE' in await cmd('eq pokrycie'), 'v54 legacy coverage retained')
    for command in ('eq pokrycie nonexistent_xyz','eq pokrycie uoss_odin_unique_5',
                    'eq pokrycie leather_vest 800','eq pokrycie leather_vest 0',
                    'eq pokrycie leather_vest abc','eq pokrycie leather_vest 1000001',
                    'eq pokrycie leather_vest 900 extra','eq pokrycie ../secret 900'):
        ck('ADMIN LIVE V70.00.2' in await cmd(command),command)
    ck('naprawialne 0' in await cmd('questy automaty skan'))
    ck('brak rozbieznosci' in await cmd('questy automaty skan 1'))
    ck('QUEST AUTOMAT KARTA' in await cmd('questy automaty karta toren_ore_samples_v0929'))
    ck('brak bezpiecznych' in (await cmd('questy automaty plan')).lower())
    # Deliberately corrupt ONLY a DRAFT field in a detached in-memory test DB.
    qid='toren_ore_samples_v0929'
    service.draft.setdefault('quest_edits',{})[qid]={'needed':999}
    ck(_scan(service)[1][qid]==15)
    ck('naprawialne 1' in await cmd('questy automaty skan'))
    ck('needed 999 -> 15' in await cmd('questy automaty plan '+qid))
    ck('gotowy' in await cmd('questy automaty status'))
    ck(service.draft['quest_edits'][qid]['needed']==999)
    ck('DRAFT' in await cmd('questy automaty zatwierdz POTWIERDZAM'))
    ck(service.draft['quest_edits'][qid]['needed']==15)
    ck('dostepne' in await cmd('questy automaty status'))
    ck(service.active==before_active)
    ck('COFNIETO' in await cmd('questy automaty cofnij POTWIERDZAM'))
    ck(service.draft['quest_edits'][qid]['needed']==999)
    ck('ADMIN LIVE V70.00.2' in await cmd('questy automaty cofnij POTWIERDZAM'))
    # Stale-plan validation protects against another admin's edits.
    ck('PLAN 1' in await cmd('questy automaty plan'))
    service.draft['balances']['fake_check']=dict(max_hp=77)
    ck('OLC zmienione od planu' in await cmd('questy automaty zatwierdz POTWIERDZAM'))
    ck(service.draft['quest_edits'][qid]['needed']==999)
    service.draft=copy.deepcopy(before_draft)
    for command in ('questy automaty skan 0','questy automaty skan 3',
                    'questy automaty skan xyz','questy automaty karta nonexistent_123',
                    'questy automaty plan bad_quest','questy automaty plan toren_ore_samples_v0929',
                    'questy automaty zatwierdz POTWIERDZAM','questy automaty cofnij POTWIERDZAM',
                    'questy automaty unknown'):
        ck('ADMIN LIVE V70.00.2' in await cmd(command),command)
    # A unique UOSS vendor item must never turn into infinite generic EQ.
    from systems.endless_loot_v5600 import eligible_normal_equipment_drop_v5600, convert_normal_equipment_drop_v5600
    from systems.infinite_equipment import infinite_equipment_variant_for_drop
    from systems.quest_equipment_v6200 import quest_equipment_id_v6200,quest_gear_profile_v6200
    from systems.endless_crafting_v5500 import endless_crafted_equipment_v5500
    from unittest.mock import patch
    unique='uoss_odin_unique_5'
    ck(unique in ITEMS)
    ck(not eligible_normal_equipment_drop_v5600(unique, {'level':900}))
    ck(convert_normal_equipment_drop_v5600(unique,{'level':900})==unique)
    ck(infinite_equipment_variant_for_drop(unique,{'level':900})==unique)
    ck(quest_gear_profile_v6200(unique,{'recommended_level':900}) is None)
    ck(quest_equipment_id_v6200(unique,{'recommended_level':900})==unique)
    with patch('systems.endless_crafting_v5500.craft_stage_v5500', return_value=900):
        ck(endless_crafted_equipment_v5500(unique,900,900)==unique)
        with patch('systems.endless_crafting_v5500.register_infinite_equipment_variant',return_value='deepq_forge_r_r30_leather_vest'):
            ck(endless_crafted_equipment_v5500('leather_vest',900,900).startswith('deepq_forge_'))
    ck(eligible_normal_equipment_drop_v5600('leather_vest', {'level':900}))
    # Multi-objective goals use the canonical mixed kill/collect/talk contract.
    from validation.v6200_admin_live_bundle import strict_service
    new_service=strict_service()
    mid='live_v7002_multi'
    base={'name':'Multi test','description':'Test', 'giver':'Rybak Borys',
          'kind':'multi_objective','target':'temple_rat','needed':6,
          'objectives':{'kill':{'temple_rat':2},'collect':{'iron_ore':3},'talk':['fisher_tomas']},
          'reward_silver':0}
    new_service.draft['quests'][mid]=copy.deepcopy(base)
    new_service.validate(new_service.draft)
    new_service.draft['quests'][mid]['needed']=11
    owner.server.live_content_v1204=new_service
    ck(_scan(new_service)[1][mid]==6)
    ck('11 -> 6' in await cmd('questy automaty plan '+mid))
    ck('DRAFT' in await cmd('questy automaty zatwierdz POTWIERDZAM'))
    ck(_scan(new_service)[1].get(mid) is None)
    ck('COFNIETO' in await cmd('questy automaty cofnij POTWIERDZAM'))
    ck(_scan(new_service)[1].get(mid)==6)
    owner.server.live_content_v1204=service
    ck('anulowany' in await cmd('questy automaty anuluj'))
    ck('brak' in await cmd('questy automaty status'))
    ck(service.draft==before_draft)
    ck(service.active==before_active)
    ck(db.conn.total_changes==before_changes)
    ck(random.getstate()==before_rng)
    ck(len(ITEMS)==before_items)
    ck(owner.server.world.mobs=={})
    ck(not db.logged)
    db.conn.close()
    return checks

def run():return asyncio.run(suite())
if __name__=='__main__':print('V70.00.2 THREE GAPS:',run(),'PASS')
