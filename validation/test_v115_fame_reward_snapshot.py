import os
import sqlite3
import tempfile
import unittest
from systems.v115 import fame_reward_snapshot as snap
from systems.v115 import fame_queue


class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = os.path.join(self.tmp.name, 'game.sqlite')
        self.conn = sqlite3.connect(self.path)
        self.plan = snap.RewardSnapshot(110, 200, 300, 400, (('Mage', 801),), 1000000, True)

    def tearDown(self):
        self.conn.close()
        self.tmp.cleanup()

    def test_all_axes_roundtrip(self):
        self.assertTrue(snap.stage_with_snapshot(self.conn, 1, 'Kraina', 'boss', 'Boss', self.plan, now=100))
        self.assertEqual(snap.load_snapshot(self.conn, 1, 'Kraina', 'boss'), self.plan)

    def test_no_award_before_60_seconds(self):
        snap.stage_with_snapshot(self.conn, 1, 'Kraina', 'boss', 'Boss', self.plan, now=100)
        self.assertFalse(fame_queue.due_events(self.conn, 1, now=159))

    def test_retry_is_idempotent(self):
        snap.stage_with_snapshot(self.conn, 1, 'Kraina', 'boss', 'Boss', self.plan, now=100)
        self.assertFalse(snap.stage_with_snapshot(self.conn, 1, 'Kraina', 'boss', 'Boss', self.plan, now=100))
        self.assertEqual(self.conn.execute('SELECT COUNT(*) FROM v115_fame_reward_snapshot').fetchone()[0], 1)

    def test_retry_with_changed_exp_rejected(self):
        snap.stage_with_snapshot(self.conn, 1, 'Kraina', 'boss', 'Boss', self.plan, now=100)
        altered = snap.RewardSnapshot(111, 200, 300, 400, (('Mage', 801),), 1000000, True)
        with self.assertRaises(ValueError):
            snap.stage_with_snapshot(self.conn, 1, 'Kraina', 'boss', 'Boss', altered, now=101)
        self.assertEqual(snap.load_snapshot(self.conn, 1, 'Kraina', 'boss'), self.plan)

    def test_invalid_plan_rolls_back_queue(self):
        bad = snap.RewardSnapshot(0, 0, 0, 0, (), 1, False)
        with self.assertRaises(ValueError):
            snap.stage_with_snapshot(self.conn, 1, 'Kraina', 'boss', 'Boss', bad, now=100)
        self.assertEqual(self.conn.execute('SELECT COUNT(*) FROM v115_fame_delivery').fetchone()[0], 0)

    def test_persists_restart(self):
        snap.stage_with_snapshot(self.conn, 1, 'Kraina', 'boss', 'Boss', self.plan, now=100)
        self.conn.commit()
        self.conn.close()
        self.conn = sqlite3.connect(self.path)
        self.assertEqual(snap.load_snapshot(self.conn, 1, 'Kraina', 'boss'), self.plan)

    def test_different_players_independent(self):
        snap.stage_with_snapshot(self.conn, 1, 'Kraina', 'boss', 'Boss', self.plan, now=100)
        snap.stage_with_snapshot(self.conn, 2, 'Kraina', 'boss', 'Boss', self.plan, now=100)
        self.assertEqual(self.conn.execute('SELECT COUNT(*) FROM v115_fame_reward_snapshot').fetchone()[0], 2)

    def test_audio_independent(self):
        import inspect
        self.assertNotIn('sound_events', inspect.getsource(snap))

    def test_reject_bad_class_configuration(self):
        with self.assertRaises(ValueError):
            snap.RewardSnapshot(1, 1, 1, 1, (), 800, False).validate()


if __name__ == '__main__':
    unittest.main()
