# -*- coding: utf-8 -*-
"""Full native v87 fresh instance E2E: TCP login banner, zero production DB read."""
from __future__ import annotations
import asyncio
from pathlib import Path
import socket
import time
from systems import admin_live_native_arena_v8600 as ctl

class NoProductionDB:
    @property
    def db(self):
        raise AssertionError('Fresh arena attempted to read production DB')

def free_port():
    with socket.socket() as s:
        s.bind(('127.0.0.1',0))
        return s.getsockname()[1]

def receive_login_banner(sock, expected, *, budget=4.0):
    """Read past telnet IAC negotiation and split TCP packets to exact banner.

    Returns bytes actually received; a missing/incorrect version never passes.
    """
    deadline = time.monotonic() + budget
    payload = bytearray()
    while time.monotonic() < deadline and len(payload) < 65536:
        sock.settimeout(min(0.4, max(0.01, deadline - time.monotonic())))
        try:
            chunk = sock.recv(4096)
        except socket.timeout:
            continue
        if not chunk:
            break
        payload.extend(chunk)
        if expected in payload:
            break
    return bytes(payload)

async def run():
    count=0
    def check(value):
        nonlocal count
        assert value
        count+=1
    port=free_port()
    check('WYLACZONA' in ctl.arena_status())
    message=ctl.arena_start(NoProductionDB(),fresh=True,port=port)
    check('pusta baza' in message)
    control=ctl._current['control'];proc=ctl._current['process']
    try:
        try:
            ctl.arena_start(NoProductionDB(),fresh=True,port=port)
        except ValueError as error:
            check('juz uruchomiona' in str(error))
        else:
            raise AssertionError('Double native arena start accepted')
        from core.bootstrap_economy_professions import VERSION
        expected_banner=('SOULBOUND ONLINE v'+VERSION).encode('ascii')
        payload=b''
        for i in range(125):
            status=ctl.arena_status()
            if 'zakonczona' in status:
                raise AssertionError('Lab exited: '+status)
            try:
                with socket.create_connection(('127.0.0.1',port),timeout=.6) as sock:
                    payload=receive_login_banner(sock, expected_banner, budget=2.5)
                    if expected_banner in payload:
                        break
            except (OSError,TimeoutError):  # AUDIT_INTENTIONAL_PASS: connection retries until isolated server is ready
                pass
            await asyncio.sleep(.32)
        check(expected_banner in payload)
        check(b'LOGIN' in payload.upper() or b'SOULBOUND ONLINE' in payload)
        check('127.0.0.1:' in ctl.arena_status())
    finally:
        result=await ctl.arena_stop()
        check('usuniete' in result)
    check(not control.exists() and proc.poll() is not None)
    check('WYLACZONA' in ctl.arena_status())
    print(f'ARENA UOSS FRESH TCP: {count} PASS',flush=True)

if __name__=='__main__':
    asyncio.run(run())
