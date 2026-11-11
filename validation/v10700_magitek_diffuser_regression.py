# -*- coding: utf-8 -*-
"""Magitek stage 4: real enemy guard/empower removal, no PVP or boss bypass."""
from __future__ import annotations
import asyncio
import time
from types import SimpleNamespace

from core.magitek.catalogue import skill_catalogue
from systems.magitek.support import (
    removable_enemy_buffs, dispel_enemy_buffs, use_support_skill,
)
from systems.monster_ai import (
    monster_ai_guard_damage_v1160, monster_ai_attack_multiplier_v1160,
)
from validation.v10700_magitek_support_regression import Actor, Server
from data.mobs import MOB_TEMPLATES

SKILL = next(x for x in skill_catalogue() if x['v107_skill'] == 'diffuser')


class Enemy:
    def __init__(self, name, room='temple_basement'):
        self.key='v107_diffuser_'+name
        self.template_id='v107_diffuser_test_'+name
        self.room_id=room
        self.hp=900
        self.alive=True
        self.engaged_by=None
        self.monster_ai_guard_until_v1160=0.0
        self.monster_ai_empowered_until_v1160=0.0
        self.uoss_permanent_protect_v11176=True
        self.uoss_permanent_shell_v11176=True
        self.v1230_phase_attack_multiplier=1.43


class RealTargetActor(Actor):
    def __init__(self, name, server):
        super().__init__(name,server)
        self.block_names=set()
        self.hostile_called=[]
        self.started=0
    async def skill_combat_target(self, query):
        self.hostile_called.append(query)
        # Stand-in for canonical target gates; record denials as in engine.
        for m in self.server.mobs:
            if m.room_id!=self.character.room_id or not m.alive:
                continue
            if query.casefold() != MOB_TEMPLATES[m.template_id]['name'].casefold():
                continue
            if query in self.block_names:
                await self.send('Walka z tym celem jest zabroniona.')
                return None
            self.combat_mob_key=m.key
            return m
        await self.send('Nie widzę tutaj takiego przeciwnika.')
        return None
    async def ensure_realtime_combat(self):self.started+=1


def run():
    count=0
    def ok(condition, note):
        nonlocal count
        assert condition, note
        count+=1
    srv=Server()
    srv.mobs=[]
    actor=RealTargetActor('Badacz',srv)
    teammate=Actor('Sympatyczna',srv)
    enemy=Enemy('magic')
    remote=Enemy('remote','square')
    srv.mobs=[enemy,remote]
    old = {}
    for mob in srv.mobs:
        old[mob.template_id]=MOB_TEMPLATES.get(mob.template_id)
        MOB_TEMPLATES[mob.template_id]={'name': 'Strażnik' if mob is enemy else 'Odległy'}
    try:
        now=time.monotonic()
        enemy.monster_ai_guard_until_v1160=now+60
        enemy.monster_ai_empowered_until_v1160=now+60
        ok(monster_ai_guard_damage_v1160(enemy,100,now=now)==80,'real guard reduces damage')
        ok(monster_ai_attack_multiplier_v1160(enemy,now=now)>1,'real attack buff increases damage')
        ok(len(removable_enemy_buffs(enemy,now))==2,'real active buffs detected')
        ok(removable_enemy_buffs(enemy,now+61)==(), 'expired statuses never removed')
        before_hp=enemy.hp
        asyncio.run(use_support_skill(actor, SKILL, 'at Strażnik'))
        ok(not removable_enemy_buffs(enemy),'both buffs removed')
        ok(monster_ai_guard_damage_v1160(enemy,100)==100,'guard gone in real damage calculation')
        ok(monster_ai_attack_multiplier_v1160(enemy)==1,'attack buff gone in real damage calculation')
        ok(enemy.hp==before_hp,'Diffuser never directly damages enemy')
        ok(enemy.uoss_permanent_protect_v11176 and enemy.uoss_permanent_shell_v11176,
           'inherent UOSS Protect/Shell not dispelled')
        ok(enemy.v1230_phase_attack_multiplier==1.43,'intrinsic boss phase remains intact')
        ok(actor.xp==['diffuser'],'successful hostile use grants XP once')
        ok(actor.hostile_called[-1]=='Strażnik','UOSS at target syntax normalized')
        ok(actor.started==1,'real combat resumes after hostile use')
        ok('osłona potwora' in actor.sent[-1] and 'wzmocnienie' in actor.sent[-1], 'NVDA text names buffs')
        old_xp=len(actor.xp)
        asyncio.run(use_support_skill(actor,SKILL,'Strażnik'))
        ok(len(actor.xp)==old_xp and 'nie ma' in actor.sent[-1],'no EXP on empty hostile buffs')
        ok(actor.started==1,'no extra real-time combat on no-effect cast')
        remote.monster_ai_guard_until_v1160=now+60
        asyncio.run(use_support_skill(actor,SKILL,'Odległy'))
        ok(len(removable_enemy_buffs(remote))==1,'remote enemy unchanged')
        ok(len(actor.xp)==old_xp,'no EXP from remote mob')
        # An enemy with a non-engageable boss protection remains invulnerable.
        enemy.monster_ai_guard_until_v1160=now+60
        actor.block_names.add('Strażnik')
        asyncio.run(use_support_skill(actor,SKILL,'Strażnik'))
        ok(len(removable_enemy_buffs(enemy))==1,'engagement blocker preserves buff')
        ok(len(actor.xp)==old_xp,'engagement blocker no XP')
        actor.block_names.clear()
        enemy.hp=0
        asyncio.run(use_support_skill(actor,SKILL,'Strażnik'))
        ok(len(removable_enemy_buffs(enemy))==0,'dead targets expose no statuses')
        ok(enemy.monster_ai_guard_until_v1160>0,'dead target state untouched')
        enemy.hp=900
        # Two valid statuses cannot be confused with negative/expired statuses.
        enemy.monster_ai_guard_until_v1160=now-5
        enemy.monster_ai_empowered_until_v1160=now+30
        labels=dispel_enemy_buffs(enemy,now)
        ok(labels==('wzmocnienie ataku',),'only active status removed')
        ok(enemy.monster_ai_guard_until_v1160==now-5,'expired guard remains as stored')
        ok(enemy.monster_ai_empowered_until_v1160==0,'active attack bonus actually cleared')
        # Do not strip negative effects; only explicitly allowlisted positive buffs.
        enemy.v0319_poison_until=time.time()+20
        enemy.monster_ai_guard_until_v1160=now+30
        dispel_enemy_buffs(enemy,now)
        ok(enemy.v0319_poison_until>time.time(),'poison survives Diffuser')
        # No accidental player-target/PVP attack: local ally gets helpful removal.
        teammate.active_skill_buffs={'ward':{'until':time.time()+50,'beneficial':True}}
        calls=len(actor.hostile_called)
        asyncio.run(use_support_skill(actor,SKILL,'Sympatyczna'))
        ok(not teammate.active_skill_buffs and len(actor.hostile_called)==calls,
           'friendly target bypasses hostile resolver and dispels buff')
        # Missing learned skill or insufficient mastery: no enemy changes.
        enemy.monster_ai_guard_until_v1160=now+30
        srv.db.learned.remove(SKILL['id'])
        asyncio.run(use_support_skill(actor,SKILL,'Strażnik'))
        ok(len(removable_enemy_buffs(enemy))==1,'unlearned Magitek cannot dispel')
        srv.db.learned.add(SKILL['id'])
        actor.level=7
        asyncio.run(use_support_skill(actor,SKILL,'Strażnik'))
        ok(len(removable_enemy_buffs(enemy))==1,'underlevel caster cannot dispel')
        actor.level=40
        actor.current_hp=0
        asyncio.run(use_support_skill(actor,SKILL,'Strażnik'))
        ok(len(removable_enemy_buffs(enemy))==1,'dead player cannot dispel')
        actor.current_hp=100
        # No query targets self, never an arbitrary enemy.
        old_calls=len(actor.hostile_called)
        asyncio.run(use_support_skill(actor,SKILL,''))
        ok(len(actor.hostile_called)==old_calls,'empty argument targets player, never enemy')
        print(f'V107 MAGITEK ETAP 4 DIFFUSER: {count} kontroli PASS')
        return count
    finally:
        for key,value in old.items():
            if value is None:MOB_TEMPLATES.pop(key,None)
            else:MOB_TEMPLATES[key]=value

if __name__=='__main__':run()
