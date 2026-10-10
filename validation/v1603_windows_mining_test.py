# -*- coding: utf-8 -*-
"""v1.60.3: regression test for direction auto-start and local STOP protocol."""
from __future__ import annotations
import asyncio
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import types
from unittest.mock import patch

# This legacy module expects injected runtime globals. The handler uses only
# normalize_lookup_text from it, so isolate the parser dependency in this test.
_stub = types.ModuleType('network.protocol_gameplay_utils')
_stub.normalize_lookup_text = lambda value: str(value or '').strip().lower()
sys.modules.setdefault('network.protocol_gameplay_utils', _stub)
from player.session_mixins.command_special_handlers import SessionCommandSpecialHandlersMixin
from systems.windows_control_v1603 import start_control_v1603


class MiningTestSession(SessionCommandSpecialHandlersMixin):
    def __init__(self):
        self.messages = []
        self.calls = []
    async def send(self, text):
        self.messages.append(text)
    async def set_auto_mining(self, enabled, direction=None):
        self.calls.append((enabled, direction))


async def mining_test():
    s = MiningTestSession()
    await s.command_mine_v0490('kierunki')
    assert s.mine_direction_choice_v1603
    assert '1 północ' in s.messages[-1] and 'kop off' in s.messages[-1]
    assert not s.calls
    for cmd, expected in (
        ('1', 'north'), ('10', 'down'), ('7', 'southeast'),
        ('północ', 'north'), ('góra', 'up'), ('prawo', 'east'),
        ('on południe', 'south'), ('wybierz 8', 'southwest'),
        ('kopanienieznane', None),
    ):
        before = len(s.calls)
        await s.command_mine_v0490(cmd)
        if expected is None:
            assert len(s.calls) == before
        else:
            assert s.calls[-1] == (True, expected), (cmd, s.calls)
    await s.command_mine_v0490('off')
    assert s.calls[-1] == (False, None)
    return len(s.calls)


async def stop_test():
    root = Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix='soulbound_stop_') as tmp:
        secret = 'abcd0123456789'*5
        file = Path(tmp)/'soulbound_control.json'
        event = asyncio.Event()
        with patch.dict(os.environ, {'SOULBOUND_CONTROL_TOKEN': secret,
                                      'SOULBOUND_CONTROL_FILE': str(file)}):
            service = await start_control_v1603(event)
        assert service and file.exists()
        data = json.loads(file.read_text(encoding='utf-8'))
        assert data['token'] == secret and data['port'] > 0
        rd,wr = await asyncio.open_connection('127.0.0.1', data['port'])
        wr.write(b'STOP incorrect-token\n')
        await wr.drain()
        assert await rd.readline() == b'ODMOWA\n'
        wr.close(); await wr.wait_closed()
        assert not event.is_set(), 'unauthenticated stop must fail'
        rd,wr = await asyncio.open_connection('127.0.0.1', data['port'])
        wr.write(('STOP '+secret+'\n').encode())
        await wr.drain()
        assert await rd.readline() == b'ZATRZYMYWANIE\n'
        wr.close(); await wr.wait_closed()
        assert event.is_set()
        await service.close()
        assert not file.exists(), 'stop removes control file'
    return 4


async def main():
    n = await mining_test()
    c = await stop_test()
    print(f'WINDOWS STOP / AUTO MINE v1.60.3: {n} komend, {c} kontrole protokolu PASS')


if __name__ == '__main__':
    asyncio.run(main())
