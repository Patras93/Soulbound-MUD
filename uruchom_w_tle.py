# -*- coding: utf-8 -*-
"""Detached Windows launcher: no long-lived CMD and no forced termination.

Used by the Windows BAT shortcuts. Requires Python 3.12+. No third-party modules.
"""
from __future__ import annotations

from datetime import datetime
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
import traceback

ROOT = Path(__file__).resolve().parent
LOGS = ROOT / 'logs'


def _log(message: str, *, error: bool = False) -> None:
    try:
        LOGS.mkdir(parents=True, exist_ok=True)
        logfile = LOGS / ('bledy.log' if error else 'start.log')
        with logfile.open('a', encoding='utf-8') as out:
            out.write(f'{datetime.now().isoformat(timespec="seconds")} | {message}\n')
    except OSError as exc:
        print(f"Brak zapisu logu startu: {exc}", file=sys.stderr, flush=True)
    print(message, file=sys.stderr if error else sys.stdout, flush=True)


def _already_running() -> bool:
    info_file = LOGS / 'soulbound_control.json'
    if info_file.is_file():
        try:
            metadata = json.loads(info_file.read_text(encoding='utf-8'))
            if Path(str(metadata.get('root', ''))).resolve() == ROOT:
                with socket.create_connection(('127.0.0.1', int(metadata['port'])), timeout=0.4):
                    return True
        except (OSError, ValueError, KeyError, TypeError):  # AUDIT_INTENTIONAL_PASS: stale metadata; port is checked independently
            pass
    # A port already occupied by another program is not safe to replace.
    try:
        with socket.create_connection(('127.0.0.1', 4000), timeout=0.4):
            raise RuntimeError('Port 4000 jest juz zajety. Sprawdz, czy Soulbound juz dziala.')
    except OSError:
        return False


def main() -> int:
    if os.name != 'nt':
        _log('Uruchamianie w tle tym skrotem jest przeznaczone dla Windows.', error=True)
        return 2
    if sys.version_info < (3, 12):
        _log('Wymagany Python 3.12 lub nowszy.', error=True)
        return 2
    if not (ROOT / 'start_windows_bootstrap.py').is_file() or not (ROOT / 'server.py').is_file():
        _log('Brakuje plikow serwera. Rozpakuj kompletna paczke.', error=True)
        return 2
    try:
        if _already_running():
            _log('Soulbound jest juz uruchomiony w tym folderze. Druga kopia nie zostanie wlaczona.')
            return 0
        # Pythonw hides the console. Fallback also has CREATE_NO_WINDOW and DETACHED_PROCESS.
        pythonw = Path(sys.executable).with_name('pythonw.exe')
        interpreter = str(pythonw if pythonw.is_file() else Path(sys.executable))
        flags = getattr(subprocess, 'DETACHED_PROCESS', 0) | getattr(subprocess, 'CREATE_NEW_PROCESS_GROUP', 0) | getattr(subprocess, 'CREATE_NO_WINDOW', 0)
        env = os.environ.copy()
        env.update({'PYTHONUTF8': '1', 'PYTHONIOENCODING': 'utf-8', 'PYTHONUNBUFFERED': '1', 'SOULBOUND_LOG_DIR': str(LOGS)})
        process = subprocess.Popen(
            [interpreter, '-u', str(ROOT / 'start_windows_bootstrap.py')],
            cwd=str(ROOT), env=env, stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
            close_fds=True, creationflags=flags,
        )
        _log(f'Uruchomiono Soulbound w tle bez CMD; PID launchera={process.pid}. Sprawdz logs\\serwer.log.')
        return 0
    except (OSError, ValueError, RuntimeError) as exc:
        _log(f'BLAD URUCHAMIANIA: {type(exc).__name__}: {exc}', error=True)
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
