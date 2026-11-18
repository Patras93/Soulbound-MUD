# -*- coding: utf-8 -*-
import sqlite3
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from systems.v115 import fame_combat_runtime, fame_combat_capture


class TestCombatSwitch(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(':memory:')
        self.session = SimpleNamespace(account_id=77, character=SimpleNamespace(account_id=77,name='Wojownik'))
        self.mob = SimpleNamespace(template_id='boss', room_id='region', home_room_id='region')
        self.template = {'name':'Prawdziwy Boss','rank':'boss'}
        self.kw = dict(character_xp=110,soul_xp=220,class_xp=330,stat_xp=440,
                       class_levels=(('Mec',801),),class_max_level=999999,overcap=False,now=100)
        self.patch = patch.object(fame_combat_runtime,'resolve_fame_objective',return_value=('Kraina','boss'))
        self.patch2 = patch.object(fame_combat_capture,'resolve_fame_objective',return_value=('Kraina','boss'))
        self.patch.start(); self.patch2.start()
    def tearDown(self):
        self.patch.stop(); self.patch2.stop(); self.conn.close()
    def stage(self):
        return fame_combat_runtime.stage_delayed_first_clear(self.conn,self.session,self.mob,self.template,**self.kw)
    def test_first_clear_only_staged(self):
        self.assertTrue(self.stage())
        self.assertEqual('WAITING',self.conn.execute('SELECT status FROM v115_fame_delivery').fetchone()[0])
        self.assertIsNone(self.conn.execute("SELECT 1 FROM sqlite_master WHERE name='fame_bosses_v1702'").fetchone())
    def test_fully_capped_hero_still_gets_delayed_fame(self):
        self.kw.update(character_xp=0,soul_xp=0,class_xp=0,stat_xp=0)
        self.assertTrue(self.stage())
        self.assertEqual('WAITING',self.conn.execute('SELECT status FROM v115_fame_delivery').fetchone()[0])

    def test_repeat_does_not_restage(self):
        self.assertTrue(self.stage())
        self.kw['character_xp'] = 99999
        self.assertTrue(self.stage())
        self.assertEqual(1,self.conn.execute('SELECT COUNT(*) FROM v115_fame_reward_snapshot').fetchone()[0])
        self.assertEqual(1,self.conn.execute('SELECT COUNT(*) FROM v115_fame_repeat_exp').fetchone()[0])
    def test_legacy_first_clear_preserved(self):
        self.conn.execute('CREATE TABLE fame_bosses_v1702(account_id INTEGER,region TEXT,boss_id TEXT)')
        self.conn.execute("INSERT INTO fame_bosses_v1702 VALUES(77,'Kraina','boss')")
        self.assertTrue(self.stage())
        self.assertFalse(self.conn.execute("SELECT 1 FROM sqlite_master WHERE name='v115_fame_delivery'").fetchone())
        self.assertEqual(1,self.conn.execute('SELECT COUNT(*) FROM v115_fame_repeat_exp').fetchone()[0])
    def test_rollback_no_pending(self):
        self.conn.execute('SAVEPOINT death')
        self.stage()
        self.conn.execute('ROLLBACK TO death')
        self.conn.execute('RELEASE death')
        self.assertFalse(self.conn.execute("SELECT 1 FROM sqlite_master WHERE name='v115_fame_delivery'").fetchone())
    def test_combat_hook_wires_zeroed_axes(self):
        src = (Path(__file__).parents[1]/'player/session_mixins/combat_rewards.py').read_text()
        self.assertIn('stage_delayed_first_clear(',src)
        for axis in ('char','soul','class','stat'):
            self.assertIn('_now_'+axis+'_v115',src)
        self.assertNotIn('record_fame_kill(',src)

if __name__=='__main__': unittest.main()
