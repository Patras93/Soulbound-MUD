# -*- coding: utf-8 -*-
"""Real, fixed gathering sites across the 30 v115 realms.

Only authored v115 rooms can expose sites. Existing tools, resource pools,
progression and native successful-gather events remain authoritative. No sound
module, new tools, items, or global harvesting permissions.
"""
from __future__ import annotations
from collections import Counter
from .high_level_world import REGION_BY_KEY

KINDS = ('fishing', 'mining', 'woodcutting', 'herbalism')
# Every realm is now 12 x 12; existing 8 x 6 site positions are unchanged.
# Rotation offsets make sites take different routes in each new region.
_WATER = {'ruiny': 'river', 'pustynia': 'lake', 'lodowiec': 'lake',
          'astral': 'river', 'kanion': 'river', 'las': 'river',
          'twierdza': 'lake', 'ocean': 'ocean', 'krypta': 'lake',
          'dolina': 'river'}
_LABELS = {'fishing': 'Łowisko Horyzontów',
           'mining': 'Żyła rud Horyzontów',
           'woodcutting': 'Drzewostan Horyzontów',
           'herbalism': 'Zielnik Horyzontów'}


def site_for_sector(region_key, x, y):
    """Stable authored node descriptor; None denotes a non-resource room."""
    region = REGION_BY_KEY.get(region_key)
    if region is None or type(x) is not int or type(y) is not int or not (0 <= x < 12 and 0 <= y < 12):
        return None
    index = int(region_key.rsplit('_', 1)[-1])
    slot = (3*x + 5*y + 7*index) % 8
    if slot >= 4:
        return None
    kind = KINDS[slot]
    return {'kind': kind, 'name': _LABELS[kind],
            'habitat': _WATER[region.biome] if kind == 'fishing' else None}


def site_for_room(room_id, room):
    """Recognize only the canonical site in a real v115 authored room."""
    if not isinstance(room_id, str) or not isinstance(room, dict):
        return None
    region_key = room.get('v115_region_key')
    if region_key not in REGION_BY_KEY:
        return None
    prefix = region_key + '_p_'
    if not room_id.startswith(prefix):
        return None
    coords = room_id[len(prefix):].split('_')
    if len(coords) != 2 or any(len(c) != 2 or not c.isascii() or not c.isdecimal() for c in coords):
        return None
    x, y = map(int, coords)
    expected = site_for_sector(region_key, x, y)
    return expected if expected is not None and room.get('v115_profession_site') == expected else None


def has_site(room_id, room, kind):
    site = site_for_room(room_id, room)
    return bool(site is not None and site['kind'] == kind)


def region_sites(rooms):
    return Counter(site['kind'] for rid, room in rooms.items()
                   if (site := site_for_room(rid, room)) is not None)


def register_authored_sites(rooms):
    """Expose sites to legacy gathering sets, preserving legacy native methods.

    Called only after new v115 ROOMS are authored. Existing public item and
    tool availability is untouched, and the canonical original fishing/water
    methods retain their exact AST contracts.
    """
    from core.progression_resources import (
        FISHING_ROOMS, RIVER_FISHING_ROOMS, LAKE_FISHING_ROOMS,
        SEA_FISHING_ROOMS, OCEAN_FISHING_ROOMS,
        FISHING_WATER_TYPE_OVERRIDES, HERBALISM_ROOMS, WOODCUTTING_ROOMS,
    )
    water = {'river': (RIVER_FISHING_ROOMS, 'Rzeka'),
             'lake': (LAKE_FISHING_ROOMS, 'Jezioro'),
             'sea': (SEA_FISHING_ROOMS, 'Morze'),
             'ocean': (OCEAN_FISHING_ROOMS, 'Ocean')}
    # Validate the whole regional catalog before any mutation.
    sites = [(rid, site) for rid, room in rooms.items()
             if (site := site_for_room(rid, room)) is not None]
    if len(sites) != 2158 or any(Counter(site['kind'] for _,site in sites)[k] < 500 for k in KINDS):
        raise ValueError('Niekompletne złoża v115; nie rejestruję części świata')
    for rid, site in sites:
        kind = site['kind']
        if kind == 'fishing':
            group, label = water[site['habitat']]
            group.add(rid)
            FISHING_ROOMS.add(rid)
            FISHING_WATER_TYPE_OVERRIDES[rid] = label
        elif kind == 'woodcutting':
            WOODCUTTING_ROOMS.add(rid)
        elif kind == 'herbalism':
            HERBALISM_ROOMS.add(rid)
        # mining uses only the v115 action admission and the existing pickaxe,
        # not the deep-mine tunnel or level unlock machinery.
    return Counter(site['kind'] for _, site in sites)
