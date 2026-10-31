# -*- coding: utf-8 -*-
"""v104: regression for ownership of market/escrow/fleet transactions."""
from __future__ import annotations
import sqlite3
import unittest
from systems.imperial_economy_v1320 import atomic

class ImperialAtomicOwnershipTests(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(':memory:')
        self.conn.execute('CREATE TABLE ledger (id INTEGER PRIMARY KEY, coins INTEGER)')
        self.conn.commit()

    def tearDown(self):
        self.conn.close()

    def test_nested_operation_preserves_outer_rollback(self):
        self.conn.execute('BEGIN')
        self.conn.execute('INSERT INTO ledger VALUES(1,10)')
        with atomic(self.conn):
            self.conn.execute('INSERT INTO ledger VALUES(2,20)')
        self.assertTrue(self.conn.in_transaction)
        self.conn.rollback()
        self.assertEqual(self.conn.execute('SELECT count(*) FROM ledger').fetchone()[0],0)

    def test_standalone_operation_persists(self):
        with atomic(self.conn):
            self.conn.execute('INSERT INTO ledger VALUES(1,10)')
        self.assertFalse(self.conn.in_transaction)
        self.assertEqual(self.conn.execute('SELECT coins FROM ledger').fetchone()[0],10)

    def test_inner_error_does_not_discard_caller_changes(self):
        self.conn.execute('BEGIN')
        self.conn.execute('INSERT INTO ledger VALUES(1,10)')
        with self.assertRaisesRegex(ValueError,'abort'):
            with atomic(self.conn):
                self.conn.execute('INSERT INTO ledger VALUES(2,20)')
                raise ValueError('abort')
        self.assertTrue(self.conn.in_transaction)
        self.assertEqual(self.conn.execute('SELECT id FROM ledger').fetchall(),[(1,)])
        self.conn.commit()
        self.assertEqual(self.conn.execute('SELECT id FROM ledger').fetchall(),[(1,)])

    def test_two_nested_savepoints_keep_parent(self):
        self.conn.execute('BEGIN')
        with atomic(self.conn):
            self.conn.execute('INSERT INTO ledger VALUES(1,10)')
            with atomic(self.conn):
                self.conn.execute('INSERT INTO ledger VALUES(2,20)')
        self.assertTrue(self.conn.in_transaction)
        self.conn.rollback()
        self.assertEqual(self.conn.execute('SELECT count(*) FROM ledger').fetchone()[0],0)

    def test_nested_error_rolls_back_only_inner(self):
        self.conn.execute('BEGIN')
        with atomic(self.conn):
            self.conn.execute('INSERT INTO ledger VALUES(1,10)')
            with self.assertRaises(ValueError):
                with atomic(self.conn):
                    self.conn.execute('INSERT INTO ledger VALUES(2,20)')
                    raise ValueError('cancel')
            self.assertEqual(self.conn.execute('SELECT id FROM ledger').fetchall(),[(1,)])
        self.conn.rollback()
        self.assertEqual(self.conn.execute('SELECT count(*) FROM ledger').fetchone()[0],0)

    def test_standalone_failure_leaves_no_active_transaction(self):
        with self.assertRaises(RuntimeError):
            with atomic(self.conn):
                self.conn.execute('INSERT INTO ledger VALUES(1,10)')
                raise RuntimeError('fail')
        self.assertFalse(self.conn.in_transaction)
        self.assertEqual(self.conn.execute('SELECT count(*) FROM ledger').fetchone()[0],0)


    def test_initializers_preserve_external_transaction(self):
        from systems import imperial_economy_v1320 as empire
        from systems import imperial_economy_v1321 as fleet
        from systems import economy4_v1360 as caravans
        for module, table in ((empire, 'empire_armies_v1320'),
                              (fleet, 'shipyard_ships_v1321'),
                              (caravans, 'trade_orders_v1360')):
            with self.subTest(module=module.__name__):
                self.conn.execute('BEGIN')
                self.conn.execute('INSERT INTO ledger VALUES(1,10)')
                module.init(self.conn)
                self.assertTrue(self.conn.in_transaction)
                self.assertIsNotNone(self.conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone())
                self.conn.rollback()
                self.assertEqual(self.conn.execute('SELECT COUNT(*) FROM ledger').fetchone()[0],0)
                self.assertIsNone(self.conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,)).fetchone())

    def test_initializers_standalone_and_idempotent(self):
        from systems import imperial_economy_v1320 as empire
        from systems import imperial_economy_v1321 as fleet
        from systems import economy4_v1360 as caravans
        for module in (empire, fleet, caravans):
            module.init(self.conn)
            module.init(self.conn)
            self.assertFalse(self.conn.in_transaction)

    def test_create_schema_fails_closed_and_rolls_back(self):
        from storage.sqlite_ddl_safe_v10400 import apply_create_schema_v104
        self.conn.execute('BEGIN')
        self.conn.execute('INSERT INTO ledger VALUES(1,10)')
        with self.assertRaisesRegex(ValueError, 'Niedozwolone'):
            apply_create_schema_v104(self.conn,
                'CREATE TABLE IF NOT EXISTS disposable (id INTEGER);\n'
                'DELETE FROM ledger;\n')
        self.assertTrue(self.conn.in_transaction)
        self.assertIsNone(self.conn.execute(
            "SELECT name FROM sqlite_master WHERE name='disposable'").fetchone())
        self.assertEqual(self.conn.execute('SELECT count(*) FROM ledger').fetchone()[0],1)
        self.conn.rollback()
        self.assertEqual(self.conn.execute('SELECT count(*) FROM ledger').fetchone()[0],0)

def run():
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(ImperialAtomicOwnershipTests)
    result=unittest.TextTestRunner(verbosity=0).run(suite)
    if not result.wasSuccessful():
        raise AssertionError('Imperial escrow transaction ownership regression FAILED')
    return result.testsRun

if __name__ == '__main__':
    raise SystemExit(0 if run()==9 else 1)
