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


def _v116_extension(room_id, room, region_key):
    """Recognize authentic v116 extensions without crediting v115-only goals.

    The newer wings carry v115_region_key for their terrain/difficulty, but
    their rooms are NOT part of the v115 144-sector/24-dungeon objective.
    Validate their canonical IDs and provenance markers: a forged/malformed
    v115 room still fails closed instead of silently becoming a free reward.
    """
    if not isinstance(room_id, str):
        return False
    from .regional_dungeons import _INDEX
    index = _INDEX[region_key]
    import re
    match = re.fullmatch(r'(v116(?:_dungeon_wing|_deep_gallery)|v11625_main_dungeon|v11626_(?:wing|gallery))_([0-9]{2})_p_([0-9]{2})_([0-9]{2})', room_id)
    if match is None:
        return False
    label, found_index, x_txt, y_txt = match.groups()
    if int(found_index) != index:
        raise ValueError('Niepoprawna kraina rozszerzenia v116')
    x, y = int(x_txt), int(y_txt)
    from systems.v116_dungeon_border_wings import wing_id, WIDTH as WING_W, HEIGHT as WING_H
    from systems.v116_deep_galleries import gallery_id, WIDTH as GAL_W, HEIGHT as GAL_H
    from systems.current_main_dungeon_expanses import sector_id as main_id, WIDTH as MAIN_W, HEIGHT as MAIN_H
    from systems.current_wing_grindfields import sector_id as side_id, WIDTH as SIDE_W, HEIGHT as SIDE_H
    kinds = {
        'v116_dungeon_wing': ('v116_dungeon_wing', None, WING_W, WING_H, wing_id),
        'v116_deep_gallery': ('v116_deep_gallery', None, GAL_W, GAL_H, gallery_id),
        'v11625_main_dungeon': ('v11625_main_dungeon_expanse', None, MAIN_W, MAIN_H, main_id),
        'v11626_wing': ('v116_dungeon_wing', 'wing', SIDE_W, SIDE_H, lambda i,a,b:side_id('wing',i,a,b)),
        'v11626_gallery': ('v116_deep_gallery', 'gallery', SIDE_W, SIDE_H, lambda i,a,b:side_id('gallery',i,a,b)),
    }
    marker, side, width, height, canonical = kinds[label]
    if (room.get(marker) != region_key or x >= width or y >= height
            or (side is not None and room.get('v11626_wing_grindfield') != side)
            or canonical(index,x,y) != room_id):
        raise ValueError('Niepoprawny sektor rozszerzenia v116')
    return True


def _valid_sector(room_id, room):
    if not isinstance(room, dict):
        return None
    key = room.get('v115_region_key')
    if key is None:
        return None
    if key not in REGION_BY_KEY:
        raise ValueError('Nieznana kraina odkrycia v115')
    if _v116_extension(room_id, room, key):
        return None  # Native discovery/EP still work; no duplicate v115 objectives.
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
