# -*- coding: utf-8 -*-
"""Audyt jednej skonsolidowanej paczki v104; nigdy nie wdraza gry.

Kazdy test jest osobnym podprocesem z wlasnym katalogiem tymczasowym,
losowym portem loopback oraz zamknietymi zmiennymi produkcyjnymi.
Zakonczenie testu (takze timeout) zapisuje jawne PASS/FAIL.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import os
import signal
from pathlib import Path
import socket
import subprocess
import sys
import tempfile
import time

from validation.v10400_fast_predeploy_isolation import isolated_predeploy_env

ROOT = Path(__file__).resolve().parents[1]
STAGES = (
    ('v104 unittest (aktualny zestaw)', ('-m', 'validation.v10400_release_gate', '--loopback', '--timeout', '120'), 170),
    ('regresja odizolowana 50 modulow, liczba kontroli z wyniku', ('-m', 'validation.v10400_suite_isolated', '--timeout', '60'), 600),
    ('profesje 1096', ('-c', 'from validation.v600_professions import run_regression; n=run_regression(); print(n, "PASS"); assert n==1096'), 85),
    ('Imperium 296', ('-c', 'from validation.v710_quality_polish import run_regression; n=run_regression(); print(n, "PASS"); assert n==296'), 200),
)
EXTRA = (
    ('prawdziwy TCP dwa konta i SQLite', ('-m', 'validation.v10400_tcp_full_journey'), 310),
    ('historyczny FAST PREDEPLOY', ('predeploy_check.py',), 320),
    ('historyczny FULL PREDEPLOY', ('predeploy_full.py',), 480),
)


def candidate_status():
    version = (ROOT / 'VERSION').read_text(encoding='utf-8').strip()
    try:
        numbers = tuple(int(part) for part in version.split('.'))
    except ValueError as exc:
        raise ValueError('Niepoprawny VERSION; przerwano kontrole RC.') from exc
    if len(numbers) != 3 or numbers < (104, 0, 0):
        raise ValueError('Nieobslugiwana wersja gry; przerwano kontrole RC.')
    return version


def private_environment(base):
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(('127.0.0.1', 0))
        port = sock.getsockname()[1]
    if port == 4000:
        raise ValueError('Zabroniony port produkcyjny 4000.')
    env = isolated_predeploy_env(dict(os.environ), str(base), port)
    env.update(PYTHONUTF8='1', PYTHONIOENCODING='utf-8',
               PYTHONDONTWRITEBYTECODE='1', PYTHONUNBUFFERED='1')
    return env


def execute_stage(name, args, timeout, base):
    env = private_environment(base)
    cmd = [sys.executable, '-u', *args]
    start = time.monotonic()
    # Spool output to disk (no PIPE deadlock / no enormous log in RAM).
    capture = base / 'stage.txt'
    rc = 1
    with capture.open('w', encoding='utf-8', errors='replace') as log:
        proc = None
        try:
            proc = subprocess.Popen(
                cmd, cwd=ROOT, env=env, stdin=subprocess.DEVNULL,
                stdout=log, stderr=subprocess.STDOUT,
                creationflags=(subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0),
                start_new_session=(os.name != 'nt'),
            )
            rc = proc.wait(timeout=timeout)
        except subprocess.TimeoutExpired:
            rc = 124
            if proc is not None:
                # Testy historyczne potrafia uruchomic potomny serwer TCP.
                # Zakoncz CALE drzewo nalezace do testu, nie tylko rodzica.
                if os.name == 'nt':
                    subprocess.run(['taskkill', '/PID', str(proc.pid), '/T', '/F'],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                   timeout=10, check=False)
                else:
                    try:
                        os.killpg(proc.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        log.write("Proces testowy zakonczyl sie przed sygnalem.\n")
                try:
                    proc.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=10)
            log.write('\nTIMEOUT: test nie skonczyl sie w limicie; zakonczono drzewo procesu.\n')
        except OSError as exc:
            log.write(f'BLAD STARTU: {type(exc).__name__}: {exc}\n')
            rc = 125
    output = capture.read_text(encoding='utf-8', errors='replace')
    return rc, output, round(time.monotonic() - start, 1)


def run(full=False, output=None):
    candidate_status()
    lines = [f'SOULBOUND V104: RAPORT JEDNEJ PACZKI {datetime.now().isoformat(timespec="seconds")}',
             'STATUS WYDANIA: RC, NIE WDRAZAC',
             'Nie uruchomiono produkcyjnego serwera ani zapisu do prawdziwej bazy.',
             f'Weryfikowany VERSION: {candidate_status()}; nie wdrazaj bez Windows 60/60 PLUS.',
             'NIEPOTWIERDZONE: produkcyjna migracja BigNumber i Windows ULTIMATE 60/60 PLUS.', '']
    failed = 0
    with tempfile.TemporaryDirectory(prefix='sb104_one_archive_') as tmp:
        for i,(name,args,limit) in enumerate(STAGES + (EXTRA if full else ()), 1):
            stage_dir = Path(tmp) / f'sb104_tcp_lab_{i:02d}'
            stage_dir.mkdir()
            print(f'KONTROLA {i}/{len(STAGES)+(len(EXTRA) if full else 0)}: {name}', flush=True)
            rc, details, seconds = execute_stage(name, args, limit, stage_dir)
            result = 'PASS' if rc == 0 else 'FAIL'
            if rc: failed += 1
            print(f'WYNIK {result}; {seconds} s; kod {rc}', flush=True)
            lines += [f'=== {name} ===', f'{result}; kod {rc}; czas {seconds} sekund',
                      'OSTATNIE KOMUNIKATY:', '\n'.join(details.splitlines()[-50:]), '']
    lines.append(f'ZESTAW TESTOW: {"PASS" if not failed else "FAIL"}, niezaliczone {failed}.')
    if not full:
        lines.append('Testy TCP i pelny historyczny PREDEPLOY byly POMINIETE; wynik nie jest pelnym audytem.')
    lines.append('ZGODA NA WDROZENIE: NIE. Wymaga rzeczywistej bazy (kopia) i Windows 60/60 PLUS; BigNumber w grze nie jest calkowicie przeniesiony.')
    report = Path(output) if output else ROOT / 'RAPORT_OSTATNIEGO_AUDYTU_V104.txt'
    report.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(f'Raport: {report}', flush=True)
    print('WDROZENIE: ZABLOKOWANE - to nie jest produkcyjny ZIP.', flush=True)
    return int(bool(failed))


def main(argv=None):
    parser = argparse.ArgumentParser(description='Jedno uruchomienie testow RC v104 bez wdrazania')
    parser.add_argument('--pelny', action='store_true', help='Dodatkowo TCP i historyczny PREDEPLOY')
    parser.add_argument('--raport', help='Sciezka wyjsciowego raportu PL')
    args = parser.parse_args(argv)
    return run(args.pelny, args.raport)


if __name__ == '__main__':
    raise SystemExit(main())
