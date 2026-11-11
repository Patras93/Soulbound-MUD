# -*- coding: utf-8 -*-
"""v34 OLC92–99: 8 runtime integrations, validation, SQLite restart/rollback."""
import copy
import json
import sqlite3
from types import SimpleNamespace


def run():
    from systems.live_content_v1204 import LiveContentV1204, blank
    from systems.live_olc34_integration import (
        ACTIVE,CATEGORIES,package,boss_pressure,profession_find,
        summon_finisher,skill_chain,spawn_reinforcements,
        quest_faction_reward,guild_treasury_reward)
    from world.uoss_superbosses import UOSS_SUPERBOSS_ENCOUNTERS_V11134
    from data.items import ITEMS
    from data.quests import QUESTS
    from data.mobs import MOB_TEMPLATES
    from data.crafting_recipes import CRAFT_RECIPES
    from data.rooms import ROOMS
    from core.classes_skills import CLASS_SKILLS
    from player.session_mixins.era_sky_v1700 import SUMMONS
    checks=0
    def ok(predicate,label):
        nonlocal checks
        assert predicate,label
        checks+=1
    def deny(f,label):
        nonlocal checks
        try:f()
        except (ValueError,TypeError):checks+=1
        else:raise AssertionError('Invalid rule accepted: '+label)
    db=sqlite3.connect(':memory:');db.row_factory=sqlite3.Row
    db.execute('CREATE TABLE quests(quest_id TEXT,status TEXT)')
    fake=SimpleNamespace(conn=db)
    world=SimpleNamespace(mobs={},_register_runtime_spawn=lambda *_:None)
    server=SimpleNamespace(world=world,sessions=[])
    service=restart=None
    boss=next(iter(UOSS_SUPERBOSS_ENCOUNTERS_V11134))
    recipe=next(k for k,v in CRAFT_RECIPES.items() if v.get('output')!='iron_ore')
    summon=next(iter(SUMMONS))
    skills=[s['id'] for group in CLASS_SKILLS.values() for s in group]
    quest='bandit_patrol' if 'bandit_patrol' in QUESTS else next(iter(QUESTS))
    guardian=next(k for k in MOB_TEMPLATES if not k.startswith(('v12812_event_','v26_event_')))
    portal=next((a,b) for a in ROOMS for b in ROOMS if a!=b
                and 'up' not in ROOMS[a].get('exits',{})
                and 'down' not in ROOMS[b].get('exits',{}))
    origin,destination=portal
    rules={
        'uoss':{boss:{'every':2,'stack_percent':110,'max_stacks':3}},
        'professions':{recipe:{'material':'iron_ore','amount':2,'every':2}},
        'summons':{summon:{'below_hp':25,'damage_percent':160}},
        'skills':{skills[1]:{'after':skills[0],'bonus_percent':180}},
        'events':{'basalt':{'reinforcement':guardian,'count':2}},
        'story':{quest:{'faction':'miners','reputation':25}},
        'guilds':{'global':{'treasury_bonus_percent':150}},
        'world':{origin:{'direction':'up','destination':destination,'return_direction':'down'}},
    }
    try:
        service=LiveContentV1204(fake)
        ok('v34_rules' in blank(),'new schema')
        ok(service.active['v34_rules']==blank()['v34_rules'],'neutral active')
        ok('v34_rules' in service._compat({}),'older SQLite backward compatible')
        ok(boss_pressure(SimpleNamespace(hp=10),{'uoss_unique_superboss_key':boss})==1.0,'neutral UOSS')
        ok(profession_find(SimpleNamespace(),recipe) is None,'neutral craft')
        ok(summon_finisher(summon,SimpleNamespace(hp=20,max_hp=100),100)==100,'neutral summon')
        ok(skill_chain(SimpleNamespace(),skills[1],1.0)==1.0,'neutral skill')
        ok(quest_faction_reward(quest) is None,'neutral faction')
        ok(guild_treasury_reward(100)==100,'neutral guild')
        staged=service.stage_edit('boss34',boss,'definicja',json.dumps(rules['uoss'][boss]))
        ok(bool(staged),'single draft edit')
        service.reset_draft()
        ok('Pakiet34 DRAFT' in package(service,json.dumps(rules)),'8-domain package')
        ok(service.active['v34_rules']['world']=={},'draft never live')
        draft=copy.deepcopy(service.draft)
        deny(lambda:service.stage_edit('boss34',boss,'definicja',json.dumps({'every':0,'stack_percent':150,'max_stacks':2})),'zero interval')
        deny(lambda:service.stage_edit('fach34',recipe,'definicja',json.dumps({'material':CRAFT_RECIPES[recipe]['output'],'amount':5,'every':2})),'resource duplication')
        deny(lambda:service.stage_edit('swiat34',origin,'definicja',json.dumps({'direction':'up','destination':'unknown_room','return_direction':'down'})),'unknown room')
        deny(lambda:package(service,json.dumps({'guilds':{'global':{'treasury_bonus_percent':50}}})),'no guild reduction')
        deny(lambda:service.stage_edit('event34','basalt','definicja',json.dumps({'reinforcement':'v12812_event_basalt','count':2})),'no boss recursive spawns')
        ok(service.draft==draft,'invalid stages are atomic')
        ok(bool(service.validate(service.draft)),'valid package')
        ok(bool(service.apply(server,'test')),'publish')
        ok(service.revision==1,'revision1')
        ok(ROOMS[origin]['exits']['up']==destination,'physical forward portal')
        ok(ROOMS[destination]['exits']['down']==origin,'physical reverse portal')
        ok(quest_faction_reward(quest)=={'faction':'miners','reputation':25},'published quest reputation')
        ok(guild_treasury_reward(100)==150,'published treasury bonus')
        mob=SimpleNamespace(hp=50,max_hp=100)
        templ={'uoss_unique_superboss_key':boss}
        ok(boss_pressure(mob,templ)==1.0,'boss first attack')
        ok(round(boss_pressure(mob,templ),2)==1.1,'boss second attack ramp')
        ok(round(boss_pressure(mob,templ),2)==1.1,'boss third attack')
        ok(round(boss_pressure(mob,templ),2)==1.21,'boss fourth attack')
        ok(round(boss_pressure(mob,templ),3)==1.21,'boss fifth')
        ok(round(boss_pressure(mob,templ),3)==1.331,'boss sixth max stack')
        ok(all(round(boss_pressure(mob,templ),3)==1.331 for _ in range(15)),'boss caps configured stacks')
        mob.hp=0
        ok(boss_pressure(mob,templ)==1.0,'dead boss no attack')
        crafter=SimpleNamespace()
        ok(profession_find(crafter,recipe) is None,'craft first')
        ok(profession_find(crafter,recipe)==('iron_ore',2),'craft second resource')
        ok(profession_find(crafter,recipe) is None,'craft third')
        ok(profession_find(crafter,recipe)==('iron_ore',2),'craft fourth')
        target=SimpleNamespace(hp=24,max_hp=100)
        ok(summon_finisher(summon,target,100)==160,'summon finisher')
        target.hp=26
        ok(summon_finisher(summon,target,100)==100,'summon no early finisher')
        target.hp=0
        ok(summon_finisher(summon,target,100)==100,'summon dead no finisher')
        mage=SimpleNamespace()
        ok(skill_chain(mage,skills[1],2.0)==2.0,'skill initial')
        ok(skill_chain(mage,skills[0],2.0)==2.0,'skill prelude')
        ok(skill_chain(mage,skills[1],2.0)==3.6,'skill chain boost')
        ok(skill_chain(mage,skills[1],2.0)==2.0,'skill repetition neutral')
        units={}
        event={'slug':'basalt','slot':1234,'expires_at':4567.0}
        ok(spawn_reinforcements(event,'square',units,MOB_TEMPLATES,lambda **kw:SimpleNamespace(**kw))==2,'two real event mobs')
        ok(spawn_reinforcements(event,'square',units,MOB_TEMPLATES,lambda **kw:SimpleNamespace(**kw))==0,'same event cannot duplicate')
        ok(len(units)==2 and all(x.v016_ephemeral and x.v029_expires_at==4567.0 for x in units.values()),'event lifetime')
        event['slot']=1235
        ok(spawn_reinforcements(event,'square',units,MOB_TEMPLATES,lambda **kw:SimpleNamespace(**kw))==2,'next rotation spawns again')
        ok('DRAFT' in __import__('systems.live_olc34_integration',fromlist=['preview']).preview(service,'swiat34',origin,'definicja'),'preview')
        service._remove(world)
        restart=LiveContentV1204(fake)
        ok(restart.revision==1,'reload revision SQLite')
        ok(ROOMS[origin]['exits']['up']==destination and ROOMS[destination]['exits']['down']==origin,'restore portals')
        ok(quest_faction_reward(quest)['reputation']==25,'restore faction')
        restart.stage_edit('swiat34',origin,'definicja','auto')
        restart.apply(server,'test2')
        ok('up' not in ROOMS[origin].get('exits',{}),'reverse portal undo source')
        ok('down' not in ROOMS[destination].get('exits',{}),'reverse portal undo destination')
        ok(quest_faction_reward(quest) is not None,'unrelated settings remain')
        for category in CATEGORIES:restart.draft['v34_rules'][category]={}
        restart.apply(server,'test3')
        ok(guild_treasury_reward(100)==100,'guild full reset')
        ok(profession_find(SimpleNamespace(),recipe) is None,'craft full reset')
        ok(quest_faction_reward(quest) is None,'story full reset')
        ok(spawn_reinforcements(event,'square',{},MOB_TEMPLATES,lambda **kw:SimpleNamespace(**kw))==0,'events full reset')
        return checks
    finally:
        if restart:restart._remove(world)
        elif service:service._remove(world)
        db.close()


if __name__=='__main__':
    print(f'Soulbound OLC34: {run()} PASS')
