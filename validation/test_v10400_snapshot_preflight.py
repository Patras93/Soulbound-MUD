# -*- coding: utf-8 -*-
"""Rehearsal safety: never claim PASS after skipping a pilot table/cell."""
from __future__ import annotations

from pathlib import Path
import sqlite3
import tempfile
import unittest
from validation.v10400_snapshot_preflight import (
    inspect_pilot_snapshot, require_exact_pilot_coverage,
)
from storage.big_number_shadow_v10400 import mirror_legacy_copy, install_shadow_schema
from validation.v10400_migration_rehearsal import rehearse


SCHEMA = '''
CREATE TABLE characters(account_id INTEGER PRIMARY KEY, character_xp INTEGER,
  soul_xp INTEGER, silver INTEGER, gold INTEGER, mithril INTEGER);
CREATE TABLE account_wallet(master_account_id INTEGER PRIMARY KEY,
  silver INTEGER, gold INTEGER, mithril INTEGER);
CREATE TABLE bank_balances(account_id INTEGER PRIMARY KEY,
  silver INTEGER, gold INTEGER, mithril INTEGER);
CREATE TABLE class_progress(account_id INTEGER, class_name TEXT, xp INTEGER,
  PRIMARY KEY(account_id, class_name));
INSERT INTO characters VALUES(1,100,200,300,4,5);
INSERT INTO account_wallet VALUES(1,300,4,5);
INSERT INTO bank_balances VALUES(1,1,2,3);
INSERT INTO class_progress VALUES(1,'Mag',7);
'''


class SnapshotPreflight(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        self.db.executescript(SCHEMA)

    def tearDown(self):
        self.db.close()

    def test_exact_mirror_coverage(self):
        snapshot = inspect_pilot_snapshot(self.db)
        self.assertEqual(snapshot['total_cells'], 12)
        self.assertEqual(snapshot['total_rows'], 4)
        mirror_legacy_copy(self.db)
        require_exact_pilot_coverage(self.db, snapshot)

    def test_deleting_one_valid_shadow_is_detected(self):
        snapshot = inspect_pilot_snapshot(self.db)
        mirror_legacy_copy(self.db)
        self.db.execute("DELETE FROM big_number_shadow_v10400 WHERE axis='characters.soul_xp'")
        with self.assertRaisesRegex(ValueError, 'nieprzeniesione'):
            require_exact_pilot_coverage(self.db, snapshot)

    def test_missing_table_is_not_silently_skipped(self):
        self.db.execute('DROP TABLE bank_balances')
        with self.assertRaisesRegex(ValueError, 'brak tabeli'):
            inspect_pilot_snapshot(self.db)

    def test_missing_numeric_column_is_not_silently_skipped(self):
        self.db.execute('ALTER TABLE account_wallet DROP COLUMN mithril')
        with self.assertRaisesRegex(ValueError, 'mithril'):
            inspect_pilot_snapshot(self.db)

    def test_text_affinity_or_negative_data_blocks(self):
        self.db.execute('DROP TABLE bank_balances')
        self.db.execute('CREATE TABLE bank_balances(account_id INTEGER PRIMARY KEY, silver TEXT, gold INTEGER, mithril INTEGER)')
        with self.assertRaisesRegex(ValueError, 'typ INTEGER'):
            inspect_pilot_snapshot(self.db)
        self.db.execute('DROP TABLE bank_balances')
        self.db.execute('CREATE TABLE bank_balances(account_id INTEGER PRIMARY KEY, silver INTEGER, gold INTEGER, mithril INTEGER)')
        self.db.execute('INSERT INTO bank_balances VALUES(1,1,2,3)')
        self.db.execute('UPDATE characters SET character_xp=-8')
        with self.assertRaisesRegex(ValueError, 'niekanoniczna'):
            inspect_pilot_snapshot(self.db)

    def test_null_value_blocks_instead_of_shortening_shadow(self):
        self.db.execute('UPDATE characters SET soul_xp=NULL')
        with self.assertRaisesRegex(ValueError, 'niekanoniczna'):
            inspect_pilot_snapshot(self.db)

    def test_bad_class_key_blocks(self):
        self.db.execute("INSERT INTO class_progress VALUES(1,'',123)")
        with self.assertRaisesRegex(ValueError, 'klucz klasy'):
            inspect_pilot_snapshot(self.db)

    def test_rehearsal_uses_wal_snapshot_and_never_writes_source(self):
        with tempfile.TemporaryDirectory(prefix='sb104_wal_guard_') as folder:
            path = Path(folder) / 'source.sqlite'
            src = sqlite3.connect(path)
            try:
                src.execute('PRAGMA journal_mode=WAL')
                src.executescript(SCHEMA)
                src.execute('UPDATE characters SET character_xp=4321 WHERE account_id=1')
                src.commit()
                result = rehearse(path)
                self.assertEqual(result['preflight']['total_cells'],12)
                self.assertEqual(result['shadow_checks'],12)
                self.assertEqual(result['production_modified'],'NIE')
                self.assertEqual(src.execute('SELECT character_xp FROM characters').fetchone()[0],4321)
                self.assertFalse(src.execute("SELECT 1 FROM sqlite_master WHERE name='big_number_shadow_v10400'").fetchone())
            finally:
                src.close()

    def test_failed_rehearsal_does_not_commit_source(self):
        # A trigger copied from source simulates a failure during shadow INSERT.
        with tempfile.TemporaryDirectory(prefix='sb104_abort_guard_') as folder:
            path = Path(folder) / 'source.sqlite'
            with sqlite3.connect(path) as src:
                src.executescript(SCHEMA)
                install_shadow_schema(src)
                src.execute("""CREATE TRIGGER force_copy_fail BEFORE INSERT ON big_number_shadow_v10400
                    BEGIN SELECT RAISE(ABORT,'test forced error'); END""")
            with self.assertRaisesRegex(sqlite3.IntegrityError, 'test forced error'):
                rehearse(path)
            with sqlite3.connect(path) as src:
                self.assertEqual(src.execute('SELECT character_xp FROM characters').fetchone()[0],100)
                self.assertEqual(src.execute('SELECT COUNT(*) FROM big_number_shadow_v10400').fetchone()[0],0)

    def test_rehearsal_rejects_incomplete_schema_on_copy(self):
        with tempfile.TemporaryDirectory(prefix='sb104_missing_guard_') as folder:
            path = Path(folder) / 'source.sqlite'
            with sqlite3.connect(path) as src:
                src.executescript(SCHEMA)
                src.execute('DROP TABLE account_wallet')
            with self.assertRaisesRegex(ValueError,'brak tabeli'):
                rehearse(path)
            with sqlite3.connect(path) as src:
                self.assertFalse(src.execute("SELECT 1 FROM sqlite_master WHERE name='big_number_shadow_v10400'").fetchone())


if __name__ == '__main__':
    unittest.main()
