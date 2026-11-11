# -*- coding: utf-8 -*-
"""Isolated v104 Admin Live Era raid-phase/Soul Trial integration tests."""
import json
import tempfile
import unittest
from copy import deepcopy
from pathlib import Path
from unittest.mock import patch

from systems import admin_live_era_v10400 as admin
from systems.content_registry import QUESTS, MOB_TEMPLATES
from world import dynamic_content  # noqa: F401 -- installs v104 catalogue

BOSS = 'v10400_raid_12_boss_1'
TRIAL = 'soul_tier_501_trial'


def sample_registries():
    return {
        'mobs': {BOSS: deepcopy(MOB_TEMPLATES[BOSS])},
        'quests': {TRIAL: deepcopy(QUESTS[TRIAL])},
        'rooms': {}, 'items': {}, 'recipes': {},
    }


class AdminEraV104ExtendedTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='sb104_admin_era_')
        self.old_path = admin.PATH
        admin.PATH = Path(self.tmp.name) / 'era.json'
        admin.reset_for_tests()
        self.r = sample_registries()
        self.original_boss = deepcopy(self.r['mobs'][BOSS])
        self.original_trial = deepcopy(self.r['quests'][TRIAL])

    def tearDown(self):
        admin.PATH = self.old_path
        admin.reset_for_tests()
        self.tmp.cleanup()

    def cmd(self, text):
        return admin.command(text, self.r)

    def test_atomic_publish_reload_undo_raid_and_trial(self):
        self.assertIn('DRAFT', self.cmd(f'ustaw raid_phase {BOSS} p1_attack_pct 150'))
        self.assertIn('DRAFT', self.cmd(f'ustaw raid_phase {BOSS} p2_hp_percent 55'))
        self.assertIn('DRAFT', self.cmd(f'ustaw raid_phase {BOSS} p3_duration_seconds 60'))
        self.assertIn('DRAFT', self.cmd(f'ustaw soul_trial {TRIAL} needed 2'))
        self.assertIn('DRAFT', self.cmd(f'ustaw soul_trial {TRIAL} reward_silver 600000000'))
        self.assertEqual(self.r['mobs'][BOSS], self.original_boss)
        self.assertEqual(self.r['quests'][TRIAL], self.original_trial)
        self.assertIn('CAS 0->0', self.cmd('sprawdz'))
        self.assertIn('opublikowano', self.cmd('aktywuj POTWIERDZAM'))
        phases = self.r['mobs'][BOSS]['olc_boss_phases']
        self.assertEqual(phases[0]['attack_multiplier'], 1.50)
        self.assertEqual(phases[1]['hp_percent'], 55)
        self.assertEqual(phases[2]['duration_seconds'], 60)
        self.assertEqual(self.r['quests'][TRIAL]['needed'], 2)
        self.assertEqual(self.r['quests'][TRIAL]['reward_silver'], 600000000)
        self.assertEqual(self.r['quests'][TRIAL]['unlocks_soul_tier'], 501)
        self.assertEqual(json.loads(admin.PATH.read_text(encoding='utf-8'))['rev'], 1)
        admin.reset_for_tests()  # fresh process registry replay
        fresh = sample_registries()
        self.assertEqual(admin.apply(fresh), 5)
        self.assertEqual(fresh['mobs'][BOSS]['olc_boss_phases'], phases)
        self.assertEqual(fresh['quests'][TRIAL]['needed'], 2)
        self.r = fresh
        self.assertIn('cofnięto', self.cmd('cofnij POTWIERDZAM'))
        self.assertEqual(self.r['mobs'][BOSS], self.original_boss)
        self.assertEqual(self.r['quests'][TRIAL], self.original_trial)
        self.assertEqual(admin.apply(sample_registries()), 0)

    def test_invalid_phase_and_immutable_soul_thresholds(self):
        self.assertIn('odrzucony', self.cmd(f'ustaw raid_phase {BOSS} p2_hp_percent 95'))
        self.assertIn('Zakres', self.cmd(f'ustaw raid_phase {BOSS} p1_attack_pct 110'))
        self.assertIn('Zakres', self.cmd(f'ustaw raid_phase {BOSS} p4_duration_seconds 150'))
        self.assertIn('Nieobsługiwane', self.cmd(f'ustaw soul_trial {TRIAL} required_soul_level 1'))
        self.assertIn('Nieobsługiwane', self.cmd('ustaw soul_trial soul_tier_500_trial needed 4'))
        self.assertIn('Nieobsługiwane', self.cmd('ustaw raid_phase v10400_raid_26_boss_1 p1_hp_percent 75'))
        self.assertIn('Nieobsługiwane', self.cmd('ustaw raid_phase v10300_swit_raid_boss_1 p1_hp_percent 75'))
        self.assertIn('brak zmian', self.cmd('sprawdz'))

    def test_bad_quest_template_protected(self):
        self.r['quests'][TRIAL]['required_soul_level'] = 5000
        self.assertIn('Nie istnieje', self.cmd(f'ustaw soul_trial {TRIAL} needed 2'))
        self.assertFalse(admin.PATH.exists())

    def test_invalid_persisted_script_is_rejected_without_live_mutation(self):
        data = admin._empty()
        data['active'][f'raid_phase|{BOSS}|p2_hp_percent'] = 99
        admin.PATH.write_text(json.dumps(data), encoding='utf-8')
        with self.assertRaises(ValueError):
            admin.apply(self.r)
        self.assertEqual(self.r['mobs'][BOSS], self.original_boss)
        self.assertEqual(self.r['quests'][TRIAL], self.original_trial)

    def test_cas_conflict_detected(self):
        self.cmd(f'ustaw raid_phase {BOSS} p1_hp_percent 75')
        state = admin._empty()
        state['rev'] = 1
        admin.PATH.write_text(json.dumps(state), encoding='utf-8')
        self.assertIn('konflikt rewizji', self.cmd('aktywuj POTWIERDZAM'))
        self.assertEqual(self.r['mobs'][BOSS], self.original_boss)
        self.assertIn('anulowany', self.cmd('anuluj'))

    def test_disk_failure_does_not_publish_live(self):
        self.cmd(f'ustaw soul_trial {TRIAL} needed 2')
        with patch.object(admin, '_save', side_effect=OSError('disk full')):
            self.assertIn('nie opublikowano', self.cmd('aktywuj POTWIERDZAM'))
        self.assertEqual(self.r['quests'][TRIAL], self.original_trial)
        self.assertFalse(admin.PATH.exists())

    def test_tier_reward_undo_preserves_existing_boss_changes(self):
        self.assertIn('opublikowano', self.cmd(f'ustaw raid_phase {BOSS} p1_hp_percent 75') and self.cmd('aktywuj POTWIERDZAM'))
        self.cmd(f'ustaw soul_trial {TRIAL} reward_gold 123')
        self.assertIn('opublikowano', self.cmd('aktywuj POTWIERDZAM'))
        self.assertEqual(self.r['quests'][TRIAL]['reward_gold'], 123)
        self.assertIn('cofnięto', self.cmd('cofnij POTWIERDZAM'))
        self.assertEqual(self.r['quests'][TRIAL]['reward_gold'], 0)
        self.assertEqual(self.r['mobs'][BOSS]['olc_boss_phases'][0]['hp_percent'], 75)


if __name__ == '__main__':
    unittest.main()
