# -*- coding: utf-8 -*-
"""v104: a real SQLite snapshot-copy rehearsal and integrity proof. No production IO."""
from __future__ import annotations
from pathlib import Path
import sqlite3
import tempfile
import unittest
from validation.v10400_migration_rehearsal import rehearse
from storage.big_number_shadow_v10400 import check_shadow
from storage.big_number_events_v10400 import apply_event_copy


class Rehearsal(unittest.TestCase):
    def test_snapshot_copy_preserves_source_and_legacy(self):
        with tempfile.TemporaryDirectory() as d:
            path=Path(d)/'source.sqlite'
            with sqlite3.connect(path) as db:
                db.executescript('''
                    CREATE TABLE accounts(id INTEGER PRIMARY KEY);
                    INSERT INTO accounts VALUES (1),(2);
                    CREATE TABLE characters(account_id INTEGER PRIMARY KEY, character_xp INTEGER,
                        soul_xp INTEGER,silver INTEGER,gold INTEGER,mithril INTEGER);
                    INSERT INTO characters VALUES (1,4567,12,8000,3,1),(2,8899,33,100,1,0);
                    CREATE TABLE class_progress(account_id INTEGER,class_name TEXT,xp INTEGER,
                        PRIMARY KEY(account_id,class_name));
                    INSERT INTO class_progress VALUES (1,'Mag',11),(1,'Wojownik',15);
                    CREATE TABLE account_wallet(master_account_id INTEGER PRIMARY KEY,
                        silver INTEGER,gold INTEGER,mithril INTEGER);
                    INSERT INTO account_wallet VALUES (1,8100,3,1);
                    CREATE TABLE bank_balances(account_id INTEGER PRIMARY KEY,
                        silver INTEGER,gold INTEGER,mithril INTEGER);
                    INSERT INTO bank_balances VALUES (1,30,0,0);
                ''')
                # Since v104 full-schema preflight, an accounts table marks
                # this as a real Soulbound-style snapshot. A pilot-only
                # fixture would correctly be rejected as incomplete.
                from validation.v10400_extended_snapshot import CHAR_FIELDS
                for name in CHAR_FIELDS:
                    db.execute(f'ALTER TABLE characters ADD COLUMN "{name}" INTEGER NOT NULL DEFAULT 0')
                db.executescript('''
                    CREATE TABLE professions(account_id INTEGER, profession TEXT, xp INTEGER,
                        PRIMARY KEY(account_id, profession));
                    INSERT INTO professions VALUES(1,'Kowalstwo',19);
                    CREATE TABLE tools(account_id INTEGER, tool_type TEXT, xp INTEGER,
                        PRIMARY KEY(account_id, tool_type));
                    INSERT INTO tools VALUES(1,'mlot',23);
                ''')
            before=path.read_bytes()
            result=rehearse(path)
            self.assertEqual(result['legacy_unchanged'],'PASS')
            self.assertEqual(result['sqlite_copy_integrity'],'PASS')
            self.assertEqual(result['idempotent'],'PASS')
            self.assertGreaterEqual(result['shadow_checks'],13)
            self.assertEqual(path.read_bytes(),before,'Source was modified')


def run():
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(Rehearsal)
    res=unittest.TextTestRunner(verbosity=0).run(suite)
    if not res.wasSuccessful():raise AssertionError('Copy recovery rehearsal FAIL')
    return res.testsRun
if __name__=='__main__':print('RECOVERY:',run(),'PASS')
