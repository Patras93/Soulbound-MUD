# -*- coding: utf-8 -*-
"""Windows PREDEPLOY regression: exact version-aware compatibility proof."""
import ast
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class VersionedLegacyGate(unittest.TestCase):
    def test_real_call_is_versioned_and_fail_closed(self):
        tree = ast.parse((ROOT / 'predeploy_full.py').read_text(encoding='utf-8'))
        calls = [n for n in ast.walk(tree) if isinstance(n, ast.Assign)
                 and any(isinstance(t, ast.Name) and t.id == 'nonblocking_legacy_audits'
                         for t in n.targets)]
        self.assertEqual(len(calls), 1)
        call = calls[0].value
        self.assertIsInstance(call, ast.Call)
        self.assertIsInstance(call.func, ast.Name)
        self.assertEqual(call.func.id, 'accepted_legacy_reports')
        self.assertEqual(len(call.args), 1)
        self.assertIsInstance(call.args[0], ast.Name)
        self.assertEqual(call.args[0].id, 'ns')
        self.assertEqual(len(call.keywords), 1)
        kw = call.keywords[0]
        self.assertEqual(kw.arg, 'version')
        self.assertIsInstance(kw.value, ast.Attribute)
        self.assertIsInstance(kw.value.value, ast.Name)
        self.assertEqual((kw.value.value.id, kw.value.attr), ('server', 'VERSION'))
        self.assertIn('if name in nonblocking_legacy_audits',
                      (ROOT / 'predeploy_full.py').read_text(encoding='utf-8'))
        self.assertIn('if audit_failures:', (ROOT / 'predeploy_full.py').read_text(encoding='utf-8'))

    def test_fast_gate_demands_the_same_exact_proof(self):
        src = (ROOT / 'predeploy_check.py').read_text(encoding='utf-8')
        required = 'nonblocking_legacy_audits = accepted_legacy_reports(ns, version=server.VERSION)'
        self.assertIn(repr(required), src)
        self.assertNotIn(repr('nonblocking_legacy_audits = accepted_legacy_reports(ns)'), src)
        self.assertIn('if name in nonblocking_legacy_audits', src)
        self.assertIn('if audit_failures:', src)

class SoulBankGateV105(unittest.TestCase):
    def test_real_soul_xp_bank_until_milestone(self):
        from player.character import Character
        from core.progression_600 import SOUL_TIER_THRESHOLDS
        for tier in (1, 9, 10, 1000, 2999):
            actor = object.__new__(Character)
            actor.soul_level = SOUL_TIER_THRESHOLDS[tier]
            actor.soul_tier = tier
            actor.soul_xp = 12345
            actor.race = 'Człowiek'
            actor._guild_bonus_percent = 0
            self.assertTrue(actor.soul_progress_is_tier_locked())
            texts = actor.add_soul_xp(1000)
            self.assertEqual(actor.soul_xp, 13345)
            self.assertTrue(any('odłożone' in msg for msg in texts))
            actor.soul_tier = tier + 1
            actor.add_soul_xp(0)
            self.assertEqual(actor.soul_xp, 13345)

if __name__ == '__main__':
    unittest.main()
