# -*- coding: utf-8 -*-
"""Source contracts: prevent regressions recovered from PREDEPLOY v103 log.

Never starts game, binds a port or reads a real database.
"""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]

class HistoricalPredeployRecovery(unittest.TestCase):
    def test_release_identity_header(self):
        version = (ROOT / 'VERSION').read_text(encoding='utf-8').strip()
        self.assertTrue((ROOT / 'CHANGELOG_PL.txt').read_text(encoding='utf-8')
                        .startswith('Aktualna paczka: v' + version + '\n'))

    def test_party_drop_validation_matches_unchanged_real_runtime(self):
        gate = (ROOT / 'predeploy_check.py').read_text(encoding='utf-8')
        audit = (ROOT / 'admin/audits.py').read_text(encoding='utf-8')
        combat = (ROOT / 'player/session_mixins/combat_rewards.py').read_text(encoding='utf-8')
        exact = 'drop_recipients = tuple(party_drop_recipients_v0359(item_id, recipients))'
        self.assertIn(exact, gate)
        self.assertIn(exact, audit)
        self.assertIn(exact, combat)
        self.assertIn('count("random.random()") == 1', gate)
        self.assertIn('if random.random() <= _effective_drop_chance_v11329:', combat)

    def test_legacy_compat_fail_closed(self):
        gate = (ROOT / 'predeploy_check.py').read_text(encoding='utf-8')
        full = (ROOT / 'predeploy_full.py').read_text(encoding='utf-8')
        # In v105 the source contract MUST pass server.VERSION so the proof
        # cannot quietly fall back to the v104-only whitelist.
        version = (ROOT / 'VERSION').read_text(encoding='utf-8').strip()
        required = ('nonblocking_legacy_audits = accepted_legacy_reports(ns, version=server.VERSION)'
                    if tuple(int(x) for x in version.split('.')) >= (105,0,0) else
                    'nonblocking_legacy_audits = accepted_legacy_reports(ns)')
        self.assertIn(required, full)
        self.assertIn('if audit_failures:', full)
        self.assertIn(required, gate)
        self.assertNotIn('nonblocking_legacy_audits = set()', full)

    def test_known_quest_growth_contract(self):
        from validation.release_contracts import modern_quest_catalog
        src = (ROOT / 'validation/v601_profession_paths.py').read_text(encoding='utf-8')
        self.assertTrue(modern_quest_catalog('103.00.0'))
        self.assertIn('len(quests)>=6793', src)

if __name__ == '__main__':
    unittest.main()
