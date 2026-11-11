# -*- coding: utf-8 -*-
"""OLC32: eight gameplay consumers + SQLite lifecycle and invalid draft protection."""
import copy
import json
import sqlite3
from types import SimpleNamespace


def run():
    from systems.live_content_v1204 import LiveContentV1204, blank
    from systems.live_olc32_finale import (
        CATEGORIES, ACTIVE, uoss_phase_multiplier, crafting_bonus,
        summon_combo, skill_combo, event_allowed, quest_bonus_items,
        guild_milestone_bonus, package,
    )
    from data.crafting_recipes import CRAFT_RECIPES
    from player.session_mixins.era_sky_v1700 import SUMMONS
    from core.classes_skills import CLASS_SKILLS
    from data.rooms import ROOMS
    from data.quests import QUESTS
    from data.items import ITEMS
    checks = 0
    def ok(value,description):
        nonlocal checks
        assert value,description
        checks+=1
    def deny(fn,description):
        nonlocal checks
        try:fn()
        except (ValueError,TypeError):checks+=1
        else:raise AssertionError('Niepoprawne dane przyjęte: '+description)

    conn=sqlite3.connect(':memory:');conn.row_factory=sqlite3.Row
    conn.execute('CREATE TABLE quests(quest_id TEXT,status TEXT)')
    world=SimpleNamespace(mobs={},_register_runtime_spawn=lambda *_:None)
    server=SimpleNamespace(world=world,sessions=[])
    service=None;restarted=None
    recipe=next(iter(CRAFT_RECIPES))
    summon=next(iter(SUMMONS))
    skill=next(s['id'] for v in CLASS_SKILLS.values() for s in v)
    room=next(iter(ROOMS))
    quest='bandit_patrol' if 'bandit_patrol' in QUESTS else next(iter(QUESTS))
    item='iron_ore' if 'iron_ore' in ITEMS else next(iter(ITEMS))
    try:
        service=LiveContentV1204(SimpleNamespace(conn=conn))
        ok(set(service.active['v32_rules'])==set(CATEGORIES),'8 dziedzin')
        ok('v32_rules' in LiveContentV1204._compat({}),'stare wersje SQLite')
        ok(crafting_bonus(recipe,room,5)==5,'neutral crafting')
        ok(event_allowed('live_inwazja',0),'neutral event')
        ok(guild_milestone_bonus(800)==0,'neutral guild')
        ok(quest_bonus_items(quest)=={},'neutral quest')
        ok(summon_combo(SimpleNamespace(),summon,50)==50,'neutral summon')
        ok(skill_combo(SimpleNamespace(),skill,1.7)==1.7,'neutral skill')
        mob=SimpleNamespace(hp=25,max_hp=100)
        templ={'uoss_unique_superboss_key':'black_rabite','max_hp':100}
        ok(uoss_phase_multiplier(mob,templ)==1.0,'neutral boss')
        rules={
            'uoss':{'black_rabite':{'phases':[{'below_hp':75,'interval':2,'damage_percent':125},
                         {'below_hp':30,'interval':3,'damage_percent':200}]}},
            'professions':{recipe:{'extra_output':3}},
            'summons':{summon:{'combo_every':2,'combo_percent':175}},
            'skills':{skill:{'combo_every':2,'combo_percent':150}},
            'story':{quest:{'bonus_items':{item:2}}},
            'guilds':{'global':{'milestones':[{'level':10,'bonus_percent':3},
                    {'level':20,'bonus_percent':5}]}},
            'world':{room:{'workshop_yield_percent':200}},
        }
        message=package(service,json.dumps(rules))
        ok('Pakiet32 przygotowany' in message,'pakiet32')
        ok(service.active['v32_rules']['uoss']=={},'draft nie opublikowany')
        old=copy.deepcopy(service.draft)
        deny(lambda:service.stage_edit('boss32','black_rabite','definicja',json.dumps(
            {'phases':[{'below_hp':50,'interval':0,'damage_percent':200}]})), 'zero interval')
        ok(service.draft==old,'walidacja atomowa')
        deny(lambda:package(service,json.dumps({'world':{room:{'workshop_yield_percent':-100}}})),
             'niepoprawny warsztat')
        ok(service.draft==old,'pakiet atomowy')
        deny(lambda:service.stage_edit('fabula32',quest,'definicja',json.dumps(
            {'bonus_items':{'unlisted_tool_fake':1}})), 'nieznany przedmiot')
        ok(service.draft==old,'quest atomowy')
        ok(service.validate(service.draft),'valid draft')
        result=service.apply(server,'test')
        ok(bool(result),'published')
        ok(service.revision==1,'revision 1')
        ok(ACTIVE['uoss']['black_rabite']['phases'][1]['damage_percent']==200,'uoss active')
        ok(crafting_bonus(recipe,room,5)==16,'recipe + workshop')
        owner=SimpleNamespace()
        ok(summon_combo(owner,summon,100)==100,'summon hit1')
        ok(summon_combo(owner,summon,100)==175,'summon hit2')
        caster=SimpleNamespace()
        ok(skill_combo(caster,skill,2.0)==2.0,'skill hit1')
        ok(skill_combo(caster,skill,2.0)==3.0,'skill hit2')
        ok(quest_bonus_items(quest)=={item:2},'quest item reward')
        ok(guild_milestone_bonus(9)==0,'guild before')
        ok(guild_milestone_bonus(10)==3,'guild level10')
        ok(guild_milestone_bonus(20)==8,'guild level20')
        ok(uoss_phase_multiplier(mob,templ)==1.0,'uoss attack1')
        ok(uoss_phase_multiplier(mob,templ)==1.0,'uoss attack2')
        ok(uoss_phase_multiplier(mob,templ)==2.0,'uoss attack3')
        mob.hp=60
        ok(uoss_phase_multiplier(mob,templ)==1.25,'uoss phase75 attack4')
        preview=__import__('systems.live_olc32_finale',fromlist=['preview']).preview
        ok('DRAFT' in preview(service,'boss32','black_rabite','definicja'),'preview')
        service.stage_edit('fach32',recipe,'definicja','auto')
        ok(recipe not in service.draft['v32_rules']['professions'],'auto')
        service.reset_draft()
        # Fresh instance simulates a restart and reloads the SQLite revision.
        service._remove(world)
        restarted=LiveContentV1204(SimpleNamespace(conn=conn))
        ok(restarted.revision==1,'restart revision')
        ok(crafting_bonus(recipe,room,5)==16,'restart applied')
        restarted.stage_edit('fach32',recipe,'definicja','auto')
        ok(restarted.active['v32_rules']['professions'],'active retained during draft')
        restarted.apply(server,'test2')
        ok(crafting_bonus(recipe,room,5)==10,'single field auto does not change workshop')
        restarted.stage_edit('fach32',recipe,'definicja',json.dumps({'extra_output':3}))
        restarted.apply(server,'test3')
        ok(crafting_bonus(recipe,room,5)==16,'reconfigure')
        restarted.reset_draft()
        # All eight-domain state can be reset atomically through the existing editor.
        for domain in CATEGORIES:restarted.draft['v32_rules'][domain]={}
        restarted.apply(server,'test4')
        ok(crafting_bonus(recipe,room,5)==5,'revert neutral')
        ok(quest_bonus_items(quest)=={},'quest revert neutral')
        ok(guild_milestone_bonus(800)==0,'guild revert neutral')
        # Standalone UTC event constraint validation (custom events are validated by live OLC).
        ACTIVE['events']['live_test_32']={'hours_utc':[0]}
        ok(event_allowed('live_test_32',0),'UTC midnight yes')
        ok(not event_allowed('live_test_32',3600),'UTC 1 am no')
        ACTIVE['events'].pop('live_test_32',None)
        return checks
    finally:
        if restarted:restarted._remove(world)
        elif service:service._remove(world)
        conn.close()


if __name__=='__main__':
    print(f'OLC32 v32.00.0: {run()} PASS')
