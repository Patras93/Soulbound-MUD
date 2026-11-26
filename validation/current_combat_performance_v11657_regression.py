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


def run_soul_equipment_regression():
    """38 authored class profiles; exact isolated combat calculations and EQ reads."""
    import math
    import sqlite3
    from core.classes_skills import CLASSES
    from core.magitek.catalogue import CLASS_INFO
    from core.archetypes.chaos import CLASS_SPECS as chaos
    from core.archetypes.expansion import CLASS_SPECS as expansion
    from core.progression_resources import class_type_for_name
    from core.progression_600 import soul_weapon_trait_totals_v11193
    from player.character import Character
    from player.session_mixins.combat_damage import SessionCombatDamageMixin as Damage
    from core.perf_diagnostics_v11320 import equipment_read_snapshot
    from systems.equipment_crafting import class_equipment_base_stat_pair, CLASS_SET_BONUSES
    from player.session_mixins import combat_damage
    from core.player_math import (character_attribute_power, character_offensive_build_multiplier,
                                  critical_chance_from_dexterity, critical_multiplier)
    from core.character_resources import character_hp_base, character_mana_base
    from pathlib import Path
    import ast
    # The full equipment module initializes the entire world catalogue on import.
    # Extract the exact synchronous production methods for this pre-boot fixture,
    # preserving their decorators. The real runtime is checked separately by TCP.
    root=Path(__file__).resolve().parents[1]
    gear={f'__relic_{i}':{'type':'soul_weapon_relic','name':str(i)} for i in range(10)}
    def extracted(relative, clsname, names, env):
        tree=ast.parse((root/relative).read_text('utf-8'))
        cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name==clsname)
        cls.body=[n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name in names]
        assert len(cls.body)==len(names)
        exec(compile(ast.Module(body=[cls],type_ignores=[]),relative,'exec'),env)
        return env[clsname]
    EQ=extracted('player/session_mixins/equipment_stats.py','SessionEquipmentStatsMixin',{
        'equipped_item_rows','soul_weapon_relic_rows_v11179','active_soul_weapon_relic_v11176',
        'equipment_bonus_totals','equipment_flat_power_totals_v11187','equipment_property_totals',
        'equipment_damage_multiplier','class_set_counts','class_set_stat_bonus_totals',
        'effective_strength','effective_dexterity','effective_intelligence','effective_willpower',
        'effective_constitution','critical_chance','critical_multiplier','max_hp','max_mana',
        'physical_power','spell_power'},dict(ITEMS=gear,CLASS_SET_BONUSES=CLASS_SET_BONUSES,
        equipment_read_snapshot=equipment_read_snapshot,character_attribute_power=character_attribute_power,
        critical_chance_from_dexterity=critical_chance_from_dexterity,player_critical_multiplier=critical_multiplier,
        character_hp_base=character_hp_base,character_mana_base=character_mana_base))
    Skills=extracted('player/session_mixins/combat_skills.py','SessionCombatSkillsMixin',{
        'offensive_skill_effective_stat_value_v11196','offensive_skill_core_stat_power_v11188',
        'offensive_skill_core_power_v11185','offensive_skill_damage_multiplier_v11186'},
        dict(equipment_read_snapshot=equipment_read_snapshot,character_attribute_power=character_attribute_power,
             character_offensive_build_multiplier=character_offensive_build_multiplier,
             party_synergy_damage_multiplier_v11338=lambda actor,kind:1.0))
    checks=0
    def check(value,label):
        nonlocal checks
        assert value,label
        checks+=1
    class DB:
        def __init__(self):
            self.conn=sqlite3.connect(':memory:')
            self.conn.row_factory=sqlite3.Row
            self.conn.executescript('CREATE TABLE gear(item_id TEXT,slot TEXT); CREATE TABLE ench(stat TEXT,amount INT); CREATE TABLE inv(item_id TEXT,qty INT); INSERT INTO ench VALUES("dexterity",5);')
            self.queries=0
            self.conn.set_trace_callback(lambda statement: setattr(self,'queries',self.queries+1))
        def equipment(self,aid):return self.conn.execute('SELECT * FROM gear').fetchall()
        def equipment_enchants_v03053(self,aid):return self.conn.execute('SELECT * FROM ench').fetchall()
        def item_qty(self,aid,item):
            row=self.conn.execute('SELECT qty FROM inv WHERE item_id=?',(item,)).fetchone()
            return row[0] if row else 0
    class Actor(Damage, EQ, Skills):
        def __init__(self, row, tier, db):
            c=Character.__new__(Character)
            c.class_name,c.class_type,c.soul_weapon,c.weapon_base=row[:4]
            c.character_level=100;c.soul_level=100;c.soul_tier=tier
            c.strength=120;c.dexterity=120;c.intelligence=120;c.willpower=120;c.constitution=120
            c.race='Człowiek';self.character=c;self.current_mana=100
            self.account_id=1;self.server=SimpleNamespace(db=db)
        def active_class_names(self):return self.character.active_class_names()
        def total_set_damage_multiplier(self):return 1.0
        def total_set_hp_mana_multiplier(self):return 1.0
        def job_ability_selected(self,*args):return False
        def skill_buff_multiplier(self,**kwargs):return 1.0
    class OldActor(Actor):
        # Original formulas with no new per-calculation EQ snapshot or engineer bonus.
        player_damage=Damage.player_damage.__wrapped__
        consider_player_expected_hit=Damage.consider_player_expected_hit.__wrapped__
        max_hp=EQ.max_hp.__wrapped__;max_mana=EQ.max_mana.__wrapped__
        physical_power=EQ.physical_power.__wrapped__;spell_power=EQ.spell_power.__wrapped__
        offensive_skill_core_power_v11185=Skills.offensive_skill_core_power_v11185.__wrapped__
        offensive_skill_damage_multiplier_v11186=Skills.offensive_skill_damage_multiplier_v11186.__wrapped__
        def basic_attack_inherent_multiplier_v1124(self):return 1.0
    rows={r[0]:r for r in CLASSES}
    rows.setdefault(CLASS_INFO[0],CLASS_INFO)
    for spec in (*chaos,*expansion):rows.setdefault(spec[0],(*spec[:3],7))
    check(len(rows)==38,'all 38 authored profiles')
    db=DB()
    from core.character_resources import AUTHORED_CLASS_PASSIVE_PROFILES
    extra_passives={spec[0]:{'kind':spec[4],'value':spec[5]} for spec in (*chaos,*expansion)}
    with patch.dict(AUTHORED_CLASS_PASSIVE_PROFILES,extra_passives), \
         patch.object(combat_damage,'party_synergy_damage_multiplier_v11338',return_value=1.0), \
         patch.object(combat_damage.random,'randint',return_value=0):
        for name,row in rows.items():
            check(class_type_for_name(name)==row[1],name+' damage channel')
            for tier in (1,9,40,1000):
                before=OldActor(row,tier,db);after=Actor(row,tier,db)
                base=before.player_damage();new=after.player_damage()
                expected=before.consider_player_expected_hit();actual=after.consider_player_expected_hit()
                check(new==base and actual==expected,name+' unchanged basic attack/preview')
                if name=='Inżynier':
                    check(after.basic_attack_build_v11196()[1]==125 and class_equipment_base_stat_pair(name)[0]=='dexterity','engineer DEX build')
                    check(after.basic_attack_inherent_multiplier_v1124()==1.0,'engineer original multiplier restored')
                check(all(math.isfinite(x) and x>=0 for x in soul_weapon_trait_totals_v11193(tier,name).values()),name+' tier traits')
                check(after.current_mana==before.current_mana,name+' same mana cost')
                skill={'id':'__fixture_skill','scale':'dexterity' if row[1]=='physical' else 'intelligence','secondary_scale':'strength','mult':1.4}
                check(after.offensive_skill_core_power_v11185(skill)==before.offensive_skill_core_power_v11185(skill),name+' skill core unchanged')
                check(after.offensive_skill_damage_multiplier_v11186(skill,row[1])==before.offensive_skill_damage_multiplier_v11186(skill,row[1]),name+' skill multiplier unchanged')
                check('_read_only_equipment_cache_v1262' not in after.__dict__,'no stale EQ scope')
        a=Actor(rows['Inżynier'],9,db);b=OldActor(rows['Inżynier'],9,db)
        def queries(fn):
            start=db.queries;value=fn();return value,db.queries-start
        old,n_old=queries(b.consider_player_expected_hit)
        new,n_new=queries(a.consider_player_expected_hit)
        check(n_new<n_old,'fewer EQ queries for basic hit preview')
        skill={'id':'__fixture_skill','scale':'dexterity','secondary_scale':'strength','mult':1.4}
        x,n_skill_old=queries(lambda:b.offensive_skill_core_power_v11185(skill))
        y,n_skill_new=queries(lambda:a.offensive_skill_core_power_v11185(skill))
        check(x==y and n_skill_new<n_skill_old,'fewer EQ queries for skill core')
        before=a.consider_player_expected_hit()
        db.conn.execute('UPDATE ench SET amount=50');db.conn.commit()
        check(a.consider_player_expected_hit()>before,'new EQ applies immediately')
        a._read_only_equipment_cache_v1262=None
        @equipment_read_snapshot
        def fail(actor):raise RuntimeError('fixture')
        try:fail(a)
        except RuntimeError as exc:check(str(exc)=='fixture','exception preserved')
        check(a._read_only_equipment_cache_v1262 is None,'prior None state restored')
        outer={};a._read_only_equipment_cache_v1262=outer
        a.player_damage()
        check(a._read_only_equipment_cache_v1262 is outer and bool(outer),'nested forecast cache preserved')
    db.conn.close()
    print(f'SOUL WEAPON / EQ SNAPSHOT v11677: {checks}/{checks} PASS; 38 profiles; preview SQL {n_old}->{n_new}; skill core SQL {n_skill_old}->{n_skill_new}',flush=True)
    return checks


def run_soul_form_regression():
    """Real form commands and collection methods against isolated SQLite."""
    import ast, asyncio, sqlite3
    from pathlib import Path
    from contextlib import contextmanager
    from tempfile import TemporaryDirectory
    root=Path(__file__).resolve().parents[1]
    def extract(relative, klass, names, env):
        tree=ast.parse((root/relative).read_text('utf8'))
        cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name==klass)
        if names is not None:
            cls.body=[n for n in cls.body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name in names]
            assert len(cls.body)==len(names)
        exec(compile(ast.Module(body=[cls],type_ignores=[]),relative,'exec'),env)
        return env[klass]
    Forms=extract('player/session_mixins/equipment_stats.py','SessionEquipmentStatsMixin',{'active_soul_weapon_relic_v11176','set_soul_weapon_form_v11179','handle_soul_weapon_relic_v11179'}, {})
    Collections=extract('storage/db_world_parts_v109/collections.py','CollectionsV109Mixin',{'add_collection_entry','collection_entry_ids','remove_collection_entry'}, {})
    Proxy=extract('storage/database.py','_DeferredCommitConnection',None,dict(sqlite3=sqlite3,contextmanager=contextmanager))
    Z='uoss_odin_unique_2'; NORMAL='__normal'; OFF='__form_off__'; CAT='active_soul_weapon_relic_v11183'
    items={Z:{'name':'Zantetsuken','required_level':999},NORMAL:{'name':'Zwykła forma','required_level':1}}
    checks=0
    def check(value,label):
        nonlocal checks
        assert value,label
        checks+=1
    class DB(Collections):
        def __init__(self,path):
            raw=sqlite3.connect(path);raw.row_factory=sqlite3.Row
            raw.execute('CREATE TABLE IF NOT EXISTS collection_codex(account_id INTEGER, category TEXT, entry_id TEXT, PRIMARY KEY(account_id,category,entry_id))')
            raw.commit();self.conn=Proxy(raw)
    class Actor(Forms):
        def __init__(self,db,aid,owned):
            self.server=SimpleNamespace(db=db);self.account_id=aid;self.owned=owned;self.messages=[]
        def soul_weapon_relic_rows_v11179(self):return [(k,items[k]) for k in self.owned]
        async def send(self,msg):self.messages.append(msg)
        def active(self):return self.active_soul_weapon_relic_v11176()[0]
    async def exercise(path):
        db=DB(path);a=Actor(db,1,[Z,NORMAL]);b=Actor(db,2,[Z]);c=Actor(db,3,[])
        check(a.active()==NORMAL,'auto excludes Zantetsuken')
        check(b.active() is None,'only Zantetsuken: base weapon')
        await a.handle_soul_weapon_relic_v11179('wybierz Zantetsuken')
        check(a.active()==Z,'manual name allowed')
        check(db.collection_entry_ids(1,CAT)=={Z},'manual persisted')
        check(Actor(db,1,[Z,NORMAL]).active()==Z,'explicit selection retained')
        await a.handle_soul_weapon_relic_v11179('off')
        check(a.active() is None,'off overrides all forms')
        check(db.collection_entry_ids(1,CAT)=={OFF},'durable off marker')
        check(a.owned==[Z,NORMAL],'ownership unchanged')
        await a.handle_soul_weapon_relic_v11179('lista')
        check('Tryb: wyłączone' in a.messages[-1],'status explains disabled')
        await b.handle_soul_weapon_relic_v11179('wybierz 1')
        check(b.active()==Z and a.active() is None,'separate character state')
        await c.handle_soul_weapon_relic_v11179('off');c.owned.append(NORMAL)
        check(c.active() is None,'off before acquisition remains off')
        db.conn.close();db=DB(path);a=Actor(db,1,[Z,NORMAL]);b=Actor(db,2,[Z]);c=Actor(db,3,[NORMAL])
        check(a.active() is None and b.active()==Z and c.active() is None,'database close/open persists')
        a.active_soul_weapon_relic_id_v11179=Z
        check(a.active() is None,'stale session attribute ignored')
        await a.handle_soul_weapon_relic_v11179('auto')
        check(a.active()==NORMAL and not db.collection_entry_ids(1,CAT),'auto clears off')
        await b.handle_soul_weapon_relic_v11179('auto')
        check(b.active() is None,'auto clears manual Zantetsuken')
        await c.handle_soul_weapon_relic_v11179('wybierz 1')
        check(c.active()==NORMAL and db.collection_entry_ids(3,CAT)=={NORMAL},'manual clears off')
        await a.handle_soul_weapon_relic_v11179('wyłącz')
        check(a.active() is None,'Polish off alias')
        await a.handle_soul_weapon_relic_v11179('wybierz nieistniejąca')
        check(a.active() is None,'invalid selection preserves off')
        with patch.object(db,'add_collection_entry',side_effect=RuntimeError('test rollback')):
            try:await a.handle_soul_weapon_relic_v11179('wybierz 1')
            except RuntimeError as exc:check(str(exc)=='test rollback','exception preserved')
        check(db.collection_entry_ids(1,CAT)=={OFF} and a.active() is None,'transaction rollback preserves off')
        db.conn.close()
    with TemporaryDirectory() as tmp:
        asyncio.run(exercise(str(Path(tmp)/'forms.db')))
    print(f'SOUL FORM OFF / ZANTETSUKEN v11678: {checks}/{checks} PASS',flush=True)
    return checks
