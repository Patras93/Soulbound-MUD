# -*- coding: utf-8 -*-
"""Regression checks for Admin Guardian 3 owner gates, staged world and SQLite safety."""
import asyncio
import copy
import sqlite3
from validation.v3600_admin_guardian2 import Fake,DB
from systems.admin_guardian3_v3700 import _arena_report, _region_ids
from data.quests import QUESTS

async def suite():
    checks=0
    s=Fake(); d=s.server.db
    async def cmd(arg):
        await s.admin_command('guardian3 '+arg)
        return s.messages[-1]
    b=Fake(False,d)
    await b.admin_command('guardian3 status')
    assert 'tylko wlasciciel' in b.messages[-1]; checks+=1
    await b.admin_command('guardian3 kraina tworz admin | Nazwa | 10 | 4 POTWIERDZAM')
    assert not b.server.live_content_v1204.draft['rooms'];checks+=1
    assert 'GUARDIAN3 v37' in await cmd('status');checks+=1
    assert 'ADMIN GUARDIAN3' in await cmd('pomoc');checks+=1
    assert 'Nieznany mob' in await cmd('arena start missing 100 10');checks+=1
    assert 'ARENA 3.0' in await cmd('arena start live_dummy 100 200');checks+=1
    assert '0 tur' in await cmd('arena wynik');checks+=1
    assert 'tura 1' in await cmd('arena tura');checks+=1
    assert s.guardian3_arena['enemy_hp']==400 and s.guardian3_arena['hero_hp']==88;checks+=1
    assert 'walka' in await cmd('arena tura');checks+=1
    assert 'wygrana' in await cmd('arena tura');checks+=1
    assert s.guardian3_arena['enemy_hp']==0 and s.guardian3_arena['hero_hp']==76;checks+=1
    assert '0' in await cmd('arena wynik');checks+=1
    assert 'ZAMKNIETA' in await cmd('arena koniec');checks+=1
    assert s.server.world.mobs=={} and not d.logged;checks+=1
    teammate=Fake(False,d);teammate.current_hp=4;teammate.current_mana=3
    s.party_key=lambda: 'party37';teammate.party_key=lambda: 'party37'
    s.server.sessions=[s,teammate]
    assert 'OSLONA DRUZYNY' in await cmd('moc oslonadruzyny POTWIERDZAM');checks+=1
    assert s.current_hp==100 and teammate.current_hp==100 and teammate.current_mana==200;checks+=1
    assert not getattr(teammate,'admin_god_v35005',False);checks+=1
    s.server.sessions=[s];s.party_key=lambda: None
    content=s.server.live_content_v1204
    content.draft['quests']={}
    content.draft['npcs']={}
    content.draft['shops']={}
    content.draft['spawns']=[]
    content.stage_mob=lambda mid,name,lv,hp,damage,exp: content.draft['mobs'].update({mid:{'name':name,'generator_level':lv,'max_hp':hp,'damage':damage,'class_xp_reward':exp}})
    content.stage_spawn=lambda rid,mid: content.draft['spawns'].append([rid,mid])
    content.stage_new_quest=lambda qid,name,giver,kind,target,needed,silver,description: content.draft['quests'].update({qid:{'name':name,'giver':giver,'kind':kind,'target':target,'needed':needed,'reward_silver':silver,'description':description}})
    assert 'PLAN DRAFT' in await cmd('kraina plan wyprawa | Szlak Wyprawy | 120 | 6');checks+=1
    assert len(s.server.live_content_v1204.draft['rooms'])==0;checks+=1
    assert 'POTWIERDZAM' in await cmd('kraina tworz wyprawa | Szlak Wyprawy | 120 | 6');checks+=1
    assert '6 pokoi' in await cmd('kraina tworz wyprawa | Szlak Wyprawy | 120 | 6 POTWIERDZAM');checks+=1
    draft=s.server.live_content_v1204.draft
    assert len(draft['rooms'])==6 and len(draft['links'])==10;checks+=1
    assert ('live_wyprawa_r01','live_wyprawa_r06')==(_region_ids('wyprawa',6)[0],_region_ids('wyprawa',6)[-1]);checks+=1
    first=copy.deepcopy(draft)
    assert 'zajete ID' in await cmd('kraina tworz wyprawa | Powtorna | 120 | 4 POTWIERDZAM');checks+=1
    assert draft==first;checks+=1
    assert 'dodano' in await cmd('kraina potwor wyprawa live_wyprawa_wilk | Wilk wyprawy | 1200 | 130 | 400 | 2 POTWIERDZAM');checks+=1
    assert 'live_wyprawa_wilk' in draft['mobs'] and ['live_wyprawa_r02','live_wyprawa_wilk'] in draft['spawns'];checks+=1
    # Real OLC NPC/shops; Fake's validator is intentionally limited.
    assert 'NPC DRAFT' in await cmd('kraina npc wyprawa live_wyprawa_kupiec | Kupiec wyprawy | 3 | kupiec | Witaj. POTWIERDZAM');checks+=1
    assert 'NPC DRAFT' in await cmd('kraina npc wyprawa live_wyprawa_dawca | Kaplan Elor | 4 | zleceniodawca | Porozmawiaj. POTWIERDZAM');checks+=1
    assert 'SKLEP DRAFT' in await cmd('kraina sklep wyprawa 3 | healing_potion,soul_shard POTWIERDZAM');checks+=1
    assert draft['npcs']['live_wyprawa_kupiec']['shopkeeper'] and len(draft['shops']['live_wyprawa_r03'])==2;checks+=1
    assert 'QUEST DRAFT' in await cmd('kraina quest wyprawa live_wyprawa_quest | Polowanie | Kaplan Elor | live_wyprawa_wilk | 5 | 100 POTWIERDZAM');checks+=1
    assert draft['npcs']['live_wyprawa_dawca']['quest']=='live_wyprawa_quest';checks+=1
    assert draft['quests']['live_wyprawa_quest']['target']=='live_wyprawa_wilk';checks+=1
    assert 'hipotetycznych' in await cmd('balans raport bandit 10');checks+=1
    assert 'DRAFT' in await cmd('balans raport live_wyprawa_wilk 200');checks+=1
    assert 'brak' in (await cmd('event raport')).lower();checks+=1
    assert 'Brak druzyny' in await cmd('moc oslonadruzyny POTWIERDZAM');checks+=1
    assert 'brak' in (await cmd('historia ostatnie')).lower();checks+=1
    assert 'brak' in (await cmd('role raport')).lower();checks+=1
    # Separate v37 ledger: do not fake quest kills or account awards.
    d.conn.execute("INSERT INTO quests VALUES (2,'temple_rats','active',2,0,-4)")
    assert 'BLEDUJACY' in await cmd('quest kontrola Friend temple_rats');checks+=1
    assert 'POTWIERDZAM' in await cmd('quest korekta Friend temple_rats licznik_ukonczen');checks+=1
    s.server.sessions=[s,teammate]
    assert 'Gracz musi byc offline' in await cmd('quest korekta Friend temple_rats licznik_ukonczen POTWIERDZAM');checks+=1
    assert d.quest(2,'temple_rats')['completion_count']==-4;checks+=1
    s.server.sessions=[s]
    assert d.quest(2,'temple_rats')['completion_count']==-4;checks+=1
    assert 'KOREKTA' in await cmd('quest korekta Friend temple_rats licznik_ukonczen POTWIERDZAM');checks+=1
    assert d.quest(2,'temple_rats')['completion_count']==0 and d.quest(2,'temple_rats')['progress']==2;checks+=1
    assert 'temple_rats' in await cmd('quest historia');checks+=1
    assert 'COFNIETO' in await cmd('quest cofnij 1 POTWIERDZAM');checks+=1
    assert d.quest(2,'temple_rats')['completion_count']==-4;checks+=1
    assert 'Nie ma aktywnej' in await cmd('quest cofnij 1 POTWIERDZAM');checks+=1
    assert 'brak' in (await cmd('quest kontrola Friend bandit_patrol')).lower();checks+=1
    assert '0' in await cmd('balans raport bandit_captain 250');checks+=1
    assert not any(x in str(d.conn.execute('SELECT sql FROM sqlite_master').fetchall()) for x in ('DROP TABLE','UPDATE quests SET progress')) ;checks+=1
    from systems.live_content_v1204 import LiveContentV1204,blank
    from systems.admin_guardian3_v3700 import (_build_region,_add_region_mob,
        _add_region_npc,_add_region_shop,_add_region_quest)
    live=object.__new__(LiveContentV1204);live.draft=blank();live.active=blank()
    _build_region(live,'wyprawa','Wyprawa Testowa',120,6);checks+=1
    _add_region_mob(live,'wyprawa',['live_wyprawa_wilk','Wilk',1200,130,400,2]);checks+=1
    _add_region_npc(live,'wyprawa',['live_wyprawa_kupiec','Kupiec wyprawy',3,'kupiec','Witaj wedrowcze.']);checks+=1
    _add_region_npc(live,'wyprawa',['live_wyprawa_dawca','Zleceniodawca wyprawy',4,'zleceniodawca','Podejmij wyprawe.']);checks+=1
    _add_region_shop(live,'wyprawa',[3,'healing_potion,soul_shard']);checks+=1
    _add_region_quest(live,'wyprawa',['live_wyprawa_quest','Polowanie','Zleceniodawca wyprawy','live_wyprawa_wilk',5,100]);checks+=1
    assert live.draft['npcs']['live_wyprawa_dawca']['quest']=='live_wyprawa_quest' and live.validate(live.draft);checks+=1
    prev=copy.deepcopy(live.draft)
    blocked=False
    try: _add_region_npc(live,'wyprawa',['live_wyprawa_intruz','Intruz',3,'kupiec','Drugi NPC.'])
    except ValueError: blocked=True
    assert blocked, 'Two NPC in one room must fail';checks+=1
    assert live.draft==prev;checks+=1
    return checks

def run():return asyncio.run(suite())
if __name__=='__main__':print('ADMIN GUARDIAN 3:',run(),'checks PASS')
