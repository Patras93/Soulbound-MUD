# -*- coding: utf-8 -*-
"""Full-schema BigNumber COPY-only gate, no production databases."""
from __future__ import annotations
import sqlite3
import tempfile
import unittest
from pathlib import Path
from validation.test_v10400_snapshot_preflight import SCHEMA
from validation.v10400_migration_rehearsal import rehearse
from validation.v10400_extended_snapshot import (CHAR_FIELDS, inspect_extended_snapshot,
    mirror_extended_copy, check_extended_coverage)
from storage.big_number_shadow_v10400 import install_shadow_schema


def full_schema(conn):
    conn.executescript(SCHEMA)
    for field in CHAR_FIELDS:
        conn.execute(f'ALTER TABLE characters ADD COLUMN "{field}" INTEGER NOT NULL DEFAULT 1')
    conn.executescript('''
        CREATE TABLE professions(account_id INTEGER, profession TEXT, xp INTEGER,
            PRIMARY KEY(account_id,profession));
        CREATE TABLE tools(account_id INTEGER, tool_type TEXT, xp INTEGER,
            PRIMARY KEY(account_id,tool_type));
        INSERT INTO professions VALUES(1,'Kowalstwo',100);
        INSERT INTO tools VALUES(1,'kilof',333);
    ''')


class ExtendedCopyGate(unittest.TestCase):
    def setUp(self):
        self.db=sqlite3.connect(':memory:')
        full_schema(self.db)
    def tearDown(self):
        self.db.close()

    def test_all_extended_axes_copied_and_idempotent(self):
        snapshot=inspect_extended_snapshot(self.db)
        self.assertTrue(snapshot['enabled'])
        self.assertEqual(snapshot['cells'],len(CHAR_FIELDS)+2)
        self.assertEqual(mirror_extended_copy(self.db,snapshot),snapshot['cells'])
        self.assertEqual(mirror_extended_copy(self.db,snapshot),0)
        self.assertEqual(check_extended_coverage(self.db,snapshot),snapshot['cells'])

    def test_missing_profession_table_blocks_not_skips(self):
        self.db.execute('DROP TABLE professions')
        with self.assertRaisesRegex(ValueError,'brak tabeli'):
            inspect_extended_snapshot(self.db)

    def test_missing_character_axis_blocks(self):
        self.db.execute('ALTER TABLE characters DROP COLUMN "soul_tier"')
        with self.assertRaisesRegex(ValueError,'soul_tier'):
            inspect_extended_snapshot(self.db)

    def test_real_database_without_any_extended_axes_blocks(self):
        self.db.execute('DROP TABLE professions')
        self.db.execute('DROP TABLE tools')
        for field in CHAR_FIELDS:
            self.db.execute(f'ALTER TABLE characters DROP COLUMN "{field}"')
        self.db.execute('CREATE TABLE accounts(id INTEGER PRIMARY KEY)')
        with self.assertRaisesRegex(ValueError,'brak tabeli lub kolumny'):
            inspect_extended_snapshot(self.db)

    def test_noninteger_work_experience_blocks(self):
        self.db.execute("UPDATE professions SET xp='bad'")
        with self.assertRaisesRegex(ValueError,'niekanoniczna'):
            inspect_extended_snapshot(self.db)

    def test_empty_profession_key_blocks(self):
        self.db.execute("INSERT INTO professions VALUES(1,'',2)")
        with self.assertRaisesRegex(ValueError,'niepoprawny klucz'):
            inspect_extended_snapshot(self.db)

    def test_missing_one_shadow_blocks(self):
        snap=inspect_extended_snapshot(self.db)
        mirror_extended_copy(self.db,snap)
        self.db.execute("DELETE FROM big_number_shadow_v10400 WHERE axis='tools.xp'")
        with self.assertRaisesRegex(ValueError,'nieprzeniesiona'):
            check_extended_coverage(self.db,snap)

    def test_legacy_change_after_mirror_blocks(self):
        snap=inspect_extended_snapshot(self.db)
        mirror_extended_copy(self.db,snap)
        self.db.execute("UPDATE tools SET xp=999 WHERE tool_type='kilof'")
        with self.assertRaisesRegex(ValueError,'INTEGER zmieniony'):
            check_extended_coverage(self.db,snap)

    def test_full_rehearsal_on_readonly_source(self):
        with tempfile.TemporaryDirectory(prefix='sb104_ext_rehearsal_') as folder:
            path=Path(folder)/'source.sqlite'
            with sqlite3.connect(path) as conn:
                full_schema(conn)
            result=rehearse(path)
            self.assertEqual(result['extended_preflight']['cells'],len(CHAR_FIELDS)+2)
            self.assertEqual(result['extended_mirrored'],len(CHAR_FIELDS)+2)
            self.assertEqual(result['production_modified'],'NIE')
            with sqlite3.connect(path) as conn:
                self.assertFalse(conn.execute("SELECT 1 FROM sqlite_master WHERE name='big_number_shadow_v10400'").fetchone())

    def test_rehearsal_partial_extended_schema_fails_closed(self):
        with tempfile.TemporaryDirectory(prefix='sb104_ext_partial_') as folder:
            path=Path(folder)/'source.sqlite'
            with sqlite3.connect(path) as conn:
                conn.executescript(SCHEMA)
                conn.execute('ALTER TABLE characters ADD COLUMN soul_tier INTEGER DEFAULT 1')
            with self.assertRaisesRegex(ValueError,'brak tabeli lub kolumny'):
                rehearse(path)

    def test_failed_full_shadow_rolls_back(self):
        with tempfile.TemporaryDirectory(prefix='sb104_ext_abort_') as folder:
            path=Path(folder)/'source.sqlite'
            with sqlite3.connect(path) as conn:
                full_schema(conn)
                install_shadow_schema(conn)
                conn.execute('''CREATE TRIGGER block_work BEFORE INSERT ON big_number_shadow_v10400
                    WHEN NEW.axis='tools.xp' BEGIN SELECT RAISE(ABORT,'work insert denied'); END''')
            with self.assertRaisesRegex(sqlite3.IntegrityError,'work insert denied'):
                rehearse(path)
            with sqlite3.connect(path) as conn:
                self.assertEqual(conn.execute('SELECT COUNT(*) FROM big_number_shadow_v10400').fetchone()[0],0)

if __name__=='__main__': unittest.main()
