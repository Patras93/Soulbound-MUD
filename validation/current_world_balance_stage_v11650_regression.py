# -*- coding: utf-8 -*-
"""Global underlevel health floor, 1–6 real players and active helpers.

No production SQLite, no TCP, no change to player or assistant damage.
"""
from __future__ import annotations
import ast
import math
import random
import sqlite3
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from systems.adaptive_combat import (
    authored_stage_challenge_multiplier_v11650,
    adaptive_encounter_stage_v2325,
    adaptive_combat_rank_v11330,
)


def run():
    checks=0
    def check(ok,why):
        nonlocal checks
        checks+=1
        if not ok:raise AssertionError(f'WORLD BALANCE v11650: {why}')
    template={'name':'Strażnik Krypty','max_hp':10000,'damage':100,
              'generator_level':120,'crypt_floor':120,'rank':'normal'}
    check(authored_stage_challenge_multiplier_v11650(template,68)>1,
          'higher-level crypt must not be trivial')
    for rank in ('normal','elite','rare','mini','boss','world_boss'):
        for stage in (1,10,40,68,80,100,200,400,800,2000):
            spec={'rank':rank,'generator_level':stage}
            check(authored_stage_challenge_multiplier_v11650(spec,stage)==1.0,
                  f'equal-level {rank} {stage}')
            check(authored_stage_challenge_multiplier_v11650(spec,stage+50)==1.0,
                  f'overlevel {rank} {stage}')
            check(authored_stage_challenge_multiplier_v11650(spec,max(1,stage-10))>=1,
                  f'underlevel {rank} {stage}')
    check(authored_stage_challenge_multiplier_v11650({'training_dummy':True,'generator_level':800},1)==1,
          'training protected')
    check(authored_stage_challenge_multiplier_v11650({},1)==1,'hub/unknown mob')
    check(authored_stage_challenge_multiplier_v11650(template,68,real_players=4,
          mercenaries=12,companions=4)>authored_stage_challenge_multiplier_v11650(template,68),
          'team assistance changes underlevel durability')
    check(authored_stage_challenge_multiplier_v11650(template,68,real_players=6,
          mercenaries=18,companions=6)<=120,'bounded six-player multiplier')
    # Compile the actual production method, avoiding a full 37k-room world boot.
    source=Path(__file__).resolve().parents[1]/'player/session_mixins/combat_damage.py'
    tree=ast.parse(source.read_text('utf-8'))
    clazz=next(n for n in tree.body if isinstance(n,ast.ClassDef)
               and n.name=='SessionCombatDamageMixin')
    fn=next(n for n in clazz.body if isinstance(n,ast.FunctionDef)
            and n.name=='apply_adaptive_mob_scale_v11330')
    ns={'ROOMS':{'crypt_room':{'generator_level':120}},
        'MOB_TEMPLATES':{'crypt_test':template},
        'adaptive_combat_rank_v11330':adaptive_combat_rank_v11330,
        'adaptive_encounter_stage_v2325':adaptive_encounter_stage_v2325,
        'math':math,'random':random,'sqlite3':sqlite3,'sys':sys}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),
                 str(source),'exec'),ns)
    apply=ns['apply_adaptive_mob_scale_v11330']
    class Db:
        def __init__(self):
            self.calls=0
            self.conn=sqlite3.connect(':memory:')
            self.conn.execute('CREATE TABLE summons_v1700 (account_id INT,active INT,hp INT)')
            self.conn.executemany('INSERT INTO summons_v1700 VALUES(?,?,?)',
                                  [(i,1,100) for i in range(1,7)])
        def mercenary_contracts(self,aid):
            self.calls+=1
            return ({'expires_at':0} for _ in range(3))
    db=Db()
    sessions=[]
    class Actor:
        def __init__(self,aid,level):
            self.account_id=aid;self.character=SimpleNamespace(character_level=level,room_id='crypt_room')
            self.server=SimpleNamespace(db=db);self.closed=False;self.current_hp=100
        def adaptive_party_members_v11330(self,mob):return sessions[:]
        def adaptive_mob_has_active_fighters_v1261(self,mob):return False
    sessions.extend(Actor(i,68) for i in range(1,5))
    mob=SimpleNamespace(key='mob',template_id='crypt_test',room_id='crypt_room',hp=10000,alive=True)
    with patch('systems.adaptive_switch_v102006.enabled',return_value=False):
        first=apply(sessions[0],mob)
        check(first and first['max_hp']>10000,'first fight more HP')
        check(first['party_size']==4,'only real players in party count')
        check(first['reward_multiplier']==1.0,'no additional EXP/Fame')
        check(db.calls==4,'4 owners queried once')
        mx=mob.hp
        mob.hp=mx//2
        after=apply(sessions[0],mob)
        check(after['max_hp']==first['max_hp'] and mob.hp==mx//2,
              'repeated checks do not heal an injured enemy')
        check(db.calls==4,'mercenary cache avoids 12 SQL scans every round')
        sessions.extend(Actor(i,68) for i in range(5,7))
        expanded=apply(sessions[0],mob)
        check(expanded['max_hp']>=first['max_hp'],'6 real players raise the target')
        check(expanded['party_size']==6,'6 slots regardless of 18 contracts and pets')
        check(expanded['reward_multiplier']==1.0,'6-player reward remains authored')
        db.conn.close()
    print(f'WORLD STAGE AND SIX-PLAYER BALANCE v116.00.50: {checks} PASS',flush=True)
    return checks

if __name__=='__main__':run()
