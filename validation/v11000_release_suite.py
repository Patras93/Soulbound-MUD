# -*- coding: utf-8 -*-
"""v110: mandatory end-to-end gates, distinct from 60 historical Windows stages."""
from __future__ import annotations
import os,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
GATES=(
 ('MODULY I BRAK STARYCH INSTALATOROW','validation/v11000_release_readiness.py',60),
 ('CZASY 8 PROFESJI I IZOLACJA KATALOGOW','validation/v11000_profession_race_timing_regression.py',30),
 ('NARZEDZIA PROFESJI — SKLEP, POSIADANIE I CENA','validation/v11000_profession_tools_regression.py',60),
 ('STARY FAST PREDEPLOY TYLKO NA PRYWATNEJ BAZIE','validation/v11000_staging_isolation_regression.py',60),
 ('12 KRAIN I 700 QUESTOW','validation/v11000_world_modules_regression.py',90),
 ('8 NAUCZYCIELI I PRAWDZIWE LEARN','validation/v11000_teachers_regression.py',120),
 ('8 ZAWODOW I ROLLBACK','validation/v11000_profession_atomic_regression.py',90),
 ('4 WYDARZENIA I ROLLBACK','validation/v11000_events_regression.py',90),
 ('JEDEN INSTALATOR I TRWALY MANIFEST','validation/v11000_release_install_regression.py',150),
 ('PELNY ROZRUCH SERWERA V110','validation/v11000_server_smoke.py',240),
 ('OLC 15.40-19 I 8 RAS W KREATORZE','validation/v11000_olc_late_integration.py',150),
 ('BEZPIECZNA MIGAWKA SQLITE I METADANE PRAGMA','validation/v11000_snapshot_contract_regression.py',60),
 ('ODZIEDZICZONE SOUL TIER 6000 TYLKO PO AUTORYZACJI','validation/v11000_soul_tier_activation_regression.py',60),
 ('HISTORYCZNE V103 W OSOBNYCH INTERPRETERACH','validation/v11000_legacy_tail_isolation.py',30),
)

def main():
    env=os.environ.copy()
    env['PYTHONDONTWRITEBYTECODE']='1'
    errors=[]
    for i,(title,script,timeout) in enumerate(GATES,1):
        started=time.monotonic()
        try:
            proc=subprocess.run([sys.executable,'-u',str(ROOT/script)],cwd=ROOT,
                 env=env,stdin=subprocess.DEVNULL,capture_output=True,text=True,
                 errors='replace',timeout=timeout)
            details=(proc.stdout+'\n'+proc.stderr).strip()
            if proc.returncode:
                errors.append(title)
                print(f'[{i}/{len(GATES)}] FAIL {title} ({time.monotonic()-started:.1f}s): {details[-800:]}',flush=True)
            else:
                lines=[x for x in proc.stdout.splitlines() if x.strip()]
                print(f'[{i}/{len(GATES)}] PASS {title} ({time.monotonic()-started:.1f}s): '+(lines[-1] if lines else 'OK')[:230],flush=True)
        except (OSError,subprocess.TimeoutExpired) as exc:
            errors.append(title)
            detail=''; detail=(str(exc.stdout or '')+' '+str(exc.stderr or ''))[-500:] if isinstance(exc,subprocess.TimeoutExpired) else str(exc)
            print(f'[{i}/{len(GATES)}] FAIL {title} ({time.monotonic()-started:.1f}s): {type(exc).__name__} {detail}',flush=True)
    if errors:
        print('V110 RELEASE SUITE FAIL: '+', '.join(errors),flush=True)
        return 2
    print(f'V110 RELEASE SUITE PASS: {len(GATES)}/{len(GATES)} obowiązkowych bramek; '
          'pełny Windows PREDEPLOY 60/60 PLUS nadal osobno wymagany.',flush=True)
    return 0

if __name__=='__main__':raise SystemExit(main())
