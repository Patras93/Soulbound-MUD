# -*- coding: utf-8 -*-
"""Runtime regression: dynamic boss-floor chests must follow boss rooms.

Designed for execution against fully-assembled `server` runtime, not as an
independent import of fragmented legacy modules.
"""


def check_dynamic_boss_chests_v1286(ns):
    errors = []
    world = ns['World']()
    defs = {
        'crypt': ('crypt_floor_', 'crypt_boss', 'crypt_floor'),
        'mythic_crypt': ('mythic_crypt_floor_', 'mythic_crypt_boss', 'mythic_crypt_floor'),
        'astral': ('astral_floor_', 'astral_boss', 'astral_floor'),
        'mythic_astral': ('mythic_astral_floor_', 'mythic_astral_boss', 'mythic_astral_floor'),
        'giant': ('giant_fortress_', 'giant_fortress_boss', 'giant_fortress_floor'),
    }
    checks = 0
    for kind, (prefix, boss_flag, floor_field) in defs.items():
        floors = (100, 110, 210) if kind == 'astral' else (10, 20, 210)
        for floor in floors:
            rid = prefix + str(floor)
            if not world.ensure_runtime_room(rid) and rid not in ns['ROOMS']:
                errors.append(f'{kind}/{floor}: cannot generate floor')
                continue
            expected = sorted({m.room_id for m in world.mobs.values()
                               if ns['MOB_TEMPLATES'].get(m.template_id, {}).get(boss_flag)
                               and int(ns['MOB_TEMPLATES'][m.template_id].get(floor_field, 0) or 0) == floor})
            if len(expected) != 1:
                errors.append(f'{kind}/{floor}: expected one boss room, got {expected}')
                continue
            boss_room = expected[0]
            mapped = ns['boss_floor_chest_room_id'](kind, floor)
            checks += 1
            if mapped != boss_room:
                errors.append(f'{kind}/{floor}: chest at {mapped}, boss at {boss_room}')
                continue
            if not ns['_boss_floor_chest_spec'](boss_room):
                errors.append(f'{kind}/{floor}: boss room has no visible chest spec')
            if ns['_boss_floor_chest_spec'](rid):
                errors.append(f'{kind}/{floor}: wrong chest at landing room')
            # A dynamic floor's authoritative chest room must remain stable if
            # the shared spawn list is pruned or compacted after creation.
            saved = ns['MOB_SPAWNS'][:]
            try:
                ns['MOB_SPAWNS'][:] = [(r, tid) for r, tid in saved
                                       if not (ns['MOB_TEMPLATES'].get(tid, {}).get(boss_flag)
                                               and int(ns['MOB_TEMPLATES'][tid].get(floor_field, 0) or 0) == floor)]
                checks += 1
                if ns['boss_floor_chest_room_id'](kind, floor) != boss_room:
                    errors.append(f'{kind}/{floor}: chest lost after spawn compaction')
            finally:
                ns['MOB_SPAWNS'][:] = saved
    return {'checks': checks, 'error_count': len(errors), 'errors': errors}
