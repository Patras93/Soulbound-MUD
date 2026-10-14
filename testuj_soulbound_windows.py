# -*- coding: utf-8 -*-
"""Isolated Windows release gate. Readable by NVDA; returns FAIL on any skipped gate.

Runs the quick, exhaustive and five-player localhost TCP checks in disposable
workspaces. Stage processes have hard deadlines so the batch never hangs forever.
"""
from __future__ import annotations

import datetime as dt
from contextlib import closing
import sqlite3
import os
from pathlib import Path
import platform
import queue
import socket
import subprocess
import sys
import tempfile
import threading
import time
import traceback

ROOT = Path(__file__).resolve().parent
LOG = ROOT / 'logs' / 'TESTY_Soulbound.log'
STAGES = (
    ('SZYBKI PREDEPLOY', 'predeploy_check.py', 480),
    ('PELNY AUDYT', 'predeploy_full.py', 600),
    ('SCENARIUSZE 4.0 AI / OCEAN / PROFESJE', 'validation/v2200_master_depths_ai.py', 180),
    ('MISTRZOWSKIE RECEPTURY / MODULY FLOTY', 'validation/v2201_fleet_mastery.py', 180),
    ('SCENARIUSZE 5.0: AI / 42 RECEPTURY / OCEAN', 'validation/v2300_world_professions_ocean.py', 180),
    ('AUDYT POKRYCIA WZDLUZ I WSZERZ', 'validation/v2302_coverage_contract.py', 180),
    ('ZADANIA — PRAWDZIWE ZDARZENIA I IZOLACJA', 'validation/v2310_event_contract.py', 180),
    ('AUTOGRACZ — MAPA, NPC, SCIEZKI', 'validation/v2320_autonomous_routes.py', 180),
    ('5 KLIENTOW TCP + RESTART', 'validation/v2102_tcp_six_players.py', 900),
)
ULTRA_STAGES = (
    ('KLASY 14 - SKILLE I MISTRZOSTWO',10,120),
    ('RASY 14 - KOMBINACJE',11,120),
    ('PROFESJE - REGULY I NAGRODY',12,120),
    ('SWIAT - LOKACJE, QUESTY I ZDARZENIA',13,180),
    ('LOCHY I WYSOKIE TERENY LVL 100-600',14,120),
    ('BOSSOWIE - REGR. SPRAWNYCH SPAWNOW',15,120),
    ('NAJEMNICY - SKALOWANIE I DAMAGE',16,120),
    ('GOSPODARKA - CENY',17,120),
    ('GOSPODARKA - TRANSAKCJE I REGRESJE',18,120),
    ('BALANS REGIONALNY',19,120),
    ('QUESTY - EXP, FAME, ZLOTO',20,180),
    ('WINDOWS - ZAMYKANIE I BRAK BLOKAD',21,120),
    ('SQLITE WAL - BACKUP, RESTORE, BLAD',22,120),
    ('WATCHDOG - AWARIA, BACKOFF I STOP',23,120),
    ('5 SESJI TCP - PRYWATNY SERWER',24,240),
    ('SQLITE LIVE - KOPIA I MIGRACJA SCHEMATU',25,180),
)
STAGES = STAGES + tuple((name, f'validation/predeploy_ultra_v2327.py --case {number}', timeout)
                         for name, number, timeout in ULTRA_STAGES)
ULTIMATE_STAGES = (
    ('KOMENDY I QUESTY - POKRYCIE REJESTRU', 26, 240),
    ('KOPALNIE - KIERUNKI', 27, 180),
    ('KOPALNIE - TRWALOSC TUNELI', 28, 180),
    ('OBRAZENIA ZYWIOLOWE', 29, 180),
    ('AOE - AI I OPTYMALIZACJA', 30, 180),
    ('PROGRESJA 50+', 31, 240),
    ('BALANS TEMPA GRINDU', 32, 180),
    ('PROFESJE - KRZYWE EXP', 33, 180),
    ('NARZEDZIA - KRZYWE EXP', 34, 180),
    ('ZAMOWIENIA I ODDANIE', 35, 180),
    ('ODRADZANIE MOBOW', 36, 180),
    ('EXP CAP I FAME', 37, 180),
    ('ROWNOLEGLE SWIATY', 38, 180),
    ('FAUNA TERENOW', 39, 180),
    ('POCZATKOWE WALKI', 40, 180),
    ('CONSIDER - REGIONY', 41, 180),
    ('TYTANI', 42, 180),
    ('WINDOWS - KOPANIE', 43, 180),
    ('STAROZYTNE KROLESTWA', 44, 180),
    ('SQLite - NAGLA AWARIA I WAL', 45, 120),
    ('SQLite - 4 PISARZY 400 COMMITOW', 46, 120),
    ('SECURITY - ZLE ZIPY BLOKOWANE', 47, 120),
    ('SECURITY - STARY PASS I PODMIENIONY ZIP BLOKOWANY', 48, 120),
    ('SQLITE - ZACHOWANIE DANYCH POSTACI NA KLONIE', 49, 180),
    ('TCP - 3 FALE PO 5 POLACZEN', 50, 240),
)
STAGES = STAGES + tuple((name, f'validation/predeploy_ultimate_v2328.py --case {number}', timeout)
                         for name, number, timeout in ULTIMATE_STAGES)


ULTIMATE60_STAGES = (
    ('KOMENDY - ROUTING, ALIASY, IZOLACJA',51,240),
    ('LOWCY I NAJEMNICY - ZALICZANIE',52,120),
    ('GŁĘBOKIE LOCHY - PRESJA I BALANS',53,120),
    ('PORTALE DRUZYNY I CHECKPOINTY',54,180),
    ('ZAMOWIENIA - RZECZYWISTE NAGRODY',55,180),
    ('AUTOMATYCZNA EKSPLORACJA - TRWALOSC',56,120),
    ('ZADANIA KLASOWE - CYKL ODNOWY',57,180),
    ('GILDIE - SKALOWANIE I KOSZTY',58,120),
    ('LECZENIE I PRZYWOLANIA W DRUZYNIE',59,120),
    ('SQLITE KLON / MIGRACJA / PLUS 5000+ REGRESJI',60,240),
)
STAGES = STAGES + tuple((name, ('validation/predeploy_plus_gate_v2330.py' if number == 60 else
                          f'validation/predeploy_ultimate60_v2329.py --case {number}'), timeout)
                         for name,number,timeout in ULTIMATE60_STAGES)




def source_db_for_gate():
    """Discover actual existing SQLite for read-only migration verification.

    No test DB, backup, or release-bundled DB is accepted as a substitute for
    a live installation. Explicit paths are authoritative (including errors).
    """
    configured = os.environ.get('SOULBOUND_ULTRA_SOURCE_DB', '').strip()
    inherited = os.environ.get('SOULBOUND_DB', '').strip()
    if configured:
        candidates = [Path(configured)]
    elif inherited:
        candidates = [Path(inherited)]
    else:
        candidates = [ROOT/'soulbound.db']
        # Standard Windows installation; only use it if the file truly exists.
        if os.name == 'nt':
            candidates.append(Path('C:/Soulbound-MUD/soulbound.db'))
    problems = []
    for candidate in candidates:
        try:
            candidate = candidate.expanduser().resolve()
            if not candidate.is_file():
                problems.append(f'nie istnieje: {candidate}')
                continue
            # Open strictly read-only: a malformed file is not an acceptable
            # "production snapshot" and must never generate a false PASS.
            with closing(sqlite3.connect(candidate.as_uri()+'?mode=ro',
                                         uri=True, timeout=10)) as db:
                db.execute('PRAGMA query_only=ON')
                table_names = {r[0] for r in db.execute(
                    "SELECT name FROM sqlite_master WHERE type='table'")}
                if not {'accounts','characters'} <= table_names:
                    problems.append(f'brak kont/postaci w SQLite: {candidate}')
                    continue
            return candidate
        except (OSError, sqlite3.Error) as exc:
            problems.append(f'{candidate}: {type(exc).__name__}: {exc}')
    raise RuntimeError(
        'Brak prawdziwej bazy Soulbound do trzech testow migracji. '
        'Podaj sciezke: TESTUJ_Soulbound.bat "C:\\Soulbound-MUD\\soulbound.db" '
        'lub uruchom PREDEPLOY_NOWEJ_WERSJI.bat z folderu dzialajacej instalacji. '
        'Sprawdzone: ' + ('; '.join(problems) if problems else '(brak)'))


def kill_owned_process(proc):
    """Stop *only* a child started by this runner, including its TCP subprocess."""
    if proc.poll() is not None:
        return
    if os.name == 'nt':
        try:
            subprocess.run(['taskkill', '/PID', str(proc.pid), '/T', '/F'],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                           timeout=8, check=False)
        except (OSError, subprocess.TimeoutExpired):
            proc.kill()
    else:
        import signal
        try:
            os.killpg(proc.pid, signal.SIGTERM)
        except ProcessLookupError:
            return
        except OSError:
            proc.terminate()
    try:
        proc.wait(timeout=8)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=8)


def stage_env(temp):
    # Never inherit production DB, tokens, Railway ports, persistent seed paths.
    env = os.environ.copy()
    for key in ('PORT', 'RAILWAY_TCP_APPLICATION_PORT', 'RAILWAY_VOLUME_MOUNT_PATH',
                'DATABASE_URL', 'SOULBOUND_WORLD_SEED_FILE', 'SOULBOUND_WORLD_SEED',
                'SOULBOUND_ADMIN_ACCOUNTS', 'SOULBOUND_CONTROL_FILE',
                'SOULBOUND_CONTROL_TOKEN', 'SOULBOUND_FULL_AUDIT',
                'SOULBOUND_HISTORICAL_AUDITS', 'SOULBOUND_SMTP_PASSWORD',
                'SOULBOUND_MAIL_PASSWORD', 'SMTP_PASSWORD'):
        env.pop(key, None)
    env.update(PYTHONUTF8='1', PYTHONIOENCODING='utf-8', PYTHONUNBUFFERED='1',
               PYTHONDONTWRITEBYTECODE='1', SOULBOUND_HOST='127.0.0.1',
               SOULBOUND_DB=str(Path(temp) / 'audit.sqlite'),
               SOULBOUND_WORLD_SEED_FILE=str(Path(temp) / 'audit_seed.txt'))
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(('127.0.0.1', 0))
        env['SOULBOUND_PORT'] = str(sock.getsockname()[1])
    return env


def run_stage(path, env, deadline, say):
    proc = None
    try:
        parts = path.split(' ')
        cmd = [sys.executable, '-u', str(ROOT / parts[0]), *parts[1:]]
        flags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
        proc = subprocess.Popen(cmd, cwd=str(ROOT), env=env,
                                creationflags=flags,
                                start_new_session=(os.name != 'nt'),
                                stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, bufsize=1,
                                encoding='utf-8', errors='replace')
        output = queue.Queue()

        def reader():
            try:
                for line in proc.stdout:
                    output.put(line.rstrip('\r\n'))
            except (OSError, ValueError) as exc:
                output.put('BLAD ODCZYTU: '+str(exc))
            finally:
                output.put(None)

        threading.Thread(target=reader, daemon=True).start()
        limit = time.monotonic() + deadline
        eof = False
        while not eof:
            try:
                line = output.get(timeout=.2)
            except queue.Empty:
                if time.monotonic() > limit:
                    say(f'FAIL: Przekroczony limit czasu {deadline} sekund. Proces zakonczony.')
                    kill_owned_process(proc)
                    return 124
                if proc.poll() is not None:
                    # Let the reader consume remaining buffered output.
                    continue
                continue
            if line is None:
                eof = True
            else:
                say(line)
            if time.monotonic() > limit:
                say(f'FAIL: Przekroczony limit czasu {deadline} sekund. Proces zakonczony.')
                kill_owned_process(proc)
                return 124
        return proc.wait(timeout=10)
    finally:
        if proc is not None and proc.poll() is None:
            kill_owned_process(proc)


def main():
    LOG.parent.mkdir(exist_ok=True, parents=True)
    try:
        sys.stdout.reconfigure(errors='replace')
    except (ValueError, AttributeError):  # AUDIT_INTENTIONAL_PASS: non-console hosts may lack reconfigure
        pass
    status = []
    with LOG.open('w', encoding='utf-8', errors='replace', buffering=1) as logfile:
        def say(msg=''):
            print(msg, flush=True)
            logfile.write(msg + '\n')
            logfile.flush()

        say('SOULBOUND v3.31.5 - PREDEPLOY 5 GRACZY ULTIMATE 60 PLUS')
        say('Start: '+dt.datetime.now().astimezone().isoformat(timespec='seconds'))
        say('Python: '+sys.version.splitlines()[0])
        say('System: '+platform.platform())
        say('Folder gry: '+str(ROOT))
        say('Baza prawdziwych graczy: tylko odczyt przez backup SQLite w etapach 25/49/60; zapisy wylacznie w TEMP')
        say('TCP: tylko 127.0.0.1, 5 zalogowanych graczy, 5 TCP i 3 fale po 5 TCP localhost')
        say('PASS wymaga wszystkich 60 etapow (w tym izolowanej kopii realnej bazy).')
        say('-' * 72)
        try:
            source = source_db_for_gate()
            # Keep this setting when a stage overrides SOULBOUND_DB with its
            # private scratch SQLite. Stage migrations read source in mode=ro.
            os.environ['SOULBOUND_ULTRA_SOURCE_DB'] = str(source)
            say('SQLITE SOURCE (wylacznie do odczytu): '+str(source))
            say('Weryfikacja kont/postaci bazy wejsciowej: PASS')
        except (OSError, ValueError, RuntimeError) as exc:
            say('FAIL PRZED STARTEM: '+str(exc))
            say('WYNIK KONCOWY: FAIL - NIE WDRAZAJ, brak wymaganej bazy SQLite')
            say('Koniec: '+dt.datetime.now().astimezone().isoformat(timespec='seconds'))
            return 2
        try:
            for title, filename, timeout in STAGES:
                started = time.monotonic()
                say('\n' + '=' * 72)
                say('START: '+title+' ['+filename+']')
                if not (ROOT / filename.split()[0]).is_file():
                    ret = 2
                    say('FAIL: Brak wymaganego pliku: '+filename)
                else:
                    with tempfile.TemporaryDirectory(prefix='soulbound-predeploy-') as temp:
                        env = stage_env(temp)
                        ret = run_stage(filename, env, timeout, say)
                elapsed = time.monotonic() - started
                outcome = 'PASS' if ret == 0 else 'FAIL'
                say(f'KONIEC: {title} | {outcome} | kod {ret} | czas {elapsed:.1f} s')
                status.append((title, ret))
        except KeyboardInterrupt:
            say('PRZERWANO: CTRL+C, nie wydawaj tej wersji jako PASS')
            status.append(('RECZNIE PRZERWANE', 130))
        except BaseException as exc:
            say('BLAD TESTERA: '+type(exc).__name__+': '+str(exc))
            say(traceback.format_exc().strip())
            status.append(('BLAD TESTERA', 99))
        say('\n' + '=' * 72)
        say('PODSUMOWANIE ETAPOW:')
        for title, ret in status:
            say(('PASS' if ret == 0 else 'FAIL') + ' - ' + title + ' (kod '+str(ret)+')')
        # Check the PLUS sub-suite was *actually executed*, not merely skipped.
        logfile.flush()
        plus_proof = 'PLUS CHECKS PASS' in LOG.read_text(encoding='utf-8',errors='replace')
        good = len(status) == len(STAGES) and all(ret == 0 for _,ret in status) and plus_proof
        if not plus_proof: say('FAIL: Brak dowodu wykonania regresji PLUS')
        say('WYNIK KONCOWY: '+('PASS - WSZYSTKIE 60 ETAPOW PLUS' if good else
                                'FAIL - NIE WDRAZAJ, popraw bledy wskazane wyzej'))
        say('Log do przeslania: '+str(LOG))
        say('Koniec: '+dt.datetime.now().astimezone().isoformat(timespec='seconds'))
        return 0 if good else 1


if __name__ == '__main__':
    raise SystemExit(main())
