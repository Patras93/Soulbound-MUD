# -*- coding: utf-8 -*-
"""Six-player extension of the tested historical autonomous TCP quest journey.

Keep the five-player historical journey unchanged for older regression gates.
The v110 gate independently proves that the sixth *authenticated* member
receives the real shared quest as well, without touching the production DB.
"""
from __future__ import annotations
import asyncio
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from validation.v2320_autonomous_tcp import (
    run_actual_npc_journey, progress_from_quests, EXPECTED_QUEST,
)


async def run_six_player_journey(clients):
    if len(clients) != 6:
        raise AssertionError('The v110 journey requires six real TCP players')
    result = await run_actual_npc_journey(clients[:5])
    last = ''
    for _ in range(8):
        last = await clients[5].command('quests', quiet=.35)
        status = progress_from_quests(last)
        if status is not None and status >= 0:
            print('TCP PLAYER 6: real party quest shared through TCP PASS', flush=True)
            return {**result, 'checks': result['checks'] + 1}
        await asyncio.sleep(.25)
    raise AssertionError('The sixth player did not receive party quest '+EXPECTED_QUEST+': '+last[-500:])


def run_contract():
    """Reject incomplete parties; 6th must have a real quest response."""
    from unittest.mock import patch
    class FakeClient:
        def __init__(self, response):
            self.response = response
            self.commands = []
        async def command(self, command, quiet=.35):
            self.commands.append(command)
            return self.response

    async def fake_historical(clients):
        assert len(clients) == 5
        return {'checks': 20, 'progress': 1}

    async def check():
        valid=[FakeClient('') for _ in range(5)]
        sixth=FakeClient('1. Szczury pod świątynią. aktywne. Postęp 0 z 10.')
        with patch(__name__+'.run_actual_npc_journey',fake_historical):
            answer=await run_six_player_journey(valid+[sixth])
            assert answer['checks']==21 and sixth.commands==['quests']
            try:
                await run_six_player_journey(valid)
            except AssertionError as exc:
                assert 'six real TCP players' in str(exc), str(exc)
            else:
                raise AssertionError('Five clients incorrectly accepted by six-player gate')
            invalid=FakeClient('Nie masz aktywnych questów')
            try:
                await run_six_player_journey(valid+[invalid])
            except AssertionError as exc:
                assert 'sixth player' in str(exc)
            else:
                raise AssertionError('Missing shared quest not detected')
        return 3
    return asyncio.run(check())


if __name__ == '__main__':
    count = run_contract()
    print(f'V110 SIX-PLAYER JOURNEY CONTRACT: {count}/{count} PASS', flush=True)
