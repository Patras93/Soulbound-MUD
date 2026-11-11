# -*- coding: utf-8 -*-
"""v105: real SQLite persistence and market/Admin Live integration (isolated)."""
import os
import sqlite3
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace

from systems.equipment_evolution_v10500 import evolve, current_stage, is_evolved, required_materials, reset_evolution
from systems import imperial_economy_v1320 as market
from systems import imperial_economy_v1321 as auction
from storage.db_inventory import DatabaseInventoryMixin
from systems import admin_live_era_v10400 as admin
from systems import admin_live_era_v10500 as admin105

IID = 'v10500_set_przesmyk_head'
ITEM = {'type':'armor','defense':4000,'affix_amount':400}


class BoundEquipmentTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='v105_market_test_')
        self.addCleanup(self.tmp.cleanup)
        self.conn = sqlite3.connect(os.path.join(self.tmp.name,'data.db'))
        self.addCleanup(self.conn.close)
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript('''
            CREATE TABLE inventory(account_id INTEGER, item_id TEXT, quantity INTEGER NOT NULL,
                PRIMARY KEY(account_id,item_id));
            CREATE TABLE profession_storage(account_id INTEGER,container TEXT,item_id TEXT,
                quantity INTEGER NOT NULL, PRIMARY KEY(account_id,container,item_id));
            CREATE TABLE player_records_v03051(account_id INTEGER,record_key TEXT,value INTEGER DEFAULT 0,
                text_value TEXT DEFAULT '',updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY(account_id,record_key));
            CREATE TABLE shop_purchase_lots_v1175(account_id INTEGER,item_id TEXT,
                paid_silver INTEGER NOT NULL,quantity INTEGER NOT NULL,
                PRIMARY KEY(account_id,item_id,paid_silver));
            CREATE TABLE market_listings_v1320(id INTEGER PRIMARY KEY AUTOINCREMENT,
                seller INTEGER,item_id TEXT,quantity INTEGER,container TEXT,price INTEGER,
                state TEXT DEFAULT 'active',created_at INTEGER);
        ''')
        self.conn.execute('INSERT INTO inventory VALUES(7,?,1)',(IID,))
        for iid,qty in required_materials(1).items():
            self.conn.execute('INSERT INTO profession_storage VALUES(?,?,?,?)',(7,'craftbox',iid,qty))
        self.conn.commit()
        ok,msg,stage=evolve(self.conn,7,IID,ITEM)
        self.assertTrue(ok,msg)
        self.assertEqual(stage,1)
        class DB(DatabaseInventoryMixin):
            def __init__(self,con): self.conn=con
            def item_qty(self,acct,iid):
                row=self.conn.execute('SELECT quantity FROM inventory WHERE account_id=? AND item_id=?',(acct,iid)).fetchone()
                return row[0] if row else 0
        self.db=DB(self.conn)

    def test_bound_read_survives_new_sqlite_connection(self):
        with sqlite3.connect(os.path.join(self.tmp.name,'data.db')) as another:
            self.assertTrue(is_evolved(another,7,IID))
            self.assertFalse(is_evolved(another,8,IID))

    def test_cannot_sell_delete_or_gift_but_normal_equipment_remains_usable(self):
        self.assertFalse(self.db.remove_item(7,IID))
        self.assertFalse(self.db.transfer_inventory_item(7,8,IID))
        self.assertEqual(self.db.item_qty(7,IID),1)
        self.assertEqual(self.db.item_qty(8,IID),0)
        self.assertEqual(current_stage(self.conn,7,IID),1)
        self.conn.execute("INSERT INTO inventory VALUES(7,'unbound_armor',1)")
        self.conn.commit()
        self.assertTrue(self.db.remove_item(7,'unbound_armor'))
        self.assertEqual(self.db.item_qty(7,'unbound_armor'),0)

    def test_mail_escrow_refuses_before_any_mutation(self):
        result=self.db.send_mail_attachment_v0614(7,8,'Nadawca',kind='item',item_id=IID,item_name='Zbroja')
        self.assertIsNone(result)
        self.assertEqual(self.db.item_qty(7,IID),1)
        self.assertEqual(current_stage(self.conn,7,IID),1)

    def test_explicit_reset_unbinds_only_v105_stage_and_preserves_legacy_history(self):
        self.conn.execute("INSERT INTO player_records_v03051(account_id,record_key,value) VALUES(7,'old_tier_history',900)")
        self.conn.commit()
        ok, text = reset_evolution(self.conn, 7, IID)
        self.assertTrue(ok, text)
        self.assertEqual(current_stage(self.conn, 7, IID), 0)
        self.assertEqual(self.conn.execute('SELECT value FROM player_records_v03051 WHERE record_key=?',
                                           ('old_tier_history',)).fetchone()[0],900)
        self.assertTrue(self.db.transfer_inventory_item(7, 8, IID))
        self.assertEqual(self.db.item_qty(8,IID),1)
        self.assertFalse(is_evolved(self.conn,8,IID))

    def test_caller_transaction_rollback_restores_evolution_reset_and_materials(self):
        # The v105 evolution operation may be called inside another quest/loot transaction.
        self.conn.execute('BEGIN')
        ok, _ = reset_evolution(self.conn,7,IID)
        self.assertTrue(ok)
        self.assertFalse(is_evolved(self.conn,7,IID))
        self.conn.rollback()
        self.assertTrue(is_evolved(self.conn,7,IID))
        self.assertEqual(current_stage(self.conn,7,IID),1)
        # New evolution writes similarly must not commit somebody else's transaction.
        for iid, qty in required_materials(2).items():
            self.conn.execute('INSERT INTO profession_storage VALUES(?,?,?,?)',(7,'craftbox',iid,qty))
        self.conn.commit()
        self.conn.execute('BEGIN')
        self.assertTrue(evolve(self.conn,7,IID,ITEM)[0])
        self.assertEqual(current_stage(self.conn,7,IID),2)
        self.conn.rollback()
        self.assertEqual(current_stage(self.conn,7,IID),1)
        for iid,qty in required_materials(2).items():
            self.assertEqual(self.conn.execute('SELECT quantity FROM profession_storage WHERE account_id=7 AND item_id=?',(iid,)).fetchone()[0],qty)

    def test_market_and_auction_are_blocked_atomically(self):
        for action in (lambda:market.list_item(self.conn,7,IID,1,100,'inventory'),
                       lambda:auction.offer_auction(self.conn,7,IID,1,100,6,'inventory')):
            with self.assertRaisesRegex(ValueError,'przypisany do postaci'):
                action()
            self.assertEqual(self.db.item_qty(7,IID),1)
            self.assertFalse(self.conn.in_transaction)
        self.assertEqual(current_stage(self.conn,7,IID),1)


class AdminV105Tests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='v105_admin_test_')
        self.addCleanup(self.tmp.cleanup)
        self.saved_path=admin.PATH
        admin.PATH=Path(self.tmp.name)/'era_v10400_overrides.json'
        admin.reset_for_tests()
        self.addCleanup(self.restore)
        self.reg={
            'rooms':{'v10500_przesmyk_01':{'recommended_mastery':10001,'generator_level':10001}},
            'mobs':{'v10500_przesmyk_boss_1':{'boss':True,'max_hp':10000000,'damage':4000}},
            'quests':{'v10500_przesmyk_hunt_01':{'needed':3,'reward_gold':300}},
            'items':{'v10500_set_przesmyk_head':{'defense':3000,'affix_amount':200}},
            'recipes':{'v10500_set_przesmyk_head':{'quantity':1,'min_profession_level':10001}},
        }

    def restore(self):
        admin.PATH=self.saved_path
        admin.reset_for_tests()

    def cmd(self,arg):return admin105.command(arg,self.reg)

    def test_admin_v105_view_draft_publish_reload_and_rollback(self):
        self.assertIn('20',self.cmd('regiony'))
        self.assertIn('20',self.cmd('regiony'))
        self.assertIn('max_hp',self.cmd('podglad mob v10500_przesmyk_boss_1 max_hp'))
        self.assertIn('DRAFT',self.cmd('ustaw mob v10500_przesmyk_boss_1 max_hp 20000000'))
        self.assertEqual(self.reg['mobs']['v10500_przesmyk_boss_1']['max_hp'],10000000)
        self.assertIn('DRAFT',self.cmd('sprawdz'))
        self.assertIn('opublikowano',self.cmd('aktywuj POTWIERDZAM'))
        self.assertEqual(self.reg['mobs']['v10500_przesmyk_boss_1']['max_hp'],20000000)
        admin.reset_for_tests()
        self.assertEqual(admin.apply(self.reg),1)
        self.assertEqual(self.reg['mobs']['v10500_przesmyk_boss_1']['max_hp'],20000000)
        self.assertIn('cofnięto',self.cmd('cofnij POTWIERDZAM'))
        self.assertEqual(self.reg['mobs']['v10500_przesmyk_boss_1']['max_hp'],10000000)

    def test_v105_other_safe_fields_and_invalid_rejections(self):
        self.assertIn('DRAFT',self.cmd('ustaw quest v10500_przesmyk_hunt_01 needed 4'))
        self.assertIn('DRAFT',self.cmd('ustaw room v10500_przesmyk_01 recommended_mastery 12000'))
        self.assertIn('DRAFT',self.cmd('ustaw item v10500_set_przesmyk_head defense 4000'))
        self.assertIn('DRAFT',self.cmd('ustaw recipe v10500_set_przesmyk_head quantity 2'))
        self.assertIn('Zakres',self.cmd('ustaw mob v10500_przesmyk_boss_1 max_hp 0'))
        self.assertIn('Nieobsługiwane',self.cmd('ustaw mob wrong_boss_1 damage 100'))
        self.assertIn('Nieobsługiwane',self.cmd('ustaw soul_trial soul_tier_1011_trial needed 2'))
        self.assertIn('opublikowano',self.cmd('aktywuj POTWIERDZAM'))
        self.assertEqual(self.reg['quests']['v10500_przesmyk_hunt_01']['needed'],4)
        self.assertEqual(self.reg['rooms']['v10500_przesmyk_01']['recommended_mastery'],12000)
        self.assertEqual(self.reg['items']['v10500_set_przesmyk_head']['defense'],4000)
        self.assertEqual(self.reg['recipes']['v10500_set_przesmyk_head']['quantity'],2)


if __name__=='__main__':unittest.main()
