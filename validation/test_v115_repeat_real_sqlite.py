# -*- coding: utf-8 -*-
"""Real SQLite character fixture: repeated Fame EXP remains delayed and durable."""
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
                    silver=4,character_xp=0 if delayed else args['character_xp'],
                    soul_xp=0 if delayed else args['soul_xp'],
                    class_xp=0 if delayed else args['class_xp'],
                    stat_xp=0 if delayed else args['stat_xp'],
                    class_levels=args['class_levels'],overcap=False,class_max_level=800)
        return delayed

    def test_repeat_xp_waits_and_does_not_add_fame(self):
        with patch('player.character.character_xp_to_next', return_value=100), \
             patch('storage.db_progression.class_mastery_xp_to_next',return_value=1000):
            due=self._stage()
            self.assertEqual('exp',deliver_stored_for_online_player(self.db,self.char,1,now=due)[0][0])
            self.assertEqual('fame',deliver_stored_for_online_player(self.db,self.char,1,now=due+2)[0][0])
            self.assertEqual(1,self.db.conn.execute('SELECT COUNT(*) FROM fame_bosses_v1702').fetchone()[0])
            before=self.balance('character')
            self.assertTrue(self._stage_repeat(now=due+5))
            self.assertEqual(before,self.balance('character'))
            self.assertEqual([],deliver_stored_for_online_player(self.db,self.char,1,now=due+6))
            paid=deliver_stored_for_online_player(self.db,self.char,1,now=due+306)
            self.assertEqual(['exp'],[v[0] for v in paid])
            self.assertGreater(self.balance('character'),before)
            self.assertEqual(1,self.db.conn.execute('SELECT COUNT(*) FROM fame_bosses_v1702').fetchone()[0])
            self.assertEqual([],deliver_stored_for_online_player(self.db,self.char,1,now=due+309))

    def test_two_overdue_repeat_awards_not_sent_together(self):
        with patch('player.character.character_xp_to_next',return_value=100), \
             patch('storage.db_progression.class_mastery_xp_to_next',return_value=1000):
            due=self._stage()
            deliver_stored_for_online_player(self.db,self.char,1,now=due)
            deliver_stored_for_online_player(self.db,self.char,1,now=due+2)
            self.assertTrue(self._stage_repeat(now=due+4))
            self.assertTrue(self._stage_repeat(now=due+5))
            self.assertEqual(2,self.db.conn.execute("SELECT count(*) FROM v115_fame_repeat_exp WHERE status='PENDING'").fetchone()[0])
            # Only one EXP event is sent per scheduler iteration, avoiding
            # overlapping soundpack notifications even after long downtime.
            first=deliver_stored_for_online_player(self.db,self.char,1,now=due+900)
            self.assertEqual(['exp'],[ev[0] for ev in first])
            self.assertEqual(1,self.db.conn.execute("SELECT count(*) FROM v115_fame_repeat_exp WHERE status='PENDING'").fetchone()[0])
            next_one=deliver_stored_for_online_player(self.db,self.char,1,now=due+903)
            self.assertEqual(['exp'],[ev[0] for ev in next_one])
            self.assertEqual(0,self.db.conn.execute("SELECT count(*) FROM v115_fame_repeat_exp WHERE status='PENDING'").fetchone()[0])
