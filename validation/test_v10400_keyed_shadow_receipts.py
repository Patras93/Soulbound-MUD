# -*- coding: utf-8 -*-
"""Wykrywanie usuniecia jedynego wpisu EXP klasy/profesji/narzedzia.

Wszystkie dane sa syntetyczne i przechowywane w odizolowanym SQLite.
"""
from __future__ import annotations
import sqlite3
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from storage.big_number_copy_runtime_v10400 import (
    read_exact_class_xp_copy, write_exact_class_xp_copy,
    read_exact_work_xp_copy, write_exact_work_xp_copy,
)


class KeyedReceiptTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='sb104_key_receipt_')
        folder = Path(self.tmp.name)
        (folder / '.SOULBOUND_V104_WYLACZNIE_KOPIA_TESTOWA').write_text('TEST', encoding='utf-8')
        self.path = folder / 'SB104_OFFLINE_TEST.sqlite'
        self.conn = sqlite3.connect(self.path)
        self.db = SimpleNamespace(path=str(self.path), conn=self.conn)
        self.conn.execute('CREATE TABLE class_progress(account_id INTEGER, class_name TEXT, level INTEGER, xp INTEGER, PRIMARY KEY(account_id,class_name))')
        self.conn.execute('CREATE TABLE professions(account_id INTEGER, profession TEXT, level INTEGER, xp INTEGER, actions INTEGER, PRIMARY KEY(account_id,profession))')
        self.conn.execute('CREATE TABLE tools(account_id INTEGER, tool_type TEXT, level INTEGER, xp INTEGER, uses INTEGER, PRIMARY KEY(account_id,tool_type))')
        self.conn.execute('INSERT INTO class_progress VALUES (1,\'Mag\',80,5)')
        self.conn.execute('INSERT INTO professions VALUES (1,\'Kowalstwo\',7,6,10)')
        self.conn.execute('INSERT INTO tools VALUES (1,\'kilof\',4,7,11)')
        self.conn.commit()

    def tearDown(self):
        self.conn.close()
        self.tmp.cleanup()

    def _write(self, kind):
        huge = 10**120 + 123
        if kind == 'class':
            write_exact_class_xp_copy(self.db, 1, 'Mag', huge)
        else:
            write_exact_work_xp_copy(self.db, 1, kind, 'Kowalstwo' if kind == 'profession' else 'kilof',
                                     level=100, xp=huge, counter=34)
        return huge

    def _read(self, kind):
        return (read_exact_class_xp_copy(self.db, 1, 'Mag') if kind == 'class'
                else read_exact_work_xp_copy(self.db, 1, kind,
                     'Kowalstwo' if kind == 'profession' else 'kilof'))

    def test_class_missing_shadow_is_detected_after_reopen(self):
        value = self._write('class')
        self.conn.commit()
        self.conn.close()
        self.conn = sqlite3.connect(self.path)
        self.db.conn = self.conn
        self.assertEqual(self._read('class'), value)
        self.conn.execute("DELETE FROM big_number_shadow_v10400 WHERE axis='class_progress.xp'")
        with self.assertRaisesRegex(ValueError, 'brak dokładnego rekordu'):
            self._read('class')
        with self.assertRaisesRegex(ValueError, 'brak dokładnego rekordu'):
            write_exact_class_xp_copy(self.db, 1, 'Mag', value+1)

    def test_profession_missing_shadow_detected(self):
        self._write('profession')
        self.conn.execute("DELETE FROM big_number_shadow_v10400 WHERE axis='professions.xp'")
        with self.assertRaisesRegex(ValueError, 'brak dokładnego rekordu'):
            self._read('profession')

    def test_tool_missing_shadow_detected(self):
        self._write('tool')
        self.conn.execute("DELETE FROM big_number_shadow_v10400 WHERE axis='tools.xp'")
        with self.assertRaisesRegex(ValueError, 'brak dokładnego rekordu'):
            self._read('tool')

    def test_missing_whole_shadow_table_detected(self):
        self._write('class')
        self.conn.execute('DROP TABLE big_number_shadow_v10400')
        with self.assertRaisesRegex(ValueError, 'brak dokładnego rekordu'):
            self._read('class')

    def test_invalid_receipt_detected(self):
        self._write('class')
        self.conn.execute("UPDATE big_number_copy_key_receipt_v10400 SET digest='bad'")
        with self.assertRaisesRegex(ValueError, 'uszkodzone potwierdzenie'):
            self._read('class')

    def test_receipt_in_savepoint_is_rolled_back_with_xp(self):
        self.conn.execute('SAVEPOINT outer')
        self._write('class')
        self.conn.execute('ROLLBACK TO outer')
        self.conn.execute('RELEASE outer')
        self.assertEqual(self._read('class'), 5)
        self.assertIsNone(self.conn.execute("SELECT 1 FROM sqlite_master WHERE name='big_number_copy_key_receipt_v10400'").fetchone())

    def test_legacy_class_without_receipt_is_compatible(self):
        self.assertEqual(self._read('class'), 5)
        self.assertEqual(self._read('profession'), 6)
        self.assertEqual(self._read('tool'), 7)

    def test_two_class_keys_do_not_collide(self):
        self.conn.execute("INSERT INTO class_progress VALUES (1,'Wojownik',70,11)")
        a = self._write('class')
        write_exact_class_xp_copy(self.db, 1, 'Wojownik', a+1)
        self.conn.execute("DELETE FROM big_number_shadow_v10400 WHERE axis='class_progress.xp' AND source_key='Mag'")
        self.assertEqual(read_exact_class_xp_copy(self.db,1,'Wojownik'), a+1)
        with self.assertRaises(ValueError):
            self._read('class')


def run():
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(KeyedReceiptTests)
    result = unittest.TextTestRunner(verbosity=0).run(suite)
    if not result.wasSuccessful():
        raise AssertionError('BigNumber: keyed receipt test FAIL')
    return result.testsRun

if __name__ == '__main__':
    print('Keyed receipts:',run(),'PASS')
