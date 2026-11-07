# -*- coding: utf-8 -*-
"""One conservative v106 audit on a separate copy (NEVER deploy).

Includes full local regression, static raid/reward gates, a real NPC payout,
all 30 natural raid stage kills with one synthetic character, five real-party
sizes on raid 26 and a full six-player final raid.  No player DB or accounts.

These checks are necessary, NOT a substitute for Windows PREDEPLOY or
historical real-EQ migration on a copy provided by the server owner.
"""
from __future__ import annotations
import argparse
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))


def run():
    ap=argparse.ArgumentParser(description='Jedna pełna kontrola Soulbound v106; NIE WDRAŻAĆ')
    ap.add_argument('--szybko',action='store_true',help='Jedna reprezentatywna walka TCP zamiast matrycy 30 bossów')
    ap.add_argument('--bez-tcp',action='store_true',help='Bez TCP: tylko kontrola offline (wynik NIE jest pełny)')
    args=ap.parse_args()
    from validation.v10600_one_package_gate import guard_root
    guard_root()
    # The environment for every child explicitly forgets production secrets.
    clean=os.environ.copy()
    for k in ('SOULBOUND_DB','DATABASE_URL','PORT','SOULBOUND_PORT','SOULBOUND_HOST',
              'RAILWAY_TCP_APPLICATION_PORT','RAILWAY_VOLUME_MOUNT_PATH',
              'SOULBOUND_WORLD_SEED_FILE','SOULBOUND_ADMIN_ACCOUNTS',
              'SOULBOUND_CONTROL_FILE','SOULBOUND_CONTROL_TOKEN',
              'SOULBOUND_SMTP_PASSWORD','SOULBOUND_MAIL_PASSWORD'):
        clean.pop(k,None)
    for k in tuple(clean):
        if k.startswith('SOULBOUND_V106_'):
            clean.pop(k,None)
    clean.update(PYTHONPATH=str(ROOT),PYTHONUTF8='1',PYTHONDONTWRITEBYTECODE='1')
    steps=[]
    core=['--bez-tcp'] if args.bez_tcp else []
    steps.append(('01 PODSTAWOWA REGRESJA V105/V106',
                  ['validation.v10600_one_package_gate',*core],2400))
    steps.append(('02 TRZYDZIEŚCI ZADAŃ I NAGRÓD',
                  ['validation.v10600_one_package_gate','--tylko-nagrody-rajd'],240))
    steps.append(('03 TRASY RAJDÓW DO NPC',
                  ['validation.v10600_rajdy_powrot_do_npc'],180))
    if not args.bez_tcp:
        steps.append(('04 ODBIÓR NAGRÓD U NPC (PRAWDZIWE TCP)',
                      ['validation.v10600_one_package_gate','--tylko-odbior-rajd-tcp'],300))
        if args.szybko:
            fights=[(26,1,1,True),(35,3,6,True)]
        else:
            # Every genuine raid boss (10 raids x 3 stages), never just its
            # authored template.  Six-person final and sizes 2..6 are extra.
            fights=[(raid,stage,1,True)
                    for raid in range(26,36) for stage in (1,2,3)]
            fights += [(26,1,n,True) for n in range(2,7)]
            fights += [(35,3,6,True)]
        for raid,stage,n,claim in fights:
            title=f'RAJD {raid} ETAP {stage}: {n} GRACZY, NATURALNY TCP'
            cmd=['validation.v10600_tcp_raid_natural_six',
                 '--pelna-walka','--gracze',str(n),'--rajd',str(raid),'--etap',str(stage)]
            if claim:cmd.append('--oddaj-po-walce')
            steps.append((title,cmd,420))
    print('SOULBOUND v106 — JEDNA ZBIORCZA KONTROLA. PRODUKCJA NIETKNIĘTA.',flush=True)
    for i,(title,cmd,timeout) in enumerate(steps,1):
        print(f'\n[{i}/{len(steps)}] {title}',flush=True)
        started=time.monotonic()
        try:
            env=clean.copy()
            if cmd[0]=='validation.v10600_rajdy_powrot_do_npc':
                env['SOULBOUND_V106_STAGING']='1'
            p=subprocess.run([sys.executable,'-B','-m',*cmd],cwd=ROOT,
                env=env,stdin=subprocess.DEVNULL,timeout=timeout,check=False)
        except subprocess.TimeoutExpired:
            print(f'FAIL: przekroczony limit testu: {title}. NIE WDRAŻAĆ.',flush=True)
            return 1
        if p.returncode:
            print(f'FAIL ({p.returncode}): {title}. NIE WDRAŻAĆ.',flush=True)
            return 1
        print(f'PASS: {title}.',flush=True)
    print(f'\n{len(steps)}/{len(steps)} KONTROLI LOKALNYCH PASS.',flush=True)
    print('UWAGA: to nadal NIE JEST Windows PREDEPLOY ani test na realnym EQ.')
    print('STATUS: KOD ROBOCZY, NIE WDRAŻAĆ.')
    return 0

if __name__=='__main__':
    raise SystemExit(run())
