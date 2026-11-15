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
    # Fail in seconds if CPU/RAM selection or 8-worker isolation regresses.
    from validation.current_predeploy_parallel_resources_regression import run as parallel_test
    parallel_test()
    # This exact regression previously raised AttributeError: ground_loot.
    engine_checks=engine_test()
    print(f'KONTROLA WSTEPNA: silnik i odswiezanie swiata PASS ({engine_checks})',flush=True)
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(TestGroundLifecycle)
    result=unittest.TextTestRunner(stream=sys.stdout,verbosity=0).run(suite)
    if not result.wasSuccessful() or result.testsRun != suite.countTestCases():
        raise AssertionError('Ciala i przedmioty na ziemi: test FAIL')
    print(f'KONTROLA WSTEPNA: ciala / EQ / ziemia PASS ({result.testsRun})',flush=True)
    crypt_test()  # raises on a failed assertion; prints the achieved check count
    print('KONTROLA WSTEPNA: questy i walka PASS',flush=True)
    from validation.current_movement_tempo_regression import run as movement_tempo_test
    movement_tempo_test()
    print('KONTROLA WSTEPNA: krok 0,10 sekundy PASS',flush=True)
    # Regression against rapid `walk krypta dol` and followers busy in combat.
    # Blocking before 60/60 avoids a long run that would still fail release.
    from validation.current_party_fast_crypt_follow_regression import run as crypt_follow_test
    crypt_follow_test()
    print('KONTROLA WSTEPNA: szybkie prowadzenie druzyny PASS',flush=True)
    from validation.current_help_atlas_regression import run as help_test
    help_test()
    print('KONTROLA WSTEPNA: pomoc i atlasy PASS',flush=True)
    return True


if __name__ == '__main__':
    try:
        run()
    except Exception as exc:
        print(f'KONTROLA WSTEPNA FAIL: {type(exc).__name__}: {exc}',file=sys.stderr,flush=True)
        raise
    print('KONTROLA WSTEPNA PASS - start pelnego 60/60 PLUS',flush=True)
