# -*- coding: utf-8 -*-
"""Tests of exact class XP on independent, marked SQLite copies only."""
from __future__ import annotations
import sqlite3
import tempfile
from pathlib import Path
import unittest
from unittest.mock import patch
from storage.db_progression import DatabaseProgressionMixin
from storage.big_number_copy_runtime_v10400 import (
    read_exact_class_xp_copy, write_exact_class_xp_copy, _require_copy_path,
)
from storage.big_number_shadow_v10400 import check_shadow
from validation.test_v10400_real_character_big_number_rehearsal import CopyDB
from core.big_numbers_v10400 import SQLITE_INT64_MAX


class CopyClassDB(DatabaseProgressionMixin, CopyDB):
    def __init__(self, folder):
        super().__init__(folder)
        self.conn.execute('''CREATE TABLE class_progress (
            account_id INTEGER NOT NULL, class_name TEXT NOT NULL,
            level INTEGER NOT NULL, xp INTEGER NOT NULL,
            active_slot INTEGER, PRIMARY KEY(account_id,class_name))''')
        self.conn.executemany('INSERT INTO class_progress VALUES (?,?,?,?,?)', [
            (1, 'Mag', 900, 11, 1), (1, 'Wojownik', 910, 17, None)
        ])
        self.conn.commit()


class ClassProgressBigNumberCopy(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='sb104_class_copy_')
        self.folder = Path(self.tmp.name)
        self.marker = self.folder / '.SOULBOUND_V104_WYLACZNIE_KOPIA_TESTOWA'
        self.marker.write_text('TEST ONLY\n', encoding='utf-8')
        self.db = CopyClassDB(self.folder)
        self.db.enable_big_number_copy_rehearsal_v104()

    def tearDown(self):
        self.db.conn.close()
        self.tmp.cleanup()

    def test_all_22_authored_classes_have_separate_exact_xp(self):
        from core.classes_skills import CLASSES
        self.assertEqual(len(CLASSES), 22)
        expected = {}
        for index, (name, *_rest) in enumerate(CLASSES):
            self.db.ensure_class_progress(1, name)
            value = 10**170 + index
            write_exact_class_xp_copy(self.db, 1, name, value)
            expected[name] = value
        self.db.conn.commit()
        self.db.conn.close()
        self.db.conn = sqlite3.connect(self.db.path)
        self.db.conn.row_factory = sqlite3.Row
        for name, value in expected.items():
            self.assertEqual(self.db.class_progress_row(1, name)['xp'], value, name)
        self.assertEqual(check_shadow(self.db.conn), 22)

    def test_two_classes_independent_and_reopen(self):
        huge = 10**300
        write_exact_class_xp_copy(self.db,1,'Mag', huge)
        write_exact_class_xp_copy(self.db,1,'Wojownik', huge + 23)
        self.db.conn.commit()
        self.assertEqual(self.db.class_progress_row(1,'Mag')['xp'], huge)
        self.assertEqual(self.db.class_progress_row(1,'Wojownik')['xp'], huge+23)
        self.assertEqual(self.db.conn.execute('SELECT xp FROM class_progress WHERE class_name=?',('Mag',)).fetchone()[0],SQLITE_INT64_MAX)
        self.db.conn.close()
        self.db.conn = sqlite3.connect(self.db.path)
        self.db.conn.row_factory=sqlite3.Row
        self.assertEqual(self.db.class_progress_row(1,'Mag')['xp'], huge)
        self.assertEqual(self.db.class_progress_row(1,'Wojownik')['xp'], huge + 23)
        self.assertEqual(check_shadow(self.db.conn), 2)

    def test_active_class_row_exposes_exact_xp(self):
        huge=10**200
        write_exact_class_xp_copy(self.db,1,'Mag',huge)
        rows = self.db.active_class_rows(1,'Mag')
        self.assertEqual(rows[0]['xp'],huge)
        self.assertEqual(rows[0][2],huge)
        self.assertEqual(tuple(rows[0]), ('Mag',900,huge,1))

    def test_external_legacy_update_refuses_read_and_write(self):
        write_exact_class_xp_copy(self.db,1,'Wojownik',10**120)
        self.db.conn.execute('UPDATE class_progress SET xp=3 WHERE class_name=?',('Wojownik',))
        with self.assertRaisesRegex(ValueError,'poza migracj'):
            self.db.class_progress_row(1,'Wojownik')
        with self.assertRaisesRegex(ValueError,'poza migracj'):
            write_exact_class_xp_copy(self.db,1,'Wojownik',10**121)
        self.assertEqual(self.db.conn.execute('SELECT xp FROM class_progress WHERE class_name=?',('Wojownik',)).fetchone()[0],3)

    def test_trigger_failure_rolls_back_legacy_mirror(self):
        old=self.db.conn.execute('SELECT xp FROM class_progress WHERE class_name=?',('Mag',)).fetchone()[0]
        self._schema()
        self.db.conn.execute('''CREATE TRIGGER reject_exact_class BEFORE INSERT ON big_number_shadow_v10400
            BEGIN SELECT RAISE(ABORT, 'failure'); END''')
        with self.assertRaisesRegex(sqlite3.IntegrityError,'failure'):
            write_exact_class_xp_copy(self.db,1,'Mag',10**180)
        self.assertEqual(self.db.conn.execute('SELECT xp FROM class_progress WHERE class_name=?',('Mag',)).fetchone()[0],old)
        self.assertEqual(self.db.conn.execute('SELECT COUNT(*) FROM big_number_shadow_v10400').fetchone()[0],0)

    def _schema(self):
        from storage.big_number_shadow_v10400 import install_shadow_schema
        install_shadow_schema(self.db.conn)
        return True

    def test_external_transaction_can_rollback_both_classes(self):
        self.db.conn.execute('SAVEPOINT both_classes')
        try:
            write_exact_class_xp_copy(self.db,1,'Mag',10**130)
            write_exact_class_xp_copy(self.db,1,'Wojownik',10**131)
            self.db.conn.execute('ROLLBACK TO SAVEPOINT both_classes')
        finally:
            self.db.conn.execute('RELEASE SAVEPOINT both_classes')
        self.assertEqual(self.db.class_progress_row(1,'Mag')['xp'],11)
        self.assertEqual(self.db.class_progress_row(1,'Wojownik')['xp'],17)

    def test_marker_missing_denies_read_and_write_before_mutation(self):
        self.marker.unlink()
        with self.assertRaises(PermissionError):
            self.db.class_progress_row(1,'NowaKlasa')
        with self.assertRaises(PermissionError):
            write_exact_class_xp_copy(self.db,1,'Mag',10**150)
        self.assertEqual(self.db.conn.execute('SELECT COUNT(*) FROM class_progress').fetchone()[0],2)

    def test_path_does_not_match_connection_denies(self):
        fake = self.folder/'different.sqlite'
        fake.touch()
        self.db.path = str(fake)
        with self.assertRaisesRegex(PermissionError,'aktyw'): _require_copy_path(self.db)

    def test_noncanonical_input_refused(self):
        for bad in ('1.0',-1, 1.1, True):
            with self.assertRaises((ValueError,TypeError)):
                write_exact_class_xp_copy(self.db,1,'Mag',bad)
        self.assertEqual(self.db.class_progress_row(1,'Mag')['xp'],11)

    def test_actual_add_class_route_keeps_huge_xp_at_cap(self):
        huge = 10**220
        write_exact_class_xp_copy(self.db, 1, 'Mag', huge)
        with patch('storage.db_progression.CLASS_MASTERY_MAX_LEVEL', 900):
            result = self.db.add_class_mastery_xp(1, 'Mag', 7)
        self.assertEqual(result['xp'], huge)
        self.assertEqual(result['overflow_xp'], 7)
        self.assertEqual(self.db.class_progress_row(1, 'Mag')['xp'], huge)

    def test_bad_checksum_refuses_read(self):
        write_exact_class_xp_copy(self.db, 1, 'Mag', 10**100)
        self.db.conn.execute("UPDATE big_number_shadow_v10400 SET sha256='invalid' "
                             "WHERE axis='class_progress.xp' AND source_key='Mag'")
        with self.assertRaisesRegex(ValueError, 'checksum'):
            self.db.class_progress_row(1, 'Mag')

    def test_normal_legacy_add_path_keeps_original_behavior(self):
        self.db._v104_big_number_copy_rehearsal=False
        self.assertEqual(self.db.class_progress_row(1,'Mag')['xp'],11)
        with patch('storage.db_progression.CLASS_MASTERY_MAX_LEVEL',900):
            result = self.db.add_class_mastery_xp(1,'Mag', 9)
        self.assertEqual(result['overflow_xp'],9)
        self.assertEqual(self.db.class_progress_row(1,'Mag')['xp'],11)


def run():
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(ClassProgressBigNumberCopy)
    result = unittest.TextTestRunner(verbosity=0).run(suite)
    if not result.wasSuccessful():
        raise AssertionError('Testy BigNumber dla klas nie przeszly.')
    return result.testsRun

if __name__=='__main__':
    unittest.main()
