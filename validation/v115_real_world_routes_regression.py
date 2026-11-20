# -*- coding: utf-8 -*-
"""v115 full authored-world integration (not merely fake fixtures)."""
import unittest
from collections import deque

# Preserve the canonical startup dependency order (boss item audit).
import systems.dungeons_regions
import world.equipment_help
from data.rooms import ROOMS
from data.mobs import MOB_TEMPLATES
from systems.content_registry import MOB_SPAWNS
from systems.v115.legacy_expareas import AREAS, room_id, WIDTH, HEIGHT, expand
from systems.v115.graveyard_expansion import room_id as grave_room_id, WIDTH as GRAVE_WIDTH, HEIGHT as GRAVE_HEIGHT

class RealWorldRoutes(unittest.TestCase):
    def test_all_six_zones_reachable_and_returnable(self):
        zones = [(key, anchor, lambda x,y,key=key:room_id(key,x,y)) for key,_,anchor,_,_ in AREAS]
        zones.append(('graveyard','graveyard',grave_room_id))
        for key, anchor, rid in zones:
            self.assertIn(anchor, ROOMS, key)
            entry = rid(0,0)
            self.assertIn(entry, ROOMS, key)
            self.assertIn(entry, ROOMS[anchor]['exits'].values(), key)
            reachable = {anchor}; queue=deque([anchor])
            while queue:
                current=queue.popleft()
                for nxt in ROOMS[current].get('exits', {}).values():
                    if nxt in ROOMS and nxt not in reachable:
                        reachable.add(nxt);queue.append(nxt)
            self.assertEqual(sum(rid(x,y) in reachable for y in range(HEIGHT) for x in range(WIDTH)),WIDTH*HEIGHT,key)
            # Every new room also has a route backwards to the original entrance.
            reverse={}; target={rid(x,y) for y in range(HEIGHT) for x in range(WIDTH)} | {anchor}
            for source in target:
                for dest in ROOMS[source].get('exits',{}).values():
                    if dest in target:reverse.setdefault(dest,set()).add(source)
            back={anchor};queue=deque([anchor])
            while queue:
                for prev in reverse.get(queue.popleft(),()):
                    if prev not in back:back.add(prev);queue.append(prev)
            self.assertEqual(sum(rid(x,y) in back for y in range(HEIGHT) for x in range(WIDTH)),WIDTH*HEIGHT,key)
    def test_horizon_hub_preserves_old_northern_route(self):
        self.assertEqual(ROOMS['crossroads']['exits']['north'], 'wild_frontier')
        self.assertEqual(ROOMS['crossroads']['exits']['up'], 'v115_horyzonty_wezel')
        self.assertEqual(ROOMS['v115_horyzonty_wezel']['exits']['down'], 'crossroads')
    def test_real_spawns_resolve(self):
        for key,_,_,_,_ in AREAS:
            own=[(room,mob) for room,mob in MOB_SPAWNS if room.startswith('v115_legacy_'+key+'_')]
            self.assertGreaterEqual(len(own),32,key)
            for room,mob in own:
                self.assertIn(room, ROOMS)
                self.assertIn(mob,MOB_TEMPLATES)
        grave=[(room,mob) for room,mob in MOB_SPAWNS if room.startswith('v115_graveyard_')]
        self.assertEqual(len(grave),GRAVE_WIDTH*GRAVE_HEIGHT//2)
    def test_existing_routes_and_idempotence(self):
        for _,_,anchor,_,_ in AREAS:
            self.assertTrue(ROOMS[anchor].get('exits'))
        self.assertEqual(expand(ROOMS,MOB_TEMPLATES,MOB_SPAWNS)['new_rooms'],0)
    def test_no_partial_install_if_late_anchor_blocked(self):
        from unittest.mock import patch
        rooms={anchor:{'exits':{}} for _,_,anchor,_,_ in AREAS}
        templates={mob:{} for _,_,_,mobs,_ in AREAS for mob in mobs}
        late=AREAS[-1][2]
        rooms[late]['exits']={key:'occupied' for key in ('up','down','west','east','south','north')}
        before={name:dict(value['exits']) for name,value in rooms.items()}
        with self.assertRaises(ValueError):expand(rooms,templates,[])
        self.assertEqual(set(rooms),set(before))
        self.assertEqual({name:value['exits'] for name,value in rooms.items()},before)

if __name__=='__main__':unittest.main()
