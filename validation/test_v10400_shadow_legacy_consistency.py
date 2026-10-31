# -*- coding: utf-8 -*-
"""Fail-closed migration integrity against legacy INTEGER drift (copy only)."""
import sqlite3
import unittest
from storage.big_number_shadow_v10400 import (
    install_shadow_schema, stage_shadow, mirror_legacy_copy,
    check_shadow, check_shadow_legacy_mirrors,
)


class ShadowLegacyConsistencyTest(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        self.db.executescript('''
            CREATE TABLE characters(account_id INTEGER PRIMARY KEY,
                character_xp INTEGER, soul_xp INTEGER, silver INTEGER,
                gold INTEGER, mithril INTEGER);
            INSERT INTO characters VALUES(1,123,456,7,8,9);
            CREATE TABLE class_progress(account_id INTEGER,
                class_name TEXT, xp INTEGER, PRIMARY KEY(account_id,class_name));
            INSERT INTO class_progress VALUES(1,'Mag',100);
            CREATE TABLE professions(account_id INTEGER, profession TEXT,
                xp INTEGER, PRIMARY KEY(account_id,profession));
            INSERT INTO professions VALUES(1,'Kowalstwo',10);
            CREATE TABLE tools(account_id INTEGER,tool_type TEXT,xp INTEGER,
                PRIMARY KEY(account_id,tool_type));
            INSERT INTO tools VALUES(1,'Mlot',20);
        ''')
        install_shadow_schema(self.db)

    def tearDown(self):
        self.db.close()

    def test_fresh_mirror_and_repeat(self):
        counts = mirror_legacy_copy(self.db)
        self.assertGreater(sum(counts.values()), 0)
        self.assertEqual(check_shadow(self.db), check_shadow_legacy_mirrors(self.db))
        self.assertEqual(sum(mirror_legacy_copy(self.db).values()), 0)

    def test_checksum_cannot_hide_legacy_mutation(self):
        mirror_legacy_copy(self.db)
        self.db.execute('UPDATE characters SET character_xp=888 WHERE account_id=1')
        self.assertGreater(check_shadow(self.db), 0)  # SHA still valid!
        with self.assertRaisesRegex(ValueError, 'zmieniony poza migracja'):
            check_shadow_legacy_mirrors(self.db)
        with self.assertRaises(ValueError):
            mirror_legacy_copy(self.db)
        self.assertEqual(self.db.execute('SELECT character_xp FROM characters').fetchone()[0], 888)

    def test_class_key_and_work_key_are_checked(self):
        stage_shadow(self.db,1,'class_progress.xp', 10**90,source_key='Mag',base_value=100)
        stage_shadow(self.db,1,'professions.xp',10**80,source_key='Kowalstwo',base_value=10)
        stage_shadow(self.db,1,'tools.xp',10**70,source_key='Mlot',base_value=20)
        self.assertEqual(check_shadow_legacy_mirrors(self.db),3)
        self.db.execute("UPDATE professions SET xp=15 WHERE profession='Kowalstwo'")
        with self.assertRaises(ValueError):
            check_shadow_legacy_mirrors(self.db)

    def test_orphan_is_not_accepted_despite_valid_sha(self):
        stage_shadow(self.db,999,'characters.character_xp',10**70,base_value=0)
        self.assertEqual(check_shadow(self.db),1)
        with self.assertRaisesRegex(ValueError,'osierocony'):
            check_shadow_legacy_mirrors(self.db)

    def test_orphan_class_key(self):
        stage_shadow(self.db,1,'class_progress.xp',10**60,source_key='Nieistniejaca',base_value=0)
        with self.assertRaisesRegex(ValueError,'osierocony'):
            check_shadow_legacy_mirrors(self.db)

    def test_reject_noninteger_mirror(self):
        stage_shadow(self.db,1,'characters.character_xp', 10**60,base_value=123)
        self.db.execute("UPDATE characters SET character_xp='123.4' WHERE account_id=1")
        with self.assertRaisesRegex(ValueError,'uszkodzone INTEGER'):
            check_shadow_legacy_mirrors(self.db)

    def test_checksum_corruption_still_rejected(self):
        stage_shadow(self.db,1,'characters.character_xp',10**60,base_value=123)
        self.db.execute("UPDATE big_number_shadow_v10400 SET balance_text='111'")
        with self.assertRaisesRegex(ValueError,'checksum|suma'):
            check_shadow_legacy_mirrors(self.db)


if __name__ == '__main__':
    unittest.main()
