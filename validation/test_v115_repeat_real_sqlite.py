# -*- coding: utf-8 -*-
"""Real SQLite character fixture: immediate repeat EXP and old queued rewards."""
from types import SimpleNamespace
from unittest.mock import patch
from validation.test_v115_end_to_end_sqlite_payout import V115RealDbAward
from systems.v115 import fame_combat_runtime, fame_combat_capture, fame_queue
from systems.v115.fame_snapshot_delivery import deliver_stored_for_online_player
from systems.combat_kill_settlement_v10400 import settle_combat_full_progression_v10400


class V115RealRepeatAward(V115RealDbAward):
    def setUp(self):
        super().setUp()
        self.char.name = 'BohaterTest'

    def _stage_repeat(self, now=400):
        player=SimpleNamespace(account_id=1, character=self.char)
        mob=SimpleNamespace(room_id='test_region',home_room_id='test_region',template_id='boss')
        args=dict(character_xp=180,soul_xp=180,class_xp=180,stat_xp=180,
                  class_levels=(('Wojownik',1),),class_max_level=800,overcap=False,now=now)
        with patch.object(fame_combat_runtime,'resolve_fame_objective',return_value=('Kraina','boss')), \
             patch.object(fame_combat_capture,'resolve_fame_objective',return_value=('Kraina','boss')):
            with self.db.conn.deferred_commits():
                delayed=fame_combat_runtime.stage_delayed_first_clear(self.db.conn,player,mob,{'name':'Boss','rank':'boss'},**args)
                settle_combat_full_progression_v10400(self.db,self.char,1,
                    silver=4,character_xp=args['character_xp'],
                    soul_xp=args['soul_xp'],
                    class_xp=args['class_xp'],
                    stat_xp=args['stat_xp'],
                    class_levels=args['class_levels'],overcap=False,class_max_level=800)
        return delayed

    def test_repeat_xp_immediate_and_does_not_add_fame(self):
        with patch('player.character.character_xp_to_next', return_value=100), \
             patch('storage.db_progression.class_mastery_xp_to_next',return_value=1000):
            due=self._stage()
            self.assertEqual('exp',deliver_stored_for_online_player(self.db,self.char,1,now=due)[0][0])
            self.assertEqual('fame',deliver_stored_for_online_player(self.db,self.char,1,now=due+2)[0][0])
            self.assertEqual(1,self.db.conn.execute('SELECT COUNT(*) FROM fame_bosses_v1702').fetchone()[0])
            before=self.balance('character')
            self.assertTrue(self._stage_repeat(now=due+5))
            self.assertGreater(self.balance('character'),before)
            self.assertEqual([],deliver_stored_for_online_player(self.db,self.char,1,now=due+306))
            self.assertEqual(1,self.db.conn.execute('SELECT COUNT(*) FROM fame_bosses_v1702').fetchone()[0])
            self.assertEqual([],deliver_stored_for_online_player(self.db,self.char,1,now=due+309))

    def test_old_queued_repeat_still_paid_once_after_upgrade(self):
        # A v116.46 repeat row already on disk must not be dropped.
        from systems.v115.fame_repeat_rewards import stage_repeat_exp
        from systems.v115.fame_reward_snapshot import RewardSnapshot
        with patch('player.character.character_xp_to_next',return_value=100), \
             patch('storage.db_progression.class_mastery_xp_to_next',return_value=1000):
            due=self._stage()
            deliver_stored_for_online_player(self.db,self.char,1,now=due)
            deliver_stored_for_online_player(self.db,self.char,1,now=due+2)
            before=self.balance('character')
            plan=RewardSnapshot(180,180,180,180,(('Wojownik',1),),800,False,'BohaterTest',True)
            token,_=stage_repeat_exp(self.db.conn,1,'Kraina','boss','Boss',plan,now=due+4)
            paid=deliver_stored_for_online_player(self.db,self.char,1,now=due+900)
            self.assertEqual(['exp'],[event[0] for event in paid])
            self.assertGreater(self.balance('character'),before)
            self.assertEqual([],deliver_stored_for_online_player(self.db,self.char,1,now=due+903))
            self.assertEqual('DONE', self.db.conn.execute('SELECT status FROM v115_fame_repeat_exp WHERE kill_token=?',(token,)).fetchone()[0])
