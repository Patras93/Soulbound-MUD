# -*- coding: utf-8 -*-
"""Authenticated localhost shutdown for Soulbound Windows .bat launcher.

No HTTP endpoint, no public listener, and no process-wide killing.  The token
is generated afresh by host_windows.py and shared through a local control file.
On Railway/Linux without the launcher's environment variables this does nothing.
"""
from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from windows_runtime_state import write_state, remove_matching
import secrets


class LocalControlV1603:
    def __init__(self, server, metadata, token, alternate=None):
        self.server = server
        self.metadata = metadata
        self.token = token
        self.alternate = alternate

    async def close(self):
        self.server.close()
        await self.server.wait_closed()
        try:
            data = json.loads(self.metadata.read_text(encoding='utf-8'))
            if secrets.compare_digest(str(data.get('token', '')), self.token):
                self.metadata.unlink(missing_ok=True)
        except (OSError, ValueError, TypeError):  # AUDIT_INTENTIONAL_PASS: stale file can be safely ignored
            pass
        if self.alternate is not None:
            try:
                remove_matching(self.alternate, 'token', self.token, root=Path(__file__).resolve().parents[1])
            except OSError as exc:
                print(f'Soulbound Windows: nie usunieto pomocniczego sterowania: {exc}', flush=True)


async def start_control_v1603(stop_event):
    token = os.environ.get('SOULBOUND_CONTROL_TOKEN', '')
    raw_filename = os.environ.get('SOULBOUND_CONTROL_FILE', '')
    fallback_filename = os.environ.get('SOULBOUND_CONTROL_FALLBACK_FILE', '')
    if not token or not raw_filename:
        return None
    if len(token) < 32:
        raise RuntimeError('Zbyt krotki token sterowania Soulbound')
    path = Path(raw_filename).resolve()
    path.parent.mkdir(parents=True, exist_ok=True)

    async def handle_client(reader, writer):
        try:
            raw = await asyncio.wait_for(reader.readline(), timeout=4)
            text = raw.decode('ascii', 'replace').strip()
            command, _, supplied = text.partition(' ')
            if (command != 'STOP' or
                    not secrets.compare_digest(supplied, token)):
                writer.write(b'ODMOWA\n')
            else:
                writer.write(b'ZATRZYMYWANIE\n')
                stop_event.set()
            await writer.drain()
        except (OSError, asyncio.TimeoutError, ValueError):  # AUDIT_INTENTIONAL_PASS: invalid control requests are rejected
            pass
        finally:
            writer.close()
            try:
                await writer.wait_closed()
            except OSError:  # AUDIT_INTENTIONAL_PASS: client disconnected after response
                pass

    service = await asyncio.start_server(handle_client, host='127.0.0.1', port=0)
    port = int(service.sockets[0].getsockname()[1])
    metadata = {'version': 1, 'pid': os.getpid(), 'port': port, 'token': token,
                'root': str(Path(__file__).resolve().parents[1])}
    supervisor_pid = os.environ.get('SOULBOUND_SUPERVISOR_PID', '')
    supervisor_run_id = os.environ.get('SOULBOUND_SUPERVISOR_RUN_ID', '')
    if supervisor_pid.isdecimal() and len(supervisor_run_id) >= 32:
        metadata['supervisor_pid'] = int(supervisor_pid)
        metadata['supervisor_run_id'] = supervisor_run_id
    tmp = path.with_suffix(f'.{os.getpid()}.tmp')
    try:
        tmp.write_text(json.dumps(metadata), encoding='utf-8')
        os.replace(tmp, path)
    except OSError:
        service.close()
        await service.wait_closed()
        try:
            tmp.unlink(missing_ok=True)
        except OSError:  # AUDIT_INTENTIONAL_PASS: diagnostic cleanup only
            pass
        raise
    alternate = Path(fallback_filename).resolve() if fallback_filename else None
    if alternate is not None and alternate != path:
        try:
            write_state(alternate, metadata)
        except OSError as exc:
            print(f'Soulbound Windows: pomocniczy plik sterowania niedostepny: {exc}', flush=True)
            alternate = None
    print('Soulbound Windows: bezpieczne zatrzymanie przez STOP_Soulbound.bat jest aktywne.', flush=True)
    return LocalControlV1603(service, path, token, alternate)
