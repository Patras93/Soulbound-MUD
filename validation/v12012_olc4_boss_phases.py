# -*- coding: utf-8 -*-
"""OLC 4.0 phase editing: SQLite, validation, live actions, rollback, protected AI."""
import copy
import json
import sqlite3
from types import SimpleNamespace

from data.mobs import MOB_TEMPLATES
from systems.live_content_v1204 import LiveContentV1204
from systems.live_olc4_boss_phases import default_boss_phases, validate_boss_phases
from systems.live_olc_preview_v12010 import describe_current_edit
from systems.live_olc4_browse import find_catalog
from systems.encounter_brain_v1230 import boss_tactics_phase_v1230
from systems.monster_ai import monster_ai_attack_multiplier_v1160


def run():
    checks = 0
    original = copy.deepcopy(MOB_TEMPLATES['bandit_captain'])
    db_conn = sqlite3.connect(':memory:')
    db_conn.row_factory = sqlite3.Row
    db_conn.execute('CREATE TABLE quests (quest_id TEXT, status TEXT)')
    world = SimpleNamespace(mobs={}, _last_refresh_at=0.0, _register_runtime_spawn=lambda *a: None)
    server = SimpleNamespace(world=world, sessions=[])
    svc = LiveContentV1204(SimpleNamespace(conn=db_conn))
    rules = [
        {'hp_percent':80, 'attack_multiplier':1.28, 'duration_seconds':44, 'message':'Bandyci ruszają!'},
        {'hp_percent':60, 'attack_multiplier':1.64, 'duration_seconds':36, 'message':'Rozkaz do kontrataku!'},
        {'hp_percent':30, 'attack_multiplier':2.0, 'duration_seconds':20, 'message':'Ostatnie siły!'},
    ]
    try:
        before = copy.deepcopy(svc.draft)
        preview = describe_current_edit(svc,'mob','bandit_captain','olc_boss_phases')
        assert '75' in preview and '50' in preview and '25' in preview and 'admin live edytuj mob' in preview
        checks += 1
        assert svc.draft == before and svc.revision == 0
        checks += 1
        for wrong in (
            {}, [], rules[:2], rules+rules[:1],
            [{**rules[0], 'hp_percent': True}, *rules[1:]],
            [{**rules[0], 'hp_percent': 50}, *rules[1:]],
            [{**rules[0], 'attack_multiplier': 0.25}, *rules[1:]],
            [{**rules[0], 'duration_seconds': 0}, *rules[1:]],
            [{**rules[0], 'message': 'x\ny'}, *rules[1:]],
            [{**rules[0], 'hack': 'eval'}, *rules[1:]],
        ):
            try:
                svc.stage_edit('mob', 'bandit_captain', 'olc_boss_phases',json.dumps(wrong))
            except ValueError:
                checks += 1
            else:
                raise AssertionError('Invalid phase rule accepted')
        for invalid_boss in ('temple_rat','goblin_king'):
            try:
                svc.stage_edit('mob', invalid_boss, 'olc_boss_phases', json.dumps(rules))
            except ValueError:
                checks += 1
            else:
                raise AssertionError('Ordinary or protected boss accepted')
        svc.stage_edit('mob', 'bandit_captain', 'olc_boss_phases', json.dumps(rules, ensure_ascii=False))
        checks += 1
        assert 'olc_boss_phases' not in MOB_TEMPLATES['bandit_captain']
        checks += 1
        assert svc.apply(server,'admin').startswith('Aktywowano rewizję 1')
        checks += 1
        assert MOB_TEMPLATES['bandit_captain']['olc_boss_phases']==rules
        checks += 1
        assert 'olc_boss_phases' in svc.active['mob_edits']['bandit_captain']
        checks += 1
        mock = SimpleNamespace(alive=True,hp=85,adaptive_max_hp_v11330=100,v1230_boss_phase=0)
        assert boss_tactics_phase_v1230(mock, MOB_TEMPLATES['bandit_captain'],now=100) is None
        checks += 1
        mock.hp=80
        message = boss_tactics_phase_v1230(mock,MOB_TEMPLATES['bandit_captain'],now=100)
        assert 'Bandyci ruszają!' in message and mock.v1230_boss_phase==1
        checks += 1
        assert mock.monster_ai_empowered_until_v1160 == 144
        checks += 1
        assert monster_ai_attack_multiplier_v1160(mock,now=100) == 1.28
        checks += 1
        assert boss_tactics_phase_v1230(mock,MOB_TEMPLATES['bandit_captain'],now=101) is None
        checks += 1
        mock.hp=20
        assert 'Ostatnie siły!' in boss_tactics_phase_v1230(mock,MOB_TEMPLATES['bandit_captain'],now=110)
        checks += 1
        assert mock.v1230_boss_phase == 3 and mock.monster_ai_empowered_until_v1160 == 130
        checks += 1
        assert monster_ai_attack_multiplier_v1160(mock,now=115)==2
        checks += 1
        assert monster_ai_attack_multiplier_v1160(mock,now=131)==1
        checks += 1
        # Only live edit values change, original HP and EXP untouched.
        assert {k:MOB_TEMPLATES['bandit_captain'][k] for k in ('max_hp','damage','class_xp_reward')} == {k:original[k] for k in ('max_hp','damage','class_xp_reward')}
        checks += 1
        # Protection: no edits to a template that is currently engaged.
        svc.stage_edit('mob','bandit_captain','olc_boss_phases','auto')
        world.mobs[1]=SimpleNamespace(engaged_by='player',aoe_engaged_by=set(),template_id='bandit_captain', home_room_id='market',room_id='market')
        try:
            svc.apply(server,'admin')
        except ValueError:
            checks += 1
        else:
            raise AssertionError('Applied boss phase edit during active combat')
        world.mobs.clear()
        assert 'rewizję 2' in svc.apply(server,'admin')
        checks += 1
        assert 'olc_boss_phases' not in MOB_TEMPLATES['bandit_captain']
        checks += 1
        legacy = SimpleNamespace(alive=True,hp=74,adaptive_max_hp_v11330=100,v1230_boss_phase=0)
        assert 'FAZA 1/3' in boss_tactics_phase_v1230(legacy,MOB_TEMPLATES['bandit_captain'],now=100)
        checks += 1
        assert abs(legacy.v1230_phase_attack_multiplier - 1.24) < 1e-9
        checks += 1
        assert svc.apply(server,'admin',rollback=True).startswith('Aktywowano rewizję 3')
        checks += 1
        assert MOB_TEMPLATES['bandit_captain']['olc_boss_phases']==rules
        checks += 1
        assert svc._compat({k:v for k,v in svc.active.items() if k != 'shop_edits'})['shop_edits'] == {}
        checks += 1
        assert default_boss_phases(original)[0]['hp_percent']==75
        checks += 1
        # Entirely NEW ordinary boss, authored with safe catalog data only.
        new_id = 'live_olc4_stage_boss'
        svc.stage_mob(new_id, 'Nowy Boss Testowy', 80, 100000, 200, 4000)
        checks += 1
        try:
            svc.stage_edit('mob','temple_rat','boss','true')
        except ValueError:
            checks += 1
        else:
            raise AssertionError('Base catalog boss flag changed')
        svc.stage_edit('mob',new_id,'boss','true')
        checks += 1
        assert '75' in describe_current_edit(svc,'mob',new_id,'olc_boss_phases')
        checks += 1
        svc.stage_edit('mob',new_id,'olc_boss_phases',json.dumps(rules))
        checks += 1
        svc.stage_spawn('market',new_id)
        checks += 1
        assert new_id in find_catalog(svc,'mob','olc4_stage_boss')
        checks += 1
        assert new_id not in MOB_TEMPLATES
        checks += 1
        assert 'rewizję 4' in svc.apply(server,'admin')
        checks += 1
        assert MOB_TEMPLATES[new_id]['boss'] is True
        checks += 1
        assert MOB_TEMPLATES[new_id]['olc_boss_phases'] == rules
        checks += 1
        new_mob=SimpleNamespace(alive=True,hp=60000,adaptive_max_hp_v11330=100000,v1230_boss_phase=0)
        assert 'FAZA 2/3' in boss_tactics_phase_v1230(new_mob,MOB_TEMPLATES[new_id],now=100)
        checks += 1
        assert new_mob.v1230_phase_attack_multiplier==1.64
        checks += 1
        # Safely revert new template, spawn and phases in one historical revision.
        assert 'rewizję 5' in svc.apply(server,'admin',rollback=True)
        checks += 1
        assert new_id not in MOB_TEMPLATES
        checks += 1
    finally:
        svc._remove(world)
        MOB_TEMPLATES['bandit_captain'] = original
        db_conn.close()
    return checks

if __name__=='__main__':
    print('OLC 4.0 boss phases:',run(),'PASS')
