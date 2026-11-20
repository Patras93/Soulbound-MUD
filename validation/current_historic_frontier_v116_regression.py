# -*- coding: utf-8 -*-
"""Current, version-neutral proof that older authored zone links remain intact."""
from __future__ import annotations
import sys
import unittest
from collections import deque
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from data.rooms import ROOMS
from data.mobs import MOB_TEMPLATES
from systems.content_registry import MOB_SPAWNS
from data.catalog_parts.rooms_01 import build_catalog as _old1
from data.catalog_parts.rooms_02 import build_catalog as _old2
from data.catalog_parts.rooms_03 import build_catalog as _old3
from data.catalog_parts.rooms_04 import build_catalog as _old4
from systems.v116_historic_frontier_regions import (
    AREAS, WIDTH, HEIGHT, NEW_ZONES, OPPOSITE, build_rooms, room_id, build_spawns,
    install_rooms)

class HistoricFrontierRegression(unittest.TestCase):
    def test_three_240_room_areas_reachable_with_border_only_entrances(self):
        self.assertEqual((WIDTH,HEIGHT),(20,12))
        self.assertEqual(len(AREAS),3)
        self.assertEqual(len(build_rooms()),720)
        for key, zone, anchor, direction,back,level,_mobs in AREAS:
            expected={room_id(key,x,y) for y in range(HEIGHT) for x in range(WIDTH)}
            self.assertEqual(len(expected),240)
            self.assertNotEqual(zone,NEW_ZONES[key])
            self.assertEqual(ROOMS[anchor]['exits'][direction],room_id(key,0,0))
            self.assertEqual(ROOMS[room_id(key,0,0)]['exits'][back],anchor)
            for rid in expected:
                room=ROOMS[rid]
                self.assertEqual(room['zone'],NEW_ZONES[key])
                self.assertEqual(room['generator_level'],level)
                self.assertFalse(any(k in room for k in ('trap','min_level','required_level','boss','auto_aggro')))
                self.assertEqual(room['v116_historic_expansion'],key)
                for direction2,dst in room['exits'].items():
                    if dst in expected:
                        self.assertEqual(ROOMS[dst]['exits'][OPPOSITE[direction2]],rid)
                    else:
                        self.assertEqual(rid,room_id(key,0,0))
                        self.assertEqual(dst,anchor)
            seen={room_id(key,0,0)}
            queue=deque(seen)
            while queue:
                for dst in ROOMS[queue.popleft()]['exits'].values():
                    if dst in expected and dst not in seen:
                        seen.add(dst);queue.append(dst)
            self.assertEqual(seen,expected)

    def test_all_original_rooms_names_descriptions_and_old_exits_untouched(self):
        old={}
        for builder in (_old1,_old2,_old3,_old4):
            part=builder()
            self.assertFalse(set(part)&set(old))
            old.update(part)
        self.assertGreater(len(old),100)
        for rid,payload in old.items():
            self.assertIn(rid,ROOMS)
            if payload.get('zone') in ('Jaskinie Goblinów','Obozowiska Bandytów','Ruiny Strażnicy'):
                self.assertEqual(ROOMS[rid]['name'],payload['name'])
                self.assertEqual(ROOMS[rid]['desc'],payload['desc'])
            for direction,dst in payload['exits'].items():
                # Legacy cemetery stairway is intentionally relocated to the
                # outer edge; every other authored historical exit is retained.
                if rid == 'graveyard' and direction == 'down' and dst == 'crypt_entrance':
                    self.assertNotIn('down', ROOMS[rid]['exits'])
                    self.assertEqual(ROOMS['v115_graveyard_11_11']['exits']['down'], dst)
                elif rid == 'crypt_entrance' and direction == 'up' and dst == 'graveyard':
                    self.assertEqual(ROOMS[rid]['exits']['up'],'v115_graveyard_11_11')
                else:
                    self.assertEqual(ROOMS[rid]['exits'][direction],dst,(rid,direction))
        # No existing boss room has changed its outgoing links.
        for rid in ('goblin_throne_cave','bandit_command_tent','ruin_command_chamber'):
            self.assertEqual(ROOMS[rid]['exits'],old[rid]['exits'])
        # The prior 116.00.9 extended areas remain intact.
        for key in ('laki','dzicz','wybrzeze'):
            self.assertIn(f'v116_border_{key}_19_11',ROOMS)

    def test_only_real_nonaltered_monster_templates_and_spawns(self):
        expected=build_spawns()
        self.assertEqual(len(expected),360)
        self.assertEqual(len(set(expected)),360)
        for rid,mob in expected:
            self.assertIn(rid,ROOMS)
            self.assertIn(mob,MOB_TEMPLATES)
            self.assertEqual(MOB_SPAWNS.count((rid,mob)),1)
            self.assertFalse(MOB_TEMPLATES[mob].get('boss'))
        self.assertFalse(any(rid.startswith('v116_historic_') and (rid,mob) not in expected
                             for rid,mob in MOB_SPAWNS))

    def test_preflight_atomic_failure_on_occupied_exit_or_collision(self):
        def fixture():return {a:{'zone':z,'exits':{}} for _k,z,a,*_ in AREAS}
        test=fixture()
        test[AREAS[-1][2]]['exits'][AREAS[-1][3]]='already_used'
        with self.assertRaises(ValueError):install_rooms(test)
        self.assertEqual(len(test),3)
        self.assertEqual(test[AREAS[0][2]]['exits'],{})
        test=fixture()
        test[room_id('gobliny',0,0)]={'zone':'some_other_zone','exits':{}}
        with self.assertRaises(ValueError):install_rooms(test)
        self.assertEqual(len(test),4)
        self.assertEqual(test[AREAS[0][2]]['exits'],{})

    def test_historical_procedural_gateways_still_work(self):
        import world.dynamic_content
        from world.generation_systems import V013_FRONTIER_SPECS, v0130_gateway_id
        for kind in ('meadow','wild','coast','ocean'):
            spec=V013_FRONTIER_SPECS[kind]
            rid=spec['anchor'];direction=spec['direction']
            self.assertEqual(ROOMS[rid]['exits'][direction],v0130_gateway_id(kind))
            self.assertEqual(ROOMS[v0130_gateway_id(kind)]['exits'][OPPOSITE[direction]],rid)

if __name__=='__main__':unittest.main()
