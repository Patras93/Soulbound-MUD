# -*- coding: utf-8 -*-
import sqlite3
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from systems.v115 import fame_combat_capture


class Tests(unittest.TestCase):
    def setUp(self):
        self.conn=sqlite3.connect(':memory:')
        self.session=SimpleNamespace(account_id=13,character=SimpleNamespace(account_id=13))
        self.mob=SimpleNamespace(template_id='boss',room_id='r',home_room_id='r')
        self.reward=dict(character_xp=120,soul_xp=30,class_xp=20,stat_xp=10,
                         class_levels=(('Mage',800),),class_max_level=100000,
                         overcap=False,now=1000)
        self.patcher=patch.object(fame_combat_capture,'resolve_fame_objective',return_value=('Region','boss'))
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()
        self.conn.close()

    def stage(self, **overrides):
        kw=dict(self.reward)
        kw.update(overrides)
        return fame_combat_capture.stage_final_combat_reward(
            self.conn,self.session,self.mob,{'name':'Boss'},**kw)

    def test_first_clear_is_staged_not_paid(self):
        self.assertTrue(self.stage())
        self.assertEqual(self.conn.execute('SELECT status FROM v115_fame_delivery').fetchone()[0],'WAITING')
        self.assertFalse(self.conn.execute("SELECT 1 FROM sqlite_master WHERE name='fame_bosses_v1702'").fetchone())
        self.assertEqual(self.conn.execute('SELECT COUNT(*) FROM v115_fame_reward_snapshot').fetchone()[0],1)

    def test_duplicate_does_not_duplicate(self):
        self.assertTrue(self.stage())
        self.assertFalse(self.stage())
        self.assertEqual(self.conn.execute('SELECT COUNT(*) FROM v115_fame_delivery').fetchone()[0],1)

    def test_conflicting_duplicate_refused(self):
        self.stage()
        with self.assertRaises(ValueError): self.stage(character_xp=121)

    def test_legacy_fame_not_recredited(self):
        self.conn.execute('CREATE TABLE fame_bosses_v1702(account_id INTEGER,region TEXT,boss_id TEXT)')
        self.conn.execute("INSERT INTO fame_bosses_v1702 VALUES(13,'Region','boss')")
        self.assertFalse(self.stage())

    def test_rollbacks_do_not_leave_queue(self):
        self.conn.execute('SAVEPOINT kill')
        self.stage()
        self.conn.execute('ROLLBACK TO kill')
        self.conn.execute('RELEASE kill')
        self.assertFalse(self.conn.execute("SELECT 1 FROM sqlite_master WHERE name='v115_fame_delivery'").fetchone())

    def test_invalid_reward_never_staged(self):
        with self.assertRaises(ValueError): self.stage(character_xp=-1)
        self.assertFalse(self.conn.execute("SELECT 1 FROM sqlite_master WHERE name='v115_fame_delivery'").fetchone())

    def test_mismatched_character_never_staged(self):
        self.session.character.account_id=99
        with self.assertRaises(ValueError): self.stage()

    def test_non_fame_unchanged(self):
        with patch.object(fame_combat_capture,'resolve_fame_objective',return_value=None):
            self.assertFalse(self.stage())
        self.assertFalse(self.conn.execute("SELECT 1 FROM sqlite_master WHERE name='v115_fame_delivery'").fetchone())

    def test_real_eligibility_rejects_common_mob(self):
        self.patcher.stop()
        try:
            self.assertIsNone(fame_combat_capture.resolve_fame_objective(self.mob, {'rank':'normal'}))
        finally:
            self.patcher.start()

if __name__=='__main__': unittest.main()
