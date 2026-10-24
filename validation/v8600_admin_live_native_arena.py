# -*- coding: utf-8 -*-
"""Actual admin live full-engine arena lifecycle / isolated SQLite regression."""
from __future__ import annotations
import asyncio
from contextlib import closing
import os
import subprocess
from pathlib import Path
import socket
import sqlite3
import sys
import tempfile
import time
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]


def _free_port():
    with socket.socket() as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]


async def _run():
    import systems.admin_live_native_arena_v8600 as ctl
    from arena_real_izolowana import _process_alive, _run_until_stopped
    checks = 0
    from core.bootstrap_economy_professions import VERSION as code_version
    assert code_version == (ROOT / 'VERSION').read_text(encoding='utf-8').strip() and int(code_version.split('.')[0]) >= 86
    checks += 1
    with subprocess.Popen([sys.executable, '-c', 'import time;time.sleep(10)']) as probe:
        try:
            assert _process_alive(probe.pid)
        finally:
            probe.terminate()
            probe.wait(timeout=10)
    checks += 1
    assert not _process_alive(-1)
    checks += 1
    # Supervisor exits cleanly when an owner process has already disappeared.
    old_owner = subprocess.Popen([sys.executable, '-c', 'pass'])
    old_pid = old_owner.pid
    old_owner.wait(timeout=10)
    dummy = subprocess.Popen([sys.executable, '-c', 'import time;time.sleep(20)'])
    try:
        assert _run_until_stopped(dummy, parent_pid=old_pid) == 0
        checks += 1
    finally:
        dummy.terminate()
        dummy.wait(timeout=10)
    # Explicit stop marker requests shutdown without hard-killing the wrapper.
    with tempfile.TemporaryDirectory(prefix='sb86-signal-') as signal_dir:
        marker = Path(signal_dir)/'stop'
        marker.write_text('STOP',encoding='ascii')
        dummy = subprocess.Popen([sys.executable, '-c', 'import time;time.sleep(20)'])
        try:
            assert _run_until_stopped(dummy, stop_file=marker) == 0
            checks += 1
        finally:
            dummy.terminate()
            dummy.wait(timeout=10)
    class FakeSession:
        def __init__(self, server, admin):
            self.server, self.admin, self.messages = server, admin, []
        def is_admin(self):
            return self.admin
        async def send(self, msg):
            self.messages.append(msg)
    with tempfile.TemporaryDirectory(prefix='sb86-owner-') as temp:
        dbpath = Path(temp) / 'source.db'
        with closing(sqlite3.connect(dbpath)) as conn:
            conn.execute('create table example (x integer)')
            conn.execute('insert into example values (456)')
            conn.commit()
        owner = sqlite3.connect(dbpath)
        try:
            server=SimpleNamespace(db=SimpleNamespace(conn=owner))
            visitor = FakeSession(server, False)
            assert await ctl.dispatch_v8600(visitor,'arena','real start POTWIERDZAM')
            assert visitor.messages[-1] == 'Nieznana komenda.'
            assert ctl._current is None
            checks += 1
            user=FakeSession(server,True)
            assert await ctl.dispatch_v8600(user,'pomoc','44')
            assert 'arena real start' in user.messages[-1]
            checks += 1
            assert await ctl.dispatch_v8600(user,'arena','real start NIE')
            assert 'POTWIERDZAM' in user.messages[-1]
            assert ctl._current is None
            checks += 1
            assert 'WYLACZONA' in ctl.arena_status()
            checks += 1
            port = _free_port()
            try:
                response=ctl.arena_start(server,source=ROOT,port=port)
                assert 'START' in response
                checks += 1
                try:
                    ctl.arena_start(server,source=ROOT,port=port)
                    raise AssertionError('Second arena was allowed')
                except ValueError as ex:
                    assert 'juz uruchomiona' in str(ex)
                checks += 1
                deadline=time.monotonic()+90
                while time.monotonic() < deadline:
                    status=ctl.arena_status()
                    if 'DZIALA' in status:
                        break
                    if 'zakonczona' in status:
                        raise AssertionError('Lab exited before ready: '+status)
                    await asyncio.sleep(.35)
                else:
                    raise TimeoutError('Real arena did not start')
                assert f'127.0.0.1:{port}' in status
                checks += 1
                assert (ctl._current is not None and ctl._current['process'].poll() is None)
                checks += 1
                # Confirm SQLite source contents persist unchanged across cloning.
                assert owner.execute('select x from example').fetchall()==[(456,)]
                checks += 1
            finally:
                if ctl._current is not None:
                    stop_path=ctl._current['stop']
                    log=ctl._current['log']
                    p=ctl._current['process']
                    control=ctl._current['control']
                    result=await ctl.arena_stop()
                    if ctl._current is not None:
                        p.terminate()
                        p.wait(timeout=20)
                        raise AssertionError('Lab did not stop gracefully: '+result)
                    assert 'usuniete' in result
                    checks += 1
                    assert not control.exists()
                    checks += 1
                    assert p.poll() is not None
                    checks += 1
                    assert 'WYLACZONA' in ctl.arena_status()
                    checks += 1
            assert owner.execute('select x from example').fetchall()==[(456,)]
            checks += 1
        finally:
            owner.close()
    print(f'ADMIN LIVE NATIVE UOSS v86: {checks} PASS',flush=True)
    return checks

if __name__=='__main__':
    asyncio.run(_run())
