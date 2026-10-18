# -*- coding: utf-8 -*-
"""ULTRA 60 PLUS step 60: preserves legacy cloned-data check, then deep properties."""
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
# When launched directly as validation/...py, validation/events.py must not
# shadow the gameplay events/ package while stage 60 imports server.
if str(ROOT) in sys.path:
    sys.path.remove(str(ROOT))
sys.path.insert(0, str(ROOT))
from validation.predeploy_ultimate60_v2329 import schema_and_data_preserved
from validation.predeploy_plus_v2330 import main as deep_checks

def main():
    schema_and_data_preserved()
    result=deep_checks()
    assert result>=5000
    from validation.v600_professions import run_regression as _v600_professions_regression
    profession_checks = _v600_professions_regression()
    assert profession_checks >= 1000
    print(f"PROFESJE 6.00.0: {profession_checks} assertions PASS", flush=True)
    from validation.v601_profession_paths import run_regression as _v601_paths
    quest_checks = _v601_paths()
    assert quest_checks >= 16000
    print(f"DROGA MISTRZA 8x120 v6.00.1: {quest_checks} assertions PASS", flush=True)
    from validation.v700_living_empire import run_regression as _v700_checks
    assert _v700_checks() >= 500
    print('ERA ZYJACEGO IMPERIUM v7.00.0: SQLite, fabula, transakcje, hunty PASS', flush=True)
    from validation.v710_quality_polish import run_regression as _v710_checks
    upgraded=_v710_checks()
    assert upgraded >= 290
    print(f'WIELKI SZLIF IMPERIUM v7.10.0: {upgraded} kontroli SQLite, fabuly i NVDA PASS', flush=True)

    # v7.10.1: final Windows 60/60 PLUS also checks the one-class migration
    # and restored physical/magic/Mec equipment split on isolated fixtures.
    from validation.v71101_single_class import run_regression as _one_class_v71101
    class_checks=_one_class_v71101()
    assert class_checks >= 41
    print(f'JEDNA KLASA v7.10.1: {class_checks} assertions PASS', flush=True)
    from validation.v3001_hybrid_equipment import run_regression as _eq_v71101
    eq_checks=_eq_v71101()
    assert eq_checks >= 43
    print(f'EQ FIZYCZNE / MAGICZNE / MEC v7.10.1: {eq_checks} assertions PASS', flush=True)
    # v8.00.0: repeated at the final PLUS gate with the production DB isolated.
    from validation.v800_class_sagas import run_regression as _v800_path_tests
    saga_checks=_v800_path_tests()
    assert saga_checks >= 18000
    print(f'DROGA LEGENDY v8.00.0: {saga_checks} assertions PASS',flush=True)
    from validation.v900_heroes import run_regression as _v900_heroes_plus
    print(f"NOWI BOHATEROWIE v9.00.0: {_v900_heroes_plus()} assertions PASS", flush=True)
    from validation.v1000_horizons import run_regression as _v1000_horizons_plus
    print(f"HORYZONTY v10.00.0: {_v1000_horizons_plus()} assertions PASS", flush=True)
    from validation.v1802_fame_expansion import run_regression as _v1100_fame_scope_plus
    fame_scope = _v1100_fame_scope_plus()
    assert fame_scope['targets']>=500 and fame_scope['pending_payout_once']
    print(f"V11 FAME 6.0: {fame_scope['targets']} important targets; no ordinary mobs; 100% CAP PASS",flush=True)
    from validation.v1100_eternal_glory import run_regression as _v1100_world_plus
    print(f"ERA WIECZNEJ CHWALY: {_v1100_world_plus()} assertions PASS", flush=True)
    from systems.eternal_glory_companions_v1100 import run_regression as _v1100_allies_plus
    print(f'V11 TACTICS: {_v1100_allies_plus()} assertions PASS', flush=True)
    from validation.v1100_worldcraft_depths import run_regression as _v1100_content_plus
    print(f"V11 PODZIEMIA I RZEMIOSLO: {_v1100_content_plus()} assertions PASS", flush=True)
    from core.class_mastery_v1100 import run_regression as _v1100_mastery_plus
    print(f'V11 KLASY 22: {_v1100_mastery_plus()} assertions PASS', flush=True)
    from validation.v1100_guild_tactics import run_regression as _v1100_guild_plus
    print(f'V11 GILDIE: {_v1100_guild_plus()} SQLite assertions PASS', flush=True)
    from validation.v3315_predeploy_5_players import run_regression as check_five_players
    extra=check_five_players()
    print(f'PREDEPLOY 5 GRACZY v3.31.5: {extra} assertions PASS', flush=True)
    # Run after every other audit because generated rooms are deliberately
    # inserted only when touched. This checks the real engine and unique spawns.
    from validation.v1100_infinite_runtime import run_regression as _infinite_v1100
    print(f'V11 NIESKONCZONE LOCHY: {_infinite_v1100()} real runtime assertions PASS', flush=True)
    print('PLUS CHECKS PASS',flush=True)
    print('ULTIMATE CASE 60/60 PLUS PASS',flush=True)

if __name__=='__main__':main()
