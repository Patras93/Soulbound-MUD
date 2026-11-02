# -*- coding: utf-8 -*-
"""v105: trwała ewolucja posiadanego EQ, atomowe materiały i realne statystyki."""
import asyncio
import os
import sqlite3
import tempfile
import unittest
from types import SimpleNamespace
from unittest.mock import patch

from systems import equipment_evolution_v10500 as evo

ITEM_ID = 'v10500_set_przesmyk_helmet'
ITEM = {'type': 'armor', 'name': 'Hełm Wygasłych Słońc', 'defense': 8000,
        'affix': 'constitution', 'affix_amount': 800, 'stats': {}}


class EquipmentEvolutionTests(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory(prefix='sb105_eq_evolve_')
        self.addCleanup(tmp.cleanup)
        self.path = os.path.join(tmp.name, 'accounts.db')
        conn = self.conn = sqlite3.connect(self.path)
        self.addCleanup(conn.close)
        conn.row_factory = sqlite3.Row
        conn.executescript('''
            CREATE TABLE inventory(account_id INTEGER,item_id TEXT,quantity INTEGER NOT NULL,
                PRIMARY KEY(account_id,item_id));
            CREATE TABLE profession_storage(account_id INTEGER,container TEXT,item_id TEXT,
                quantity INTEGER NOT NULL,PRIMARY KEY(account_id,container,item_id));
            CREATE TABLE player_records_v03051(account_id INTEGER NOT NULL,record_key TEXT NOT NULL,
                value INTEGER NOT NULL DEFAULT 0,text_value TEXT NOT NULL DEFAULT '',
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,PRIMARY KEY(account_id,record_key));
            CREATE TABLE equipment(account_id INTEGER NOT NULL,slot TEXT NOT NULL,item_id TEXT NOT NULL,
                PRIMARY KEY(account_id,slot));
            CREATE TABLE equipment_runes_v0925(account_id INTEGER,item_id TEXT,socket_index INTEGER,rune_id TEXT);
        ''')
        for account in (7, 8):
            conn.execute('INSERT INTO inventory VALUES (?,?,?)', (account, ITEM_ID, 1))
        conn.execute('INSERT INTO equipment VALUES (?,?,?)', (7, 'head', ITEM_ID))
        conn.execute('INSERT INTO equipment_runes_v0925 VALUES (?,?,?,?)', (7,ITEM_ID,1,'rune_guard'))
        conn.execute("INSERT INTO player_records_v03051(account_id,record_key,value) "
                     "VALUES(7,'old_soul_tier_progress',300)")
        self.materials = evo.required_materials(1)
        for item_id, quantity in self.materials.items():
            conn.execute('INSERT INTO profession_storage VALUES (?,?,?,?)',
                         (7, 'craftbox', item_id, quantity))
        conn.commit()

    def test_real_persistent_progress_and_preserves_gear_and_old_records(self):
        ok, text, stage = evo.evolve(self.conn, 7, ITEM_ID, ITEM)
        self.assertTrue(ok, text)
        self.assertEqual(stage, 1)
        self.assertEqual(evo.current_stage(self.conn, 7, ITEM_ID), 1)
        self.assertEqual(evo.current_stage(self.conn, 8, ITEM_ID), 0)
        self.assertEqual(evo.stage_stat_bonus(1, ITEM), 20)
        self.assertEqual(evo.stage_defense_bonus(1, ITEM), 100)
        check = sqlite3.connect(self.path)
        self.addCleanup(check.close)
        self.assertEqual(evo.current_stage(check,7,ITEM_ID),1)
        self.assertEqual(check.execute("SELECT value FROM player_records_v03051 "
                             "WHERE account_id=7 AND record_key='old_soul_tier_progress'").fetchone()[0],300)
        self.assertEqual(check.execute('SELECT rune_id FROM equipment_runes_v0925').fetchone()[0],'rune_guard')
        self.assertEqual(check.execute('SELECT item_id FROM equipment').fetchone()[0],ITEM_ID)
        self.assertEqual(check.execute('SELECT quantity FROM inventory WHERE account_id=7').fetchone()[0],1)
        self.assertTrue(all(check.execute('SELECT quantity FROM profession_storage '
                           'WHERE account_id=7 AND item_id=?',(k,)).fetchone()[0]==0 for k in self.materials))

    def test_atomic_no_partial_consume_when_material_missing(self):
        missing=list(self.materials)[-1]
        self.conn.execute('UPDATE profession_storage SET quantity=0 WHERE item_id=?',(missing,))
        self.conn.commit()
        before=self.conn.execute('SELECT item_id,quantity FROM profession_storage ORDER BY item_id').fetchall()
        self.assertFalse(evo.evolve(self.conn,7,ITEM_ID,ITEM)[0])
        after=self.conn.execute('SELECT item_id,quantity FROM profession_storage ORDER BY item_id').fetchall()
        self.assertEqual([tuple(x) for x in before],[tuple(x) for x in after])
        self.assertEqual(evo.current_stage(self.conn,7,ITEM_ID),0)

    def test_no_item_no_benefit_and_duplicate_copies_are_rejected(self):
        self.conn.execute('DELETE FROM inventory WHERE account_id=7')
        self.conn.commit()
        self.assertFalse(evo.evolve(self.conn,7,ITEM_ID,ITEM)[0])
        self.conn.execute('INSERT INTO inventory VALUES (7,?,2)',(ITEM_ID,))
        self.conn.commit()
        self.assertFalse(evo.evolve(self.conn,7,ITEM_ID,ITEM)[0])
        self.assertEqual(evo.current_stage(self.conn,7,ITEM_ID),0)

    def test_non_armor_and_bad_materials_do_not_change_anything(self):
        self.assertFalse(evo.evolve(self.conn,7,ITEM_ID,{'type':'weapon'})[0])
        with self.assertRaises(ValueError):evo.required_materials(11)
        self.assertEqual(evo.current_stage(self.conn,7,ITEM_ID),0)

    def test_progress_requires_different_region_materials_next_level(self):
        self.assertTrue(evo.evolve(self.conn,7,ITEM_ID,ITEM)[0])
        self.assertNotEqual(evo.required_materials(1),evo.required_materials(2))
        self.assertFalse(evo.evolve(self.conn,7,ITEM_ID,ITEM)[0])
        self.assertEqual(evo.current_stage(self.conn,7,ITEM_ID),1)

    def test_actual_equipment_stats_and_defense_gain_and_remain_unchanged_without_evolution(self):
        # Original production methods without importing the entire startup world,
        # whose catalogue requires the complete server bootstrap.
        import ast
        from pathlib import Path
        code=(Path(__file__).resolve().parents[1]/'player/session_mixins/equipment_stats.py').read_text(encoding='utf-8')
        parsed=ast.parse(code)
        klass=next(node for node in parsed.body if isinstance(node,ast.ClassDef)
                   and node.name=='SessionEquipmentStatsMixin')
        selected=('equipped_item_rows','equipment_bonus_totals','defense')
        body=[node for node in klass.body if isinstance(node,ast.FunctionDef)
              and node.name in selected]
        self.assertEqual(len(body),3)
        ns={'ITEMS':{ITEM_ID:ITEM},'crossover_bonus_v3001':lambda item:({},{}),
            'TECH_SET_ITEMS_V03114':{},
            'v03042_upgrade_defense_bonus':lambda item,stage:0,
            'physical_defense_base':lambda lvl,constitution:0,
            'shield_multiplier':lambda actor:1.0}
        exec(compile(ast.fix_missing_locations(ast.Module(body=body,type_ignores=[])),
                     'equipment_stats.py','exec'),ns)
        class TestDB:
            conn=self.conn
            def equipment(self, account):
                return self.conn.execute('SELECT item_id,slot FROM equipment WHERE account_id=?',(account,)).fetchall()
            def equipment_reforge(self,*_):return None
            def equipment_runes_v0925(self,*_):return ()
            def equipment_upgrade_level_v03042(self,*_):return 0
            def equipment_enchants_v03053(self,*_):return ()
        class Actor:
            equipped_item_rows=ns['equipped_item_rows']
            equipment_bonus_totals=ns['equipment_bonus_totals']
            defense=ns['defense']
            def __init__(self):
                self.server=SimpleNamespace(db=TestDB())
                self.account_id=7
                self.character=SimpleNamespace(character_level=1)
                self._read_only_equipment_cache_v1262=None
            def class_set_stat_bonus_totals(self):return {}
            def active_soul_weapon_relic_v11176(self):return (None,None)
            def equipment_total_socket_capacity_v03114(self,*_):return 0
            def effective_constitution(self):return 1
            def total_set_defense_multiplier(self):return 1.0
            def equipment_property_totals(self):return {'physical_defense_pct':0}
        a=Actor()
        base=a.equipment_bonus_totals()['constitution']
        base_def=a.defense()
        self.assertTrue(evo.evolve(self.conn,7,ITEM_ID,ITEM)[0])
        a._read_only_equipment_cache_v1262=None
        self.assertEqual(a.equipment_bonus_totals()['constitution']-base,20)
        self.assertEqual(a.defense()-base_def,100)
        # No item equipped: no bonus, despite durable record in character history.
        self.conn.execute('DELETE FROM equipment WHERE account_id=7')
        self.conn.commit()
        a._read_only_equipment_cache_v1262=None
        self.assertEqual(a.equipment_bonus_totals()['constitution'],0)

    def test_sqlite_trigger_failure_rolls_back_materials(self):
        self.conn.execute("CREATE TRIGGER reject_evolution BEFORE INSERT ON player_records_v03051 "
                          "WHEN NEW.record_key LIKE 'eq_evolution_v10500:%' "
                          "BEGIN SELECT RAISE(ABORT,'injected persistence failure'); END")
        self.conn.commit()
        with self.assertRaises(sqlite3.IntegrityError):
            evo.evolve(self.conn,7,ITEM_ID,ITEM)
        for iid, qty in self.materials.items():
            self.assertEqual(self.conn.execute(
                'SELECT quantity FROM profession_storage WHERE account_id=7 AND item_id=?',(iid,)
            ).fetchone()[0],qty)
        self.assertEqual(evo.current_stage(self.conn,7,ITEM_ID),0)

    def test_real_command_uses_materials_and_returns_short_nvda_response(self):
        from player.session_mixins.forge_guilds import SessionForgeGuildsMixin
        actor=SimpleNamespace(account_id=7,combat_mob_key=None,sent=[],
                              server=SimpleNamespace(db=SimpleNamespace(conn=self.conn)),
                              at_haldor_forge_v0925=lambda:True)
        async def send(text):actor.sent.append(text)
        actor.send=send
        actor.owned_equipment_upgrade_rows_v03042=lambda:[(ITEM_ID,ITEM,1,0)]
        actor.resolve_owned_equipment_v0925=lambda text,free_only=False:(ITEM_ID,ITEM) if text else None
        actor._read_only_equipment_cache_v1262={'bonuses':{'constitution':0}}
        asyncio.run(SessionForgeGuildsMixin.evolve_equipment_v10500(actor,'lista'))
        self.assertTrue(any('strona 1/1' in msg for msg in actor.sent))
        asyncio.run(SessionForgeGuildsMixin.evolve_equipment_v10500(actor,'1'))
        self.assertEqual(evo.current_stage(self.conn,7,ITEM_ID),1)
        self.assertEqual(actor._read_only_equipment_cache_v1262,None)
        self.assertTrue(any('Konstytucja +20' in msg for msg in actor.sent))

    def test_player_command_is_registered_and_guarded_by_forge(self):
        from player.session_mixins.command_registry import COMMAND_REGISTRY
        from player.session_mixins.forge_guilds import SessionForgeGuildsMixin
        self.assertEqual(COMMAND_REGISTRY['ewolucja'][0], 'evolve_equipment_v10500')
        actor=SimpleNamespace(account_id=7,combat_mob_key=None,sent=[],
                              server=SimpleNamespace(db=SimpleNamespace(conn=self.conn)),
                              at_haldor_forge_v0925=lambda:False)
        async def send(text):actor.sent.append(text)
        actor.send=send
        actor.owned_equipment_upgrade_rows_v03042=lambda: [(ITEM_ID,ITEM,1,0)]
        asyncio.run(SessionForgeGuildsMixin.evolve_equipment_v10500(actor,ITEM_ID))
        self.assertIn('Haldor',actor.sent[-1])
        self.assertEqual(evo.current_stage(self.conn,7,ITEM_ID),0)

if __name__=='__main__':unittest.main()
