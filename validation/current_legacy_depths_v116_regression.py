# -*- coding: utf-8 -*-
"""Regression of v116 depth extensions. Directly runnable and release-gated."""
from __future__ import annotations
import sys,unittest
from collections import deque
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) in sys.path:sys.path.remove(str(ROOT))
sys.path.insert(0,str(ROOT))
from data.rooms import ROOMS
from data.mobs import MOB_TEMPLATES
from systems.content_registry import MOB_SPAWNS
from data.catalog_parts.rooms_01 import build_catalog as old_01
from data.catalog_parts.rooms_02 import build_catalog as old_02
from data.catalog_parts.rooms_03 import build_catalog as old_03
from data.catalog_parts.rooms_04 import build_catalog as old_04
from systems.v116_legacy_depths_regions import (
    AREAS, WIDTH, HEIGHT, OPPOSITE, build_rooms, build_spawns, install_rooms, room_id,
)

class LegacyDepthsRegression(unittest.TestCase):
    def test_large_connected_areas_with_perimeter_only_exits(self):
        self.assertEqual((WIDTH,HEIGHT,len(AREAS)),(20,12,3))
        self.assertEqual(len(build_rooms()),720)
        for key,_source,anchor,direction,reverse,entry,zone,level,_mobs in AREAS:
            ids={room_id(key,x,y) for y in range(HEIGHT) for x in range(WIDTH)}
            self.assertEqual(len(ids),240)
            start=room_id(key,*entry)
            self.assertEqual(ROOMS[anchor]['exits'][direction],start)
            self.assertEqual(ROOMS[start]['exits'][reverse],anchor)
            visited={start};todo=deque([start])
            while todo:
                rid=todo.popleft();room=ROOMS[rid]
                self.assertEqual(room['zone'],zone)
                self.assertEqual(room['generator_level'],level)
                self.assertEqual(room['v116_legacy_depths'],key)
                self.assertFalse(any(x in room for x in ('trap','boss','auto_aggro','min_level','required_level')))
                for way,dst in room['exits'].items():
                    if dst in ids:
                        self.assertEqual(ROOMS[dst]['exits'][OPPOSITE[way]],rid)
                        if dst not in visited:visited.add(dst);todo.append(dst)
                    else:self.assertEqual((rid,dst,way),(start,anchor,reverse))
            self.assertEqual(visited,ids)
    def test_existing_early_dungeons_and_bosses_unchanged(self):
        old={}
        for fn in (old_01,old_02,old_03,old_04):old.update(fn())
        for rid,data in old.items():
            if data.get('zone') not in ('Piwnica Świątyni','Podziemia'):continue
            self.assertIn(rid,ROOMS)
            self.assertEqual(ROOMS[rid]['name'],data['name'])
            self.assertEqual(ROOMS[rid]['desc'],data['desc'])
            self.assertEqual(ROOMS[rid]['zone'],data['zone'])
            for direction,dst in data['exits'].items():
                self.assertEqual(ROOMS[rid]['exits'].get(direction),
                                 'v115_graveyard_11_11' if rid=='crypt_entrance' and direction=='up' else dst,
                                 (rid,direction))
            extra=set(ROOMS[rid]['exits'])-set(data['exits'])
            self.assertEqual(extra,{'north'} if rid=='temple_basement_deep_nest'
                              else {'west'} if rid in ('cave_entrance','crypt_entrance')
                              else set(),rid)
        for bossroom in ('crystal_chamber','crypt_depths','temple_basement_lower_vault'):
            self.assertEqual(ROOMS[bossroom]['exits'],old[bossroom]['exits'])
        self.assertEqual(ROOMS['crypt_hall']['exits'],old['crypt_hall']['exits'])
    def test_spawns_existing_regular_mobs_only(self):
        expected=build_spawns();self.assertEqual(len(expected),360)
        self.assertEqual(len(set(expected)),360)
        for rid,mob in expected:
            self.assertIn(rid,ROOMS)
            self.assertIn(mob,MOB_TEMPLATES)
            self.assertFalse(MOB_TEMPLATES[mob].get('boss'))
            self.assertNotIn(MOB_TEMPLATES[mob].get('boss_mechanic'),('crystal_lord','world_boss'))
            self.assertEqual(MOB_SPAWNS.count((rid,mob)),1)
        self.assertFalse(any(rid.startswith('v116_depths_') and (rid,mob) not in expected
                             for rid,mob in MOB_SPAWNS))
    def test_atomic_failure_missing_anchor_occupied_exit_or_id_collision(self):
        def fixture():return {anchor:{'zone':zone,'exits':{}}
                             for _key,zone,anchor,*_ in AREAS}
        x=fixture();del x['crypt_entrance']
        with self.assertRaises(ValueError):install_rooms(x)
        self.assertEqual(len(x),2)
        x=fixture();x['crypt_entrance']['exits']['west']='something'
        with self.assertRaises(ValueError):install_rooms(x)
        self.assertEqual(len(x),3)
        self.assertNotIn('north',x['temple_basement_deep_nest']['exits'])
        x=fixture();x[room_id('swiatynia',0,0)]={'exits':{}}
        with self.assertRaises(ValueError):install_rooms(x)
        self.assertEqual(len(x),4)
    def test_prior_expansions_and_safe_old_entry(self):
        for suffix in ('laki','dzicz','wybrzeze'):
            self.assertIn(f'v116_border_{suffix}_19_11',ROOMS)
        for suffix in ('gobliny','bandyci','straznica'):
            self.assertIn(f'v116_historic_{suffix}_19_11',ROOMS)
        self.assertIn('v116_dungeon_wing_30_p_11_09',ROOMS)
        self.assertEqual(ROOMS['temple_basement']['exits']['up'],'temple')
        self.assertEqual(ROOMS['crypt_entrance']['exits']['up'],'v115_graveyard_11_11')
        self.assertEqual(ROOMS['cave_entrance']['exits']['down'],'cave_tunnel')

if __name__=='__main__':unittest.main()
