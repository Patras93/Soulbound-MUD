# -*- coding: utf-8 -*-
"""Osłona Duszy — DB trwałość, czas, warunki i realna obrona."""
import ast
import sqlite3
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch
from systems import soul_weapon_elements_v10500 as soul


class ShieldTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory(prefix='soul_shield_')
        self.addCleanup(tmp.cleanup)
        self.path=Path(tmp.name)/'players.db'
        self.conn=sqlite3.connect(self.path)
        self.addCleanup(self.conn.close)
        self.conn.execute('CREATE TABLE player_records_v03051('
             'account_id INTEGER NOT NULL,record_key TEXT NOT NULL,'
             'value INTEGER NOT NULL DEFAULT 0,text_value TEXT NOT NULL DEFAULT "",'
             'updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,'
             'PRIMARY KEY(account_id,record_key))')
        self.conn.commit()

    def actor(self, tier=1300, account=1, conn=None):
        return SimpleNamespace(character=SimpleNamespace(soul_tier=tier),account_id=account,
                               server=SimpleNamespace(db=SimpleNamespace(conn=conn or self.conn)))

    def test_requires_tier_and_element(self):
        self.assertFalse(soul.activate_shield(self.actor(tier=1199),now=1000)[0])
        self.assertFalse(soul.activate_shield(self.actor(),now=1000)[0])
        self.assertEqual(soul.shield_multiplier(self.actor(),now=1000),1.)

    def test_persistent_shield_timing_cooldown_and_character_isolation(self):
        a=self.actor()
        self.assertTrue(soul.choose_element(a,'ogień')[0])
        ok,_=soul.activate_shield(a,now=1000)
        self.assertTrue(ok)
        self.assertEqual(soul.shield_multiplier(a,now=1000),1.15)
        self.assertEqual(soul.shield_multiplier(a,now=1029),1.15)
        self.assertEqual(soul.shield_multiplier(a,now=1030),1.0)
        reopened=sqlite3.connect(self.path);self.addCleanup(reopened.close)
        again=self.actor(conn=reopened)
        self.assertEqual(soul.shield_multiplier(again,now=1020),1.15)
        self.assertFalse(soul.activate_shield(again,now=1179)[0])
        self.assertTrue(soul.activate_shield(again,now=1180)[0])
        self.assertEqual(soul.shield_multiplier(self.actor(account=2),now=1181),1.)

    def test_actual_numeric_physical_and_magic_defense_increase(self):
        src=(Path(__file__).resolve().parents[1]/'player/session_mixins/equipment_stats.py').read_text('utf-8')
        tree=ast.parse(src)
        cls=next(node for node in tree.body if isinstance(node,ast.ClassDef)
                 and node.name=='SessionEquipmentStatsMixin')
        methods=[node for node in cls.body if isinstance(node,ast.FunctionDef)
                 and node.name in ('defense','magic_defense')]
        ns={'shield_multiplier':soul.shield_multiplier,
            'physical_defense_base':lambda lvl,con:200,
            'magic_defense_base':lambda lvl,will:200,
            'ITEMS':{},'TECH_SET_ITEMS_V03114':{},
            'v03042_upgrade_defense_bonus':lambda *a:0}
        exec(compile(ast.fix_missing_locations(ast.Module(body=methods,type_ignores=[])),
                     'equipment_stats.py','exec'),ns)
        a=self.actor()
        a.character.character_level=1
        a.character.class_magic_defense_multiplier=lambda:1.
        a.character.racial_magic_defense_multiplier=lambda:1.
        a.effective_constitution=lambda:1
        a.effective_willpower=lambda:1
        a.total_set_defense_multiplier=lambda:1.
        a.equipment_flat_power_totals_v11187=lambda:{'magic_defense':0}
        a.equipment_property_totals=lambda:{'magic_defense_pct':0,'physical_defense_pct':0}
        a.server.db.equipment=lambda _account:[]
        self.assertEqual(ns['defense'](a),200)
        self.assertEqual(ns['magic_defense'](a),200)
        self.assertTrue(soul.choose_element(a,'piorun')[0])
        self.assertTrue(soul.activate_shield(a,now=1000)[0])
        # Freeze clock only for the active shield's 30-second window.
        with patch.object(soul.time,'time',return_value=1010):
            self.assertEqual(ns['defense'](a),230)
            self.assertEqual(ns['magic_defense'](a),230)
        with patch.object(soul.time,'time',return_value=1040):
            self.assertEqual(ns['defense'](a),200)
            self.assertEqual(ns['magic_defense'](a),200)

    def test_real_defense_methods_contain_shield_and_use_live_multiplier(self):
        src=(Path(__file__).resolve().parents[1]/'player/session_mixins/equipment_stats.py').read_text('utf-8')
        tree=ast.parse(src)
        cls=next(t for t in tree.body if isinstance(t,ast.ClassDef) and t.name=='SessionEquipmentStatsMixin')
        functions={n.name:n for n in cls.body if isinstance(n,ast.FunctionDef)}
        for name in ('defense','magic_defense'):
            self.assertTrue(any(isinstance(n,ast.Call) and isinstance(n.func,ast.Name)
                                and n.func.id=='shield_multiplier' for n in ast.walk(functions[name])))
        self.assertIn('bronduszy oslona',src)

if __name__=='__main__': unittest.main()
