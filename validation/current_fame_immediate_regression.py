# -*- coding: utf-8 -*-
"""v116.00.47: immediate ordinary EXP, independent deferred Fame, old debts safe."""
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from validation.test_v10400_full_kill_atomic import FullKillAtomic
from systems.v115 import fame_combat_runtime, fame_queue
from systems.v115.fame_reward_snapshot import load_snapshot
from systems.v115.fame_snapshot_delivery import deliver_stored_for_online_player
from systems.combat_kill_settlement_v10400 import settle_combat_full_progression_v10400


class FameInstant11647(FullKillAtomic):
    def setUp(self):
        super().setUp()
        self.char.name='Tester'
        self.db.multi_cap_v23215=lambda account_id: 40
        self.mob=SimpleNamespace(room_id='room',home_room_id='room',template_id='boss')
        self.session=SimpleNamespace(account_id=1,character=self.char)
        self.template={'name':'Naturalny boss','rank':'boss'}
        self.inputs=dict(character_xp=200,soul_xp=200,class_xp=200,stat_xp=200,
                         class_levels=(('Wojownik',1),),class_max_level=800,overcap=False)

    def award_kill(self, now):
        with patch.object(fame_combat_runtime,'resolve_fame_objective',return_value=('Kraina','boss')):
            with self.db.conn.deferred_commits():
                staged=fame_combat_runtime.stage_delayed_first_clear(
                    self.db.conn,self.session,self.mob,self.template,now=now,**self.inputs)
                assert staged
                reward=settle_combat_full_progression_v10400(
                    self.db,self.char,1,silver=11,**self.inputs)
        return reward

    def test_first_kill_immediate_then_only_fame_bonus_later(self):
        with patch('player.character.character_xp_to_next',return_value=100), \
             patch('storage.db_progression.class_mastery_xp_to_next',return_value=1000):
            first=self.award_kill(100)
            self.assertGreater(first['character'][0],0)
            self.assertGreater(first['soul'][0],0)
            self.assertEqual(111,self.saved('silver')[0])
            snapshot=load_snapshot(self.db.conn,1,'Kraina','boss')
            self.assertEqual((0,0,0,0),(snapshot.character_xp,snapshot.soul_xp,snapshot.class_xp,snapshot.stat_xp))
            due=self.db.conn.execute('SELECT due_at FROM v115_fame_delivery').fetchone()[0]
            before=self.balance('character')
            self.assertEqual([],deliver_stored_for_online_player(self.db,self.char,1,now=due-1))
            ev=deliver_stored_for_online_player(self.db,self.char,1,now=due)
            self.assertEqual(['exp'],[x[0] for x in ev])
            self.assertEqual(False,ev[0][4]['fame_normal_exp_deferred'])
            self.assertEqual(40,ev[0][4]['fame_bonus_cap'])
            self.assertGreaterEqual(self.balance('character'),before)
            self.assertEqual(['fame'],[x[0] for x in deliver_stored_for_online_player(self.db,self.char,1,now=due+2)])
            self.assertEqual([],deliver_stored_for_online_player(self.db,self.char,1,now=due+3))
            self.assertEqual(1,self.db.conn.execute('SELECT count(*) FROM fame_bosses_v1702').fetchone()[0])
            before_repeat=self.balance('character')
            self.award_kill(due+4)
            self.assertGreater(self.balance('character'),before_repeat)
            self.assertEqual([],deliver_stored_for_online_player(self.db,self.char,1,now=due+300))
            self.assertIsNone(self.db.conn.execute("SELECT 1 FROM sqlite_master WHERE name='v115_fame_repeat_exp'").fetchone())
            self.assertEqual(1,self.db.conn.execute('SELECT count(*) FROM fame_bosses_v1702').fetchone()[0])

    def test_old_queue_still_awards_original_xp_once(self):
        from systems.v115.fame_reward_snapshot import RewardSnapshot,stage_with_snapshot
        old=RewardSnapshot(75,75,75,75,(('Wojownik',1),),800,False,'Tester',True)
        with self.db.conn.deferred_commits():
            self.assertTrue(stage_with_snapshot(self.db.conn,1,'Stara kraina','stary boss','Stary boss',old,now=100))
        due=self.db.conn.execute("SELECT due_at FROM v115_fame_delivery WHERE boss_id='stary boss'").fetchone()[0]
        with patch('player.character.character_xp_to_next',return_value=100), \
             patch('storage.db_progression.class_mastery_xp_to_next',return_value=1000):
            event=deliver_stored_for_online_player(self.db,self.char,1,now=due)
            self.assertEqual('exp',event[0][0])
            self.assertTrue(event[0][4]['fame_normal_exp_deferred'])
            self.assertEqual(40,event[0][4]['fame_bonus_cap'])
            self.assertEqual([],deliver_stored_for_online_player(self.db,self.char,1,now=due+1))
            self.assertEqual('fame',deliver_stored_for_online_player(self.db,self.char,1,now=due+2)[0][0])
            self.assertEqual([],deliver_stored_for_online_player(self.db,self.char,1,now=due+3))


def run():
    names=('test_first_kill_immediate_then_only_fame_bonus_later','test_old_queue_still_awards_original_xp_once')
    suite=unittest.TestSuite(FameInstant11647(n) for n in names)
    outcome=unittest.TextTestRunner(verbosity=2).run(suite)
    if not outcome.wasSuccessful():raise AssertionError('Fame 116.47 regression failed')
    return outcome.testsRun

if __name__=='__main__':
    print('v116.00.47 FAME:',run(),'PASS')
