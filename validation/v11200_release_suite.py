# -*- coding: utf-8 -*-
"""Current source gates. Legacy save upgrades additionally require Windows 60/60 PLUS."""
from __future__ import annotations
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
GATES=(
    'validation/current_explicit_runtime_regression.py',
    'validation/current_install_regression.py',
    'validation/test_native_session_dependencies.py',
    'validation/test_runtime_transport.py',
    'validation/current_activation_independence_regression.py',
    'validation/test_runtime_explicit_mixins.py',
    'validation/current_only_server_smoke.py',
    'validation/v11200_release_readiness.py',
    'validation/v11200_runtime_independence_regression.py',
    'validation/v11200_release_activation_regression.py',
    'validation/v11200_installer_independence_regression.py',
    'validation/v11200_parallel_schedule_regression.py',
    'validation/v11200_eternal_glory_ownership_regression.py',
    'validation/v11200_catalog_gift_ownership_regression.py',
    'validation/v11200_fresh_install_regression.py',
    'validation/v11200_realms_ownership_regression.py',
    'validation/v11200_horizons_ownership_regression.py',
    'validation/v11200_profession_ownership_regression.py',
    'validation/v11200_big_batch_ownership_regression.py',
    'validation/v11200_broken_v111_recovery_regression.py',
    'validation/v11100_holiday_contract.py',
    'validation/v11100_holiday_schedule_regression.py',
    'validation/v11100_holiday_events_regression.py',
    'validation/v11100_holiday_challenges_regression.py',
    'validation/v11100_holiday_combat_regression.py',
    'validation/v11100_holiday_prizes_regression.py',
    'validation/v11100_server_smoke.py',
)

def run_gate(index, rel, env):
    """Independent process and regular-file output: no inherited stdout pipe hang."""
    import tempfile
    started=time.monotonic()
    with tempfile.TemporaryFile(mode='w+t',encoding='utf-8') as log:
        try:
            proc=subprocess.run(
                [sys.executable,'-u',str(ROOT/rel)],cwd=ROOT,env=env,
                stdout=log,stderr=subprocess.STDOUT,stdin=subprocess.DEVNULL,
                timeout=240,check=False)
            code=proc.returncode
        except subprocess.TimeoutExpired:
            code=124
        except OSError as exc:
            code=126
            print(repr(exc),file=log)
        log.flush()
        log.seek(0)
        output=log.read()[-420:].strip()
    return index,rel,code,time.monotonic()-started,output


def main():
    from concurrent.futures import ThreadPoolExecutor, as_completed
    # Main Windows 60 PLUS runs separately; these isolated v112 gates are also
    # concurrent, without skipping any inherited historical behavior checks.
    workers=min(4,max(1,(os.cpu_count() or 2)//4))
    env=dict(os.environ,PYTHONDONTWRITEBYTECODE='1',PYTHONPATH=str(ROOT),
             PYTHONUTF8='1',PYTHONIOENCODING='utf-8')
    print(f'V112 SUITE: {len(GATES)} obowiązkowych bramek, {workers} procesy równolegle',flush=True)
    results={}
    # Start real TCP startup first; it must not queue behind short audits.
    priority=[len(GATES)-1,*range(len(GATES)-1)]
    with ThreadPoolExecutor(max_workers=workers) as pool:
        futures={pool.submit(run_gate,i,GATES[i],env):i for i in priority}
        for future in as_completed(futures):
            index=futures[future]
            try:
                row=future.result()
            except BaseException as exc:
                row=(index,GATES[index],99,0.0,type(exc).__name__+': '+str(exc))
            results[index]=row
            _,rel,code,elapsed,excerpt=row
            print(f'V112 {index+1}/{len(GATES)} '+('PASS' if code==0 else 'FAIL')+
                  f' {rel} ({elapsed:.1f}s) '+excerpt,flush=True)
    failures=[row for row in results.values() if row[2]!=0]
    if len(results)!=len(GATES):
        failures.append((-1,'niekompletne wyniki',99,0.0,''))
    if failures:
        print('V112 RELEASE SUITE FAIL: '+', '.join(x[1] for x in failures),flush=True)
        return 2
    print(f'V112 RELEASE SUITE PASS {len(GATES)}/{len(GATES)}; '
          'legacy-save upgrades require their separate Windows 60/60 PLUS',flush=True)
    return 0

if __name__=='__main__':raise SystemExit(main())
