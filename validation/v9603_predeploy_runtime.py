# -*- coding: utf-8 -*-
"""v96.00.3 contract: all 60 gates remain required, with realistic deadlines."""
from pathlib import Path
import ast
from validation.release_contracts import release_valid, parse_version

def run():
    from core.bootstrap_economy_professions import VERSION
    from testuj_soulbound_windows import STAGES
    root = Path(__file__).resolve().parents[1]
    count = 0
    def ck(condition, message):
        nonlocal count
        assert condition, message
        count += 1
    ck(VERSION == (root / 'VERSION').read_text(encoding='utf-8').strip(), 'version file')
    ck(release_valid(VERSION, '87.00.0'), 'minimum v87')
    ck(not release_valid('87.00.0', VERSION), 'historical mismatch rejected')
    ck(not release_valid(VERSION, str(parse_version(VERSION)[0]+1)+'.00.0'), 'future minimum rejected')
    ck(parse_version(VERSION) >= (96, 0, 3), 'release minimum number')
    ck(len(STAGES) == 60, '60 stages required')
    ck(len({name for name, *_ in STAGES}) == 60, 'unique stages')
    ck(STAGES[0][1] == 'predeploy_check.py', 'fast audit required')
    ck(STAGES[1][1] == 'predeploy_full.py', 'full audit required')
    ck(STAGES[0][2] >= 1000, 'fast audit deadline')
    ck(STAGES[1][2] >= 1200, 'full audit deadline')
    ck(STAGES[-1][1] == 'validation/predeploy_plus_gate_v2330.py', 'plus gate required')
    ck(all(x[2] > 0 for x in STAGES), 'positive deadlines')
    source = (root/'validation/v8700_admin_live_large_update.py').read_text(encoding='utf-8')
    ck("release_valid(VERSION, '87.00.0')" in source, 'v87 validates release')
    ck("VERSION in ('87.00.0'" not in source, 'v87 no fixed release list')
    for filename in ('testuj_soulbound_windows.py','predeploy_check.py','predeploy_full.py','server.py'):
        ast.parse((root/filename).read_text(encoding='utf-8'),filename=filename)
        count += 1
    return count

if __name__ == '__main__':
    print(f'V96.00.3 PREDEPLOY: {run()} checks PASS')
