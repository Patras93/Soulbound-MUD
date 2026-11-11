# -*- coding: utf-8 -*-
"""Tests for the read-only v104->v105 SQLite snapshot migration audit."""
import sqlite3
import tempfile
import unittest
from pathlib import Path
from validation.v10500_safe_db_migration_audit import fingerprint, rehearse


class MigrationAuditContractTests(unittest.TestCase):
    def test_fingerprint_covers_old_quest_history_and_equipment_rows(self):
        with sqlite3.connect(':memory:') as conn:
            conn.executescript('''
                CREATE TABLE characters(account_id INTEGER PRIMARY KEY,soul_level INTEGER,soul_tier INTEGER);
                CREATE TABLE quests(account_id INTEGER,quest_id TEXT,status TEXT,progress INTEGER);
                CREATE TABLE equipment(account_id INTEGER,slot TEXT,item_id TEXT);
            ''')
            conn.execute('INSERT INTO characters VALUES(1,195,19)')
            conn.execute("INSERT INTO quests VALUES(1,'soul_tier_10_trial','completed',2)")
            conn.execute("INSERT INTO equipment VALUES(1,'ring1','iron_ring')")
            baseline=fingerprint(conn)
            self.assertEqual(baseline['quests'][0],1)
            self.assertEqual(baseline['equipment'][0],1)
            conn.execute('UPDATE quests SET progress=3')
            self.assertNotEqual(fingerprint(conn)['quests'],baseline['quests'])
            conn.execute('UPDATE equipment SET item_id=?',('new_ring',))
            self.assertNotEqual(fingerprint(conn)['equipment'],baseline['equipment'])

    def test_audit_refuses_non_sqlite_and_missing_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            filename=Path(tmp)/'not_database.txt'
            filename.write_text('not a database',encoding='utf8')
            with self.assertRaises(ValueError):
                rehearse(filename)
            with self.assertRaises(FileNotFoundError):
                rehearse(Path(tmp)/'missing.db')


if __name__=='__main__': unittest.main()
