# -*- coding: utf-8 -*-
"""v12.00.1: crypt progression, dynamic floor elites and one-time Fame."""
from __future__ import annotations


def run_regression():
    import sqlite3
    from types import SimpleNamespace
    import server
    from systems.content_registry import MOB_TEMPLATES
    from systems.fame_v1702 import fame_catalog, record_fame_kill, _is_fame_target, fame_region
    from world.economy_quests import create_infinite_crypt_floor_definition
    from world.crypt_floor_progression import v0190_combat_reward
    checks = 0
    for floor in (1, 5, 10, 35, 195, 200):
        assert f'crypt_elite_guardian_{floor}' in MOB_TEMPLATES
        checks += 1
    for floor in (1, 2, 5, 10, 100):
        mob=MOB_TEMPLATES[f'crypt_floor_mob_{floor}']
        assert int(mob['max_hp'])>0 and int(mob['damage'])>0
        assert v0190_combat_reward(mob, 'class')>0
        checks += 2
    assert not _is_fame_target(MOB_TEMPLATES['crypt_floor_mob_1'])
    assert _is_fame_target(MOB_TEMPLATES['crypt_elite_guardian_1'])
    assert _is_fame_target(MOB_TEMPLATES['crypt_boss_10'])
    checks += 3
    assert v0190_combat_reward(MOB_TEMPLATES['crypt_floor_mob_2'], 'class') > v0190_combat_reward(MOB_TEMPLATES['crypt_floor_mob_1'], 'class')
    checks += 1
    conn=sqlite3.connect(':memory:')
    try:
        session=SimpleNamespace(account_id=42)
        elite=SimpleNamespace(template_id='crypt_elite_guardian_1',room_id='crypt_floor_1',home_room_id='crypt_floor_1')
        assert len(record_fame_kill(conn,[session],elite,MOB_TEMPLATES[elite.template_id]))==1
        assert len(record_fame_kill(conn,[session],elite,MOB_TEMPLATES[elite.template_id]))==0
        normal=SimpleNamespace(template_id='crypt_floor_mob_1',room_id='crypt_floor_1',home_room_id='crypt_floor_1')
        assert len(record_fame_kill(conn,[session],normal,MOB_TEMPLATES[normal.template_id]))==0
        checks += 3
    finally:
        conn.close()
    zone=fame_region('crypt_floor_1')
    assert 'crypt_elite_guardian_1' in fame_catalog().get(zone,())
    checks += 1
    rid, spawns = create_infinite_crypt_floor_definition(205)
    assert any(tid=='crypt_elite_guardian_205' for _,tid in spawns)
    assert _is_fame_target(MOB_TEMPLATES['crypt_elite_guardian_205'])
    checks += 2
    return checks

if __name__=='__main__':
    print('KRYPTA v12.00.1:',run_regression(),'checks PASS')
