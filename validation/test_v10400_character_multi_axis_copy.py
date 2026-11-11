# -*- coding: utf-8 -*-
"""Offline-only end-to-end regression for progression shadow axes v104.

Every test uses a disposable SQLite database plus an explicit copy marker.
No production server, no network listener, and no existing user DB.
"""
from __future__ import annotations

from pathlib import Path
import sqlite3
import tempfile
import unittest

from core.big_numbers_v10400 import SQLITE_INT64_MAX
from player.character import Character
from storage.big_number_copy_runtime_v10400 import AXES, read_exact_progression_copy
from storage.big_number_shadow_v10400 import PILOT_COLUMNS, check_shadow
from validation.test_v10400_real_character_big_number_rehearsal import CopyDB


class CharacterMultiAxisCopy(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(prefix='sb_v104_extended_copy_')
        self.folder = Path(self.tmp.name)
        (self.folder / '.SOULBOUND_V104_WYLACZNIE_KOPIA_TESTOWA').write_text(
            'TEST ONLY\n', encoding='utf-8'
        )
        self.db = CopyDB(self.folder)
        # The minimal fixture omits slot; model the actual production schema
        # for list-view SELECT ac.slot while keeping all files disposable.
        self.db.conn.execute('ALTER TABLE account_characters ADD COLUMN slot INTEGER DEFAULT 1')

    def tearDown(self):
        self.db.conn.close()
        self.tmp.cleanup()

    def enable(self):
        self.db.enable_big_number_copy_rehearsal_v104()
        return Character.from_row(self.db.character_for_account(1))

    def test_all_progression_axes_roundtrip_and_mirrors(self):
        character = self.enable()
        huge = 10 ** 200
        for index, axis in enumerate(AXES):
            setattr(character, axis, huge + index)
        # stat_progress is derived from the six stat progress fields, not from
        # the potentially stale Character.stat_progress cache.
        derived = min(getattr(character, stat + '_progress') for stat in (
            'strength', 'dexterity', 'constitution',
            'intelligence', 'willpower', 'charisma'
        ))
        self.db.save_character(character)
        before = dict(self.db.conn.execute('SELECT * FROM characters WHERE account_id=1').fetchone())
        for axis in AXES:
            self.assertEqual(before[axis], SQLITE_INT64_MAX, axis)
        self.assertEqual(check_shadow(self.db.conn), len(AXES))
        self.db.conn.close()
        self.db.conn = sqlite3.connect(self.db.path)
        self.db.conn.row_factory = sqlite3.Row
        after = Character.from_row(self.db.character_for_account(1))
        for index, axis in enumerate(AXES):
            expected = derived if axis == 'stat_progress' else huge + index
            self.assertEqual(getattr(after, axis), expected, axis)
        self.assertEqual(self.db.conn.execute(
            'SELECT gold FROM account_wallet WHERE master_account_id=1'
        ).fetchone()[0], 0)

    def test_positional_character_reads_are_exact_after_reopen(self):
        character = self.enable()
        character.character_xp = 10 ** 180 + 19
        character.soul_xp = 10 ** 181 + 7
        character.soul_tier = 10 ** 182 + 3
        self.db.save_character(character)
        self.db.conn.close()
        self.db.conn = sqlite3.connect(self.db.path)
        self.db.conn.row_factory = sqlite3.Row
        row = self.db.character_for_account(1)
        columns = row.keys()
        for key in ('character_xp', 'soul_xp', 'soul_tier'):
            offset = columns.index(key)
            self.assertEqual(row[offset], row[key], key)
            self.assertGreater(row[offset], SQLITE_INT64_MAX)
        self.assertEqual(row[-1], row[columns[-1]])
        self.assertEqual(tuple(row), tuple(row[k] for k in columns))
        self.assertEqual(row[:], tuple(row))
        idx = columns.index('character_xp')
        self.assertEqual(row[idx:idx+1], (row['character_xp'],))
        self.assertEqual(len(row), len(columns))

    def test_case_insensitive_row_read_does_not_truncate_big_number(self):
        character = self.enable()
        character.character_xp = 10 ** 220 + 321
        self.db.save_character(character)
        row = self.db.character_for_account(1)
        self.assertEqual(row['CHARACTER_XP'], character.character_xp)
        self.assertEqual(row['Character_Xp'], character.character_xp)
        self.assertEqual(row[row.keys().index('character_xp')], character.character_xp)
        with self.assertRaises((IndexError, KeyError)):
            _ = row['missing_field']

    def test_character_selection_list_has_exact_big_number_and_recovers(self):
        character = self.enable()
        character.character_level = 10 ** 170 + 7
        character.soul_xp = 10 ** 171 + 8
        self.db.save_character(character)
        self.db.conn.close()
        self.db.conn = sqlite3.connect(self.db.path)
        self.db.conn.row_factory = sqlite3.Row
        entries = self.db.characters_for_master(1)
        self.assertEqual(len(entries), 1)
        row = entries[0]
        self.assertEqual(row['CHARACTER_LEVEL'], 10 ** 170 + 7)
        self.assertEqual(row['soul_xp'], 10 ** 171 + 8)
        self.assertEqual(row[row.keys().index('character_level')], 10 ** 170 + 7)
        self.assertEqual(row['character_account_id'], 1)

    def test_removed_copy_marker_refuses_character_selection(self):
        self.enable()
        (self.folder / '.SOULBOUND_V104_WYLACZNIE_KOPIA_TESTOWA').unlink()
        with self.assertRaises(PermissionError):
            self.db.characters_for_master(1)

    def test_all_fields_rollback_after_last_shadow_failure(self):
        character = self.enable()
        original = dict(self.db.conn.execute('SELECT * FROM characters').fetchone())
        character.soul_level = 10**150
        character.soul_tier = 10**151
        character.charisma_progress = 10**152
        character.silver = 50
        # Install the schema BEFORE adding the trigger, without touching data.
        from storage.big_number_shadow_v10400 import install_shadow_schema
        install_shadow_schema(self.db.conn)
        self.db.conn.execute('''CREATE TRIGGER reject_last_axis_2
            BEFORE INSERT ON big_number_shadow_v10400
            WHEN NEW.axis='characters.charisma_progress'
            BEGIN SELECT RAISE(ABORT, 'LAST_AXIS_FAIL'); END''')
        with self.assertRaisesRegex(sqlite3.IntegrityError, 'LAST_AXIS_FAIL'):
            self.db.save_character(character)
        actual = dict(self.db.conn.execute('SELECT * FROM characters').fetchone())
        self.assertEqual(actual, original)
        self.assertEqual(self.db.conn.execute(
            'SELECT silver FROM account_wallet WHERE master_account_id=1'
        ).fetchone()[0], 20)
        self.assertEqual(self.db.conn.execute('SELECT COUNT(*) FROM big_number_shadow_v10400').fetchone()[0],0)
        self.assertEqual(character.silver, 50)

    def test_legacy_writer_conflict_on_level_refuses_overwrite(self):
        character = self.enable()
        character.character_level = 10**100
        self.db.save_character(character)
        self.db.conn.execute('UPDATE characters SET character_level=7 WHERE account_id=1')
        with self.assertRaisesRegex(ValueError, 'poza migracj'):
            self.db.character_for_account(1)
        with self.assertRaisesRegex(ValueError, 'poza migracj'):
            self.db.save_character(character)
        self.assertEqual(self.db.conn.execute(
            'SELECT character_level FROM characters WHERE account_id=1'
        ).fetchone()[0], 7)

    def test_legacy_mode_refuses_huge_level_before_wallet_write(self):
        normal = Character.from_row(self.db.character_for_account(1))
        normal.soul_level = 10**100
        normal.gold = 99
        with self.assertRaises(OverflowError):
            self.db.save_character(normal)
        self.assertEqual(self.db.conn.execute(
            'SELECT gold FROM account_wallet WHERE master_account_id=1'
        ).fetchone()[0], 0)
        self.assertEqual(self.db.conn.execute(
            'SELECT soul_level FROM characters WHERE account_id=1'
        ).fetchone()[0], 5000)

    def test_copy_marker_removed_stops_all_axes(self):
        character = self.enable()
        character.soul_tier = 10**200
        (self.folder / '.SOULBOUND_V104_WYLACZNIE_KOPIA_TESTOWA').unlink()
        with self.assertRaises(PermissionError):
            self.db.save_character(character)

    def test_pilot_legacy_shadow_mirror_scope_unchanged(self):
        self.assertEqual(PILOT_COLUMNS['characters'][1],
            ('character_xp', 'soul_xp', 'silver', 'gold', 'mithril'))
        self.assertEqual(len(AXES), 14)

if __name__ == '__main__':
    unittest.main()
