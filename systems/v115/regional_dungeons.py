# -*- coding: utf-8 -*-
"""v115: real, connected 24-room dungeons for every new high-level realm.

The base 144-room regions remain accessible, with no level gate. A dungeon clear
is credited only for a confirmed boss defeat at its final chamber; merely
visiting the dungeon never completes it. No separate game engine or soundpack.
"""
from __future__ import annotations
from .high_level_world import REGIONS, REGION_BY_KEY
from .playable_regions import room_id as sector_room_id

WIDTH, HEIGHT = 6, 4
ENTRY_X, ENTRY_Y = 11, 10  # border sector; no cross-zone gates in the interior
_NAMES = ('Zewnętrzny Krąg', 'Zapomniany Trakt', 'Krypta', 'Galeria',
          'Pęknięta Sala', 'Kamienny Labirynt', 'Podziemna Przełęcz', 'Komora')
_INDEX = {reg.key: i for i, reg in enumerate(REGIONS, 1)}


def room_id(region_key: str, x: int, y: int) -> str:
    if region_key not in _INDEX:
        raise ValueError('Nieznana kraina v115')
    if type(x) is not int or type(y) is not int or not 0 <= x < WIDTH or not 0 <= y < HEIGHT:
        raise ValueError('Nieprawidłowe współrzędne lochu')
    return f'v115_dungeon_{_INDEX[region_key]:02d}_p_{x:02d}_{y:02d}'


def warden_id(region_key: str) -> str:
    if region_key not in _INDEX:
        raise ValueError('Nieznana kraina v115')
    return f'v115_dungeon_{_INDEX[region_key]:02d}_warden'


def build_rooms():
    rooms = {}
    for reg in REGIONS:
        for y in range(HEIGHT):
            for x in range(WIDTH):
                rid = room_id(reg.key,x,y)
                exits = {}
                if x: exits['west'] = room_id(reg.key,x-1,y)
                if x < WIDTH-1: exits['east'] = room_id(reg.key,x+1,y)
                if y: exits['south'] = room_id(reg.key,x,y-1)
                if y < HEIGHT-1: exits['north'] = room_id(reg.key,x,y+1)
                if x==0 and y==0:
                    exits['down'] = sector_room_id(reg.key,ENTRY_X,ENTRY_Y)
                rooms[rid] = {
                    'zone':f'Podziemia — {reg.name}',
                    'name':f'{_NAMES[(3*x+5*y)%len(_NAMES)]} — {reg.name}',
                    'desc':('Rozległe podziemia z wieloma ścieżkami. '
                            f'Sektor {x+1}/{WIDTH}, pas {y+1}/{HEIGHT}. '
                            'W głębi czeka strażnik lochu.'),
                    'v115_region_key':reg.key, 'v115_dungeon_key':reg.key,
                    'v1000_landmark':(x+y)%2==0,
                    'exploration_ep':(15+min(15,x+2*y)) if (x+y)%2==0 else 0,
                    # Do not add an artificial +50 threat stage here. The
                    # core adaptive underlevel curve would otherwise turn an
                    # equal-level world boss into a multi-hour one-shot wall.
                    # Boss rank, 45x authored HP and player-party DPS already
                    # provide the intended challenge for 1–6 real players.
                    'generator_level':reg.suggested_level,
                    'exits':exits,
                }
    return rooms


def build_mobs():
    result={}
    for reg in REGIONS:
        level=max(1,reg.suggested_level)
        prefix=f'v115_dungeon_{_INDEX[reg.key]:02d}'
        for kind in ('lurker','warden'):
            boss=kind=='warden'
            result[f'{prefix}_{kind}']={
                'name':f"{'Strażnik Podziemi' if boss else 'Cień Podziemi'} — {reg.name}",
                'max_hp':level*(45 if boss else 10),
                'damage':max(1,level//(3 if boss else 12)),
                'damage_type':'magic' if boss else 'physical',
                'silver':min(10000,level//4),
                'gold':min(1000,level//150), 'mithril':0,
                'stat_reward':level*(5 if boss else 2),
                'class_xp_reward':level*(16 if boss else 8),
                'soul_reward':level*(8 if boss else 4),
                'drops':{}, 'quest_target':None,
                'generator_level':level,
                'v115_region_key':reg.key,
                **({'boss':True,'world_boss':True,'v115_dungeon_boss':reg.key} if boss else {}),
            }
    return result


def build_spawns():
    result=[]
    for reg in REGIONS:
        prefix=f'v115_dungeon_{_INDEX[reg.key]:02d}'
        for y in range(HEIGHT):
            for x in range(WIDTH):
                if (x+y)%2 == 0 and (x,y) != (WIDTH-1,HEIGHT-1):
                    result.append((room_id(reg.key,x,y),f'{prefix}_lurker'))
        result.append((room_id(reg.key,WIDTH-1,HEIGHT-1),f'{prefix}_warden'))
    return result


def install_rooms(existing):
    """Pre-validate ALL links and anchors before mutating the world catalog."""
    rooms=build_rooms()
    if set(rooms).intersection(existing):
        raise ValueError('v115: kolizja ID lochów')
    anchors=[]
    for reg in REGIONS:
        anchor=sector_room_id(reg.key,ENTRY_X,ENTRY_Y)
        room=existing.get(anchor)
        if not isinstance(room,dict) or room.get('v115_region_key')!=reg.key:
            raise ValueError(f'v115: brak prawdziwego wejścia do lochu: {anchor}')
        if 'up' in room.get('exits',{}):
            raise ValueError(f'v115: zajęte wyjście do lochu: {anchor}')
        anchors.append((anchor, room_id(reg.key,0,0)))
    for rid,room in rooms.items():
        for dest in room['exits'].values():
            if dest not in rooms and dest not in existing:
                raise ValueError(f'v115: brak przejścia {rid}->{dest}')
    existing.update(rooms)
    for anchor,target in anchors:
        existing[anchor]['exits']['up']=target
    return len(rooms)


def validate_spawns(rooms,mobs,spawns):
    for rid,mid in spawns:
        if rid not in rooms or mid not in mobs:
            raise ValueError('v115: niespójny spawn lochu')
    return True


def is_authored_dungeon_room(room_key, room):
    """Check both canonical room ID and its authoritative region metadata."""
    if not isinstance(room,dict) or not isinstance(room_key,str):
        return None
    reg=room.get('v115_dungeon_key')
    if reg is None:
        return None
    if reg not in REGION_BY_KEY or room.get('v115_region_key')!=reg:
        raise ValueError('Nieprawidłowy region lochu')
    parts=room_key.split('_p_')
    if len(parts)!=2 or len(parts[1])!=5 or parts[1][2]!='_':
        raise ValueError('Niepoprawny identyfikator komnaty')
    coords=parts[1].split('_')
    if not all(x.isascii() and x.isdigit() for x in coords):
        raise ValueError('Niepoprawne współrzędne komnaty')
    x,y=map(int,coords)
    if room_id(reg,x,y)!=room_key:
        raise ValueError('Komnata poza autoryzowanym lochem')
    return reg


def is_authored_warden_template(actual_id: str, template: dict, region_key: str) -> bool:
    """Recognize real world-generated clones of an authored dungeon warden.

    World._terrain_scaled_template_v0362 and world threat v0384 replace the
    instance template id with a runtime clone on actual server startup. The
    region's catalog ID is not necessarily the instance ID after scaling.
    Only a registered clone of the exact regional warden can clear the dungeon.
    """
    if region_key not in _INDEX or not isinstance(actual_id, str) or not isinstance(template, dict):
        return False
    expected = warden_id(region_key)
    if template.get('v115_dungeon_boss') != region_key or not template.get('boss'):
        return False
    if actual_id == expected:
        return True
    # Runtime variants must be descendants of THIS exact warden, never a
    # similarly named monster, a player supplied ID or a different boss.
    return (actual_id.startswith(expected + '__')
            and template.get('base_template') == expected)
