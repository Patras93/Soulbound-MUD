# -*- coding: utf-8 -*-
"""Jedno uruchomienie kontrolne v104, bez dotykania bazy graczy i produkcji.

Nie zastępuje pełnego PREDEPLOY Windows 60/60 PLUS.
"""
from __future__ import annotations

from datetime import datetime
import os
from pathlib import Path
import re
import socket
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parent


def isolated_env(directory):
    # One canonical isolation policy for all v104 audit runners: temp DB,
    # local-only listener, and no inherited Railway/production secrets.
    from validation.v10400_fast_predeploy_isolation import isolated_predeploy_env
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.bind(('127.0.0.1', 0))
        temp_port = probe.getsockname()[1]
    env = isolated_predeploy_env(dict(os.environ), str(directory), temp_port)
    env.update(PYTHONUTF8='1', PYTHONIOENCODING='utf-8',
               PYTHONDONTWRITEBYTECODE='1', PYTHONUNBUFFERED='1')
    return env


def main():
    if sys.version_info < (3, 12):
        print('BLAD: wymagany Python 3.12+.', flush=True)
        return 2
    if (ROOT / 'VERSION').read_text(encoding='utf-8').strip() != '103.00.0':
        print('BLOKADA: ten kandydat nie ma spodziewanego VERSION 103.00.0.', flush=True)
        return 2
    folder = Path(tempfile.mkdtemp(prefix='sb104_tcp_lab_'))
    report = folder / 'WYNIK_ZBIORCZY_V104_PL.txt'
    env = isolated_env(folder)
    stages = (
        ('AST, archiwum i aktualne testy v104', [sys.executable, '-m', 'validation.v10400_release_gate', '--loopback', '--timeout', '180'], 240),
        ('Regresja v104 odizolowana', [sys.executable, '-m', 'validation.v10400_suite_isolated', '--timeout', '60'], 600),
        ('Profesje v600: rollback SQLite 1096', [sys.executable, '-c', 'from validation.v600_professions import run_regression; n=run_regression(); print(n, "PASS"); assert n==1096'], 90),
        ('Imperium v710: rollback SQLite 296', [sys.executable, '-c', 'from validation.v710_quality_polish import run_regression; n=run_regression(); print(n, "PASS"); assert n==296'], 90),
        ('TCP: 2 konta, quest, walka, druzyna', [sys.executable, '-m', 'validation.v10400_tcp_full_journey'], 330),
    )
    lines = [f'Soulbound v104 RC - audyt uruchomiony {datetime.now().isoformat(timespec="seconds")}',
             'Kandydat, tylko testy - NIE WDRAZAC.']
    for name, args, limit in stages:
        print(f'KONTROLA: {name}...', flush=True)
        try:
            result = subprocess.run(args, cwd=ROOT, env=env, stdout=subprocess.PIPE,
                                    stderr=subprocess.STDOUT, text=True,
                                    encoding='utf-8', errors='replace', timeout=limit,
                                    stdin=subprocess.DEVNULL)
            output = result.stdout
            rc = result.returncode
        except subprocess.TimeoutExpired as exc:
            output = (exc.stdout or b'')
            if isinstance(output, bytes):
                output = output.decode('utf-8', 'replace')
            rc = 124
        lines += [f'\n=== {name} ===', f'Wynik: {"PASS" if rc == 0 else "FAIL"}, kod {rc}', output]
        if rc:
            report.write_text('\n'.join(lines), encoding='utf-8')
            print('FAIL. Nic nie zostalo wdrozone. Ostatnie komunikaty:', flush=True)
            print('\n'.join(output.splitlines()[-12:]), flush=True)
            print(f'Log: {report}', flush=True)
            return 1
        print('PASS.', flush=True)
    lines.append('WYNIK: KONTROLA TESTOWA PASS. NADAL BRAK ZGODY NA WDROZENIE.')
    lines.append('Pozostaje pelna migracja BigNumber, atomowosc wszystkich efektow zabicia i Windows PREDEPLOY 60/60 PLUS na kopii rzeczywistej bazy.')
    report.write_text('\n'.join(lines), encoding='utf-8')
    print('WYNIK: testy zbiorcze PASS; to NIE jest finalny PREDEPLOY 60/60 PLUS.', flush=True)
    print(f'Log: {report}', flush=True)
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
