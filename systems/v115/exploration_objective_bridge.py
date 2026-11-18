# -*- coding: utf-8 -*-
"""v115: authoritative room discovery -> persistent regional objectives.

Only authored v115 sector rooms are eligible. The existing discovery and
landmark-EP systems remain the sole source of EP; we never mint EP here.
Distinct room IDs are stable event IDs, allowing idempotent recovery on revisit
if the optional v115 objective settlement failed on the first arrival.
No soundpack or network dependency.
"""
from __future__ import annotations
from .high_level_world import REGION_BY_KEY
from .playable_regions import WIDTH, HEIGHT, room_id as sector_id
from .objective_progress import record_event
from .objective_rewards import settle_kill_objectives


def _valid_sector(room_id, room):
    if not isinstance(room, dict):
        return None
    key = room.get('v115_region_key')
    if key is None:
        return None
    if key not in REGION_BY_KEY:
        raise ValueError('Nieznana kraina odkrycia v115')
    from .regional_dungeons import is_authored_dungeon_room
    dungeon = is_authored_dungeon_room(room_id, room)
    if dungeon is not None:
        return dungeon
    prefix = key + '_p_'
    if not isinstance(room_id, str) or not room_id.startswith(prefix):
        raise ValueError('Odkrycie v115 poza autoryzowanym sektorem')
    coords = room_id[len(prefix):].split('_')
    if len(coords) != 2 or not all(len(c)==2 and c.isascii() and c.isdigit() for c in coords):
        raise ValueError('Nieprawidłowy identyfikator sektora')
    x, y = map(int, coords)
    if not (0 <= x < WIDTH and 0 <= y < HEIGHT) or sector_id(key, x, y) != room_id:
        raise ValueError('Sektor spoza granic krainy')
    return key


def record_v115_room_visit(session, room_id, room):
    """Credit one regional exploration event per room/account, then pay silver.

    The caller must pass the authoritative room metadata after recording the
    actual visit via native discover_room(). The game may call this on later
    visits to recover a prior failed v115 write; IDs prevent duplicated gains.

    Returns (new_event_count, quests_paid, achievements_paid, silver_paid).
    SQLite credit+wallet stay within one transaction; all messages follow commit.
    """
    region = _valid_sector(room_id, room)
    if region is None:
        return (0, 0, 0, 0)
    db = session.server.db
    account_id = session.account_id
    character = session.character
    if type(account_id) is not int or account_id <= 0 or int(character.account_id) != account_id:
        raise ValueError('Nagroda za odkrycie: błędny odbiorca')
    if not callable(getattr(db, 'save_character', None)):
        raise TypeError('Brak zapisu postaci')
    objectives = ['explore']
    if room.get('v1000_landmark') and int(room.get('exploration_ep', 0) or 0) > 0:
        objectives.append('discover_checkpoint')
    original_wallet = (character.silver, character.gold, character.mithril)
    new_objectives = []
    paid = (0, 0, 0)
    try:
        with db.conn:
            for objective in objectives:
                event_id = f'v115:room:{room_id}:{objective}'
                if record_event(db.conn, account_id, event_id, region, objective):
                    new_objectives.append(objective)
            if new_objectives:
                paid = settle_kill_objectives(db, character, account_id, region, new_objectives)
    except BaseException:
        character.silver, character.gold, character.mithril = original_wallet
        raise
    return (len(new_objectives), *paid)
