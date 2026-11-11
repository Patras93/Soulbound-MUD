# -*- coding: utf-8 -*-
"""OLC44-51 integration: eight areas, real consumers, old saves, rollback."""
import copy
import json
import sqlite3
from types import SimpleNamespace


def run():
    from systems.live_content_v1204 import LiveContentV1204, blank
    from systems.live_olc26_world import (ACTIVE, profession_xp_bonus,
         summon_intercept_chance, summon_incoming_damage, faction_reward,
         shop_price, conflicting_quests, uoss_berserk_factor)
    from systems.world_events_v12812 import active_city_event_v12812
    from systems.live_olc25_workflows import bundle_new_skills
    from data.mobs import MOB_TEMPLATES
    from data.quests import QUESTS
    from core.classes_skills import CLASS_SKILLS
    checks=0
    def ok(value, label):
        nonlocal checks
        assert value, label
        checks+=1
    def deny(func,label):
        nonlocal checks
        try:func()
        except (ValueError,TypeError):checks+=1
        else:raise AssertionError('Nie odrzucono: '+label)
    conn=sqlite3.connect(':memory:');conn.row_factory=sqlite3.Row
    conn.execute('CREATE TABLE quests(quest_id TEXT, status TEXT)')
    world=SimpleNamespace(mobs={}, _last_refresh_at=0., _register_runtime_spawn=lambda *args:None)
    server=SimpleNamespace(world=world,sessions=[])
    old_templates={}
    for slug in ('basalt','echo','star','myth'):
        tid='v12812_event_'+slug
        if tid not in MOB_TEMPLATES:
            MOB_TEMPLATES[tid]={'name':'Testowy boss','max_hp':10000,'damage':200,
                                'silver':100,'damage_type':'physical','attack_elements_v11339':('dark',)}
            old_templates[tid]=None
        else:old_templates[tid]=copy.deepcopy(MOB_TEMPLATES[tid])
    svc=None; restarted=None
    try:
        svc=LiveContentV1204(SimpleNamespace(conn=conn))
        ok(set(svc.draft['v26_rules'])==set(ACTIVE),'v26 blank domains')
        ok(profession_xp_bonus('Górnictwo',100)==100,'vanilla profession')
        ok(shop_price(100)==100,'vanilla shop price')
        ok(faction_reward('miners',100)==100,'vanilla faction')
        ok(summon_intercept_chance('pajak')==.32,'vanilla summon')
        ok(not conflicting_quests('bandit_patrol'),'vanilla story')
        boss=MOB_TEMPLATES['uoss_superboss_black_rabite_v11136']
        fake=SimpleNamespace(hp=3000000,adaptive_max_hp_v11330=0)
        ok(uoss_berserk_factor(fake,boss)==1.0,'vanilla UOSS')
        # Legacy v25 JSON payload without v26 section must be readable.
        old=blank();old.pop('v26_rules')
        ok('v26_rules' in svc._compat(old),'backward compatibility')
        # New eight domains: 1 UOSS, 2 profession, 3 summons, 4 real skille,
        # 5 custom event, 6 branching narrative, 7 faction, 8 shop economy.
        svc.stage_edit('uoss26','black_rabite','berserk_hp_percent','30')
        svc.stage_edit('uoss26','black_rabite','berserk_damage_percent','180')
        deny(lambda:svc.stage_edit('uoss26','black_rabite','berserk_damage_percent','0'),'0 attack boost')
        svc.stage_edit('fach26','Górnictwo','xp_percent','150')
        deny(lambda:svc.stage_edit('fach26','Nieistniejaca','xp_percent','120'),'unknown profession')
        svc.stage_edit('summon26','pajak','intercept_chance_percent','70')
        svc.stage_edit('summon26','pajak','incoming_damage_percent','50')
        deny(lambda:svc.stage_edit('summon26','pajak','incoming_damage_percent','-9'),'negative damage percent')
        skills=[{'id':'live_v26_flame','class':'Mag','name':'Ognisty deszcz v26',
                 'kind':'aoe_damage','unlock':50,'mana':150,'mult':1.5,
                 'scale':'intelligence','desc':'Nowa w pełni walcząca magia.',
                 'element':'fire','status':{'kind':'burn','chance':.5,'ticks':2}}]
        ok('DRAFT' in bundle_new_skills(svc,json.dumps(skills,ensure_ascii=False)),'batch new skill')
        ok(svc.draft['skills']['live_v26_flame']['olc_status']['kind']=='burn','real skill status')
        before=copy.deepcopy(svc.draft)
        deny(lambda:bundle_new_skills(svc,json.dumps(skills)),'duplicate skills must fail')
        ok(svc.draft==before,'bundle atomic rollback')
        event={'name':'Najazd Żelaznych Golemów','boss_name':'Golem Zmierzchu',
               'city':'basalt','style':'physical','element':'earth','hp':123456,
               'damage':3456,'silver':50000}
        svc.stage_edit('event26','live_golems','definicja',json.dumps(event,ensure_ascii=False))
        invalid=dict(event);invalid['city']='worldwide'
        deny(lambda:svc.stage_edit('event26','live_wrong','definicja',json.dumps(invalid)),'event invalid city')
        svc.stage_edit('wybor26','live_bandit_choice','questy',json.dumps(['bandit_patrol','goblin_problem']))
        deny(lambda:svc.stage_edit('wybor26','live_bad_choice','questy',json.dumps(['bandit_patrol','unknown'])),'story unknown')
        svc.stage_edit('frakcja26','miners','reputation_percent','160')
        deny(lambda:svc.stage_edit('frakcja26','not_known','reputation_percent','120'),'unknown faction')
        svc.stage_edit('ekonomia26','global','shop_price_percent','85')
        deny(lambda:svc.stage_edit('ekonomia26','global','shop_price_percent','0'),'zero shop price')
        # No runtime mutations before publish
        ok(shop_price(100)==100,'draft price ignored')
        ok(profession_xp_bonus('Górnictwo',100)==100,'draft exp ignored')
        ok(active_city_event_v12812(4*10800)['slug']=='basalt','draft event ignored')
        ok(not conflicting_quests('bandit_patrol'),'draft branches ignored')
        ok('Aktywowano' in svc.apply(server,'v26_admin'),'published v26')
        ok(shop_price(200)==170,'shop pricing consumer')
        ok(faction_reward('miners',100)==160,'faction gain consumer')
        ok(profession_xp_bonus('Górnictwo',100)==150,'profession xp consumer')
        ok(summon_intercept_chance('pajak')==.7,'summon interception consumer')
        ok(summon_incoming_damage('pajak',120)==60,'summon damage consumer')
        ok(conflicting_quests('bandit_patrol')==('goblin_problem',),'mutually exclusive stories')
        fake.hp=900000
        ok(uoss_berserk_factor(fake,boss)==1.8,'UOSS enrage low HP')
        fake.hp=2500000
        ok(uoss_berserk_factor(fake,boss)==1.0,'UOSS no enrage high HP')
        monster_id='v26_event_live_golems'
        ok(monster_id in MOB_TEMPLATES and MOB_TEMPLATES[monster_id]['damage']==3456,'real boss template')
        ok(MOB_TEMPLATES[monster_id]['max_hp']==123456 and MOB_TEMPLATES[monster_id]['silver']==50000,'event real payouts')
        next_event=active_city_event_v12812(4*10800)
        ok(next_event['slug']=='live_golems','new fifth rotation slot')
        ok(next_event['room_id']=='v12812_city_basalt_gate','existing safe arena')
        ok(next_event['template_id']==monster_id,'boss template id')
        ok(any(sk['id']=='live_v26_flame' for sk in CLASS_SKILLS['Mag']),'new spell in real class')
        svc._remove(world)
        restarted=LiveContentV1204(SimpleNamespace(conn=conn))
        ok(restarted.revision==1,'SQLite revision survives')
        ok(shop_price(200)==170,'world after restart')
        ok(active_city_event_v12812(4*10800)['slug']=='live_golems','event after restart')
        ok(profession_xp_bonus('Górnictwo',100)==150,'profession after restart')
        # Removing one field does not erase other modes
        restarted.stage_edit('ekonomia26','global','shop_price_percent','auto')
        restarted.stage_edit('frakcja26','miners','reputation_percent','auto')
        ok('Aktywowano' in restarted.apply(server,'v26_admin'),'publish auto rollback')
        ok(shop_price(200)==200 and faction_reward('miners',100)==100,'auto resets')
        ok(summon_intercept_chance('pajak')==.7,'other branches preserved')
        ok(active_city_event_v12812(4*10800)['slug']=='live_golems','event survives other auto')
    finally:
        for service in (restarted,svc):
            if service and service._undo: service._remove(world)
        for tid,before in old_templates.items():
            if before is None:MOB_TEMPLATES.pop(tid,None)
            else:MOB_TEMPLATES[tid]=before
    return checks

if __name__=='__main__':
    print('OLC 44-51:',run(),'PASS')
