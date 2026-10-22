# -*- coding: utf-8 -*-
"""Soulbound 21.00.0: live phase tactics, validation, SQLite and true AI paths."""
import copy
import json
import sqlite3
from types import SimpleNamespace

from data.mobs import MOB_TEMPLATES
from systems.live_olc21_phase_strategy import (
    PHASE_STRATEGY_FIELDS, phase_setting, validate_phase_strategy,
)
from systems.live_content_v1204 import LiveContentV1204
from systems.live_olc_preview_v12010 import describe_current_edit
from systems.boss_companions_v1281 import boss_companion_due_v1281
from systems.encounter_brain_v1230 import ordinary_tactics_v1230, tactical_element_v1230


def run():
    checks = 0
    def check(condition, description=''):
        nonlocal checks
        assert condition, description
        checks += 1
    def reject(fn, description):
        try: fn()
        except (ValueError, TypeError): check(True)
        else: raise AssertionError('Nie odrzucono: ' + description)

    # Strict validation also applies to entire imported revisions (not only commands).
    for field, rule in PHASE_STRATEGY_FIELDS.items():
        example = 'weakest' if isinstance(rule[0], str) else rule[0]
        check(validate_phase_strategy(field, {'0': example, '5': example}))
        check(phase_setting({field:{'5':example}},5,field,None) == example)
        check(phase_setting({field:{'5':example}},0,field,'odziedziczone') == 'odziedziczone')
        check(phase_setting({field:{'9':example}},9,field,'odziedziczone') == 'odziedziczone')
        check(phase_setting({field:{'2':True}},2,field,'odziedziczone') == 'odziedziczone')
        invalid = [None, {}, [], {'6':example}, {'-1':example}, {0:example},
                   {'0':None}, {'0':True}, {'0':1.0}, {'0':[]},
                   {'0':example,'1':None}, {'0':example,'7':example}]
        invalid += ([{'0':'zly'}, {'0':10}] if isinstance(rule[0],str) else
                    [{'0':rule[0]-1}, {'0':rule[1]+1}, {'0':'4'}])
        for payload in invalid:
            reject(lambda payload=payload:validate_phase_strategy(field,payload),str(payload))
    reject(lambda:validate_phase_strategy('olc_boss_phase_untrusted', {'0':4}), 'unknown key')

    # Full runtime test: phase-to-phase wave cadence, no cap on guardians.
    template={'name':'Zwykły boss','boss':True,'max_hp':1000,
              'olc_boss_guardian_interval':6,'olc_boss_phase_guardian_intervals':{'2':2}}
    mob=SimpleNamespace(alive=True,engaged_by={'gracz'},template_id='test_boss',
                        combat_turn=4,boss_last_summon_turn_v1281=-1,
                        hp=700,adaptive_max_hp_v11330=1000,v1230_boss_phase=0)
    check(not boss_companion_due_v1281(mob,template))
    mob.v1230_boss_phase=2
    check(boss_companion_due_v1281(mob,template))
    mob.boss_last_summon_turn_v1281=4
    check(not boss_companion_due_v1281(mob,template))
    mob.boss_last_summon_turn_v1281=-1
    check(not boss_companion_due_v1281(mob,dict(template,uoss_unique_superboss_key='black_rabite')))
    mob.v1230_boss_phase=0
    check(not boss_companion_due_v1281(mob,template))

    # Real tactical element decision depends on phase override rather than preview.
    spell={'name':'Wojownik testowy','boss':True,'max_hp':1000,
           'olc_boss_tactic_interval':5,'olc_boss_phase_tactic_intervals':{'2':3}}
    mob.combat_turn=3
    check(tactical_element_v1230(mob,spell) is None)
    mob.v1230_boss_phase=2
    result=tactical_element_v1230(mob,spell)
    check(isinstance(result,dict) and result.get('element') in
          ('fire','ice','lightning','dark','poison','shadow','holy'))
    check(tactical_element_v1230(mob,dict(spell,uoss_unique_superboss_key='black_rabite')) is None)

    def ally(key,hp):
        return SimpleNamespace(key=key,room_id='test_room',template_id='unit',
                               engaged_by='gracz',alive=True,hp=hp,adaptive_max_hp_v11330=100,monster_ai_guard_until_v1160=0)
    weak=ally('slaby',30); strong=ally('silniejszy',65)
    mob=SimpleNamespace(key='boss',template_id='test_boss',room_id='test_room',
                        alive=True,engaged_by='gracz',hp=72,combat_turn=4,
                        adaptive_max_hp_v11330=100,v1230_boss_phase=2)
    world=SimpleNamespace(room_mobs=lambda _:[mob,weak,strong])
    # Shared base catalog has no custom runtime history; avoid modifying global registration.
    rules={'boss':True,'name':'Wojownik testowy','max_hp':100,
           'olc_boss_guard_threshold':35,'olc_boss_support_interval':6,
           'olc_boss_rally_interval':6,
           'olc_boss_phase_guard_thresholds':{'2':80},
           'olc_boss_phase_support_intervals':{'2':4},
           'olc_boss_phase_support_durations':{'2':21},
           'olc_boss_phase_support_priorities':{'2':'strongest'},
           'olc_boss_phase_rally_hp_thresholds':{'2':80},
           'olc_boss_phase_rally_intervals':{'2':4},
           'olc_boss_phase_rally_durations':{'2':22}}
    msg=ordinary_tactics_v1230(world,mob,rules,now=1000)
    check('osłania' in msg and '21 sekund' in msg,repr(msg))
    check(strong.monster_ai_guard_until_v1160==1021)
    check(weak.monster_ai_guard_until_v1160==0)
    mob.monster_ai_next_action_v1160=0
    world.room_mobs=lambda _:[mob]
    msg=ordinary_tactics_v1230(world,mob,rules,now=1040)
    check('kontratak' in msg,repr(msg))
    check(mob.monster_ai_empowered_until_v1160 == 1062)
    mob.v1230_boss_phase=0
    mob.monster_ai_next_action_v1160=0
    check(ordinary_tactics_v1230(world,mob,rules,now=1100)=='')

    # Actual OLC: 9 fields staged, not applied until activation; source protected.
    conn=sqlite3.connect(':memory:')
    conn.row_factory=sqlite3.Row
    conn.execute('CREATE TABLE quests (quest_id TEXT, status TEXT)')
    world=SimpleNamespace(mobs={}, _last_refresh_at=0.,_register_runtime_spawn=lambda *a:None)
    server=SimpleNamespace(world=world,sessions=[])
    svc=LiveContentV1204(SimpleNamespace(conn=conn))
    base=copy.deepcopy(MOB_TEMPLATES['bandit_captain'])
    values={field:({'0':'weakest','2':'strongest'} if isinstance(rule[0],str)
                    else {'0':rule[0],'2':rule[1]}) for field,rule in PHASE_STRATEGY_FIELDS.items()}
    try:
        for field,val in values.items():
            view=describe_current_edit(svc,'mob','bandit_captain',field)
            check('obecnie: auto' in view and 'Do skopiowania' in view,view)
            svc.stage_edit('mob','bandit_captain',field,json.dumps(val))
            check(svc.draft['mob_edits']['bandit_captain'][field]==val)
            check(field not in MOB_TEMPLATES['bandit_captain'])
            check(str(val['2']) in describe_current_edit(svc,'mob','bandit_captain',field))
        original=copy.deepcopy(svc.draft)
        reject(lambda:svc.stage_edit('mob','bandit_captain','olc_boss_phase_tactic_intervals','{"0":true}'), 'bool')
        reject(lambda:svc.stage_edit('mob','bandit_captain','olc_boss_phase_guardian_intervals','{"7":4}'), 'phase 7')
        reject(lambda:svc.stage_edit('mob','bandit_captain','olc_boss_phase_support_priorities','{"2":"furia"}'), 'priority')
        reject(lambda:svc.stage_edit('mob','bandit_captain','olc_boss_phase_tactic_intervals','{"2":4,"7":4}'), 'extra phase')
        check(svc.draft==original,'invalid stage must be atomic')
        # Protection of authored superboss and normal mobs in validation.
        check(not svc.draft.get('rooms'))
        reject(lambda:svc.stage_edit('mob','temple_rat','olc_boss_phase_tactic_intervals','{"0":2}'), 'nonboss')
        svc.apply(server,'v2100_test')
        for field,val in values.items():
            check(MOB_TEMPLATES['bandit_captain'][field]==val)
        svc._remove(world)
        reopened=LiveContentV1204(SimpleNamespace(conn=conn))
        check(reopened.revision==1)
        for field,val in values.items():
            check(reopened.active['mob_edits']['bandit_captain'][field]==val)
            reopened.stage_edit('mob','bandit_captain',field,'auto')
        check(not reopened.draft['mob_edits'].get('bandit_captain'))
        reopened.apply(server,'v2100_test')
        for field in values:
            check(field not in MOB_TEMPLATES['bandit_captain'])
        reopened._remove(world)
    finally:
        svc._remove(world)
        check(MOB_TEMPLATES['bandit_captain']==base)
        conn.close()
    return checks


if __name__=='__main__':
    print('Soulbound v21.00.0 / OLC18:',run(),'PASS')
