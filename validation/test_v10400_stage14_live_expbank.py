# -*- coding: utf-8 -*-
"""Etap 14: aktywna ścieżka EXP Bank, tylko SQLite :memory: / plik tymczasowy.

Bez importu server.py, bez otwierania portów i bez danych użytkownika.
"""
from __future__ import annotations
import sqlite3
import tempfile
from pathlib import Path
import unittest

from storage.db_experience_bank_v2011 import DatabaseExperienceBankV2011Mixin
from storage.database import _DeferredCommitConnection


class Bank(DatabaseExperienceBankV2011Mixin):
    def __init__(self, file=':memory:', *, defer=False):
        raw = sqlite3.connect(file)
        raw.execute('PRAGMA foreign_keys=ON')
        self.conn = _DeferredCommitConnection(raw) if defer else raw
        self.conn.execute('CREATE TABLE IF NOT EXISTS accounts(id INTEGER PRIMARY KEY)')
        self.conn.executemany('INSERT OR IGNORE INTO accounts(id) VALUES(?)', [(1,), (2,)])
        self.conn.commit()
        self.create_experience_bank_schema_v2011()

    def balance(self, account=1, kind='character', key=''):
        r = self.conn.execute('SELECT balance FROM experience_bank_v2011 WHERE account_id=? AND kind=? AND source_key=?', (account, kind, key)).fetchone()
        return None if r is None else r[0]


class LiveBankStage14Tests(unittest.TestCase):
    def setUp(self):
        self.db = Bank()

    def tearDown(self):
        self.db.conn.close()

    def test_zero_cap_never_drops_xp(self):
        self.assertEqual(self.db.allocate_experience_bank_v2011(1, 5000, 'character', '', 0), 0)
        self.assertEqual(self.db.balance(), '5000')
        self.assertEqual(self.db.allocate_experience_bank_v2011(1, 1, 'character', '', 100), 2)
        self.assertEqual(self.db.balance(), '4999')

    def test_zero_amount_creates_no_rows(self):
        self.assertEqual(self.db.allocate_experience_bank_v2011(1, 0, 'character', '', 0), 0)
        self.assertIsNone(self.db.balance())

    def test_no_loss_math_and_repay_one_to_one(self):
        amount=100000
        paid=self.db.allocate_experience_bank_v2011(1, amount, 'character', '', 500)
        self.assertEqual(paid, 500)
        self.assertEqual(int(self.db.balance())+paid, amount)
        previous=int(self.db.balance())
        paid2=self.db.allocate_experience_bank_v2011(1, 5, 'character', '', 500)
        self.assertEqual(paid2, 10)
        self.assertEqual(previous+5, paid2+int(self.db.balance()))

    def test_huge_balance_text_no_float(self):
        huge=10**100
        self.assertEqual(self.db.allocate_experience_bank_v2011(1, huge, 'soul', '', 300), 300)
        self.assertEqual(self.db.balance(kind='soul'), str(huge-300))

    def test_4000_digit_balance(self):
        huge=10**3900
        self.assertEqual(self.db.allocate_experience_bank_v2011(1, huge, 'character', '', 0), 0)
        self.assertEqual(self.db.balance(), str(huge))

    def test_over_budget_guard_atomic(self):
        huge=int("9" * 4096)
        # Addition of two 4096-digit nines must be refused before TEXT write.
        self.db.conn.execute('INSERT INTO experience_bank_v2011 VALUES(?,?,?,?)', (1,'character','',str(huge)))
        old=self.db.balance()
        with self.assertRaises(ValueError):
            self.db.allocate_experience_bank_v2011(1, huge, 'character', '', 0)
        self.assertEqual(self.db.balance(), old)

    def test_axis_independence(self):
        for kind,key in (('stat','strength'),('stat','dexterity'),('class','Mag'),('class','Wojownik'),('tool','pickaxe'),('profession','Gornictwo')):
            self.db.allocate_experience_bank_v2011(1,3000,kind,key,0)
        self.assertEqual(len(self.db.experience_bank_rows_v2011(1)),6)
        self.assertEqual(self.db.experience_bank_rows_v2011(2),[])

    def test_source_normalization(self):
        self.db.allocate_experience_bank_v2011(1,500,'character','SOMETHING',0)
        self.assertEqual(self.db.balance(), '500')
        self.assertIsNone(self.db.balance(key='SOMETHING'))

    def test_corrupt_negative_balance_does_not_disappear(self):
        self.db.conn.execute('INSERT INTO experience_bank_v2011 VALUES(?,?,?,?)', (1,'soul','','-9'))
        with self.assertRaises(ValueError):self.db.allocate_experience_bank_v2011(1,50,'soul','',100)
        self.assertEqual(self.db.balance(kind='soul'), '-9')
        with self.assertRaises(ValueError):self.db.experience_bank_rows_v2011(1)

    def test_corrupt_decimal_balance_does_not_disappear(self):
        self.db.conn.execute('INSERT INTO experience_bank_v2011 VALUES(?,?,?,?)', (1,'character','','3.14'))
        with self.assertRaises(ValueError):self.db.allocate_experience_bank_v2011(1,50,'character','',100)
        self.assertEqual(self.db.balance(), '3.14')

    def test_float_bool_negative_rejected(self):
        for amount,cap in ((1.5,100),(True,100),(-5,100),(5,5.0),(5,-1),(5,True)):
            with self.subTest(amount=amount,cap=cap),self.assertRaises((TypeError,ValueError)):
                self.db.allocate_experience_bank_v2011(1,amount,'character','',cap)
        self.assertIsNone(self.db.balance())

    def test_invalid_identity_or_axis_rejected(self):
        for account,kind,key in ((0,'character',''),(True,'character',''),(1,'invalid',''),(1,'class','x'*161)):
            with self.subTest(account=account,kind=kind),self.assertRaises(ValueError):
                self.db.allocate_experience_bank_v2011(account,5,kind,key,100)

    def test_fk_failure_no_ghost_balance(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.allocate_experience_bank_v2011(3,50,'character','',0)
        self.assertIsNone(self.db.balance(3))
        self.assertEqual(self.db.allocate_experience_bank_v2011(1,50,'character','',0),0)
        self.assertEqual(self.db.balance(),'50')

    def test_trigger_failure_atomic(self):
        self.db.conn.execute("CREATE TRIGGER fail_insert BEFORE INSERT ON experience_bank_v2011 BEGIN SELECT RAISE(ABORT,'no'); END")
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.allocate_experience_bank_v2011(1,100,'character','',0)
        self.assertIsNone(self.db.balance())
        self.db.conn.execute('DROP TRIGGER fail_insert')
        self.assertEqual(self.db.allocate_experience_bank_v2011(1,100,'character','',0),0)
        self.assertEqual(self.db.balance(),'100')

    def test_parent_savepoint_and_deferred_commit(self):
        self.db.conn.close()
        self.db=Bank(defer=True)
        with self.db.conn.deferred_commits():
            self.db.conn.execute('SAVEPOINT outer_test')
            self.db.allocate_experience_bank_v2011(1,100,'class','Mag',0)
            self.db.conn.execute('ROLLBACK TO SAVEPOINT outer_test')
            self.db.conn.execute('RELEASE SAVEPOINT outer_test')
        self.assertIsNone(self.db.balance(kind='class',key='Mag'))

    def test_real_experience_gateway_zero_cap(self):
        # Live combat/quest systems call this gateway, not the storage helper.
        from systems.experience_bank_v2011 import banked_experience_v2011
        self.db.multi_cap_v23215 = lambda account_id: 0
        self.assertEqual(banked_experience_v2011(
            self.db, 1, 123456, 'soul', 9000), 0)
        self.assertEqual(self.db.balance(kind='soul'), '123456')
        self.db.multi_cap_v23215 = lambda account_id: 100
        self.assertEqual(banked_experience_v2011(
            self.db, 1, 5, 'soul', 9000, overcap=True), 10)
        self.assertEqual(self.db.balance(kind='soul'), '123451')

    def test_real_gateway_independent_cap_per_class(self):
        from systems.experience_bank_v2011 import banked_experience_v2011
        self.db.multi_cap_v23215 = lambda account_id: 50
        self.assertEqual(banked_experience_v2011(
            self.db, 1, 500, 'class', 9000, source_key='Mag'), 50)
        self.assertEqual(banked_experience_v2011(
            self.db, 1, 500, 'class', 9000, source_key='Wojownik'), 50)
        self.assertEqual(self.db.balance(kind='class',key='Mag'), '450')
        self.assertEqual(self.db.balance(kind='class',key='Wojownik'), '450')

    def test_restart_preserves_balance(self):
        with tempfile.TemporaryDirectory() as temp:
            path=str(Path(temp)/'progress.db')
            db=Bank(path)
            db.allocate_experience_bank_v2011(1,10**80,'character','',0)
            db.conn.close()
            db=Bank(path)
            self.assertEqual(db.balance(),str(10**80))
            self.assertEqual(db.conn.execute('PRAGMA integrity_check').fetchone()[0],'ok')
            db.conn.close()


def run():
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(LiveBankStage14Tests)
    out=unittest.TextTestRunner(verbosity=1).run(suite)
    if not out.wasSuccessful():raise AssertionError('V104 etap14 EXP Bank FAIL')
    return out.testsRun

if __name__=='__main__':print('V104 ETAP 14 BANK EXP:',run(),'PASS',flush=True)
