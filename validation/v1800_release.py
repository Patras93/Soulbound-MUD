# -*- coding: utf-8 -*-
"""Focused checks of additive 1.80.0 content, tactics and balance contracts."""
import asyncio
import sqlite3
import sys
from unittest.mock import patch
from types import SimpleNamespace
from core.classes_skills import CLASSES
from systems.era_chaos_v1800 import CHAOS_REALMS, CLASS_MASTERY, compute_reaction
from player.session_mixins.chaos_v1800 import SessionChaosV1800Mixin, ensure_combat_v1800


def check_content(rooms,mobs,quests,items):
    checks=0
    assert len(CLASS_MASTERY)==len(CLASSES)==14;checks+=1
    assert rooms['v1700_city_market']['exits']['west']=='v1800_portal';checks+=1
    assert rooms['v1800_portal']['exits']['east']=='v1700_city_market';checks+=1
    for slug,_,_,_,bosses in CHAOS_REALMS:
        assert len(bosses)==3
        for i in range(4):
            room=f'v1800_{slug}_{i}'
            assert room in rooms
            for direction,target in rooms[room]['exits'].items():
                assert target in rooms, (room,direction,target)
                assert room in rooms[target]['exits'].values(),(room,target)
                checks+=2
        for j in range(3):
            mob=f'v1800_{slug}_boss_{j}'
            assert mobs[mob]['v1800_chaos_boss'] is True
            assert quests[f'v1800_hunt_{slug}_{j}']['target']==mob
            assert mobs[mob]['drops'][f'v1800_{slug}_sigil']==1.0
            checks+=3
        assert f'v1800_{slug}_sigil' in items;checks+=1
    assert compute_reaction('fire','ice',1000)==('Szok Termiczny',90);checks+=1
    assert compute_reaction('fire','fire',1000)==('',0);checks+=1
    assert compute_reaction('fire','ice',0)==('Szok Termiczny',0);checks+=1
    assert max(compute_reaction('fire',el,1000)[1] for el in ['ice','lightning','dark'])<=100;checks+=1
    return checks


class _Mock(SessionChaosV1800Mixin):
    def __init__(self):
        conn=sqlite3.connect(':memory:');conn.row_factory=sqlite3.Row
        self.server=SimpleNamespace(db=SimpleNamespace(conn=conn),world=SimpleNamespace(mobs={}),party_combat_broadcast=self._party_send)
        self.character=SimpleNamespace(class_name='Mag',class_type='magic',character_level=160,room_id='arena')
        self.account_id=2;self.current_hp=550;self.current_mana=500;self.skill_guard=0
        self.combat_mob_key=None;self.messages=[]
    def _v1700_conn(self):return self.server.db.conn
    def max_hp(self):return 1000
    async def send(self,text):self.messages.append(text)
    async def _party_send(self,session,text,detail='essential'):self.messages.append(text)
    async def apply_boss_defense(self,mob,amount):return amount
    def v0210_adjust_player_damage(self,amount):return amount
    def spell_power(self):return 1000
    def physical_power(self):return 1000
    def mob_effective_max_hp_v11330(self,mob,template):return mob.max_hp
    async def mob_defeated(self,mob):self.messages.append('DEFEATED')


def check_runtime():
    a=_Mock();checks=0
    ensure_combat_v1800(a._v1700_conn());a.server.db._v1800_ready=True
    assert a._v1800_tactic()=='szturm';checks+=1
    asyncio.run(a.tactics_v1800('bastion'))
    assert a._v1800_tactic()=='bastion';checks+=1
    assert a._v1800_form_bonus()==(.94,.04);checks+=1
    a2=_Mock();a2.server.db=a.server.db
    assert a2._v1800_tactic()=='bastion';checks+=1
    asyncio.run(a2.tactics_v1800('harmonia'))
    assert a2._v1800_form_bonus()==(.97,.015);checks+=1
    asyncio.run(a2.tactics_v1800('nieistniejaca'))
    assert a2._v1800_tactic()=='harmonia';checks+=1
    asyncio.run(a.class_mastery_v1800(''))
    assert 'Arkaniczne' in a.messages[-1];checks+=1
    a.character.character_level=149
    asyncio.run(a.class_mastery_v1800('uzyj'))
    assert 'poziomu 150' in a.messages[-1] and a.current_mana==500;checks+=1
    a.character.character_level=160
    asyncio.run(a.class_mastery_v1800('uzyj'))
    assert 'najpierw walczy' in a.messages[-1] and a.current_mana==500;checks+=1
    # Guard & heal branches can be exercised without a simulated enemy.
    a.character.class_name='Strażnik';a.character.class_type='physical'
    asyncio.run(a.class_mastery_v1800('uzyj'))
    assert a.skill_guard>=80 and a.current_mana==500;checks+=1
    before=a.skill_guard
    asyncio.run(a.class_mastery_v1800('uzyj'))
    assert a.skill_guard==before and 'sekund' in a.messages[-1];checks+=1
    # Actual mage mastery damages an active target, bills MP and persists cooldown.
    a3=_Mock()
    enemy=SimpleNamespace(template_id='v1800_popiol_boss_0',room_id='arena',alive=True,
                          hp=100000,max_hp=100000,key='boss')
    a3.server.world.mobs['boss']=enemy;a3.combat_mob_key='boss'
    with patch.dict(sys.modules,{'world.machine_expansion': SimpleNamespace(
            v0314_adjust_damage_vs_template=lambda template,damage,kind,label:(damage,''))}):
        asyncio.run(a3.class_mastery_v1800('uzyj'))
    assert enemy.hp<100000 and a3.current_mana==390;checks+=1
    before=enemy.hp
    asyncio.run(a3.class_mastery_v1800('uzyj'))
    assert enemy.hp==before and 'sekund' in a3.messages[-1];checks+=1
    from data.mobs import MOB_TEMPLATES
    with patch.dict(MOB_TEMPLATES,{'v1800_popiol_boss_0': {'name':'Test Chaos', 'v1800_chaos_boss':True}}):
        asyncio.run(a3.chaos_boss_phase_v1800(enemy))
        assert int(getattr(enemy,'_v1800_chaos_phase',0))==0;checks+=1
        enemy.hp=49000
        asyncio.run(a3.chaos_boss_phase_v1800(enemy))
        assert enemy._v1800_chaos_phase==2;checks+=1
        current=len(a3.messages)
        asyncio.run(a3.chaos_boss_phase_v1800(enemy))
        assert len(a3.messages)==current;checks+=1
        enemy.hp=24900
        asyncio.run(a3.chaos_boss_phase_v1800(enemy))
        assert enemy._v1800_chaos_phase==3;checks+=1
    async def reactions():
        mob=SimpleNamespace()
        v1=await a3._v1800_elemental_reaction(mob,'fire',1000)
        v2=await a3._v1800_elemental_reaction(mob,'ice',1000)
        v3=await a3._v1800_elemental_reaction(mob,'lightning',1000)
        return v1,v2,v3
    assert asyncio.run(reactions())==(0,90,0);checks+=1
    return checks


if __name__=='__main__':
    print('ERA 1.80: tactical/runtime checks',check_runtime())
