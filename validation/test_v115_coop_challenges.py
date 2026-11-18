# -*- coding: utf-8 -*-
"""v115 coop objectives: real party members only; regional guardian challenge."""
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from validation.test_v10400_atomic_live_character_xp import fixture
from systems.v115.high_level_world import REGIONS
from systems.v115.combat_objective_bridge import record_v115_victory
from systems.v115.objective_progress import total

REGION=REGIONS[0].key

class CooperationObjectives(unittest.TestCase):
    def setUp(self):
        self.db,self.c=fixture()
        self.c.room_id='arena'
        self.killer=SimpleNamespace(account_id=1,character=self.c)
        self.members=[self.killer]
        self.server=SimpleNamespace(db=self.db,party_sessions=lambda *args,**kwargs:self.members)
        self.killer.server=self.server
        self.mob=SimpleNamespace(alive=False,template_id=f'{REGION}_guardian')
        self.template={'v115_region_key':REGION,'boss':True}
    def tearDown(self):self.db.conn.close()

    def test_regional_guardian_is_a_challenge(self):
        with self.db.conn.deferred_commits():
            credited=record_v115_victory(self.killer,self.mob,self.template,event_id='guardian-1')
        self.assertEqual(credited,3)
        self.assertEqual(total(self.db.conn,1,REGION,'win_challenge'),1)
        self.assertEqual(total(self.db.conn,1,REGION,'help_party'),0)
        with self.db.conn.deferred_commits():
            self.assertEqual(record_v115_victory(self.killer,self.mob,self.template,event_id='guardian-1'),0)

    def test_non_guardian_boss_not_a_challenge(self):
        self.mob.template_id='legacy_boss'
        with self.db.conn.deferred_commits():
            self.assertEqual(record_v115_victory(self.killer,self.mob,self.template,event_id='boss'),2)
        self.assertEqual(total(self.db.conn,1,REGION,'win_challenge'),0)

    def test_teamwork_only_for_two_real_players_same_room(self):
        c2=SimpleNamespace(account_id=2,room_id='arena',silver=0,gold=0,mithril=0)
        member2=SimpleNamespace(account_id=2,character=c2)
        self.members.append(member2)
        self.mob.template_id='v115_region_01_patrol'
        captured=[]
        def fake_record(_conn, account_id, event_id, region, objective):
            captured.append((account_id,objective))
            return True
        with patch('systems.v115.combat_objective_bridge.record_event',side_effect=fake_record), \
             patch('systems.v115.combat_objective_bridge.settle_kill_objectives',return_value=(0,0,0)):
            self.assertEqual(record_v115_victory(self.killer,self.mob,{'v115_region_key':REGION},event_id='co-op'),4)
        self.assertEqual({x for x in captured if x[1]=='help_party'}, {(1,'help_party'),(2,'help_party')})

    def test_duplicate_account_is_not_second_player(self):
        self.members.append(SimpleNamespace(account_id=1,character=self.c))
        self.mob.template_id='v115_region_01_patrol'
        with self.db.conn.deferred_commits():
            self.assertEqual(record_v115_victory(self.killer,self.mob,{'v115_region_key':REGION},event_id='duplicate'),1)
        self.assertEqual(total(self.db.conn,1,REGION,'help_party'),0)

    def test_member_outside_room_not_counted(self):
        outsider=SimpleNamespace(account_id=2,character=SimpleNamespace(account_id=2,room_id='crossroads'))
        self.members.append(outsider)
        self.mob.template_id='v115_region_01_patrol'
        with self.db.conn.deferred_commits():
            self.assertEqual(record_v115_victory(self.killer,self.mob,{'v115_region_key':REGION},event_id='outside'),1)
        self.assertEqual(total(self.db.conn,1,REGION,'help_party'),0)

    def test_old_mob_does_nothing(self):
        self.assertEqual(record_v115_victory(self.killer,self.mob,{},event_id='old'),0)

if __name__=='__main__':unittest.main()
