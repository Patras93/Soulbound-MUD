# -*- coding: utf-8 -*-
"""Independent-process v104 regression runner; prevents shared import globals.

Never reads a production database, never starts a remote listener. Every module
from the historical suite has a separate subprocess with a strict timeout.
"""
from __future__ import annotations
import argparse
import os
import socket
from pathlib import Path
import re
import signal
import subprocess
import sys
import tempfile
import time
from validation.v10400_suite_safe import TESTS

ROOT = Path(__file__).resolve().parents[1]
MARK = 'SB104_CHECKS='  # determined from the child stdout, never from guessed counts
CHILD = '''import importlib
obj=importlib.import_module(__import__('sys').argv[1])
n=(getattr(obj, 'run', None) or obj.run_regression)()
n=n[0] if isinstance(n,tuple) else n
assert type(n) is int and n >= 0
print('SB104_CHECKS='+str(n),flush=True)
'''


def safe_env(directory):
    """Force an isolated database, seed, logs and loopback listener per test.

    Historical modules sometimes import a server at module load. Removing
    SOULBOUND_DB alone is unsafe: it re-enables the default ./soulbound.db.
    """
    from validation.v10400_release_isolation_guard import private_tcp_environment
    folder = Path(directory).resolve(strict=True)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(('127.0.0.1', 0))
        port = probe.getsockname()[1]
    if port == 4000:
        raise ValueError('Izolacja regresji: port 4000 zabroniony.')
    env = private_tcp_environment(os.environ, str(folder), port)
    env.update(PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1',
               PYTHONIOENCODING='utf-8', PYTHONUNBUFFERED='1',
               SOULBOUND_TEST_TEMP=str(folder))
    return env


def run(*, seconds_per_module=60, stop_on_failure=False, report_path=None, start_index=1, end_index=None):
    if seconds_per_module < 1:
        raise ValueError('Limit musi być dodatni.')
    if (not TESTS or len(TESTS) != len(set(TESTS))):
        raise ValueError('Lista regresji jest pusta lub zawiera duplikaty.')
    if (type(start_index) is not int or start_index < 1 or start_index > len(TESTS)
        or (end_index is not None and
            (type(end_index) is not int or end_index < start_index or end_index > len(TESTS)))):
        raise ValueError('Zakres regresji jest pusty lub poza lista modulow.')
    total=0
    failures=[]
    report=['SOULBOUND v104 — odizolowana regresja, bez wdrażania.',
            'Każdy moduł w osobnym procesie. Wyniki wyłącznie z wykonanych testów.']
    start=time.monotonic()
    with tempfile.TemporaryDirectory(prefix='sb104_regression_isolated_') as tmp:
        for index,name in enumerate(TESTS, 1):
            if index < start_index or (end_index is not None and index > end_index):
                continue
            folder=Path(tmp)/f'sb104_tcp_lab_{index:02d}'
            folder.mkdir()
            now=time.monotonic()
            try:
                capture=folder/'module.log'
                with capture.open('w', encoding='utf-8', errors='replace') as log:
                    proc=subprocess.Popen(
                        [sys.executable,'-B','-c',CHILD,name], cwd=ROOT,
                        env=safe_env(folder), stdin=subprocess.DEVNULL,
                        stdout=log, stderr=subprocess.STDOUT,
                        start_new_session=(os.name != 'nt'),
                        creationflags=(subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0),
                    )
                    try:
                        returncode=proc.wait(timeout=seconds_per_module)
                    except subprocess.TimeoutExpired:
                        if os.name == 'nt':
                            subprocess.run(['taskkill','/PID',str(proc.pid),'/T','/F'],
                                           stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
                                           timeout=10,check=False)
                        else:
                            try:
                                os.killpg(proc.pid,signal.SIGKILL)
                            except ProcessLookupError:
                                log.write("Proces lokalny juz zakonczony.\n")
                        try:
                            proc.wait(timeout=10)
                        except subprocess.TimeoutExpired:
                            proc.kill()
                            proc.wait(timeout=10)
                        raise
                    finally:
                        # A child auditor may leave a local server after exiting;
                        # do not allow it to outlive the isolated test.
                        if os.name != 'nt':
                            try:
                                os.killpg(proc.pid,signal.SIGKILL)
                            except ProcessLookupError:
                                log.write("Proces lokalny juz zakonczony.\n")
                output=capture.read_text(encoding='utf-8',errors='replace')
                found=re.findall(r'^SB104_CHECKS=(\d+)$',output,re.MULTILINE)
                if returncode or len(found)!=1:
                    raise RuntimeError('kod='+str(returncode)+'; '+output[-800:])
                value=int(found[0])
                total+=value
                line=f'PASS {name}: {value} kontroli ({time.monotonic()-now:.1f} s)'
            except subprocess.TimeoutExpired:
                line=f'TIMEOUT {name}: ponad {seconds_per_module} s — NIEZALICZONE'
                failures.append(name)
            except (OSError,RuntimeError) as error:
                line=f'FAIL {name}: {str(error)[-500:]}'
                failures.append(name)
            print(line,flush=True)
            report.append(line)
            if failures and stop_on_failure:
                break
    report.append(f'Wynik: {total} potwierdzonych kontroli, {len(failures)} błędnych lub nieukończonych modułów.')
    report.append(f'Łączny czas: {time.monotonic()-start:.1f} s.')
    report.append('ZGODA NA WDROZENIE: NIE. Wymagany osobny Windows PREDEPLOY 60/60 i migracja BigNumber.')
    if report_path:
        Path(report_path).write_text('\n'.join(report)+'\n',encoding='utf-8')
    print(report[-3],flush=True)
    if failures:
        raise RuntimeError(f'Regresja NIEZALICZONA: {len(failures)} modułów')
    return total


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--timeout',type=int,default=60)
    ap.add_argument('--stop-on-failure',action='store_true')
    ap.add_argument('--raport')
    ap.add_argument('--start-index',type=int,default=1)
    ap.add_argument('--end-index',type=int)
    args=ap.parse_args()
    try:
        return 0 if run(seconds_per_module=args.timeout,
            stop_on_failure=args.stop_on_failure,report_path=args.raport,
            start_index=args.start_index,end_index=args.end_index)>=0 else 1
    except (RuntimeError,ValueError) as exc:
        print('BRAK PASS: '+str(exc),file=sys.stderr)
        return 1

if __name__ == '__main__':
    raise SystemExit(main())
