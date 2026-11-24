# -*- coding: utf-8 -*-
"""Real source-level 116.69 hot-path regressions. No production DB or TCP."""
from __future__ import annotations
import ast
import sqlite3
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from world.world_state import World


def load_passive_method():
    """Compile the exact native source method without importing a full session.

    The native session import triggers a complete world generation; the
    production bootstrap/import path remains verified by PREDEPLOY itself.
    """
    filename=Path(__file__).resolve().parents[1]/'player/session_mixins/skill_queue_buffs.py'
    tree=ast.parse(filename.read_text(encoding='utf-8'),filename=str(filename))
    owner=next(x for x in tree.body if isinstance(x,ast.ClassDef)
               and x.name=='SessionSkillQueueBuffsMixin')
    method=next(x for x in owner.body if isinstance(x,(ast.FunctionDef,ast.AsyncFunctionDef))
                and x.name=='passive_class_boost_multiplier_v11134')
    spec=ast.Module(body=[method],type_ignores=[])
    ast.fix_missing_locations(spec)
    from systems.soul_evolutions_v1332 import role_evolution
    namespace={'CLASS_SKILLS':{},'SKILL_MAX_LEVEL':600,
               'class_type_for_name':lambda x:'physical' if x=='Mec' else 'magic'}
    exec(compile(spec,str(filename),'exec'),namespace)
    return namespace, namespace['passive_class_boost_multiplier_v11134']


def run():
    checks=0
    def check(value,message):
        nonlocal checks
        checks+=1
        if not value:raise AssertionError('v116.69: '+message)

    globals_,boost_method=load_passive_method()
    conn=sqlite3.connect(':memory:')
    conn.execute('CREATE TABLE learned_skills (account_id INT,skill_id TEXT)')
    conn.execute('CREATE TABLE skill_progress (account_id INT,skill_id TEXT,level INT)')
    boosts=[{'id':f'passive_{n}','kind':'boost','boost':1.04,'unlock':1}
            for n in range(5)]
    globals_['CLASS_SKILLS']['Mec']=boosts
    for skill in boosts:
        conn.execute('INSERT INTO learned_skills VALUES (7,?)',(skill['id'],))
        if skill is not boosts[0]:
            conn.execute('INSERT INTO skill_progress VALUES (7,?,?)',(skill['id'],6))
    conn.commit()
    class DB:
        def __init__(self):self.conn=conn;self.calls=0
        def knows_skill(self,aid,sid):
            self.calls+=1
            return True
        def skill_progress(self,aid,sid):
            self.calls+=1
            conn.execute('INSERT OR IGNORE INTO skill_progress VALUES (?,?,1)',(aid,sid))
            conn.commit()
            return {'level':1}
    db=DB()
    class Actor:
        account_id=7
        character=SimpleNamespace(soul_level=85)
        def __init__(self):
            self.server=SimpleNamespace(db=db)
            self._read_only_equipment_cache_v1262={}
        def active_class_names(self):return ('Mec',)
        def skill_mastery_unlocked(self,skill):return True
        passive_class_boost_multiplier_v11134=boost_method
    actor=Actor()
    trace=[];conn.set_trace_callback(trace.append)
    from systems import soul_evolutions_v1332
    with patch.object(soul_evolutions_v1332,'role_evolution',return_value=1.0):
        before=conn.total_changes
        bonuses=[actor.passive_class_boost_multiplier_v11134(target_type='physical')
                 for _ in range(480)]
        check(all(v==bonuses[0] for v in bonuses),'480 repeated forecasts are consistent')
        check(conn.total_changes==before,'480 forecasts do not write player progress')
        check(db.calls==0,'never use mutating skill_progress helper in forecast')
        check(len(trace)<=2,'480 forecasts, one SQLite joined query')
        check(not any('INSERT ' in q.upper() or 'COMMIT' in q.upper() for q in trace),
              'no INSERT/COMMIT in SQL trace')
        check(len(actor._read_only_equipment_cache_v1262['boost_levels_v11669'])==5,
              'cache contains learned boosts, including missing progress row')
        expected=1 + sum(.04 * (1 + ((1 if s is boosts[0] else 6)/600)) for s in boosts)
        check(abs(bonuses[0]-expected)<1e-9,'all passive levels and default 1 match formula')
        check(actor.passive_class_boost_multiplier_v11134(target_type='feedback')==1,
              'Feedback remains isolated from physical boosts')
        globals_['CLASS_SKILLS']['Mec']=boosts+[{'id':'not_learned','kind':'boost','boost':100}]
        check(actor.passive_class_boost_multiplier_v11134(target_type='physical')==bonuses[0],
              'unlearned skill never increases damage')
        globals_['CLASS_SKILLS']['Mec']=boosts
        del actor._read_only_equipment_cache_v1262
        trace.clear()
        actor.passive_class_boost_multiplier_v11134(target_type='physical')
        check(db.calls==0,'without per-request cache still no mutating helper')
        check(len(trace)<=2,'outside burst stays read-only and bounded')
        # A historical DB without these tables uses legacy helper behavior.
        old_db=actor.server.db
        actor.server.db=SimpleNamespace(knows_skill=lambda aid,sid:True,
            skill_progress=lambda aid,sid:{'level':1 if sid=='passive_0' else 6})
        check(abs(actor.passive_class_boost_multiplier_v11134(target_type='physical')-bonuses[0])<1e-9,
              'historical fixture fallback keeps identical bonus')
        actor.server.db=old_db
    conn.close()

    # Fully registered dynamic spawns keep correct identities as they wander.
    from data import mobs as mob_catalog
    from systems import content_registry
    from core import runtime_rules
    test_template='v11669_proof_mob'
    with patch.dict(mob_catalog.MOB_TEMPLATES,{test_template:{'max_hp':100,'name':'Test'}}), \
         patch.object(content_registry,'MOB_SPAWNS',[]), \
         patch.object(runtime_rules,'get_rule',return_value=lambda name:lambda t:None), \
         patch.object(World,'_terrain_scaled_template_v0362',lambda self,r,t:t), \
         patch.object(World,'_elite_spawn_template_v11338',lambda self,t:t), \
         patch.object(World,'_restore_v105_authored_stage',lambda self,r,t:None):
        class Guarded(dict):
            def values(self):raise AssertionError('unexpected O(world size) mob scan')
        w=World.__new__(World);w.mobs=Guarded();w._last_refresh_at=12.
        first=w._register_runtime_spawn('a',test_template)
        check(len(w.mobs)==1,'one base spawn')
        first.room_id='b'
        check(w._register_runtime_spawn('a',test_template) is first,
              'wandering does not replace monster and discard fight state')
        check(len(w.mobs)==1 and len(content_registry.MOB_SPAWNS)==1,
              'revisiting home does not duplicate monster or definition')
        for i in range(114):w._register_runtime_spawn(f'newroom{i}',test_template)
        check(len(w.mobs)==115,'all 114 real new room encounters retained')
        check(len(content_registry.MOB_SPAWNS)==115,'exactly 114 new definitions retained')
        content_registry.MOB_SPAWNS.append(('external',test_template))
        w._register_runtime_spawn('external',test_template)
        check(content_registry.MOB_SPAWNS.count(('external',test_template))==1,
              'external content invalidates index without duplication')

    from world import dynamic_content
    from data import rooms as room_catalog
    with patch.dict(room_catalog.ROOMS,{'v11669_test':{'zone':'Łąki','exits':{}}}):
        check(dynamic_content.mob_room_can_wander('v11669_test'),
              'natural terrain can wander')
        room_catalog.ROOMS['v11669_test']['zone']='Krypta'
        check(not dynamic_content.mob_room_can_wander('v11669_test'),
              'zone change blocks dungeon wandering immediately')
        room_catalog.ROOMS['v11669_test']['zone']='Łąki'
        room_catalog.ROOMS['v11669_test']['procedural_infinite']=True
        check(not dynamic_content.mob_room_can_wander('v11669_test'),
              'infinite dungeon remains nonwanderable')
    print(f'LIVE BATTLE/WORLD v116.69: {checks}/{checks} PASS',flush=True)
    return checks

if __name__=='__main__':run()
