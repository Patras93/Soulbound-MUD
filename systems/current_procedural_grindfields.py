# -*- coding: utf-8 -*-
"""Rozległe expowiska na piętrach tworzonych na żądanie (v116.00.27).

Boczne sektory zachowują identyfikatory; w Magitek sala schodów jest na końcu galerii.
Tworzone dopiero podczas wejścia na piętro; żadnych migracji baz danych.
"""
from __future__ import annotations

WIDTH = 12
HEIGHT = 12
REVERSE = {'north': 'south', 'south': 'north', 'west': 'east', 'east': 'west'}


def extend_instance_floor(canonical_room, pairs, runtime=False):
    """Dodaj 144 pokoi i do 72 zwykłych spawnów do już rozwiniętego piętra."""
    from data.rooms import ROOMS
    from data.mobs import MOB_TEMPLATES
    from systems.content_registry import MOB_SPAWNS
    from world.dynamic_content import (
        v0100_instance_spec, v0100_subroom_id, v0100_copy_resource_membership,
    )
    import data.catalog_mutations as catalog

    from core.runtime_rules import get_rule
    spec = get_rule('v0100_instance_spec')(canonical_room)
    if not spec or canonical_room not in ROOMS:
        return pairs
    old_total = int(spec['rooms'])
    if v0100_subroom_id(canonical_room, 1) not in ROOMS:
        return pairs
    first = v0100_subroom_id(canonical_room, old_total)
    if first in ROOMS:  # idempotent: no duplicate rooms or spawns
        return pairs

    # Prefer the very end of the original maze (not its final boss room).
    # Only an UNUSED outward-facing direction may be used.
    anchor = None
    direction = None
    for idx in range(old_total - 2, 0, -1):
        rid = v0100_subroom_id(canonical_room, idx)
        if rid in ROOMS and 'south' not in ROOMS[rid].get('exits', {}):
            anchor, direction = rid, 'south'
            break
    if anchor is None:
        raise RuntimeError(f'Brak wolnego granicznego wyjścia na piętrze: {canonical_room}')

    # v116.00.29: check ALL identifiers before creating any rooms. Previously a
    # collision near the end left a partially generated floor in the catalogue.
    # Re-entering a floor must never overwrite a saved location or spawn.
    planned_ids = [v0100_subroom_id(canonical_room, old_total + offset)
                   for offset in range(WIDTH * HEIGHT)]
    occupied = next((rid for rid in planned_ids if rid in ROOMS), None)
    if occupied is not None:
        raise RuntimeError(f'Kolizja identyfikatora proceduralnego: {occupied}')

    base = ROOMS[canonical_room]
    zone = base.get('zone', 'Loch')
    ids = {}
    for y in range(HEIGHT):
        for x in range(WIDTH):
            offset = y * WIDTH + x
            rid = v0100_subroom_id(canonical_room, old_total + offset)
            ids[x, y] = rid
            data = {
                'zone': zone,
                'name': f'Rozległa galeria — piętro {spec["floor"]}, sektor {x+1}/{y+1}',
                'desc': 'Szeroka boczna część piętra. Przejścia łączą się w pętle, umożliwiając dłuższe wyprawy i walki.',
                'exits': {},
                'v0100_instance_kind': spec['kind'],
                'v0100_floor': int(spec['floor']),
                'v0100_floor_room': old_total + offset + 1,
                'procedural_dynamic': True,
                'generated_on_demand': True,
                'v11627_grindfield': True,
                'exploration_ep': 0,
            }
            if 'recommended_mastery' in base:
                data['recommended_mastery'] = base['recommended_mastery']
            if spec.get('profession_dungeon'):
                data['profession_dungeon'] = spec['profession_dungeon']
                data['profession_dungeon_floor'] = int(spec['floor'])
            catalog.catalog_assign(data, 'ROOMS', ROOMS, (rid,))

    for (x, y), rid in ids.items():
        if x + 1 < WIDTH:
            right = ids[x + 1, y]
            catalog.catalog_assign(right, 'ROOMS', ROOMS, (rid, 'exits', 'east'))
            catalog.catalog_assign(rid, 'ROOMS', ROOMS, (right, 'exits', 'west'))
        if y + 1 < HEIGHT:
            below = ids[x, y + 1]
            catalog.catalog_assign(below, 'ROOMS', ROOMS, (rid, 'exits', 'south'))
            catalog.catalog_assign(rid, 'ROOMS', ROOMS, (below, 'exits', 'north'))

    # Anchor is at the old maze boundary; new sector (0,0) is at its edge.
    catalog.catalog_assign(first, 'ROOMS', ROOMS, (anchor, 'exits', direction))
    catalog.catalog_assign(anchor, 'ROOMS', ROOMS, (first, 'exits', REVERSE[direction]))
    # Magitek keeps the boss and staircase in their original room ID,
    # but the only entrance is now at the opposite corner of the gallery.
    if spec['kind'] == 'magitek':
        final = v0100_subroom_id(canonical_room, old_total - 1)
        final_exits = ROOMS[final]['exits']
        if final_exits.get('down'):
            for d, neighbor in list(final_exits.items()):
                if d not in REVERSE:
                    continue
                if ROOMS.get(neighbor, {}).get('exits', {}).get(REVERSE[d]) == final:
                    catalog.catalog_pop_path('ROOMS', ROOMS, (neighbor, 'exits'), REVERSE[d], None)
                catalog.catalog_pop_path('ROOMS', ROOMS, (final, 'exits'), d, None)
            end = ids[WIDTH - 1, HEIGHT - 1]
            catalog.catalog_assign(final, 'ROOMS', ROOMS, (end, 'exits', 'east'))
            catalog.catalog_assign(end, 'ROOMS', ROOMS, (final, 'exits', 'west'))
            previous = base.get('exits', {}).get('up')
            previous_spec = get_rule('v0100_instance_spec')(previous) if previous else None
            if previous_spec and previous_spec['kind'] == 'magitek':
                previous_final = v0100_subroom_id(previous, int(previous_spec['rooms']) - 1)
                catalog.catalog_assign(previous_final, 'ROOMS', ROOMS, (canonical_room, 'exits', 'up'))
    v0100_copy_resource_membership(canonical_room, list(ids.values()))

    # Spawn only existing ordinary enemies from this floor, never bosses.
    boss_flag = spec.get('boss_flag')
    regular = []
    for room, template_id in pairs:
        if room != canonical_room:
            continue
        template = MOB_TEMPLATES.get(template_id, {})
        if boss_flag and template.get(boss_flag):
            continue
        if any(template.get(flag) for flag in ('boss', 'is_boss', 'superboss', 'crypt_boss',
                                               'mythic_crypt_boss', 'astral_boss',
                                               'mythic_astral_boss', 'giant_fortress_boss')):
            continue
        if template_id not in regular:
            regular.append(template_id)
    extras = []
    if regular:
        for idx in range(0, WIDTH * HEIGHT, 2):
            extras.append((v0100_subroom_id(canonical_room, old_total + idx),
                           regular[(idx // 2) % len(regular)]))
    if runtime:
        return list(pairs) + extras
    MOB_SPAWNS.extend(extras)
    return pairs
