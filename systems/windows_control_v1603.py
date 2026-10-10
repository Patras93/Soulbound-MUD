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
import secrets


class LocalControlV1603:
    def __init__(self, server, metadata, token):
        self.server = server
        self.metadata = metadata
        self.token = token

    async def close(self):
        self.server.close()
        await self.server.wait_closed()
        try:
            data = json.loads(self.metadata.read_text(encoding='utf-8'))
            if secrets.compare_digest(str(data.get('token', '')), self.token):
                self.metadata.unlink(missing_ok=True)
        except (OSError, ValueError, TypeError):  # AUDIT_INTENTIONAL_PASS: stale file can be safely ignored
            pass


async def start_control_v1603(stop_event):
    token = os.environ.get('SOULBOUND_CONTROL_TOKEN', '')
    raw_filename = os.environ.get('SOULBOUND_CONTROL_FILE', '')
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
    print('Soulbound Windows: bezpieczne zatrzymanie przez STOP_Soulbound.bat jest aktywne.', flush=True)
    return LocalControlV1603(service, path, token)
