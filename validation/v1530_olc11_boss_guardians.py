# -*- coding: utf-8 -*-
"""v15.30.0: optional guardian waves for ordinary bosses, without reward changes."""
import copy
import sqlite3
from types import SimpleNamespace

from data.mobs import MOB_TEMPLATES
from systems.boss_companions_v1281 import (
    GUARDIAN_ROLES_V12811, boss_companion_due_v1281, boss_guardian_role_v12811,
)
from systems.live_content_v1204 import LiveContentV1204


def run():
    checks = 0
    template = {'name': 'Zwykły boss', 'boss': True}
    boss = SimpleNamespace(alive=True, engaged_by={'player'}, combat_turn=3,
                           boss_last_summon_turn_v1281=-1, v1230_boss_phase=0)
    assert boss_companion_due_v1281(boss, template); checks += 1
    original_roles = [boss_guardian_role_v12811(template, boss, i)[0] for i in range(1, 6)]
    assert original_roles == [r[0] for r in GUARDIAN_ROLES_V12811]; checks += 1
    override = dict(template, olc_boss_guardian_interval=5,
                    olc_boss_guardian_roles=['uzdrowiciel', 'obronca'])
    assert not boss_companion_due_v1281(boss, override); checks += 1
    boss.combat_turn = 5
    assert boss_companion_due_v1281(boss, override); checks += 1
    boss.boss_last_summon_turn_v1281 = 5
    assert not boss_companion_due_v1281(boss, override); checks += 1
    boss.boss_last_summon_turn_v1281 = -1
    for i, role in enumerate(('uzdrowiciel', 'obronca', 'uzdrowiciel'), 1):
        assert boss_guardian_role_v12811(override, boss, i)[0] == role; checks += 1
    boss.v1230_boss_phase = 1
    assert boss_guardian_role_v12811(override, boss, 1)[0] == 'uzdrowiciel'; checks += 1
    # Unique UOSS encounters never enter the ordinary guardian system.
    uoss = dict(override, uoss_unique_superboss_key='black_rabite')
    assert not boss_companion_due_v1281(boss, uoss); checks += 1
    # Genuine UOSS summon semantics stay independent of the new ordinary-boss fields.
    from world.uoss_superboss_runtime import superboss_source_summons_v11162
    source = SimpleNamespace(combat_turn=2, uoss_last_summon_turn_v1144=-1)
    assert superboss_source_summons_v11162(None, {'uoss_unique_superboss_key':'black_rabite'},
                                          source, 'Summon Greater Demon') == ('uoss_add_greater_demon_v11156',)
    checks += 1
    conn=sqlite3.connect(':memory:')
    conn.row_factory=sqlite3.Row
    conn.execute('CREATE TABLE quests (quest_id TEXT, status TEXT)')
    world=SimpleNamespace(mobs={}, _last_refresh_at=0., _register_runtime_spawn=lambda *a:None)
    srv=SimpleNamespace(world=world,sessions=[])
    svc=LiveContentV1204(SimpleNamespace(conn=conn))
    old=copy.deepcopy(MOB_TEMPLATES['bandit_captain'])
    try:
        svc.stage_edit('mob', 'bandit_captain', 'olc_boss_guardian_interval', '5')
        svc.stage_edit('mob', 'bandit_captain', 'olc_boss_guardian_roles', '["uzdrowiciel","obronca"]')
        assert svc.draft['mob_edits']['bandit_captain']['olc_boss_guardian_interval']==5;checks+=1
        assert svc.draft['mob_edits']['bandit_captain']['olc_boss_guardian_roles']==['uzdrowiciel','obronca'];checks+=1
        for field, bad in [('olc_boss_guardian_interval','1'),('olc_boss_guardian_interval','13'),
                           ('olc_boss_guardian_roles','[]'),('olc_boss_guardian_roles','["niewidzialny"]'),
                           ('olc_boss_guardian_roles','[1]'),('olc_boss_guardian_roles','{"bad":1}')]:
            before=copy.deepcopy(svc.draft)
            try: svc.stage_edit('mob','bandit_captain',field,bad)
            except ValueError: checks+=1
            else: raise AssertionError(f'Accepted invalid {field}: {bad}')
            assert svc.draft == before;checks+=1
        svc.apply(srv, 'v1530_validation')
        assert MOB_TEMPLATES['bandit_captain']['olc_boss_guardian_interval'] == 5;checks+=1
        assert MOB_TEMPLATES['bandit_captain']['olc_boss_guardian_roles'] == ['uzdrowiciel','obronca'];checks+=1
        svc._remove(world)
        reopened=LiveContentV1204(SimpleNamespace(conn=conn))
        assert reopened.revision == 1;checks+=1
        assert reopened.active['mob_edits']['bandit_captain']['olc_boss_guardian_interval']==5;checks+=1
        reopened.stage_edit('mob','bandit_captain','olc_boss_guardian_interval','auto')
        reopened.stage_edit('mob','bandit_captain','olc_boss_guardian_roles','auto')
        assert not reopened.draft['mob_edits'].get('bandit_captain');checks+=1
        reopened.apply(srv,'v1530_validation')
        assert 'olc_boss_guardian_interval' not in MOB_TEMPLATES['bandit_captain'];checks+=1
        assert 'olc_boss_guardian_roles' not in MOB_TEMPLATES['bandit_captain'];checks+=1
        reopened._remove(world)
    finally:
        svc._remove(world)
        assert MOB_TEMPLATES['bandit_captain'] == old
        conn.close()
    return checks

if __name__ == '__main__':
    print('v15.30.0 OLC11 guardian waves:',run(),'PASS')
