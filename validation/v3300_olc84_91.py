# -*- coding: utf-8 -*-
"""v33 OLC 84-91: eight domains, runtime effects, invalid data, SQLite restart."""
import copy
import json
import sqlite3
from types import SimpleNamespace


def run():
    from systems.live_content_v1204 import LiveContentV1204
    from systems.live_olc33_mechanics import (
        CATEGORIES, ACTIVE, craft_byproduct, uoss_restore, summon_support,
        skill_alternation, event_guardians, quest_guild_reward,
        guild_boss_class_xp, package, spawn_guardians)
    from data.crafting_recipes import CRAFT_RECIPES
    from data.items import ITEMS
    from data.mobs import MOB_TEMPLATES
    from data.rooms import ROOMS
    from core.classes_skills import CLASS_SKILLS
    from world.uoss_superbosses import UOSS_SUPERBOSS_ENCOUNTERS_V11134
    from player.session_mixins.era_sky_v1700 import SUMMONS
    checks=0
    def ok(value, label):
        nonlocal checks
        assert value,label
        checks+=1
    def deny(f,label):
        nonlocal checks
        try:f()
        except (ValueError,TypeError):checks+=1
        else:raise AssertionError('Unexpected acceptance: '+label)
    db=sqlite3.connect(':memory:');db.row_factory=sqlite3.Row
    db.execute('CREATE TABLE quests(quest_id TEXT,status TEXT)')
    fake=SimpleNamespace(conn=db)
    server=SimpleNamespace(world=SimpleNamespace(mobs={},_register_runtime_spawn=lambda *_:None),sessions=[])
    service=None;restart=None
    boss=next(iter(UOSS_SUPERBOSS_ENCOUNTERS_V11134))
    recipe=next(k for k,v in CRAFT_RECIPES.items() if v.get('output')!='iron_ore')
    summon=next(iter(SUMMONS))
    skills=[s['id'] for group in CLASS_SKILLS.values() for s in group]
    origin=next(k for k,v in ROOMS.items() if 'up' not in v.get('exits',{}))
    target=next(k for k in ROOMS if k!=origin)
    mob_id=next(k for k in MOB_TEMPLATES if not k.startswith(('v12812_event_','v26_event_')))
    try:
        service=LiveContentV1204(fake)
        ok(set(service.active['v33_rules'])==set(CATEGORIES),'eight categories')
        ok(service._compat({})['v33_rules']==service.active['v33_rules'],'older SQLite')
        rules={
          'uoss':{boss:{'below_hp':50,'every':2,'restore_percent':5}},
          'professions':{recipe:{'byproduct':'iron_ore','amount':2,'every':2}},
          'summons':{summon:{'heal_owner_percent':2,'every':2}},
          'skills':{skills[0]:{'alternate_with':skills[1],'bonus_percent':150}},
          'events':{'basalt':{'guardian':mob_id,'count':2}},
          'story':{'bandit_patrol':{'guild_class':'Wojownik','guild_rep':10}},
          'guilds':{'global':{'boss_class_xp_percent':125}},
          'world':{origin:{'direction':'up','destination':target}},
        }
        ok(uoss_restore(SimpleNamespace(hp=20,max_hp=100),{'uoss_unique_superboss_key':boss})==0,'neutral boss')
        ok(craft_byproduct(SimpleNamespace(),recipe) is None,'neutral profession')
        ok(event_guardians('basalt') is None,'neutral event')
        ok(quest_guild_reward('bandit_patrol') is None,'neutral story')
        ok(ROOMS[origin].get('exits',{}).get('up') is None,'neutral portal')
        preview=service.stage_edit('boss33',boss,'definicja',json.dumps(rules['uoss'][boss]))
        ok(bool(preview),'stage boss')
        service.reset_draft()
        ok(service.active['v33_rules']['uoss']=={},'active unaffected by stage')
        message=package(service,json.dumps(rules))
        ok('DRAFT' in message,'bundle authored')
        before=copy.deepcopy(service.draft)
        deny(lambda:service.stage_edit('swiat33',origin,'definicja',json.dumps({'direction':'up','destination':'inexistent_room'})),'invalid destination')
        deny(lambda:service.stage_edit('boss33',boss,'definicja',json.dumps({'below_hp':40,'every':0,'restore_percent':10})),'zero interval')
        deny(lambda:service.stage_edit('fach33',recipe,'definicja',json.dumps({'byproduct':CRAFT_RECIPES[recipe]['output'],'amount':2,'every':2})),'self byproduct')
        deny(lambda:package(service,json.dumps({'guilds':{'global':{'boss_class_xp_percent':40}}})),'invalid XP reduction')
        deny(lambda:service.stage_edit('event33','basalt','definicja',json.dumps({'guardian':'v12812_event_basalt','count':2})),'no recursive event guardian')
        ok(service.draft==before,'all invalid attempts atomic')
        ok(service.validate(service.draft),'valid staged data')
        ok(service.apply(server,'administrator'),'published')
        ok(ROOMS[origin]['exits']['up']==target,'portal physically visible in ROOMS')
        ok(event_guardians('basalt')==(mob_id,2),'guardian authored')
        ok(quest_guild_reward('bandit_patrol')['guild_rep']==10,'story authored')
        mob=SimpleNamespace(hp=20,max_hp=100)
        template={'uoss_unique_superboss_key':boss,'max_hp':100}
        ok(uoss_restore(mob,template)==0,'boss attack1 no heal')
        ok(uoss_restore(mob,template)==5 and mob.hp==25,'boss attack2 heal')
        mob.hp=0
        ok(uoss_restore(mob,template)==0,'no resurrection from zero')
        mob.hp=100
        ok(uoss_restore(mob,template)==0,'no overheal')
        owner=SimpleNamespace()
        ok(craft_byproduct(owner,recipe) is None,'craft1')
        ok(craft_byproduct(owner,recipe)==('iron_ore',2),'craft2 gives real material')
        ok(craft_byproduct(owner,recipe) is None,'craft3')
        ok(craft_byproduct(owner,recipe)==('iron_ore',2),'craft4')
        ok(skill_alternation(owner,skills[1],100)==100,'prelude')
        ok(skill_alternation(owner,skills[0],100)==150,'alternation synergy')
        ok(skill_alternation(owner,skills[0],100)==100,'repetition not synergy')
        ok(skill_alternation(owner,skills[1],300)==300,'reset')
        ok(skill_alternation(owner,skills[0],200)==300,'second synergy')
        ok(guild_boss_class_xp({'boss_mechanic':'enrage'},SimpleNamespace(guild_row_v0926=lambda:{'clan_id':1}),100)==125,'guild boss XP')
        ok(guild_boss_class_xp({'boss_mechanic':'enrage'},SimpleNamespace(guild_row_v0926=lambda:None),100)==100,'non-guild no bonus')
        ok(guild_boss_class_xp({'boss_mechanic':'enrage','uoss_unique_superboss_key':boss},SimpleNamespace(guild_row_v0926=lambda:{'clan_id':1}),100)==100,'UOSS exact XP untouched')
        ok(guild_boss_class_xp({},SimpleNamespace(guild_row_v0926=lambda:{'clan_id':1}),100)==100,'regular mob no bonus')
        ok('DRAFT' in __import__('systems.live_olc33_mechanics',fromlist=['preview']).preview(service,'boss33',boss,'definicja'),'current & draft preview')
        # Guardians are authored as real MobState entries by the world spawner.
        ok(event_guardians('basalt')==(mob_id,2),'guardian slot definition persists')
        # Real world event companion creation contract: no duplicate spawns.
        fake_mobs={}
        event={'slug':'basalt','slot':1245,'expires_at':4000.0}
        ok(spawn_guardians(event,'square',fake_mobs,MOB_TEMPLATES,lambda **kw:SimpleNamespace(**kw))==2,'event wave spawned')
        ok(len(fake_mobs)==2 and all(v.v016_ephemeral for v in fake_mobs.values()),'real ephemeral companions')
        ok(all(v.v029_expires_at==4000.0 for v in fake_mobs.values()),'event expiry')
        ok(spawn_guardians(event,'square',fake_mobs,MOB_TEMPLATES,lambda **kw:SimpleNamespace(**kw))==0,'idempotent wave')
        event['slot']=1246
        ok(spawn_guardians(event,'square',fake_mobs,MOB_TEMPLATES,lambda **kw:SimpleNamespace(**kw))==2,'new event gets new wave')
        # Restore active content because WorldState is not the server's live world.
        service._remove(server.world)
        restart=LiveContentV1204(fake)
        ok(restart.revision==1,'SQLite reload revision')
        ok(ROOMS[origin]['exits']['up']==target,'portal persisted SQLite')
        ok(event_guardians('basalt')==(mob_id,2),'guards persisted SQLite')
        restart.stage_edit('swiat33',origin,'definicja','auto')
        restart.apply(server,'administrator')
        ok('up' not in ROOMS[origin].get('exits',{}),'single portal undo')
        ok(restart.active['v33_rules']['story'],'other rules remain')
        for c in CATEGORIES:restart.draft['v33_rules'][c]={}
        restart.apply(server,'administrator')
        ok(event_guardians('basalt') is None,'events fully reset')
        ok(quest_guild_reward('bandit_patrol') is None,'story fully reset')
        ok(craft_byproduct(SimpleNamespace(),recipe) is None,'craft reset')
        ok(uoss_restore(SimpleNamespace(hp=25,max_hp=100),template)==0,'boss reset')
        return checks
    finally:
        if restart:restart._remove(server.world)
        elif service:service._remove(server.world)
        db.close()

if __name__=='__main__':
    print(f'Soulbound OLC33: {run()} PASS')
