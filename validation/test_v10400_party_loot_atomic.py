# -*- coding: utf-8 -*-
"""Real SQLite regression for the per-roll party item grants (no TCP)."""
import sqlite3
import unittest
from types import SimpleNamespace
from storage.database import _DeferredCommitConnection
from storage.db_inventory import DatabaseInventoryMixin
from systems.atomic_party_loot_v10400 import grant_party_loot_atomic_v10400


class LootDB(DatabaseInventoryMixin):
    def __init__(self):
        raw = sqlite3.connect(':memory:')
        self.conn = _DeferredCommitConnection(raw)
        self.conn.executescript('''
            CREATE TABLE inventory (account_id INTEGER, item_id TEXT, quantity INTEGER NOT NULL,
                PRIMARY KEY(account_id,item_id));
            CREATE TABLE profession_storage (account_id INTEGER, container TEXT,
                item_id TEXT, quantity INTEGER NOT NULL,
                PRIMARY KEY(account_id,container,item_id));
        ''')
    def close(self): self.conn.close()


class PartyLootAtomic(unittest.TestCase):
    def setUp(self):
        self.db = LootDB()
        self.party = [SimpleNamespace(account_id=n) for n in (1, 2, 3)]
    def tearDown(self): self.db.close()
    def items(self):
        return list(self.db.conn.execute('SELECT account_id,item_id,quantity FROM inventory ORDER BY account_id,item_id'))
    def storage(self):
        return list(self.db.conn.execute('SELECT account_id,container,item_id,quantity FROM profession_storage ORDER BY account_id,item_id'))

    def test_whole_party_receives_rolled_loot(self):
        awarded = grant_party_loot_atomic_v10400(self.db,self.party,'iron_sword')
        self.assertEqual(awarded,(1,2,3))
        self.assertEqual(self.items(),[(1,'iron_sword',1),(2,'iron_sword',1),(3,'iron_sword',1)])
        grant_party_loot_atomic_v10400(self.db,self.party,'iron_sword')
        self.assertEqual(self.items(),[(1,'iron_sword',2),(2,'iron_sword',2),(3,'iron_sword',2)])

    def test_storage_uses_source_id(self):
        grant_party_loot_atomic_v10400(self.db,self.party,'variant01',craftbox=True,craftbox_item_id='circuit')
        self.assertEqual(self.items(),[])
        self.assertEqual(self.storage(),[(n,'craftbox','circuit',1) for n in (1,2,3)])

    def test_inventory_failure_rolls_back_party(self):
        self.db.conn.execute('CREATE TRIGGER fail_third BEFORE INSERT ON inventory WHEN NEW.account_id=3 BEGIN SELECT RAISE(ABORT,\'third\'); END')
        with self.assertRaises(sqlite3.IntegrityError):
            grant_party_loot_atomic_v10400(self.db,self.party,'gem')
        self.assertEqual(self.items(),[])
        # Retry after removing fault; no duplicate items for earlier recipients.
        self.db.conn.execute('DROP TRIGGER fail_third')
        grant_party_loot_atomic_v10400(self.db,self.party,'gem')
        self.assertEqual(self.items(),[(n,'gem',1) for n in (1,2,3)])

    def test_storage_failure_rolls_back_party(self):
        self.db.conn.execute('CREATE TRIGGER fail_third BEFORE INSERT ON profession_storage WHEN NEW.account_id=3 BEGIN SELECT RAISE(ABORT,\'third\'); END')
        with self.assertRaises(sqlite3.IntegrityError):
            grant_party_loot_atomic_v10400(self.db,self.party,'circuit',craftbox=True)
        self.assertEqual(self.storage(),[])

    def test_preflight_overflow_does_not_change_anyone(self):
        maxv = (1<<63)-1
        self.db.conn.execute('INSERT INTO inventory VALUES (?,?,?)',(3,'gem',maxv))
        with self.assertRaises(OverflowError):
            grant_party_loot_atomic_v10400(self.db,self.party,'gem')
        self.assertEqual(self.items(),[(3,'gem',maxv)])

    def test_corrupt_real_quantity_rejected(self):
        self.db.conn.execute('INSERT INTO inventory VALUES (?,?,?)',(3,'gem',1.75))
        with self.assertRaises(ValueError):
            grant_party_loot_atomic_v10400(self.db,self.party,'gem')
        self.assertEqual(len(self.items()),1)

    def test_duplicate_recipient_rejected(self):
        with self.assertRaises(ValueError):
            grant_party_loot_atomic_v10400(self.db,[1,2,1],'gem')
        self.assertEqual(self.items(),[])

    def test_validation_is_before_writes(self):
        for bad in (['oops',1,2],[0],[-1],[(1,2)], [1,True]):
            with self.assertRaises(ValueError):
                grant_party_loot_atomic_v10400(self.db,bad,'gem')
        with self.assertRaises(ValueError):
            grant_party_loot_atomic_v10400(self.db,[1],'gem',craftbox=True,craftbox_item_id='')
        self.assertEqual(self.items(),[])

    def test_empty_party_no_write(self):
        self.assertEqual(grant_party_loot_atomic_v10400(self.db,[],'gem'),())
        self.assertEqual(self.items(),[])


def run():
    result=unittest.TextTestRunner(verbosity=1).run(
        unittest.defaultTestLoader.loadTestsFromTestCase(PartyLootAtomic))
    if not result.wasSuccessful():
        raise AssertionError('Atomic party loot tests failed')
    return result.testsRun

if __name__=='__main__': print('PARTY LOOT:',run(),'PASS')
