# -*- coding: utf-8 -*-
"""Runtime v116.00.27: floor side-expanses, old boss checkpoints and saves."""
from __future__ import annotations
import sys
from pathlib import Path
from collections import deque
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) in sys.path:sys.path.remove(str(ROOT))
sys.path.insert(0,str(ROOT))
from data.rooms import ROOMS
from data.mobs import MOB_TEMPLATES
from systems.content_registry import MOB_SPAWNS
from world.dynamic_content import (
    v0100_subroom_id, v0100_instance_spec, _v11627_original_expand,
    v0100_expand_instance_floor,
)
from world.economy_quests import (
    create_infinite_crypt_floor_definition,
    create_infinite_profession_dungeon_floor_definition,
    create_infinite_mine_floor_definition,
    create_infinite_astral_floor_definition,
)
from systems.current_procedural_grindfields import WIDTH,HEIGHT

REVERSE={'north':'south','south':'north','east':'west','west':'east'}

def run():
    checks=0
    def ck(ok,msg):
        nonlocal checks
        assert ok,msg
        checks+=1
    cases=(
        ('crypt_regular',create_infinite_crypt_floor_definition,(401,)),
        ('crypt_boss',create_infinite_crypt_floor_definition,(410,)),
        ('astral',create_infinite_astral_floor_definition,(401,)),
        ('profession',create_infinite_profession_dungeon_floor_definition,('crystal_mine',401)),
        ('mine',create_infinite_mine_floor_definition,(401,)),
    )
    for kind,creator,args in cases:
        canonical,pairs=creator(*args)
        spec=v0100_instance_spec(canonical)
        ck(bool(spec),f'{kind}: canonical spec')
        old_total=spec['rooms']
        _v11627_original_expand(canonical,pairs,runtime=True)
        old_ids=[canonical]+[v0100_subroom_id(canonical,i) for i in range(1,old_total)]
        old={rid:{key:(dict(value) if isinstance(value,dict) else value)
                  for key,value in ROOMS[rid].items()} for rid in old_ids}
        original_pairs=list(pairs)
        original_global_spawns=list(MOB_SPAWNS)
        expanded=v0100_expand_instance_floor(canonical,pairs,runtime=True)
        new_ids={v0100_subroom_id(canonical,old_total+i) for i in range(WIDTH*HEIGHT)}
        ck(len(new_ids)==144 and all(rid in ROOMS for rid in new_ids),f'{kind}: 144 new rooms')
        ck(all(ROOMS[rid]['zone']==ROOMS[canonical]['zone'] for rid in new_ids),f'{kind}: zone unchanged')
        ck(all(ROOMS[rid].get('exploration_ep')==0 for rid in new_ids),f'{kind}: no discovery XP')
        ck(all(not any(k in ROOMS[rid] for k in ('trap','boss','auto_aggro','min_level')) for rid in new_ids),f'{kind}: no traps/bosses/gates')
        for rid,saved in old.items():
            now=ROOMS[rid]
            ck({k:v for k,v in now.items() if k!='exits'}=={k:v for k,v in saved.items() if k!='exits'},f'{kind}: unchanged room data {rid}')
            for direction,target in saved['exits'].items():
                ck(now['exits'].get(direction)==target,f'{kind}: old exit intact {rid}:{direction}')
        touched=[rid for rid in old if ROOMS[rid]['exits']!=old[rid]['exits']]
        ck(len(touched)==1,f'{kind}: exactly one old boundary changed: {touched}')
        ck(all(ROOMS[x]['exits'].get(REVERSE[d])==rid for rid in new_ids for d,x in ROOMS[rid]['exits'].items() if d in REVERSE and x in ROOMS),f'{kind}: reversible directions')
        first=v0100_subroom_id(canonical,old_total)
        ck(any(dst==first for dst in ROOMS[touched[0]]['exits'].values()),f'{kind}: side entrance')
        visited={first}; queue=deque([first])
        while queue:
            u=queue.popleft()
            for next_id in ROOMS[u]['exits'].values():
                if next_id in new_ids and next_id not in visited:
                    visited.add(next_id);queue.append(next_id)
        ck(visited==new_ids,f'{kind}: all 144 side rooms reachable')
        last=v0100_subroom_id(canonical,old_total-1)
        ck(ROOMS[last]==old[last],f'{kind}: boss/down-stairs room unchanged')
        ck(MOB_SPAWNS==original_global_spawns,f'{kind}: runtime does not modify static spawns')
        fresh=[(rid,mob) for rid,mob in expanded if rid in new_ids]
        ck(len(fresh) in (0,72),f'{kind}: no invented enemies')
        ck(all(mob in MOB_TEMPLATES and not MOB_TEMPLATES[mob].get('boss') for _,mob in fresh),f'{kind}: ordinary mob templates')
        ck(v0100_expand_instance_floor(canonical,pairs,runtime=True)==pairs,f'{kind}: idempotency')
        print(f'PASS {kind} old={old_total} new=144 additional-spawns={len(fresh)}',flush=True)
    print('PROCEDURAL GRINDFIELDS '+str(checks)+'/'+str(checks)+' PASS',flush=True)


def run_real_procedural_entrance_tours():
    """Real floor creators, all rooms, graph return and idempotence; no live DB.

    This calls the production World.ensure_infinite_dungeon_floor code, but
    substitutes only live combat-event/spawn object creation (never the
    actual floor, room or exit generators). It is not a live TCP walk-through.
    """
    from collections import deque
    from data.rooms import ROOMS
    from data.mobs import MOB_TEMPLATES
    from systems.content_registry import MOB_SPAWNS
    from world.world_state import World

    cases = (
        ('astral', 'astral_gate', 'up', 'astral_floor_100'),
        ('crypt', 'crypt_hall', 'down', 'crypt_floor_1'),
        ('mine', 'crystal_chamber', 'down', 'mine_floor_1'),
        ('crystal_mine', 'crystal_chamber', 'east', 'prof_crystal_mine_1'),
        ('ancient_forest', 'deep_grove', 'down', 'prof_ancient_forest_1'),
        ('giant', 'giant_fortress_gate', 'up', 'giant_fortress_1'),
        ('alchemy', 'herbalist_hut', 'north', 'prof_alchemy_garden_1'),
        ('mythic_astral', 'mythic_astral_gate', 'up', 'mythic_astral_floor_1'),
        ('mythic_crypt', 'mythic_crypt_gate', 'down', 'mythic_crypt_floor_1'),
        ('sunken_grotto', 'sea_pier', 'down', 'prof_sunken_grotto_1'),
        ('uoss_deep', 'uoss_deep_dungeon_entry_v11331', 'down',
         'uoss_deep_dungeon_floor_1_v11331'),
    )
    reverse = {'north':'south','south':'north','east':'west','west':'east',
               'up':'down','down':'up'}
    passed = 0
    for kind, entrance, direction, target in cases:
        assert entrance in ROOMS, (kind, 'missing entrance')
        assert ROOMS[entrance]['exits'].get(direction) == target, (kind,'wrong entry')
        before_ids = set(ROOMS)
        before_spawns = tuple(MOB_SPAWNS)
        spawned = []
        world = World.__new__(World)
        world._generatorize_runtime_room = lambda room_id: True
        world._register_runtime_spawn = lambda rid,tid: spawned.append((rid,tid))
        assert world.ensure_infinite_dungeon_floor(target), (kind,'generation refused')
        assert target in ROOMS, (kind,'not created')
        new = set(ROOMS) - before_ids
        side = {rid for rid in new if ROOMS[rid].get('v11627_grindfield')
                or ROOMS[rid].get('v11628_grindfield')}
        assert len(side) == 144, (kind,'not 144 side rooms',len(side))
        assert all(ROOMS[rid]['zone'] == ROOMS[target]['zone'] for rid in side),kind
        assert all(not any(ROOMS[rid].get(flag) for flag in
                           ('trap','auto_aggro','min_level','boss')) for rid in side),kind
        assert all(ROOMS[rid].get('exploration_ep',0) == 0 for rid in side),kind
        allowed = new | {target,entrance}
        found = {target}
        queue = deque([target])
        while queue:
            rid = queue.popleft()
            for dest in ROOMS[rid]['exits'].values():
                if dest in allowed and dest not in found:
                    found.add(dest); queue.append(dest)
        assert side <= found, (kind,'disconnected side rooms',len(side-found))
        assert entrance in found, (kind,'no return to original entrance')
        for rid in side:
            for movement,dest in ROOMS[rid]['exits'].items():
                if dest in allowed and movement in reverse:
                    assert ROOMS[dest]['exits'].get(reverse[movement]) == rid, (
                        kind,'one-way side route',rid,movement,dest)
        assert all(not MOB_TEMPLATES[tid].get('boss') for rid,tid in spawned
                   if rid in side), (kind,'boss in side exp field')
        assert tuple(MOB_SPAWNS) == before_spawns, (kind,'global spawns mutated')
        previous = (len(ROOMS),len(spawned))
        assert world.ensure_infinite_dungeon_floor(target), (kind,'repeat failed')
        assert (len(ROOMS),len(spawned)) == previous, (kind,'duplicate generation')
        print('PASS 11 DUNGEON TOUR',kind,'rooms',len(new),
              'side',len(side),'spawns',len(spawned),flush=True)
        passed += 1
    assert passed == 11
    # Boss floors are tested through existing boss-gate/checkpoint regressions.
    # Do not move them or bypass the first-clear requirements here.
    print('REAL FLOOR GENERATION/RETURN 11/11 PASS',flush=True)

if __name__=='__main__':
    run()
    run_real_procedural_entrance_tours()
