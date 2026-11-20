# -*- coding: utf-8 -*-
"""60 real grinding zones: all 120 old rooms intact, 24 extra per zone."""
from __future__ import annotations
import sys,unittest
from collections import deque,Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) in sys.path:sys.path.remove(str(ROOT))
sys.path.insert(0,str(ROOT))
from data.rooms import ROOMS
from data.mobs import MOB_TEMPLATES
from systems.content_registry import MOB_SPAWNS
from systems.v115.high_level_world import REGIONS
from systems.v116_dungeon_border_wings import wing_id,build_rooms as original_wing_rooms
from systems.v116_deep_galleries import gallery_id,build_rooms as original_gallery_rooms
from systems.current_wing_grindfields import (TYPES,WIDTH,HEIGHT,OPPOSITES,
   sector_id,boundary_anchor,build_rooms,build_spawns,install_rooms)

class WingGrindfields(unittest.TestCase):
    def test_zone_sizes_new_rooms_and_old_exits(self):
        self.assertEqual((len(REGIONS),WIDTH,HEIGHT,len(build_rooms())),(30,6,4,1440))
        originals={'wing':original_wing_rooms(),'gallery':original_gallery_rooms()}
        for kind,oldid,prefix,tag in TYPES:
            for index,reg in enumerate(REGIONS,1):
                anchor=boundary_anchor(kind,index)
                entry=sector_id(kind,index,0,0)
                self.assertEqual(ROOMS[anchor]['exits']['east'],entry)
                self.assertEqual(ROOMS[entry]['exits']['west'],anchor)
                self.assertEqual(ROOMS[anchor]['zone'],ROOMS[entry]['zone'])
                self.assertEqual(sum(room['zone']==f'{prefix} — {reg.name}' for room in ROOMS.values()),144)
                for rid,prev in originals[kind].items():
                    if prev.get('v115_region_key')!=reg.key:continue
                    now=ROOMS[rid]
                    for key,value in prev.items():
                        if key!='exits':self.assertEqual(now[key],value)
                        else:
                            for way,target in value.items():self.assertEqual(now['exits'].get(way),target)
                            # Gallery entrance is appended later to the old wing (0,9).
                            extra=set(now['exits'])-set(value)
                            permitted={'east'} if rid==anchor else set()
                            if kind=='wing' and rid==wing_id(index,0,9):permitted={'north'}
                            self.assertEqual(extra,permitted,(rid,extra))

    def test_reachable_two_way_no_new_boss_exp_or_traps(self):
        for kind,oldid,prefix,tag in TYPES:
            for index,reg in enumerate(REGIONS,1):
                ids={sector_id(kind,index,x,y) for y in range(HEIGHT) for x in range(WIDTH)}
                start=sector_id(kind,index,0,0)
                visited={start};queue=deque([start])
                while queue:
                    rid=queue.popleft();r=ROOMS[rid]
                    self.assertEqual((r['zone'],r[tag],r['v115_region_key']),
                        (f'{prefix} — {reg.name}',reg.key,reg.key))
                    self.assertEqual(r['exploration_ep'],0)
                    self.assertEqual(r['v1000_landmark'],False)
                    for key in ('boss','world_boss','trap','auto_aggro','min_level','required_level'):
                        self.assertNotIn(key,r)
                    for way,to in r['exits'].items():
                        self.assertEqual(ROOMS[to]['exits'].get(OPPOSITES[way]),rid)
                        if to not in ids:self.assertEqual((rid,way,to),(start,'west',boundary_anchor(kind,index)))
                        elif to not in visited:visited.add(to);queue.append(to)
                self.assertEqual(visited,ids)

    def test_spawn_identity_and_one_per_sector(self):
        expected=build_spawns()
        self.assertEqual((len(expected),len(set(expected))),(720,720))
        actual=[(rid,mob) for rid,mob in MOB_SPAWNS if rid.startswith('v11626_')]
        self.assertEqual(Counter(actual),Counter(expected))
        for rid,mob in expected:
            self.assertIn(rid,ROOMS)
            self.assertIn(mob,MOB_TEMPLATES)
            self.assertFalse(MOB_TEMPLATES[mob].get('boss') or MOB_TEMPLATES[mob].get('world_boss'))

    def test_atomic_preflight_missing_wrong_occupied_collision(self):
        def fixture():
            return {boundary_anchor(kind,index):{'zone':f'{prefix} — {reg.name}',
              tag:reg.key,'v115_region_key':reg.key,'exits':{}}
              for kind,oldid,prefix,tag in TYPES for index,reg in enumerate(REGIONS,1)}
        sample=fixture();missing=boundary_anchor('gallery',30);sample.pop(missing)
        with self.assertRaises(ValueError):install_rooms(sample)
        self.assertEqual(len(sample),59)
        sample=fixture();sample[missing]['v115_region_key']='incorrect'
        with self.assertRaises(ValueError):install_rooms(sample)
        self.assertEqual(len(sample),60)
        sample=fixture();sample[missing]['exits']['east']='occupied'
        with self.assertRaises(ValueError):install_rooms(sample)
        self.assertEqual(len(sample),60)
        sample=fixture();sample[sector_id('wing',1,0,0)]={'exits':{}}
        with self.assertRaises(ValueError):install_rooms(sample)
        self.assertEqual(len(sample),61)
        self.assertNotIn('east',sample[boundary_anchor('wing',1)]['exits'])

    def test_old_cross_zone_dungeon_connections_remain(self):
        for index,reg in enumerate(REGIONS,1):
            wing_entry=wing_id(index,11,0)
            gallery_entry=gallery_id(index,0,0)
            self.assertEqual(ROOMS[wing_entry]['exits']['east'],f'v115_dungeon_{index:02d}_p_00_03')
            self.assertEqual(ROOMS[wing_id(index,0,9)]['exits']['north'],gallery_entry)
            self.assertEqual(ROOMS[gallery_entry]['exits']['south'],wing_id(index,0,9))

if __name__=='__main__':unittest.main()
