# -*- coding: utf-8 -*-
"""v116: complete proof of 30 long, border-linked high-level galleries."""
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
from systems.v115.high_level_world import REGIONS
from systems.v115.regional_dungeons import build_rooms as original_dungeons, room_id as dungeon_id
from systems.v116_dungeon_border_wings import (build_rooms as earlier_wings,
    wing_id,HEIGHT as OLD_HEIGHT)
from systems.v116_deep_galleries import (WIDTH,HEIGHT,ENTRY,OPPOSITE,
    gallery_id,build_rooms,build_spawns,install_rooms)

class DeepGalleriesRegression(unittest.TestCase):
    def test_layout_all_connected_reverse_and_outer_border_only(self):
        self.assertEqual((len(REGIONS),WIDTH,HEIGHT), (30,12,10))
        self.assertEqual(len(build_rooms()),3600)
        for index,reg in enumerate(REGIONS,1):
            ids={gallery_id(index,x,y) for y in range(HEIGHT) for x in range(WIDTH)}
            old=wing_id(index,0,OLD_HEIGHT-1)
            start=gallery_id(index,*ENTRY)
            self.assertEqual(len(ids),120)
            self.assertEqual(ROOMS[old]['exits']['north'],start)
            self.assertEqual(ROOMS[start]['exits']['south'],old)
            self.assertEqual(ROOMS[old]['v115_region_key'],reg.key)
            visited={start};todo=deque([start])
            while todo:
                rid=todo.popleft();room=ROOMS[rid]
                self.assertEqual(room['zone'],f'Dalsze Podziemia — {reg.name}')
                self.assertEqual(room['generator_level'],reg.suggested_level)
                self.assertEqual(room['v116_deep_gallery'],reg.key)
                self.assertNotIn('v115_dungeon_key',room)
                self.assertFalse(any(k in room for k in
                                 ('trap','auto_aggro','required_level','min_level','boss','world_boss')))
                for direction,dst in room['exits'].items():
                    if dst in ids:
                        self.assertEqual(ROOMS[dst]['exits'][OPPOSITE[direction]],rid)
                        if dst not in visited:visited.add(dst);todo.append(dst)
                    else:
                        self.assertIn((rid,direction,dst),{
                            (start,'south',old),
                            (gallery_id(index,11,8),'east',f'v11626_gallery_{index:02d}_p_00_00'),
                        })
            self.assertEqual(visited,ids)

    def test_original_wings_and_boss_chambers_persist(self):
        for rid,data in earlier_wings().items():
            old=ROOMS[rid]
            for key in ('zone','name','desc','generator_level','v115_region_key',
                        'v116_dungeon_wing','exploration_ep'):
                self.assertEqual(old[key],data[key],(rid,key))
            for direction,dest in data['exits'].items():
                self.assertEqual(old['exits'][direction],dest,(rid,direction))
            index=int(rid.split('_')[3])
            special=wing_id(index,0,OLD_HEIGHT-1)==rid
            extra=set(old['exits'])-set(data['exits'])
            permitted=({'north'} if special else set())
            if rid==wing_id(index,11,8):permitted={'east'}
            self.assertEqual(extra,permitted,rid)
        for rid, data in original_dungeons().items():
            self.assertEqual(ROOMS[rid]['name'],data['name'])
            self.assertEqual(ROOMS[rid]['desc'],data['desc'])
            for way,dest in data['exits'].items():
                self.assertEqual(ROOMS[rid]['exits'][way],dest)
            if rid.endswith('_p_05_03'):
                self.assertEqual(ROOMS[rid],data)

    def test_new_regular_spawns_not_bosses(self):
        expected=build_spawns()
        self.assertEqual(len(expected),1800)
        self.assertEqual(len(set(expected)),1800)
        for rid,mob in expected:
            self.assertIn(rid,ROOMS)
            self.assertIn(mob,MOB_TEMPLATES)
            self.assertFalse(MOB_TEMPLATES[mob].get('boss'))
            self.assertFalse(MOB_TEMPLATES[mob].get('world_boss'))
            self.assertEqual(MOB_SPAWNS.count((rid,mob)),1)
        self.assertEqual({p for p in MOB_SPAWNS if p[0].startswith('v116_deep_gallery_')},set(expected))

    def test_atomic_missing_anchor_wrong_region_occupied_exit_and_id(self):
        def fixture():
            return {wing_id(i,0,OLD_HEIGHT-1):{'v116_dungeon_wing':reg.key,
                   'v115_region_key':reg.key,'exits':{}}
                   for i,reg in enumerate(REGIONS,1)}
        x=fixture();x.pop(wing_id(30,0,OLD_HEIGHT-1))
        with self.assertRaises(ValueError):install_rooms(x)
        self.assertEqual(len(x),29)
        x=fixture();x[wing_id(30,0,OLD_HEIGHT-1)]['v115_region_key']='wrong'
        with self.assertRaises(ValueError):install_rooms(x)
        self.assertEqual(len(x),30)
        x=fixture();x[wing_id(30,0,OLD_HEIGHT-1)]['exits']['north']='occupied'
        with self.assertRaises(ValueError):install_rooms(x)
        self.assertEqual(len(x),30)
        self.assertNotIn('north',x[wing_id(1,0,OLD_HEIGHT-1)]['exits'])
        x=fixture();x[gallery_id(30,0,0)]={'exits':{}}
        with self.assertRaises(ValueError):install_rooms(x)
        self.assertEqual(len(x),31)

    def test_prior_regions_and_borders_preserved(self):
        for region in ('laki','dzicz','wybrzeze'):
            self.assertIn(f'v116_border_{region}_19_11',ROOMS)
        for region in ('gobliny','bandyci','straznica'):
            self.assertIn(f'v116_historic_{region}_19_11',ROOMS)
        for region in ('swiatynia','kopalnia','krypta'):
            self.assertIn(f'v116_depths_{region}_19_11',ROOMS)

if __name__=='__main__':unittest.main()
