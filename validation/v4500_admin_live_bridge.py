# -*- coding: utf-8 -*-
"""Owner-friendly live aliases: no new commands required for Guardian11."""
import asyncio
import copy
import random
from types import SimpleNamespace
from validation.v3600_admin_guardian2 import Fake
from systems.live_content_v1204 import LiveContentV1204
from data.quests import QUESTS

async def suite():
    n=0
    owner=Fake();db=owner.server.db
    owner.server.live_content_v1204=LiveContentV1204(SimpleNamespace(conn=db.conn))
    guest=Fake(False,db)
    guest.server.live_content_v1204=owner.server.live_content_v1204
    before_draft=copy.deepcopy(owner.server.live_content_v1204.draft)
    before_q=copy.deepcopy(QUESTS['bandit_patrol'])
    before_db=list(db.conn.execute('SELECT * FROM quests'))
    rng=random.getstate()
    async def run(text,s=owner):
        await s.admin_command('live '+text)
        return s.messages[-1]
    for page in ('1','2','3'):
        assert f'ARENA {page}/3' in await run('arena pomoc '+page);n+=1
    assert 'pomoc 1, 2' in await run('arena pomoc 4');n+=1
    assert 'Nieznana komenda' in await run('arena start serpentarius 9000000 20000',guest);n+=1
    assert not getattr(guest,'guardian7_lab',None);n+=1
    assert 'nieznana opcja' in await run('arena nieistniejaca');n+=1
    assert 'ARENA11 START' in await run('arena start serpentarius 9000000 20000');n+=1
    assert random.getstate()==rng;n+=1
    assert 'ARENA11 KLASA' in await run('arena klasa Wojownik 10 100 POTWIERDZAM');n+=1
    assert 'warrior_power_slash' in await run('arena skille');n+=1
    assert 'ARENA11 PRZEDMIOT' in await run('arena przedmiot leather_vest');n+=1
    assert 'ARENA11 ZALOZONO' in await run('arena zaloz leather_vest POTWIERDZAM');n+=1
    assert 'leather_vest' in await run('arena ekwipunek');n+=1
    snapshot=(owner.guardian7_lab['round'],owner.guardian7_lab['boss'].hp,owner.guardian7_lab['hero_hp'],copy.deepcopy(owner.guardian7_lab['_guardian11_build']))
    assert 'ARENA11 PLAN' in await run('arena sekwencja plan atak,skill:warrior_power_slash');n+=1
    assert 'ARENA10 MIGAWKA' in await run('arena migawka');n+=1
    assert 'ARENA10 PROGNOZA' in await run('arena prognoza 3');n+=1
    assert 'ARENA11 POROWNAJ' in await run('arena sekwencja porownaj atak / obrona');n+=1
    assert (owner.guardian7_lab['round'],owner.guardian7_lab['boss'].hp,owner.guardian7_lab['hero_hp'],owner.guardian7_lab['_guardian11_build'])==snapshot;n+=1
    assert random.getstate()==rng;n+=1
    assert 'ARENA11 WYKONANO' in await run('arena sekwencja wykonaj atak,obrona POTWIERDZAM');n+=1
    assert owner.guardian7_lab['round']==2;n+=1
    assert 'ARENA11 ZDJETO' in await run('arena zdejmij body POTWIERDZAM');n+=1
    assert 'ARENA11' in await run('arena wynik');n+=1
    assert 'ARENA11:' in await run('arena wyjdz');n+=1
    assert owner.guardian7_lab is None;n+=1
    assert 'NAGRODY KATALOG' in await run('nagrody katalog bandit');n+=1
    assert 'QUEST7 SKAN' in await run('questy skan');n+=1
    assert 'OLC' in await run('olc kontrola');n+=1
    assert owner.server.live_content_v1204.draft==before_draft;n+=1
    assert QUESTS['bandit_patrol']==before_q;n+=1
    assert list(db.conn.execute('SELECT * FROM quests'))==before_db;n+=1
    assert owner.current_hp==20 and owner.current_mana==10;n+=1
    assert random.getstate()==rng;n+=1
    assert not db.logged and owner.server.world.mobs=={};n+=1
    db.conn.close()
    return n

def run():return asyncio.run(suite())
if __name__=='__main__':print('ADMIN LIVE GUARDIAN11 v45:',run(),'checks PASS')
