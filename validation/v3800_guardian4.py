# -*- coding: utf-8 -*-
"""Regression: Guardian4 seven areas, owner gate, atomic DRAFT, no game rewards."""
import asyncio
import copy
from validation.v3600_admin_guardian2 import Fake
from systems.live_content_v1204 import LiveContentV1204, blank
from systems.admin_guardian3_v3700 import (_build_region,_add_region_mob,
                                             _add_region_npc,_add_region_shop,_add_region_quest)
from systems.admin_guardian4_v3800 import _arena_projection, _area_report, _area_connect

async def suite():
    checks=0
    s=Fake()
    async def cmd(command):
        await s.admin_command('guardian4 '+command)
        return s.messages[-1]
    stranger=Fake(False,s.server.db)
    await stranger.admin_command('guardian4 status')
    assert 'tylko wlasciciel' in stranger.messages[-1];checks+=1
    assert 'GUARDIAN4' in await cmd('pomoc');checks+=1
    assert 'v38' in await cmd('status');checks+=1
    db=s.server.db
    logged_before=len(db.logged);world_before=copy.deepcopy(s.server.world.mobs)
    assert 'WYGRANA' in await cmd('arena prognoza live_dummy 100 200');checks+=1
    assert 'HP moba 0/600' in s.messages[-1] and 'postaci 76/100' in s.messages[-1];checks+=1
    assert 'PORAZKA' in await cmd('arena prognoza live_dummy 10 20');checks+=1
    assert 'LIMIT_TUR' in await cmd('arena prognoza live_dummy 100 100 1');checks+=1
    assert 'WARIANT B' in await cmd('arena porownaj live_dummy 100 100 200');checks+=1
    assert 'Zakres' in await cmd('arena prognoza live_dummy 100 200 1001');checks+=1
    assert s.server.world.mobs==world_before and len(db.logged)==logged_before;checks+=1
    assert 'Nieznany mob' in await cmd('arena prognoza missing 100 200');checks+=1
    from types import SimpleNamespace
    live=object.__new__(LiveContentV1204);live.draft=blank();live.active=blank()
    _build_region(live,'skalne','Gory Skalne',100,6)
    _add_region_mob(live,'skalne',['live_skalne_wilk','Wilk',1200,100,500,3])
    _add_region_npc(live,'skalne',['live_skalne_kupiec','Kupiec Gorski',2,'kupiec','Witaj.'])
    _add_region_npc(live,'skalne',['live_skalne_questgiver','Gorski Przewodnik',4,'zleceniodawca','Wyrusz.'])
    _add_region_shop(live,'skalne',[2,'healing_potion,soul_shard'])
    _add_region_quest(live,'skalne',['live_skalne_quest','Wyprawa','Gorski Przewodnik','live_skalne_wilk',5,100])
    s.server.live_content_v1204=live
    assert '6/6' in await cmd('kraina sprawdz skalne');checks+=1
    assert 'wejsc z zewnatrz 0' in s.messages[-1];checks+=1
    saved=copy.deepcopy(live.draft)
    assert 'POTWIERDZAM' in await cmd('kraina polacz skalne 1 6 north');checks+=1
    assert live.draft==saved;checks+=1
    assert 'KRAINA DRAFT' in await cmd('kraina polacz skalne 1 6 north POTWIERDZAM');checks+=1
    assert ['live_skalne_r01','north','live_skalne_r06'] in live.draft['links'];checks+=1
    assert ['live_skalne_r06','south','live_skalne_r01'] in live.draft['links'];checks+=1
    new=copy.deepcopy(live.draft)
    assert 'zajety' in await cmd('kraina polacz skalne 1 5 north POTWIERDZAM');checks+=1
    assert live.draft==new;checks+=1
    assert 'rozne' in await cmd('kraina polacz skalne 1 1 east POTWIERDZAM');checks+=1
    assert 'Nie ma takiej krainy' in await cmd('kraina sprawdz obca');checks+=1
    assert 'kolizje NPC 0' in await cmd('kraina sprawdz skalne');checks+=1
    assert live.validate(live.draft);checks+=1
    # test that failed OLC validation leaves original DRAFT intact
    before=copy.deepcopy(live.draft)
    real_validate=live.validate
    def fail(*_):raise ValueError('celowo zablokowana walidacja')
    live.validate=fail
    assert 'celowo zablokowana' in await cmd('kraina polacz skalne 1 5 up POTWIERDZAM');checks+=1
    assert before==live.draft;checks+=1
    live.validate=real_validate
    assert 'Quest' not in await cmd('questy skan Friend') or 'QUESTY' in s.messages[-1];checks+=1
    db.conn.execute("INSERT INTO quests VALUES (2,'temple_rats','active',-3,0,-2)")
    assert 'ujemny postep' in await cmd('questy skan Friend');checks+=1
    assert 'ujemny licznik' in s.messages[-1];checks+=1
    assert db.quest(2,'temple_rats')['progress']==-3 and db.quest(2,'temple_rats')['completion_count']==-2;checks+=1
    assert 'Nieznany nick' in await cmd('questy skan Nobody');checks+=1
    assert 'cel moba istnieje' in await cmd('questy katalog live_skalne_quest');checks+=1
    assert 'Nieznany QUEST_ID' in await cmd('questy katalog xxxxxx');checks+=1
    assert 'wariant A' in (await cmd('balans porownaj live_skalne_wilk 200 300'));checks+=1
    assert 'roznica' in s.messages[-1];checks+=1
    assert 'EVENTY GUARDIAN' in await cmd('event raport');checks+=1
    assert 'brak aktywnych' in s.messages[-1];checks+=1
    s.server.guardian_events_v3600={'najazd':{'room':'temple','keys':['event1'],'started':0}}
    s.server.guardian_spawns_v3600={'event1':'bandit'}
    assert 'najazd' in await cmd('event raport');checks+=1
    assert '0/1 mobow' in s.messages[-1];checks+=1
    db.conn.execute("INSERT INTO admin_actions_v1224(admin_login,action,target) VALUES ('owner','g2_guardian_fix','quest')")
    assert 'g2_guardian_fix' in await cmd('historia filtruj guardian');checks+=1
    assert 'brak dopasowan' in await cmd('historia filtruj xxyyz');checks+=1
    assert 'Fragment akcji' in await cmd('historia filtruj %');checks+=1
    assert 'ROLE GUARDIAN' in await cmd('role raport');checks+=1
    assert 'tylko wlasciciel' in stranger.messages[-1];checks+=1
    assert len(db.logged)==logged_before+1 and s.server.world.mobs==world_before;checks+=1
    return checks

def run():return asyncio.run(suite())
if __name__=='__main__':print('ADMIN GUARDIAN 4:',run(),'checks PASS')
