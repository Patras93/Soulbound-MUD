# -*- coding: utf-8 -*-
"""v110: isolated, validated teacher mappings for the eight new classes.

Teachers reuse existing dedicated NPCs in eight new realms.  No global catalogue
or historical NPC is mutated here: only the not-yet-committed v110 staging rows.
"""
from __future__ import annotations

from core.archetypes.expansion import CLASS_SPECS
from world.v11000_realm_index import REGIONS


def assign_teachers(staged_npcs, staged_rooms, make_prefix):
    names = [row[0] for row in CLASS_SPECS]
    if len(names) != 8 or len(set(names)) != 8 or len(REGIONS) < 8:
        raise RuntimeError('v110: niepełne lub powtórzone klasy nauczycieli')
    used_rooms = set()
    for index, class_name in enumerate(names):
        nid = make_prefix(REGIONS[index][0]) + '_npc_2'
        npc = staged_npcs.get(nid)
        if not npc or npc.get('teacher_class'):
            raise RuntimeError('v110: niedostępny NPC nauczyciela: ' + nid)
        room = npc.get('room')
        if not room or room not in staged_rooms or room in used_rooms:
            raise RuntimeError('v110: niedostępna sala nauczyciela: ' + nid)
        used_rooms.add(room)
        npc['teacher_class'] = class_name
        npc['dialogue'] += ' Nauczyciel klasy ' + class_name + '. Użyj komendy learn lub talk.'
    if len(used_rooms) != 8:
        raise RuntimeError('v110: niedostateczna liczba sal nauczycieli')
    return 8
