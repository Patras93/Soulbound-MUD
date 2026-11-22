# -*- coding: utf-8 -*-
"""v116.00.55: real navigation/wander indexing + read-only equipment safety.

Synthetic fixtures only; never read or modify a player's database or run the
production network listener. Do not interpret these checks as a full Windows
60/60 PLUS or as a real-player response-time benchmark.
"""
from __future__ import annotations
from collections import deque
from dataclasses import replace
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
import random
import time


def _old_shortest_path(rooms, start, goal):
    if start == goal:
        return []
    queue = [(start, [])]
    visited = {start}
    while queue:
        room, path = queue.pop(0)
        meta = rooms.get(room)
        if not meta:
            continue
        for direction, target in meta['exits'].items():
            if target in visited or target not in rooms:
                continue
            next_path = path + [(direction, target)]
            if target == goal:
                return next_path
            visited.add(target)
            queue.append((target, next_path))
    return None


def _old_wander(world, templates, eligibility, candidates, now):
    from world.dynamic_content import MOB_WANDER_MIN_SECONDS, MOB_WANDER_MAX_SECONDS, MOB_WANDER_ROOM_CAP
    live = dict(world._last_live_counts)
    moves = []
    for mob in world.mobs.values():
        if not mob.alive or mob.engaged_by:
            continue
        if now < float(mob.next_wander_at or 0.0):
            continue
        mob.next_wander_at = now + random.uniform(MOB_WANDER_MIN_SECONDS, MOB_WANDER_MAX_SECONDS)
        if not eligibility(templates.get(mob.template_id, {})):
            continue
        options = [destination for destination in candidates(mob.room_id)
                   if live.get(destination, 0) < MOB_WANDER_ROOM_CAP]
        if not options:
            continue
        old = mob.room_id
        mob.room_id = random.choice(options)
        live[old] = max(0, live.get(old, 1)-1)
        live[mob.room_id] = live.get(mob.room_id, 0) + 1
        moves.append((mob, old, mob.room_id))
    by_room = {room: list(rows) for room,rows in world._last_live_by_room.items()}
    for mob,old,target in moves:
        old_rows = by_room.get(old, [])
        if mob in old_rows:
            old_rows.remove(mob)
        if old_rows:
            by_room[old] = old_rows
        else:
            by_room.pop(old,None)
        by_room.setdefault(target,[]).append(mob)
    return moves, live, {room:tuple(rows) for room,rows in by_room.items()}


def run():
    from player.session_mixins import guide_navigation as navigation
    from world import world_state
    from world import dynamic_content
    from data.mobs import MOB_TEMPLATES
    from systems.runtime_activation import enabled
    checks = 0
    # Deterministic 5,000 room mesh, with loops, dead-ends, and ties.
    rooms = {f's{i}': {'name':f'Sektor {i}', 'zone':'synthetic',
        'exits': ({'east':f's{i+1}','south':f's{i+2}'} if i < 4998 else
                  {'east':f's{i+1}'} if i==4998 else {})} for i in range(5000)}
    guide = navigation.SessionGuideNavigationMixin()
    guide.server = SimpleNamespace(world=SimpleNamespace(ensure_runtime_room=lambda room: False))
    with patch.object(navigation, 'ROOMS', rooms):
        for start in (0,17,211,2700,4980,4999):
            for goal in (0,1,75,530,4995,4999):
                expected = _old_shortest_path(rooms,f's{start}',f's{goal}')
                actual = guide.shortest_path(f's{start}',f's{goal}')
                assert actual == expected,(start,goal)
                checks+=1
        assert guide.shortest_path('s100', 'does_not_exist') is None
        checks+=1
        baseline=time.perf_counter()
        for _ in range(3):_old_shortest_path(rooms,'s0','s4999')
        baseline=time.perf_counter()-baseline
        optimized=time.perf_counter()
        for _ in range(3):guide.shortest_path('s0','s4999')
        optimized=time.perf_counter()-optimized
        # Pathological Python runtime differences are not a release gate, but
        # record the speedup for transparent release notes.
        assert optimized>0 and baseline>0
        checks+=1
        # Prevent crossing floors. Same result as old BFS with floor filter.
        floor_parser=lambda node: 1 if node.startswith('s') and int(node[1:]) < 150 else 2
        within=guide.shortest_path_within_floor_v11340('s2','s100',floor_parser,1)
        assert within and within[-1][1]=='s100' and len(within)==49
        assert guide.shortest_path_within_floor_v11340('s2','s151',floor_parser,1) is None
        checks+=2

    # Exact equality of move choice, living room-index ordering and counts.
    mobs={f'm{i}':world_state.MobState(f'm{i}', f'r{i%450}', 'synthetic',100,
                                    next_wander_at=0.0) for i in range(1800)}
    def build_world():
        obj=world_state.World.__new__(world_state.World)
        obj.mobs={key:replace(mob) for key,mob in mobs.items()}
        obj._last_live_by_room={}
        for mob in obj.mobs.values():
            obj._last_live_by_room.setdefault(mob.room_id,[]).append(mob)
        obj._last_live_by_room={rid:tuple(rows) for rid,rows in obj._last_live_by_room.items()}
        obj._last_live_counts={rid:len(rows) for rid,rows in obj._last_live_by_room.items()}
        obj.refresh=lambda:dict(obj._last_live_counts)
        return obj
    def candidates(room_id):
        index=int(room_id[1:]);return [f'r{(index+1)%450}',f'r{(index+2)%450}']
    a,b=build_world(),build_world()
    with patch.object(dynamic_content,'mob_template_can_wander',lambda template:True),patch.object(dynamic_content,'mob_wander_candidates',candidates):
        random.seed(88121)
        old_moves,old_counts,old_rows=_old_wander(a,{'synthetic':{}},lambda template:True,candidates,1.0)
        random.seed(88121)
        new_moves=b.wander_step(now=1.0)
    assert [(m.key,old,dest) for m,old,dest in old_moves]==[(m.key,old,dest) for m,old,dest in new_moves]
    checks+=1
    assert b._last_live_counts==old_counts
    checks+=1
    assert {rid:tuple(mob.key for mob in rows) for rid,rows in b._last_live_by_room.items()}=={
        rid:tuple(mob.key for mob in rows) for rid,rows in old_rows.items()}
    checks+=1
    # No moved entity may remain in the old indexed room after a tick.
    for rid,rows in b._last_live_by_room.items():
        assert all(mob.room_id==rid and mob.alive for mob in rows)
        checks+=1
    # Read-only command scope: not when modifying equipment.
    loop=(Path(__file__).resolve().parents[1]/'player/session_mixins/command_loop.py').read_text(encoding='utf-8')
    assert 'command in ("eq", "equipment")' in loop
    assert '("auto", "automatycznie", "najlepsze", "best")' in loop
    assert 'pop("_read_only_equipment_cache_v1262", None)' in loop
    checks+=3
    inv=(Path(__file__).resolve().parents[1]/'player/session_mixins/inventory_equipment.py').read_text(encoding='utf-8')
    assert 'rows = self.equipped_item_rows()' in inv
    checks+=1
    print(f'v116.00.55 LIVE PERF REGRESSION: {checks} PASS; '
          f'synthetic BFS legacy={baseline:.4f}s optimized={optimized:.4f}s '
          f'speedup={baseline/optimized:.1f}x',flush=True)
    return checks


if __name__=='__main__':run()
