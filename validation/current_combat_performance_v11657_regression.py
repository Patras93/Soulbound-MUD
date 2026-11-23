# -*- coding: utf-8 -*-
"""v116.00.57: independent combat + active-world performance regression.

Read-only, synthetic data. No real player SQLite or TCP. These checks do not
replace Windows 60/60 PLUS or an observed in-game duration measurement.
"""
from __future__ import annotations

from dataclasses import replace
from types import SimpleNamespace
from unittest.mock import patch
import random

from systems.adaptive_combat import authored_party_damage_target_hp_v11652
from world.world_state import MobState, World


def run():
    checks = 0
    def ok(value, label):
        nonlocal checks
        checks += 1
        if not value:
            raise AssertionError('v11657: ' + label)

    room = {'generator_level': 65, 'zone': 'hunting'}
    enemy = {'max_hp': 55_000, 'rank': 'normal', 'generator_level': 65}
    burst = 360_000   # three realistically learned strong skills
    # A single 5-second nine-hire opening round must be counted by power,
    # not by a flat percentage per hire or only a normal autoattack.
    old = authored_party_damage_target_hp_v11652(
        enemy, 55_000, 85, 24_000, room, 3, 9, 3, skill_burst=burst)
    new = authored_party_damage_target_hp_v11652(
        enemy, 55_000, 85, 24_000, room, 3, 9, 3, skill_burst=burst,
        helper_opening_burst=5_000_000)
    ok(new > old * 3, 'real opening helper attacks change target')
    ok(new >= 2 * 5_000_000 * 0.65, 'more than one first helper volley')
    ok(new < 5 * 5_000_000, 'not a 50-rotation helper sponge')
    ok(old == authored_party_damage_target_hp_v11652(
        enemy, 55_000, 85, 24_000, room, 3, 9, 3, skill_burst=burst,
        helper_opening_burst=0), 'no helpers: previous formula unchanged')
    for level in (35, 50, 65, 85, 100):
        a = authored_party_damage_target_hp_v11652(
            enemy, 55_000, level, 24_000, room, 3, 9, 3,
            skill_burst=burst, helper_opening_burst=5_000_000)
        ok(a >= 55_000, 'no HP regression')
    old_weak = {'generator_level': 2, 'max_hp': 95, 'rank': 'normal'}
    for level in (1, 25, 85, 400):
        value = authored_party_damage_target_hp_v11652(
            old_weak, 95, level, 20_000, {'generator_level':2}, 3, 9, 3,
            skill_burst=burst, helper_opening_burst=5_000_000)
        if level >= 85:
            ok(value == 95, 'levelled players still trivialize starter rats')
        else:
            ok(value >= 95, 'beginner unchanged or more difficult')
    # The former v116.56 threshold excluded stage 30 for a level-85 party.
    broad = {'generator_level': 31, 'max_hp': 2000, 'rank':'normal'}
    ok(authored_party_damage_target_hp_v11652(broad, 2000, 85, 20_000,
       {'generator_level':31}, 3, 6, 1, skill_burst=100_000) > 2000,
       'under-levelled real hunting zone supported')
    far_old = {'generator_level':20, 'max_hp':100, 'rank':'normal'}
    ok(authored_party_damage_target_hp_v11652(far_old, 100, 85, 20_000,
       {'generator_level':20}, 3, 6, 1, skill_burst=100_000) == 100,
       'distant trivial region not inflated')

    # Exercise the real production scaler (not just the pure formula) with
    # extremely high owner-derived mercenary output. It must not read/change
    # a real database, alter EXP or heal repeatedly.
    from validation.current_skill_burst_v11656_regression import run as old_skill_regression
    ok(old_skill_regression() >= 15, 'v11656 learned skills preserved')
    from player.session_mixins import combat_damage
    from systems.adaptive_switch_v102006 import enabled
    class FakeDB:
        def __init__(self):
            import sqlite3
            self.conn=sqlite3.connect(':memory:')
            self.conn.execute('CREATE TABLE summons_v1700(account_id INT, active INT, hp INT)')
            self.conn.execute('INSERT INTO summons_v1700 VALUES(1,1,100)')
        def mercenary_contracts(self, aid):
            return [dict(expires_at=0) for _ in range(3)]
        def learned_skill_ids(self,aid):return set()
    class Actor:
        def __init__(self):
            self.character=SimpleNamespace(character_level=85,room_id='v57_demo',
                                           soul_level=85,class_name='Mec')
            self.account_id=1;self.current_hp=100;self.closed=False
            self.server=SimpleNamespace(db=FakeDB())
            self.helper_calls=0
        def adaptive_party_members_v11330(self,mob):return [self]
        def adaptive_mob_has_active_fighters_v1261(self,mob):return False
        def adaptive_party_dps_v1261(self,members):return 20000
        def adaptive_member_mercenary_dps_v1261(self, member):
            self.helper_calls += 1
            return 3_000_000
        def class_skills(self):return ()
    actor=Actor()
    mob=SimpleNamespace(key='mob57', template_id='v57_demo',
                        room_id='v57_demo', hp=55_000, alive=True)
    real_template={'generator_level':65, 'max_hp':55_000,'rank':'normal'}
    real_room={'generator_level':65,'zone':'v57-demo'}
    with patch.object(combat_damage,'MOB_TEMPLATES',{'v57_demo':real_template}), \
         patch.object(combat_damage,'ROOMS',{'v57_demo':real_room}), \
         patch('systems.adaptive_switch_v102006.enabled',return_value=False):
        scale=combat_damage.SessionCombatDamageMixin.apply_adaptive_mob_scale_v11330
        result=scale(actor,mob)
        ok(result is not None and mob.hp > 15_000_000,
           'live pre-attack HP covers real hired first volley')
        ok(result['reward_multiplier']==1.0,'no HP-based EXP multiplier')
        hp_before=mob.hp
        for _ in range(4):scale(actor,mob)
        ok(mob.hp==hp_before,'rescaling does not heal repeatedly')
        ok(actor.helper_calls==1,'no repeated expensive mercenary DPS calls')
    actor.server.db.conn.close()
    # Canonical room graph: cache across successive 15-second wandering rounds,
    # but changing an exit or a neighbor's zone invalidates that room's entry.
    rooms = {}
    for i in range(120):
        rooms[f'v57_r{i}'] = {'name':'R'+str(i),'zone':'v57-outskirts',
            'exits': {'east':f'v57_r{(i+1)%120}', 'west':f'v57_r{(i-1)%120}'}}
    mobs = {f'v57_m{i}':MobState(key=f'v57_m{i}',
       room_id=f'v57_r{i%120}',template_id='goblin',hp=100,
       next_wander_at=0.0) for i in range(360)}
    world = World.__new__(World)
    world.mobs = {key:replace(mob) for key,mob in mobs.items()}
    world._last_live_by_room={rid:tuple(m for m in world.mobs.values() if m.room_id==rid)
                              for rid in rooms}
    world._last_live_counts={rid:len(rows) for rid,rows in world._last_live_by_room.items()}
    world.refresh=lambda: dict(world._last_live_counts)
    from data import rooms as data_rooms
    from world import dynamic_content
    original_candidates=dynamic_content.mob_wander_candidates
    called = []
    def counted(room_id):
        called.append(room_id)
        return original_candidates(room_id)
    with patch.object(data_rooms,'ROOMS',rooms), \
         patch.object(dynamic_content,'mob_template_can_wander',return_value=True), \
         patch.object(dynamic_content,'mob_wander_candidates',side_effect=counted):
        random.seed(771)
        world.wander_step(now=10)
        first=len(called)
        ok(first >= 100, 'cold graph actually built')
        called.clear()
        for mob in world.mobs.values():mob.next_wander_at=0.0
        random.seed(772)
        world.wander_step(now=20)
        ok(len(called)==0,'warm graph avoids repeat discovery')
        for rid, group in world._last_live_by_room.items():
            ok(all(m.room_id == rid for m in group),'warm index correct')
        # Change destination in-place with the same number of exits: invalidate.
        rooms['v57_r5']['exits']['east']='v57_r10'
        called.clear()
        for mob in world.mobs.values():mob.next_wander_at=0.0
        random.seed(773)
        world.wander_step(now=30)
        ok('v57_r5' in called,'same-length exit edit invalidates cache')
        # Modify neighboring zone in-place: no crossing zone boundaries.
        rooms['v57_r6']['zone']='dangerous-foreign-zone'
        called.clear()
        for mob in world.mobs.values():mob.next_wander_at=0.0
        random.seed(774)
        world.wander_step(now=40)
        ok('v57_r5' in called or 'v57_r7' in called,
           'neighbor-zone edit invalidates cached routes')
    print(f'COMBAT + WORLD PERFORMANCE v116.00.57: {checks} PASS; '
          f'cold_wander_candidates={first}, warm_calls=0',flush=True)
    return checks

if __name__=='__main__':run()
