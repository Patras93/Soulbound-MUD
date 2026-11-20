# -*- coding: utf-8 -*-
"""Regresja 20 rozległych historycznych krain v105, bez starych zmian."""
from __future__ import annotations
import sys,unittest
from pathlib import Path
from collections import Counter
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from data.rooms import ROOMS
from systems.content_registry import MOB_SPAWNS,MOB_TEMPLATES
import world.dynamic_content
from systems.current_legacy_region_expansion import SLUGS, WIDTH, HEIGHT, room_id

class LegacyRegionExpansion(unittest.TestCase):
    def test_20_regions_144_new_rooms_each(self):
        self.assertEqual((len(SLUGS),WIDTH,HEIGHT),(20,12,12))
        groups=Counter(r.get('v116_large_legacy') for r in ROOMS.values() if 'v116_large_legacy' in r)
        self.assertEqual(groups,Counter({slug:144 for slug in SLUGS}))

    def test_legacy_routes_and_all_return_paths(self):
        for slug in SLUGS:
            a=f'v10500_{slug}_01';z=f'v10500_{slug}_14'
            zone=ROOMS[a]['zone']
            self.assertEqual(ROOMS[a]['exits']['north'],f'v10500_{slug}_02')
            self.assertEqual(ROOMS[a]['exits']['south'],room_id(slug,0,11))
            self.assertEqual(ROOMS[room_id(slug,0,11)]['exits']['north'],a)
            self.assertEqual(ROOMS[z]['exits']['south'],f'v10500_{slug}_13')
            for y in range(12):
                for x in range(12):
                    rid=room_id(slug,x,y)
                    room=ROOMS[rid]
                    self.assertEqual(room['zone'],zone)
                    self.assertNotIn('trap',room)
                    self.assertNotIn('auto_aggro',room)
                    self.assertNotIn('min_level',room)
                    self.assertEqual(room['exploration_ep'],0)
                    for direction,target in room['exits'].items():
                        self.assertIn(target,ROOMS)
                        inverse={'north':'south','south':'north','east':'west','west':'east'}[direction]
                        self.assertEqual(ROOMS[target]['exits'].get(inverse),rid)
            self.assertEqual(sum(r['zone']==zone for r in ROOMS.values()),158)

    def test_v105_authored_normal_mob_restored_in_extended_room(self):
        # The exact bug from Windows PREDEPLOY v116.00.38: expansion spawns
        # were unexpectedly stronger than the same monster in native v105.
        from copy import deepcopy
        from unittest.mock import patch
        from world.world_state import World
        from data.mobs import MOB_TEMPLATES as MOB_DATA
        for slug in SLUGS:
            base_id = f'v10500_{slug}_mob_1'
            base = MOB_DATA[base_id]
            test_id = base_id + '__world_v0384_regression'
            clone = deepcopy(base)
            clone.update(base_template=base_id,
                         world_threat_overdrive_v0384=True,
                         global_difficulty_overdrive_v0386=True,
                         max_hp=int(base['max_hp']) * 2,
                         damage=int(base['damage']) * 2)
            with patch.dict(MOB_DATA, {test_id: clone}):
                World._restore_v105_authored_stage(room_id(slug, 0, 0), test_id)
                self.assertEqual(clone['max_hp'], base['max_hp'], slug)
                self.assertEqual(clone['damage'], base['damage'], slug)
                self.assertEqual(clone['generator_level'], base['generator_level'], slug)

    def test_v105_expansion_does_not_change_elites_bosses_or_other_regions(self):
        from copy import deepcopy
        from unittest.mock import patch
        from world.world_state import World
        from data.mobs import MOB_TEMPLATES as MOB_DATA
        own = 'v10500_przesmyk_mob_1'
        other = 'v10500_przelom_mob_1'
        for base_id, room, affix in (
            (own, room_id('przesmyk', 1, 1), 'enraged'),
            (other, room_id('przesmyk', 1, 1), None),
            ('v10500_przesmyk_boss_1', room_id('przesmyk', 1, 1), None),
        ):
            source = MOB_DATA[base_id]
            test_id = base_id + '__v11639_nonordinary_regression'
            clone = deepcopy(source)
            clone.update(base_template=base_id, max_hp=777777777,
                         damage=777777, generator_level=29999)
            if affix:
                clone['elite_affix'] = affix
            with patch.dict(MOB_DATA, {test_id: clone}):
                World._restore_v105_authored_stage(room, test_id)
                self.assertEqual(clone['max_hp'], 777777777, base_id)
                self.assertEqual(clone['damage'], 777777, base_id)

    def test_ordinary_monsters_only(self):
        new=[(rid,mob) for rid,mob in MOB_SPAWNS if rid.startswith('v11621_region_')]
        self.assertEqual(len(new),720)
        self.assertEqual(len(set(new)),720)
        for rid,mob in new:
            self.assertIn(rid,ROOMS)
            self.assertIn(mob,MOB_TEMPLATES)
            self.assertIn('_mob_',mob)
            self.assertNotIn('boss',mob.lower())

if __name__=='__main__':unittest.main()
