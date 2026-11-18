# -*- coding: utf-8 -*-
"""Never deposit delayed EXP into another character of the same account."""
import sqlite3
import unittest
from types import SimpleNamespace
from unittest.mock import patch
from systems.v115 import fame_exp_progression, fame_queue
from systems.v115.fame_reward_snapshot import RewardSnapshot, load_snapshot
from systems.v115.fame_snapshot_delivery import stage_first_clear, deliver_stored_for_online_player


class Connection:
    def __init__(self):
        self.raw = sqlite3.connect(":memory:")
    def __getattr__(self, key):
        return getattr(self.raw, key)
    def deferred_commits(self):
        conn = self.raw
        class Transaction:
            def __enter__(self): return conn
            def __exit__(self, etype, val, tb):
                if etype: conn.rollback()
                else: conn.commit()
        return Transaction()


class CharacterOwnershipTests(unittest.TestCase):
    def setUp(self):
        self.conn = Connection()
        self.db = SimpleNamespace(conn=self.conn)
        self.plan = RewardSnapshot(101, 102, 103, 104, (("Mage", 801),), 99999, False,
                                   character_name="ElizaTest")
        self.assertTrue(stage_first_clear(self.conn, 17, "Region", "boss", "Boss", self.plan, now=100))
        self.conn.commit()
        self.due = self.conn.execute("SELECT due_at FROM v115_fame_delivery").fetchone()[0]
    def tearDown(self):
        self.conn.raw.close()

    def test_wrong_character_cannot_receive_experience(self):
        fake = SimpleNamespace(account_id=17, name="OtherHero")
        with patch.object(fame_exp_progression, 'settle_fame_exp_progression', side_effect=AssertionError('wrong payout')):
            self.assertEqual([], deliver_stored_for_online_player(self.db, fake, 17, now=self.due))
        self.assertEqual('WAITING', self.conn.execute('SELECT status FROM v115_fame_delivery').fetchone()[0])

    def test_correct_character_gets_exactly_one_payout(self):
        original = SimpleNamespace(account_id=17, name="ElizaTest")
        paid = []
        def award(db, character, account, region, boss, **kwargs):
            def callback(conn, val):
                paid.append(kwargs['character_xp'])
            ok = fame_queue.settle_exp(db.conn, account, region, boss, callback, now=kwargs['now'])
            db.conn.commit()
            return {'paid': True} if ok else None
        with patch.object(fame_exp_progression,'settle_fame_exp_progression', award):
            self.assertEqual('exp', deliver_stored_for_online_player(self.db,original,17,now=self.due)[0][0])
            self.assertEqual([],deliver_stored_for_online_player(self.db,original,17,now=self.due+1))
        self.assertEqual([101],paid)

    def test_restart_snapshot_preserves_name(self):
        self.assertEqual('ElizaTest', load_snapshot(self.conn,17,'Region','boss').character_name)

    def test_different_recipient_name_is_not_silently_replaced(self):
        other = RewardSnapshot(101,102,103,104,(("Mage",801),),99999,False,
                               character_name="OtherHero")
        with self.assertRaises(ValueError):
            stage_first_clear(self.conn,17,'Region','boss','Boss',other,now=101)


if __name__ == '__main__': unittest.main()
