# -*- coding: utf-8 -*-
"""30 main dungeons: 144-room exp zone, boss untouched, connected to both wings."""
from __future__ import annotations
import sys, unittest
from collections import deque
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) in sys.path:sys.path.remove(str(ROOT))
sys.path.insert(0,str(ROOT))
from data.rooms import ROOMS
from data.mobs import MOB_TEMPLATES
from systems.content_registry import MOB_SPAWNS
from systems.v115.high_level_world import REGIONS
from systems.v115.regional_dungeons import (room_id as old_id, build_rooms as old_rooms,
    build_spawns as old_spawns)
from systems.v116_dungeon_border_wings import wing_id
from systems.v116_deep_galleries import gallery_id
from systems.current_main_dungeon_expanses import (sector_id,build_rooms,
    build_spawns,install_rooms, WIDTH,HEIGHT,OPPOSITE)

class MainDungeonExpanses(unittest.TestCase):
    def test_30_main_dungeons_large_bosses_and_prior_rooms_unchanged(self):
        self.assertEqual((len(REGIONS),WIDTH,HEIGHT),(30,12,10))
        self.assertEqual(len(build_rooms()),3600)
        original=old_rooms()
        for index,reg in enumerate(REGIONS,1):
            name=f'Podziemia — {reg.name}'
            base={rid for rid in original if rid.startswith(f'v115_dungeon_{index:02d}_p_')}
            extra={sector_id(index,x,y) for y in range(HEIGHT) for x in range(WIDTH)}
            self.assertEqual((len(base),len(extra)),(24,120))
            self.assertEqual(sum(r['zone']==name for r in ROOMS.values()),144)
            for rid in base:
                prev=original[rid];curr=ROOMS[rid]
                for k,v in prev.items():
                    if k=='exits':
                        for way,target in v.items():self.assertEqual(curr['exits'][way],target)
                        self.assertEqual(set(curr['exits'])-set(v),
                            {'east'} if rid==old_id(reg.key,5,0) else
                            {'west'} if rid==old_id(reg.key,0,3) else set())
                    else:self.assertEqual(curr[k],v)
            boss=old_id(reg.key,5,3)
            self.assertEqual(ROOMS[boss],original[boss])
            anchor=old_id(reg.key,5,0)
            self.assertEqual(ROOMS[anchor]['exits']['east'],sector_id(index,0,0))
            self.assertEqual(ROOMS[sector_id(index,0,0)]['exits']['west'],anchor)
            # Other 240 previously authored rooms and links are still present.
            self.assertIn(wing_id(index,11,0),ROOMS)
            self.assertIn(gallery_id(index,0,0),ROOMS)

    def test_full_grid_reversible_reachable_and_without_xp_bonus(self):
        for index,reg in enumerate(REGIONS,1):
            ids={sector_id(index,x,y) for y in range(HEIGHT) for x in range(WIDTH)}
            first=sector_id(index,0,0);anchor=old_id(reg.key,5,0)
            visited={first};q=deque([first])
            while q:
                rid=q.popleft();room=ROOMS[rid]
                self.assertEqual(room['zone'],f'Podziemia — {reg.name}')
                self.assertEqual(room['v115_region_key'],reg.key)
                self.assertEqual(room['v11625_main_dungeon_expanse'],reg.key)
                self.assertNotIn('v115_dungeon_key',room)
                self.assertEqual(room['exploration_ep'],0)
                for key in ('trap','auto_aggro','boss','required_level','min_level'):
                    self.assertNotIn(key,room)
                for way,dst in room['exits'].items():
                    self.assertEqual(ROOMS[dst]['exits'].get(OPPOSITE[way]),rid)
                    if dst not in ids:
                        self.assertEqual((rid,way,dst),(first,'west',anchor))
                    elif dst not in visited:visited.add(dst);q.append(dst)
            self.assertEqual(visited,ids)

    def test_only_real_regular_lurkers_in_new_sectors(self):
        expected=build_spawns()
        self.assertEqual(len(expected),1800)
        self.assertEqual(len(set(expected)),1800)
        actual=[(rid,mob) for rid,mob in MOB_SPAWNS if rid.startswith('v11625_main_dungeon_')]
        self.assertEqual(set(actual),set(expected))
        for rid,mob in expected:
            self.assertEqual(actual.count((rid,mob)),1)
            self.assertIn(rid,ROOMS)
            self.assertIn(mob,MOB_TEMPLATES)
            self.assertFalse(MOB_TEMPLATES[mob].get('boss'))
            self.assertFalse(MOB_TEMPLATES[mob].get('world_boss'))
        for rid,mob in old_spawns():self.assertIn((rid,mob),MOB_SPAWNS)

    def test_v116_live_discovery_bridge_accepts_all_new_dungeon_rooms(self):
        from systems.v115.exploration_objective_bridge import _valid_sector
        from systems.v115.playable_regions import room_id as original_id
        from systems.v115.regional_dungeons import room_id as dungeon_id
        # The actual 12,240 generated rooms carry v115_region_key for
        # terrain scaling. None may be mistaken for a v115 objective sector.
        extensions = [(rid, room) for rid, room in ROOMS.items()
                      if rid.startswith('v116') and room.get('v115_region_key')]
        self.assertEqual(len(extensions),12240)
        for rid, room in extensions:
            self.assertIsNone(_valid_sector(rid, room), rid)
        for reg in REGIONS:
            a=original_id(reg.key,0,0)
            b=dungeon_id(reg.key,0,0)
            self.assertEqual(_valid_sector(a,ROOMS[a]),reg.key)
            self.assertEqual(_valid_sector(b,ROOMS[b]),reg.key)
        actual=extensions[0]
        # Reject counterfeit IDs/region keys rather than silently treating
        # corrupt metadata as an ordinary extension.
        with self.assertRaises(ValueError):
            _valid_sector(actual[0], dict(actual[1],v115_region_key=REGIONS[-1].key))
        with self.assertRaises(ValueError):
            _valid_sector(actual[0]+'_fake',actual[1])
        with self.assertRaises(ValueError):
            _valid_sector('forged',{'v115_region_key':REGIONS[0].key})

    def test_spawn_threat_index_is_exact_and_rebuilds_after_growth(self):
        from core import mines_threat as threat
        from unittest.mock import patch
        from systems.content_registry import MOB_SPAWNS as REAL_SPAWNS
        # No need to mutate players' DB or the actual world catalog.
        first=[(f'fixture_room_{i}', 'temple_rat') for i in range(22000)]
        with patch('systems.content_registry.MOB_SPAWNS',first):
            index=threat.v0866_room_spawn_index()
            self.assertEqual(len(index),22000)
            self.assertIs(index,threat.v0866_room_spawn_index())
            for i in (0,123,999,10000,21999):
                profile=threat.v0866_room_threat_profile(f'fixture_room_{i}',1)
                self.assertEqual(profile['normal_count'],1)
            first.append(('fixture_new_room','temple_rat'))
            self.assertEqual(threat.v0866_room_threat_profile('fixture_new_room',1)['normal_count'],1)
        # Rebuild on the real source after the synthetic fixture exits.
        self.assertEqual(sum(map(len,threat.v0866_room_spawn_index().values())),len(REAL_SPAWNS))

    def test_atomic_preflight_rejects_missing_wrong_occupied_and_collision(self):
        def sample():
            return {old_id(reg.key,5,0):{'zone':f'Podziemia — {reg.name}',
                'v115_dungeon_key':reg.key,'v115_region_key':reg.key,'exits':{}}
                for reg in REGIONS}
        key=old_id(REGIONS[-1].key,5,0)
        x=sample();x.pop(key)
        with self.assertRaises(ValueError):install_rooms(x)
        self.assertEqual(len(x),29)
        x=sample();x[key]['v115_dungeon_key']='other'
        with self.assertRaises(ValueError):install_rooms(x)
        self.assertEqual(len(x),30)
        x=sample();x[key]['exits']['east']='reserved'
        with self.assertRaises(ValueError):install_rooms(x)
        self.assertEqual(len(x),30)
        x=sample();x[sector_id(1,0,0)]={'exits':{}}
        with self.assertRaises(ValueError):install_rooms(x)
        self.assertEqual(len(x),31)

if __name__=='__main__':unittest.main()
