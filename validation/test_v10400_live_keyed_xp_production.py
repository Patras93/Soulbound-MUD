# -*- coding: utf-8 -*-
"""Production BigNumber: no rehearsal marker, real Database and SQLite."""
import sqlite3
import tempfile
import unittest
from pathlib import Path

from core.big_numbers_v10400 import SQLITE_INT64_MAX
from storage.database import Database
from storage.big_number_live_keyed_xp_v10400 import (
    read_live_keyed_xp, write_live_keyed_xp,
)


class ProductionKeyedXPTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='sb104_prod_keyed_xp_')
        self.path = Path(self.tmp.name) / 'sandbox.sqlite'
        self.db = Database(str(self.path))
        self.uid = self.db.create_account('Tester', 'safe-test-password')
        self.db.ensure_class_progress(self.uid, 'Rycerz')
        self.db.ensure_profession(self.uid, 'Zielarstwo')
        self.db.ensure_tool(self.uid, 'kilof')

    def tearDown(self):
        self.db.conn.close()
        self.tmp.cleanup()

    def test_all_three_routes_exact_on_production_db_after_reopen(self):
        x = 10 ** 150 + 27
        self.db.save_profession(self.uid, 'Zielarstwo', 650, x, 42)
        self.db.save_tool(self.uid, 'kilof', 660, x+1, 43)
        write_live_keyed_xp(self.db, self.uid, 'class', 'Rycerz', xp=x+2, level=700)
        self.db.conn.commit()
        self.db.conn.close()
        self.db = Database(str(self.path))
        self.assertFalse(getattr(self.db, '_v104_big_number_copy_rehearsal', False))
        self.assertEqual(self.db.profession(self.uid, 'Zielarstwo')['xp'], x)
        self.assertEqual(self.db.tool(self.uid, 'kilof')['xp'], x+1)
        self.assertEqual(self.db.class_progress_row(self.uid, 'Rycerz')['xp'], x+2)
        self.assertEqual(self.db.profession(self.uid, 'Zielarstwo')[3], x)  # positional row access
        self.assertEqual(self.db.conn.execute('SELECT xp FROM professions').fetchone()[0], SQLITE_INT64_MAX)
        self.assertEqual(self.db.conn.execute('SELECT xp FROM tools').fetchone()[0], SQLITE_INT64_MAX)
        # Lazy ensure / INSERT OR IGNORE must not reject a previously migrated row.
        self.db.ensure_profession(self.uid, 'Zielarstwo')
        self.db.ensure_tool(self.uid, 'kilof')
        self.db.ensure_class_progress(self.uid, 'Rycerz')

    def test_direct_legacy_write_refused_after_exact_write(self):
        self.db.save_profession(self.uid, 'Zielarstwo', 5, 10**100, 4)
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.conn.execute('UPDATE professions SET xp=1 WHERE account_id=?', (self.uid,))
        self.assertEqual(self.db.profession(self.uid, 'Zielarstwo')['xp'], 10**100)

    def test_removed_shadow_detected_by_receipt(self):
        self.db.save_tool(self.uid, 'kilof', 7, 10**140, 10)
        self.db.conn.execute('DELETE FROM big_number_live_keyed_xp_v10400 WHERE kind=?', ('tool',))
        with self.assertRaisesRegex(ValueError, 'zniknal dokladny'):
            self.db.tool(self.uid, 'kilof')
        with self.assertRaises(ValueError):
            self.db.save_tool(self.uid, 'kilof', 8, 100, 11)

    def test_shadow_checksum_mismatch_blocks_read_and_write(self):
        self.db.save_profession(self.uid, 'Zielarstwo', 6, 10**180, 8)
        self.db.conn.execute('UPDATE big_number_live_keyed_xp_v10400 SET value_text=?', ('123456',))
        with self.assertRaisesRegex(ValueError, 'suma kontrolna'):
            self.db.profession(self.uid, 'Zielarstwo')
        with self.assertRaises(ValueError):
            self.db.save_profession(self.uid, 'Zielarstwo', 7, 200, 9)

    def test_outer_savepoint_rolls_back_exact_and_mirror(self):
        self.db.save_tool(self.uid, 'kilof', 7, 10**110, 10)
        self.db.conn.execute('SAVEPOINT parent_gameplay')
        self.db.save_tool(self.uid, 'kilof', 8, 10**120, 11)
        self.assertEqual(self.db.tool(self.uid, 'kilof')['xp'], 10**120)
        self.db.conn.execute('ROLLBACK TO SAVEPOINT parent_gameplay')
        self.db.conn.execute('RELEASE SAVEPOINT parent_gameplay')
        self.assertEqual(self.db.tool(self.uid, 'kilof')['xp'], 10**110)

    def test_forced_failure_cannot_change_old_row_or_shadow(self):
        before = tuple(self.db.conn.execute('SELECT level,xp,actions FROM professions').fetchone())
        self.db.conn.execute('''CREATE TRIGGER reject_live_shadow BEFORE INSERT
           ON big_number_live_keyed_xp_v10400
           BEGIN SELECT RAISE(ABORT, 'forced failure'); END''')
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.save_profession(self.uid, 'Zielarstwo', 11, 10**200, 8)
        self.assertEqual(tuple(self.db.conn.execute('SELECT level,xp,actions FROM professions').fetchone()), before)
        self.assertEqual(self.db.profession(self.uid, 'Zielarstwo')['xp'], 0)

    def test_legacy_unmigrated_read_is_unchanged(self):
        self.assertEqual(self.db.profession(self.uid, 'Zielarstwo')['xp'], 0)
        self.db.conn.execute('UPDATE professions SET xp=56 WHERE account_id=?', (self.uid,))
        self.assertEqual(self.db.profession(self.uid, 'Zielarstwo')['xp'], 56)
        # Ordinary small EXP keeps old INTEGER storage with no extra writes.
        self.db.save_profession(self.uid, 'Zielarstwo', 12, 57, 8)
        self.assertEqual(self.db.profession(self.uid, 'Zielarstwo')['xp'], 57)
        self.assertEqual(self.db.conn.execute(
            'SELECT COUNT(*) FROM big_number_live_keyed_xp_v10400').fetchone()[0], 0)
        self.db.conn.execute('UPDATE professions SET xp=58 WHERE account_id=?', (self.uid,))
        self.assertEqual(self.db.profession(self.uid, 'Zielarstwo')['xp'], 58)

    def test_invalid_xp_or_level_never_partial(self):
        baseline = self.db.tool(self.uid, 'kilof')['xp']
        for xp, level in ((-1, 1), (1.25, 1), ('10oops', 1), (10**100, 10**100)):
            with self.subTest(xp=str(xp)[:12]):
                with self.assertRaises((ValueError, TypeError, OverflowError)):
                    self.db.save_tool(self.uid, 'kilof', level, xp, 9)
                self.assertEqual(self.db.tool(self.uid, 'kilof')['xp'], baseline)

    def test_class_active_row_is_exact(self):
        x=10**170+1
        write_live_keyed_xp(self.db, self.uid, 'class', 'Rycerz', xp=x, level=800)
        self.db.ensure_primary_class(self.uid, 'Rycerz')
        self.assertEqual(self.db.active_class_rows(self.uid, 'Rycerz')[0]['xp'],x)
        self.assertEqual(self.db.active_class_rows(self.uid, 'Rycerz')[0][2],x)

    def test_tampered_legacy_mirror_is_detected_after_reopen(self):
        self.db.save_tool(self.uid, 'kilof', 5, 10**111, 3)
        # A database editor could remove triggers, so the reader must also
        # verify the old mirror against signed authoritative TEXT.
        self.db.conn.execute('DROP TRIGGER sb104_exact_tool_update')
        self.db.conn.execute('UPDATE tools SET xp=15 WHERE account_id=?', (self.uid,))
        self.db.conn.commit()
        self.db.conn.close()
        self.db=Database(str(self.path))
        with self.assertRaisesRegex(ValueError, 'przestarzaly'):
            self.db.tool(self.uid, 'kilof')


def run():
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(ProductionKeyedXPTests)
    result=unittest.TextTestRunner(verbosity=0).run(suite)
    if not result.wasSuccessful():
        raise AssertionError('Produkcyjny BigNumber ProductionKeyedXPTests: blad testow.')
    return result.testsRun


if __name__ == '__main__':
    unittest.main()
