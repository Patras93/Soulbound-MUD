# -*- coding: utf-8 -*-
"""Gameplay checks for Gor-Khaz and unlimited opening boss summons."""
from __future__ import annotations


def audit_orc_summons_v1301(rooms, mobs, spawns, npcs, quests):
    import world.world_state as ws
    from systems.boss_companions_v1281 import boss_companion_due_v1281
    errors = []
    checks = 0

    def check(condition, description):
        nonlocal checks
        checks += 1
        if not condition:
            errors.append(description)

    entrance = 'v1300_orc_border'
    check(rooms.get('v1300_lost_hamlet', {}).get('exits', {}).get('north') == entrance, 'orc entry')
    check(rooms.get(entrance, {}).get('exits', {}).get('south') == 'v1300_lost_hamlet', 'orc return')
    for role in ('gate', 'square', 'market', 'tavern', 'citadel', 'throne'):
        check('v1300_orc_' + role in rooms, 'orc role ' + role)
    for questid in ('defense', 'expedition', 'contract', 'saga_1', 'saga_2', 'saga_3'):
        quest = quests.get('v1300_orc_' + questid, {})
        check(any(n.get('name') == quest.get('giver') for n in npcs.values()), 'quest giver ' + questid)
    for key in ('v1300_orc_citadel_boss', 'v1300_orc_throne_boss'):
        check(key in mobs, 'orc boss ' + key)
    template = mobs['v1300_orc_throne_boss']
    boss = ws.MobState('test-orc-king', 'v1300_orc_throne', 'v1300_orc_throne_boss', hp=template['max_hp'], engaged_by='Tester')
    check(boss_companion_due_v1281(boss, template, opening=True), 'opening due')
    original_catalog = ws.MOB_TEMPLATES
    ws.MOB_TEMPLATES = dict(mobs)
    try:
        world = ws.World.__new__(ws.World)
        world.mobs = {boss.key: boss}
        world._last_refresh_at = 0.0
        guardian = world.spawn_boss_companion_v1281(boss)
        check(guardian is not None and guardian.alive, 'first guardian')
        if guardian:
            check(guardian.engaged_by == boss.engaged_by, 'summon engaged in same fight')
            boss.boss_opening_summoned_v1301 = True
            check(not boss_companion_due_v1281(boss, template, opening=True), 'opening only once')
            for turn in range(1, 13):
                boss.combat_turn = turn
                eligible = boss_companion_due_v1281(boss, template)
                check(eligible == (turn % 3 == 0), f'summon turn {turn}')
                if eligible:
                    add = world.spawn_boss_companion_v1281(boss)
                    check(add is not None and add.key != guardian.key, f'unlimited summon {turn}')
                    boss.boss_last_summon_turn_v1281 = turn
        for _ in range(15):
            world.spawn_boss_companion_v1281(boss)
        adds = [m for m in world.mobs.values() if getattr(m, 'monster_ai_parent_v1160', None) == boss.key]
        check(len(adds) == 20, '20 simultaneous guards')
        check(len({ws.MOB_TEMPLATES[a.template_id].get('boss_guardian_role_v12811') for a in adds}) == 5, 'five roles')
        uoss = dict(template, uoss_unique_superboss_key='black_rabite')
        check(not boss_companion_due_v1281(boss, uoss, opening=True), 'preserve UOSS special script')
    finally:
        ws.MOB_TEMPLATES = original_catalog
    return {'checks': checks, 'error_count': len(errors), 'errors': errors}
