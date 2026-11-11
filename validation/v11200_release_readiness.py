# -*- coding: utf-8 -*-
"""v112: fail-closed release preflight; one self-contained runtime."""
from __future__ import annotations
import ast
from pathlib import Path
from systems.v11200_activation import REQUIRED

ROOT=Path(__file__).resolve().parents[1]
EXTRAS=(
    'validation/current_explicit_runtime_regression.py',
    'validation/current_six_client_tcp.py',
    'validation/current_catalog_equivalence.py',
    'validation/current_catalog_baseline.json',
    'validation/current_install_regression.py',
    'validation/current_activation_independence_regression.py',
    'validation/test_runtime_explicit_mixins.py',
    'validation/current_only_server_smoke.py',
    'validation/v11200_release_readiness.py',
    'validation/v11200_runtime_independence_regression.py',
    'validation/v11200_installer_independence_regression.py',
    'validation/v11200_closed_runtime_gate.py',
    'validation/v11200_parallel_schedule_regression.py',
    'validation/v11200_eternal_glory_ownership_regression.py',
    'validation/v11200_catalog_gift_ownership_regression.py',
    'validation/v11200_realms_ownership_regression.py',
    'validation/v11200_horizons_ownership_regression.py',
    'validation/v11200_profession_ownership_regression.py',
    'validation/v11200_big_batch_ownership_regression.py',
    'validation/v11200_big_batch_manifest.json',
    'validation/v11200_fresh_install_regression.py',
    'core/source_contracts.py',
    'predeploy_check.py',
    'validation/v11200_release_suite.py',
    'validation/v11200_release_activation_regression.py',
    'validation/v11200_broken_v111_recovery_regression.py',
    'validation/v11100_v107_functional_audit.py',
    'validation/v11100_holiday_contract.py',
    'validation/v11100_holiday_schedule_regression.py',
    'validation/v11100_holiday_events_regression.py',
    'validation/v11100_holiday_challenges_regression.py',
    'validation/v11100_holiday_combat_regression.py',
    'validation/v11100_holiday_prizes_regression.py',
    'validation/v11100_server_smoke.py',
)

def unmet_requirements(root=ROOT):
    root=Path(root)
    problems=[]
    try:
        if (root/'VERSION').read_text('utf-8-sig').strip()!='112.00.0':
            problems.append('VERSION nie jest 112.00.0')
        if 'VERSION = "112.00.0"' not in (root/'core/bootstrap_economy_professions.py').read_text('utf-8-sig'):
            problems.append('Kod gry nie ma wersji 112.00.0')
    except (OSError, UnicodeError) as exc:
        problems.append('Brak identyfikatora gry: '+str(exc))
    for rel in (*REQUIRED,*EXTRAS):
        file=root/rel
        if not file.is_file():
            problems.append('Brak pliku: '+rel)
        elif file.suffix=='.py':
            try:ast.parse(file.read_text(encoding='utf-8-sig'),filename=rel)
            except (SyntaxError, OSError, UnicodeError) as exc:problems.append('Błąd składni: '+rel+': '+str(exc))
    # Fast PREDEPLOY must read the shipped code via the current source contract,
    # not import the retired v4.20/v109 facades.  The historical modularization
    # test itself remains a separate, mandatory behavior/AST regression.
    try:
        source=(root/'predeploy_check.py').read_text(encoding='utf-8-sig')
        tree=ast.parse(source,filename='predeploy_check.py')
        legacy={'validation.v4200_virtual_source',
                'validation.v10900_actual_modular_source'}
        imported={node.module for node in ast.walk(tree)
                  if isinstance(node,ast.ImportFrom)}
        if imported & legacy:
            problems.append('Szybki PREDEPLOY nadal wymaga starego czytnika: '+
                            ', '.join(sorted(imported & legacy)))
        if 'core.source_contracts' not in imported:
            problems.append('Brak bieżącego czytnika źródeł PREDEPLOY')
        contracts=ast.parse((root/'core/source_contracts.py').read_text('utf-8-sig'))
        if not any(isinstance(node,ast.FunctionDef) and
                   node.name=='read_actual_modular_source_current'
                   for node in contracts.body):
            problems.append('Brak samodzielnego czytnika aktualnych modułów')
        for number in range(1,4):
            path=root/f'world/quests/base_{number:02d}.py'
            if not path.is_file() or path.is_symlink():
                problems.append('Brak aktualnego modułu zadań: '+str(path.relative_to(root)))
    except (OSError, SyntaxError, UnicodeError) as exc:
        problems.append('Weryfikacja aktualnego czytnika: '+str(exc))
    if (root/'LIVE_CONTENT/release_current.json').exists():
        problems.append('Kandydat nie może zawierać produkcyjnego manifestu')
    try:
        from testuj_soulbound_windows import STAGES
        if len(STAGES)!=60:
            problems.append('Niekompletne 60 etapów PREDEPLOY')
    except (ImportError, ValueError, OSError) as exc:
        problems.append('Tester Windows: '+repr(exc))
    return problems

if __name__=='__main__':
    errors=unmet_requirements()
    if errors:
        print('V112 READINESS FAIL: '+'; '.join(errors))
        raise SystemExit(2)
    print('V112 READINESS PASS: version, 60 stages, required runtime and standalone activation')
