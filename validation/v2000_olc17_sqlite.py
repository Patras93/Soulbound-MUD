# -*- coding: utf-8 -*-
"""OLC 17 staged activation, persistence, auto-rollback and UOSS protection."""
import copy
import sqlite3
from types import SimpleNamespace
from data.mobs import MOB_TEMPLATES
from systems.live_content_v1204 import LiveContentV1204
from systems.boss_companions_v1281 import boss_companion_due_v1281, boss_guardian_role_v12811
from systems.live_olc_preview_v12010 import describe_current_edit


def run():
    n = 0
    def ck(condition, message=''):
        nonlocal n
        assert condition, message
        n += 1
    conn = sqlite3.connect(':memory:')
    conn.row_factory = sqlite3.Row
    conn.execute('CREATE TABLE quests (quest_id TEXT, status TEXT)')
    world = SimpleNamespace(mobs={}, _last_refresh_at=0., _register_runtime_spawn=lambda *a:None)
    server = SimpleNamespace(world=world,sessions=[])
    svc = LiveContentV1204(SimpleNamespace(conn=conn))
    original = copy.deepcopy(MOB_TEMPLATES['bandit_captain'])
    try:
        stage = [
            ('olc_boss_guardian_hp_threshold','65',65),
            ('olc_boss_rally_hp_threshold','35',35),
            ('olc_boss_guardian_phase_roles','{"0":["zbrojny"],"2":["uzdrowiciel","furia"]}',
                                             {'0':['zbrojny'],'2':['uzdrowiciel','furia']}),
            ('olc_boss_phase_element_cycles','{"0":["fire","ice"],"2":["holy"]}',
                                            {'0':['fire','ice'],'2':['holy']})
        ]
        for field,raw,expected in stage:
            svc.stage_edit('mob','bandit_captain',field,raw)
            ck(svc.draft['mob_edits']['bandit_captain'][field] == expected)
            ck(field not in MOB_TEMPLATES['bandit_captain'])
            preview=describe_current_edit(svc,'mob','bandit_captain',field)
            ck('bandit_captain' in preview)
        before = copy.deepcopy(svc.draft)
        invalid = [
            ('olc_boss_guardian_hp_threshold','0'),
            ('olc_boss_guardian_hp_threshold','101'),
            ('olc_boss_rally_hp_threshold','4'),
            ('olc_boss_rally_hp_threshold','96'),
            ('olc_boss_guardian_phase_roles','{"0":["smok"]}'),
            ('olc_boss_phase_element_cycles','{"0":["smok"]}'),
            ('olc_boss_guardian_phase_roles','{"6":["zbrojny"]}'),
            ('olc_boss_phase_element_cycles','{"2":[]}'),
            ('olc_boss_phase_element_cycles','{"0":"fire"}'),
            ('olc_boss_guardian_phase_roles','{"0":["zbrojny"],"0x":["obronca"]}'),
        ]
        for field,raw in invalid:
            try: svc.stage_edit('mob','bandit_captain',field,raw)
            except (ValueError, TypeError):ck(True)
            else:raise AssertionError(f'Accepted {field}: {raw}')
            ck(before==svc.draft)
        svc.apply(server,'v2000_validation')
        for field,_,expected in stage:
            ck(MOB_TEMPLATES['bandit_captain'][field] == expected)
        mob=SimpleNamespace(alive=True,engaged_by={'p'},combat_turn=3,
                            hp=800,adaptive_max_hp_v11330=1000,
                            v1230_boss_phase=0,boss_last_summon_turn_v1281=-1)
        template=MOB_TEMPLATES['bandit_captain']
        ck(not boss_companion_due_v1281(mob,template))
        mob.hp=600
        ck(boss_companion_due_v1281(mob,template))
        ck(boss_guardian_role_v12811(template,mob,1)[0]=='zbrojny')
        mob.v1230_boss_phase=2
        ck(boss_guardian_role_v12811(template,mob,1)[0]=='uzdrowiciel')
        ck(not boss_companion_due_v1281(mob,dict(template,uoss_unique_superboss_key='black_rabite')))
        svc._remove(world)
        reopened=LiveContentV1204(SimpleNamespace(conn=conn))
        ck(reopened.revision == 1)
        for field,_,expected in stage:
            ck(reopened.active['mob_edits']['bandit_captain'][field]==expected)
            reopened.stage_edit('mob','bandit_captain',field,'auto')
        ck(not reopened.draft['mob_edits'].get('bandit_captain'))
        reopened.apply(server,'v2000_validation')
        for field,_,_ in stage:
            ck(field not in MOB_TEMPLATES['bandit_captain'])
        reopened._remove(world)
    finally:
        svc._remove(world)
        ck(MOB_TEMPLATES['bandit_captain'] == original)
        conn.close()
    return n

if __name__=='__main__':
    print('Soulbound v20.00.0 / OLC17 SQLite:',run(),'PASS')
