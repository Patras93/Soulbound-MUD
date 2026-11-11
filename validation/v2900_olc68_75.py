# -*- coding: utf-8 -*-
"""OLC68–75: eight real consumers, draft/commit/restart/revert/validation."""
import copy
import json
import sqlite3
from types import SimpleNamespace


def run():
    from systems.live_content_v1204 import LiveContentV1204, blank
    from systems.live_olc29_creation import (ACTIVE,CATEGORIES,preview,package,
        boss_pulse_factor,authored_arena,quest_choice_text,guild_level_bonus,trade_price)
    from player.session_mixins.era_sky_v1700 import SUMMONS,SUMMON_MANA
    from systems.world_events_v12812 import active_city_event_v12812
    from world.uoss_superbosses import UOSS_SUPERBOSS_ENCOUNTERS_V11134
    from data.rooms import ROOMS
    from data.mobs import MOB_TEMPLATES
    checks=0
    def ok(result,name):
        nonlocal checks
        assert result,name
        checks+=1
    def deny(action,name):
        nonlocal checks
        try:action()
        except (ValueError,TypeError):checks+=1
        else:raise AssertionError('accepted invalid '+name)
    c=sqlite3.connect(':memory:');c.row_factory=sqlite3.Row
    c.execute('CREATE TABLE quests(quest_id TEXT,status TEXT)')
    world=SimpleNamespace(mobs={},_last_refresh_at=0.,_register_runtime_spawn=lambda *_:None)
    server=SimpleNamespace(world=world,sessions=[])
    svc=None;again=None
    rid='live_hall_v29';mid='live_boss_v29';event_id='live_event_v29';kind='live_wolf_v29'
    profid='live_prof_v29';recipeid='live_recipe_v29';skillid='live_skill_v29'
    original={key:copy.deepcopy(MOB_TEMPLATES.get(key)) for key in
        ('v12812_event_basalt','v12812_event_echo','v12812_event_star','v12812_event_myth')}
    try:
        for slug in ('basalt','echo','star','myth'):
            tid='v12812_event_'+slug
            if tid not in MOB_TEMPLATES:
                MOB_TEMPLATES[tid]={'name':'test','max_hp':100000,'damage':3000,'class_xp_reward':1000,
                    'soul_reward':100,'stat_reward':50,'silver':900,'damage_type':'physical'}
        svc=LiveContentV1204(SimpleNamespace(conn=c))
        ok(set(svc.active['v29_rules'])==set(CATEGORIES),'8 domains')
        ok(trade_price(rid,200,'sell')==200,'neutral trade')
        ok(guild_level_bonus(800)==0,'neutral guild')
        ok(quest_choice_text('bandit_patrol')=='','neutral story')
        ok(authored_arena(event_id,'default')=='default','neutral event')
        ok(kind not in SUMMONS,'custom summon absent')
        ok('v29_rules' in LiveContentV1204._compat({}),'old revision compatibility')
        ok('v29_rules' in LiveContentV1204._compat({**blank(),'v29_rules':blank()['v29_rules']}),'new compatibility')
        svc.stage_room(rid,45,'Sala Legend','Własna arena legend','Pogranicze')
        svc.stage_edit('uoss29','black_rabite','definicja',json.dumps({'cycle':3,'extra_damage_percent':180}))
        svc.stage_edit('summon29',kind,'definicja',json.dumps({'name':'Wilk Pradawny','class':'Druid','mana':105,
            'kind':'physical','power':90,'materials':{}}))
        svc.stage_edit('gildia29','global','definicja',json.dumps({'level_step':10,'bonus_per_step':2,'maximum_bonus':50}))
        svc.stage_edit('swiat29',rid,'definicja',json.dumps({'buy_percent':110,'sell_percent':135}))
        svc.stage_edit('fabula29','bandit_patrol','definicja',json.dumps({'text':'Obrona przełęczy zmienia los bandytów.'}))
        svc.stage_mob(mid,'Mistrz Areny',45,120000,900,6000)
        svc.stage_spawn(rid,mid)
        svc.stage_new_profession_and_tool_v2400(profid,'Sztuka Kamienia','live_tool_v29','live_tool_kind_v29',
            'Dłuto Runiczne',rid,100,'Narzędzie obróbki kamienia')
        svc.stage_new_profession_recipe_v2400(recipeid,'Rzeźba Pradawna',profid,'iron_ingot',
            json.dumps({'iron_ore':2}),1,1,'Wytwarzanie ze skały')
        svc.stage_edit('fach29',recipeid,'definicja',json.dumps({'label':'Tworzenie pradawnych rzeźb'}))
        svc.stage_new_skill(skillid,'Mag','Cios Rytualny','damage',1,100,1.3,'intelligence','Atak żywiołów')
        svc.stage_edit('skill29',skillid,'definicja',json.dumps({'name':'Rytualny Ogień'}))
        ev={'name':'Obrona Bramy','boss_name':'Mistrz Bram','city':'basalt','style':'physical','element':'earth',
            'hp':250000,'damage':500,'silver':5000}
        svc.stage_edit('event26',event_id,'definicja',json.dumps(ev))
        svc.stage_edit('event29',event_id,'definicja',json.dumps({'arena':rid}))
        ok(kind not in SUMMONS,'draft not installed')
        ok('Aktualnie:' in preview(svc,'summon29',kind,'definicja') or 'DRAFT:' in preview(svc,'summon29',kind,'definicja'),'preview')
        before=copy.deepcopy(svc.draft)
        deny(lambda:svc.stage_edit('summon29','live_bad_v29','definicja',json.dumps({'name':'bad','class':'Druid','mana':0,
            'kind':'physical','power':90,'materials':{}})),'reject missing')
        ok(svc.draft==before,'invalid draft atomic')
        for category,key,record in (
            ('summon29',kind,{'name':'n','class':'Assassin','mana':10,'kind':'physical','power':80,'materials':{}}),
            ('event29',event_id,{'arena':'unknown_place'}),
            ('gildia29','global',{'level_step':0,'bonus_per_step':1,'maximum_bonus':90}),
            ('swiat29',rid,{'buy_percent':0,'sell_percent':100}),
            ('fabula29','missing_quest',{'text':'no'}),
        ):
            deny(lambda cat=category,k=key,row=record:svc.stage_edit(cat,k,'definicja',json.dumps(row)),category)
        ok(svc.draft==before,'all invalid drafts atomic')
        ok('Aktywowano' in svc.apply(server,'test29'),'publish')
        ok(SUMMONS[kind][0]=='Wilk Pradawny','summon runtime registry')
        ok(SUMMON_MANA[kind]==105,'mana runtime registry')
        ok(SUMMONS[kind][4]==0.90,'pet owner scaling ratio')
        from player.session_mixins.era_sky_v1700 import SessionSkyV1700Mixin
        pet_hp=SessionSkyV1700Mixin._v1702_summon_max_hp(
            SimpleNamespace(max_hp=lambda:2000),kind,level=10)
        ok(pet_hp>2000*0.65,'new summon uses owner HP and level scaling')
        ok(authored_arena(event_id,'default')==rid,'custom arena location')
        ev_ids=[active_city_event_v12812(10800*i)['slug'] for i in range(8)]
        ok(event_id in ev_ids,'scheduled authored event')
        ok(any(active_city_event_v12812(10800*i)['room_id']==rid for i in range(8)),'actual event arena')
        ok(quest_choice_text('bandit_patrol').startswith('Obrona'),'narrative text')
        ok(guild_level_bonus(50)==10,'guild level progression')
        ok(guild_level_bonus(800)==50,'guild bonus ceiling')
        ok(trade_price(rid,100,'buy')==110,'local purchase')
        ok(trade_price(rid,100,'sell')==135,'local sale')
        ok(trade_price('non_custom',100,'buy')==100,'elsewhere neutral')
        boss=SimpleNamespace(hp=500000)
        template={'uoss_unique_superboss_key':'black_rabite'}
        ok(boss_pulse_factor(boss,template)==1.0,'pulse 1')
        ok(boss_pulse_factor(boss,template)==1.0,'pulse 2')
        ok(abs(boss_pulse_factor(boss,template)-1.8)<1e-8,'pulse 3')
        ok(boss_pulse_factor(boss,{'name':'normal'})==1,'normal mobs unaffected')
        from data.crafting_recipes import CRAFT_RECIPES
        from core.classes_skills import CLASS_SKILLS
        from data.quests import QUESTS
        ok(CRAFT_RECIPES[recipeid]['name']=='Tworzenie pradawnych rzeźb','real profession action')
        ok(any(x['name']=='Rytualny Ogień' for x in CLASS_SKILLS['Mag']),'real class skill catalog')
        ok('Obrona przełęczy' in QUESTS['bandit_patrol']['description'],'real narrative description')
        ok(mid in MOB_TEMPLATES,'custom boss actually installed')
        ok(rid in ROOMS,'arena actually installed')
        svc._remove(world)
        ok(kind not in SUMMONS,'custom summon rollback')
        ok(recipeid not in CRAFT_RECIPES,'new recipe rollback')
        ok(not any(x['id']==skillid for x in CLASS_SKILLS['Mag']),'new skill rollback')
        ok(guild_level_bonus(50)==0,'gild bonus reset')
        again=LiveContentV1204(SimpleNamespace(conn=c))
        ok(kind in SUMMONS and SUMMON_MANA[kind]==105,'restart summon persisted')
        ok(authored_arena(event_id,'default')==rid,'restart arena persisted')
        ok(trade_price(rid,100,'sell')==135,'restart local shop')
        # Undo a single field; published rooms and event still exist.
        again.stage_edit('gildia29','global','definicja','auto')
        again.stage_edit('swiat29',rid,'definicja','auto')
        again.apply(server,'test29')
        ok(guild_level_bonus(50)==0,'reset guild')
        ok(trade_price(rid,100,'sell')==100,'reset trade')
        ok(kind in SUMMONS,'other custom summon remains')
        # Atomic eight-system pack rejects invalid cross-refs without any leftover draft.
        before=copy.deepcopy(again.draft)
        deny(lambda:package(again,json.dumps({'summons':{'live_bad_v29':{'name':'bad','class':'Mag','mana':200,
             'kind':'magic','power':150,'materials':{'missing_item':1}}}})),'atomic package validation')
        ok(before==again.draft,'package rollback')
        ok('OLC29' in package(again,json.dumps({'story':{'bandit_patrol':{'text':'Nowy los.'}}})),
           'package valid')
        ok(again.draft['v29_rules']['story']['bandit_patrol']['text']=='Nowy los.','package staged')
        again._remove(world)
        ok(kind not in SUMMONS,'cleanup post restart')
    finally:
        if again and again._undo:again._remove(world)
        if svc and svc._undo:svc._remove(world)
        from systems.live_olc29_creation import sync
        sync(blank()['v29_rules'])
        for key,val in original.items():
            if val is None:MOB_TEMPLATES.pop(key,None)
            else:MOB_TEMPLATES[key]=val
    print(f'OLC68-75 v29: {checks} PASS')
    return checks

if __name__=='__main__':run()
