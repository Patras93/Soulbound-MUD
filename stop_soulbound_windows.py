# -*- coding: utf-8 -*-
"""Gracefully stop only this Soulbound instance and its crash supervisor.

Never kills processes. Any missing/ambiguous control information must block a
release, rather than claiming that the game has stopped.
"""
from __future__ import annotations

import os
from pathlib import Path
import socket
import sys
import time

from windows_launcher_state import process_alive
from windows_runtime_state import fallback_dir, read_state, write_state, remove_matching

ROOT = Path(__file__).resolve().parent
LOGS = ROOT / 'logs'
ALT = fallback_dir(ROOT)
CONTROL_FILES = (LOGS / 'soulbound_control.json', ALT / 'soulbound_control.json',
                 Path(os.getenv('TEMP') or os.getenv('TMP') or ROOT) / 'Soulbound-MUD-logs' / 'soulbound_control.json')
SUPERVISOR_FILES = (LOGS / 'soulbound_supervisor.json', ALT / 'soulbound_supervisor.json')
LAUNCHER_FILES = (LOGS / 'soulbound_launcher.json', ALT / 'soulbound_launcher.json')
REQUEST_FILES = (LOGS / 'soulbound_stop_request.json', ALT / 'soulbound_stop_request.json')


def same_root(data: dict) -> bool:
    try:
        return bool(data.get('root')) and Path(str(data['root'])).resolve() == ROOT
    except (OSError, TypeError, ValueError):
        return False


def live_state(files, *, supervisor: bool) -> dict:
    for path in files:
        entry = read_state(path)
        if not same_root(entry):
            continue
        try:
            pid = int(entry['pid'])
        except (TypeError, ValueError, KeyError):
            continue
        if pid <= 0 or not process_alive(pid):
            continue
        if supervisor and (not isinstance(entry.get('run_id'), str) or len(entry['run_id']) < 32):
            continue
        return entry
    return {}


def port_open(port: int = 4000) -> bool:
    try:
        with socket.create_connection(('127.0.0.1', port), timeout=.3):
            return True
    except OSError:
        return False


def request_watchdog(watch: dict) -> None:
    if not watch:
        return
    request = {'run_id': watch['run_id'], 'root': str(ROOT)}
    # The primary request is mandatory: failing to inform the watchdog is fatal.
    write_state(REQUEST_FILES[0], request)
    try:
        write_state(REQUEST_FILES[1], request)
    except OSError:
        print('UWAGA: pomocniczy znacznik STOP niedostepny; glowny zostal zapisany.', flush=True)


def undo_watchdog_request(watch: dict) -> None:
    if watch:
        for request in REQUEST_FILES:
            try:
                remove_matching(request, 'run_id', watch['run_id'], root=ROOT)
            except OSError:
                print('UWAGA: nie mozna cofnac niepotwierdzonego STOP. Sprawdz logs\\watchdog.log.', flush=True)


def controls() -> list[tuple[Path, dict]]:
    found = []
    for path in CONTROL_FILES:
        data = read_state(path)
        if not same_root(data):
            continue
        try:
            port = int(data['port'])
            token = str(data['token'])
            pid = int(data['pid'])
        except (ValueError, TypeError, KeyError):
            continue
        if 1024 <= port <= 65535 and len(token) >= 32 and pid > 0 and process_alive(pid):
            found.append((path, data))
    return found


def authenticated_stop(found: list[tuple[Path, dict]], launcher: dict) -> dict:
    for path, metadata in found:
        # An active host can authenticate the exact child PID. Reject stale
        # metadata; if the host state itself is missing, the token still protects us.
        if launcher and int(launcher.get('server_pid', -1)) != int(metadata['pid']):
            continue
        try:
            with socket.create_connection(('127.0.0.1', int(metadata['port'])), timeout=4) as connection:
                connection.settimeout(6)
                connection.sendall(('STOP ' + str(metadata['token']) + '\n').encode('ascii'))
                reply = connection.recv(128).decode('ascii', 'replace').strip()
            if reply == 'ZATRZYMYWANIE':
                return metadata
        except (OSError, ValueError, UnicodeError):
            continue
    return {}


def finished(control: dict, launcher: dict, watch: dict) -> bool:
    for pidinfo in (launcher, watch, control):
        if pidinfo and process_alive(int(pidinfo['pid'])):
            return False
    # The original port must be free; never overwrite game code while another
    # process occupies it, even if the old Soulbound already exited.
    return not port_open(4000)


def main() -> int:
    watch = {}
    requested = False
    try:
        watch = live_state(SUPERVISOR_FILES, supervisor=True)
        launcher = live_state(LAUNCHER_FILES, supervisor=False)
        found = controls()
        if not watch:
            # Server-generated, token-protected metadata also carries the
            # watchdog identity; usable when BOTH watchdog JSON copies vanish.
            for _, meta in found:
                try:
                    candidate_pid = int(meta['supervisor_pid'])
                    candidate_id = str(meta['supervisor_run_id'])
                    if candidate_pid > 0 and len(candidate_id) >= 32 and process_alive(candidate_pid):
                        watch = {'pid': candidate_pid, 'run_id': candidate_id, 'root': str(ROOT)}
                        break
                except (KeyError, TypeError, ValueError):
                    continue
        if not found:
            if launcher or port_open():
                print('BLAD: port 4000 lub launcher dziala, lecz brak uwierzytelnionego sterowania Soulbound. Nie zamykam procesu.', flush=True)
                return 3
            if watch:
                request_watchdog(watch)
                requested = True
                print('Soulbound: nadzorca oczekuje na restart; prosze o jego zatrzymanie.', flush=True)
            else:
                print('Soulbound: serwer i nadzorca juz sa zatrzymane.', flush=True)
                return 0
        else:
            if watch:
                request_watchdog(watch)  # BEFORE STOP prevents crash auto-restart.
                requested = True
            accepted = authenticated_stop(found, launcher)
            if not accepted:
                if requested:
                    undo_watchdog_request(watch)
                print('BLAD: brak potwierdzenia STOP od serwera. Nie zatrzymano go na sile.', flush=True)
                return 3
            print('Soulbound: serwer potwierdzil STOP. Czekam na zapis SQLite i zamkniecie nadzorcy.', flush=True)
        started = time.monotonic()
        while time.monotonic() - started < 135:
            if finished(accepted if found else {}, launcher, watch):
                print('Soulbound: potwierdzono zakonczenie serwera, launchera i nadzorcy. Port 4000 wolny.', flush=True)
                return 0
            time.sleep(.25)
        print('BLAD: nie wszystkie procesy zakonczyly prace lub port 4000 pozostaje zajety. Aktualizacja zabroniona.', flush=True)
        return 4
    except (OSError, ValueError, TypeError, UnicodeError, KeyError) as exc:
        # The watchdog request remains in place after a failure unless the
        # socket explicitly rejected STOP; never risk an unplanned restart.
        print(f'BLAD: STOP nie powiodl sie: {type(exc).__name__}: {exc}. Nie wymuszono zabicia procesu.', flush=True)
        return 3


if __name__ == '__main__':
    sys.exit(main())
