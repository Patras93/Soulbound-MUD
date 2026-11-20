# -*- coding: utf-8 -*-
"""Regresje rozbudowanych historycznych expowisk."""
import sys, unittest
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from data.rooms import ROOMS
from systems.content_registry import MOB_SPAWNS,MOB_TEMPLATES
import world.dynamic_content
from systems.current_remaining_grindfields import SPECS, WIDTH, HEIGHT, OPPOSITE, sector_id

class Grindfields(unittest.TestCase):
    def test_all_13_are_large_and_anchored_at_edge(self):
        self.assertEqual(len(SPECS),13)
        self.assertEqual(len({z for _,_,z,_ in SPECS}),13)
        for slug,anchor,zone,mobs in SPECS:
            self.assertEqual(ROOMS[anchor]['exits']['east'],sector_id(slug,0,6))
            self.assertGreaterEqual(sum(r['zone']==zone for r in ROOMS.values()),174)
            self.assertTrue(all(m in MOB_TEMPLATES for m in mobs))
            self.assertEqual(ROOMS[sector_id(slug,0,6)]['exits']['west'],anchor)
    def test_reversible_grid_and_safe_mobs(self):
        sp=Counter((rid,m) for rid,m in MOB_SPAWNS if rid.startswith('v11623_exp_'))
        self.assertEqual(sum(sp.values()),936)
        self.assertTrue(all(n==1 for n in sp.values()))
        for slug,anchor,zone,mobs in SPECS:
            for y in range(HEIGHT):
                for x in range(WIDTH):
                    rid=sector_id(slug,x,y)
                    room=ROOMS[rid]
                    self.assertEqual(room['zone'],zone)
                    self.assertNotIn('trap',room)
                    self.assertNotIn('auto_aggro',room)
                    self.assertNotIn('min_level',room)
                    self.assertEqual(room['exploration_ep'],0)
                    for d,to in room['exits'].items():
                        self.assertEqual(ROOMS[to]['exits'].get(OPPOSITE[d]),rid)
            self.assertEqual(sum(n for (rid,m),n in sp.items() if rid.startswith('v11623_exp_'+slug+'_')),72)
            self.assertTrue(all(m in MOB_TEMPLATES for (rid,m),n in sp.items() if rid.startswith('v11623_exp_'+slug+'_')))
    def test_legacy_exp_unchanged(self):
        # Nie wolno zamienić zwykłej krainy w nową strefę ani dopisać nowego bossa.
        for _,_,zone,_ in SPECS:
            self.assertGreaterEqual(sum(r['zone']==zone for r in ROOMS.values()),174)
        self.assertNotIn('v11623_exp_',str([m for _,m in MOB_SPAWNS if 'boss' in m.lower()]))



class CoreGrindfields(unittest.TestCase):
    def test_four_core_regions_are_large(self):
        from systems.current_remaining_grindfields import CORE_GRIND_SPECS, core_sector_id
        from collections import Counter
        self.assertEqual(len(CORE_GRIND_SPECS), 4)
        self.assertEqual(len({z for _,_,z,_ in CORE_GRIND_SPECS}), 4)
        expected = {'Łąki Zielarskie':210, 'Góry':216, 'Łąki':222, 'Dzicz':252}
        for slug, anchor, zone, mobs in CORE_GRIND_SPECS:
            self.assertEqual(sum(r['zone'] == zone for r in ROOMS.values()), expected[zone])
            self.assertEqual(ROOMS[anchor]['exits']['east'], core_sector_id(slug,0,6))
            self.assertEqual(ROOMS[core_sector_id(slug,0,6)]['exits']['west'], anchor)
            self.assertTrue(all(m in MOB_TEMPLATES for m in mobs))

    def test_reversible_new_grids_no_extra_xp_or_bosses(self):
        from systems.current_remaining_grindfields import CORE_GRIND_SPECS, core_sector_id
        extra_spawns = [(r,m) for r,m in MOB_SPAWNS if r.startswith('v11624_core_')]
        self.assertEqual(len(extra_spawns), 288)
        for slug, anchor, zone, mobs in CORE_GRIND_SPECS:
            self.assertEqual(sum(r.startswith('v11624_core_'+slug+'_') for r,m in extra_spawns),72)
            for y in range(12):
                for x in range(12):
                    rid = core_sector_id(slug,x,y)
                    room = ROOMS[rid]
                    self.assertEqual(room['zone'], zone)
                    self.assertEqual(room['exploration_ep'], 0)
                    self.assertNotIn('trap',room)
                    self.assertNotIn('auto_aggro',room)
                    self.assertNotIn('min_level',room)
                    for d,target in room['exits'].items():
                        self.assertEqual(ROOMS[target]['exits'].get(OPPOSITE[d]),rid)
        self.assertTrue(all(m in MOB_TEMPLATES for _,m in extra_spawns))
        self.assertTrue(all('boss' not in m.lower() for _,m in extra_spawns))

if __name__=='__main__':unittest.main()
