# -*- coding: utf-8 -*-
"""v111: wszystkie bramki kalendarza w jednym przebiegu, bez osobnych BAT."""
from __future__ import annotations
import subprocess,sys,os,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
GATES=(
 'validation/v11100_predeploy_self_containment.py',
 'validation/v11100_release_readiness.py',
 'validation/v11100_release_activation_regression.py',
 'validation/v11100_holiday_contract.py',
 'validation/v11100_holiday_schedule_regression.py',
 'validation/v11100_holiday_events_regression.py',
 'validation/v11100_holiday_challenges_regression.py',
 'validation/v11100_holiday_combat_regression.py',
 'validation/v11100_holiday_prizes_regression.py',
 'validation/v11100_server_smoke.py',
)
def main():
    env=os.environ.copy()
    env['PYTHONDONTWRITEBYTECODE']='1'
    env['PYTHONPATH']=str(ROOT)
    fails=[]
    for i,rel in enumerate(GATES,1):
        started=time.monotonic()
        try:
            r=subprocess.run([sys.executable,'-u',str(ROOT/rel)],cwd=ROOT,
                stdin=subprocess.DEVNULL,env=env,capture_output=True,text=True,timeout=240)
            report=(r.stdout+'\n'+r.stderr).strip()
            if r.returncode:fails.append(rel)
            print(f'V111 {i}/{len(GATES)} '+('FAIL' if r.returncode else 'PASS')+' '+rel+
                  f' ({time.monotonic()-started:.1f}s) '+report[-320:],flush=True)
        except (OSError,subprocess.TimeoutExpired) as exc:
            fails.append(rel)
            print(f'V111 {i}/{len(GATES)} FAIL {rel}: {exc}',flush=True)
    if fails:
        print('V111 RELEASE SUITE FAIL: '+', '.join(fails),flush=True)
        return 2
    print(f'V111 RELEASE SUITE PASS: {len(GATES)}/{len(GATES)}; pełny Windows 60/60 nadal obowiązkowy',flush=True)
    return 0
if __name__=='__main__':raise SystemExit(main())
