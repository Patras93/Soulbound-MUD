# -*- coding: utf-8 -*-
"""Small mandatory fail-closed smoke gate before the full Windows 60/60 PLUS.

Runs real mechanics with synthetic actors and in-memory or disposable SQLite.
Never replaces any of the 60 historical or three universal release gates.
"""
from __future__ import annotations
import sys
import unittest
from pathlib import Path

ROOT=Path(__file__).resolve().parent
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))


def run():
    # Fail in milliseconds on a new unclassified empty exception handler in
    # this sensitive driver; the full historical audit checks all sources.
    from validation.current_predeploy_parallel_resources_regression import check_no_swallowed_handlers
    check_no_swallowed_handlers(ROOT / 'testuj_soulbound_windows.py')
    print('KONTROLA WSTEPNA: pusty except w harmonogramie 0/0 PASS', flush=True)
    # The historical full audit found two fresh empty except handlers only
    # after the expensive runtime phases. Scan every Python file BEFORE 60/60,
    # using the same classification contract as the existing gate. This costs
    # just a few seconds and leaves ALL original tests mandatory.
    audited = 0
    for source in ROOT.rglob('*.py'):
        if '__pycache__' not in source.parts:
            check_no_swallowed_handlers(source)
            audited += 1
    print(f'KONTROLA WSTEPNA: {audited} plikow Python, 0 nieklasyfikowanych pustych except PASS', flush=True)
    from validation.v2003_engine_optimization import run_regression as engine_test
    from validation.current_corpse_ground_lifecycle_regression import TestGroundLifecycle
    from validation.current_crypt_overcap_party_regression import run as crypt_test

    # In the previous attempt a modified source-pinned look() failed late in
    # the historical audit. Check ALL pinned native methods before 60/60.
    from validation.current_native_v420_contract import EXPECTED, verify_native_method
    protected = 0
    for relative, methods in EXPECTED.items():
        for method in methods:
            verify_native_method(ROOT / relative, method)
            protected += 1
    print(f'KONTROLA WSTEPNA: chronione historyczne metody AST PASS ({protected})',flush=True)
    # v116.00.63: WinError 121 during TCP read closes the session cleanly.
    from validation.current_windows_tcp_read_timeout_v11663_regression import run as tcp_timeout_test
    assert tcp_timeout_test() == 7
    print('WINDOWS TCP READ TIMEOUT v116.00.63: 7/7 PASS', flush=True)
    # v116.67: fail immediately if cast/c collide with the canonical skill command.
    from validation.current_cast_command_alias_v11667_regression import run as cast_skill_alias_test
    assert cast_skill_alias_test() == 14
    from validation.current_v114_published_native_contract_regression import run as published_native_test
    published_native_test()
    from validation.current_v11325_item_description_contract import run as item_description_test
    item_description_test()
    print('KONTROLA WSTEPNA: opisy przedmiotow i zgodnosc AST PASS',flush=True)
    # Fail in seconds if CPU/RAM selection or 8-worker isolation regresses.
    from validation.current_predeploy_parallel_resources_regression import run as parallel_test
    parallel_test()
    from validation.current_predeploy_historical_parallel_regression import run_regression as historic_parallel_test
    historic_parallel_test()
    from validation.current_predeploy_critical_path_regression import run_regression as critical_path_test
    critical_path_test()
    # This exact regression previously raised AttributeError: ground_loot.
    engine_checks=engine_test()
    print(f'KONTROLA WSTEPNA: silnik i odswiezanie swiata PASS ({engine_checks})',flush=True)
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(TestGroundLifecycle)
    result=unittest.TextTestRunner(stream=sys.stdout,verbosity=0).run(suite)
    if not result.wasSuccessful() or result.testsRun != suite.countTestCases():
        raise AssertionError('Ciala i przedmioty na ziemi: test FAIL')
    print(f'KONTROLA WSTEPNA: ciala / EQ / ziemia PASS ({result.testsRun})',flush=True)
    crypt_test()  # raises on a failed assertion; prints the achieved check count
    from validation.current_fame_immediate_regression import run as current_fame_test
    current_fame_test()  # instant kill EXP, separate first Fame bonus, legacy debt
    print('KONTROLA WSTEPNA: natychmiastowy EXP i osobny Fame PASS',flush=True)
    # v116.66: catch Fame message syntax that bytecode compilation permits.
    from validation.current_fame_message_v11666_regression import run as fame_message_test
    assert fame_message_test() == 8
    # v116.00.62: Soul Tier ma blokowac nowe nagrody i bank do unlock.
    from validation.current_soul_tier_lock_v11662_regression import run as soul_gate_test
    assert soul_gate_test() == 4
    print('SOUL TIER LOCK NO NEW XP v116.00.62: 4/4 PASS', flush=True)
    # v116.64: all class starting schools and own teachers, portal confirmation.
    from validation.current_class_schools_v11664_regression import run as class_schools_test
    assert class_schools_test() == 7
    print('CLASS SCHOOLS AND TEACHERS: 7/7 PASS',flush=True)
    # v116.64: assert LIVE kill/quest/EP/Fame source balance, not legacy fixtures.
    from validation.current_global_rebalance_v11664_regression import run as global_rebalance_test
    assert global_rebalance_test() == 8
    print('GLOBAL REBALANCE v116.64: 8/8 PASS',flush=True)
    # v116.65: no player summons in live runtime; UOSS NPC helpers remain.
    from validation.current_retired_player_minions_v11665_regression import run as retired_summons_test
    assert retired_summons_test() == 17
    # v116.64: mandatory active-runtime removal of CAP, bank and hirelings.
    from validation.current_no_cap_hires_cast_v11664_regression import run as no_cap_no_hires_test
    assert no_cap_no_hires_test() == 5
    print('NO CAP / NO HIRES / SKELETAL CAST: 5/5 PASS',flush=True)
    # v116.00.53: Future EP/Fame must not issue the full escalating cap.
    from validation.current_milestone_pacing_v11653_regression import run as milestone_pacing_test
    assert milestone_pacing_test() >= 60
    print('V116.00.53 MILESTONE EP/FAME 5/10 PROCENT: PASS',flush=True)
    # v116.00.50: each party member must keep all hires and summons;
    # cached world events and atlas must not rescan 37k rooms per step.
    from validation.current_six_player_helpers_performance_v11650_regression import run as six_helpers_test
    six_helpers_test()
    from validation.current_world_event_atlas_cache_v11650_regression import run as caches_test
    caches_test()
    print('KONTROLA WSTEPNA: 6 graczy, najemnicy, chowance i cache swiata PASS', flush=True)
    from validation.current_world_balance_stage_v11650_regression import run as stage_balance_test
    stage_balance_test()  # every world zone; higher-stage mobs resist group+helpers
    from validation.current_global_combat_balance_v11651_regression import run as global_balance_test
    global_balance_test()  # cap stacking, Krypta floor 60, all ranks and 1-6 players
    print('KONTROLA WSTEPNA: globalny balans HP 1-6 graczy i krypta pietro 60 PASS',flush=True)
    from validation.current_global_party_dps_v11652_regression import run as party_damage_balance_test
    party_damage_balance_test()  # all world ranks/regions + actual live HP route
    # v116.00.56: real learned Mec and other class skill-burst test.
    from validation.current_skill_burst_v11656_regression import run as learned_burst_test
    assert learned_burst_test() >= 15
    print('KONTROLA WSTEPNA: skille 1-6 graczy i wsparcie przeciw one-shot PASS',flush=True)
    # v116.00.57: actual helper full-strength opening and cached roaming graph.
    from validation.current_combat_performance_v11657_regression import run as combat_perf_test
    assert combat_perf_test() >= 140
    print('KONTROLA WSTEPNA: historyczna wydajnosc helperow i cache wedrowek PASS; najemnicy w nowej grze nieaktywni',flush=True)
    print('KONTROLA WSTEPNA: globalny balans realnej sily drużyny 1-6 graczy PASS', flush=True)
    print('KONTROLA WSTEPNA: trudnosc calego swiata i 1-6 graczy PASS', flush=True)
    from validation.current_quest_accept_performance_regression import run as quest_lookup_test
    quest_lookup_test()  # NPC lookup: preserve names, forbid whole-world offer scans
    print('KONTROLA WSTEPNA: szybkie przyjmowanie questow PASS',flush=True)
    from validation.current_city_pest_quest_regression import run as city_pest_test
    city_pest_test()  # authored city threat, room-aware and nested runtime variants
    print('KONTROLA WSTEPNA: questy i walka PASS',flush=True)
    from validation.current_movement_tempo_regression import run as movement_tempo_test
    movement_tempo_test()
    print('KONTROLA WSTEPNA: krok 0,10 sekundy PASS',flush=True)
    # Regression against rapid `walk krypta dol` and followers busy in combat.
    # Blocking before 60/60 avoids a long run that would still fail release.
    from validation.current_party_fast_crypt_follow_regression import run as crypt_follow_test
    crypt_follow_test()
    print('KONTROLA WSTEPNA: szybkie prowadzenie druzyny PASS',flush=True)
    # v116.00.55: newest production hot paths; fail before costly 60 PLUS.
    from validation.current_live_performance_v11655_regression import run as live_perf_test
    assert live_perf_test() >= 480
    print('KONTROLA WSTEPNA: wydajnosc aktywnego swiata, tras i EQ PASS',flush=True)
    # The help atlas tests create a full catalogue and may get stuck when
    # sharing the warmed-up engine process. A clean isolated Python process
    # checks the same authored atlas contract without leaking runtime state.
    import subprocess as _sb_subprocess
    import sys as _sb_sys
    help_result = _sb_subprocess.run(
        [_sb_sys.executable, '-u', '-m', 'validation.current_help_atlas_regression'],
        cwd=ROOT, capture_output=True, text=True, timeout=45, check=False)
    if help_result.returncode or 'CURRENT HELP/ATLAS:' not in help_result.stdout or 'PASS' not in help_result.stdout:
        raise AssertionError('Atlas help fail: '+(help_result.stdout + help_result.stderr)[-1500:])
    print('KONTROLA WSTEPNA: pomoc i atlasy PASS',flush=True)
    # v114: run isolated progression regressions as fail-closed checks before
    # the expensive 60 historical gates. The Tier test needs the preserved
    # v106 T6000 authored catalogue, but no production records or services.
    import os
    import subprocess
    import sys as _sys
    env=dict(os.environ)
    env['SOULBOUND_V106_STAGING']='1'
    for module in ('validation.v11400_soul_infinite_regression',
                   'validation.current_unbounded_progression_v114_regression',
                   'validation.current_soul_v113_pacing_v11403_regression',
                   'validation.current_v11405_emergency_regression',
                   'validation.current_nopycache_v11406_regression',
                   'validation.v11400_xp_late_continuation_regression',
                   'validation.current_saved_content_compatibility_regression',
                   'validation.current_published_nonempty_startup_regression',
                   'validation.current_published_readonly_regression',
                   'validation.current_expbank_all_v114_regression',
                   'validation.current_retire_live_content_regression'):
        command=[_sys.executable, '-u', '-m', 'unittest', module, '-q'] if module.endswith('soul_infinite_regression') else [_sys.executable, '-u', '-m', module]
        result=subprocess.run(command, cwd=ROOT, env=env, capture_output=True,
                              text=True, timeout=60, check=False)
        if result.returncode:
            raise AssertionError('v114 regression FAIL '+module+': '+(result.stdout+result.stderr)[-2000:])
        print('KONTROLA WSTEPNA v114: '+module+' PASS '+(result.stdout+result.stderr)[-240:].strip(),flush=True)
    return True


if __name__ == '__main__':
    try:
        run()
    except Exception as exc:
        print(f'KONTROLA WSTEPNA FAIL: {type(exc).__name__}: {exc}',file=sys.stderr,flush=True)
        raise
    print('KONTROLA WSTEPNA PASS - start pelnego 60/60 PLUS',flush=True)
