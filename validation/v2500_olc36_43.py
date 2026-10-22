# -*- coding: utf-8 -*-
"""OLC 36-43 integration: real catalog installs, revisions, rollback and safety."""
import copy
import json
import sqlite3
from types import SimpleNamespace

def run():
    from systems.live_content_v1204 import LiveContentV1204
    from systems.live_olc24_revolution import (stage_story_arc, ACTIVE, extra_cap_value,
        summon_factor, uoss_lockout_hours)
    from systems.live_olc25_workflows import profession_package, batch, summary
    from data.rooms import ROOMS
    from data.mobs import MOB_TEMPLATES
    from data.quests import QUESTS
    from data.crafting_recipes import CRAFT_RECIPES
    from core.bootstrap_economy_professions import PROFESSION_RANK_NAMES
    from systems.world_events_v12812 import active_city_event_v12812
    checks=0
    def ok(expression, label):
        nonlocal checks
        assert expression,label
        checks+=1
    def deny(func, label):
        nonlocal checks
        try:func()
        except (ValueError,TypeError):checks+=1
        else:raise AssertionError('Nie odrzucono: '+label)
    conn=sqlite3.connect(':memory:');conn.row_factory=sqlite3.Row
    conn.execute('CREATE TABLE quests(quest_id TEXT, status TEXT)')
    world=SimpleNamespace(mobs={},_last_refresh_at=0.,_register_runtime_spawn=lambda *a:None)
    server=SimpleNamespace(world=world,sessions=[])
    service=LiveContentV1204(SimpleNamespace(conn=conn))
    before=copy.deepcopy(service.draft)
    boss_id='uoss_superboss_black_rabite_v11136'
    base_boss=copy.deepcopy(MOB_TEMPLATES[boss_id])
    event_id='v12812_event_basalt'
    event_existed=event_id in MOB_TEMPLATES
    if not event_existed:
        # The real server registers city bosses during server.py startup.
        # Standalone tests install a representative base template.
        MOB_TEMPLATES[event_id]={'max_hp':10000,'damage':500,'damage_type':'physical','attack_elements_v11339':('dark',),'name':'Wydarzenie testowe'}
    base_event=copy.deepcopy(MOB_TEMPLATES[event_id])
    room_orig=copy.deepcopy(ROOMS['square'])
    orig_quest=copy.deepcopy(QUESTS['bandit_patrol'])
    try:
        ok('OLC 36' in summary(service),'panel NVDA')
        for key,val in [('gold','100'),('silver','0'),('mithril','0'),('source_xp','18900001'),('lockout_hours','36')]:
            service.stage_edit('uoss','black_rabite',key,val);ok(True,'uoss '+key)
        deny(lambda:service.stage_edit('uoss','black_rabite','source_xp','0'),'source XP zero')
        deny(lambda:service.stage_edit('uoss','black_rabite','invalid_field','7'),'UOSS unknown')
        service.stage_edit('przywolany','pajak','regen_percent','200')
        ok(summon_factor('pajak','regen_percent')==100,'draft not live')
        deny(lambda:service.stage_edit('przywolany','pajak','regen_percent','0'),'regen zero')
        service.stage_edit('capkroki','global','step_extra_exp',json.dumps([100]*80))
        deny(lambda:service.stage_edit('capkroki','global','step_extra_exp',json.dumps([100]*81)),'80 groups max')
        service.stage_edit('event','basalt','style','magic')
        service.stage_edit('event','basalt','element','fire')
        deny(lambda:service.stage_edit('event','basalt','style','rocket'),'style invalid')
        service.stage_edit('kontrola','global','event_hp_percent','180')
        service.stage_edit('kontrola','global','event_damage_percent','140')
        deny(lambda:service.stage_edit('kontrola','global','event_hp_percent','50'),'event HP low')
        recipe='live_v25_sugar_recipe'; profession='live_v25_sugar'
        pakiet=' | '.join([
            profession,'Cukiernictwo V25','live_v25_sugar_tool','live_v25_sugar_type',
            'Wałek cukiernika','square','500','Wałek do wyrobów.',
            recipe,'Tabliczka v25',profession,'iron_ingot','{"iron_ore":2}',
            '1','1','Autorska receptura doświadczalna.'])
        ok('DRAFT' in profession_package(service,pakiet),'profession package')
        pre=copy.deepcopy(service.draft)
        deny(lambda:profession_package(service,pakiet.replace('iron_ingot','non_existing_item')),'atomic duplicated invalid bundle')
        ok(service.draft==pre,'package unchanged on invalid')
        service.stage_new_skill('live_v25_moon','Mag','Księżycowy podmuch',
            'damage',30,50,1.8,'intelligence','Nowy czar.')
        ok('DRAFT' in batch(service,'skille',json.dumps({'live_v25_moon':{'mana':35,'name':'Księżycowy Blask'}},ensure_ascii=False)),'batch skill')
        ok(service.draft['skills']['live_v25_moon']['mana']==35,'skill actual staged')
        pre=copy.deepcopy(service.draft)
        deny(lambda:batch(service,'skille',json.dumps({'live_v25_moon':{'mana':40,'invalid_field':'no'}})),'invalid skills batch')
        ok(service.draft==pre,'skills atomic invalid')
        ok('DRAFT' in batch(service,'pokoje',json.dumps({'square':{'name':'Główny Plac v25'}})),'room batch')
        ok(ROOMS['square']['name']==room_orig['name'],'room draft not live')
        ok('quest' in stage_story_arc(service,json.dumps({'quests':{'bandit_patrol':{
            'description':'Patrol bandytów po aktualizacji v25.',
            'reward_gold':100}}})), 'story reward and desc')
        ok(QUESTS['bandit_patrol']==orig_quest,'story staged not live')
        ok('Aktywowano' in service.apply(server,'v25_admin'),'publish')
        ok(uoss_lockout_hours('black_rabite')==36,'UOSS lockout runtime')
        ok(MOB_TEMPLATES[boss_id]['source_xp']==18900001,'UOSS exact XP runtime')
        ok(MOB_TEMPLATES[boss_id]['olc_uoss_currency_override']=={'gold':100,'silver':0,'mithril':0},'UOSS payout metadata')
        ok(summon_factor('pajak','regen_percent')==200,'summon regen runtime')
        ok(extra_cap_value(800)==80000,'80 brackets x 10 levels')
        ok(active_city_event_v12812(0)['style']=='magic','event style runtime')
        ok(active_city_event_v12812(0)['element']=='fire','event element runtime')
        ok(MOB_TEMPLATES[event_id]['max_hp']==base_event['max_hp']*180//100,'event boss HP')
        ok(MOB_TEMPLATES[event_id]['damage']==base_event['damage']*140//100,'event boss dmg')
        ok(ROOMS['square']['name']=='Główny Plac v25','published room name')
        ok(QUESTS['bandit_patrol']['description']=='Patrol bandytów po aktualizacji v25.','published real quest desc')
        ok(PROFESSION_RANK_NAMES['Cukiernictwo V25'],'profession published')
        ok(CRAFT_RECIPES[recipe]['profession']=='Cukiernictwo V25','recipe published')
        # Restart: serialized revisions must survive and no duplicate multipliers.
        service._remove(world)
        service2=LiveContentV1204(SimpleNamespace(conn=conn))
        ok(service2.revision==1,'SQLite revision')
        ok(extra_cap_value(800)==80000,'SQLite cap 80 survives')
        ok(MOB_TEMPLATES[event_id]['max_hp']==base_event['max_hp']*180//100,'restart no double scaling')
        service2.stage_edit('uoss','black_rabite','gold','auto')
        ok('Aktywowano' in service2.apply(server,'v25_admin'),'single-field auto')
        ok('gold' not in MOB_TEMPLATES[boss_id]['olc_uoss_currency_override'],'reset gold')
        ok(MOB_TEMPLATES[boss_id]['source_xp']==18900001,'source XP untouched')
    finally:
        try:
            # remove installed snapshot regardless of phase of test
            if service and service._undo:service._remove(world)
            if 'service2' in locals() and service2._undo:service2._remove(world)
        finally:
            MOB_TEMPLATES[boss_id]=base_boss
            if event_existed: MOB_TEMPLATES[event_id]=base_event
            else: MOB_TEMPLATES.pop(event_id,None)
            ROOMS['square']=room_orig
            QUESTS['bandit_patrol']=orig_quest
    return checks

if __name__=='__main__':
    print(f'V25 OLC36–43: {run()} PASS')
