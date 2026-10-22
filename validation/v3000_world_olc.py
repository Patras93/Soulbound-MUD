# -*- coding: utf-8 -*-
"""v30: prawdziwe pokoje i moby 401-800 oraz fazy UOSS i custom summon."""
import copy
import sqlite3
from types import SimpleNamespace


def run():
    from world.dynamic_content import EXP_AREAS
    from world.v3000_endgame_401_800 import REGIONS, install
    from data.rooms import ROOMS
    from data.mobs import MOB_TEMPLATES
    from systems.content_registry import MOB_SPAWNS
    from core.mines_threat import EXP_ZONE_AREA_ID,EXP_AREA_TARGET_POWER
    from core.progression_resources import v0190_mob_stage
    from player.session_mixins.exp_terrain import SessionExpTerrainMixin
    from validation.v2910_dynamic_exp_areas import FakeSession
    from player.session_mixins.era_sky_v1700 import SUMMONS,SUMMON_MANA,SessionSkyV1700Mixin
    from systems.live_content_v1204 import LiveContentV1204
    from systems.live_olc29_creation import boss_pulse_factor, quest_ending_text, ACTIVE
    checks=0
    def ok(value,message):
        nonlocal checks
        assert value,message
        checks+=1
    areas={a['id']:a for a in EXP_AREAS}
    spawn_counts={}
    for rid,mid in MOB_SPAWNS:spawn_counts[rid]=spawn_counts.get(rid,0)+1
    old_end=ROOMS['world_crown_summit']['exits']['up']
    ok(old_end=='v3000_scarlet_1','fizyczne wyjscie z Korony')
    ok(len(REGIONS)==4,'cztery regiony')
    for slug,zone,low,high,parent,entr,ret,titles,names,boss,element in REGIONS:
        area=areas['v3000_'+slug]
        ok(area['difficulty']==f'endgame {low}-{high}','pasmo '+slug)
        ok(EXP_ZONE_AREA_ID[zone]==area['id'],'wskaznik strefy '+slug)
        ok(EXP_AREA_TARGET_POWER[area['id']]==low,'prog zagrozenia '+slug)
        ok(ROOMS[parent]['exits'][entr]==f'v3000_{slug}_1','wejscie '+slug)
        ok(ROOMS[f'v3000_{slug}_1']['exits'][ret]==parent,'powrot '+slug)
        for i in range(1,7):
            rid=f'v3000_{slug}_{i}'
            room=ROOMS[rid]
            ok(room['zone']==zone,'strefa '+rid)
            ok(low<=room['generator_level']<=high,'level pokoju '+rid)
            if i<6:ok(room['exits']['north']==f'v3000_{slug}_{i+1}','przejscie north '+rid)
            if i>1:ok(room['exits']['south']==f'v3000_{slug}_{i-1}','przejscie south '+rid)
            ok(spawn_counts.get(rid,0)>=1,'przeciwnicy w '+rid)
            ok(not room.get('trap'),'zero pulapek '+rid)
        for j in range(1,5):
            mob=MOB_TEMPLATES[f'v3000_{slug}_mob_{j}']
            ok(low<=v0190_mob_stage(mob)<=high,'mobil etap '+slug)
            ok(mob['class_xp_reward']>0 and mob['soul_reward']>0,'nagrody '+slug)
        last=MOB_TEMPLATES[f'v3000_{slug}_boss']
        ok(v0190_mob_stage(last)==high,'finał poziomu '+slug)
        ok(last['world_boss'] and last['class_xp_reward']>0,'prawdziwy boss '+slug)
        ok((f'v3000_{slug}_6',f'v3000_{slug}_boss') in MOB_SPAWNS,'spawn bossa '+slug)
        for sample in (low, (low+high)//2, high):
            session=FakeSession(sample)
            first=session.recommended_exp_areas_v2910()[0]
            ok(first['id']==area['id'],f'polecane {sample} {slug}')
    ok('world_crown' not in [a['id'] for a in FakeSession(401).recommended_exp_areas_v2910()],'nie polecaj starego regionu 401')
    ok(areas['v3000_eternal']['id'] in [a['id'] for a in FakeSession(800).recommended_exp_areas_v2910()],'endgame 800')
    # No duplicate spawns or rooms on a repeated installer invocation.
    count=len(MOB_SPAWNS); rooms_before=len(ROOMS)
    from core.mines_threat import EXP_AREA_BASE_CATEGORY,GUIDE_DESTINATION_ALIASES
    ok(install(ROOMS,MOB_TEMPLATES,MOB_SPAWNS,EXP_AREAS,EXP_ZONE_AREA_ID,EXP_AREA_BASE_CATEGORY,GUIDE_DESTINATION_ALIASES,EXP_AREA_TARGET_POWER)==(), 'idempotent reinstall')
    ok(count==len(MOB_SPAWNS) and rooms_before==len(ROOMS),'no duplicates')
    # Hot edits are persisted in the *existing* SQLite DRAFT/revision service.
    c=sqlite3.connect(':memory:');c.row_factory=sqlite3.Row
    c.execute('CREATE TABLE quests(quest_id TEXT,status TEXT)')
    world=SimpleNamespace(mobs={},_last_refresh_at=0.,_register_runtime_spawn=lambda *_:None)
    server=SimpleNamespace(world=world,sessions=[])
    summon_id='live_stormwolf_v30'
    before_summons=copy.deepcopy(ACTIVE['summons'])
    try:
        svc=LiveContentV1204(SimpleNamespace(conn=c))
        boss_row={'cycle':3,'extra_damage_percent':180,'phase_threshold_percent':30,'phase_damage_percent':170}
        pet_row={'name':'Wilk Burzy','class':'Druid','mana':123,'kind':'magic','power':95,'materials':{},'hp_percent':170,'attack_percent':130}
        import json
        svc.stage_edit('boss29','black_rabite','definicja',json.dumps(boss_row))
        svc.stage_edit('summon29',summon_id,'definicja',json.dumps(pet_row))
        svc.stage_edit('fabula29','bandit_patrol','definicja',json.dumps(
            {'text':'Wybor strazy.', 'ending':'Szlak bandytow zostal obroniony.'}))
        ok(summon_id not in SUMMONS,'no draft leak')
        ok('Aktywowano' in svc.apply(server,'test30'),'publish')
        ok(summon_id in SUMMONS and SUMMON_MANA[summon_id]==123,'summon real registered')
        ok(quest_ending_text('bandit_patrol')=='Szlak bandytow zostal obroniony.', 'story published in runtime')
        ok(abs(SUMMONS[summon_id][4]-.95*1.3)<.00001,'attack actual ratio')
        fake=SimpleNamespace(hp=1000,max_hp=1000)
        template={'uoss_unique_superboss_key':'black_rabite','max_hp':1000}
        ok(boss_pulse_factor(fake,template)==1.0,'normal fase no pulse')
        fake.hp=200
        ok(abs(boss_pulse_factor(fake,template)-1.7)<.00001,'low HP phase real multiplier')
        ok(abs(boss_pulse_factor(fake,template)-3.06)<.00001,'pulse combines with phase')
        fake_pet=SimpleNamespace(max_hp=lambda:1000,character=SimpleNamespace(character_level=200))
        hp=SessionSkyV1700Mixin._v1702_summon_max_hp(fake_pet,summon_id,1,1000)
        ok(hp>=1000,'custom HP factor applies to summon')
        second=LiveContentV1204(SimpleNamespace(conn=c))
        ok(second.active['v29_rules']['summons'][summon_id]['hp_percent']==170,'SQLite restart loads author settings')
        ok(second.active['v29_rules']['bosses']['black_rabite']['phase_threshold_percent']==30,'SQLite boss phase')
        ok(second.active['v29_rules']['story']['bandit_patrol']['ending']=='Szlak bandytow zostal obroniony.','SQLite story ending')
        second.stage_edit('boss29','black_rabite','definicja','auto')
        ok('Aktywowano' in second.apply(server,'test30'),'publish rollback of one setting')
        ok(boss_pulse_factor(SimpleNamespace(hp=100,max_hp=1000),template)==1,'one setting reset')
    finally:
        try:
            if 'second' in locals():second._remove(world)
            if 'svc' in locals():svc._remove(world)
        except Exception as exc:
            raise AssertionError("v30 OLC cleanup failure") from exc
        ACTIVE['summons'].clear();ACTIVE['summons'].update(before_summons)
        SUMMONS.pop(summon_id,None);SUMMON_MANA.pop(summon_id,None)
        c.close()
    return checks

if __name__=='__main__':print(f'V30.00.0 EXPOWISKA + OLC: {run()} checks PASS')
