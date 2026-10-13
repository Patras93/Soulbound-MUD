# -*- coding: utf-8 -*-
"""Accessible, read-only diagnostic: port 4000 + supervisor PID + logs."""
from __future__ import annotations
import json
import os
from pathlib import Path
import socket
import sys
from windows_launcher_state import process_alive
from windows_runtime_state import fallback_dir, read_state
ROOT = Path(__file__).resolve().parent
LOGS = ROOT / 'logs'

def status():
    try:
        info = read_state(LOGS / 'soulbound_supervisor.json')
        if not info:
            info = read_state(fallback_dir(ROOT) / 'soulbound_supervisor.json')
        pid = int(info['pid'])
        alive = info.get('root') == str(ROOT) and process_alive(pid)
    except (OSError, KeyError, ValueError, TypeError):
        pid, alive = 0, False
    print('NADZORCA:', 'DZIALA' if alive else 'NIE DZIALA', '| PID:', pid)
    try:
        with socket.create_connection(('127.0.0.1', 4000), timeout=1):
            port = True
    except OSError:
        port = False
    print('PORT TCP 4000:', 'OTWARTY' if port else 'ZAMKNIETY')
    print('LOG:', LOGS / 'watchdog.log')
    print('BAZA:', ROOT / 'soulbound.db')
    print('UWAGA: otwarty port oznacza polaczenie TCP, a nie pelny test logowania.')
    return 0
if __name__=='__main__':
    sys.exit(status())
