# -*- coding: utf-8 -*-
"""v105: housing and profession direct-SQL paths must not clone bound EQ."""
import asyncio
import ast
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

# Compile the exact production methods without bootstrapping the entire server.
# Importing social_expansion directly in a unittest discovery can initialise
# catalogs out of order and incorrectly trigger the legacy Boris guard.
root=Path(__file__).resolve().parents[1]
def _load_real_method(file_path, class_name, func_name, scope):
    tree=ast.parse(file_path.read_text(encoding='utf8'))
    nodes=next(n.body for n in tree.body if isinstance(n,ast.ClassDef) and n.name==class_name) if class_name else tree.body
    fn=next(n for n in nodes if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name==func_name)
    fn.decorator_list=[]
    exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),str(file_path),'exec'),scope)
    return scope[func_name]

import unicodedata
def _lookup(value):
    return str(value).casefold()
_housing_scope={'normalize_lookup_text':_lookup,'player_item_display_name_v0335':lambda x:str(x),
                'currency_price_text':lambda x:str(x),'CURRENCY_SQLITE_SAFE_TOTAL':10**17}
housing_method=_load_real_method(root/'player/session_mixins/social_expansion.py',
              'SessionSocialExpansionMixin','housing_v03051',_housing_scope)
_prof_scope={k:set() for k in ('HERB_STORAGE_IDS','FISH_STORAGE_IDS','WOOD_STORAGE_IDS','MINING_STORAGE_IDS')}
for name in ('_material_containers','_sum','_remove_all'):
    _load_real_method(root/'player/session_mixins/profesje6.py',None,name,_prof_scope)
_remove_all=_prof_scope['_remove_all']
from storage.db_inventory import DatabaseInventoryMixin
from systems.equipment_evolution_v10500 import record_key

ITEM = 'v10500_set_przesmyk_head'


class DB(DatabaseInventoryMixin):
    def __init__(self, conn):
        self.conn=conn

    def storage_qty(self, account, container, iid):
        row=self.conn.execute('SELECT quantity FROM profession_storage WHERE account_id=? AND container=? AND item_id=?',
                              (account,container,iid)).fetchone()
        return int(row[0]) if row else 0


class Actor:
    housing_v03051=housing_method

    def __init__(self, db):
        self.account_id=7
        self.server=type('Server',(),{'db':db})()
        self.messages=[]

    async def send(self, msg, *args, **kwargs):
        self.messages.append(str(msg))


class HousingBoundItemTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory(prefix='sb105_house_atomic_')
        self.addCleanup(tmp.cleanup)
        self.path=Path(tmp.name)/'db.sqlite'
        self.con=sqlite3.connect(self.path)
        self.addCleanup(self.con.close)
        self.con.row_factory=sqlite3.Row
        self.con.executescript('''
            CREATE TABLE inventory(account_id INTEGER,item_id TEXT,quantity INTEGER NOT NULL,
              PRIMARY KEY(account_id,item_id));
            CREATE TABLE player_records_v03051(account_id INTEGER,record_key TEXT,value INTEGER,
              PRIMARY KEY(account_id,record_key));
            CREATE TABLE player_housing_v03051(account_id INTEGER PRIMARY KEY,
              name TEXT DEFAULT 'Dom',level INTEGER DEFAULT 1,decor TEXT DEFAULT '',storage_json TEXT DEFAULT '{}');
            CREATE TABLE profession_storage(account_id INTEGER,container TEXT,item_id TEXT,quantity INTEGER,
              PRIMARY KEY(account_id,container,item_id));
            CREATE TABLE shop_purchase_lots_v1175(account_id INTEGER,item_id TEXT,paid_silver INTEGER,
              quantity INTEGER,PRIMARY KEY(account_id,item_id,paid_silver));
        ''')
        self.con.execute('INSERT INTO inventory VALUES (7,?,1)',(ITEM,))
        self.con.execute('INSERT INTO player_records_v03051 VALUES (7,?,3)',(record_key(ITEM),))
        self.con.commit()
        self.db=DB(self.con)
        self.actor=Actor(self.db)

    def box(self):
        row=self.con.execute('SELECT storage_json FROM player_housing_v03051 WHERE account_id=7').fetchone()
        return json.loads(row[0]) if row else {}

    def test_bound_eq_cannot_clone_through_house_store(self):
        asyncio.run(self.actor.housing_v03051('store '+ITEM))
        self.assertEqual(self.db.item_qty(7,ITEM),1)
        self.assertEqual(self.box(),{})
        self.assertTrue(any('przypisane' in x for x in self.actor.messages))
        self.con.close()
        with sqlite3.connect(self.path) as reopened:
            self.assertEqual(reopened.execute('SELECT quantity FROM inventory').fetchone()[0],1)
            self.assertEqual(json.loads(reopened.execute('SELECT storage_json FROM player_housing_v03051').fetchone()[0]),{})

    def test_rejected_inventory_removal_does_not_credit_house(self):
        self.con.execute('DELETE FROM player_records_v03051')
        self.con.commit()
        self.db.remove_item = lambda *a, **k: False
        asyncio.run(self.actor.housing_v03051('store '+ITEM))
        self.assertEqual(self.box(),{})
        self.assertEqual(self.db.item_qty(7,ITEM),1)
        self.assertTrue(any('Nie udało' in x for x in self.actor.messages))

    def test_previous_broken_copy_in_house_cannot_be_retrieved_when_bound(self):
        self.con.execute('INSERT INTO player_housing_v03051(account_id,storage_json) VALUES (7,?)',
                         (json.dumps({ITEM:1}),))
        self.con.commit()
        asyncio.run(self.actor.housing_v03051('take '+ITEM))
        self.assertEqual(self.db.item_qty(7,ITEM),1)
        self.assertEqual(self.box(),{ITEM:1})

    def test_normal_store_and_take_preserve_count_and_wallet_basis(self):
        normal='v10500_test_plain_shield'
        self.con.execute('INSERT INTO inventory VALUES (7,?,2)',(normal,))
        self.con.execute('INSERT INTO shop_purchase_lots_v1175 VALUES (7,?,50,2)',(normal,))
        self.con.commit()
        asyncio.run(self.actor.housing_v03051('store '+normal+' 1'))
        self.assertEqual(self.db.item_qty(7,normal),1)
        self.assertEqual(self.box()[normal],1)
        self.assertEqual(self.con.execute('SELECT quantity FROM shop_purchase_lots_v1175').fetchone()[0],1)
        asyncio.run(self.actor.housing_v03051('take '+normal+' 1'))
        self.assertEqual(self.db.item_qty(7,normal),2)
        self.assertNotIn(normal,self.box())

    def test_db_error_after_inventory_deduction_rolls_back_all(self):
        self.con.execute('INSERT INTO inventory VALUES (7,?,1)',('unbound_test',))
        self.con.execute('INSERT INTO shop_purchase_lots_v1175 VALUES (7,?,40,1)',('unbound_test',))
        self.con.execute('''CREATE TRIGGER reject_house_update BEFORE UPDATE OF storage_json
                             ON player_housing_v03051 BEGIN SELECT RAISE(ABORT,'simulated disk failure'); END''')
        self.con.commit()
        with self.assertRaisesRegex(sqlite3.IntegrityError,'simulated disk failure'):
            asyncio.run(self.actor.housing_v03051('store unbound_test'))
        self.assertEqual(self.db.item_qty(7,'unbound_test'),1)
        self.assertEqual(self.box(),{})
        self.assertEqual(self.con.execute('SELECT quantity FROM shop_purchase_lots_v1175 WHERE item_id=?',
                                          ('unbound_test',)).fetchone()[0],1)
        self.assertFalse(self.con.in_transaction)

    def test_house_take_sql_failure_does_not_create_inventory_copy(self):
        iid='stored_shield'
        self.con.execute('INSERT INTO player_housing_v03051(account_id,storage_json) VALUES (7,?)',
                         (json.dumps({iid:1}),))
        self.con.execute('''CREATE TRIGGER reject_house_take BEFORE UPDATE OF storage_json
                             ON player_housing_v03051 BEGIN SELECT RAISE(ABORT,'take disk failure'); END''')
        self.con.commit()
        with self.assertRaisesRegex(sqlite3.IntegrityError,'take disk failure'):
            asyncio.run(self.actor.housing_v03051('take '+iid))
        self.assertEqual(self.db.item_qty(7,iid),0)
        self.assertEqual(self.box(),{iid:1})
        self.assertFalse(self.con.in_transaction)

    def test_profession_batch_sql_cannot_consume_evolved_equipment(self):
        # Even a malicious mixed-source ingredient (craftbox + inventory)
        # must be refused before decrementing the available craftbox quantity.
        self.con.execute('INSERT INTO profession_storage VALUES (7,?,?,1)',('craftbox',ITEM))
        self.con.commit()
        self.assertFalse(_remove_all(self.db,7,ITEM,2))
        self.assertEqual(self.con.execute('SELECT quantity FROM profession_storage WHERE account_id=7 AND item_id=?',
                                          (ITEM,)).fetchone()[0],1)
        self.assertEqual(self.db.item_qty(7,ITEM),1)
        self.con.execute('INSERT INTO inventory VALUES (7,?,1)',('non_evolved_prof_material',))
        self.con.commit()
        self.assertTrue(_remove_all(self.db,7,'non_evolved_prof_material',1))
        self.assertEqual(self.db.item_qty(7,'non_evolved_prof_material'),0)
        self.con.rollback()


if __name__=='__main__': unittest.main()
