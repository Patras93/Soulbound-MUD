# -*- coding: utf-8 -*-
"""No server startup, soundpack or external service required."""
import sqlite3
import unittest
from systems.v115 import fame_queue as q

class QueueTests(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        self.db.execute('CREATE TABLE balances (account INTEGER PRIMARY KEY, xp INTEGER DEFAULT 0, fame INTEGER DEFAULT 0)')
        self.db.execute('INSERT INTO balances VALUES(7,0,0)')
        q.ensure_schema(self.db)
        self.start = 1_000_000.0
        self.assertTrue(q.schedule_fame(self.db,7,'kraina','boss','Boss',reward_xp=1500,now=self.start))
        self.due=self.start+q.deterministic_delay(7,'kraina','boss')
    def add_xp(self, conn, amount):
        conn.execute('UPDATE balances SET xp=xp+? WHERE account=7',(amount,))
    def add_fame(self, conn, amount):
        conn.execute('UPDATE balances SET fame=fame+? WHERE account=7',(amount,))
    def balance(self):
        return self.db.execute('SELECT xp,fame FROM balances WHERE account=7').fetchone()
    def test_delay_and_order(self):
        self.assertEqual(q.due_events(self.db,7,now=self.due-0.1),[])
        self.assertFalse(q.settle_fame(self.db,7,'kraina','boss',self.add_fame,now=self.due))
        self.assertTrue(q.settle_exp(self.db,7,'kraina','boss',self.add_xp,now=self.due))
        self.assertEqual(self.balance(),(1500,0))
        self.assertFalse(q.settle_fame(self.db,7,'kraina','boss',self.add_fame,now=self.due+1.9))
        self.assertTrue(q.settle_fame(self.db,7,'kraina','boss',self.add_fame,now=self.due+2))
        self.assertEqual(self.balance(),(1500,1))
    def test_idempotent(self):
        self.assertFalse(q.schedule_fame(self.db,7,'kraina','boss','Boss',reward_xp=999999,now=self.start))
        self.assertTrue(q.settle_exp(self.db,7,'kraina','boss',self.add_xp,now=self.due))
        self.assertFalse(q.settle_exp(self.db,7,'kraina','boss',self.add_xp,now=self.due+1))
        self.assertTrue(q.settle_fame(self.db,7,'kraina','boss',self.add_fame,now=self.due+2))
        self.assertFalse(q.settle_fame(self.db,7,'kraina','boss',self.add_fame,now=self.due+3))
        self.assertEqual(self.balance(),(1500,1))
    def test_atomic_rollback(self):
        def bad(conn,amount):
            self.add_xp(conn,amount)
            raise RuntimeError('failed payout')
        with self.assertRaises(RuntimeError):
            q.settle_exp(self.db,7,'kraina','boss',bad,now=self.due)
        self.assertEqual(self.balance(),(0,0))
        self.assertEqual(q.due_events(self.db,7,now=self.due)[0][3],'WAITING')
    def test_persistent_restart(self):
        self.db.commit()
        dump='\n'.join(self.db.iterdump())
        reopened=sqlite3.connect(':memory:')
        reopened.executescript(dump)
        self.assertEqual(q.due_events(reopened,7,now=self.due)[0][4],1500)
    def test_two_accounts_and_ranges(self):
        self.assertTrue(q.schedule_fame(self.db,8,'kraina','boss','Boss',reward_xp=20,now=self.start))
        self.assertFalse(q.due_events(self.db,8,now=self.start))
        self.assertEqual(len(q.due_events(self.db,7,now=self.due)),1)
        for acct in range(1,100):
            self.assertTrue(60<=q.deterministic_delay(acct,'a','b')<=300)
    def test_migration_old_v115_table(self):
        c=sqlite3.connect(':memory:')
        c.execute('''CREATE TABLE v115_fame_delivery (account_id INTEGER,region TEXT,boss_id TEXT,boss_name TEXT,due_at REAL,fame_due_at REAL,status TEXT,created_at REAL,PRIMARY KEY(account_id,region,boss_id))''')
        q.ensure_schema(c)
        self.assertIn('reward_xp',{r[1] for r in c.execute('PRAGMA table_info(v115_fame_delivery)')})
        self.assertIn('fame_points',{r[1] for r in c.execute('PRAGMA table_info(v115_fame_delivery)')})
    def test_no_soundpack_import(self):
        import ast, inspect
        tree=ast.parse(inspect.getsource(q))
        imports=[n.module for n in ast.walk(tree) if isinstance(n, ast.ImportFrom)]
        imports += [alias.name for n in ast.walk(tree) if isinstance(n, ast.Import) for alias in n.names]
        self.assertFalse(any('sound' in (name or '') for name in imports))

if __name__=='__main__': unittest.main()
