# -*- coding: utf-8 -*-
"""Stage 3: real v107 Magicite state, skill command, PvE and negative cases.

Uses a disposable SQLite file and fake PvE objects; NO production server or DB.
"""
from __future__ import annotations
import asyncio
import os
import sqlite3
import tempfile
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from core.magitek.catalogue import skill_catalogue
from systems.magitek.magicite import (
    CORES, ensure_magicite_schema, read_link, bind_core, unlock_link,
    magicite_command, cast_magicite, calculate_damage,
)

SKILLS={row['v107_skill']:row for row in skill_catalogue()}

class DB:
    def __init__(self, path):
        self.conn=sqlite3.connect(path)
        self.learned={row['id'] for row in skill_catalogue()}
        self.saved=[]
    def knows_skill(self, account, skill): return skill in self.learned
    def skill_progress(self, account, skill): return {'level':23}
    def close(self):self.conn.close()

class Mob:
    def __init__(self,name,room='guild_arcane_chamber',hp=160):
        self.key=name; self.room_id=room;self.hp=hp;self.alive=True
        self.template_id='v107_magicite_test_'+name
        self.engaged_by=None;self.engaged_at=0.0

class World:
    def __init__(self,mobs):self.mobs=mobs
    def room_mobs(self,room):return list(self.mobs)

class Actor:
    def __init__(self,db,room='guild_arcane_chamber',level=15,mobs=None):
        self.server=SimpleNamespace(db=db,world=World(mobs or []))
        self.server.engagement_allowed=lambda actor,mob: mob.key!='friendly'
        self.server.sanitize_mob_engagement=lambda mob: None
        async def _assist(actor,mob): return None
        self.server.auto_assist_party_combat=_assist
        self.character=SimpleNamespace(name='Badacz',class_name='Magitek',
                                       room_id=room,character_level=40)
        self.account_id=7;self.closed=False;self.current_hp=120
        self.current_mana=150;self.v0319_silence_until=0
        self._level=level;self.messages=[];self.xp=[];self.dead=[]
        self.started=0;self.scaled=[];self.waves=[];self.combat_mob_key=None
    async def send(self,text):self.messages.append(text)
    def class_mastery_level(self,cls):return self._level
    def is_downed_v0371(self):return False
    def effective_intelligence(self):return 200
    def effective_willpower(self):return 150
    async def apply_boss_defense(self,mob,damage):return damage//2 if mob.key=='boss' else damage
    async def mob_defeated(self,mob):mob.alive=False;self.dead.append(mob.key)
    async def grant_skill_use_xp(self,skill):self.xp.append(skill['v107_skill'])
    async def ensure_realtime_combat(self):self.started+=1
    def apply_adaptive_mob_scale_v11330(self,mob):self.scaled.append(mob.key)
    async def boss_summon_wave_v1301(self,mob,opening=False):self.waves.append((mob.key,opening))


def run():
    previous={key:os.environ.get(key) for key in ('SOULBOUND_V112_STAGING','SOULBOUND_HOST','SOULBOUND_PORT','SOULBOUND_DB','SOULBOUND_V107_STAGING')}
    os.environ.update({'SOULBOUND_V112_STAGING':'1','SOULBOUND_HOST':'127.0.0.1','SOULBOUND_PORT':'48471'})
    os.environ.pop('SOULBOUND_V107_STAGING',None)
    checks=0
    def ok(state,desc):
        nonlocal checks
        if not state: raise AssertionError(desc)
        checks+=1
    def command(a,query):return asyncio.run(magicite_command(a,query))
    def cast(a,query=''):return asyncio.run(cast_magicite(a,SKILLS['magicitelink'],query))
    from data.mobs import MOB_TEMPLATES
    prepared={}
    for mob_name in ('goblin','boss','friendly'):
        key='v107_magicite_test_'+mob_name
        prepared[key]=MOB_TEMPLATES.get(key)
        MOB_TEMPLATES[key]={'name':mob_name,'damage_type':'magic'}
    try:
        with tempfile.TemporaryDirectory(prefix='sb112_magicite_') as directory:
            filename=Path(directory)/'staging.db'
            os.environ['SOULBOUND_DB']=str(filename)
            db=DB(filename)
            actor=Actor(db)
            ok(read_link(db,7)==(False,''),'readonly initial state')
            ok(db.conn.execute("SELECT name FROM sqlite_master WHERE name='magitek_magicite_link_v107'").fetchone() is None,'no implicit schema changes')
            command(actor,'status')
            ok(actor.messages[-1].startswith('Magicite Link: Zablokowany'),'status in Polish')
            actor.character.room_id='square'; command(actor,'odblokuj')
            ok(read_link(db,7)==(False,''),'trainer room required')
            actor.character.room_id='guild_arcane_chamber';actor._level=14
            command(actor,'odblokuj')
            ok(read_link(db,7)==(False,''),'level 15 unlock required')
            actor._level=15
            db.learned.remove('v107_magitek_magicitelink')
            command(actor,'odblokuj')
            ok(read_link(db,7)==(False,''),'learn Magicite Link first')
            db.learned.add('v107_magitek_magicitelink')
            db.learned.remove('v107_magitek_icebeam')
            command(actor,'odblokuj')
            ok(read_link(db,7)==(False,''),'beam training requirement')
            db.learned.add('v107_magitek_icebeam')
            command(actor,'powiaz ogien')
            ok(read_link(db,7)==(False,''),'cannot link without unlock')
            command(actor,'odblokuj')
            ok(read_link(db,7)==(True,''),'solo training unlock persisted')
            command(actor,'odblokuj')
            ok(read_link(db,7)==(True,''),'repeated unlock is idempotent')
            command(actor,'powiaz babylon')
            ok(read_link(db,7)==(True,''),'unknown core refused')
            command(actor,'powiaz lod')
            ok(read_link(db,7)==(True,'lod'),'core bound')
            for core in CORES:
                command(actor,'powiaz '+core)
                ok(read_link(db,7)==(True,core),f'{core} link supported')
            actor.character.room_id='square';command(actor,'powiaz lod')
            ok(read_link(db,7)==(True,'trucizna'),'cannot relink outside trainer')
            actor.character.room_id='guild_arcane_chamber'
            ok(not bind_core(db,7,"'; DELETE FROM accounts;--"),'SQL injection/invalid core forbidden')
            actor2=Actor(db); actor2.account_id=8
            ok(read_link(db,8)==(False,''),'per-character link, not account-wide')
            ok(not bind_core(db,8,'lod'),'other character cannot bind')
            db.close()
            reopened=DB(filename)
            ok(read_link(reopened,7)==(True,'trucizna'),'SQLite persistence after close/reopen')
            actor=Actor(reopened,mobs=[Mob('goblin',hp=300),Mob('boss',hp=300),Mob('friendly',hp=300)])
            cast(actor,'at goblin')
            ok(actor.current_mana==150 and not actor.xp,'no target allowed for AoE')
            actor._level=14; cast(actor)
            ok(actor.current_mana==150 and not actor.xp,'level gate on cast')
            actor._level=15; actor.v0319_silence_until=10**11;cast(actor)
            ok(actor.current_mana==150 and 'Silence' in actor.messages[-1],'silence blocks cast')
            actor.v0319_silence_until=0;actor.current_mana=1;cast(actor)
            ok(actor.current_mana==1 and not actor.xp,'low MP refuses before effect')
            actor.current_mana=150;actor.server.world.mobs=[Mob('friendly')];cast(actor)
            ok(actor.current_mana==150 and not actor.xp,'no valid target refuses without MP/XP')
            actor.server.world.mobs=[Mob('goblin',hp=300),Mob('boss',hp=300),Mob('friendly',hp=300)]
            cast(actor)
            ok(actor.current_mana==120 and actor.xp==['magicitelink'],'once-per-cast mana and XP')
            ok(actor.server.world.mobs[0].hp<300 and actor.server.world.mobs[1].hp<300,'real AoE hits both enemies')
            ok(actor.server.world.mobs[2].hp==300,'no friendly/PvP damage')
            ok(actor.server.world.mobs[1].hp>actor.server.world.mobs[0].hp,'native boss guard reduces hit')
            ok(getattr(actor.server.world.mobs[0],'v0319_poison_until',0)>0,'native poison DoT active')
            ok(actor.started==1,'realtime combat continues')
            ok(len(actor.scaled)==2 and len(actor.waves)==2,'adaptive scaling and boss opening called')
            ok(actor.combat_mob_key in ('goblin','boss'),'normal realtime combat target initialized')
            small=Actor(reopened,mobs=[Mob('goblin',hp=1),Mob('boss',hp=1)])
            cast(small)
            ok(small.dead==['goblin','boss'],'kills through canonical mob_defeated')
            ok(small.started==0,'no surviving enemy no re-engage')
            ok(small.current_mana==120 and len(small.xp)==1,'charge once on kill')
            small.character.class_name='Wojownik';small.server.world.mobs=[Mob('goblin',hp=500)]
            cast(small)
            ok(len(small.xp)==1 and small.server.world.mobs[0].hp==500
               and 'wymaga żywej' in small.messages[-1], 'non-Magitek forbidden')
            small.character.class_name='Magitek';small.current_hp=0;cast(small)
            ok(len(small.xp)==1,'dead caster forbidden')
            ok(calculate_damage(10,200,150,20,1.0)>0,'finite nonzero damage')
            ok(CORES['piorun'][2]!=CORES['ogien'][2],'source variable MP adapted')
            # Existing unique-superboss safety rules must apply to Magicite AoE.
            from world.uoss_superboss_runtime import superboss_attack_gate_v11137
            solo=Actor(reopened,mobs=[Mob('boss',hp=500)])
            with patch('world.uoss_superboss_runtime.superboss_attack_gate_v11137',return_value=(False,'boss locked')):
                cast(solo)
            ok(solo.current_mana==150 and solo.server.world.mobs[0].hp==500
               and not solo.xp, 'boss gate cannot be bypassed')
            # Call through the real combat mixin, not only the helper.
            from player.session_mixins.combat_skills import SessionCombatSkillsMixin
            through=Actor(reopened,mobs=[Mob('goblin',hp=500)])
            def find_skill_from_input(raw):
                return SKILLS['magicitelink'],''
            through.find_skill_from_input=find_skill_from_input
            asyncio.run(SessionCombatSkillsMixin.use_class_skill(through,'magicitelink'))
            ok(through.server.world.mobs[0].hp<500 and through.xp==['magicitelink'],
               'real combat mixin Magicite skill dispatch')
            # direct UI dispatch: real installed router must route only Magitek subcommands.
            from player.session_mixins.command_special_handlers import SessionCommandSpecialHandlersMixin
            class UI(Actor,SessionCommandSpecialHandlersMixin):
                async def command_skill_v0490(self,args):self.fallback=args
            ui=UI(reopened)
            asyncio.run(ui.command_magitek_v107('magicite status'))
            ok(ui.messages[-1].startswith('Magicite Link: '),'mtek magicite UI status')
            asyncio.run(ui.command_magitek_v107('firebeam'))
            ok(ui.fallback=='firebeam','mtek normal skill path preserved')
            ui.character.class_name='Wojownik'
            asyncio.run(ui.command_magitek_v107('magicite status'))
            ok('wymaga aktywnej klasy' in ui.messages[-1],'other class blocked')
            reopened.close()
            # Strict staging guard independent of fake DB.
            del os.environ['SOULBOUND_V112_STAGING']
            blocked=False
            try: ensure_magicite_schema(DB(':memory:'))
            except RuntimeError: blocked=True
            ok(blocked,'schema rejects production mode')
    finally:
        for key, prior in prepared.items():
            if prior is None:MOB_TEMPLATES.pop(key,None)
            else:MOB_TEMPLATES[key]=prior
        for key,previous_value in previous.items():
            if previous_value is None:os.environ.pop(key,None)
            else:os.environ[key]=previous_value
    print(f'V107 MAGITEK ETAP 3 MAGICITE: {checks} kontroli PASS')
    return checks

if __name__=='__main__':run()
