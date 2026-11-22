# -*- coding: utf-8 -*-
"""World-wide anti-one-shot soft floor, tested without production SQLite/network."""
from __future__ import annotations

import ast
import math
import sqlite3
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from systems.adaptive_combat import (
    adaptive_combat_rank_v11330,
    authored_stage_challenge_multiplier_v11650,
    authored_stage_combat_level_v11651,
    authored_party_damage_target_hp_v11652,
    V11652_COMBAT_HP_CEILINGS,
)


def run():
    count = 0

    def check(condition, label):
        nonlocal count
        count += 1
        if not condition:
            raise AssertionError(f'GLOBAL PARTY DPS v11652: {label}')

    for rank in ('normal', 'elite', 'rare', 'mini', 'boss', 'world_boss'):
        for stage in (1, 20, 50, 85, 100, 116, 139, 200, 800, 30000):
            template = {'generator_level': stage, 'rank': rank,
                        'max_hp': 12000, 'damage': 220, 'class_xp_reward': 555}
            original = dict(template)
            for level in (1, 20, 73, 85, 150, 800, 1000):
                for party, hires, pets in ((1,0,0), (2,6,2), (3,9,3), (4,12,4), (6,18,6)):
                    prev = 12000
                    for dps in (0, 2500, 10000, 100000, 1000000):
                        result = authored_party_damage_target_hp_v11652(
                            template, 12000, level, dps,
                            real_players=party, mercenaries=hires, companions=pets)
                        check(result >= prev, f'monotone DPS: {rank}/{stage}/{level}/{party}/{dps}')
                        check(result <= 12000 * V11652_COMBAT_HP_CEILINGS[rank],
                              f'health bound: {rank}/{stage}/{level}/{party}/{dps}')
                        if level >= stage + 16:
                            check(result == 12000, f'old zone remains easy: {rank}/{stage}/{level}')
                        if dps == 0:
                            check(result == 12000, 'weak party never has HP penalty for helper count')
                        prev = result
            check(original == template, f'catalog immutable: {rank}/{stage}')

    for rank in ('normal', 'elite', 'rare', 'mini', 'boss', 'world_boss'):
        template = {'generator_level': 85, 'rank': rank}
        baseline = authored_party_damage_target_hp_v11652(template, 10000, 85, 12000, real_players=1)
        for party, hires, pets in ((2,6,2), (3,9,3), (6,18,6)):
            value = authored_party_damage_target_hp_v11652(
                template, 10000, 85, 12000 * party, real_players=party,
                mercenaries=hires, companions=pets)
            check(value >= baseline, f'local party {party}: rank {rank}')
    check(authored_stage_combat_level_v11651(
        {'crypt_floor': 60, 'generator_level': 139}) == 80,
          'normal crypt60 recommended level 80, not duplicate generator 139')
    check(authored_stage_combat_level_v11651(
        {'mythic_crypt_floor': 1, 'generator_level': 116}) == 116,
          'mythic first floor is genuine late-game stage, not level 61')
    t = {'crypt_floor': 60, 'generator_level': 139, 'rank':'normal'}
    base = 139071
    weak = authored_party_damage_target_hp_v11652(t, base, 73, 4000,
        real_players=2, mercenaries=6, companions=2)
    stage_multiplier = authored_stage_challenge_multiplier_v11650(t, 73,
        real_players=2, mercenaries=6, companions=2)
    check(weak == base and base < round(base * stage_multiplier) < 200000,
          'two level73 players on crypt floor60 never get v116.50 x33 HP')
    mythic = {'mythic_crypt_floor':1, 'generator_level':116, 'rank':'normal'}
    strong = authored_party_damage_target_hp_v11652(
        mythic, 55000, 85, 240000, real_players=3,
        mercenaries=9, companions=3)
    check(55000 * 4 < strong <= 55000 * 40,
          'strong level85 3-player mythic encounter should resist a single team burst')
    check(authored_party_damage_target_hp_v11652(
        mythic, 55000, 145, 240000, real_players=3,
        mercenaries=9, companions=3) == 55000,
          'high-level hero farming old mythic floor has no forced scaling')
    check(authored_party_damage_target_hp_v11652(
        {'training_dummy':True,'generator_level':120},1,85,10**12,6,18,6) == 1,
          'training dummy stays untouched')
    check(authored_party_damage_target_hp_v11652(
        {'name':'unknown'},10000,85,10**12,6,18,6) == 10000,
          'unknown stage stays untouched')
    check(authored_party_damage_target_hp_v11652(
        {'generator_level':10**12},10**60,85,10**100,
        real_players=6,mercenaries=18,companions=6) > 10**60,
          'large-number levels and HP do not overflow')

    # Compile REAL production method, but run it against read-only isolated
    # fakes. The test must exercise a same-level mob (old v11651 early return),
    # the cache and the existing no-heal-on-repeated-attack contract.
    src = Path(__file__).resolve().parents[1] / 'player/session_mixins/combat_damage.py'
    tree = ast.parse(src.read_text('utf8'))
    klass = next(x for x in tree.body if isinstance(x, ast.ClassDef)
                 and x.name == 'SessionCombatDamageMixin')
    method = next(x for x in klass.body if isinstance(x, ast.FunctionDef)
                  and x.name == 'apply_adaptive_mob_scale_v11330')
    namespace = {'MOB_TEMPLATES':{
            'mythic':dict(mythic, max_hp=55000),
            'crypt':dict(t, max_hp=base),
            'old':{'generator_level':5,'max_hp':1000, 'rank':'normal'}},
        'ROOMS':{'mythic_room':{},'crypt_room':{},'old_room':{}},
        'adaptive_combat_rank_v11330':adaptive_combat_rank_v11330,
        'authored_stage_combat_level_v11651':authored_stage_combat_level_v11651,
        'authored_party_damage_target_hp_v11652':authored_party_damage_target_hp_v11652,
        'math':math, 'sqlite3':sqlite3,'sys':sys}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[method],type_ignores=[])),
                 str(src), 'exec'), namespace)
    apply = namespace['apply_adaptive_mob_scale_v11330']
    class DB:
        def __init__(self):
            self.conn=sqlite3.connect(':memory:')
            self.conn.execute('CREATE TABLE summons_v1700(account_id INT,active INT,hp INT)')
            self.conn.executemany('INSERT INTO summons_v1700 VALUES(?,?,?)',
                [(i,1,100) for i in range(1,7)])
            self.queries=0
        def mercenary_contracts(self, aid):
            self.queries += 1
            return [dict(expires_at=0) for _ in range(3)]
    db = DB()
    members=[]
    class Actor:
        def __init__(self, i):
            self.account_id=i
            self.character=SimpleNamespace(character_level=85,room_id='mythic_room')
            self.server=SimpleNamespace(db=db)
            self.closed=False; self.current_hp=100
            self.calls=0
        def adaptive_party_members_v11330(self,mob):
            return members
        def adaptive_mob_has_active_fighters_v1261(self,mob):
            return False
        def adaptive_party_dps_v1261(self,party):
            self.calls+=1
            return sum(x.dps for x in party)
    for i in range(1,4):
        a=Actor(i);a.dps=80000;members.append(a)
    def mob(template_id,room_id,hp):
        return SimpleNamespace(key=template_id,template_id=template_id,room_id=room_id,hp=hp,alive=True)
    with patch('systems.adaptive_switch_v102006.enabled',return_value=False):
        myth=mob('mythic','mythic_room',55000)
        first=apply(members[0],myth)
        check(first and first['max_hp'] >= strong, 'production path grows mythic health')
        check(first['party_size']==3 and first['reward_multiplier']==1., 'no XP/Fame multiplier')
        check(members[0].calls==1 and db.queries==3, 'one DPS calculation and 3 helper queries')
        myth.hp//=2
        remain=myth.hp
        second=apply(members[0],myth)
        check(second['max_hp']==first['max_hp'] and myth.hp==remain,
              'no repeat scaling or healing during combat')
        check(members[0].calls==1 and db.queries==3,
              '5-second party-DPS and helper cache do not reread data each hit')
        # Two weaker fighters should not re-trigger an enormous multiplier in
        # a floor-60 crypt. Ignore prior mythic cache due to different party.
        members[:] = members[:2]
        for a in members:
            a.character.character_level=73
            a.character.room_id='crypt_room'
            a.dps=2000
        crypt=mob('crypt','crypt_room',base)
        outcome=apply(members[0],crypt)
        check(outcome and base < outcome['max_hp'] < 200000,
              'level73 crypt60 keeps modest original stage resistance')
        # Old easy world enemies are never boosted to match current parties.
        for a in members:
            a.character.character_level=85
            a.character.room_id='old_room'
            a.dps=80000
        old=mob('old','old_room',1000)
        check(apply(members[0],old) is None and old.hp==1000,
              'lower-level legacy zones not forced to current player power')
    db.conn.close()
    print(f'GLOBAL PARTY DPS v116.00.52: {count} PASS',flush=True)
    return count


if __name__ == '__main__':
    run()
