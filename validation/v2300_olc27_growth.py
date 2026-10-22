# -*- coding: utf-8 -*-
"""v23 genuine engine, OLC, SQLite, cap-bank, summon AI and event calendar regressions.

In-memory user schema only; no real user database, no network calls.
"""
import copy
import json
import sqlite3
from types import SimpleNamespace

from systems.live_content_v1204 import LiveContentV1204
from systems.live_olc22_empire import validate_summons, validate_world, extra_preview
from systems.live_olc22_state import WORLD_OVERRIDES
from systems.live_olc23_state import SUMMON_TACTICS
from systems.summon_ai_v1200 import CLASS_AI, plan_for_class
from systems.world_events_v12812 import active_city_event_v12812
from systems.live_olc23_calendar import event_calendar_lines
from systems.multi_cap_v23215 import multi_cap_calculation_v23217, multi_cap_experience_v23215
from validation.v23215_multi_cap import TestDB
from core.classes_skills import CLASS_SKILLS
from systems.experience_bank_v2011 import banked_experience_v2011


def run():
    n = 0
    def ok(condition, message=''):
        nonlocal n
        assert condition, 'v23: '+str(message)
        n += 1
    def reject(fn, label):
        try:
            fn()
        except (ValueError, TypeError):
            ok(True, label)
        else:
            raise AssertionError('v23 accepted invalid: '+label)

    # strict JSON types; no negative balance, injections or unknown fields.
    ok(validate_world({}))
    for name, valids in (
        ('multi_cap_bonus_percent', [100, 150, 1000]),
        ('event_offset_minutes', [0, 30, 719]),
        ('multi_cap_all_owned_classes', [False, True]),
        ('multi_cap_category_bonus', [{}, {'klasy':120}, {'dusza':100,'profesje':1000}]),
    ):
        for v in valids:
            ok(validate_world({name:v}), name+str(v))
    for name, invalids in (
        ('multi_cap_bonus_percent', [-100,0,1,99,1001,True,150.5,'200',None]),
        ('event_offset_minutes', [-1,720,1440,True,60.0,'3',None]),
        ('multi_cap_all_owned_classes', [1,0,None,'true','false',[],{}]),
        ('multi_cap_category_bonus', [[],None,{'evil':120},{'klasy':99},{'klasy':1001},{'dusza':True},{'klasy':1.5},{'klasy':'200'},'{}']),
    ):
        for v in invalids:
            reject(lambda key=name,val=v: validate_world({key:val}), name+str(v))
    ok(validate_summons({'Strażnik':{'guard_threshold_percent':95},
                         'Berserker':{'execute_threshold_percent':55},
                         'Mag':{'tactic_interval':2}}))
    for field, invalids in (
        ('guard_threshold_percent',[0,4,101,False,3.5,'80',None]),
        ('execute_threshold_percent',[0,96,True,1.5,'25',None]),
        ('tactic_interval',[-1,0,13,True,3.0,'3',None]),
    ):
        for val in invalids:
            reject(lambda k=field,v=val: validate_summons({'Mag':{k:v}}), field+str(val))

    # Stateful publish and persisted rollback (not just parse validation).
    WORLD_OVERRIDES.clear(); SUMMON_TACTICS.clear()
    original_class_ai = copy.deepcopy(CLASS_AI)
    conn=sqlite3.connect(':memory:');conn.row_factory=sqlite3.Row
    conn.execute('CREATE TABLE quests (quest_id TEXT, status TEXT)')
    world=SimpleNamespace(mobs={},_last_refresh_at=0.,_register_runtime_spawn=lambda *a:None)
    server=SimpleNamespace(world=world,sessions=[])
    service=LiveContentV1204(SimpleNamespace(conn=conn))
    try:
        capdb=TestDB()
        capdb.ensure_primary_class(1,'Wojownik')
        capdb.ensure_class_progress(1,'Mag')
        capdb.conn.execute("UPDATE class_progress SET level=30,active_slot=NULL WHERE account_id=1 AND class_name='Mag'")
        capdb.conn.commit()
        mag_skill=CLASS_SKILLS['Mag'][0]['id']
        capdb.conn.execute('INSERT INTO learned_skills VALUES(1,?)',(mag_skill,))
        capdb.conn.execute('INSERT INTO skill_progress VALUES(1,?,?)',(mag_skill,8))
        capdb.conn.execute("INSERT INTO ascension_progress_v021 VALUES(1,'class:Mag',10)")
        capdb.conn.commit()
        original=multi_cap_calculation_v23217(capdb.conn,1)
        ok(original[0]==5500 and original[2]['klasy']==1, 'default older cap')
        ok(event_calendar_lines(2,now=0)[0].startswith('HARMONOGRAM'))
        ok(active_city_event_v12812(now=0)['slug']=='basalt')
        ok(plan_for_class('Mag',owner_hp=100,owner_max=100,step=2,marked=False)['action']=='strike')
        ok(plan_for_class('Strażnik',owner_hp=90,owner_max=100,guarded=False)['action']=='strike')
        ok(plan_for_class('Berserker',owner_hp=100,owner_max=100,enemy_hp=50,enemy_max=100)['action']=='strike')
        # Author can inspect the CURRENT value before changing it.
        for group,key,field,label in (
            ('swiat','global','multi_cap_bonus_percent','100'),
            ('swiat','global','multi_cap_category_bonus','{}'),
            ('swiat','global','multi_cap_all_owned_classes','False'),
            ('swiat','global','event_offset_minutes','0'),
            ('przywolanie','Mag','tactic_interval','3'),
            ('przywolanie','Strażnik','guard_threshold_percent','80'),
            ('przywolanie','Berserker','execute_threshold_percent','35'),
        ):
            message=extra_preview(service,group,key,field)
            ok(label in message and 'admin live edytuj' in message and 'auto' in message, message)
        # Preflight: staging alone cannot affect current live player state.
        for section,key,field,val in (
            ('swiat','global','multi_cap_bonus_percent','150'),
            ('swiat','global','multi_cap_category_bonus',json.dumps({'klasy':200,'profesje':150},ensure_ascii=False)),
            ('swiat','global','multi_cap_all_owned_classes','true'),
            ('swiat','global','event_offset_minutes','30'),
            ('przywolanie','Mag','tactic_interval','2'),
            ('przywolanie','Strażnik','guard_threshold_percent','95'),
            ('przywolanie','Berserker','execute_threshold_percent','55'),
        ):
            ok(bool(service.stage_edit(section,key,field,val)))
        ok(multi_cap_experience_v23215(capdb.conn,1)==5500)
        ok(not SUMMON_TACTICS and WORLD_OVERRIDES=={})
        reject(lambda:service.stage_edit('swiat','global','multi_cap_bonus_percent','50'),'no nerf')
        reject(lambda:service.stage_edit('swiat','global','multi_cap_category_bonus','{"klasy":50}'),'no category nerf')
        reject(lambda:service.stage_edit('przywolanie','Mag','tactic_interval','0'),'invalid tactics')
        reject(lambda:service.stage_edit('swiat','global','multi_cap_all_owned_classes','1'),'strict bool')
        reject(lambda:service.stage_edit('swiat','global','multi_cap_category_bonus','{"__class__":100}'),'no injection')
        reject(lambda:service.stage_edit('swiat','global','event_offset_minutes','720'),'strict event boundary')
        world.mobs['v12812:event:1:basalt'] = SimpleNamespace(
            home_room_id='v12812_city_basalt_gate',room_id='v12812_city_basalt_gate',
            template_id='v12812_event_basalt',engaged_by=set(),aoe_engaged_by=set())
        ok('Aktywowano' in service.apply(server,'test_v23'))
        ok('v12812:event:1:basalt' not in world.mobs, 'remove obsolete city boss on event schedule change')
        ok(service.revision==1)
        result=multi_cap_calculation_v23217(capdb.conn,1)
        ok(result[2]['klasy']==31 and result[0]>original[0]*2, 'all unlocked plus 2x class cap')
        ok(result[2]['skille']==8, 'learned archived-class skill')
        ok(result[2]['wzniesienia']==10, 'owned archived-class ascension')
        ok(banked_experience_v2011(capdb,1,result[0]*3,'character',1)==result[0], 'bank uses authoritative cap')
        ok(sum(result[3].values())==result[0], 'cap parts reconciled')
        ok(result[3]['klasy']>=190000, 'effective levels not fake bonus')
        ok(SUMMON_TACTICS['Mag']['tactic_interval']==2)
        ok(plan_for_class('Mag',owner_hp=100,owner_max=100,step=2,marked=False)['action']=='mark')
        ok(plan_for_class('Strażnik',owner_hp=90,owner_max=100,guarded=False)['action']=='guard')
        ok(plan_for_class('Berserker',owner_hp=100,owner_max=100,enemy_hp=50,enemy_max=100)['action']=='execute')
        ok(active_city_event_v12812(now=0)['slug']=='myth', 'offset moves slot -1')
        ok(active_city_event_v12812(now=30*60)['slug']=='basalt')
        ok(active_city_event_v12812(now=30*60)['expires_at']==(180+30)*60)
        for line in event_calendar_lines(8,now=30*60):
            ok('HARMONOGRAM' in line or 'Teraz' in line or 'koniec' in line)
        # Reading persisted SQLite in a fresh runtime (remove then reopen).
        service._remove(world)
        ok(not SUMMON_TACTICS and not WORLD_OVERRIDES)
        restored=LiveContentV1204(SimpleNamespace(conn=conn))
        ok(restored.revision==1)
        ok(restored.active['world_overrides']['multi_cap_all_owned_classes'] is True)
        ok(SUMMON_TACTICS['Mag']['tactic_interval']==2)
        ok(multi_cap_experience_v23215(capdb.conn,1)==result[0])
        # Explicit auto reset cannot silently delete character/quest tables.
        for key in ('multi_cap_bonus_percent','multi_cap_category_bonus',
                    'multi_cap_all_owned_classes','event_offset_minutes'):
            restored.stage_edit('swiat','global',key,'auto')
        for cls,field in [('Mag','tactic_interval'),('Strażnik','guard_threshold_percent'),
                          ('Berserker','execute_threshold_percent')]:
            restored.stage_edit('przywolanie',cls,field,'auto')
        ok('Aktywowano' in restored.apply(server,'reset_v23'))
        ok(multi_cap_experience_v23215(capdb.conn,1)==5500)
        ok(not SUMMON_TACTICS and not WORLD_OVERRIDES)
        ok(plan_for_class('Mag',owner_hp=100,owner_max=100,step=2,marked=False)['action']=='strike')
        ok(active_city_event_v12812(now=0)['slug']=='basalt')
        # Rollback latest revision restores previous active v23 (SQLite history).
        ok('Aktywowano' in restored.apply(server,'rollback_v23',rollback=True))
        ok(multi_cap_experience_v23215(capdb.conn,1)==result[0])
        ok(SUMMON_TACTICS['Mag']['tactic_interval']==2)
        restored._remove(world)
        capdb.conn.close()
    finally:
        service._remove(world)
        CLASS_AI.clear(); CLASS_AI.update(original_class_ai)
        WORLD_OVERRIDES.clear(); SUMMON_TACTICS.clear()
        conn.close()
    return n

if __name__ == '__main__':
    print('V23 OLC27 INTEGRATION:',run(),'PASS')
