# -*- coding: utf-8 -*-
"""Read-only forecasts, live room index and mob-index reuse; isolated fixtures."""
import ast
import re
import sqlite3
import time
import unicodedata
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]


def methods(relative, klass, names, env, bases=()):
    tree = ast.parse((ROOT / relative).read_text('utf-8'))
    node = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == klass)
    node.body = [n for n in node.body if isinstance(n, ast.FunctionDef) and n.name in names]
    assert len(node.body) == len(names), (klass, names)
    node.bases = [ast.Name(id=f'Base{i}', ctx=ast.Load()) for i in range(len(bases))]
    env.update({f'Base{i}': base for i, base in enumerate(bases)})
    exec(compile(ast.fix_missing_locations(ast.Module(body=[node], type_ignores=[])), relative, 'exec'), env)
    return env[klass]


def run():
    from systems.encounter_burst_v11656 import member_skill_burst_v11656
    from core import classes_skills, runtime_rules
    from player.session_mixins import guide_navigation
    from world.world_state import World, MobState
    from data import rooms as room_catalog
    from core.perf_diagnostics_v11320 import equipment_read_snapshot
    checks = 0
    def check(value, label):
        nonlocal checks
        assert value, label
        checks += 1
    # Use the actual inventory SQL helpers and actual relic filter.
    items = {f'relic{i}': {'type': 'soul_weapon_relic', 'name': f'Relikt {i}', 'required_level': i} for i in range(1, 101)}
    items.update({f'ordinary{i}': {'type': 'armor'} for i in range(5000)})
    Inventory = methods('storage/db_inventory_parts_v109/inventory.py', 'InventoryV109Mixin', {'inventory', 'item_qty'}, {})
    Relics = methods('player/session_mixins/equipment_stats.py', 'SessionEquipmentStatsMixin', {'soul_weapon_relic_rows_v11179'}, {'ITEMS': items})
    raw = sqlite3.connect(':memory:'); raw.row_factory = sqlite3.Row
    raw.executescript('CREATE TABLE inventory(account_id INT,item_id TEXT,quantity INT, PRIMARY KEY(account_id,item_id)); CREATE TABLE class_progress(account_id INT,class_name TEXT,level INT); CREATE TABLE learned_skills(account_id INT,skill_id TEXT); CREATE TABLE skill_progress(account_id INT,skill_id TEXT,level INT);')
    raw.executemany('INSERT INTO inventory VALUES (?,?,?)', [(1,'relic1',1),(1,'relic2',0),(1,'relic3',2),(1,'relic99',1),(1,'ordinary1',4),(2,'relic2',1)])
    raw.execute('INSERT INTO class_progress VALUES(1,"Mec",85)')
    raw.commit()
    class DB(Inventory):
        conn = raw
        def active_class_names(self, aid, primary):
            return [r[0] for r in raw.execute('SELECT class_name FROM class_progress WHERE account_id=?',(aid,))]
        def class_progress_row(self, aid, name):
            return raw.execute('SELECT level FROM class_progress WHERE account_id=? AND class_name=?',(aid,name)).fetchone()
        def learned_skill_ids(self, aid):
            return {r[0] for r in raw.execute('SELECT skill_id FROM learned_skills WHERE account_id=?',(aid,))}
    db = DB(); trace=[]; raw.set_trace_callback(trace.append)
    actor=Relics();actor.server=SimpleNamespace(db=db);actor.character=SimpleNamespace(character_level=85);actor.account_id=1
    rows=actor.soul_weapon_relic_rows_v11179()
    check([k for k,_ in rows]==['relic1','relic3'],'owned, positive, level-valid relics only')
    check(len(trace)==1,'one inventory SELECT for 100 catalogue relics')
    actor.account_id=2;trace.clear()
    check([k for k,_ in actor.soul_weapon_relic_rows_v11179()]==['relic2'] and len(trace)==1,'separate character ownership')
    actor.account_id=1;raw.execute('UPDATE inventory SET quantity=1 WHERE item_id="relic2" AND account_id=1');raw.commit()
    check([k for k,_ in actor.soul_weapon_relic_rows_v11179()]==['relic1','relic2','relic3'],'new ownership visible immediately')
    items['ordinary1']={'type':'soul_weapon_relic','name':'Nowa forma','required_level':1}
    check('ordinary1' in dict(actor.soul_weapon_relic_rows_v11179()),'same-ID template edit visible without scanning world')
    # Real passive, class and mastery handlers under the production forecast.
    skills=[dict(id=f'off{i}',kind='damage',mult=1.0,scale='strength',unlock=1) for i in range(240)]
    boosts=[dict(id=f'boost{i}',kind='boost',boost=1.04,unlock=1+i*15) for i in range(8)]
    catalogue={'Mec':skills+boosts,'Mag':[dict(id='off0',kind='damage')]}
    raw.executemany('INSERT INTO learned_skills VALUES(1,?)',[(s['id'],) for s in skills+boosts])
    raw.executemany('INSERT INTO skill_progress VALUES(1,?,?)',[(s['id'],7) for s in skills+boosts]);raw.commit()
    Class=methods('player/session_mixins/class_progression.py','SessionClassProgressionMixin',{'refresh_active_classes','active_class_names','skill_class_name','class_mastery_level','skill_mastery_unlocked','skill_required_mastery'},{'CLASS_SKILLS':catalogue})
    Buff=methods('player/session_mixins/skill_queue_buffs.py','SessionSkillQueueBuffsMixin',{'passive_class_boost_multiplier_v11134','skill_buff_multiplier'},{'CLASS_SKILLS':catalogue,'SKILL_MAX_LEVEL':600,'class_type_for_name':lambda n:'physical','sqlite3':sqlite3})
    class Actor(Class,Buff):
        def __init__(self, legacy=False):
            self.legacy=legacy;self.account_id=1;self.server=SimpleNamespace(db=db);self.current_hp=100
            self.character=SimpleNamespace(character_level=85,soul_level=85,class_name='Mec',active_class_names=lambda:['Mec'])
            for method in ('class_physical_damage_multiplier','racial_physical_damage_multiplier','racial_all_damage_multiplier'):
                setattr(self.character,method,lambda:1.0)
        def __getattribute__(self,name):
            if name=='_burst_reads_v11681' and object.__getattribute__(self,'legacy'):
                return None
            return object.__getattribute__(self,name)
        def class_skills(self):return [s for c in self.active_class_names() for s in catalogue[c]]
        def offensive_skill_core_power_v11185(self,s):return 10000
        def offensive_skill_damage_type_v11190(self,s):
            assert self.skill_class_name(s)=='Mec';return 'physical'
        def total_set_damage_multiplier(self):return 1.0
        def equipment_damage_multiplier(self,k):return 1.0
        def cleanup_skill_buffs(self):return None
        def critical_multiplier(self):return 2.0
    old,new=Actor(True),Actor();before=raw.total_changes
    with patch('systems.party_synergies.party_synergy_damage_multiplier_v11338',return_value=1.0):
        trace.clear();baseline=member_skill_burst_v11656(old,now=100);old_queries=len(trace)
        trace.clear();actual=member_skill_burst_v11656(new,now=100);new_queries=len(trace)
        check(actual==baseline and actual>0,'same 240-skill forecast, duplicate owner first wins')
        check(new_queries<old_queries and new_queries<=10,'bounded synchronous class/passive reads')
        check(raw.total_changes==before and not raw.in_transaction,'no writes or commits from forecast')
        check('_burst_reads_v11681' not in vars(new) and '_read_only_equipment_cache_v1262' not in vars(new),'read scopes released')
        raw.execute('UPDATE class_progress SET level=120');raw.commit()
        old2=Actor(True);changed=member_skill_burst_v11656(new,now=115)
        check(changed==member_skill_burst_v11656(old2,now=115) and changed>actual,'next forecast sees new mastery')
        new._burst_reads_v11681={'sentinel':True};member_skill_burst_v11656(new,now=130)
        check(new._burst_reads_v11681=={'sentinel':True},'outer cache restored')
    raw.close()
    # Preserve the old navigation text semantics even on ASCII/Polish input.
    def old_normalize(value):
        text=value.strip().lower().replace('ł','l').replace('Ł','l')
        text=unicodedata.normalize('NFKD',text);text=''.join(c for c in text if not unicodedata.combining(c))
        text=text.replace('_',' ').replace('-',' ');return ' '.join(re.sub(r'[^a-z0-9 ]+',' ',text).split())
    for value in ('ABC DEF','Łąki Zielarskie','A_b-c!','Strażnik', 'ŻÓŁĆ','İﬀ 123','  X  Y  '):
        check(guide_navigation._normalized_room_search_text_v107(value)==old_normalize(value),'same normalization '+value)
    # Rebuild the live index after a floor is added; unchanged rooms never need
    # a second alias computation. New/renamed/removed entries remain exact.
    class Guide(guide_navigation.SessionGuideNavigationMixin):
        calls=0
        def room_search_aliases(self,rid,room):
            self.calls+=1;return super().room_search_aliases(rid,room)
    env={}
    Session=methods('player/session.py','Session',{'_v11644_get_room_index','find_room_matches','rooms_in_exact_zone'},env,(Guide,))
    Session._v11644_room_index=None
    guide=Session();rooms={f'room_{i}':{'name':f'Komnata {i:04d}','zone':'Łąki','exits':{}} for i in range(2000)}
    with patch.object(classes_skills,'ROOMS',rooms),patch.object(guide_navigation,'ROOMS',rooms):
        data=guide._v11644_get_room_index();cold=guide.calls
        check(cold==2000 and len(data[2])==2000,'cold complete index')
        rooms['room_1']['name']='Nowa Komnata';rooms['room_2']['zone']='Las';rooms.pop('room_3');rooms['room_new']={'name':'Nowe wejście','zone':'Las','exits':{}};rooms['room_new2']={'name':'Nowe wyjście','zone':'Las','exits':{}}
        data2=guide._v11644_get_room_index();warm=guide.calls-cold
        check(warm==4 and len(data2[2])==2001,'only 4 new/changed aliases on rebuild')
        check('room_3' not in data2[2] and 'nowa komnata' in data2[1] and 'komnata 0001' not in data2[1],'renamed and removed entries updated')
        check(set(data2[0]['las'])=={'room_2','room_new','room_new2'},'zone move and new floor visible')
        expected={rid:set(Guide.room_search_aliases(Guide(),rid,room)) for rid,room in rooms.items()}
        check({rid:set(aliases) for rid,aliases in data2[2].items()}==expected,'rebuilt aliases equal complete fresh scan')
    # Preserve exact authoritative mob order while retaining unchanged tuples.
    world=World.__new__(World);world.mobs={};world.corpses={};world.ground_loot={};world.ground_loot_counter=0
    world._last_refresh_at=0;world._refresh_min_interval=.25;world._last_live_counts={};world._last_live_by_room={}
    for i in range(6000):
        mob=MobState(str(i),f'r{i%2000}','fixture',100,next_wander_at=time.time()+9999)
        world.mobs[mob.key]=mob
    def expected_rooms():
        expected={}
        for m in world.mobs.values():
            if m.alive:expected.setdefault(m.room_id,[]).append(m.key)
        return expected
    def actual_rooms():return {rid:[m.key for m in group] for rid,group in world._last_live_by_room.items()}
    with patch.object(runtime_rules,'get_rule',return_value=lambda t:None):
        world.refresh(force=True);first=world._last_live_by_room
        world.refresh(force=True)
        reused=sum(world._last_live_by_room[rid] is rows for rid,rows in first.items())
        check(reused==2000 and actual_rooms()==expected_rooms(),'all unchanged room tuples reused')
        world.mobs['0'].room_id='r1';world.mobs['2001'].alive=False;world.mobs['2001'].respawn_at=float('inf');world.mobs.pop('4002')
        world.mobs['new']=MobState('new','r2','fixture',100,next_wander_at=time.time()+9999)
        world.refresh(force=True)
        check(actual_rooms()==expected_rooms(),'move, death, removal, new spawn preserve order')
        check(world._last_live_counts=={k:len(v) for k,v in expected_rooms().items()},'room counts exact')
        check(world._last_live_by_room['r3'] is first['r3'],'untouched room still reused')
        counts=world._last_live_counts;rows=world._last_live_by_room
        world.refresh=lambda:counts
        check(not world.wander_step(now=1,mob_keys=tuple(world.mobs)[:2048]) and world._last_live_counts is counts and world._last_live_by_room is rows,'no-move slice allocates no new index')
    print(f'PERFORMANCE v11681: {checks}/{checks} PASS; 240 skill forecast SQL {old_queries}->{new_queries}; room aliases {cold}->{warm}; reused tuples {reused}',flush=True)
    return checks

if __name__=='__main__':run()
