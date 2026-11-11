# -*- coding: utf-8 -*-
"""SQLite tests: full set of rolled loot from one kill is atomic."""
import sqlite3
import unittest
from types import SimpleNamespace
from storage.database import _DeferredCommitConnection
from storage.db_inventory import DatabaseInventoryMixin
from systems.atomic_party_loot_v10400 import (
    grant_party_loot_batch_atomic_v10400, grant_party_loot_atomic_v10400)


class LootDB(DatabaseInventoryMixin):
    def __init__(self):
        self.conn = _DeferredCommitConnection(sqlite3.connect(':memory:'))
        self.conn.executescript('''
            CREATE TABLE inventory (account_id INTEGER, item_id TEXT, quantity INTEGER NOT NULL,
                PRIMARY KEY(account_id,item_id));
            CREATE TABLE profession_storage (account_id INTEGER, container TEXT,
                item_id TEXT, quantity INTEGER NOT NULL,
                PRIMARY KEY(account_id,container,item_id));
        ''')
    def close(self): self.conn.close()


class AllRollsAtomic(unittest.TestCase):
    def setUp(self):
        self.db = LootDB()
        self.p = [SimpleNamespace(account_id=i) for i in (1, 2, 3)]
    def tearDown(self): self.db.close()
    def inventory(self):
        return list(self.db.conn.execute('SELECT account_id,item_id,quantity FROM inventory ORDER BY account_id,item_id'))
    def storage(self):
        return list(self.db.conn.execute('SELECT account_id,container,item_id,quantity FROM profession_storage ORDER BY account_id,item_id'))
    def rolls(self):
        return [
            (self.p, 'sword', False, None),
            (self.p, 'ore', True, 'ore'),
            (self.p[:2], 'relic', False, None),
            (self.p, 'trophy', False, None),
            (self.p, 'badge', False, None),
        ]

    def test_all_sources_paid_together(self):
        result = grant_party_loot_batch_atomic_v10400(self.db, self.rolls())
        self.assertEqual(result, ((1,2,3),(1,2,3),(1,2),(1,2,3),(1,2,3)))
        self.assertEqual(len(self.inventory()), 3*3 + 2)
        self.assertEqual(len(self.storage()), 3)

    def test_last_roll_failure_rolls_back_everything(self):
        self.db.conn.execute('''CREATE TRIGGER fail_last BEFORE INSERT ON inventory
            WHEN NEW.account_id=3 AND NEW.item_id='badge'
            BEGIN SELECT RAISE(ABORT,'last roll'); END''')
        with self.assertRaises(sqlite3.IntegrityError):
            grant_party_loot_batch_atomic_v10400(self.db,self.rolls())
        self.assertEqual(self.inventory(), [])
        self.assertEqual(self.storage(), [])
        self.db.conn.execute('DROP TRIGGER fail_last')
        grant_party_loot_batch_atomic_v10400(self.db,self.rolls())
        self.assertEqual(len(self.inventory()),11)

    def test_storage_roll_failure_restores_normal_drop(self):
        self.db.conn.execute('''CREATE TRIGGER fail_storage BEFORE INSERT ON profession_storage
            WHEN NEW.account_id=2 BEGIN SELECT RAISE(ABORT,'storage'); END''')
        with self.assertRaises(sqlite3.IntegrityError):
            grant_party_loot_batch_atomic_v10400(self.db,self.rolls())
        self.assertEqual(self.inventory(), [])

    def test_repeated_item_aggregate_boundary(self):
        lim=(1<<63)-1
        self.db.conn.execute('INSERT INTO inventory VALUES (1,?,?)',('badge',lim-1))
        with self.assertRaises(OverflowError):
            grant_party_loot_batch_atomic_v10400(self.db,[
                ([1,2],'badge',False,None),([1,2],'badge',False,None)])
        self.assertEqual(self.inventory(),[(1,'badge',lim-1)])

    def test_same_item_two_rolls_is_two_copies(self):
        grant_party_loot_batch_atomic_v10400(self.db,[
            ([1,2],'badge',False,None),([1,2],'badge',False,None)])
        self.assertEqual(self.inventory(),[(1,'badge',2),(2,'badge',2)])

    def test_preexisting_transaction_preserved_on_failure(self):
        self.db.conn.execute('INSERT INTO inventory VALUES (1,?,?)',('old',1))
        self.db.conn.execute('''CREATE TRIGGER fail_badge BEFORE INSERT ON inventory
            WHEN NEW.item_id='badge' BEGIN SELECT RAISE(ABORT,'bad'); END''')
        with self.assertRaises(sqlite3.IntegrityError):
            grant_party_loot_batch_atomic_v10400(self.db,self.rolls())
        self.assertEqual(self.inventory(),[(1,'old',1)])

    def test_caller_can_rollback_successful_full_party_loot(self):
        # A quest/kill coordinator may have its own outer SQLite transaction.
        # Successful inventory settlement must not commit it prematurely.
        self.db.conn.execute('SAVEPOINT whole_kill')
        self.db.conn.execute('INSERT INTO inventory VALUES (1,?,?)', ('old', 1))
        grant_party_loot_batch_atomic_v10400(self.db, self.rolls())
        self.assertTrue(self.db.conn.in_transaction)
        self.assertGreater(len(self.inventory()), 1)
        self.db.conn.execute('ROLLBACK TO SAVEPOINT whole_kill')
        self.db.conn.execute('RELEASE SAVEPOINT whole_kill')
        self.assertEqual(self.inventory(), [])
        self.assertEqual(self.storage(), [])

    def test_corrupt_real_rejected_without_writes(self):
        self.db.conn.execute('INSERT INTO inventory VALUES (1,?,?)',('badge',1.5))
        with self.assertRaises(ValueError):
            grant_party_loot_batch_atomic_v10400(self.db, self.rolls())
        self.assertEqual(len(self.inventory()),1)

    def test_bad_recipient_any_roll_aborts_all(self):
        for bad in (0,-1,'1',True,None):
            with self.assertRaises(ValueError):
                grant_party_loot_batch_atomic_v10400(self.db,[
                    (self.p,'sword',False,None), ([bad],'badge',False,None)])
        self.assertEqual(self.inventory(),[])

    def test_no_rolls_and_empty_party(self):
        self.assertEqual(grant_party_loot_batch_atomic_v10400(self.db,[]),())
        self.assertEqual(grant_party_loot_batch_atomic_v10400(self.db,[((), 'sword',False,None)]),((),))
        self.assertEqual(self.inventory(),[])

    def test_legacy_helper_remains_compatible(self):
        self.assertEqual(grant_party_loot_atomic_v10400(self.db, self.p, 'sword'),(1,2,3))
        self.assertEqual(self.inventory(),[(i,'sword',1) for i in (1,2,3)])


def run():
    result=unittest.TextTestRunner(verbosity=1).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(AllRollsAtomic))
    if not result.wasSuccessful():
        raise AssertionError('All-roll transaction tests failed')
    return result.testsRun

if __name__=='__main__':
    print('ALL ROLLS ONE KILL:',run(),'PASS')
