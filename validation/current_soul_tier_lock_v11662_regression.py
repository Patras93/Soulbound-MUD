# -*- coding: utf-8 -*-
"""Soul Tier lock: no NEW Soul XP, no bank deposits, safe saved history.

Private in-memory SQLite, no production DB / sockets / deployment.
"""
from __future__ import annotations

import asyncio
import sqlite3
import unittest
from types import MethodType, SimpleNamespace
from unittest.mock import patch

from player.character import Character
from systems.atomic_progression_rewards_v10400 import award_soul_xp_atomic_v10400
from systems.manual_exp_bank_v11325 import redeem_exp_bank
from validation.test_v10400_atomic_live_character_xp import fixture


class SoulTierNoNewXP(unittest.TestCase):
    @staticmethod
    def actor(level=90, tier=8, xp=12345):
        char = object.__new__(Character)
        char.soul_level, char.soul_tier, char.soul_xp = level, tier, xp
        char.race = 'Człowiek'
        char._guild_bonus_percent = 0
        char.racial_soul_xp_multiplier = lambda: 1.0
        return char

    def test_locked_direct_reward_does_not_accumulate(self):
        c = self.actor()
        self.assertTrue(c.soul_progress_is_tier_locked())
        for amount in (1, 100, 10**12, 0):
            messages = c.add_soul_xp(amount)
            self.assertEqual((c.soul_level, c.soul_tier, c.soul_xp), (90, 8, 12345))
            self.assertIn('nie naliczono', ' '.join(messages))
        c.soul_tier = 9
        self.assertFalse(c.soul_progress_is_tier_locked())
        c.add_soul_xp(100)
        self.assertEqual(c.soul_xp, 12445)

    def test_first_award_that_reaches_lock_preserves_prior_earned_xp(self):
        c = self.actor(level=89, tier=8, xp=0)
        needed = c.soul_xp_to_next()
        c.add_soul_xp(needed + 13)
        self.assertEqual((c.soul_level, c.soul_xp), (90, 13))
        self.assertTrue(c.soul_progress_is_tier_locked())
        c.add_soul_xp(20_000)
        self.assertEqual(c.soul_xp, 13)
        c.soul_tier = 9
        c.add_soul_xp(1)
        self.assertEqual(c.soul_xp, 14)

    def test_atomic_gateway_bypasses_both_bank_modes(self):
        db, c = fixture()
        try:
            c.soul_level, c.soul_tier, c.soul_xp = 90, 8, 445
            c.soul_progress_is_tier_locked = MethodType(Character.soul_progress_is_tier_locked, c)
            c.soul_level_cap_for_current_tier = MethodType(Character.soul_level_cap_for_current_tier, c)
            c.add_soul_xp = MethodType(Character.add_soul_xp, c)
            db.conn.execute("UPDATE characters SET soul_level=90,soul_tier=8,soul_xp=445 WHERE account_id=1")
            db.conn.execute("INSERT INTO experience_bank_v2011 VALUES(1,'soul','','987')")
            db.conn.commit()
            for manual in (True, False):
                db._manual_bank_only_v11325 = manual
                for extra in (False, True):
                    paid, notes = award_soul_xp_atomic_v10400(db, c, 1, 1_000_000,
                                                              overcap=extra)
                    self.assertEqual(paid, 0)
                    self.assertIn('nie naliczono', ' '.join(notes))
                    self.assertEqual(c.soul_xp, 445)
                    self.assertEqual(db.conn.execute("SELECT soul_xp FROM characters WHERE account_id=1").fetchone()[0], 445)
                    self.assertEqual(db.conn.execute("SELECT balance FROM experience_bank_v2011 WHERE account_id=1 AND kind='soul'").fetchone()[0], '987')
        finally:
            db.conn.close()

    def test_manual_bank_claim_waits_for_unlock(self):
        from storage.database import _DeferredCommitConnection
        base = sqlite3.connect(':memory:')
        db = SimpleNamespace(conn=_DeferredCommitConnection(base))
        db.conn.execute('CREATE TABLE experience_bank_v2011(account_id INTEGER,kind TEXT,source_key TEXT,balance TEXT,PRIMARY KEY(account_id,kind,source_key))')
        db.conn.execute("INSERT INTO experience_bank_v2011 VALUES(1,'soul','','4000')")
        db.conn.commit()
        db.experience_bank_rows_v2011 = lambda aid: [
            ('soul', '', int(r[0])) for r in db.conn.execute(
                "SELECT balance FROM experience_bank_v2011 WHERE account_id=? AND kind='soul'", (aid,))]
        db.save_character = lambda char, commit=False: None
        c = self.actor(xp=100)
        c.account_id = 1
        c.add_soul_xp = MethodType(Character.add_soul_xp, c)
        sent = []
        sess = SimpleNamespace(server=SimpleNamespace(db=db), account_id=1,
                               character=c, send=lambda msg: sent.append(msg))
        async def send(msg): sent.append(str(msg))
        sess.send = send
        try:
            with patch('systems.multi_cap_v23215.multi_cap_experience_v23215', return_value=100):
                asyncio.run(redeem_exp_bank(sess, all_balances=True))
            self.assertEqual(c.soul_xp, 100)
            self.assertEqual(db.conn.execute("SELECT balance FROM experience_bank_v2011").fetchone()[0], '4000')
            self.assertTrue(any('Pozostało w banku' in x for x in sent))
            c.soul_tier = 9
            with patch('systems.multi_cap_v23215.multi_cap_experience_v23215', return_value=100):
                asyncio.run(redeem_exp_bank(sess, all_balances=True))
            self.assertEqual(c.soul_xp, 4100)
            self.assertEqual(db.conn.execute("SELECT balance FROM experience_bank_v2011").fetchone()[0], '0')
        finally:
            db.conn.close()


def run():
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(SoulTierNoNewXP)
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    if not result.wasSuccessful():
        raise AssertionError('Soul Tier no new XP regression FAIL')
    return result.testsRun


if __name__ == '__main__':
    print(f'SOUL TIER LOCK NO NEW XP v116.00.62: {run()}/4 PASS', flush=True)
