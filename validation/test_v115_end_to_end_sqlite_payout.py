# -*- coding: utf-8 -*-
"""Real character + SQLite/EXP Bank fixture, no network, audio or live user DB."""
from types import SimpleNamespace
from unittest.mock import patch
from validation.test_v10400_full_kill_atomic import FullKillAtomic
from systems.v115 import fame_combat_runtime, fame_combat_capture, fame_queue
from systems.v115.fame_snapshot_delivery import deliver_stored_for_online_player
from systems.combat_kill_settlement_v10400 import settle_combat_full_progression_v10400


class V115RealDbAward(FullKillAtomic):
    def _stage(self):
        player = SimpleNamespace(account_id=1, character=self.char)
        mob = SimpleNamespace(room_id='test_region',home_room_id='test_region',template_id='boss')
        args = dict(character_xp=200,soul_xp=200,class_xp=200,stat_xp=200,
                    class_levels=(('Wojownik',1),),class_max_level=800,overcap=False,now=100)
        with patch.object(fame_combat_runtime, 'resolve_fame_objective', return_value=('Kraina','boss')), \
             patch.object(fame_combat_capture, 'resolve_fame_objective', return_value=('Kraina','boss')):
            with self.db.conn.deferred_commits():
                # Regression for already-queued legacy v115/v116.46 payouts.
                # Old saves still contain their ordinary EXP until this clears.
                first = fame_combat_capture.stage_final_combat_reward(
                    self.db.conn, player, mob, {'name':'Boss','rank':'boss'}, **args)
                settle_combat_full_progression_v10400(
                    self.db,self.char,1,silver=11,gold=0,mithril=0,
                    character_xp=0 if first else args['character_xp'],
                    soul_xp=0 if first else args['soul_xp'],
                    class_xp=0 if first else args['class_xp'],
                    stat_xp=0 if first else args['stat_xp'],
                    class_levels=args['class_levels'],overcap=False,class_max_level=800)
        due=self.db.conn.execute('SELECT due_at FROM v115_fame_delivery').fetchone()[0]
        return due

    def test_money_now_xp_later_fame_last_once(self):
        with patch('player.character.character_xp_to_next', return_value=100), \
             patch('storage.db_progression.class_mastery_xp_to_next', return_value=1000):
            due = self._stage()
            self.assertEqual(self.saved('silver','character_level','soul_level'),(111,2,2))
            self.assertEqual(self.balance('character'),0)
            self.assertEqual(self.balance('class','Wojownik'),0)
            self.assertEqual(self.balance('soul'),0)
            self.assertEqual([],deliver_stored_for_online_player(self.db,self.char,1,now=due-1))
            self.assertEqual('exp',deliver_stored_for_online_player(self.db,self.char,1,now=due)[0][0])
            self.assertEqual([],deliver_stored_for_online_player(self.db,self.char,1,now=due+1))
            self.assertEqual('fame',deliver_stored_for_online_player(self.db,self.char,1,now=due+2)[0][0])
            self.assertEqual([],deliver_stored_for_online_player(self.db,self.char,1,now=due+100))
            self.assertEqual(self.db.conn.execute('SELECT COUNT(*) FROM fame_bosses_v1702').fetchone()[0],1)
            self.assertEqual(self.db.conn.execute('SELECT status FROM v115_fame_delivery').fetchone()[0],'DONE')
            self.assertGreater(self.balance('character'),0)
            self.assertGreater(self.balance('soul'),0)
            self.assertGreater(self.balance('class','Wojownik'),0)

    def test_failed_delayed_class_award_keeps_queue_and_all_xp(self):
        with patch('player.character.character_xp_to_next', return_value=100), \
             patch('storage.db_progression.class_mastery_xp_to_next', return_value=1000):
            due = self._stage()
            before = (self.char.character_level, self.char.soul_level, self.char.character_xp)
            self.db.conn.execute("CREATE TRIGGER reject_class_v115 BEFORE INSERT ON class_progress BEGIN SELECT RAISE(ABORT, 'class payout failed'); END")
            with self.assertRaises(Exception):
                deliver_stored_for_online_player(self.db,self.char,1,now=due)
            self.assertEqual(self.db.conn.execute('SELECT status FROM v115_fame_delivery').fetchone()[0],'WAITING')
            self.assertEqual(self.balance('character'),0)
            self.assertEqual(self.balance('soul'),0)
            self.assertEqual(self.balance('class','Wojownik'),0)
            self.assertEqual((self.char.character_level,self.char.soul_level,self.char.character_xp),before)
            self.db.conn.execute('DROP TRIGGER reject_class_v115')
            self.assertEqual('exp',deliver_stored_for_online_player(self.db,self.char,1,now=due)[0][0])



if __name__=='__main__':
    import unittest
    unittest.main()
