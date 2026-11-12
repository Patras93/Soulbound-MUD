# -*- coding: utf-8 -*-
"""Version-neutral EXTRA gate for all future releases.

Only tests independent of historical v112 activation or release IDs belong here.
The 60 PLUS stages, EQ compatibility and six-player TCP are separately mandatory.
"""
from __future__ import annotations
import os
import subprocess
import sys
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT=Path(__file__).resolve().parents[1]
GATES=(
    'validation/current_explicit_runtime_regression.py',
    'validation/test_native_session_dependencies.py',
    'validation/test_runtime_transport.py',
    'validation/test_runtime_explicit_mixins.py',
    'validation/current_universal_update_regression.py',
    'validation/current_universal_end_to_end_regression.py',
    'validation/current_full_backup_regression.py',
    'validation/current_real_backup_contract_regression.py',
    'validation/current_universal_activation_regression.py',
    'validation/current_unlimited_characters_regression.py',
    'validation/current_version_neutral_game_regression.py',
    'validation/current_activation_independence_regression.py',
    'validation/current_staging_environment_regression.py',
    'validation/current_tool_tier_after_800_regression.py',
    'validation/current_only_server_smoke.py',
)

def run(rel):
    import tempfile
    with tempfile.TemporaryFile(mode='w+t',encoding='utf-8') as log:
        try:
            code=subprocess.run([sys.executable,'-u',str(ROOT/rel)],cwd=ROOT,
                                env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',
                                         PYTHONUTF8='1',PYTHONIOENCODING='utf-8'),
                                stdin=subprocess.DEVNULL,stdout=log,
                                stderr=subprocess.STDOUT,timeout=240).returncode
        except subprocess.TimeoutExpired:code=124
        except OSError as exc:
            code=126;print(repr(exc),file=log)
        log.seek(0)
        return rel,code,log.read()[-400:].strip()

def main():
    outcomes={}
    # Memory-heavy boot/catalog tests should not compete with the many fast
    # SQLite and import checks: on small Windows hosts that overlap can cause
    # nondeterministic timeouts. Keep lightweight gates parallel, run real
    # runtime boot once on its own after they have finished.
    slow = 'validation/current_only_server_smoke.py'
    with ThreadPoolExecutor(max_workers=3) as pool:
        pending={pool.submit(run,rel):rel for rel in GATES if rel != slow}
        for future in as_completed(pending):
            rel,code,output=future.result()
            outcomes[rel]=code
            print(('PASS' if code==0 else 'FAIL')+' '+rel+' '+output,flush=True)
    if all(code == 0 for code in outcomes.values()):
        print('START ' + slow + ' (bez równoległych obciążeń)', flush=True)
        rel,code,output=run(slow)
        outcomes[rel]=code
        print(('PASS' if code==0 else 'FAIL')+' '+rel+' '+output,flush=True)
    else:
        outcomes[slow]=125
        print('SKIP '+slow+' (wcześniejsza bramka nie przeszła)',flush=True)
    passed=sum(code==0 for code in outcomes.values())
    print('UNIVERSAL RELEASE SAFETY: '+str(passed)+'/'+str(len(GATES))+' PASS',flush=True)
    return 0 if passed==len(GATES) else 2

if __name__=='__main__':raise SystemExit(main())
