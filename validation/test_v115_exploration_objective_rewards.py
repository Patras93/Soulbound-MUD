# -*- coding: utf-8 -*-
"""Tests v115 regional exploration objective activation, with real wallet SQLite."""
import unittest
import sqlite3
from types import SimpleNamespace
from validation.test_v10400_atomic_live_character_xp import fixture
from systems.v115.high_level_world import REGIONS
from systems.v115.playable_regions import room_id, build_rooms, WIDTH, HEIGHT
from systems.v115.exploration_objective_bridge import record_v115_room_visit
from systems.v115.objective_progress import total

REGION = REGIONS[0].key
ROOMS = build_rooms()

class RegionalExplorationRewards(unittest.TestCase):
    def setUp(self):
        self.db, self.character = fixture()
        self.session = SimpleNamespace(account_id=1,character=self.character,
                                       server=SimpleNamespace(db=self.db))
    def tearDown(self):
        self.db.conn.close()
    def visit(self,x,y):
        rid = room_id(REGION,x,y)
        return record_v115_room_visit(self.session,rid,ROOMS[rid])
    def wallet(self):
        return int(self.db.conn.execute('SELECT silver FROM account_wallet').fetchone()[0])
    def test_real_sqlite_three_rooms_complete_exploration_quest(self):
        self.visit(0,0)
        self.visit(1,0)
        self.visit(2,0)
        self.assertEqual(total(self.db.conn,1,REGION,'explore'),3)
        self.assertGreater(self.wallet(),100)
        self.assertEqual(self.wallet(),self.character.silver)
        self.assertEqual(self.db.conn.execute("SELECT count(*) FROM v115_objective_claims WHERE claim_key LIKE 'v115_quest_%'").fetchone()[0],3)
    def test_checkpoints_only_for_ep_landmark(self):
        self.visit(0,0)
        self.visit(1,0)
        self.visit(2,0)
        self.assertEqual(total(self.db.conn,1,REGION,'discover_checkpoint'),2)
    def test_duplicate_room_revisit_never_adds_progress_or_silver(self):
        self.assertEqual(self.visit(0,0)[0],2)
        first=self.wallet()
        self.assertEqual(self.visit(0,0),(0,0,0,0))
        self.assertEqual(self.wallet(),first)
        self.assertEqual(total(self.db.conn,1,REGION,'explore'),1)
    def test_other_accounts_separated(self):
        from systems.v115.objective_progress import record_event
        self.visit(0,0)
        with self.db.conn:
            self.assertTrue(record_event(self.db.conn,2,'v115:room:another:explore',REGION,'explore'))
        self.assertEqual(total(self.db.conn,1,REGION,'explore'),1)
        self.assertEqual(total(self.db.conn,2,REGION,'explore'),1)
    def test_unmarked_legacy_room_is_noop_no_schema(self):
        self.assertEqual(record_v115_room_visit(self.session,'graveyard',{'zone':'Cmentarz'}),(0,0,0,0))
        self.assertFalse(self.db.conn.execute("SELECT name FROM sqlite_master WHERE name='v115_objective_events'").fetchone())
    def test_invalid_authored_room_is_rejected(self):
        with self.assertRaises(ValueError):
            record_v115_room_visit(self.session,'forged', {'v115_region_key':REGION})
        with self.assertRaises(ValueError):
            record_v115_room_visit(self.session,room_id(REGION,0,0).replace('00_00','99_00'), {'v115_region_key':REGION})
    def test_failed_wallet_update_does_not_credit_objective(self):
        self.db.conn.execute("CREATE TRIGGER fail_visit_wallet BEFORE UPDATE ON account_wallet BEGIN SELECT RAISE(ABORT,'denied'); END")
        with self.assertRaises(sqlite3.IntegrityError):
            self.visit(0,0)
        self.assertEqual(self.wallet(),100)
        self.assertEqual(self.character.silver,100)
        self.assertEqual(total(self.db.conn,1,REGION,'explore'),0)
        self.db.conn.execute('DROP TRIGGER fail_visit_wallet')
        self.assertEqual(self.visit(0,0)[0],2)
        self.assertGreater(self.wallet(),100)
    def test_cross_account_mismatch_fails(self):
        self.character.account_id=2
        with self.assertRaises(ValueError):self.visit(0,0)
        self.assertEqual(self.wallet(),100)
    def test_every_region_has_24_landmarks_with_ep(self):
        for region in REGIONS:
            area=[room for name,room in ROOMS.items() if room.get('v115_region_key')==region.key]
            self.assertEqual(len(area),WIDTH*HEIGHT)
            self.assertEqual(sum(bool(room.get('v1000_landmark')) and room.get('exploration_ep',0)>0 for room in area),24)
    def test_soundpack_not_required(self):
        import inspect
        from systems.v115 import exploration_objective_bridge
        self.assertNotIn('sound_events', inspect.getsource(exploration_objective_bridge))
        self.assertNotIn('soundpack', inspect.getsource(exploration_objective_bridge).lower().replace('no soundpack',''))
    def test_hook_in_real_discovery_before_early_return(self):
        from pathlib import Path
        source=(Path(__file__).resolve().parents[1]/'player/session_mixins/exploration_progress.py').read_text('utf8')
        anchor='if not is_new:'
        self.assertIn('record_v115_room_visit(self, str(room_id), room_meta)', source)
        self.assertLess(source.index('record_v115_room_visit(self, str(room_id), room_meta)'),source.index(anchor,source.index('async def discover_room(')))
if __name__=='__main__':unittest.main()
