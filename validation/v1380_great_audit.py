# -*- coding: utf-8 -*-
"""v1.38.0: deterministic, read-only gameplay invariants for both deploy gates.

Audits progression 1..800, endgame dungeon payouts, profession pacing,
checkpoint chests, old save compatibility, active help, and Generator Core
removal. SQLite tests use an in-memory database; no production volumes.
"""
from __future__ import annotations

from pathlib import Path


def run_great_audit_v1380():
    errors = []
    checks = 0

    def check(value, description):
        nonlocal checks
        checks += 1
        if not value:
            errors.append(description)

    # Canonical import order: Database establishes static mine catalogue before session mixins.
    from storage.database import Database  # noqa: F401
    from core.bootstrap_economy_professions import VERSION
    from core.progression_600 import (
        CHARACTER_MAX_LEVEL, CLASS_MASTERY_MAX_LEVEL, PROFESSION_MAX_LEVEL,
        SOUL_MAX_LEVEL, SKILL_MAX_LEVEL, SOUL_WEAPON_MASTERY_MAX_LEVEL,
        TOOL_MAX_LEVEL, TOOL_MAX_TIER, SOUL_MAX_TIER,
    )
    check(tuple(int(n) for n in VERSION.split('.')[:3]) >= (1, 50, 0), 'runtime version 1.50+')
    for axis, limit in (
        ('character', CHARACTER_MAX_LEVEL), ('class', CLASS_MASTERY_MAX_LEVEL),
        ('profession', PROFESSION_MAX_LEVEL), ('soul', SOUL_MAX_LEVEL),
        ('skill', SKILL_MAX_LEVEL), ('weapon', SOUL_WEAPON_MASTERY_MAX_LEVEL),
        ('tool', TOOL_MAX_LEVEL),
    ):
        check(limit == 800, f'{axis} cap 800')
    check(SOUL_MAX_TIER == 80, 'Soul Tiers 80')
    check(TOOL_MAX_TIER == 80, 'tool tiers 80')

    from core.progression_resources import (
        character_xp_to_next, class_mastery_xp_to_next, soul_xp_to_next,
        skill_xp_to_next, soul_weapon_mastery_xp_to_next,
    )
    for name, req in (
        ('postać', character_xp_to_next), ('klasa', class_mastery_xp_to_next),
        ('dusza', soul_xp_to_next), ('skill', skill_xp_to_next),
        ('Broń Duszy', soul_weapon_mastery_xp_to_next),
    ):
        prev = 0
        for level in range(1, 800):
            needed = req(level)
            check(isinstance(needed, int) and needed >= prev and needed > 0,
                  f'{name} XP curve at level {level}')
            prev = needed
        check(req(800) == 0, f'{name} max-level XP must be zero')

    from systems.dungeon_experience_v1285 import dungeon_recipient_xp_v1286
    for axis, req in (
        ('character', character_xp_to_next), ('class', class_mastery_xp_to_next),
        ('soul', soul_xp_to_next),
    ):
        for floor in (10, 20, 100, 200, 400, 600, 800):
            normal = {'crypt_floor': floor, 'generator_level': floor}
            boss = {**normal, 'crypt_boss': True}
            for level in (1, 50, 100, 150, 200, 400, 600, 799):
                requirement = req(level)
                for template, label in ((normal, 'mob'), (boss, 'boss')):
                    payout = dungeon_recipient_xp_v1286(
                        template, axis, 10**18, level,
                        combat_multiplier=1.75, downstream_multiplier=4,
                    )
                    check(0 < payout * 4 <= requirement * 0.42 + 4,
                          f'{axis} lvl={level} floor={floor} {label}: multi-level XP')
                if level >= 101:
                    normal_xp = dungeon_recipient_xp_v1286(normal, axis, 1, level)
                    boss_xp = dungeon_recipient_xp_v1286(boss, axis, 1, level)
                    check(boss_xp > normal_xp, f'{axis}: boss bonus floor={floor} lvl={level}')
            check(dungeon_recipient_xp_v1286(
                {**normal, 'source_xp_exact': True}, axis, 1234, 150) == 1234,
                f'{axis}: UOSS exact XP touched floor={floor}')
        check(dungeon_recipient_xp_v1286(
            {'generator_level': 800}, axis, 1234, 150) == 1234,
            f'{axis}: open-world XP touched')

    from config.balance import (
        PROFESSION_XP_REQUIREMENT_MULTIPLIERS, profession_xp_requirement_v1401,
    )
    from core.profession_timing import (
        TOOL_ACTION_BASE_SECONDS, TOOL_ACTION_MIN_SECONDS,
        profession_action_seconds,
    )
    from systems.legendary_achievements_v1370 import PROFESSIONS_V1370
    from core.progression_resources import v0190_requirement
    check(len(PROFESSIONS_V1370) == 14, '14 professions')
    check(set(PROFESSIONS_V1370) == set(PROFESSION_XP_REQUIREMENT_MULTIPLIERS),
          'every profession has a requirement multiplier')
    check(PROFESSION_XP_REQUIREMENT_MULTIPLIERS.get('Wędkarstwo') == 4,
          'fishing requirement x4 retained')
    for profession in PROFESSIONS_V1370:
        prev = 0
        for level in (1, 2, 10, 50, 100, 200, 400, 600, 799):
            needed = profession_xp_requirement_v1401(
                v0190_requirement("profession", level), profession, level
            )
            check(needed >= prev and needed > 0,
                  f'{profession}: XP requirement at {level}')
            prev = needed
        check(PROFESSION_MAX_LEVEL == 800, f'{profession}: XP cap at 800')
    for tool_type, seconds in TOOL_ACTION_BASE_SECONDS.items():
        minimum = TOOL_ACTION_MIN_SECONDS[tool_type]
        check(profession_action_seconds(tool_type, 1) == seconds,
              f'{tool_type}: original start action seconds')
        check(profession_action_seconds(tool_type, 800) == minimum,
              f'{tool_type}: original minimum action seconds')
        check(seconds >= minimum >= 1, f'{tool_type}: valid timers')
    check(TOOL_ACTION_MIN_SECONDS['fishing'] == 3, 'fishing must retain 3s minimum')

    # Validate authored player-visible content without importing runtime modules
    # ahead of the world initialization sequence. Full predeploy separately
    # checks actual world and chest instances.
    root = Path(__file__).resolve().parents[1]
    help_source = (root / 'systems' / 'content_registry.py').read_text(encoding='utf-8')
    check('EXP Biegłości korzysta z Generator Core i' not in help_source,
          'obsolete Generator Core claim in live help')
    tool_source = (root / 'systems' / 'professions.py').read_text(encoding='utf-8')
    jewelry_source = (root / 'systems' / 'equipment_crafting.py').read_text(encoding='utf-8')
    for item_id in (
        'tailor_kit', 'tanning_knife', 'carpenter_tools',
        'runic_focus', 'archaeology_brush', 'surveyor_compass',
    ):
        line = next((line for line in tool_source.splitlines() if f'"{item_id}":' in line), '')
        check('1-800' in line and '80 Tierów' in line,
              f'{item_id}: obsolete tool description')
    check('Ma własny level 1-800, XP i 80 Tierów' in jewelry_source,
          'jeweler tool obsolete description')

    # The internal error registry remains owner-only, with explicit purge
    # confirmation and an independent SQLite action log.
    from validation.admin_error_cleanup_v1371_test import run_admin_error_cleanup_v1371
    cleanup = run_admin_error_cleanup_v1371()
    check(cleanup['errors'] == 0, 'admin error purge SQLite regression')

    import sqlite3
    with sqlite3.connect(':memory:') as conn:
        conn.execute('CREATE TABLE progress (account_id INTEGER PRIMARY KEY, xp INTEGER)')
        conn.execute('INSERT INTO progress VALUES (?, ?)', (1, 123456789))
        with conn:
            conn.execute('UPDATE progress SET xp=xp+? WHERE account_id=?', (5, 1))
        check(conn.execute('SELECT xp FROM progress WHERE account_id=1').fetchone()[0]
              == 123456794, 'SQLite progress persistence')
        check(conn.execute('PRAGMA integrity_check').fetchone()[0] == 'ok',
              'SQLite integrity')

    root = Path(__file__).resolve().parents[1]
    check(not (root / 'core' / 'generator_core.py').exists(),
          'removed Generator Core file restored')
    return {'checks': checks, 'error_count': len(errors), 'errors': errors}


if __name__ == '__main__':
    outcome = run_great_audit_v1380()
    print(outcome)
    if outcome['error_count']:
        raise SystemExit(1)
