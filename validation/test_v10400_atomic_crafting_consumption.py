# -*- coding: utf-8 -*-
"""v104: zliczanie bez przepełnienia i atomowe pobieranie surowców."""
import sqlite3
import unittest
from storage.database import _DeferredCommitConnection
from storage.db_inventory import DatabaseInventoryMixin

MAX = (1 << 63) - 1


class CraftingDB(DatabaseInventoryMixin):
    def __init__(self):
        self.conn = _DeferredCommitConnection(sqlite3.connect(':memory:'))
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript('''
            CREATE TABLE inventory (account_id INTEGER, item_id TEXT, quantity INTEGER,
                PRIMARY KEY(account_id,item_id));
            CREATE TABLE profession_storage (account_id INTEGER, container TEXT,
                item_id TEXT, quantity INTEGER, PRIMARY KEY(account_id,container,item_id));
            CREATE TABLE bank_items (account_id INTEGER, item_id TEXT, quantity INTEGER,
                PRIMARY KEY(account_id,item_id));
            CREATE TABLE shop_purchase_lots_v1175 (account_id INTEGER, item_id TEXT,
                paid_silver INTEGER, quantity INTEGER,
                PRIMARY KEY(account_id,item_id,paid_silver));
        ''')

    def put(self, item, qty, location='inventory'):
        if location == 'inventory':
            self.conn.execute('INSERT INTO inventory VALUES (?,?,?)', (1,item,qty))
        else:
            self.conn.execute('INSERT INTO profession_storage VALUES (?,?,?,?)',
                              (1,'craftbox',item,qty))
        self.conn.commit()

    def rows(self):
        return (
            list(self.conn.execute('SELECT * FROM inventory ORDER BY item_id')),
            list(self.conn.execute('SELECT * FROM profession_storage ORDER BY item_id')),
            list(self.conn.execute('SELECT * FROM shop_purchase_lots_v1175')),
        )


class CraftingAtomicTest(unittest.TestCase):
    def setUp(self):
        self.db = CraftingDB()

    def tearDown(self):
        self.db.conn.close()

    def test_integer_sum_above_int64_without_overflow(self):
        self.db.put('a',MAX)
        self.db.put('b',MAX, 'storage')
        self.assertEqual(self.db.total_items_across_storage_and_inventory(1,['a','b'],'craftbox'),2*MAX)

    def test_duplicate_ids_count_once(self):
        self.db.put('a', 2)
        self.assertEqual(self.db.total_items_across_storage_and_inventory(1,['a','a']),2)
        self.assertFalse(self.db.consume_items_across_storage_and_inventory(1,['a','a'],3))
        self.assertEqual(self.db.item_qty(1,'a'),2)

    def test_insufficient_stock_removes_nothing(self):
        self.db.put('a',1,'storage')
        self.db.put('b',3)
        before=self.db.rows()
        self.assertFalse(self.db.consume_items_across_storage_and_inventory(1,['a','b'],5,'craftbox'))
        self.assertEqual(self.db.rows(),before)

    def test_consume_mixed_storage_and_inventory(self):
        self.db.put('a',2,'storage')
        self.db.put('b',4)
        self.assertTrue(self.db.consume_items_across_storage_and_inventory(1,['b','a'],5,'craftbox'))
        self.assertEqual(self.db.storage_qty(1,'craftbox','a'),0)
        self.assertEqual(self.db.item_qty(1,'b'),1)

    def test_failed_later_inventory_removal_rolls_back_storage_and_lots(self):
        self.db.put('a',2,'storage')
        self.db.put('b',4)
        self.db.conn.execute('INSERT INTO shop_purchase_lots_v1175 VALUES (1,\'b\',50,4)')
        self.db.conn.execute('''CREATE TRIGGER fail_remove BEFORE UPDATE ON inventory
            WHEN NEW.item_id='b' BEGIN SELECT RAISE(ABORT,'fail b'); END''')
        before=self.db.rows()
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.consume_items_across_storage_and_inventory(1,['a','b'],5,'craftbox')
        self.assertEqual(self.db.rows(),before)
        self.db.conn.execute('DROP TRIGGER fail_remove')
        self.assertTrue(self.db.consume_items_across_storage_and_inventory(1,['a','b'],5,'craftbox'))
        self.assertEqual(self.db.item_qty(1,'b'),1)
        self.assertEqual(self.db.conn.execute('SELECT quantity FROM shop_purchase_lots_v1175').fetchone()[0],1)

    def test_nested_outer_savepoint_can_be_rolled_back(self):
        self.db.put('a',3)
        self.db.conn.execute('SAVEPOINT caller')
        self.assertTrue(self.db.consume_items_across_storage_and_inventory(1,['a'],2))
        self.assertEqual(self.db.item_qty(1,'a'),1)
        self.db.conn.execute('ROLLBACK TO SAVEPOINT caller')
        self.db.conn.execute('RELEASE SAVEPOINT caller')
        self.assertEqual(self.db.item_qty(1,'a'),3)

    def test_reject_corrupted_quantities_without_any_change(self):
        self.db.put('a',3.25)
        before=self.db.rows()
        with self.assertRaises((ValueError,TypeError)):
            self.db.total_items_across_storage_and_inventory(1,['a'])
        with self.assertRaises((ValueError,TypeError)):
            self.db.consume_items_across_storage_and_inventory(1,['a'],2)
        self.assertEqual(self.db.rows(),before)

    def test_reject_invalid_needed(self):
        for value in (-1,1.2,True,MAX+1):
            with self.assertRaises((ValueError,TypeError,OverflowError)):
                self.db.consume_items_across_storage_and_inventory(1,['a'],value)
        self.assertTrue(self.db.consume_items_across_storage_and_inventory(1,['a'],0))

    def test_parameter_batching_above_450(self):
        ids=[f'test{i}' for i in range(600)]
        self.db.put(ids[-1],2)
        self.assertEqual(self.db.total_items_across_storage_and_inventory(1,ids),2)
        self.assertTrue(self.db.consume_items_across_storage_and_inventory(1,ids,1))

    def test_add_item_no_float_overflow(self):
        self.db.put('gem', MAX)
        before=self.db.rows()
        with self.assertRaises(OverflowError):
            self.db.add_item(1,'gem',1)
        self.assertEqual(self.db.rows(),before)
        with self.assertRaises(TypeError):
            self.db.add_item(1,'gem',1.5)

    def test_storage_add_no_float_overflow(self):
        self.db.put('ore', MAX, 'storage')
        before=self.db.rows()
        with self.assertRaises(OverflowError):
            self.db.add_storage_item(1,'craftbox','ore',1)
        self.assertEqual(self.db.rows(),before)

    def test_bank_add_no_float_overflow(self):
        self.db.conn.execute('INSERT INTO bank_items VALUES (1, ?, ?)',('gem',MAX))
        with self.assertRaises(OverflowError):
            self.db.add_bank_item(1,'gem',1)
        self.assertEqual(self.db.conn.execute('SELECT quantity FROM bank_items').fetchone()[0],MAX)


def run():
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(CraftingAtomicTest)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    if not result.wasSuccessful():
        raise AssertionError('v104 craft atomic failed')
    return result.testsRun

if __name__ == '__main__':
    print('V104 CRAFT/QUEST ATOMIC:',run(),'PASS')
