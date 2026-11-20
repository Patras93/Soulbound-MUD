# -*- coding: utf-8 -*-
"""Checks actual catalog + old routes, border exits, return paths, spawns, no traps."""
import unittest
from collections import deque
from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from data.rooms import ROOMS
from data.mobs import MOB_TEMPLATES
from systems.content_registry import MOB_SPAWNS
from data.catalog_parts.rooms_01 import build_catalog as old_rooms_01
from data.catalog_parts.rooms_02 import build_catalog as old_rooms_02
from data.catalog_parts.rooms_03 import build_catalog as old_rooms_03
from data.catalog_parts.rooms_04 import build_catalog as old_rooms_04
from systems.v116_starter_border_regions import (
    AREAS, WIDTH, HEIGHT, room_id, build_rooms, build_spawns, install_rooms, OPPOSITE, EXTENSION_ZONES,
)

class StarterBorderRegionsV116(unittest.TestCase):
    def test_exact_three_sprawling_connected_zones_and_edge_entrances(self):
        self.assertEqual((WIDTH,HEIGHT),(20,12))
        self.assertEqual(len(AREAS),3)
        planned=build_rooms()
        self.assertEqual(len(planned),3*240)
        for key,zone,anchor,forward,back,start,level,_enemies in AREAS:
            inside={room_id(key,x,y) for y in range(HEIGHT) for x in range(WIDTH)}
            self.assertEqual(len(inside),240)
            self.assertTrue(all(room_id(key,x,y) in inside for x in range(12) for y in range(12)))
            self.assertTrue(all(ROOMS[r]['zone']==EXTENSION_ZONES[key] for r in inside))
            self.assertNotEqual(EXTENSION_ZONES[key],zone)  # do not hijack v0100 procedural room quotas
            self.assertTrue(all(ROOMS[r]['generator_level']==level for r in inside))
            entrance=room_id(key,*start)
            self.assertEqual(ROOMS[anchor]['exits'][forward],entrance)
            self.assertEqual(ROOMS[entrance]['exits'][back],anchor)
            self.assertTrue(start[0] in (0,WIDTH-1) or start[1] in (0,HEIGHT-1))
            # Bidirectional grid. Exactly one link to the historic region, on the edge.
            for x in range(WIDTH):
                for y in range(HEIGHT):
                    rid=room_id(key,x,y)
                    room=ROOMS[rid]
                    self.assertNotIn('trap',room)
                    self.assertNotIn('min_level',room)
                    self.assertNotIn('required_level',room)
                    for direction,dst in room['exits'].items():
                        if dst in inside:
                            self.assertEqual(ROOMS[dst]['exits'][OPPOSITE[direction]],rid)
                        else:
                            self.assertEqual(rid,entrance)
                            self.assertEqual(dst,anchor)
            seen={entrance};pending=deque([entrance])
            while pending:
                for dst in ROOMS[pending.popleft()]['exits'].values():
                    if dst in inside and dst not in seen:
                        seen.add(dst);pending.append(dst)
            self.assertEqual(seen,inside)

    def test_existing_v1168_sector_names_and_descriptions_stay_identical(self):
        # A player who saved their position inside the 12x12 grid must see
        # the exact same room name/description after upgrading to 20x12.
        from systems.v116_starter_border_regions import LANDSCAPES
        for key in ('laki', 'dzicz', 'wybrzeze'):
            for x in range(12):
                for y in range(12):
                    rid=room_id(key,x,y)
                    room=ROOMS[rid]
                    expected_name=f'{LANDSCAPES[key][(x+3*y)%len(LANDSCAPES[key])]} — {EXTENSION_ZONES[key]} ({x+1}/12, {y+1}/12)'
                    expected_desc=f'{EXTENSION_ZONES[key]}. Sektor {x+1}/12, pas {y+1}/12. Ścieżki prowadzą w kilku kierunkach.'
                    self.assertEqual(room['name'],expected_name,rid)
                    self.assertEqual(room['desc'],expected_desc,rid)
            self.assertIn('13/20',ROOMS[room_id(key,12,0)]['name'])

    def test_all_existing_rooms_and_original_exits_survive(self):
        originals={}
        for builder in (old_rooms_01,old_rooms_02,old_rooms_03,old_rooms_04):
            part=builder()
            self.assertFalse(set(originals)&set(part))
            originals.update(part)
        self.assertGreater(len(originals),80)
        for rid,payload in originals.items():
            self.assertIn(rid,ROOMS)
            for direction,old_dst in payload.get('exits',{}).items():
                self.assertEqual(ROOMS[rid]['exits'].get(direction),
                                 None if rid=='graveyard' and direction=='down' else
                                 'v115_graveyard_11_11' if rid=='crypt_entrance' and direction=='up' else old_dst,
                                 (rid,direction))
        self.assertEqual(ROOMS['crossroads']['exits']['up'],'v115_horyzonty_wezel')
        self.assertEqual(ROOMS['graveyard']['exits']['up'],'v115_graveyard_00_00')

    def test_monsters_reuse_existing_templates_and_are_spawned(self):
        expected=build_spawns()
        self.assertEqual(len(expected),3*120)
        self.assertEqual(len(set(expected)),len(expected))
        for rid,mob in expected:
            self.assertIn(rid,ROOMS)
            self.assertIn(mob,MOB_TEMPLATES)
            self.assertEqual(MOB_SPAWNS.count((rid,mob)),1)
        self.assertFalse(any(room.startswith('v116_border_') and (room,mob) not in expected
                             for room,mob in MOB_SPAWNS))

    def test_historical_procedural_gateways_remain_usable(self):
        # Runtime world generation must retain the pre-v116 v0100/v0130 gates.
        import world.dynamic_content
        from world.generation_systems import V013_FRONTIER_SPECS, v0130_gateway_id
        for kind in ('meadow', 'wild', 'coast', 'ocean'):
            spec=V013_FRONTIER_SPECS[kind]
            anchor=spec['anchor'];direction=spec['direction']
            self.assertIn(anchor,ROOMS)
            self.assertEqual(ROOMS[anchor]['exits'][direction],v0130_gateway_id(kind))
            self.assertEqual(ROOMS[v0130_gateway_id(kind)]['exits'][OPPOSITE[direction]],anchor)
        for rid in ('v0100_laki_001', 'v0100_dzicz_001', 'v0100_wybrzeze_001'):
            self.assertIn(rid,ROOMS)

    def test_preflight_rejects_collisions_and_occupied_old_exit_without_mutation(self):
        def fixtures():
            return {anchor:{'zone':zone,'exits':{}} for _,zone,anchor,*_ in AREAS}
        old=fixtures()
        old[AREAS[-1][2]]['exits'][AREAS[-1][3]]='reserved'
        with self.assertRaises(ValueError):install_rooms(old)
        self.assertEqual(set(old),{p[2] for p in AREAS})
        old=fixtures()
        old[room_id(AREAS[-1][0],0,0)]={'exits':{}}
        with self.assertRaises(ValueError):install_rooms(old)
        self.assertEqual(len(old),len(AREAS)+1)
        self.assertTrue(all(not v['exits'] for k,v in old.items() if k in {p[2] for p in AREAS}))

if __name__=='__main__':
    unittest.main()
