# -*- coding: utf-8 -*-
"""Guardian11: detached class skills, simulated equipment, deterministic scripts."""
import asyncio
import copy
import random
from types import SimpleNamespace
from validation.v3600_admin_guardian2 import Fake
from systems.live_content_v1204 import LiveContentV1204
from data.mobs import MOB_TEMPLATES
from data.items import ITEMS
from data.quests import QUESTS

async def suite():
    count=0
    owner=Fake(); db=owner.server.db
    owner.server.live_content_v1204=LiveContentV1204(SimpleNamespace(conn=db.conn))
    service=owner.server.live_content_v1204
    baseline_draft=copy.deepcopy(service.draft)
    baseline_quest=copy.deepcopy(QUESTS['bandit_patrol'])
    baseline_mob=copy.deepcopy(MOB_TEMPLATES['uoss_superboss_serpentarius_v11136'])
    baseline_db=list(db.conn.execute('SELECT * FROM quests'))
    guest=Fake(False,db)
    async def run(line,user=owner):
        await user.admin_command('guardian11 '+line)
        return user.messages[-1]
    def fingerprint():
        a=owner.guardian7_lab
        if a is None:return None
        return (a['round'],a['hero_hp'],a['boss'].hp,a['total_dealt'],a['total_taken'],
                a['_guardian10_rng'],copy.deepcopy(a['_guardian11_build']),list(a['notes']))
    for p in (1,2,3):
        assert 'GUARDIAN11' in await run('pomoc '+str(p));count+=1
    assert 'GUARDIAN11' in await run('pomoc 4');count+=1
    assert 'tylko administrator' in await run('arena start serpentarius 9000000 20000',guest);count+=1
    assert not getattr(guest,'guardian7_lab',None);count+=1
    worldrng=random.getstate()
    assert 'ARENA11 START' in await run('arena start serpentarius 9000000 20000');count+=1
    assert random.getstate()==worldrng;count+=1
    assert 'GUARDIAN11' in await run('arena skille');count+=1
    assert 'GUARDIAN11' in await run('arena klasa Niebieski 200 200 POTWIERDZAM');count+=1
    assert 'ARENA11 KLASA' in await run('arena klasa Wojownik 10 100 POTWIERDZAM');count+=1
    assert 'warrior_power_slash' in await run('arena skille');count+=1
    assert 'GUARDIAN11' in await run('arena skille 1000');count+=1
    assert 'GUARDIAN11' in await run('arena skill missing_skill');count+=1
    assert 'ARENA11 PRZEDMIOT' in await run('arena przedmiot leather_vest');count+=1
    assert 'GUARDIAN11' in await run('arena zaloz healing_potion POTWIERDZAM');count+=1
    assert 'GUARDIAN11' in await run('arena zaloz leather_vest NIE');count+=1
    assert 'ARENA11 ZALOZONO' in await run('arena zaloz leather_vest POTWIERDZAM');count+=1
    assert 'leather_vest' in await run('arena ekwipunek');count+=1
    baseline=fingerprint(); world_before=random.getstate()
    assert 'ARENA11 PLAN' in await run('arena sekwencja plan atak,skill:warrior_power_slash,obrona');count+=1
    assert fingerprint()==baseline and random.getstate()==world_before;count+=1
    assert 'ARENA11 POROWNAJ' in await run('arena sekwencja porownaj atak,atak / obrona,atak');count+=1
    assert fingerprint()==baseline and random.getstate()==world_before;count+=1
    for text in ('arena sekwencja plan atak,', 'arena sekwencja plan atak,skill:missing',
                 'arena sekwencja wykonaj atak,skill:missing POTWIERDZAM',
                 'arena sekwencja plan atak,atak,atak,atak,atak,atak,atak,atak,atak,atak,atak,atak,atak',
                 'arena sekwencja wykonaj atak NIE'):
        assert 'GUARDIAN11' in await run(text);count+=1
        assert fingerprint()==baseline and random.getstate()==world_before;count+=1
    assert 'ARENA11 WYKONANO' in await run('arena sekwencja wykonaj atak,skill:warrior_power_slash,obrona POTWIERDZAM');count+=1
    assert owner.guardian7_lab['round']==3;count+=1
    assert random.getstate()==world_before;count+=1
    assert 'ARENA11' in await run('arena skill warrior_power_slash');count+=1
    assert random.getstate()==world_before;count+=1
    assert 'ARENA11' in await run('arena wynik');count+=1
    assert 'ARENA11 ZDJETO' in await run('arena zdejmij body POTWIERDZAM');count+=1
    assert 'brak' in await run('arena ekwipunek');count+=1
    assert 'GUARDIAN11' in await run('arena zdejmij body POTWIERDZAM');count+=1
    assert 'ARENA11 KLASA' in await run('arena klasa Mag 50 0 POTWIERDZAM');count+=1
    assert 'Za malo many' in await run('arena skill v0922_mage_grid_1_2');count+=1
    assert 'ARENA11 KLASA' in await run('arena klasa Mag 50 200 POTWIERDZAM');count+=1
    before=owner.guardian7_lab['_guardian11_build']['mana']
    assert 'Pocisk' in await run('arena skill v0922_mage_grid_1_2');count+=1
    assert owner.guardian7_lab['_guardian11_build']['mana']<before;count+=1
    assert 'GUARDIAN11' in await run('arena skill v0922_mage_grid_1_3');count+=1 # unsupported AoE
    assert random.getstate()==world_before;count+=1
    assert 'ARENA11' in await run('arena wyjdz');count+=1
    assert owner.guardian7_lab is None and owner.guardian9_snapshot is None;count+=1
    assert service.draft==baseline_draft;count+=1
    assert QUESTS['bandit_patrol']==baseline_quest;count+=1
    assert MOB_TEMPLATES['uoss_superboss_serpentarius_v11136']==baseline_mob;count+=1
    assert list(db.conn.execute('SELECT * FROM quests'))==baseline_db;count+=1
    assert not db.logged and owner.server.world.mobs=={};count+=1
    assert owner.current_hp==20 and owner.current_mana==10;count+=1
    db.conn.close()
    return count

def run():return asyncio.run(suite())
if __name__=='__main__':print('GUARDIAN11 v45:',run(),'checks PASS')
