# -*- coding: utf-8 -*-
"""Real, isolated v104.00.2 band and world-invasion integration regressions."""
import sqlite3
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from systems import admin_live_era_v10400 as admin
from systems import soul_xp_bands_v10402 as bands
from systems import world_invasions_v10400 as inv
from core import progression_resources as progress


class LiveBandsAndInvasionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='v10402_isolated_')
        self.original = admin.PATH
        admin.PATH = Path(self.tmp.name) / 'era_v10400_overrides.json'
        admin.reset_for_tests()
        self.reg = {'rooms':{}, 'mobs':{}, 'quests':{}, 'items':{}, 'recipes':{}}

    def tearDown(self):
        admin.PATH = self.original
        admin.reset_for_tests()
        self.tmp.cleanup()

    def cmd(self, text, conn=None):
        return admin.command(text, self.reg, connection=conn)

    def test_real_soul_level_xp_and_persisted_undo(self):
        with patch('core.live_level_caps_v5200.cap', return_value=10000):
            original = {l: progress.soul_xp_to_next(l) for l in (500,501,1000,1001,5000,5001,10000)}
            self.assertTrue(original[501] > 0)
            self.assertIn('DRAFT', self.cmd('ustaw soul_xp_band v10400_soul_501_1000 required_pct 150'))
            self.assertEqual(progress.soul_xp_to_next(501), original[501])
            self.assertIn('opublikowano', self.cmd('aktywuj POTWIERDZAM'))
            self.assertEqual(progress.soul_xp_to_next(501), (original[501]*150+50)//100)
            self.assertEqual(progress.soul_xp_to_next(1000), (original[1000]*150+50)//100)
            for l in (500,1001,5000,5001,10000):
                self.assertEqual(progress.soul_xp_to_next(l),original[l])
            self.assertEqual(bands.current_percent('v10400_soul_501_1000'),150)
            admin.reset_for_tests()
            self.assertEqual(bands.current_percent('v10400_soul_501_1000'),100)
            self.assertEqual(admin.apply(self.reg),1)
            self.assertEqual(progress.soul_xp_to_next(501),(original[501]*150+50)//100)
            self.assertIn('cofnięto',self.cmd('cofnij POTWIERDZAM'))
            self.assertEqual(progress.soul_xp_to_next(501),original[501])

    def test_reject_invalid_band_and_no_mutation(self):
        self.assertIn('Nieobsługiwane',self.cmd('ustaw soul_xp_band v10400_soul_1_500 required_pct 80'))
        self.assertIn('Zakres',self.cmd('ustaw soul_xp_band v10400_soul_501_1000 required_pct 0'))
        self.assertIn('Zakres',self.cmd('ustaw soul_xp_band v10400_soul_501_1000 required_pct 401'))
        self.assertIn('Nieobsługiwane',self.cmd('ustaw soul_trial soul_tier_501_trial required_soul_level 4900'))
        self.assertIn('brak zmian',self.cmd('sprawdz'))
        self.assertFalse(admin.PATH.exists())
        self.assertEqual(bands.percent_for_level(501),100)

    def test_two_bands_revert_and_cancel(self):
        self.assertIn('DRAFT',self.cmd('ustaw soul_xp_band v10400_soul_501_1000 required_pct 50'))
        self.assertIn('DRAFT',self.cmd('ustaw soul_xp_band v10400_soul_5001_10000 required_pct 130'))
        self.assertIn('anulowany',self.cmd('anuluj'))
        self.assertEqual(bands.percent_for_level(9000),100)
        self.cmd('ustaw soul_xp_band v10400_soul_501_1000 required_pct 50')
        self.cmd('ustaw soul_xp_band v10400_soul_5001_10000 required_pct 130')
        self.assertIn('opublikowano',self.cmd('aktywuj POTWIERDZAM'))
        self.assertEqual(bands.percent_for_level(500),100)
        self.assertEqual(bands.percent_for_level(501),50)
        self.assertEqual(bands.percent_for_level(3000),100)
        self.assertEqual(bands.percent_for_level(6000),130)
        self.assertEqual(bands.percent_for_level(10001),100)
        self.assertIn('cofnięto',self.cmd('cofnij POTWIERDZAM'))
        self.assertEqual(bands.percent_for_level(501),100)
        self.assertEqual(bands.percent_for_level(6000),100)

    def test_invasion_actual_db_status_and_no_spurious_writes(self):
        c=sqlite3.connect(':memory:')
        inv.create_schema(c)
        now=1800000000
        current=inv.rotation(now)
        with patch.object(inv.time,'time',return_value=now):
            self.assertIn('3 fronty',self.cmd('wydarzenia'))
            before=c.total_changes
            message=self.cmd('wydarzenia',c)
            self.assertIn('INWAZJA V104:',message)
            self.assertIn('0/8',message)
            self.assertIn('Finałowy boss:',message)
            self.assertEqual(c.total_changes,before)
            c.execute('INSERT INTO world_invasion_fronts_v10400(slot,slug,kills) VALUES (?,?,?)',
                      (current['slot'],current['fronts'][0],5))
            self.assertIn('5/8',self.cmd('wydarzenia',c))
            self.assertIn('zmiana',self.cmd('wydarzenia',c).lower())
        c.close()

    def test_bad_saved_band_no_partial_registry_change(self):
        import json
        invalid=admin._empty()
        invalid['active']['soul_xp_band|v10400_soul_501_1000|required_pct']=999
        admin.PATH.write_text(json.dumps(invalid),encoding='utf-8')
        with self.assertRaises(ValueError):
            admin.apply(self.reg)
        self.assertEqual(bands.percent_for_level(501),100)


if __name__=='__main__':
    unittest.main()
