# -*- coding: utf-8 -*-
"""v116: extensive 12x12 realms, border-only inter-zone passages.

Older room IDs, enemies, existing quests and SQLite positions remain stable.
"""
import unittest
from collections import deque
from data.rooms import ROOMS
from systems.content_registry import MOB_SPAWNS
from systems.v115.high_level_world import REGIONS
from systems.v115.playable_regions import room_id, WIDTH, HEIGHT, HUB
from systems.v115.regional_dungeons import ENTRY_X, ENTRY_Y, room_id as dungeon_id

class ExpansiveBorderRoutes(unittest.TestCase):
    def test_regions_are_large_with_old_rooms_preserved(self):
        self.assertEqual((WIDTH,HEIGHT),(12,12))
        for reg in REGIONS:
            sector_ids={room_id(reg.key,x,y) for y in range(HEIGHT) for x in range(WIDTH)}
            self.assertEqual(len(sector_ids),144)
            self.assertTrue(all(rid in ROOMS for rid in sector_ids))
            self.assertIn(room_id(reg.key,7,5),sector_ids)
            self.assertIn((room_id(reg.key,7,5),f'{reg.key}_guardian'),MOB_SPAWNS)
            self.assertTrue(all(ROOMS[rid]['v115_region_key']==reg.key for rid in sector_ids))
            # Route through the whole area, not a short tunnel to a gateway.
            origin=room_id(reg.key,0,0)
            visited={origin}; queue=deque([origin]);
            while queue:
                for dest in ROOMS[queue.popleft()]['exits'].values():
                    if dest in sector_ids and dest not in visited: visited.add(dest);queue.append(dest)
            self.assertEqual(visited,sector_ids)

    def test_all_cross_zone_links_are_on_a_boundary(self):
        for reg in REGIONS:
            for y in range(HEIGHT):
                for x in range(WIDTH):
                    rid=room_id(reg.key,x,y)
                    room=ROOMS[rid]
                    for direction,dest in room['exits'].items():
                        if dest.startswith(reg.key+'_p_'):
                            inverse={'north':'south','south':'north','east':'west','west':'east'}[direction]
                            self.assertEqual(ROOMS[dest]['exits'][inverse],rid)
                        else:
                            self.assertTrue(x in (0,WIDTH-1) or y in (0,HEIGHT-1),rid)
                            if direction=='west' and (x,y)==(0,0):
                                self.assertTrue(dest.startswith('v116_horizon_border_') and dest.endswith('_12'))
                            elif direction=='up':
                                self.assertEqual((x,y),(ENTRY_X,ENTRY_Y))
                                self.assertEqual(dest,dungeon_id(reg.key,0,0))
                            else: self.fail(f'Unexpected cross-zone exit {rid} {direction} {dest}')
            self.assertEqual(ROOMS[dungeon_id(reg.key,0,0)]['exits']['down'],room_id(reg.key,ENTRY_X,ENTRY_Y))
            # Historical interior stair location is now an ordinary walkable sector.
            self.assertNotIn('up',ROOMS[room_id(reg.key,6,4)]['exits'])

    def test_no_auto_aggression_or_trap_exits(self):
        from data.mobs import MOB_TEMPLATES
        for reg in REGIONS:
            for y in range(HEIGHT):
                for x in range(WIDTH):
                    r=ROOMS[room_id(reg.key,x,y)]
                    self.assertNotIn('min_level',r)
                    self.assertNotIn('trap',r)
            self.assertFalse(MOB_TEMPLATES[f'{reg.key}_scout'].get('auto_aggro',False))

if __name__ == '__main__': unittest.main()
