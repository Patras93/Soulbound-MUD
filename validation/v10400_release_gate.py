# -*- coding: utf-8 -*-
"""Jedna, powtarzalna bramka v104 bez uruchamiania produkcyjnego serwera.

Domyslnie sprawdza kod, czystosc paczki i testy unittest v104.
Nie modyfikuje VERSION, zadnych baz postaci ani Admin Live. Testy pracuja
na pamieciowych lub tymczasowych bazach. Testy gniazd loopback sa osobne.
"""
from __future__ import annotations

import argparse
import ast
import os
import socket
import tempfile
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]


def check_files():
    from validation.v10400_release_isolation_guard import forbidden_release_paths
    relative = sorted(p.relative_to(ROOT).as_posix() for p in ROOT.rglob('*') if p.is_file())
    invalid = forbidden_release_paths(relative)
    if invalid:
        raise AssertionError('Niebezpieczne pliki w paczce: ' + ', '.join(invalid[:25]))
    if len(relative) != len(set(relative)):
        raise AssertionError('Powtorzone sciezki w paczce.')
    py_count = 0
    for name in relative:
        if name.endswith('.py'):
            ast.parse((ROOT / name).read_text(encoding='utf-8-sig'), filename=name)
            py_count += 1
    return py_count, len(relative)


def run_tests(*, loopback=False, timeout=120):
    files = sorted((ROOT/'validation').glob('test_v10400_*.py'))
    if not loopback:
        files = [p for p in files if 'tcp_wait_single_socket' not in p.name]
    modules = ['validation.'+p.stem for p in files]
    # Tests import historical game modules; never let them use a live SQLite
    # database, world seed or the production listener at port 4000.
    from validation.v10400_release_isolation_guard import private_tcp_environment
    with tempfile.TemporaryDirectory(prefix='sb104_tcp_lab_units_') as temp:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.bind(('127.0.0.1', 0))
            port = probe.getsockname()[1]
        if port == 4000:
            raise AssertionError('Port produkcyjny 4000 wylosowany w bramce.')
        env = private_tcp_environment(os.environ, temp, port)
        env.update(PYTHONDONTWRITEBYTECODE='1', PYTHONUTF8='1',
                   PYTHONIOENCODING='utf-8', PYTHONUNBUFFERED='1')
        proc = subprocess.run([sys.executable, '-m', 'unittest', '-q', *modules],
                              cwd=str(ROOT), env=env, text=True, encoding='utf-8',
                              errors='replace', stdout=subprocess.PIPE,
                              stderr=subprocess.STDOUT, timeout=timeout,
                              stdin=subprocess.DEVNULL)
    if proc.returncode:
        raise AssertionError('Testy v104 FAIL:\n'+proc.stdout[-3500:])
    return len(modules), proc.stdout.strip()


def run(*, loopback=False, timeout=120):
    start=time.monotonic()
    py, files = check_files()
    modules, outcome = run_tests(loopback=loopback, timeout=timeout)
    version = (ROOT/'VERSION').read_text(encoding='utf-8').strip()
    if version not in ('104.00.0', '104.00.1', '104.00.2', '104.00.3', '105.00.0', '106.00.0', '107.00.0'):
        raise AssertionError('Nieoczekiwany VERSION. Nie zmieniaj wersji bez PREDEPLOY.')
    print(f'AST: {py} plikow Python PASS')
    print(f'Paczka: {files} plikow, brak baz, cache, logow i sekretow PASS')
    print(f'Unittest: {modules} modulow: {outcome}')
    print(f'Czas kontroli: {time.monotonic()-start:.1f}s')
    print('STATUS: BRAMKA OFFLINE PASS. BRAK ZGODY NA WDROZENIE.')
    print('BLOKADY: pelna migracja BigNumber, atomowosc wszystkich efektow zabicia, Windows PREDEPLOY.')
    print('TCP realne jest osobnym testem: SPRAWDZ_V104_DWA_KONTA_WALKA_TCP.bat')


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description='Soulbound v104: bezpieczna kontrola offline')
    parser.add_argument('--loopback', action='store_true', help='Dodaj unit testy lokalnych gniazd TCP')
    parser.add_argument('--timeout', type=int, default=120)
    options=parser.parse_args()
    try:
        run(loopback=options.loopback, timeout=options.timeout)
    except (AssertionError, SyntaxError, subprocess.TimeoutExpired, OSError) as e:
        print('STATUS: FAIL, NIE WDRAZAC:', e, file=sys.stderr)
        sys.exit(1)
