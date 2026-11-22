# -*- coding: utf-8 -*-
"""Actual learned-skill first-rotation HP floor (isolated, no player DB)."""
from __future__ import annotations

import math
import sqlite3
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import ast

from systems.encounter_burst_v11656 import member_skill_burst_v11656,party_skill_burst_v11656
from systems.adaptive_combat import (authored_party_damage_target_hp_v11652,
    authored_stage_combat_level_v11651,adaptive_combat_rank_v11330)


def run():
    n=0
    def check(cond, name):
        nonlocal n
        n+=1
        if not cond:raise AssertionError('BURST v11656 '+name)

    class DB:
        def __init__(self):
            self.progress={}
            self.calls=0
            self.conn=sqlite3.connect(':memory:')
            self.conn.execute('CREATE TABLE summons_v1700(account_id INT,active INT,hp INT)')
        def learned_skill_ids(self, account):
            self.calls+=1
            return {key for aid,key in self.progress if aid==account}
        def skill_progress(self,account,key):
            self.calls+=1
            return {'level':self.progress[(account,key)]}
        def mercenary_contracts(self,aid):
            return [dict(expires_at=0) for _ in range(3)]
    class Character:
        character_level=85
        soul_level=85
        class_name='Mec'
        room_id='mythic_room'
        def class_physical_damage_multiplier(self):return 1.0
        def racial_physical_damage_multiplier(self):return 1.0
        def class_magic_damage_multiplier(self):return 1.0
        def racial_magic_damage_multiplier(self):return 1.0
        def racial_all_damage_multiplier(self):return 1.0
    class Actor:
        def __init__(self,aid,db):
            self.account_id=aid; self.server=SimpleNamespace(db=db)
            self.character=Character();self.closed=False;self.current_hp=100
            self.skill_calls=0;self.dps_calls=0
        def class_skills(self):
            return [dict(id='mec_blast',kind='aoe_damage',mult=1.0,scale='intelligence'),
                    dict(id='mec_unknown',kind='aoe_damage',mult=1000),
                    dict(id='mec_compress',kind='damage',mec_special='compress',mult=100000)]
        def offensive_skill_core_power_v11185(self,skill):
            self.skill_calls+=1
            return 120000
        def offensive_skill_damage_type_v11190(self,skill):return 'magic'
        def total_set_damage_multiplier(self):return 1.
        def equipment_damage_multiplier(self,k):return 1.
        def skill_buff_multiplier(self,**k):return 1.
        def critical_multiplier(self):return 2.
        def adaptive_party_members_v11330(self,mob):return members
        def adaptive_mob_has_active_fighters_v1261(self,mob):return False
        def adaptive_party_dps_v1261(self,mm):
            self.dps_calls+=1
            return 8000 * len(mm)  # weak autoattacks, giant learned burst
    db=DB();members=[Actor(i,db) for i in (1,2,3)]
    for i in (1,2,3):db.progress[(i,'mec_blast')]=1;db.progress[(i,'mec_compress')]=1
    with patch('systems.party_synergies.party_synergy_damage_multiplier_v11338',return_value=1.):
        p=party_skill_burst_v11656(members,now=10.)
        check(p >= 3*120000, 'three truly learned skills contribute to party burst')
        calls=db.calls
        check(p==party_skill_burst_v11656(members,now=12.) and db.calls==calls,
              'cached forecast does not query DB repeatedly')
        check(all(a.skill_calls==1 for a in members), 'unknown and percent skills excluded')
        check(db.progress=={(i,k):1 for i in (1,2,3) for k in ('mec_blast','mec_compress')},
              'skill levels not modified')
        t={'mythic_crypt_floor':1,'generator_level':116,'max_hp':55000,'rank':'normal'}
        ordinary=authored_party_damage_target_hp_v11652(t,55000,85,24000,real_players=3)
        target=authored_party_damage_target_hp_v11652(t,55000,85,24000,real_players=3,skill_burst=p)
        check(target >= 2*p and target>ordinary,'no one-hit from first full trained-skill round')
        check(target < 6*p,'roughly two rotations, not fifty-rotation sponge')
        assisted=authored_party_damage_target_hp_v11652(
            t,55000,85,24000,real_players=3,mercenaries=9,companions=3,
            skill_burst=p)
        check(assisted > target and assisted <= 4*p,
              'hires/pets add bounded realistic pressure, without counting as players')
        old={'generator_level':3,'max_hp':100,'rank':'normal'}
        check(authored_party_damage_target_hp_v11652(old,100,85,24000,
             real_players=3,skill_burst=p)==100,'old beginner goblin remains weak')
        tower={'astral_floor':50,'max_hp':5000,'rank':'normal'}
        check(authored_party_damage_target_hp_v11652(tower,5000,85,24000,
             real_players=3,skill_burst=p)>=2*p,
             'tower floor 50 remains relevant at level 85')
        check(authored_party_damage_target_hp_v11652(tower,5000,85,24000,
             real_players=3,skill_burst=0)==5000,
             'weak/no-skill player never receives new penalty')
        # Rank boss retains meaningful but bounded difficulty.
        boss=dict(t,rank='boss')
        check(authored_party_damage_target_hp_v11652(boss,55000,85,24000,
             skill_burst=p)>=4*p,'boss lasts longer than ordinary')

    # Exercise actual v116.56 production scaler with the mocked actual party.
    src=Path(__file__).resolve().parents[1]/'player/session_mixins/combat_damage.py'
    root=ast.parse(src.read_text('utf-8'))
    cls=next(x for x in root.body if isinstance(x,ast.ClassDef)
             and x.name=='SessionCombatDamageMixin')
    method=next(x for x in cls.body if isinstance(x,ast.FunctionDef)
                and x.name=='apply_adaptive_mob_scale_v11330')
    with patch('systems.party_synergies.party_synergy_damage_multiplier_v11338',return_value=1.), \
         patch('systems.adaptive_switch_v102006.enabled',return_value=False):
        env={'MOB_TEMPLATES':{'mythic':t,'tower':tower,'old':old},
             'ROOMS':{'mythic_room':{},'tower_room':{},'old_room':{}},
             'math':math,'sys':sys,'sqlite3':sqlite3,
             'authored_stage_combat_level_v11651':authored_stage_combat_level_v11651,
             'authored_party_damage_target_hp_v11652':authored_party_damage_target_hp_v11652,
             'adaptive_combat_rank_v11330':adaptive_combat_rank_v11330}
        exec(compile(ast.fix_missing_locations(ast.Module(body=[method],type_ignores=[])),str(src),'exec'),env)
        apply=env['apply_adaptive_mob_scale_v11330']
        mob=SimpleNamespace(key='m',template_id='mythic',room_id='mythic_room',hp=55000,alive=True)
        first=apply(members[0],mob)
        check(first and mob.hp>=2*p,'production scales mob before any first attack')
        check(first['reward_multiplier']==1.,'no XP inflation from HP adjustment')
        before=mob.hp
        second=apply(members[0],mob)
        check(mob.hp==before and second['max_hp']==first['max_hp'], 'no repeated healing')
        members[0].character.room_id='tower_room'
        tower_mob=SimpleNamespace(key='t',template_id='tower',room_id='tower_room',hp=5000,alive=True)
        check(apply(members[0],tower_mob) is not None and tower_mob.hp>=2*p,
              'production tower path correct')
    db.conn.close()
    print(f'LEARNED SKILL BURST v116.00.56: {n} PASS',flush=True)
    return n

if __name__=='__main__':run()
