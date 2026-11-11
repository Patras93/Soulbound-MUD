# -*- coding: utf-8 -*-
"""v65: equipment sourced status proofs + UOSS helper passives, zero live effects."""
from __future__ import annotations
import asyncio,copy,random
from types import SimpleNamespace
from validation.v3600_admin_guardian2 import Fake
from systems.live_content_v1204 import LiveContentV1204
from systems.admin_live_v6500 import _replica,_status,_equipment,_passives
from systems.admin_guardian9_v4300 import _sync_actor
from world.uoss_superboss_runtime import superboss_apply_source_status_v11173
from data.items import ITEMS
from data.mobs import MOB_TEMPLATES

async def suite():
    n=0
    def ck(condition,label=''):
        nonlocal n
        assert condition, label
        n+=1
    owner=Fake();db=owner.server.db
    owner.server.live_content_v1204=LiveContentV1204(SimpleNamespace(conn=db.conn))
    visitor=Fake(False,db)
    visitor.server.live_content_v1204=owner.server.live_content_v1204
    before_draft=copy.deepcopy(owner.server.live_content_v1204.draft)
    before_active=copy.deepcopy(owner.server.live_content_v1204.active)
    before_db=db.conn.total_changes
    before_rng=random.getstate()
    before_mobs=copy.deepcopy(MOB_TEMPLATES['uoss_superboss_ruby_weapon_v11136'])
    before_item=copy.deepcopy(ITEMS['uoss_odin_unique_5'])
    async def command(raw, who=owner):
        await who.admin_command('live '+raw)
        return who.messages[-1]
    ck('POMOC 20' in (await command('pomoc 20')))
    ck('Nieznana komenda' in (await command('pomoc 20',visitor)))
    ck('Nieznana komenda' in (await command('arena uoss ekwipunek',visitor)))
    ck('Nieznana komenda' in (await command('arena uoss status Mini',visitor)))
    ck('Nieznana komenda' in (await command('arena uoss pasywy',visitor)))
    ck('ADMIN LIVE V65' in (await command('arena uoss ekwipunek')))
    ck('ADMIN LIVE V65' in (await command('arena uoss status Mini')))
    ck('ADMIN LIVE V65' in (await command('arena uoss pasywy')))
    ck('ARENA11 START' in (await command('arena start ruby_weapon 5000000 1000')))
    ck('brak testowego EQ' in (await command('arena uoss ekwipunek')))
    state=owner.guardian7_lab
    baseline=copy.deepcopy(state)
    rng=state['_guardian10_rng']
    ck('NALOZONY NA KOPIE' in (await command('arena uoss status Mini')))
    ck('NALOZONY NA KOPIE' in (await command('arena uoss status Imp')))
    ck('ADMIN LIVE V65' in (await command('arena uoss status Hall of Stone')))
    ck('ADMIN LIVE V65' in (await command('arena uoss status nie_ma_takiej')))
    ck('ADMIN LIVE V65' in (await command('arena uoss status '+ 'a'*91)))
    ck(random.getstate()==before_rng)
    ck(state['_guardian10_rng']==rng)
    ck(state['round']==baseline['round'] and state['hero_hp']==baseline['hero_hp'])
    ck(state['actor8'].uoss_source_statuses_v11173==set())
    ck('ARENA11 ZALOZONO' in (await command('arena zaloz uoss_odin_unique_5 POTWIERDZAM')))
    ck('mini' in (await command('arena uoss ekwipunek')))
    ck('imp' in (await command('arena uoss ekwipunek')))
    ck('ZABLOKOWANY PRZEZ EQ' in (await command('arena uoss status Mini')))
    ck('ZABLOKOWANY PRZEZ EQ' in (await command('arena uoss status Imp')))
    ck(_replica(owner)['actor8'].equipped_item_rows()==({'item_id':'uoss_odin_unique_5'},))
    ck(owner.guardian7_lab['actor8'].uoss_source_statuses_v11173==set())
    # This integration is not only informational: the actual sourced status
    # function invoked during a normal modelled UOSS round sees the gear.
    _sync_actor(state)
    response=superboss_apply_source_status_v11173(state['actor8'],state['template'],'Mini')
    ck(response['blocked'] is True)
    ck('mini' not in state['actor8'].uoss_source_statuses_v11173)
    ck('ARENA11 ZDJETO' in (await command('arena zdejmij head POTWIERDZAM')))
    ck('brak testowego EQ' in (await command('arena uoss ekwipunek')))
    ck('NALOZONY NA KOPIE' in (await command('arena uoss status Mini')))
    _sync_actor(state)
    response=superboss_apply_source_status_v11173(state['actor8'],state['template'],'Mini')
    ck(response['blocked'] is False)
    ck('mini' in state['actor8'].uoss_source_statuses_v11173)
    # Two armor pieces with status-proof; replacing slot removes previous proof.
    ck('ARENA11 ZALOZONO' in (await command('arena zaloz uoss_odin_unique_4 POTWIERDZAM')))
    ck('ARENA11 ZALOZONO' in (await command('arena zaloz uoss_odin_unique_5 POTWIERDZAM')))
    ck('uoss_odin_unique_4' in (await command('arena uoss ekwipunek')))
    ck(len(_replica(owner)['actor8'].equipped_item_rows())==2)
    ck('ARENA11 ZALOZONO' in (await command('arena zaloz uoss_thief_hat POTWIERDZAM')))
    ck(len(_replica(owner)['actor8'].equipped_item_rows())==2)
    ck('immobilize' in (await command('arena uoss ekwipunek')))
    ck('mini' not in (await command('arena uoss ekwipunek')))
    ck('ZABLOKOWANY PRZEZ EQ' in (await command('arena uoss status Imp')))
    ck('NALOZONY NA KOPIE' in (await command('arena uoss status Mini')))
    # The clone supports source UOSS status for another boss as well.
    ck('ARENA11 START' in (await command('arena start yiazmat 6000000 2000')))
    ck('ARENA11 ZALOZONO' in (await command('arena zaloz uoss_thief_hat POTWIERDZAM')))
    ck('ZABLOKOWANY PRZEZ EQ' in (await command('arena uoss status Ice Breath')))
    ck('NALOZONY NA KOPIE' in (await command('arena uoss status Stone Breath')))
    ck('brak aktywnego pomocnika' in (await command('arena uoss pasywy')))
    # Byblos/Seifer source passives belong to boss test clone, not live world.
    ck('ARENA11 START' in (await command('arena start serpentarius 6000000 3000 Byblos')))
    original=owner.guardian7_lab['boss']
    source_flags=(getattr(original,'uoss_ignore_helper_target_v11174',False),
                  getattr(original,'uoss_power_breakdown_v11174',False))
    ck('Byblos' in (await command('arena uoss pasywy')))
    ck('boss ignoruje pomocnika' in (await command('arena uoss pasywy')))
    ck((getattr(original,'uoss_ignore_helper_target_v11174',False),
        getattr(original,'uoss_power_breakdown_v11174',False))==source_flags)
    ck('ARENA11 START' in (await command('arena start odin 6000000 3000 Seifer')))
    original=owner.guardian7_lab['boss']
    power_before=getattr(original,'uoss_power_breakdown_v11174',False)
    ck('Seifer' in (await command('arena uoss pasywy')))
    ck('Power Breakdown na bossie' in (await command('arena uoss pasywy')))
    ck(getattr(original,'uoss_power_breakdown_v11174',False)==power_before)
    ck('ADMIN LIVE V65' in (await command('arena uoss pasywy zle')))
    ck('ADMIN LIVE V65' in (await command('arena uoss niespodzianka')))
    ck(random.getstate()==before_rng)
    ck(owner.server.live_content_v1204.draft==before_draft)
    ck(owner.server.live_content_v1204.active==before_active)
    ck(db.conn.total_changes==before_db)
    ck(MOB_TEMPLATES['uoss_superboss_ruby_weapon_v11136']==before_mobs)
    ck(ITEMS['uoss_odin_unique_5']==before_item)
    ck(owner.current_hp==20 and owner.current_mana==10)
    ck(owner.server.world.mobs=={})
    ck(not db.logged)
    ck('ARENA11:' in (await command('arena wyjdz')))
    ck(owner.guardian7_lab is None)
    db.conn.close()
    return n

def run():return asyncio.run(suite())
if __name__=='__main__':print('V65 UOSS SOURCE EQ:',run(),'PASS')
