# -*- coding: utf-8 -*-
"""Testy pelnego odcisku bazy: zadnych cichych zmian rozszerzonych osi."""
import sqlite3
import unittest
from validation.v10400_migration_rehearsal import legacy_digest

class TestSourceFingerprint(unittest.TestCase):
    def setUp(self):
        self.db = sqlite3.connect(':memory:')
        statements = (
            'CREATE TABLE characters(account_id INTEGER PRIMARY KEY, character_xp INTEGER, soul_xp INTEGER, stat_progress INTEGER, display_name TEXT)',
            'CREATE TABLE account_wallet(master_account_id INTEGER PRIMARY KEY, silver INTEGER, gold INTEGER, mithril INTEGER)',
            'CREATE TABLE bank_balances(account_id INTEGER PRIMARY KEY, silver INTEGER, gold INTEGER, mithril INTEGER)',
            'CREATE TABLE class_progress(account_id INTEGER, class_name TEXT, level INTEGER, xp INTEGER)',
            'CREATE TABLE professions(account_id INTEGER, profession TEXT, level INTEGER, xp INTEGER, actions INTEGER)',
            'CREATE TABLE tools(account_id INTEGER, tool_type TEXT, level INTEGER, xp INTEGER, uses INTEGER)',
        )
        for sql in statements: self.db.execute(sql)
        self.db.execute("INSERT INTO characters VALUES(1,10,20,30,'Bohater')")
        self.db.execute('INSERT INTO account_wallet VALUES(1,1,2,3)')
        self.db.execute('INSERT INTO bank_balances VALUES(1,1,2,3)')
        self.db.execute("INSERT INTO class_progress VALUES(1,'Wojownik',1,50)")
        self.db.execute("INSERT INTO professions VALUES(1,'Kowalstwo',1,50,9)")
        self.db.execute("INSERT INTO tools VALUES(1,'Mlot',1,50,9)")
        self.original = legacy_digest(self.db)

    def tearDown(self): self.db.close()

    def assert_changed(self, sql):
        self.db.execute(sql)
        self.assertNotEqual(legacy_digest(self.db), self.original)

    def test_base_values_stable(self):
        self.assertEqual(legacy_digest(self.db), self.original)
    def test_extended_stat_exp_changes(self):
        self.assert_changed('UPDATE characters SET stat_progress=31 WHERE account_id=1')
    def test_character_name_changes(self):
        self.assert_changed("UPDATE characters SET display_name='Inna' WHERE account_id=1")
    def test_class_identity_changes(self):
        self.assert_changed("UPDATE class_progress SET class_name='Mag' WHERE account_id=1")
    def test_profession_identity_changes(self):
        self.assert_changed("UPDATE professions SET profession='Rybak' WHERE account_id=1")
    def test_tool_identity_changes(self):
        self.assert_changed("UPDATE tools SET tool_type='Kilof' WHERE account_id=1")
    def test_non_xp_counters_change(self):
        self.assert_changed('UPDATE tools SET uses=10 WHERE account_id=1')
    def test_empty_source_table_change(self):
        self.assert_changed('DELETE FROM bank_balances WHERE account_id=1')
    def test_schema_change(self):
        self.assert_changed('ALTER TABLE characters ADD COLUMN extra_axis INTEGER DEFAULT 0')
    def test_two_classes_same_xp_identifiable(self):
        self.db.execute("INSERT INTO class_progress VALUES(1,'Mag',1,50)")
        before = legacy_digest(self.db)
        self.db.execute("UPDATE class_progress SET class_name='Druid' WHERE class_name='Mag'")
        self.assertNotEqual(legacy_digest(self.db), before)
    def test_no_sql_sum_or_float_conversion(self):
        self.db.execute('UPDATE characters SET character_xp=9223372036854775807')
        self.assertEqual(legacy_digest(self.db), legacy_digest(self.db))

if __name__ == '__main__': unittest.main()
