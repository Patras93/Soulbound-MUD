# -*- coding: utf-8 -*-
"""Isolated Windows release gate. Readable by NVDA; returns FAIL on any skipped gate.

Runs the quick, exhaustive and six-player localhost TCP checks in disposable
workspaces. Stage processes have hard deadlines so the batch never hangs forever.
"""
from __future__ import annotations

import datetime as dt
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
    ('6 KLIENTOW TCP + RESTART', 'validation/v2102_tcp_six_players.py', 900),
)


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
        cmd = [sys.executable, '-u', str(ROOT / path)]
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

        say('SOULBOUND v2.32.4 - RAILWAY DOCKER QUALITY GATE')
        say('Start: '+dt.datetime.now().astimezone().isoformat(timespec='seconds'))
        say('Python: '+sys.version.splitlines()[0])
        say('System: '+platform.platform())
        say('Folder gry: '+str(ROOT))
        say('Baza prawdziwych graczy: NIE UZYWANA, tylko tymczasowe SQLite')
        say('TCP: tylko 127.0.0.1, maksymalnie 6 graczy testowych')
        say('PASS wymaga wykonania wszystkich dziewieciu etapow; sam FAST to za malo.')
        say('-' * 72)
        try:
            for title, filename, timeout in STAGES:
                started = time.monotonic()
                say('\n' + '=' * 72)
                say('START: '+title+' ['+filename+']')
                if not (ROOT / filename).is_file():
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
        good = len(status) == len(STAGES) and all(ret == 0 for _,ret in status)
        say('WYNIK KONCOWY: '+('PASS - WSZYSTKIE 9 ETAPOW' if good else
                                'FAIL - NIE WDRAZAJ, popraw bledy wskazane wyzej'))
        say('Log do przeslania: '+str(LOG))
        say('Koniec: '+dt.datetime.now().astimezone().isoformat(timespec='seconds'))
        return 0 if good else 1


if __name__ == '__main__':
    raise SystemExit(main())
