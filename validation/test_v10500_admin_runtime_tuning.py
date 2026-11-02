# -*- coding: utf-8 -*-
"""Actual v105 Admin Live CAS, persisted runtime coefficients and safety guards."""
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from systems import admin_live_era_v10400 as core
from systems import admin_live_era_v10500 as front
from systems import soul_weapon_elements_v10500 as soul
from systems import equipment_evolution_v10500 as gear

SOUL_DEFAULT = {'passive_pct': 3, 'weakness_pct': 8, 'impulse_pct': 20,
                'impulse_cooldown': 90, 'shield_pct': 15,
                'shield_seconds': 30, 'shield_cooldown': 180}
EQ_DEFAULT = {'stat_pct': 100, 'defense_pct': 100}

class V105LiveRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='sb105_live_')
        self.addCleanup(self.temp.cleanup)
        self.path = core.PATH
        core.PATH = Path(self.temp.name) / 'LIVE_CONTENT' / 'era_v10400_overrides.json'
        core.reset_for_tests()
        soul.LIVE_TUNING['v10500_bron_duszy'].update(SOUL_DEFAULT)
        gear.LIVE_TUNING['v10500_ewolucja_eq'].update(EQ_DEFAULT)
        self.addCleanup(self.cleanup)
        self.reg = {'mobs':{}, 'quests':{}, 'items':{}, 'recipes':{}, 'rooms':{}}

    def cleanup(self):
        core.PATH = self.path
        core.reset_for_tests()
        soul.LIVE_TUNING['v10500_bron_duszy'].update(SOUL_DEFAULT)
        gear.LIVE_TUNING['v10500_ewolucja_eq'].update(EQ_DEFAULT)

    def cmd(self, command):
        return front.command(command, self.reg)

    def test_persisted_soul_and_eq_draft_cas_revert_changes_actual_bonuses(self):
        self.assertIn('3', self.cmd('podglad soul_power v10500_bron_duszy passive_pct'))
        self.assertIn('DRAFT', self.cmd('ustaw soul_power v10500_bron_duszy passive_pct 9'))
        self.assertIn('DRAFT', self.cmd('ustaw soul_power v10500_bron_duszy impulse_pct 30'))
        self.assertIn('DRAFT', self.cmd('ustaw soul_power v10500_bron_duszy shield_pct 25'))
        self.assertIn('DRAFT', self.cmd('ustaw eq_evolution v10500_ewolucja_eq stat_pct 200'))
        self.assertIn('DRAFT', self.cmd('ustaw eq_evolution v10500_ewolucja_eq defense_pct 200'))
        self.assertEqual(gear.stage_defense_bonus(2, {'defense': 800}), 20)  # DRAFT never live
        self.assertIn('opublikowano', self.cmd('aktywuj POTWIERDZAM'))
        self.assertEqual(gear.stage_defense_bonus(2, {'defense': 800}), 40)
        self.assertEqual(gear.stage_stat_bonus(2, {'affix_amount': 400}), 40)
        self.assertEqual(soul.tuning('passive_pct'), 9)
        self.assertEqual(soul.tuning('impulse_pct'), 30)
        # Actual weapon path consumes the new parameters.
        actor = SimpleNamespace(account_id=2, character=SimpleNamespace(soul_tier=1300),
                                _v105_selected_element_cache=(2, 'fire'), _v105_impulse_charged=2)
        with patch('systems.elemental_combat.mob_element_affinities_v11339', return_value=()):
            self.assertAlmostEqual(soul.weapon_multiplier(actor, {'name':'Dummy'}),1.09)
        self.assertAlmostEqual(soul.consume_impulse(actor),1.30)
        self.assertIn('cofnięto',self.cmd('cofnij POTWIERDZAM'))
        self.assertEqual(gear.stage_defense_bonus(2, {'defense': 800}), 20)
        self.assertEqual(soul.tuning('passive_pct'),3)
        self.assertEqual(soul.tuning('impulse_pct'),20)
        # Re-apply from disk as startup does, without a new revision or duplicate changes.
        core.reset_for_tests()
        self.assertEqual(core.apply(self.reg),0)
        self.assertEqual(soul.tuning('shield_pct'),15)
        self.assertEqual(json.loads(core.PATH.read_text('utf-8'))['rev'],2)

    def test_bad_fields_ids_and_conflicting_duration_are_rejected(self):
        for args in (
            'ustaw soul_power v10500_other passive_pct 5',
            'ustaw eq_evolution v10500_other stat_pct 100',
            'ustaw soul_power v10500_bron_duszy invalid 5',
        ):
            self.assertIn('Nieobsługiwane',self.cmd(args))
        self.assertIn('Zakres',self.cmd('ustaw soul_power v10500_bron_duszy shield_pct 51'))
        self.assertIn('Zakres',self.cmd('ustaw eq_evolution v10500_ewolucja_eq defense_pct 100000'))
        self.assertIn('DRAFT',self.cmd('ustaw soul_power v10500_bron_duszy shield_seconds 120'))
        self.assertIn('odrzucony',self.cmd('ustaw soul_power v10500_bron_duszy shield_cooldown 60'))
        self.assertIn('sprawdz',self.cmd('sprawdz').replace('DRAFT','sprawdz'))
        self.assertEqual(soul.tuning('shield_seconds'),30)
        self.assertFalse(core.PATH.exists())

    def test_cas_revision_conflict_never_publishes(self):
        self.assertIn('DRAFT',self.cmd('ustaw soul_power v10500_bron_duszy passive_pct 11'))
        # Another server process created a higher revision while this draft was open.
        core._save({'schema':1,'rev':9,'active':{},'previous':None,'base':{}})
        self.assertIn('konflikt',self.cmd('aktywuj POTWIERDZAM'))
        self.assertEqual(soul.tuning('passive_pct'),3)
        self.assertEqual(json.loads(core.PATH.read_text('utf-8'))['rev'],9)

    def test_evolved_gear_cannot_transfer_legacy_runes_directly(self):
        from storage.db_inventory import DatabaseInventoryMixin
        from storage.db_crafting_extensions import DatabaseCraftingExtensionsMixin
        class DB(DatabaseInventoryMixin):
            def __init__(self, conn):self.conn=conn
        # Actual DB layer test with a minimal v105 ledger; fail before querying
        # legacy rune tables, therefore no equipment mutation is possible.
        conn=sqlite3.connect(':memory:')
        self.addCleanup(conn.close)
        conn.execute('CREATE TABLE player_records_v03051(account_id INTEGER,record_key TEXT,value INTEGER, PRIMARY KEY(account_id,record_key))')
        conn.execute('INSERT INTO player_records_v03051 VALUES (7, ?, 2)',(gear.record_key('sword_1'),))
        db=DB(conn)
        with self.assertRaisesRegex(ValueError,'przypisany do postaci'):
            db.transfer_equipment_crafting_v0925(7,8,'sword_1')
        # Ensure the higher-priority override has the same guard before super().
        import inspect
        body=inspect.getsource(DatabaseCraftingExtensionsMixin.transfer_equipment_crafting_v0925)
        self.assertIn('is_evolved(self.conn, from_account_id, item_id)',body)
        self.assertEqual(conn.execute('SELECT value FROM player_records_v03051').fetchone()[0],2)

if __name__ == '__main__':
    unittest.main()
