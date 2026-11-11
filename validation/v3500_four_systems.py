# -*- coding: utf-8 -*-
"""OLC35 real effects: phase AI, crafted actions, guild wars, cities, revision/rollback."""
import copy
import json
import sqlite3
from types import SimpleNamespace


def run():
    from systems.live_content_v1204 import LiveContentV1204, blank
    from systems.live_olc35_finale import (ACTIVE, package, boss_action, start_war, war_status,
        war_boss_kill, city_upgrade, city_level, city_bonus, city_config, war_config, validate, city_craft_bonus)
    from world.uoss_superbosses import UOSS_SUPERBOSS_ENCOUNTERS_V11134
    from data.crafting_recipes import CRAFT_RECIPES
    checks=0
    def ok(condition, label):
        nonlocal checks
        assert condition,label
        checks+=1
    def deny(func, label):
        nonlocal checks
        try:func()
        except (ValueError,TypeError):checks+=1
        else:raise AssertionError('Accepted invalid '+label)

    boss=next(iter(UOSS_SUPERBOSS_ENCOUNTERS_V11134))
    recipe=next(key for key,row in CRAFT_RECIPES.items() if row.get('ingredients') and row.get('tool_item_id') and row.get('tool_type'))
    db=sqlite3.connect(':memory:');db.row_factory=sqlite3.Row
    db.execute('CREATE TABLE quests(quest_id TEXT,status TEXT)')
    db.execute('CREATE TABLE player_clans(id INTEGER PRIMARY KEY, treasury INTEGER NOT NULL DEFAULT 0)')
    db.execute('INSERT INTO player_clans(id,treasury) VALUES(?,?)',(10,1000000))
    server=SimpleNamespace(world=SimpleNamespace(mobs={}),sessions=[])
    service=LiveContentV1204(SimpleNamespace(conn=db))
    old=dict(service.active)
    try:
        ok('v35_rules' in blank(),'blank has v35')
        ok(service.active['v35_rules']==blank()['v35_rules'],'neutral default')
        ok('v35_rules' in service._compat({}),'old SQLite')
        neutral=SimpleNamespace(hp=20,max_hp=100)
        ok(boss_action(neutral,{'uoss_unique_superboss_key':boss})==1.0,'neutral boss')
        rules={
            'bosses':{boss:{'phases':[{'below_hp':50,'every':2,'action':'strike','power':180},
                                     {'below_hp':20,'every':3,'action':'heal','power':4}]}},
            'activities':{'live_gornicze_przetwarzanie':{'name':'Nowa czynność kowalska','recipe':recipe}},
            'wars':{'global':{'bosses_needed':2,'reward_silver':10000,'cooldown_minutes':120}},
            'cities':{'global':{'max_level':3,'base_cost_silver':100,'bonus_per_level':2}},
        }
        ok(validate(rules, payload=service.draft),'valid config')
        ok('Pakiet35 DRAFT' in package(service,json.dumps(rules)),'package stages')
        ok(service.active['v35_rules']['bosses']=={},'draft not live')
        snapshot=copy.deepcopy(service.draft)
        deny(lambda:service.stage_edit('boss35',boss,'definicja',json.dumps({'phases':[{'below_hp':55,'every':0,'action':'strike','power':500}]})),'invalid boss')
        deny(lambda:service.stage_edit('czyn35','live_test_no_item','definicja',json.dumps({'name':'Oszustwo','recipe':'nothing'})),'bad recipe')
        deny(lambda:package(service,json.dumps({'wars':{'global':{'bosses_needed':0,'reward_silver':10,'cooldown_minutes':10}}})),'zero bosses')
        ok(service.draft==snapshot,'atomic rejected changes')
        ok('aktualnie' in __import__('systems.live_olc35_finale',fromlist=['preview']).preview(service,'boss35',boss,'definicja'),'field preview')
        ok(bool(service.apply(server,'test')),'publication')
        ok(ACTIVE['bosses'][boss]==rules['bosses'][boss],'active boss')
        ok(ACTIVE['activities']['live_gornicze_przetwarzanie']['recipe']==recipe,'active craft')
        ok(war_config()['bosses_needed']==2,'live war settings')
        ok(city_config()['bonus_per_level']==2,'live city settings')
        mob=SimpleNamespace(hp=40,max_hp=100)
        ok(boss_action(mob,{'uoss_unique_superboss_key':boss})==1.0,'not every turn')
        ok(boss_action(mob,{'uoss_unique_superboss_key':boss})==1.8,'active damage phase')
        injured=SimpleNamespace(hp=10,max_hp=100)
        for _ in range(2):
            ok(boss_action(injured,{'uoss_unique_superboss_key':boss})==1.0,'heal waits')
        ok(boss_action(injured,{'uoss_unique_superboss_key':boss})==1.0 and injured.hp==14,'heal triggers and bounded')
        ok(start_war(db,10,1000),'start war')
        ok(not start_war(db,10,1000),'prevent duplicate war')
        ok(war_boss_kill(db,10,1001,False) is None,'no nonboss credit')
        ok(war_boss_kill(db,10,1001,True)==(1,2,0),'first boss')
        ok(war_boss_kill(db,10,1002,True)==(2,2,10000),'completed war')
        ok(war_boss_kill(db,10,1002,True) is None,'no repeated reward')
        ok(db.execute('SELECT treasury FROM player_clans WHERE id=10').fetchone()[0]==1010000,'silver reward once')
        ok(not start_war(db,10,1003),'cooldown')
        ok(start_war(db,10,1002+120*60),'cooldown expires')
        ok(city_bonus(db,10)==0,'neutral city')
        ok(city_level(db,10,'warsztat')==0,'city empty')
        ok(city_upgrade(db,10,'warsztat')==(True,1,100),'city consumes currency')
        ok(city_bonus(db,10)==2,'city boosts guild')
        ok(city_upgrade(db,10,'warsztat')==(True,2,400),'squared upgrade cost')
        ok(city_upgrade(db,10,'warsztat')==(True,3,900),'third upgrade')
        ok(city_craft_bonus(db,10,5)==6,'workshop creates one additional craft item')
        ok(city_craft_bonus(db,None,5)==5,'nonmember unchanged')
        ok(city_upgrade(db,10,'warsztat')==(False,3,0),'level cap')
        deny(lambda:city_upgrade(db,10,'exploit'),'unknown building')
        ok(city_level(db,10,'warsztat')==3,'city persisted')
        restart=LiveContentV1204(SimpleNamespace(conn=db))
        ok(restart.revision==1,'restart revision')
        ok(ACTIVE['activities']['live_gornicze_przetwarzanie']['recipe']==recipe,'restart active')
        ok(city_level(db,10,'warsztat')==3,'city SQLite independent of OLC')
        # Rollback published OLC while retaining guild earned progress/currency.
        restart.stage_edit('boss35',boss,'definicja','auto')
        ok(bool(restart.apply(server,'test')),'publish auto rollback')
        ok(boss not in ACTIVE['bosses'],'boss disabled')
        ok(city_level(db,10,'warsztat')==3,'city progression persists')
        ok(war_status(db,10) is not None,'war progress persists')
    finally:
        try:
            service._remove(server.world)
        except Exception as exc:
            raise AssertionError("v35 OLC cleanup failure") from exc
        db.close()
    return checks

if __name__=='__main__':
    print('OLC35',run(),'PASS')
