# -*- coding: utf-8 -*-
"""Exercise actual character persistence on fenced disposable databases only."""
from __future__ import annotations
from dataclasses import fields
from pathlib import Path
import sqlite3
import tempfile
import unittest
from player.character import Character
from storage.db_accounts import DatabaseAccountsMixin
from core.big_numbers_v10400 import SQLITE_INT64_MAX

class CopyDB(DatabaseAccountsMixin):
    def __init__(self, folder):
        self.path = str(Path(folder) / 'SB104_OFFLINE_TEST.sqlite')
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        types = {f.name: f.type for f in fields(Character)}
        names = list(types)
        cols = ['"'+name+'" '+('TEXT' if typ is str or typ == 'str' else 'INTEGER')
                + (' PRIMARY KEY' if name=='account_id' else '') for name,typ in types.items()]
        self.conn.execute('CREATE TABLE characters ('+','.join(cols)+')')
        values = {k: ('' if types[k] is str or types[k]=='str' else 0) for k in names}
        values.update(account_id=1, name='Test', name_nom='Test', character_level=800, soul_level=5000,
                      character_xp=100, soul_xp=200, silver=20, gold=0, mithril=0,
                      room_id='temple', guild_reputation_json='{}', guild_exams_json='{}',
                      guild_class_quests_json='{}', guild_bounty_json='{}')
        self.conn.execute('INSERT INTO characters ('+','.join('"'+k+'"' for k in names)+') VALUES ('+','.join('?' for _ in names)+')', tuple(values.values()))
        self.conn.execute('CREATE TABLE account_wallet (master_account_id INTEGER PRIMARY KEY, silver INTEGER, gold INTEGER, mithril INTEGER, updated_at TEXT)')
        self.conn.execute('CREATE TABLE account_characters (master_account_id INTEGER, character_account_id INTEGER)')
        self.conn.execute('INSERT INTO account_characters VALUES (1,1)')
        self.conn.execute('INSERT INTO account_wallet VALUES (1,20,0,0,\'start\')')
        self.conn.commit()

class RealCharacterRehearsal(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='soulbound_v104_copy_bridge_')
        self.root = Path(self.temp.name)
        (self.root / '.SOULBOUND_V104_WYLACZNIE_KOPIA_TESTOWA').write_text('TYLKO TEST\n', encoding='utf-8')
        self.db = CopyDB(self.root)
    def tearDown(self):
        self.db.conn.close()
        self.temp.cleanup()
    def test_live_methods_roundtrip_huge_both_axes(self):
        self.db.enable_big_number_copy_rehearsal_v104()
        character = Character.from_row(self.db.character_for_account(1))
        character.character_xp = 10 ** 250 + 44
        character.soul_xp = 10 ** 251 + 45
        self.db.save_character(character)
        sql = self.db.conn.execute('SELECT character_xp,soul_xp FROM characters WHERE account_id=1').fetchone()
        self.assertEqual(tuple(sql), (SQLITE_INT64_MAX, SQLITE_INT64_MAX))
        self.db.conn.close()
        self.db.conn = sqlite3.connect(self.db.path)
        self.db.conn.row_factory = sqlite3.Row
        loaded = Character.from_row(self.db.character_for_account(1))
        self.assertEqual((loaded.character_xp, loaded.soul_xp), (10 ** 250 + 44, 10 ** 251 + 45))
        self.assertEqual(loaded.name, 'Test')
    def test_regular_path_rejects_large_xp(self):
        character = Character.from_row(self.db.character_for_account(1))
        character.character_xp=10**200
        with self.assertRaises(OverflowError):
            self.db.save_character(character)
        self.assertEqual(self.db.conn.execute('SELECT character_xp FROM characters').fetchone()[0], 100)
    def test_offline_optin_refuses_without_marker(self):
        (self.root / '.SOULBOUND_V104_WYLACZNIE_KOPIA_TESTOWA').unlink()
        with self.assertRaises(PermissionError):
            self.db.enable_big_number_copy_rehearsal_v104()
    def test_marker_removed_after_enable_blocks_writes(self):
        self.db.enable_big_number_copy_rehearsal_v104()
        (self.root / '.SOULBOUND_V104_WYLACZNIE_KOPIA_TESTOWA').unlink()
        ch=Character.from_row(self.db.conn.execute('SELECT * FROM characters').fetchone())
        ch.character_xp=10**100
        with self.assertRaises(PermissionError):
            self.db.save_character(ch)
    def test_shadow_stale_mirror_blocks_write(self):
        self.db.enable_big_number_copy_rehearsal_v104()
        ch=Character.from_row(self.db.character_for_account(1))
        ch.character_xp=10**100
        self.db.save_character(ch)
        self.db.conn.execute('UPDATE characters SET character_xp=4 WHERE account_id=1')
        with self.assertRaisesRegex(ValueError, 'poza migracj'):
            self.db.save_character(ch)
        self.assertEqual(self.db.conn.execute('SELECT character_xp FROM characters').fetchone()[0],4)
    def test_failed_second_shadow_write_rolls_back_both(self):
        self.db.enable_big_number_copy_rehearsal_v104()
        ch=Character.from_row(self.db.character_for_account(1))
        ch.character_xp=10**100
        ch.soul_xp=10**101
        # Install table first, then insert a failing trigger for the second axis.
        from storage.big_number_shadow_v10400 import install_shadow_schema
        install_shadow_schema(self.db.conn)
        self.db.conn.execute('''CREATE TRIGGER bad_shadow BEFORE INSERT ON big_number_shadow_v10400
            WHEN NEW.axis='characters.soul_xp' BEGIN SELECT RAISE(ABORT,'shadow failure'); END''')
        with self.assertRaises(sqlite3.IntegrityError):
            self.db.save_character(ch)
        row=self.db.conn.execute('SELECT character_xp,soul_xp FROM characters WHERE account_id=1').fetchone()
        self.assertEqual(tuple(row), (100,200))
        self.assertEqual(self.db.conn.execute('SELECT COUNT(*) FROM big_number_shadow_v10400').fetchone()[0],0)

if __name__=='__main__': unittest.main()
