# -*- coding: utf-8 -*-
import unittest
from systems.v115.high_level_world import REGIONS, REGION_BY_KEY, dynamic_region
from systems.v115.content_catalog import quest_catalog, achievement_catalog, repeatable_threshold

class CatalogTests(unittest.TestCase):
    def test_thirty_unique_regions(self):
        self.assertEqual(len(REGIONS),30)
        self.assertEqual(len(REGION_BY_KEY),30)
        self.assertEqual(len(set(r.name for r in REGIONS)),30)
    def test_dynamic_levels_and_open_access(self):
        for r in REGIONS:
            first=dynamic_region(r.key,1)
            higher=dynamic_region(r.key,1000)
            self.assertFalse(first['entry_locked'])
            self.assertEqual(higher['suggested_level']-first['suggested_level'],99900)
    def test_invalid_depths(self):
        for v in (0,-1,True,2.5,10**12):
            with self.assertRaises(ValueError):dynamic_region(REGIONS[0].key,v)
    def test_5000_quest_definitions(self):
        items=quest_catalog()
        self.assertEqual(len(items),5000)
        self.assertEqual(len({x.key for x in items}),5000)
        self.assertTrue(all(x.target>0 and x.region in REGION_BY_KEY for x in items))
        self.assertGreater(len({(x.region,x.objective,x.target) for x in items}),4500)
    def test_2000_achievement_definitions(self):
        items=achievement_catalog()
        self.assertEqual(len(items),2000)
        self.assertEqual(len({x.key for x in items}),2000)
        self.assertTrue(all(x.repeatable and x.threshold>=1 for x in items))
    def test_repeatable_increasing(self):
        self.assertEqual([repeatable_threshold(7,n) for n in range(4)],[7,14,21,28])

if __name__=='__main__':unittest.main()
