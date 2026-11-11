# -*- coding: utf-8 -*-
"""v111: kontrola kompletności nowego kodu, bez aktywacji produkcji."""
from __future__ import annotations
from pathlib import Path
import ast
from systems.v11100_holiday_activation import REQUIRED
ROOT=Path(__file__).resolve().parents[1]
HOLIDAY=(
 'validation/v11100_predeploy_self_containment.py',
 'validation/v11100_canonical_quests_regression.py',
 'validation/v11100_v107_functional_audit.py',
 'validation/v11100_current_tail_isolation.py',
 'validation/v11100_private_fast_gate.py',
 'validation/v11100_holiday_contract.py',
 'validation/v11100_holiday_events_regression.py',
 'validation/v11100_holiday_schedule_regression.py',
 'validation/v11100_holiday_challenges_regression.py',
 'validation/v11100_holiday_combat_regression.py',
 'validation/v11100_holiday_prizes_regression.py',
 'validation/v11100_release_suite.py',
 'validation/v11100_minimal_runtime_regression.py',
)
def unmet_requirements(root=ROOT):
    root=Path(root)
    bad=[]
    try:
        if (root/'VERSION').read_text(encoding='utf-8-sig').strip()!='111.00.0':
            bad.append('VERSION nie jest 111.00.0')
        if 'VERSION = "111.00.0"' not in (root/'core/bootstrap_economy_professions.py').read_text(encoding='utf-8-sig'):
            bad.append('kod gry ma inny numer wersji')
    except OSError as exc: bad.append('Brak identyfikatora: '+str(exc))
    for name in (*REQUIRED,*HOLIDAY):
        p=root/name
        if not p.is_file():bad.append('Brak: '+name)
        elif p.suffix=='.py':
            try:ast.parse(p.read_text(encoding='utf-8-sig'),filename=name)
            except (SyntaxError,UnicodeError) as exc:bad.append('Składnia: '+name+': '+str(exc))
    # One durable v111 gate: a full test ZIP may contain hundreds of offline
    # regressions; the activated production manifest and installer must not.
    try:
        from validation.v11100_minimal_runtime_regression import main as _minimal_runtime_check
        _minimal_runtime_check()
    except (AssertionError, OSError, ValueError, RuntimeError, ImportError, KeyError) as exc:
        bad.append('Instalacja minimalna: '+repr(exc))
    if (root/'LIVE_CONTENT/release_current.json').is_file():
        bad.append('Znacznik może utworzyć wyłącznie instalator po PREDEPLOY')
    return bad
if __name__=='__main__':
    failures=unmet_requirements()
    if failures:
        print('V111 READINESS FAIL: '+ '; '.join(failures))
        raise SystemExit(2)
    print('V111 READINESS PASS: wersja, moduły, bramki, brak znacznika wydania')
