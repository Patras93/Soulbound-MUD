# -*- coding: utf-8 -*-
"""Credit v115 regional objectives only after a native quest was completed.

Uses the native QuestCompletedEvent and the authoritative completion_count.
All payments remain in existing wallet and objective SQLite tables. Optional
best-effort listener: an additional v115 reward must never undo a quest.
No audio, no new profession tools, no replacement quest engine.
"""
from __future__ import annotations
from core.classes_skills import ROOMS
from systems.content_registry import QUESTS
from .exploration_objective_bridge import _valid_sector
from .objective_progress import record_event
from .objective_rewards import settle_kill_objectives


def record_v115_completed_quest(session, quest_id):
    """Return (new_event, quests, achievements, silver) for a real turn-in.

    The native quest row is already committed before QuestCompletedEvent is
    published. completion_count makes retries idempotent, including a repeat
    of the same event after restart. Credit only while actually inside an
    authored v115 sector, never in the old world or at a spoofed room ID.
    """
    if not isinstance(quest_id, str) or not 1 <= len(quest_id) <= 120:
        raise ValueError('Nieprawidłowe ID ukończonego zadania')
    if quest_id not in QUESTS:
        raise ValueError('Nieznany ukończony quest')
    character = getattr(session, 'character', None)
    account_id = getattr(session, 'account_id', None)
    if character is None or type(account_id) is not int or account_id <= 0:
        raise ValueError('Nieprawidłowy odbiorca ukończonego zadania')
    if int(getattr(character, 'account_id', -1)) != account_id:
        raise ValueError('Postać nie należy do konta')
    room_id = getattr(character, 'room_id', None)
    region = _valid_sector(room_id, ROOMS.get(room_id))
    if region is None:
        return (0, 0, 0, 0)
    db = session.server.db
    row = db.quest(account_id, quest_id)
    if not row or row['status'] != 'completed':
        return (0, 0, 0, 0)
    count = int(row['completion_count'])
    if count < 1:
        return (0, 0, 0, 0)
    event_id = f'v115:quest_complete:{quest_id}:{count}'
    original_wallet = (character.silver, character.gold, character.mithril)
    try:
        with db.conn:
            added = record_event(db.conn, account_id, event_id, region, 'complete_quest')
            awards = settle_kill_objectives(db, character, account_id, region,
                                            ('complete_quest',)) if added else (0, 0, 0)
    except BaseException:
        character.silver, character.gold, character.mithril = original_wallet
        raise
    return (int(added), *awards)


async def credit_v115_completed_quest(event):
    """Subscriber to the normal quest completion bus; no client hooks."""
    added, quests, achievements, silver = record_v115_completed_quest(
        event.session, event.quest_id)
    if quests or achievements:
        await event.session.send(
            f'Horyzonty: {quests} zadań, {achievements} osiągnięć; +{silver} srebra.')
