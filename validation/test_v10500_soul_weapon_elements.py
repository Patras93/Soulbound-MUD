# -*- coding: utf-8 -*-
"""Isolated v105 production combat and durable character settings tests."""
import asyncio
import os
import sqlite3
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from systems import soul_weapon_elements_v10500 as soul


class V105SoulElementTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='sb105_soul_elements_')
        self.addCleanup(self.temp.cleanup)
        self.db_file=os.path.join(self.temp.name,'characters.sqlite')
        self.conn=sqlite3.connect(self.db_file)
        self.addCleanup(self.conn.close)
        self.conn.execute('CREATE TABLE player_records_v03051('
             'account_id INTEGER NOT NULL,record_key TEXT NOT NULL,'
             'value INTEGER NOT NULL DEFAULT 0,text_value TEXT NOT NULL DEFAULT "",'
             'updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,'
             'PRIMARY KEY(account_id,record_key))')
        self.conn.execute("INSERT INTO player_records_v03051(account_id,record_key,value) "
                          "VALUES(7,'unrelated_progress',123)")
        self.conn.commit()

    def actor(self, tier=1200, conn=None, account=7):
        a=SimpleNamespace(account_id=account,
            character=SimpleNamespace(soul_tier=tier,class_name='Wojownik',
                                     soul_weapon_mastery_level=1),
            server=SimpleNamespace(db=SimpleNamespace(conn=conn or self.conn)),
            critical_chance=lambda: 0.,critical_multiplier=lambda: 1.,
            mob_effective_max_hp_v11330=lambda mob,templ:10000)
        return a

    def test_selection_is_per_character_and_survives_relogin(self):
        a=self.actor()
        ok,msg=soul.choose_element(a,'piorun')
        self.assertTrue(ok,msg)
        self.assertEqual(soul.selected_element(a),'lightning')
        self.assertEqual(soul.selected_element(self.actor(account=8)),'')
        reopened=sqlite3.connect(self.db_file)
        self.addCleanup(reopened.close)
        self.assertEqual(soul.selected_element(self.actor(conn=reopened)),'lightning')
        self.assertEqual(self.conn.execute("SELECT value FROM player_records_v03051 "
                          "WHERE record_key='unrelated_progress'").fetchone()[0],123)
        self.assertFalse(soul.choose_element(a,'nieistniejący')[0])
        self.assertEqual(soul.selected_element(a),'lightning')

    def test_not_before_tier_1100(self):
        a=self.actor(tier=1099)
        self.assertFalse(soul.choose_element(a,'ogień')[0])
        self.assertFalse(soul.activate_impulse(a,now=100)[0])
        self.assertEqual(soul.selected_element(a),'')

    def test_switching_character_cannot_leak_element_or_impulse(self):
        a=self.actor(account=7)
        self.assertTrue(soul.choose_element(a,'piorun')[0])
        self.assertTrue(soul.activate_impulse(a,now=100)[0])
        a.account_id=8  # Same session, different account-character.
        self.assertEqual(soul.selected_element(a),'')
        self.assertEqual(soul.consume_impulse(a),1.0)
        self.assertTrue(soul.choose_element(a,'woda')[0])
        self.assertEqual(soul.selected_element(a),'water')
        a.account_id=7
        self.assertEqual(soul.selected_element(a),'lightning')
        self.assertEqual(soul.consume_impulse(a),1.2)

    def test_cooldown_is_persistent_and_consumes_once(self):
        a=self.actor()
        soul.choose_element(a,'piorun')
        self.assertEqual(soul.consume_impulse(a),1.0)
        self.assertTrue(soul.activate_impulse(a,now=1000)[0])
        self.assertEqual(soul.consume_impulse(a),1.2)
        self.assertEqual(soul.consume_impulse(a),1.0)
        reopened=sqlite3.connect(self.db_file)
        self.addCleanup(reopened.close)
        logged_again=self.actor(conn=reopened)
        self.assertFalse(soul.activate_impulse(logged_again,now=1001)[0])
        self.assertTrue(soul.activate_impulse(logged_again,now=1090)[0])
        self.assertEqual(soul.consume_impulse(logged_again),1.2)

    def test_actual_source_weapon_attack_uses_element_and_impulse(self):
        from systems import uoss_basic_weapon_shared_v8000 as weapon
        a=self.actor()
        mob=SimpleNamespace(hp=10000)
        template={'name':'Wodny Strażnik'}
        traits=dict(damage_percent=0.,execute_damage_percent=0.,boss_damage_percent=0.,
                    crit_chance=0.,crit_damage_percent=0.)
        mastery=dict(damage_percent=0.,boss_damage_percent=0.,crit_chance=0.,
                     crit_damage_percent=0.)
        with (patch.object(weapon,'soul_weapon_trait_totals_v11193',return_value=traits),
              patch.object(weapon,'soul_weapon_mastery_bonuses',return_value=mastery),
              patch.object(weapon,'weapon_resonance_percent',return_value=0),
              patch.object(weapon.random,'random',return_value=1.0)):
            base=weapon.weapon_attack_boost(a,mob,template,100)[0]
            self.assertEqual(base,100)
            soul.choose_element(a,'piorun')
            self.assertEqual(soul.weapon_multiplier(a,template),1.08)
            self.assertEqual(weapon.weapon_attack_boost(a,mob,template,100)[0],108)
            self.assertTrue(soul.activate_impulse(a,now=1000)[0])
            self.assertEqual(weapon.weapon_attack_boost(a,mob,template,100)[0],130)
            self.assertEqual(weapon.weapon_attack_boost(a,mob,template,100)[0],108)

    def test_actual_session_handler_and_commands(self):
        # Extract the unmodified production body; full session imports need
        # startup bootstrap and must not run against production DB in unit tests.
        import ast
        from pathlib import Path
        root=Path(__file__).resolve().parents[1]
        src=(root/'player/session_mixins/equipment_stats.py').read_text(encoding='utf-8')
        parsed=ast.parse(src)
        cls=next(node for node in parsed.body if isinstance(node,ast.ClassDef)
                 and node.name=='SessionEquipmentStatsMixin')
        method=next(node for node in cls.body if isinstance(node,ast.AsyncFunctionDef)
                    and node.name=='soul_weapon_command_v10500')
        compiled=compile(ast.fix_missing_locations(ast.Module(body=[method],type_ignores=[])),
                         'equipment_stats.py','exec')
        scope={};exec(compiled,scope)
        fn=scope['soul_weapon_command_v10500']
        registry=(root/'player/session_mixins/command_registry.py').read_text(encoding='utf-8')
        self.assertIn("'bronduszy': ('soul_weapon_command_v10500'",registry)
        a=self.actor()
        a.sent=[]
        async def send(message):a.sent.append(message)
        a.send=send
        asyncio.run(fn(a,'zywiol piorun'))
        self.assertEqual(soul.selected_element(a),'lightning')
        asyncio.run(fn(a,'status'))
        self.assertIn('Piorun',a.sent[-1])
        asyncio.run(fn(a,'impuls'))
        self.assertIn('Impuls',a.sent[-1])

if __name__=='__main__':
    unittest.main()
