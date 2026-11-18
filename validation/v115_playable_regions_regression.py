# -*- coding: utf-8 -*-
import unittest
from collections import deque
from systems.v115.playable_regions import build_rooms,build_mobs,build_spawns,validate_world,HUB,WIDTH,HEIGHT,room_id
from systems.v115.high_level_world import REGIONS

class LargeAreasV115(unittest.TestCase):
 def test_counts(self):
  self.assertEqual((len(build_rooms()),len(build_mobs()),len(build_spawns())),(1470,90,750))
 def test_catalog_valid(self):
  self.assertTrue(validate_world({'crossroads':{}},{},[]))
 def test_every_area_connected_and_looped(self):
  rooms=build_rooms()
  for region in REGIONS:
   entry=room_id(region.key,0,0)
   seen={entry}; queue=deque([entry]); edges=0
   while queue:
    current=queue.popleft()
    for dst in rooms[current]['exits'].values():
     if not dst.startswith(region.key+'_p_'):continue
     edges+=1
     if dst not in seen:seen.add(dst);queue.append(dst)
   self.assertEqual(len(seen),48)
   self.assertGreater(edges//2,48) # wiele petli, nie liniowy korytarz
 def test_return_paths(self):
  rooms=build_rooms()
  for rid,room in rooms.items():
   if '_p_' not in rid:continue
   for direct, reverse in [('north','south'),('east','west'),('south','north'),('west','east')]:
    dest=room['exits'].get(direct)
    if dest and '_p_' in dest:self.assertEqual(rooms[dest]['exits'][reverse],rid)
 def test_spawns_across_all_regions(self):
  spawns=build_spawns()
  for region in REGIONS:
   self.assertEqual(sum(x.startswith(region.key+'_p_') for x,y in spawns),25)
   self.assertIn((room_id(region.key,7,5),f'{region.key}_guardian'),spawns)
 def test_no_level_gate_soundpack_dependency(self):
  import inspect, systems.v115.playable_regions as m
  self.assertNotIn('sound_events',inspect.getsource(m))
  for room in build_rooms().values():
   self.assertNotIn('min_level',room)
   self.assertNotIn('required_level',room)
 def test_runtime_integration(self):
  from data.rooms import ROOMS
  from data.mobs import MOB_TEMPLATES
  from systems.content_registry import MOB_SPAWNS
  self.assertIn(HUB,ROOMS)
  self.assertEqual(ROOMS['crossroads']['exits']['up'],HUB)
  self.assertIn('v115_region_01_scout',MOB_TEMPLATES)
  self.assertEqual(len([x for x in MOB_SPAWNS if any(x[0].startswith(region.key+'_p_') for region in REGIONS)]),750)
 def test_legacy_preserved(self):
  from data.rooms import ROOMS
  self.assertEqual(ROOMS['crossroads']['exits']['south'],'old_road')
  self.assertEqual(ROOMS['graveyard']['name'],'Stary Cmentarz')
if __name__=='__main__':unittest.main()
