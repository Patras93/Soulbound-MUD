# -*- coding: utf-8 -*-
"""v1.25.1: persistable, character-owned horizontal shafts in the Deep Mine.

Legacy mine floors and their pre-generated subrooms remain intact.
Coordinates and room IDs are deterministic, so re-login needs no room snapshot.
"""
import re

HORIZONTAL_MINE_DIRECTIONS = {
    "north": (0, 1), "south": (0, -1), "east": (1, 0), "west": (-1, 0),
    "northeast": (1, 1), "northwest": (-1, 1),
    "southeast": (1, -1), "southwest": (-1, -1),
}
MINE_DIRECTION_LABELS = {
    "north": "północ", "south": "południe", "east": "wschód", "west": "zachód",
    "northeast": "północny wschód", "northwest": "północny zachód",
    "southeast": "południowy wschód", "southwest": "południowy zachód",
    "up": "góra", "down": "dół",
}
MINE_DIRECTION_ALIASES = {
    "n": "north", "north": "north", "polnoc": "north", "północ": "north",
    "s": "south", "south": "south", "poludnie": "south", "południe": "south",
    "e": "east", "east": "east", "wschod": "east", "wschód": "east",
    "w": "west", "west": "west", "zachod": "west", "zachód": "west",
    "prawo": "east", "right": "east", "lewo": "west", "left": "west",
    "ne": "northeast", "northeast": "northeast", "polnocnywschod": "northeast", "północnywschód": "northeast",
    "nw": "northwest", "northwest": "northwest", "polnocnyzachod": "northwest", "północnyzachód": "northwest",
    "se": "southeast", "southeast": "southeast", "poludniowywschod": "southeast", "południowywschód": "southeast",
    "sw": "southwest", "southwest": "southwest", "poludniowyzachod": "southwest", "południowyzachód": "southwest",
    "down": "down", "dol": "down", "dół": "down", "d": "down",
    "up": "up", "gora": "up", "góra": "up", "u": "up",
}
_TUNNEL = re.compile(r"^mine_floor_(\d+)_dig_(\d+)_([pm]\d+)_([pm]\d+)$")
_LEGACY_FLOOR = re.compile(r"^mine_floor_(\d+)(?:_r\d+)?$")

def mine_direction(value):
    return MINE_DIRECTION_ALIASES.get(str(value or '').strip().lower().replace(' ', '').replace('-', '').replace('_',''))

def mine_tunnel_coords(room_id, account_id):
    """Return (floor, x, y), rejecting another character's tunnel."""
    match = _LEGACY_FLOOR.fullmatch(str(room_id or ''))
    if match:
        return (int(match.group(1)), 0, 0)
    match = _TUNNEL.fullmatch(str(room_id or ''))
    if not match or int(match.group(2)) != int(account_id):
        return None
    return int(match.group(1)), decode_coord(match.group(3)), decode_coord(match.group(4))

def encode_coord(number):
    number = int(number)
    return ('m' if number < 0 else 'p') + str(abs(number))

def decode_coord(value):
    return int(value[1:]) * (-1 if value[0] == 'm' else 1)

def mine_tunnel_room_id(floor, account_id, x, y):
    if not x and not y:
        return f'mine_floor_{int(floor)}'
    return f'mine_floor_{int(floor)}_dig_{int(account_id)}_{encode_coord(x)}_{encode_coord(y)}'

def mine_tunnel_identity(room_id):
    match = _TUNNEL.fullmatch(str(room_id or ''))
    if not match:
        return None
    return int(match.group(1)), int(match.group(2)), decode_coord(match.group(3)), decode_coord(match.group(4))
