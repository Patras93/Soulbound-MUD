# -*- coding: utf-8 -*-
"""Regression: no partial SQLite COMMIT after an interrupted kill."""
import sqlite3
import tempfile
import unittest
from pathlib import Path
from storage.database import _DeferredCommitConnection

class DeferredRollbackTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="sb104_deferred_")
        self.path = str(Path(self.temp.name) / "test.sqlite")
        self.raw = sqlite3.connect(self.path)
        self.db = _DeferredCommitConnection(self.raw)
        self.db.execute("CREATE TABLE rewards(x INTEGER NOT NULL)")
        self.db.commit()

    def tearDown(self):
        self.raw.close()
        self.temp.cleanup()

    def rows(self):
        with sqlite3.connect(self.path) as check:
            return [r[0] for r in check.execute("SELECT x FROM rewards ORDER BY x")]

    def test_exception_never_publishes_a_requested_commit(self):
        with self.assertRaisesRegex(RuntimeError, "forced"):
            with self.db.deferred_commits():
                self.db.execute("INSERT INTO rewards VALUES (1)")
                self.db.commit()
                raise RuntimeError("forced")
        self.assertEqual(self.rows(), [])
        self.assertEqual(self.db._defer_depth, 0)
        self.assertFalse(self.db._commit_pending)

    def test_nested_rollback_on_outer_failure(self):
        with self.assertRaises(ValueError):
            with self.db.deferred_commits():
                self.db.execute("INSERT INTO rewards VALUES (1)")
                with self.db.deferred_commits():
                    self.db.execute("INSERT INTO rewards VALUES (2)")
                    self.db.commit()
                self.assertEqual(self.rows(), [])
                raise ValueError("abort")
        self.assertEqual(self.rows(), [])

    def test_success_flushes_only_after_outer_scope(self):
        with self.db.deferred_commits():
            with self.db.deferred_commits():
                self.db.execute("INSERT INTO rewards VALUES (3)")
                self.db.commit()
            self.db.flush_deferred_commit()
            self.assertEqual(self.rows(), [])
        self.assertEqual(self.rows(), [3])

    def test_sqlite_context_manager_does_not_bypass_deferral(self):
        with self.assertRaises(ValueError):
            with self.db.deferred_commits():
                with self.db as conn:
                    conn.execute("INSERT INTO rewards VALUES (4)")
                self.assertEqual(self.rows(), [])
                raise ValueError("abort")
        self.assertEqual(self.rows(), [])

    def test_context_manager_commits_after_success(self):
        with self.db.deferred_commits():
            with self.db as conn:
                conn.execute("INSERT INTO rewards VALUES (5)")
            self.assertEqual(self.rows(), [])
        self.assertEqual(self.rows(), [5])

    def test_preexisting_uncommitted_writes_survive_failed_scope(self):
        self.db.execute("INSERT INTO rewards VALUES (8)")
        with self.assertRaises(RuntimeError):
            with self.db.deferred_commits():
                self.db.execute("INSERT INTO rewards VALUES (9)")
                self.db.commit()
                raise RuntimeError("cancel")
        self.assertEqual([x[0] for x in self.db.execute("SELECT x FROM rewards")], [8])
        self.db.commit()
        self.assertEqual(self.rows(), [8])

    def test_caught_nested_failure_keeps_only_outer_work(self):
        with self.db.deferred_commits():
            self.db.execute("INSERT INTO rewards VALUES (10)")
            try:
                with self.db.deferred_commits():
                    self.db.execute("INSERT INTO rewards VALUES (11)")
                    self.db.commit()
                    raise ValueError("inner")
            except ValueError:  # AUDIT_INTENTIONAL_PASS: expected inner rollback in test
                pass
            self.db.execute("INSERT INTO rewards VALUES (12)")
            self.db.commit()
        self.assertEqual(self.rows(), [10, 12])

    def test_external_savepoint_survives_successful_deferred_scope(self):
        self.db.execute('SAVEPOINT outer_reward')
        self.db.execute('INSERT INTO rewards VALUES (201)')
        with self.db.deferred_commits():
            self.db.execute('INSERT INTO rewards VALUES (202)')
            self.db.commit()  # requested by an inner game method
        self.assertTrue(self.db.in_transaction)
        self.assertEqual(self.rows(), [])  # another connection cannot see writes
        self.db.execute('ROLLBACK TO SAVEPOINT outer_reward')
        self.db.execute('RELEASE SAVEPOINT outer_reward')
        self.assertEqual(self.rows(), [])
        self.assertFalse(self.db._commit_pending)

    def test_external_transaction_remains_owned_after_nested_success(self):
        self.db.execute('BEGIN IMMEDIATE')
        self.db.execute('INSERT INTO rewards VALUES (203)')
        with self.db.deferred_commits():
            with self.db.deferred_commits():
                self.db.execute('INSERT INTO rewards VALUES (204)')
                self.db.commit()
        self.assertEqual(self.rows(), [])
        self.db.rollback()
        self.assertEqual(self.rows(), [])
        # Once external transaction ends, an ordinary independent reward must commit.
        with self.db.deferred_commits():
            self.db.execute('INSERT INTO rewards VALUES (205)')
            self.db.commit()
        self.assertEqual(self.rows(), [205])

    def test_external_savepoint_success_then_caller_commit(self):
        self.db.execute('SAVEPOINT master')
        with self.db.deferred_commits():
            self.db.execute('INSERT INTO rewards VALUES (206)')
            self.db.commit()
        self.assertEqual(self.rows(), [])
        self.db.execute('RELEASE SAVEPOINT master')
        self.assertEqual(self.rows(), [206])

    def test_context_manager_inside_caller_savepoint_cannot_commit(self):
        self.db.execute('SAVEPOINT external')
        with self.db as connection:
            connection.execute('INSERT INTO rewards VALUES (207)')
        self.assertTrue(self.db.in_transaction)
        self.assertEqual(self.rows(), [])
        self.db.execute('ROLLBACK TO SAVEPOINT external')
        self.db.execute('RELEASE SAVEPOINT external')
        self.assertEqual(self.rows(), [])

    def test_failed_nested_context_only_rolls_back_own_writes(self):
        self.db.execute('SAVEPOINT external')
        self.db.execute('INSERT INTO rewards VALUES (208)')
        with self.assertRaisesRegex(RuntimeError, 'abort'):
            with self.db as connection:
                connection.execute('INSERT INTO rewards VALUES (209)')
                raise RuntimeError('abort')
        self.assertEqual([v[0] for v in self.db.execute('SELECT x FROM rewards')], [208])
        self.db.execute('RELEASE SAVEPOINT external')
        self.assertEqual(self.rows(), [208])

    def test_executescript_rolls_back_inside_deferred_transaction(self):
        # The safe proxy executes each complete SQL statement without calling
        # sqlite3.Connection.executescript (which would force a COMMIT).
        with self.assertRaisesRegex(RuntimeError, 'rollback sentinel'):
            with self.db.deferred_commits():
                self.db.execute('INSERT INTO rewards VALUES (210)')
                self.db.executescript('INSERT INTO rewards VALUES (211);')
                self.assertEqual([r[0] for r in self.db.execute("SELECT x FROM rewards ORDER BY x")], [210, 211])
                raise RuntimeError('rollback sentinel')
        self.assertEqual(self.rows(), [])

    def test_executescript_does_not_commit_external_savepoint(self):
        self.db.execute('SAVEPOINT external_sqlite_owner')
        self.db.execute('INSERT INTO rewards VALUES (212)')
        self.db.executescript('INSERT INTO rewards VALUES (213);')
        self.assertTrue(self.db.in_transaction)
        self.assertEqual([r[0] for r in self.db.execute("SELECT x FROM rewards ORDER BY x")], [212, 213])
        self.db.execute('ROLLBACK TO SAVEPOINT external_sqlite_owner')
        self.db.execute('RELEASE SAVEPOINT external_sqlite_owner')
        self.assertEqual(self.rows(), [])

    def test_executescript_does_not_commit_implicit_transaction(self):
        self.db.execute('INSERT INTO rewards VALUES (214)')
        self.assertTrue(self.db.in_transaction)
        self.db.executescript('INSERT INTO rewards VALUES (215);')
        self.assertTrue(self.db.in_transaction)
        self.assertEqual([r[0] for r in self.db.execute("SELECT x FROM rewards ORDER BY x")], [214, 215])
        self.db.rollback()
        self.assertEqual(self.rows(), [])

    def test_executescript_error_never_commits_partial_script(self):
        # Even when the first statement succeeds, the caller's SAVEPOINT
        # must roll back both ordinary SQL and the earlier script statement.
        with self.assertRaises(sqlite3.OperationalError):
            with self.db.deferred_commits():
                self.db.execute('INSERT INTO rewards VALUES (216)')
                self.db.executescript('INSERT INTO rewards VALUES (217); INVALID SQL;')
        self.assertEqual(self.rows(), [])

    def test_executescript_still_works_for_startup_schema(self):
        self.db.executescript('CREATE TABLE other (x INTEGER);')
        self.assertEqual(self.db.execute("SELECT name FROM sqlite_master WHERE name='other'").fetchone()[0], 'other')

    def test_usable_after_rollback(self):
        with self.assertRaises(RuntimeError):
            with self.db.deferred_commits():
                self.db.execute("INSERT INTO rewards VALUES (6)")
                self.db.commit()
                raise RuntimeError()
        with self.db.deferred_commits():
            self.db.execute("INSERT INTO rewards VALUES (7)")
            self.db.commit()
        self.assertEqual(self.rows(), [7])

def run():
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(DeferredRollbackTests)
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    if not result.wasSuccessful():
        raise AssertionError('SQLite deferred commit ownership regression FAIL')
    return result.testsRun


if __name__ == "__main__":
    print('DEFERRED COMMIT SQLITE:', run(), 'PASS')
