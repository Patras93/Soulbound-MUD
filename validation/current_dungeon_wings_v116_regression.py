# -*- coding: utf-8 -*-
"""Proof of thirty optional, non-invasive large dungeon wings."""
from __future__ import annotations
import sys,unittest
from collections import deque
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from data.rooms import ROOMS
from data.mobs import MOB_TEMPLATES
from systems.content_registry import MOB_SPAWNS
from systems.v115.high_level_world import REGIONS
from systems.v115.regional_dungeons import (build_rooms as old_rooms, room_id as old_id,
                                             warden_id, WIDTH as OLD_WIDTH, HEIGHT as OLD_HEIGHT)
from systems.v116_deep_galleries import gallery_id
from systems.v116_dungeon_border_wings import (WIDTH,HEIGHT,ENTRANCE_X,ENTRANCE_Y,
       OPPOSITE,wing_id,build_rooms,build_spawns,install_rooms)

class DungeonWingsRegression(unittest.TestCase):
    def test_wings_are_large_connected_and_reversible(self):
        self.assertEqual((WIDTH,HEIGHT,OLD_WIDTH,OLD_HEIGHT),(12,10,6,4))
        self.assertEqual(len(REGIONS),30)
        planned=build_rooms()
        self.assertEqual(len(planned),3600)
        for index,reg in enumerate(REGIONS,1):
            ids={wing_id(index,x,y) for y in range(HEIGHT) for x in range(WIDTH)}
            self.assertEqual(len(ids),120)
            anchor=old_id(reg.key,0,3)
            entry=wing_id(index,ENTRANCE_X,ENTRANCE_Y)
            self.assertEqual(ROOMS[anchor]['exits']['west'],entry)
            self.assertEqual(ROOMS[entry]['exits']['east'],anchor)
            visited={entry};todo=deque([entry])
            while todo:
                rid=todo.popleft()
                room=ROOMS[rid]
                self.assertEqual(room['generator_level'],reg.suggested_level)
                self.assertEqual(room['v115_region_key'],reg.key)
                self.assertEqual(room['v116_dungeon_wing'],reg.key)
                self.assertNotIn('v115_dungeon_key',room)
                self.assertFalse(any(k in room for k in ('trap','required_level','min_level','boss','auto_aggro')))
                for direction,dst in room['exits'].items():
                    if dst in ids:
                        self.assertEqual(ROOMS[dst]['exits'][OPPOSITE[direction]],rid)
                        if dst not in visited:
                            visited.add(dst);todo.append(dst)
                    else:
                        self.assertIn((rid,dst,direction),{
                            (entry,anchor,'east'),
                            (wing_id(index,0,HEIGHT-1),gallery_id(index,0,0),'north'),
                            (wing_id(index,11,8), f'v11626_wing_{index:02d}_p_00_00','east'),
                        })
            self.assertEqual(visited,ids)
    def test_existing_dungeons_and_bosses_are_unchanged(self):
        old=old_rooms();self.assertEqual(len(old),720)
        for rid,room in old.items():
            self.assertEqual(ROOMS[rid]['name'],room['name'])
            self.assertEqual(ROOMS[rid]['desc'],room['desc'])
            self.assertEqual(ROOMS[rid]['zone'],room['zone'])
            self.assertEqual(ROOMS[rid]['generator_level'],room['generator_level'])
            self.assertEqual(ROOMS[rid]['v115_dungeon_key'],room['v115_dungeon_key'])
            for direction,dst in room['exits'].items():
                self.assertEqual(ROOMS[rid]['exits'][direction],dst)
            extra=set(ROOMS[rid]['exits'])-set(room['exits'])
            if rid.endswith('_p_00_03'):
                self.assertEqual(extra,{'west'})
            elif rid.endswith('_p_05_00'):
                # v116.00.25: only the east outer BORDER may lead to the
                # additional main expanse; all other historical exits stay.
                from systems.current_main_dungeon_expanses import sector_id
                self.assertEqual(extra,{'east'})
                index=int(rid.split('_')[2])
                self.assertEqual(ROOMS[rid]['exits']['east'],sector_id(index,0,0))
            else:
                self.assertEqual(extra,set())
        for reg in REGIONS:
            boss=old_id(reg.key,5,3)
            self.assertEqual(ROOMS[boss],old[boss])
            self.assertTrue(MOB_TEMPLATES[warden_id(reg.key)]['boss'])
    def test_spawns_only_existing_regular_enemies(self):
        expected=build_spawns()
        self.assertEqual(len(expected),1800)
        self.assertEqual(len(set(expected)),1800)
        for rid,mob in expected:
            self.assertIn(rid,ROOMS)
            self.assertIn(mob,MOB_TEMPLATES)
            self.assertFalse(MOB_TEMPLATES[mob].get('boss'))
            self.assertEqual(MOB_SPAWNS.count((rid,mob)),1)
        self.assertFalse(any(rid.startswith('v116_dungeon_wing_') and (rid,mob) not in expected
                             for rid,mob in MOB_SPAWNS))
    def test_install_atomic_on_missing_anchor_occupied_direction_or_collision(self):
        def fixture():
            return {old_id(reg.key,0,3):{'v115_dungeon_key':reg.key,
                      'v115_region_key':reg.key,'exits':{}} for reg in REGIONS}
        case=fixture();del case[old_id(REGIONS[15].key,0,3)]
        before=len(case)
        with self.assertRaises(ValueError):install_rooms(case)
        self.assertEqual(len(case),before)
        case=fixture();case[old_id(REGIONS[-1].key,0,3)]['exits']['west']='occupied'
        with self.assertRaises(ValueError):install_rooms(case)
        self.assertEqual(len(case),30)
        self.assertFalse('west' in case[old_id(REGIONS[0].key,0,3)]['exits'])
        case=fixture();case[wing_id(1,0,0)]={'exits':{}}
        with self.assertRaises(ValueError):install_rooms(case)
        self.assertEqual(len(case),31)
        self.assertFalse('west' in case[old_id(REGIONS[0].key,0,3)]['exits'])
    def test_prior_regions_still_present(self):
        for key in ('gobliny','bandyci','straznica'):
            self.assertIn(f'v116_historic_{key}_19_11',ROOMS)
        for key in ('laki','dzicz','wybrzeze'):
            self.assertIn(f'v116_border_{key}_19_11',ROOMS)
if __name__=='__main__':unittest.main()
