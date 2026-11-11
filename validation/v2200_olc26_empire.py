# -*- coding: utf-8 -*-
"""Integration: eight OLC areas, new runtime hooks, strict user JSON and SQLite."""
import copy
import json
import sqlite3
from types import SimpleNamespace
from data.mobs import MOB_TEMPLATES
from systems.live_content_v1204 import LiveContentV1204
from systems.live_olc22_empire import (validate_ancient,validate_summons,
    validate_world,ordinary_reward_bonus,extra_preview)
from systems.live_olc22_state import WORLD_OVERRIDES
from systems.summon_ai_v1200 import CLASS_AI,plan_for_class
from systems.world_events_v12812 import active_city_event_v12812
from systems.war_of_gods_bosses_v5000 import unique_phase, PROFILES
from systems.live_olc_preview_v12010 import describe_current_edit


def run():
    count=0
    def ok(x, reason=''):
        nonlocal count
        assert x, reason
        count+=1
    def rejected(fn, label):
        try: fn()
        except (TypeError, ValueError): ok(True)
        else: raise AssertionError('ACCEPTED INVALID: '+label)
    base = [{'hp_percent':80,'name':'Pierwsza Burza','attack_percent':150,
             'element':'lightning','duration_seconds':20},
            {'hp_percent':49,'name':'Nowy Sztorm','attack_percent':200,
             'element':'ice','duration_seconds':40},
            {'hp_percent':19,'name':'Błysk na Koniec','attack_percent':300,
             'element':'fire','duration_seconds':60}]
    ok(validate_ancient(base))
    for k in ('hp_percent','name','attack_percent','element','duration_seconds'):
        for candidate in (None,True,{},[],1.5):
            changed=copy.deepcopy(base);changed[0][k]=candidate
            rejected(lambda d=changed:validate_ancient(d),k+repr(candidate))
    for v in ([],[base[0]],base+[base[0]],{'0':base[0]},None,'[]'):
        rejected(lambda x=v:validate_ancient(x),'shape')
    for v in (-1,0,101,102,'3',True):
        changed=copy.deepcopy(base);changed[1]['hp_percent']=v
        rejected(lambda d=changed:validate_ancient(d),'hp')
    for v in (-1,0,99,1000,'200',False):
        changed=copy.deepcopy(base);changed[2]['attack_percent']=v
        rejected(lambda d=changed:validate_ancient(d),'attack')
    for v in ('unknown','electric','',15,None):
        changed=copy.deepcopy(base);changed[2]['element']=v
        rejected(lambda d=changed:validate_ancient(d),'element')
    for v in (0,-1,181,True,3.5,'33'):
        changed=copy.deepcopy(base);changed[2]['duration_seconds']=v
        rejected(lambda d=changed:validate_ancient(d),'duration')
    for v in ({'Druid':{'role':'heal','bonus_percent':200}}, {'Mag':{'ability':'Kula energii'}},
              {'Nekromanta':{'role':'curse','bonus_percent':300}}):
        ok(validate_summons(v))
    for v in ({'Foo':{'role':'heal'}}, {'Druid':{}}, {'Druid':{'hack':'x'}},
              {'Druid':{'bonus_percent':99}}, {'Druid':{'bonus_percent':301}},
              {'Druid':{'bonus_percent':True}}, {'Druid':{'role':'forbidden'}},
              {'Druid':{'ability':''}}, []):
        rejected(lambda x=v:validate_summons(x),'summons')
    for key,bad in [('combat_xp_bonus_percent',99),('combat_xp_bonus_percent',301),
                    ('combat_xp_bonus_percent',True),('event_cycle_minutes',29),
                    ('event_cycle_minutes',721),('event_cycle_minutes',3.5),
                    ('event_order',['basalt','basalt','star','myth']),('event_order',[]),
                    ('event_order','basalt'),('evil',33)]:
        rejected(lambda key=key,v=bad:validate_world({key:v}),key)
    ok(validate_world({'combat_xp_bonus_percent':200,'event_cycle_minutes':45,
                       'event_order':['myth','star','echo','basalt']}))
    ok(ordinary_reward_bonus(110)==110)
    ok(ordinary_reward_bonus(110,exact=True)==110)
    # A v500 ancient definition, not the separate original UOSS scripts.
    bossid='v4000_ancient_00_boss'
    original=MOB_TEMPLATES.get(bossid)
    template={'name':'Test Pradawny','max_hp':1000,'boss':True,'v500_ancient_profile':0}
    MOB_TEMPLATES[bossid]=template
    conn=sqlite3.connect(':memory:');conn.row_factory=sqlite3.Row
    conn.execute('CREATE TABLE quests (quest_id TEXT, status TEXT)')
    world=SimpleNamespace(mobs={},_last_refresh_at=0.,_register_runtime_spawn=lambda *a:None)
    server=SimpleNamespace(world=world,sessions=[])
    svc=LiveContentV1204(SimpleNamespace(conn=conn))
    class_ai=copy.deepcopy(CLASS_AI)
    try:
        # Eight areas: ancient v500, summons, profession/tool, skill, balance, event, quest/NPC, world.
        ok('olc_ancient_phases' in describe_current_edit(svc,'mob',bossid,'olc_ancient_phases'))
        svc.stage_edit('mob',bossid,'olc_ancient_phases',json.dumps(base))
        for name,val in [('przywolanie','Druid')]:
            ok('auto' in extra_preview(svc,name,val,'bonus_percent'))
        svc.stage_edit('przywolanie','Druid','role','guard')
        svc.stage_edit('przywolanie','Druid','bonus_percent','250')
        svc.stage_edit('przywolanie','Nekromanta','ability','Zew Dusz')
        svc.stage_edit('swiat','global','combat_xp_bonus_percent','160')
        svc.stage_edit('swiat','global','event_cycle_minutes','45')
        svc.stage_edit('swiat','global','event_order','["myth","star","echo","basalt"]')
        ok('45' in extra_preview(svc,'swiat','global','event_cycle_minutes'))
        ok(CLASS_AI==class_ai)
        ok(ordinary_reward_bonus(100)==100)
        ok(svc.draft['summon_edits']['Druid']['bonus_percent']==250)
        ok(MOB_TEMPLATES[bossid]==template)
        # Existing systems: editable profile for professions/tools, new skills and real NPC quests.
        svc.stage_edit('profesja','Kowalstwo','xp_scale','135')
        ok(svc.draft['profession_edits']['Kowalstwo']['xp_scale']==135)
        ok('skill_edits' in svc.draft and 'quests' in svc.draft and 'room_edits' in svc.draft)
        rejected(lambda:svc.stage_edit('mob','bandit_captain','olc_ancient_phases',json.dumps(base)),'protected old boss')
        rejected(lambda:svc.stage_edit('przywolanie','Druid','bonus_percent','99'),'summon nerf')
        rejected(lambda:svc.stage_edit('swiat','global','combat_xp_bonus_percent','70'),'xp nerf')
        rejected(lambda:svc.stage_edit('swiat','global','event_order','["star"]'),'events lost')
        # Do not affect original reward or UOSS exact source reward.
        result=svc.apply(server,'integracja')
        ok('Aktywowano' in result)
        ok(CLASS_AI['Druid'][1]=='guard')
        ok(CLASS_AI['Druid'][2]>class_ai['Druid'][2])
        ok(CLASS_AI['Nekromanta'][0]=='Zew Dusz')
        ok(ordinary_reward_bonus(100)==160)
        ok(ordinary_reward_bonus(100,exact=True)==100)
        ok(ordinary_reward_bonus(0)==0)
        ok(active_city_event_v12812(now=0)['slug']=='myth')
        ok(active_city_event_v12812(now=45*60)['slug']=='star')
        ok(active_city_event_v12812(now=45*60)['expires_at']==90*60)
        ok(MOB_TEMPLATES[bossid]['olc_ancient_phases']==base)
        m=SimpleNamespace(alive=True,hp=700,adaptive_max_hp_v11330=1000,v1230_boss_phase=0)
        msg=unique_phase(m,MOB_TEMPLATES[bossid],now=2000)
        ok('Pierwsza Burza' in msg)
        ok(m.v500_phase_element=='lightning')
        ok(m.monster_ai_empowered_until_v1160==2020)
        m.hp=150
        msg=unique_phase(m,MOB_TEMPLATES[bossid],now=2100)
        ok('Błysk na Koniec' in msg)
        ok(m.v1230_phase_attack_multiplier==3.0)
        ok(m.monster_ai_empowered_until_v1160==2160)
        # Simulate a genuine fresh process: remove in-memory live overlays.
        svc._remove(world)
        # Persisted revision reopens with same overrides.
        reopened=LiveContentV1204(SimpleNamespace(conn=conn))
        ok(reopened.revision==1)
        ok(reopened.active['world_overrides']['event_cycle_minutes']==45)
        ok(reopened.active['summon_edits']['Druid']['role']=='guard')
        ok(MOB_TEMPLATES[bossid]['olc_ancient_phases']==base)
        reopened.stage_edit('swiat','global','combat_xp_bonus_percent','auto')
        reopened.stage_edit('swiat','global','event_order','auto')
        reopened.stage_edit('swiat','global','event_cycle_minutes','auto')
        for key in ('Druid','Nekromanta'):
            for field in list(reopened.draft['summon_edits'].get(key,{})):
                reopened.stage_edit('przywolanie',key,field,'auto')
        reopened.stage_edit('mob',bossid,'olc_ancient_phases','auto')
        reopened.stage_edit('profesja','Kowalstwo','xp_scale','auto')
        ok('Aktywowano' in reopened.apply(server,'reset'))
        ok(ordinary_reward_bonus(100)==100)
        ok(CLASS_AI['Druid']==class_ai['Druid'])
        ok(MOB_TEMPLATES[bossid]==template)
        ok(active_city_event_v12812(now=0)['slug']=='basalt')
        reopened._remove(world)
        svc._remove(world)
        ok(CLASS_AI==class_ai)
        ok(ordinary_reward_bonus(100)==100)
    finally:
        svc._remove(world)
        WORLD_OVERRIDES.clear()
        CLASS_AI.clear();CLASS_AI.update(class_ai)
        if original is None:MOB_TEMPLATES.pop(bossid,None)
        else:MOB_TEMPLATES[bossid]=original
        conn.close()
    return count

if __name__=='__main__':
    print('Soulbound v22.00.0 OLC19-26:',run(),'PASS')
