# -*- coding: utf-8 -*-
"""Guardian10 regression: RNG, snapshot, readonly OLC, permissions, old features."""
import asyncio
import copy
import random
from types import SimpleNamespace
from validation.v3600_admin_guardian2 import Fake
from systems.live_content_v1204 import LiveContentV1204
from systems.admin_guardian10_v4400 import _seed_params
from data.mobs import MOB_TEMPLATES
from data.quests import QUESTS

async def suite():
    n=0
    owner=Fake(); db=owner.server.db
    owner.server.live_content_v1204=LiveContentV1204(SimpleNamespace(conn=db.conn))
    service=owner.server.live_content_v1204
    initial_draft=copy.deepcopy(service.draft)
    original_boss=copy.deepcopy(MOB_TEMPLATES['uoss_superboss_serpentarius_v11136'])
    original_quest=copy.deepcopy(QUESTS['bandit_patrol'])
    guest=Fake(False,db)
    db.conn.execute("INSERT INTO quests(account_id,quest_id,status,progress,completion_count) VALUES(1,'bandit_patrol','active',7,0)")
    db.conn.commit(); baseline_sqlite=list(db.conn.execute('SELECT * FROM quests'))
    async def cmd(s,command):
        await s.admin_command('guardian10 '+command)
        return s.messages[-1]
    for page in (1,2,3):
        assert 'GUARDIAN10' in await cmd(owner,'pomoc '+str(page));n+=1
    assert 'GUARDIAN10' in await cmd(owner,'pomoc 4');n+=1
    assert 'tylko' in await cmd(guest,'arena start serpentarius 5000000 10000');n+=1
    assert not getattr(guest,'guardian7_lab',None);n+=1
    assert 'GUARDIAN10' in await cmd(owner,'arena porownaj 3');n+=1
    state_before=random.getstate()
    assert 'ARENA10 START' in await cmd(owner,'arena start serpentarius 5000000 1000 Byblos');n+=1
    assert random.getstate()==state_before;n+=1
    a=owner.guardian7_lab
    assert a['_guardian10_seed']==_seed_params('serpentarius','5000000','1000','Byblos');n+=1
    rng=a['_guardian10_rng'];base=copy.deepcopy(a)
    def view(st):
        return (st['round'],st['hero_hp'],st['hero_max'],st['boss'].hp,st['boss'].phase_stage,
                [(v['id'],v['hp']) for v in st['adds']],st['total_dealt'],st['total_taken'],
                tuple(st['notes']),tuple(sorted(st['statuses'])),st['_guardian10_rng'],st['_guardian10_seed'])
    baseline=view(a)
    for amount in (1,3,10,20):
        before=random.getstate()
        assert 'ARENA10 PROGNOZA' in await cmd(owner,f'arena prognoza {amount}');n+=1
        assert view(owner.guardian7_lab)==baseline;n+=1
        assert random.getstate()==before;n+=1
    assert 'ARENA10 POROWNAJ' in await cmd(owner,'arena porownaj 6');n+=1
    assert view(owner.guardian7_lab)==baseline and random.getstate()==state_before;n+=1
    assert 'GUARDIAN10' in await cmd(owner,'arena prognoza 21');n+=1
    assert 'GUARDIAN10' in await cmd(owner,'arena porownaj 0');n+=1
    assert 'GUARDIAN10' in await cmd(owner,'arena seria 3 zla');n+=1
    assert a['_guardian10_rng']==rng;n+=1
    assert 'ARENA10 MIGAWKA' in await cmd(owner,'arena migawka');n+=1
    assert 'ARENA10 SERIA' in await cmd(owner,'arena seria 4');n+=1
    assert owner.guardian7_lab['round']==4 and random.getstate()==state_before;n+=1
    r1=copy.deepcopy(owner.guardian7_lab)
    assert 'ARENA10 PRZYWROCONO' in await cmd(owner,'arena przywroc POTWIERDZAM');n+=1
    assert view(owner.guardian7_lab)==baseline;n+=1
    assert 'ARENA10 SERIA' in await cmd(owner,'arena seria 4');n+=1
    assert view(owner.guardian7_lab)==view(r1);n+=1
    assert 'ARENA10' in await cmd(owner,'arena status');n+=1
    assert 'ARENA10 RAPORT' in await cmd(owner,'arena raport');n+=1
    assert 'ARENA10' in await cmd(owner,'arena dziennik');n+=1
    assert 'GUARDIAN10' in await cmd(owner,'arena atak 999');n+=1
    assert view(owner.guardian7_lab)==view(r1) and random.getstate()==state_before;n+=1
    assert 'GUARDIAN10' in await cmd(owner,'arena ziarno 15 NIE');n+=1
    assert view(owner.guardian7_lab)==view(r1);n+=1
    assert 'ARENA10 ZIARNO 15' in await cmd(owner,'arena ziarno 15 POTWIERDZAM');n+=1
    assert owner.guardian7_lab['_guardian10_rng']==random.Random(15).getstate();n+=1
    assert random.getstate()==state_before;n+=1
    assert 'ARENA10' in await cmd(owner,'arena atak');n+=1
    assert 'ARENA10' in await cmd(owner,'arena magia ogien');n+=1
    assert 'ARENA10' in await cmd(owner,'arena lecz');n+=1
    assert 'ARENA10' in await cmd(owner,'arena oczysc');n+=1
    assert 'ARENA10' in await cmd(owner,'arena obrona');n+=1
    assert random.getstate()==state_before;n+=1
    assert 'ARENA10' in await cmd(owner,'arena wyjdz');n+=1
    assert owner.guardian7_lab is None and owner.guardian9_snapshot is None;n+=1
    assert 'GUARDIAN10' in await cmd(owner,'arena przywroc POTWIERDZAM');n+=1
    assert 'ARENA10 START' in await cmd(owner,'arena start black_rabite 100000000 1000');n+=1
    assert 'ARENA10' in await cmd(owner,'arena seria 2');n+=1
    assert random.getstate()==state_before;n+=1
    assert 'ARENA10' in await cmd(owner,'arena wyjdz');n+=1
    for action in ('nagrody','diagnoza','porownaj','zaleznosci'):
        assert 'bandit_patrol' in await cmd(owner,'questy '+action+' bandit_patrol');n+=1
    assert 'DRAFT' in await cmd(owner,'questy draft');n+=1
    assert 'ROZNICE' in await cmd(owner,'questy seria roznice bandit_patrol | needed | 12');n+=1
    assert service.draft==initial_draft;n+=1
    assert 'GUARDIAN10' in await cmd(owner,'questy seria roznice bandit_patrol | needed | 12 ; missing_id | needed | 5');n+=1
    assert service.draft==initial_draft;n+=1
    assert random.getstate()==state_before;n+=1
    assert list(db.conn.execute('SELECT * FROM quests'))==baseline_sqlite;n+=1
    assert MOB_TEMPLATES['uoss_superboss_serpentarius_v11136']==original_boss;n+=1
    assert QUESTS['bandit_patrol']==original_quest;n+=1
    assert owner.current_hp==20 and owner.current_mana==10 and owner.server.world.mobs=={};n+=1
    assert not any('guardian10' in str(row) for row in db.logged);n+=1
    db.conn.close()
    return n

def run():return asyncio.run(suite())
if __name__=='__main__':print('GUARDIAN10 v44:',run(),'checks PASS')
