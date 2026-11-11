# -*- coding: utf-8 -*-
"""Stage 4: Diffuser through REAL Soulbound skill_combat_target method body."""
from __future__ import annotations
import asyncio
import time
from types import SimpleNamespace

from core.magitek.catalogue import skill_catalogue
from data.mobs import MOB_TEMPLATES
from player.session_mixins.skill_learning import SessionSkillLearningMixin
from systems.magitek.support import use_support_skill
from validation.v10700_magitek_support_regression import Actor, Server

SKILL=next(row for row in skill_catalogue() if row['v107_skill']=='diffuser')

class World:
    def __init__(self, mob):
        self.mobs={mob.key:mob}
        self.mob=mob
        self.refreshed=0
    def refresh(self):self.refreshed+=1
    def find_mob(self, room, query):
        if room==self.mob.room_id and query.casefold()==MOB_TEMPLATES[self.mob.template_id]['name'].casefold():
            return self.mob
        return None

class Engine(Server):
    def __init__(self,mob):
        super().__init__()
        self.world=World(mob)
        self.allow=True
        self.protect_calls=0
        self.room_notices=[]
    def engagement_allowed(self,actor,mob):return self.allow
    async def apply_party_protection(self,actor,mob):
        self.protect_calls+=1
        return None
    async def broadcast_room(self,room,text,exclude=None):
        self.room_notices.append((room,text))

class Player(Actor,SessionSkillLearningMixin):
    def __init__(self,name,srv):
        super().__init__(name,srv)
        self.starts=0
        self.waves=[]
    async def skill_combat_target(self,query):
        # Not a mock: execute the production method bound to the mixin.
        return await SessionSkillLearningMixin.skill_combat_target(self,query)
    def protected_player_target(self,query):
        return next((p for p in self.server.members if p.character.name.casefold()==query.casefold()),None)
    async def reject_friendly_npc_attack(self,query):
        if query.casefold()=='iria':
            await self.send('NPC jest chroniony.')
            return True
        return False
    def engagement_block_message(self,mob):return 'To starcie jest zablokowane.'
    async def boss_summon_wave_v1301(self,mob,opening=False):
        self.waves.append((mob.key,opening))
    async def ensure_realtime_combat(self):self.starts+=1


def run():
    checks=0
    def ok(value,description):
        nonlocal checks
        assert value,description
        checks+=1
    mob=SimpleNamespace(key='v107_diffuser_real_mob',template_id='v107_diffuser_real_template',
        hp=500,alive=True,room_id='temple_basement',engaged_by=None,engaged_at=0.0,
        player_hits=0,combat_turn=0)
    old=MOB_TEMPLATES.get(mob.template_id)
    MOB_TEMPLATES[mob.template_id]={'name':'Rzeczywisty Strażnik','damage_type':'physical'}
    try:
        srv=Engine(mob)
        actor=Player('Inżynier',srv)
        ally=Actor('Sympatyczna',srv)
        def cast(target):asyncio.run(use_support_skill(actor,SKILL,target))
        mob.monster_ai_guard_until_v1160=time.monotonic()+40
        srv.allow=False
        cast('Rzeczywisty Strażnik')
        ok(mob.monster_ai_guard_until_v1160>time.monotonic(),'true engagement gate protects status')
        ok(not actor.xp and actor.combat_mob_key is None, 'no XP and no combat when denied')
        ok(actor.sent[-1]=='To starcie jest zablokowane.','canonical denial message')
        srv.allow=True
        cast('Iria')
        ok(mob.monster_ai_guard_until_v1160>time.monotonic() and not actor.xp,'friendly NPC protected')
        cast('Sympatyczna')
        ok(mob.monster_ai_guard_until_v1160>time.monotonic() and not actor.xp,'player cannot be hostile target')
        cast('Rzeczywisty Strażnik')
        ok(mob.monster_ai_guard_until_v1160==0,'authentic resolved mob dispelled')
        ok(len(actor.xp)==1 and actor.xp[-1]=='diffuser','XP only after real success')
        ok(actor.combat_mob_key==mob.key and mob.engaged_by==actor.character.name,
           'canonical engagement and target retained')
        ok(srv.protect_calls==1 and actor.waves==[(mob.key,True)], 'canonical party protector and boss opener')
        ok(actor.starts==1 and srv.world.refreshed>=1,'canonical realtime combat started')
        ok(len(srv.room_notices)==1,'real room broadcast on opening')
        cast('Rzeczywisty Strażnik')
        ok(len(actor.xp)==1,'no XP for no existing buff')
        print(f'V107 MAGITEK ETAP 4 PRAWDZIWY CELOWNIK: {checks} kontroli PASS')
        return checks
    finally:
        if old is None:MOB_TEMPLATES.pop(mob.template_id,None)
        else:MOB_TEMPLATES[mob.template_id]=old

if __name__=='__main__':run()
