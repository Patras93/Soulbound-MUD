# -*- coding: utf-8 -*-
"""v2.32.13: real loopback stop protocol + supervisor fail-closed regressions.

Only temporary state files and a mock event are used. Production processes,
production SQLite, and the real port 4000 are never touched.
"""
from __future__ import annotations
import asyncio
import json
import os
from pathlib import Path
import tempfile
from unittest.mock import patch

import stop_soulbound_windows as stop
from systems.windows_control_v1603 import start_control_v1603
from windows_runtime_state import read_state, write_state

ROOT = Path(__file__).resolve().parents[1]


async def test_authenticated_fallback(tmp):
    control1 = tmp / 'primary' / 'soulbound_control.json'
    control2 = tmp / 'secondary' / 'soulbound_control.json'
    supervisor1 = tmp / 'primary' / 'soulbound_supervisor.json'
    supervisor2 = tmp / 'secondary' / 'soulbound_supervisor.json'
    launcher1 = tmp / 'primary' / 'soulbound_launcher.json'
    launcher2 = tmp / 'secondary' / 'soulbound_launcher.json'
    request1 = tmp / 'primary' / 'soulbound_stop_request.json'
    request2 = tmp / 'secondary' / 'soulbound_stop_request.json'
    token = '9e' * 32
    event = asyncio.Event()
    flags = {'server': True, 'host': True, 'watchdog': True}
    rid = 'a1' * 24
    with patch.dict(os.environ, {'SOULBOUND_CONTROL_TOKEN': token,
                                 'SOULBOUND_CONTROL_FILE': str(control1),
                                 'SOULBOUND_CONTROL_FALLBACK_FILE': str(control2),
                                 'SOULBOUND_SUPERVISOR_PID': '99113',
                                 'SOULBOUND_SUPERVISOR_RUN_ID': rid}):
        service = await start_control_v1603(event)
    assert control1.exists() and control2.exists(), 'two independent control records required'
    metadata = read_state(control2)
    assert metadata['token'] == token
    # Simulate a maintenance program deleting the primary JSON record.
    control1.unlink()
    assert metadata['supervisor_pid'] == 99113
    # Both watchdog records are missing: STOP must recover its identity from
    # the server-signed control metadata, not silently skip watchdog shutdown.
    write_state(launcher2, {'pid': 99114, 'root': str(ROOT), 'server_pid': metadata['pid']})

    original = (stop.CONTROL_FILES, stop.SUPERVISOR_FILES, stop.LAUNCHER_FILES, stop.REQUEST_FILES)
    stop.CONTROL_FILES = (control1, control2)
    stop.SUPERVISOR_FILES = (supervisor1, supervisor2)
    stop.LAUNCHER_FILES = (launcher1, launcher2)
    stop.REQUEST_FILES = (request1, request2)

    def fake_alive(pid):
        if pid == metadata['pid']:
            return flags['server']
        if pid == 99114:
            return flags['host']
        if pid == 99113:
            return flags['watchdog']
        return False

    def fake_port(port=4000):
        return flags['server']

    async def complete_stop():
        await asyncio.wait_for(event.wait(), 6)
        assert read_state(request1).get('run_id') == rid, 'request must precede server shutdown'
        await service.close()
        flags.update(server=False, host=False, watchdog=False)

    try:
        with patch.object(stop, 'process_alive', side_effect=fake_alive), patch.object(stop, 'port_open', side_effect=fake_port):
            closer = asyncio.create_task(complete_stop())
            status = await asyncio.wait_for(asyncio.to_thread(stop.main), 8)
            await closer
        assert status == 0, status
        assert not control2.exists(), 'fallback control token cleanup'
    finally:
        stop.CONTROL_FILES, stop.SUPERVISOR_FILES, stop.LAUNCHER_FILES, stop.REQUEST_FILES = original
    return 8


def test_reject_missing_control(tmp):
    c = tmp / 'missing.json'
    w = tmp / 'watch.json'
    req = tmp / 'request.json'
    write_state(w, {'pid': 99203, 'root': str(ROOT), 'run_id': 'bb' * 24})
    original = (stop.CONTROL_FILES, stop.SUPERVISOR_FILES, stop.LAUNCHER_FILES, stop.REQUEST_FILES)
    stop.CONTROL_FILES = (c,)
    stop.SUPERVISOR_FILES = (w,)
    stop.LAUNCHER_FILES = (tmp / 'missing-launcher.json',)
    stop.REQUEST_FILES = (req, tmp / 'backup-request.json')
    try:
        with patch.object(stop, 'process_alive', side_effect=lambda pid: pid == 99203), patch.object(stop, 'port_open', return_value=True):
            status = stop.main()
        assert status == 3, 'must reject untrusted occupied port'
        assert not req.exists(), 'must not signal watchdog without authentication'
    finally:
        stop.CONTROL_FILES, stop.SUPERVISOR_FILES, stop.LAUNCHER_FILES, stop.REQUEST_FILES = original
    return 3


def test_watchdog_backoff_only(tmp):
    w = tmp / 'watch.json'
    req = tmp / 'request.json'
    write_state(w, {'pid': 99213, 'root': str(ROOT), 'run_id': 'ab' * 24})
    running = [True]
    original = (stop.CONTROL_FILES, stop.SUPERVISOR_FILES, stop.LAUNCHER_FILES, stop.REQUEST_FILES)
    stop.CONTROL_FILES = (tmp / 'missing-control.json',)
    stop.SUPERVISOR_FILES = (w,)
    stop.LAUNCHER_FILES = (tmp / 'missing-launcher.json',)
    stop.REQUEST_FILES = (req, tmp / 'secondary-request.json')
    real_sleep = stop.time.sleep

    def fake_sleep(n):
        assert read_state(req).get('run_id') == 'ab' * 24
        running[0] = False
        real_sleep(.002)

    try:
        with patch.object(stop, 'process_alive', side_effect=lambda pid: running[0] if pid == 99213 else False), patch.object(stop, 'port_open', return_value=False), patch.object(stop.time, 'sleep', side_effect=fake_sleep):
            status = stop.main()
        assert status == 0
    finally:
        stop.CONTROL_FILES, stop.SUPERVISOR_FILES, stop.LAUNCHER_FILES, stop.REQUEST_FILES = original
    return 3


def test_bat_exit_codes():
    bat = (ROOT / 'STOP_Soulbound.bat').read_text(encoding='utf-8').lower()
    assert 'exit /b !errorlevel!' in bat, 'STOP must propagate the Python return code'
    assert 'enabledelayedexpansion' in bat
    assert 'taskkill' not in bat and 'stop-process' not in bat
    update = (ROOT / 'aktualizuj_soulbound.py').read_text(encoding='utf-8')
    assert 'stop_soulbound_windows.py' in update and 'timeout=180' in update
    assert "filename in ('soulbound_control.json', 'soulbound_supervisor.json', 'soulbound_launcher.json')" in update
    return 5


def run_regression():
    with tempfile.TemporaryDirectory(prefix='sb-stop-23213-') as td:
        p = Path(td)
        n = asyncio.run(test_authenticated_fallback(p))
        n += test_reject_missing_control(p)
        n += test_watchdog_backoff_only(p)
        n += test_bat_exit_codes()
    return n


if __name__ == '__main__':
    print(f'STOP + WATCHDOG v2.32.13: {run_regression()} checks PASS', flush=True)
