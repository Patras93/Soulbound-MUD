# -*- coding: utf-8 -*-
"""v115 regional resources: real command admission, old tools, no sound."""
import asyncio
import inspect
import unittest
from collections import Counter
from types import SimpleNamespace

from data.rooms import ROOMS
from systems.v115.high_level_world import REGIONS
from systems.v115.playable_regions import WIDTH, HEIGHT, room_id, build_rooms
from systems.v115.profession_sites import (
    site_for_sector, site_for_room, has_site, region_sites, KINDS
)
# unittest discover -s validation otherwise shadows runtime events with
# validation/events.py; prefer the actual game package during imports.
import sys
from pathlib import Path
_game_root = str(Path(__file__).resolve().parents[1])
if sys.path[0] != _game_root:
    sys.path.insert(0, _game_root)
from player.session_mixins.gathering_actions import SessionGatheringActionsMixin
from player.session_mixins.gathering import SessionGatheringMixin


class _Probe:
    combat_mob_key = None
    account_id = 1

    def __init__(self, room):
        self.character = SimpleNamespace(room_id=room)
        self.sent = []
        self.server = SimpleNamespace(db=SimpleNamespace(item_qty=lambda *_: 0))

    async def send(self, message):
        self.sent.append(message)


class ProfessionRegionSites(unittest.TestCase):
    def test_30_regions_all_have_balanced_real_sites(self):
        self.assertEqual(len(REGIONS), 30)
        self.assertEqual(region_sites(ROOMS), Counter({k: 180 for k in KINDS}))
        for region in REGIONS:
            local = {room_id(region.key, x, y): ROOMS[room_id(region.key, x, y)]
                     for y in range(HEIGHT) for x in range(WIDTH)}
            self.assertEqual(region_sites(local), Counter({k: 6 for k in KINDS}))
            self.assertEqual(len(local), 48)
            self.assertEqual(sum(1 for r in local.values() if 'v115_profession_site' in r), 24)

    def test_real_sites_contain_useful_audio_free_text(self):
        for region in REGIONS:
            for y in range(HEIGHT):
                for x in range(WIDTH):
                    rid = room_id(region.key, x, y)
                    site = site_for_room(rid, ROOMS[rid])
                    expected = site_for_sector(region.key, x, y)
                    self.assertEqual(site, expected)
                    if site:
                        self.assertIn(site['name'], ROOMS[rid]['desc'])
                        self.assertIn('Komenda:', ROOMS[rid]['desc'])
                        self.assertNotIn('sound', str(site).lower())

    def test_reject_forged_sites_and_other_terrain(self):
        example = site_for_sector(REGIONS[0].key, 0, 0)
        self.assertIsNone(site_for_room('graveyard', {'v115_region_key': REGIONS[0].key,
                                      'v115_profession_site': example}))
        self.assertIsNone(site_for_room('v115_region_01_p_99_99', {
            'v115_region_key': REGIONS[0].key, 'v115_profession_site': example}))
        self.assertIsNone(site_for_room('v115_region_01_p_00_00', {
            'v115_region_key': REGIONS[0].key, 'v115_profession_site': {'kind': 'mining'}}))
        self.assertFalse(has_site('crossroads', ROOMS['crossroads'], 'mining'))

    def test_sites_are_single_profession_only(self):
        for region in REGIONS:
            for y in range(HEIGHT):
                for x in range(WIDTH):
                    rid = room_id(region.key, x, y)
                    for kind in KINDS:
                        self.assertEqual(has_site(rid, ROOMS[rid], kind),
                                         bool(site_for_room(rid, ROOMS[rid]) and
                                              site_for_room(rid, ROOMS[rid])['kind'] == kind))

    def test_fishing_habitats_and_water_labels(self):
        for region in REGIONS:
            rid = next(room_id(region.key, x, y) for y in range(HEIGHT) for x in range(WIDTH)
                       if has_site(room_id(region.key,x,y),ROOMS[room_id(region.key,x,y)],'fishing'))
            dummy = _Probe(rid)
            habitat = SessionGatheringMixin.fishing_habitat(dummy)
            label = SessionGatheringMixin.fishing_water_type(dummy)
            self.assertIn(habitat, ('river','lake','sea','ocean'))
            self.assertIn(label, ('Rzeka','Jezioro','Morze','Ocean'))
            self.assertIsNotNone(habitat)

    def test_each_existing_command_recognizes_site_but_still_requires_existing_tool(self):
        actions = {'fishing': (SessionGatheringActionsMixin.fish, 'Wędki'),
                   'mining': (SessionGatheringActionsMixin.mine, 'Kilofa'),
                   'woodcutting': (SessionGatheringActionsMixin.woodcut, 'Piły'),
                   'herbalism': (SessionGatheringActionsMixin.gather_herb, 'Sierpa')}
        region=REGIONS[0]
        for kind, (method, expected_message) in actions.items():
            with self.subTest(kind=kind):
                rid=next(room_id(region.key, x, y) for y in range(HEIGHT) for x in range(WIDTH)
                         if has_site(room_id(region.key,x,y),ROOMS[room_id(region.key,x,y)],kind))
                dummy = _Probe(rid)
                asyncio.run(method(dummy))
                self.assertEqual(len(dummy.sent),1)
                self.assertIn(expected_message, dummy.sent[0])
                old = _Probe('crossroads')
                asyncio.run(method(old))
                self.assertEqual(len(old.sent),1)
                self.assertNotIn(expected_message,old.sent[0])

    def test_real_existing_resource_pools_yield_an_item(self):
        from data.items import ITEMS
        class Professional(SessionGatheringMixin):
            def __init__(self, rid):
                self.character = SimpleNamespace(room_id=rid)
        for region in REGIONS:
            for kind in KINDS:
                rid = next(room_id(region.key, x, y) for y in range(HEIGHT) for x in range(WIDTH)
                           if has_site(room_id(region.key,x,y), ROOMS[room_id(region.key,x,y)], kind))
                actor = Professional(rid)
                if kind == 'fishing':
                    item = actor.fishing_loot(1, actor.fishing_habitat())
                elif kind == 'mining':
                    item = actor.mining_loot(1, rid)
                elif kind == 'woodcutting':
                    item = actor.woodcutting_loot(1, rid)
                else:
                    item = actor.herbalism_loot(1, rid)
                with self.subTest(region=region.key, kind=kind):
                    self.assertIn(item, ITEMS)

    def test_old_fishing_contract_and_tools_preserved(self):
        from pathlib import Path
        from validation.current_native_v420_contract import verify_native_method
        from core.progression_resources import (
            FISHING_ROOMS, WOODCUTTING_ROOMS, HERBALISM_ROOMS
        )
        root = Path(__file__).resolve().parents[1]
        self.assertTrue(verify_native_method(
            root / 'player/session_mixins/gathering.py',
            'SessionGatheringMixin.fishing_water_type'))
        self.assertIn('riverbank', FISHING_ROOMS)
        self.assertIn('lumberjack_camp', WOODCUTTING_ROOMS)
        self.assertIn('meadow', HERBALISM_ROOMS)
        self.assertNotIn('crossroads', FISHING_ROOMS)

    def test_no_new_tool_or_new_sound_imports(self):
        from systems.v115 import profession_sites, playable_regions
        for module in (profession_sites,playable_regions):
            source = inspect.getsource(module)
            self.assertNotIn('sound_events',source)
            self.assertNotIn('SOUND_EVENT',source)
            self.assertNotIn('add_item(',source)

if __name__ == '__main__':
    unittest.main()
