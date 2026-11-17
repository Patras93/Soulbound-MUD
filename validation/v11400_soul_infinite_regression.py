# -*- coding: utf-8 -*-
"""Non-production regression for v114 Soul Tier arithmetic and progression.

Run from repository root with SOULBOUND_V106_STAGING=1 during WIP so the
legacy 6000-tier catalogue is present without touching any real DB or port.
"""
from __future__ import annotations
import asyncio
import os
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from core import progression_600 as p
from player import character as character_module
from player.session_mixins.skill_learning import SessionSkillLearningMixin


class DummyDb:
    def __init__(self): self.saved = []
    def save_character(self, c): self.saved.append(c.soul_tier)


class DummyServer:
    def __init__(self): self.db = DummyDb(); self.broadcasts=[]
    async def broadcast_room(self, room_id, message, **kwargs):
        self.broadcasts.append((room_id, message))


class DummySession(SessionSkillLearningMixin):
    def __init__(self, tier, soul_level, quest_done=True):
        self.character = SimpleNamespace(
            soul_tier=tier, soul_level=soul_level, class_name='Wojownik',
            room_id='safe_test_room', name='Testowa',
            soul_power=lambda: 123, soul_weapon_class_bonus_text=lambda: 'test',
        )
        self.server = DummyServer()
        self.messages=[]
        self.quest_done=quest_done
    async def send(self, message): self.messages.append(str(message))
    def soul_tier_quest_completed(self, tier): return self.quest_done
    def soul_next_goal_text(self): return 'Następny próg.'
    def soul_milestone_text(self, tier): return f'Milestone {tier}'


class SoulInfiniteTests(unittest.TestCase):
    def test_historical_catalogue_exact(self):
        self.assertEqual(p.SOUL_MAX_TIER, 6000)
        for t in (1,2,10,40,80,3000,3001,5999,6000):
            self.assertEqual(p.soul_tier_required_level(t), p.SOUL_TIER_THRESHOLDS[t-1])
            self.assertEqual(p.soul_tier_power_bonus(t), p.SOUL_TIER_POWER_BONUSES[t-1])
            self.assertEqual(p.soul_tier_class_bonus(t), p.SOUL_TIER_CLASS_BONUS_PERCENT[t-1])
        self.assertEqual(p.soul_tier_required_level(6000), 60000)
        self.assertEqual(p.soul_tier_required_level(6001), 60010)
        self.assertEqual(p.soul_tier_required_level(100_000), 1_000_000)
        self.assertIn(6000,p.SOUL_TRIAL_QUEST_IDS)
        self.assertNotIn(6010,p.SOUL_TRIAL_QUEST_IDS)

    def test_bonus_and_trait_extend(self):
        for t in (6001,6010,100_000):
            self.assertGreater(p.soul_tier_power_bonus(t),p.soul_tier_power_bonus(t-1))
            self.assertGreaterEqual(p.soul_tier_class_bonus(t),p.soul_tier_class_bonus(t-1))
            self.assertIn(str(t),p.soul_tier_title_for_class(t,'Wojownik') if t % 100 else f'{t}')
        t6000=p.soul_weapon_trait_totals_v11193(6000,'Wojownik')
        t6001=p.soul_weapon_trait_totals_v11193(6001,'Wojownik')
        trait=p.soul_weapon_trait_for_tier_v11193(6001,'Wojownik')
        self.assertAlmostEqual(t6001[trait['effect']]-t6000[trait['effect']],trait['value'],places=5)
        self.assertEqual(p.soul_tier_guardian_reduction(100_000), 65)
        self.assertEqual(p.soul_tier_dodge_bonus(100_000), .05)

    def test_character_gate_after_6000(self):
        c=object.__new__(character_module.Character)
        c.soul_tier=6000; c.soul_level=60009; c.weapon_base=1; c.class_name='Wojownik'
        c.soul_xp=0; c.race='Człowiek'
        self.assertEqual(c.soul_level_cap_for_current_tier(),60010)
        self.assertIsNone(c.can_unlock())
        c.soul_level=60010
        self.assertTrue(c.soul_progress_is_tier_locked())
        self.assertEqual(c.can_unlock(),6001)
        c.soul_tier=6001
        self.assertFalse(c.soul_progress_is_tier_locked())
        self.assertEqual(c.soul_level_cap_for_current_tier(),60020)
        self.assertGreater(c.soul_power(), 0)


class SoulUnlockTests(unittest.IsolatedAsyncioTestCase):
    async def test_single_tier_6001(self):
        s=DummySession(6000,60010)
        await s.unlock()
        self.assertEqual(s.character.soul_tier,6001)
        self.assertEqual(s.server.db.saved,[6001])
        self.assertTrue(any('Odblokowano Soul Tier 6001' in m for m in s.messages))

    async def test_level_gate(self):
        s=DummySession(6000,60009)
        await s.unlock()
        self.assertEqual(s.character.soul_tier,6000)
        self.assertFalse(s.server.db.saved)
        self.assertTrue(any('Soul Level 60010' in m for m in s.messages))

    async def test_old_trial_cannot_be_skipped(self):
        s=DummySession(5999,60030,quest_done=False)
        await s.unlock(multi=True)
        self.assertEqual(s.character.soul_tier,5999)
        self.assertFalse(s.server.db.saved)
        self.assertTrue(any('Próba Tieru 6000' in m for m in s.messages))

    async def test_multi_tier_many_no_iteration_spike(self):
        s=DummySession(6000,2_000_000)
        await asyncio.wait_for(s.unlock(multi=True),timeout=3)
        self.assertEqual(s.character.soul_tier,200_000)
        self.assertEqual(s.server.db.saved,[200_000])
        self.assertTrue(any('6001–200000' in m for m in s.messages))


if __name__=='__main__': unittest.main(verbosity=2)
