# -*- coding: utf-8 -*-
"""OLC52-59: eight true consumers, commit/rollback, replay of older saves."""
import copy
import sqlite3
import json
from types import SimpleNamespace


def run():
    from systems.live_content_v1204 import LiveContentV1204, blank
    from systems.live_olc27_master import (
        DOMAINS, ACTIVE, uoss_desperation_factor, profession_tool_xp,
        summon_may_intercept, skill_mana_cost, quest_character_xp,
        faction_extra, shop_room_price)
    from core.classes_skills import effective_skill_mana_cost
    from data.mobs import MOB_TEMPLATES
    from data.shops import SHOPS
    from systems.world_events_v12812 import active_city_event_v12812
    checks=0
    def ok(condition, label):
        nonlocal checks
        assert condition,label
        checks+=1
    def deny(fn,label):
        nonlocal checks
        try:fn()
        except (ValueError,TypeError):checks+=1
        else:raise AssertionError('Brak walidacji: '+label)
    con=sqlite3.connect(':memory:');con.row_factory=sqlite3.Row
    con.execute('CREATE TABLE quests(quest_id TEXT,status TEXT)')
    world=SimpleNamespace(mobs={},_last_refresh_at=0.,_register_runtime_spawn=lambda *args:None)
    server=SimpleNamespace(world=world,sessions=[])
    old_templates={}
    for slug in ('basalt','echo','star','myth'):
        key='v12812_event_'+slug
        old_templates[key]=copy.deepcopy(MOB_TEMPLATES.get(key))
        if key not in MOB_TEMPLATES:
            MOB_TEMPLATES[key]={'name':'Boss testowy', 'max_hp':10000,
                'damage':200,'class_xp_reward':500,'soul_reward':50,
                'stat_reward':5,'silver':120,'damage_type':'physical',
                'attack_elements_v11339':('dark',)}
    shop_key=next(iter(SHOPS))
    # The authored basalt event may already have real XP in the full world.
    # Preserve that inherited baseline instead of assuming the 500 XP fallback.
    inherited_event_xp = MOB_TEMPLATES['v12812_event_basalt'].get('class_xp_reward')
    assert type(inherited_event_xp) is int and inherited_event_xp > 0
    boss=MOB_TEMPLATES['uoss_superboss_black_rabite_v11136']
    mob=SimpleNamespace(hp=2000000,adaptive_max_hp_v11330=0)
    service=None;again=None
    try:
        service=LiveContentV1204(SimpleNamespace(conn=con))
        ok(set(service.active['v27_rules'])==set(DOMAINS),'eight domains')
        ok(skill_mana_cost(100)==100,'mana neutral')
        ok(effective_skill_mana_cost({'mana':100},'Mag')==100,'real skill cost neutral')
        ok(effective_skill_mana_cost({'mana':100},'Wojownik')==0,'physical classes still free')
        ok(profession_tool_xp('Górnictwo',200)==200,'neutral tool reward')
        ok(summon_may_intercept('pajak',1,10000),'vanilla low-HP pet can defend')
        ok(quest_character_xp(600)==600,'neutral quest XP')
        ok(faction_extra('miners',5)==5,'neutral faction')
        ok(shop_room_price(shop_key,100)==100,'neutral shop')
        ok(uoss_desperation_factor(mob,boss)==1.0,'neutral boss')
        prior=blank();prior.pop('v27_rules')
        ok('v27_rules' in service._compat(prior),'read v26 history')
        event={'name':'Próba Ziemi','boss_name':'Golem Przysięgi',
               'city':'basalt','style':'physical','element':'earth',
               'hp':550000,'damage':2800,'silver':2100}
        service.stage_edit('event26','live_earth_trial','definicja',json.dumps(event,ensure_ascii=False))
        service.stage_edit('uoss27','black_rabite','desperation_damage_percent','250')
        service.stage_edit('fach27','Górnictwo','tool_xp_percent','175')
        service.stage_edit('summon27','pajak','intercept_min_hp_percent','35')
        service.stage_edit('magia27','global','mana_percent','150')
        service.stage_edit('event27','live_earth_trial','class_xp_reward','200000')
        service.stage_edit('event27','live_earth_trial','soul_reward','100000')
        service.stage_edit('event27','live_earth_trial','stat_reward','25000')
        service.stage_edit('fabula27','global','quest_xp_percent','225')
        service.stage_edit('frakcja27','miners','reputation_extra','70')
        service.stage_edit('sklep27',shop_key,'price_percent','130')
        ok(service.draft['v27_rules']['skills']['global']['mana_percent']==150,'draft stored')
        deny(lambda:service.stage_edit('magia27','global','mana_percent','0'),'0% mana')
        deny(lambda:service.stage_edit('summon27','pajak','intercept_min_hp_percent','101'),'hp threshold')
        deny(lambda:service.stage_edit('uoss27','not_a_boss','desperation_damage_percent','200'),'unknown UOSS')
        deny(lambda:service.stage_edit('sklep27','not_a_shop','price_percent','110'),'unknown shop')
        deny(lambda:service.stage_edit('event27','not_live_event','class_xp_reward','1000'),'unknown event')
        deny(lambda:service.stage_edit('fach27','unknown','tool_xp_percent','120'),'unknown profession')
        deny(lambda:service.stage_edit('magia27','global','mana_percent','1e3'),'numeric syntax')
        ok(skill_mana_cost(100)==100,'draft not active')
        ok(shop_room_price(shop_key,100)==100,'draft shop not active')
        ok('Aktywowano' in service.apply(server,'v27_tester'),'publish')
        ok(profession_tool_xp('Górnictwo',200)==350,'tool EXP effect')
        ok(not summon_may_intercept('pajak',34,100),'pet too weak')
        ok(summon_may_intercept('pajak',35,100),'pet healthy')
        ok(effective_skill_mana_cost({'mana':100},'Mag')==150,'real mana')
        ok(effective_skill_mana_cost({'source_mp_cost':200},'Mag')==300,'authored mana')
        ok(effective_skill_mana_cost({'mana':100},'Wojownik')==0,'physical free after publish')
        ok(quest_character_xp(400)==900,'quest XP at turn-in')
        ok(faction_extra('miners',5)==75,'reputation effect')
        ok(faction_extra('miners',0)==0,'no reward for no gain')
        ok(shop_room_price(shop_key,100)==130,'shop effect')
        ok(shop_room_price('different_room',100)==100,'unmodified shop neutral')
        max_hp=int(boss['max_hp']);mob.hp=max_hp
        ok(uoss_desperation_factor(mob,boss)==1.0,'UOSS full HP')
        mob.hp=max_hp//2
        ok(abs(uoss_desperation_factor(mob,boss)-1.75)<.0001,'UOSS half HP')
        tid='v26_event_live_earth_trial'
        ok(tid in MOB_TEMPLATES,'boss truly registered')
        ok(MOB_TEMPLATES[tid]['class_xp_reward']==200000,'boss class XP reward')
        ok(MOB_TEMPLATES[tid]['soul_reward']==100000,'boss soul XP')
        ok(MOB_TEMPLATES[tid]['stat_reward']==25000,'boss stat XP')
        ok(active_city_event_v12812(4*10800)['template_id']==tid,'real event rotation')
        ok(service.revision==1,'committed revision')
        service._remove(world)
        again=LiveContentV1204(SimpleNamespace(conn=con))
        ok(again.revision==1,'SQLite reopened')
        ok(skill_mana_cost(100)==150,'mana after restart')
        ok(MOB_TEMPLATES[tid]['class_xp_reward']==200000,'event XP after restart')
        ok(shop_room_price(shop_key,100)==130,'shop after restart')
        again.stage_edit('magia27','global','mana_percent','auto')
        again.stage_edit('event27','live_earth_trial','class_xp_reward','auto')
        ok('Aktywowano' in again.apply(server,'v27_tester'),'auto published')
        ok(skill_mana_cost(100)==100,'mana reset')
        ok(MOB_TEMPLATES[tid]['class_xp_reward']==inherited_event_xp,'event inherited XP restored')
        ok(MOB_TEMPLATES[tid]['soul_reward']==100000,'event other reward retained')
        ok(quest_character_xp(400)==900,'quest unchanged after isolated reset')
        ok(con.execute('SELECT COUNT(*) FROM live_content_history_v1204').fetchone()[0]==2,
           'history persisted')
    finally:
        for svc in (again,service):
            if svc is not None and svc._undo:svc._remove(world)
        for tid,meta in old_templates.items():
            if meta is None:MOB_TEMPLATES.pop(tid,None)
            else:MOB_TEMPLATES[tid]=meta
        con.close()
    return checks

if __name__=='__main__':
    print('OLC52-59:',run(),'PASS')
