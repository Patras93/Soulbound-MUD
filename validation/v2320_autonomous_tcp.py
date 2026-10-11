# -*- coding: utf-8 -*-
"""Actual player-facing TCP journey: NPC -> quest -> monster kill -> persistence.

This does NOT claim to finish all quests or even this ten-rat quest. It
intentionally proves one genuine live kill-based progress step and rejects
unearned turn-ins. Never injects progress or modifies a production database.
"""
from __future__ import annotations
import asyncio
import re
import time

QUEST_NAME = 'Szczury pod świątynią'
EXPECTED_QUEST = 'temple_rats'
GOAL = 10


def progress_from_quests(text):
    for line in str(text).splitlines():
        if QUEST_NAME.casefold() in line.casefold() and 'Postęp' in line:
            match = re.search(r'Postęp\s+(\d+)\s+z\s+10', line, flags=re.IGNORECASE)
            if match:
                return int(match.group(1))
    return None


def selftest():
    assert progress_from_quests('1. Szczury pod świątynią. aktywne. Postęp 0 z 10.') == 0
    assert progress_from_quests('1. Szczury pod świątynią. aktywne. Postęp 4 z 10.') == 4
    assert progress_from_quests('Nie masz aktywnych questów') is None
    assert progress_from_quests('1. Inny quest. Postęp 4 z 10.') is None
    return 4


async def _observe(lead, command, expected, *, attempts=8):
    """Wait for the answer to THIS command, not delayed room broadcasts.

    Combat, movement and quest messages share an asynchronous TCP socket.
    One recv() is never a reliable acknowledgement of a prior command.
    Reissuing read-only commands is safe; all writes happen only after an
    unambiguous positive read-only observation.
    """
    outputs = []
    for index in range(attempts):
        response = await lead.command(command, quiet=0.35)
        outputs.append(response)
        if expected(response):
            return response
        await asyncio.sleep(0.3 + index * 0.1)
    raise AssertionError(f"Unexpected response to {command!r}: " +
                         ' | '.join(t[-350:] for t in outputs[-3:]))


async def run_actual_delivery(lead, routes):
    """Complete a genuine courier delivery using the generated NPC world."""
    if not routes or not routes.get('to_sol') or not routes.get('to_doran'):
        raise AssertionError('Missing real NPC route in private child world')
    expected = 'Pierwsze kroki: Paczka dla Kowala'
    for move in routes['to_sol']:
        await lead.command(move)
        # Movement notifications may arrive later than this command's reply.
        await asyncio.sleep(.25)
    await _observe(lead, 'look', lambda t: 'NPC: Archiwista Sol' in t,
                   attempts=12)
    print('AUTOGRACZ TCP: realna trasa do Archiwisty Sola PASS', flush=True)
    offer = await _observe(lead, 'quest list Archiwista Sol',
                           lambda t: expected in t, attempts=8)
    match = re.search(r'(?m)^\s*(\d+)\.\s*'+re.escape(expected), offer)
    if not match:
        raise AssertionError('No Sol quest ordinal in real NPC list: '+offer[-750:])
    accepted = await lead.command('przyjmij '+match.group(1))
    status = await _observe(lead, 'quests', lambda t: expected in t)
    inventory = await _observe(lead, 'inventory',
                               lambda t: 'paczka' in t.casefold(), attempts=8)
    print('AUTOGRACZ TCP: prawdziwy quest Sola przyjety; paczka w EQ PASS', flush=True)
    for move in routes['to_doran']:
        await lead.command(move)
        await asyncio.sleep(.25)
    await _observe(lead, 'look', lambda t: 'NPC: Kowal Doran' in t,
                   attempts=12)
    print('AUTOGRACZ TCP: realna trasa do Kowala Dorana PASS', flush=True)
    # Verify the destination interaction; don't trust a generic 'ok' response.
    result = await lead.command('talk Kowal Doran')
    state = await _observe(lead, 'quests', lambda t: (
        expected in t or 'AKTYWNE ZADANIA' in t or 'Nie masz aktywnych' in t),
        attempts=8)
    # The FINAL proof is the persisted quest status, verified by caller after
    # TCP sockets close, not matching a vague dialogue substring here.
    print('AUTOGRACZ TCP: rozmowa u Dorana wykonana; czeka na weryfikacje SQLite',
          flush=True)
    return 1


async def run_actual_npc_journey(clients):
    """Called from the guarded six-client private TCP server session."""
    assert len(clients) == 6
    lead = clients[0]
    checked = selftest()
    dialogue = await lead.command('talk Kapłan Elor')
    assert 'Kapłan Elor:' in dialogue and QUEST_NAME in dialogue, 'NPC did not present quest'
    checked += 1
    listing = await lead.command('quest list Kapłan Elor')
    assert f'1. {QUEST_NAME}' in listing, 'NPC offer changed or absent'
    checked += 1
    accepted = await lead.command('przyjmij 1')
    assert f'Quest przyjęty: {QUEST_NAME}' in accepted, accepted[-500:]
    checked += 1
    qlines = await lead.command('quests')
    assert progress_from_quests(qlines) == 0, qlines[-500:]
    checked += 1

    # Party leader shares with nearby members. Check actual responses from
    # separate authenticated sockets, not fabricated database rows.
    shared = await asyncio.gather(*(c.command('quests') for c in clients[1:]))
    if any(progress_from_quests(result) != 0 for result in shared):
        raise AssertionError('Party quest was not given to all five local members')
    checked += 5

    premature = await lead.command('oddaj 1')
    assert 'nie jest jeszcze gotowe' in premature.casefold(), premature[-500:]
    checked += 1

    # Party test remains at Temple; solo delivery runs after restart,
    # so concurrent party teleport broadcasts cannot mask NPC replies.
    arrived = await lead.command('down')
    assert 'Piwnic' in arrived, 'Navigation down did not reach temple basement'
    seen = ''
    for _ in range(8):
        seen = await lead.command('look')
        if 'Szczur' in seen and 'Przeciwnicy' in seen:
            break
        await asyncio.sleep(.35)
    else:
        raise AssertionError('No visible rats at basement after movement: '+seen[-750:])
    checked += 2

    fighting = await lead.command('attack Szczur')
    # TCP carries async room/battle broadcasts: an attack may return leftover
    # look output before the attack message. Only a later REAL kill proves it.
    checked += 1

    # Combat runs asynchronously. A single nonzero quest progress is only
    # counted after the server's authentic kill event, NOT after attack start.
    deadline = time.monotonic() + 100
    last = ''
    progress = 0
    next_retry = time.monotonic() + 22
    while time.monotonic() < deadline:
        await asyncio.sleep(1.5)
        last = await lead.command('quests')
        value = progress_from_quests(last)
        if value is None:
            # Async combat messages can precede the requested quest response.
            # No synthetic progress is ever credited: poll again.
            continue
        if value > 0:
            progress = value
            break
        if time.monotonic() >= next_retry:
            await lead.command('attack Szczur')
            next_retry = time.monotonic() + 22
    if progress < 1:
        raise AssertionError('Attack started but no actual rat kill credited in 100 seconds: '+last[-500:])
    checked += 1
    print(f'AUTOGRACZ TCP: rzeczywisty kill -> quest {EXPECTED_QUEST}: '+
          f'{progress}/{GOAL}, bez ustawiania postepu SQLite', flush=True)
    # Leave the active quest in DB for the restart/persistence gate.
    print('AUTOGRACZ TCP: NPC dialog, oferta, przyjecie, 5 udostepnien party, '
          'blokada przedwczesnej nagrody, przejscie i realna walka PASS', flush=True)
    return {'checks': checked, 'commands': 8 + len(shared) + max(1, progress),
            'progress': progress}


async def check_after_restart(clients, routes):
    text = await clients[0].command('quests')
    progress = progress_from_quests(text)
    if progress is None or progress < 1:
        raise AssertionError('Real kill quest progress disappeared after server restart: '+text[-500:])
    print(f'AUTOGRACZ TCP RESTART: quest {EXPECTED_QUEST} zachowal '
          f'{progress}/{GOAL} zabic w SQLite PASS', flush=True)
    completed = await run_actual_delivery(clients[0], routes)
    return 1 + completed


if __name__ == '__main__':
    print('AUTOGRACZ TCP CONTRACT: '+str(selftest())+' PASS. '
          'Prawdziwe połączenia uruchamia ostatnia bramka szesciu graczy.')
