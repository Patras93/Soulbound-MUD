# -*- coding: utf-8 -*-
"""OLC16 deterministic regression: on-hit statuses share the existing combat engine.

This file intentionally does not boot a server or touch a player's SQLite DB.
Those checks are provided by the full PREDEPLOY 60 PLUS on Windows.
"""
import asyncio
import math
from types import SimpleNamespace
from systems.live_olc19_status_skills import (
    parse_status, apply_skill_status_v1900, cast_with_olc_status_v1900)
from systems.summon_status_v1808 import summon_status_enemy_turn_v1808


def run():
    n=0
    def ok(expr):
        nonlocal n
        assert expr
        n+=1
    for k in ('poison','burn','freeze','shock'):
        parsed=parse_status({'kind':k,'chance':0.5})
        ok(parsed=={'kind':k,'chance':0.5})
    ok(parse_status('auto') is None)
    ok(parse_status('-') is None)
    ok(parse_status('{"kind":"poison","chance":0.3}')['chance']==0.3)
    invalid=({},[],{'kind':'poison'},{'kind':'bad','chance':0.2},
             {'kind':'burn','chance':1.1},{'kind':'shock','chance':-0.2},
             {'kind':'poison','chance':True},{'kind':'poison','chance':float('nan')},
             {'kind':'poison','chance':0.3,'code':'import os'}, 'no-json')
    for value in invalid:
        try:parse_status(value)
        except (ValueError,TypeError):ok(True)
        else:raise AssertionError(f'Zaakceptowano status {value!r}')

    def mob(hp=1000, key='m'):
        return SimpleNamespace(key=key,hp=hp,alive=True,room_id='room',
                               template_id='wolf',adaptive_max_hp_v11330=hp)
    normal={'max_hp':1000}
    for kind in ('poison','burn','freeze','shock'):
        target=mob()
        msg=apply_skill_status_v1900(target,{'kind':kind,'chance':1.0},200,normal,now=10,roll=0)
        ok(bool(msg))
        ok(kind in target.v1808_summon_statuses)
        ok(not apply_skill_status_v1900(target,{'kind':kind,'chance':1.0},200,normal,now=11,roll=0))
        ok(target.hp==1000) # status does not modify direct damage
        if kind in ('poison','burn'):
            msg,skip,killed=summon_status_enemy_turn_v1808(target,now=14)
            ok(not skip and not killed)
            ok(target.hp<1000 and 'obrażeń okresowych' in msg[0])
            ok('kobry' not in msg[0] and 'żywiołaka' not in msg[0])
        else:
            msg,skip,killed=summon_status_enemy_turn_v1808(target,now=11)
            ok(skip and not killed)
            ok('umiejętność' in msg[0])
            _msg,skip_again,_dead=summon_status_enemy_turn_v1808(target,now=11.1)
            ok(not skip_again)
    target=mob()
    ok(not apply_skill_status_v1900(target,{'kind':'poison','chance':.25},300,normal,now=10,roll=.99))
    ok(not target.v1808_summon_statuses)
    # No artificial cap at high levels: integer-percent DOT from a giant hit.
    huge=mob(hp=10**90)
    apply_skill_status_v1900(huge,{'kind':'poison','chance':1.0},10**60,
                              {'max_hp':10**90},now=10,roll=0)
    ok(huge.v1808_summon_statuses['poison']['power']==(10**60*7)//100)
    boss=mob()
    ok(not apply_skill_status_v1900(boss,{'kind':'shock','chance':.2},300,{'boss':True,'max_hp':1000},now=10,roll=.15))
    ok(not boss.v1808_summon_statuses)
    dead=mob(0)
    ok(not apply_skill_status_v1900(dead,{'kind':'poison','chance':1.},300,normal,now=10,roll=0))
    ok(not apply_skill_status_v1900(mob(),{'kind':'poison','chance':1.},0,normal,now=10,roll=0))
    # One shared status pool: avoid endless control effects and DOT reloads.
    mixed=mob()
    apply_skill_status_v1900(mixed,{'kind':'shock','chance':1.},300,normal,now=10,roll=0)
    ok(not apply_skill_status_v1900(mixed,{'kind':'freeze','chance':1.},300,normal,now=11,roll=0))
    apply_skill_status_v1900(mixed,{'kind':'poison','chance':1.},300,normal,now=11,roll=0)
    ok(not apply_skill_status_v1900(mixed,{'kind':'burn','chance':1.},300,normal,now=11,roll=0))
    ok(len(mixed.v1808_summon_statuses)==2)
    small=mob(hp=1)
    apply_skill_status_v1900(small,{'kind':'poison','chance':1.},50,{'max_hp':1000},now=10,roll=0)
    lines,skip,killed=summon_status_enemy_turn_v1808(small,now=14)
    ok(killed and skip and small.hp==0 and len(lines)==1)

    # Runtime wrapper delegates failed spells, does not add status without hit.
    async def no_hit(self,raw):return 'no-hit'
    class Session:
        def __init__(self):
            self.character=SimpleNamespace(room_id='room')
            self._recap52_dealt=0
            self.combat_mob_key='m'
            self.m=mob()
            self.server=SimpleNamespace(world=SimpleNamespace(room_mobs=lambda _room:[self.m]),party_combat_broadcast=self.broadcast)
        async def broadcast(self,*args,**kwargs):
            return None
        def find_skill_from_input(self,raw):
            return {'id':'live_test','name':'Test','kind':'damage','olc_status':{'kind':'poison','chance':1.}},''
    s=Session()
    ok(asyncio.run(cast_with_olc_status_v1900(s,'test',no_hit))=='no-hit')
    ok(not hasattr(s.m,'v1808_summon_statuses'))
    async def successful(self,raw):
        self.m.hp -= 100
        self._recap52_dealt += 100
        return 'hit'
    ok(asyncio.run(cast_with_olc_status_v1900(s,'test',successful,{'wolf':{'max_hp':1000}}))=='hit')
    ok('poison' in s.m.v1808_summon_statuses)
    ok(s.m.hp==900)
    # AoE keeps its own damage statistics, yet still installs status per target.
    s2=Session()
    s2.find_skill_from_input=lambda raw:({'id':'live_aoe','name':'AOE','kind':'aoe_damage','olc_status':{'kind':'burn','chance':1.0}},'')
    s2.n=mob(key='n')
    s2.server.world.room_mobs=lambda _room:[s2.m,s2.n]
    async def successful_aoe(self,raw):
        self.m.hp -= 120
        self.n.hp -= 90
        return 'aoe'
    ok(asyncio.run(cast_with_olc_status_v1900(s2,'test',successful_aoe,{'wolf':{'max_hp':1000}}))=='aoe')
    ok('burn' in s2.m.v1808_summon_statuses)
    ok('burn' in s2.n.v1808_summon_statuses)
    return n


if __name__=='__main__':
    print('OLC v19.00.0',run(),'PASS')
