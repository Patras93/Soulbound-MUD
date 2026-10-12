# -*- coding: utf-8 -*-
"""Persistent crash supervisor for Soulbound on Windows (Python standard library only).

The dedicated supervisor remains alive while the game server process may exit.
STOP_Soulbound creates a matching shutdown-request before sending authenticated
STOP; a crashed server exits without such request and is restarted with backoff.
"""
from __future__ import annotations

import ctypes
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import secrets
import sys
import time
import traceback

from windows_launcher_state import process_alive

ROOT = Path(__file__).resolve().parent
LOGS = ROOT / 'logs'
STATE = LOGS / 'soulbound_supervisor.json'
REQUEST = LOGS / 'soulbound_stop_request.json'
LOG = LOGS / 'watchdog.log'


def report(message: str, *, error: bool = False) -> None:
    when = datetime.now().isoformat(timespec='seconds')
    try:
        LOGS.mkdir(parents=True, exist_ok=True)
        with LOG.open('a', encoding='utf-8') as f:
            f.write(f'{when} | {message}\n')
    except OSError:
        pass
    stream = sys.stderr if error else sys.stdout
    if stream is not None:
        print(message, file=stream, flush=True)


def atomic_json(path: Path, value: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_name(path.name + f'.{os.getpid()}.new')
    try:
        temp.write_text(json.dumps(value, ensure_ascii=False), encoding='utf-8')
        os.replace(temp, path)
    finally:
        temp.unlink(missing_ok=True)


def read_json(path: Path) -> dict:
    try:
        result = json.loads(path.read_text(encoding='utf-8'))
        return result if isinstance(result, dict) else {}
    except (OSError, ValueError, UnicodeError):
        return {}


def stop_requested(run_id: str) -> bool:
    return read_json(REQUEST).get('run_id') == run_id


def mutex_handle():
    if os.name != 'nt':
        return None
    from ctypes import wintypes
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.CreateMutexW.argtypes = [ctypes.c_void_p, wintypes.BOOL, wintypes.LPCWSTR]
    kernel.CreateMutexW.restype = wintypes.HANDLE
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL
    digest = hashlib.sha256(str(ROOT).casefold().encode('utf-8')).hexdigest()[:24]
    handle = kernel.CreateMutexW(None, False, 'Local\\SoulboundSupervisor-' + digest)
    if not handle:
        raise OSError(ctypes.get_last_error(), 'Nie mozna utworzyc mutex Windows')
    if ctypes.get_last_error() == 183:  # ERROR_ALREADY_EXISTS
        kernel.CloseHandle(handle)
        return False
    return (kernel, handle)


def supervise(run_server_fn=None, *, pause_fn=time.sleep, now_fn=time.monotonic, max_cycles=None) -> int:
    """Optional injectable clock/run function for non-Windows self-tests."""
    if run_server_fn is None:
        from host_windows import run_server
        run_server_fn = run_server
    mutex = mutex_handle()
    if mutex is False:
        report('WATCHDOG: inny nadzorca dla tego katalogu juz pracuje.')
        return 0
    run_id = secrets.token_hex(24)
    started = now_fn()
    cycles = 0
    consecutive_short = 0
    clean_start = False
    result = 0
    try:
        existing = read_json(STATE)
        if (existing.get('root') == str(ROOT) and existing.get('pid') != os.getpid()
                and process_alive(existing.get('pid'))):
            # Also protected by named mutex, but leave a guard in case mutex unavailable.
            report('WATCHDOG: nadzorca juz uruchomiony.')
            return 0
        atomic_json(STATE, {'pid': os.getpid(), 'root': str(ROOT), 'run_id': run_id, 'started': datetime.now().isoformat(timespec='seconds')})
        report('WATCHDOG START: automatyczne uruchamianie po awarii wlaczone.')
        while True:
            if stop_requested(run_id):
                clean_start = True
                report('WATCHDOG STOP: przerwano start przed nastepna proba.')
                break
            cycles += 1
            attempt = now_fn()
            try:
                code = int(run_server_fn())
            except KeyboardInterrupt:
                report('WATCHDOG: reczne przerwanie nadzorcy.')
                break
            except Exception as exc:
                code = 1
                report(f'WATCHDOG BLAD HOSTA: {type(exc).__name__}: {exc}\n{traceback.format_exc()}', error=True)
            duration = now_fn() - attempt
            if stop_requested(run_id):
                clean_start = True
                report('WATCHDOG STOP: zatwierdzone reczne zamkniecie, bez restartu.')
                break
            if max_cycles is not None and cycles >= max_cycles:
                # Test-only exit, never used by Windows launcher.
                break
            if duration >= 120:
                consecutive_short = 0
            else:
                consecutive_short += 1
            if consecutive_short >= 6:
                delay = 300
            else:
                delay = min(60, 5 * (2 ** min(consecutive_short - 1, 4)))
            report(f'WATCHDOG: serwer zakonczyl prace (kod {code}, czas {duration:.1f} s). Ponowna proba za {delay} s.', error=True)
            # Check stop requests during backoff so a manual shutdown does not wait 5 min.
            end = now_fn() + delay
            while now_fn() < end:
                if stop_requested(run_id):
                    clean_start = True
                    report('WATCHDOG STOP: przerwano oczekiwanie na restart.')
                    break
                pause_fn(min(1, end - now_fn()))
            if clean_start:
                break
        return result
    finally:
        info = read_json(STATE)
        if info.get('run_id') == run_id and info.get('pid') == os.getpid():
            STATE.unlink(missing_ok=True)
        if stop_requested(run_id):
            REQUEST.unlink(missing_ok=True)
        if isinstance(mutex, tuple):
            mutex[0].CloseHandle(mutex[1])
        report('WATCHDOG: nadzorca zakonczyl prace.')


if __name__ == '__main__':
    try:
        raise SystemExit(supervise())
    except Exception as exc:
        report(f'WATCHDOG BLAD KRYTYCZNY: {type(exc).__name__}: {exc}\n{traceback.format_exc()}', error=True)
        raise SystemExit(1)
