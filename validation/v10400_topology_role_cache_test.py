# -*- coding: utf-8 -*-
"""Regresja algorytmu wyboru przejsc przed i po optymalizacji v104.

Nie uruchamia serwera, nie korzysta z baz i nie zmienia map gry.
"""
from __future__ import annotations
import random
from world import topology_generator as t


def _legacy_candidates(rooms, left, right, seed):
    candidates = []
    right_set = set(right)
    for a, da in t._component_slots(rooms, left):
        db = t.OPPOSITE[da]
        for b in right_set:
            if t._free(rooms[b], db):
                role_score = t._role_compat(t._room_role(a, rooms[a]), t._room_role(b, rooms[b]))
                score = role_score * 10.0 + t._unit(f"{seed}:link:{a}:{da}:{b}")
                candidates.append((score, a, da, b, db))
    candidates.sort(reverse=True)
    return candidates


def run():
    rng = random.Random(10400)
    checks = 0
    names = ('Brama', 'Krypta', 'Karczma', 'Warsztat', 'Gildia', 'Las',
             'Wieza', 'Swiatynia', 'Port')
    for case in range(50):
        rooms = {}
        for i in range(rng.randint(5, 18)):
            rid = f'left_{i:03}'
            rooms[rid] = {'name': rng.choice(names) + ' ' + str(i), 'exits': {}}
        cut = len(rooms)
        for i in range(rng.randint(4, 16)):
            rid = f'right_{i:03}'
            rooms[rid] = {'name': rng.choice(names) + ' ' + str(i), 'exits': {}}
        left, right = list(rooms)[:cut], list(rooms)[cut:]
        for room in rooms.values():
            for d in t.GENERATED_DIRS:
                if rng.random() < .18:
                    room['exits'][d] = 'zajety'
        legacy = _legacy_candidates(rooms, left, right, f'v104:{case}')
        current = t._candidate_links(rooms, left, right, f'v104:{case}')
        assert current == legacy, (case, 'candidate order changed')
        roles = {rid: t._room_role(rid, room) for rid, room in rooms.items()}
        current_cached = t._candidate_links(rooms, left, right, f'v104:{case}', roles)
        assert current_cached == legacy, (case, 'cached candidate order changed')
        checks += 2
    return checks

if __name__ == '__main__':
    print('V104 TOPOLOGIA CACHE:', run(), 'PASS')
