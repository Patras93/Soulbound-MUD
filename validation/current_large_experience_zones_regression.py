# -*- coding: utf-8 -*-
"""Weryfikuje duże expowiska i nienaruszone drogi w v116.00.22."""
from __future__ import annotations
import sys,unittest
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from data.rooms import ROOMS
from systems.content_registry import MOB_SPAWNS,MOB_TEMPLATES
import world.dynamic_content
from systems.current_large_experience_zones import region_specs,room_id,WIDTH,HEIGHT,OPPOSITE

class LargeExperienceZones(unittest.TestCase):
    def test_all_27_zones_large_and_no_collisions(self):
        specs=list(region_specs())
        self.assertEqual(len(specs),27)
        self.assertEqual(len({s[0] for s in specs}),27)
        self.assertEqual((WIDTH,HEIGHT),(12,12))
        groups=Counter(r.get('v116_large_exp') for r in ROOMS.values() if 'v116_large_exp' in r)
        self.assertEqual(groups,Counter({slug:144 for slug,*_ in specs}))
        for slug,anchor,direction,mobs in specs:
            zone=ROOMS[anchor]['zone']
            self.assertGreaterEqual(sum(r.get('zone')==zone for r in ROOMS.values()),144)
            self.assertTrue(all(mob in MOB_TEMPLATES for mob in mobs))
            self.assertEqual(ROOMS[anchor]['exits'][direction],room_id(slug,0,11 if direction=='south' else 6))

    def test_paths_are_reversible_and_no_traps(self):
        for slug,anchor,direction,_ in region_specs():
            zone=ROOMS[anchor]['zone']
            for y in range(HEIGHT):
                for x in range(WIDTH):
                    rid=room_id(slug,x,y);r=ROOMS[rid]
                    self.assertEqual(r['zone'],zone)
                    self.assertNotIn('trap',r)
                    self.assertNotIn('auto_aggro',r)
                    self.assertNotIn('min_level',r)
                    self.assertEqual(r['exploration_ep'],0)
                    for d,t in r['exits'].items():
                        self.assertIn(t,ROOMS)
                        self.assertEqual(ROOMS[t]['exits'].get(OPPOSITE[d]),rid)

    def test_old_bosses_not_spawned_or_changed(self):
        sp=[(rid,mob) for rid,mob in MOB_SPAWNS if rid.startswith('v11622_exp_')]
        self.assertEqual(len(sp),1944)
        self.assertEqual(len(set(sp)),1944)
        for rid,mob in sp:
            self.assertIn(rid,ROOMS)
            self.assertIn(mob,MOB_TEMPLATES)
            self.assertNotIn('boss',mob.lower())
            self.assertNotIn('raid',mob.lower())

    def test_no_ordinary_exp_zone_still_under_24(self):
        zcounts=Counter(r.get('zone') for r in ROOMS.values())
        spawns_per_zone=Counter(ROOMS[rid]['zone'] for rid,mob in MOB_SPAWNS if rid in ROOMS)
        short={z for z,n in zcounts.items() if n<24 and spawns_per_zone[z]>0}
        self.assertEqual(short,{'Super Bossowie UOSSMUD'})

if __name__=='__main__':unittest.main()
