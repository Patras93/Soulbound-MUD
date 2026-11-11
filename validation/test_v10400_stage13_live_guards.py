# -*- coding: utf-8 -*-
"""Test ochrony rzeczywistych metod banku, profesji i narzedzi; SQLite :memory:."""
import sqlite3
import unittest
from storage.db_inventory import DatabaseInventoryMixin
from core.sqlite_numeric_guard_v10400 import SQLiteNumericLimitV104


class DB(DatabaseInventoryMixin):
    def master_account_for_character(self, account_id): return account_id


class LiveGuardsTest(unittest.TestCase):
    def setUp(self):
        self.d=DB()
        self.d.conn=sqlite3.connect(':memory:')
        self.d.conn.row_factory=sqlite3.Row
        self.d.conn.executescript('''
            CREATE TABLE bank_balances(account_id INTEGER PRIMARY KEY,
                silver INTEGER, gold INTEGER, mithril INTEGER);
            INSERT INTO bank_balances VALUES(1,100,0,0);
            CREATE TABLE professions(account_id INTEGER,profession TEXT,
                level INTEGER,xp INTEGER,actions INTEGER,PRIMARY KEY(account_id,profession));
            INSERT INTO professions VALUES(1,'Alchemia',6000,25,1);
            CREATE TABLE tools(account_id INTEGER,tool_type TEXT,
                level INTEGER,xp INTEGER,uses INTEGER,PRIMARY KEY(account_id,tool_type));
            INSERT INTO tools VALUES(1,'Mlot',6000,30,2);
        ''')
    def tearDown(self): self.d.conn.close()

    def test_bank_rejects_real_and_text(self):
        for value in (1.5, '200x', 'bad'):
            self.d.conn.execute('UPDATE bank_balances SET silver=?',(value,))
            with self.assertRaises(TypeError):self.d.bank_balance(1)
            self.assertEqual(self.d.conn.execute('SELECT silver FROM bank_balances').fetchone()[0],value)

    def test_bank_valid_change(self):
        self.assertTrue(self.d.change_bank_currency(1,'silver',250))
        self.assertEqual(self.d.bank_balance(1)['silver'],350)

    def test_bank_huge_change_safe(self):
        with self.assertRaises(SQLiteNumericLimitV104):self.d.change_bank_currency(1,'silver',10**100)
        self.assertEqual(self.d.bank_balance(1)['silver'],100)

    def test_bank_rejects_noninteger_delta(self):
        with self.assertRaises(TypeError):self.d.change_bank_currency(1,'gold',1.5)
        self.assertEqual(self.d.bank_balance(1)['silver'],100)

    def test_profession_valid(self):
        self.d.save_profession(1,'Alchemia',6001,500,8)
        row=self.d.conn.execute('SELECT level,xp,actions FROM professions').fetchone()
        self.assertEqual(tuple(row),(6001,500,8))

    def test_profession_overflow_never_changes_row(self):
        before=tuple(self.d.conn.execute('SELECT level,xp,actions FROM professions').fetchone())
        for args in ((10**100,100,9),(6001,10**100,9),(6001,100,10**100)):
            with self.assertRaises(SQLiteNumericLimitV104):self.d.save_profession(1,'Alchemia',*args)
            self.assertEqual(tuple(self.d.conn.execute('SELECT level,xp,actions FROM professions').fetchone()),before)

    def test_tool_valid(self):
        self.d.save_tool(1,'Mlot',6001,900,3)
        self.assertEqual(tuple(self.d.conn.execute('SELECT level,xp,uses FROM tools').fetchone()),(6001,900,3))

    def test_tool_overflow_never_changes_row(self):
        before=tuple(self.d.conn.execute('SELECT level,xp,uses FROM tools').fetchone())
        for args in ((10**100,900,3),(6001,10**100,3),(6001,900,10**100)):
            with self.assertRaises(SQLiteNumericLimitV104):self.d.save_tool(1,'Mlot',*args)
            self.assertEqual(tuple(self.d.conn.execute('SELECT level,xp,uses FROM tools').fetchone()),before)

    def test_tool_rejects_float(self):
        with self.assertRaises(TypeError):self.d.save_tool(1,'Mlot',6001,1.25,8)


def run():
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(LiveGuardsTest)
    out=unittest.TextTestRunner(verbosity=0).run(suite)
    if not out.wasSuccessful():raise AssertionError('V104 etap13 guards failed')
    return out.testsRun

if __name__=='__main__':print('V104 GUARDS:',run(),'PASS',flush=True)
