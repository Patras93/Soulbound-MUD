# -*- coding: utf-8 -*-
"""Regional profession goals v115: credit only completed native actions.

No new tools or recipes. Existing gathering events and crafting quest callbacks
are the only authorized entry points. Items/EP/XP belong to their native systems.
No audio module is imported or required.
"""
from __future__ import annotations
from uuid import uuid4
from core.classes_skills import ROOMS
from .exploration_objective_bridge import _valid_sector
from .objective_progress import record_event
from .objective_rewards import settle_kill_objectives

SUPPORTED = frozenset(('collect_resource', 'craft_item'))


def record_v115_profession_action(session, objective, quantity, *, event_id=None):
    """Credit a confirmed resource/craft event in an authored v115 room.

    Returns (new_events, quests, achievements, silver). Never gives resources,
    tool EXP or EP; those remain owned by the established profession systems.
    """
    if objective not in SUPPORTED:
        raise ValueError('Nieznany cel profesji v115')
    if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity <= 0:
        raise ValueError('Nieprawidłowa liczba zdobytych przedmiotów')
    account_id = getattr(session, 'account_id', None)
    character = getattr(session, 'character', None)
    if type(account_id) is not int or account_id <= 0 or character is None or int(getattr(character,'account_id',-1)) != account_id:
        raise ValueError('Nieprawidłowa postać dla nagrody profesji')
    room_id = getattr(character, 'room_id', None)
    region = _valid_sector(room_id, ROOMS.get(room_id))
    if region is None:
        return (0, 0, 0, 0)
    db = session.server.db
    if not callable(getattr(db, 'save_character', None)):
        raise TypeError('Brak autorytatywnego zapisu postaci')
    # Native batch actions can make many items at once; follow the objective
    # event contract and bound one event's contribution. No synthetic tools.
    amount = min(quantity, 10000)
    event_id = event_id or f'v115:profession:{objective}:{uuid4().hex}'
    original_wallet = (character.silver, character.gold, character.mithril)
    try:
        with db.conn:
            inserted = record_event(db.conn, account_id, event_id, region, objective, amount)
            paid = settle_kill_objectives(db, character, account_id, region, (objective,)) if inserted else (0,0,0)
    except BaseException:
        character.silver, character.gold, character.mithril = original_wallet
        raise
    return (int(inserted), *paid)


async def announce_v115_profession_action(session, objective, quantity):
    """Best-effort *additional* milestone after native action succeeded.

    Do not undo delivered items or interrupt original progression if the
    optional v115 objective store fails. Native gameplay remains authoritative.
    """
    try:
        _, quests, achievements, silver = record_v115_profession_action(
            session, objective, quantity)
    except Exception as exc:
        reporter = getattr(session.server, 'report_runtime_error', None)
        if callable(reporter):
            try:
                reporter(exc, command='v115:profession', handler=objective)
            except Exception as report_error:
                print(f'V115_PROFESSION_REPORT_ERROR: {type(report_error).__name__}: {report_error}', flush=True)
        else:
            print(f'V115_PROFESSION_OBJECTIVE_ERROR: {type(exc).__name__}: {exc}', flush=True)
        return
    if quests or achievements:
        await session.send(
            f'Profesje v115: {quests} zadań, {achievements} osiągnięć; +{silver} srebra.')
