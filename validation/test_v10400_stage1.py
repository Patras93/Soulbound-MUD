# -*- coding: utf-8 -*-
"""Actual executable offline unit/regression checks for the first v104 stage."""
from __future__ import annotations

from contextlib import closing
from pathlib import Path
import sqlite3
import tempfile
import unittest

from core.big_numbers_v10400 import (canonical_uint, number, add, subtract,
     compare, sortable, legacy_sqlite_uint, sum_values, SQLITE_INT64_MAX)
from storage.big_number_shadow_v10400 import (install_shadow_schema, stage_shadow,
    fetch_shadow, mirror_legacy_copy, check_shadow)
from validation.v10400_big_number_audit import audit, open_read_only
from validation.v10400_migration_rehearsal import rehearse


class BigNumberTest(unittest.TestCase):
    def test_roundtrip(self):
        for n in (0, 1, 42, 800, 5000, 10000, 1000000000,
                  2**63-1, 2**63, 2**64, 10**100, 10**1000):
            with self.subTest(n=n):
                self.assertEqual(number(canonical_uint(n)), n)
                self.assertEqual(canonical_uint('000'+str(n)),str(n))

    def test_reject_garbage(self):
        for value in ('', '-1', '+1', '1.0', '1e9', ' 1', '1 ', '一', '1\n2',
                      'NaN', 'inf', '01x', '9'*4097, -1, True, 1.0, None, b'3'):
            with self.subTest(value=str(value)[:40]), self.assertRaises((ValueError, TypeError)):
                canonical_uint(value)

    def test_math(self):
        a=2**120
        self.assertEqual(add(str(a),str(a)),str(2*a))
        self.assertEqual(subtract(str(a*3),str(a)),str(a*2))
        self.assertEqual(compare('0000002','2'),0)
        self.assertLess(compare('9','10'),0)
        self.assertGreater(compare('100','99'),0)
        self.assertEqual(sorted(['300','2','22','100'],key=sortable),['2','22','100','300'])
        self.assertEqual(sum_values([2**80,2**80, '02']),str(2**81+2))
        with self.assertRaises(ValueError):subtract('1','2')

    def test_legacy_range(self):
        self.assertEqual(legacy_sqlite_uint(SQLITE_INT64_MAX),SQLITE_INT64_MAX)
        with self.assertRaises(OverflowError):legacy_sqlite_uint(SQLITE_INT64_MAX+1)

    def test_large_near_decimal_guard(self):
        for length in (100,500,1000,3000,4090):
            n='9'*length
            with self.subTest(length=length):
                self.assertEqual(number(n)+1,10**length)
                self.assertEqual(subtract(add(n,'1'),'1'),n)


class ShadowTest(unittest.TestCase):
    def setUp(self):
        self.db=sqlite3.connect(':memory:')
        self.db.executescript('''
          CREATE TABLE characters (account_id INTEGER PRIMARY KEY, character_xp INTEGER,
              soul_xp INTEGER,silver INTEGER,gold INTEGER,mithril INTEGER);
          CREATE TABLE account_wallet (master_account_id INTEGER PRIMARY KEY,
              silver INTEGER,gold INTEGER,mithril INTEGER);
          CREATE TABLE bank_balances (account_id INTEGER PRIMARY KEY,
              silver INTEGER,gold INTEGER,mithril INTEGER);
          CREATE TABLE class_progress (account_id INTEGER, class_name TEXT, xp INTEGER);
          INSERT INTO characters VALUES (1,500000,900,250,2,0);
          INSERT INTO account_wallet VALUES (1,250,2,0);
          INSERT INTO bank_balances VALUES (1,1000,0,0);
          INSERT INTO class_progress VALUES (1,'Mag',2000);
          INSERT INTO class_progress VALUES (1,'Druid',3300);
        ''')

    def tearDown(self):self.db.close()

    def test_mirror_twice_and_immutable(self):
        counts=mirror_legacy_copy(self.db)
        self.assertEqual(counts['characters'],5)
        self.assertEqual(counts['account_wallet'],3)
        self.assertEqual(counts['bank_balances'],3)
        self.assertEqual(counts['class_progress'],2)
        self.assertEqual(sum(counts.values()),13)
        self.assertEqual(sum(mirror_legacy_copy(self.db).values()),0)
        self.assertEqual(check_shadow(self.db),13)
        self.assertEqual(fetch_shadow(self.db,1,'characters.character_xp'),500000)
        self.assertEqual(fetch_shadow(self.db,1,'class_progress.xp',source_key='Mag'),2000)
        self.assertEqual(fetch_shadow(self.db,1,'class_progress.xp',source_key='Druid'),3300)
        self.assertEqual(self.db.execute('SELECT character_xp FROM characters').fetchone()[0],500000)

    def test_above_int64_never_touches_legacy(self):
        install_shadow_schema(self.db)
        value=str(10**100)
        stage_shadow(self.db,1,'characters.character_xp',value,base_value=500000)
        self.assertEqual(fetch_shadow(self.db,1,'characters.character_xp'),10**100)
        self.assertEqual(self.db.execute('SELECT character_xp FROM characters').fetchone()[0],500000)
        self.assertEqual(check_shadow(self.db),1)

    def test_bad_axis_and_checksums(self):
        install_shadow_schema(self.db)
        with self.assertRaises(ValueError):stage_shadow(self.db,1,'characters.password_hash','9')
        stage_shadow(self.db,1,'characters.gold','99',base_value=2)
        self.db.execute("UPDATE big_number_shadow_v10400 SET balance_text='100' WHERE axis='characters.gold'")
        with self.assertRaises(ValueError):fetch_shadow(self.db,1,'characters.gold')
        with self.assertRaises(ValueError):check_shadow(self.db)

    def test_sql_audit(self):
        a=audit(self.db)
        self.assertEqual(a['integrity'],'PASS')
        self.assertEqual(a['near_int64'],0)
        self.assertGreater(a['rows_checked'],0)

    def test_readonly_rehearsal(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'fake_players.db'
            with closing(sqlite3.connect(p)) as destination:self.db.backup(destination)
            size=p.stat().st_size
            r=rehearse(p)
            self.assertEqual(r['production_modified'],'NIE')
            self.assertEqual(r['idempotent'],'PASS')
            self.assertEqual(r['legacy_unchanged'],'PASS')
            self.assertEqual(r['shadow_checks'],13)
            self.assertEqual(p.stat().st_size,size)
            with closing(open_read_only(p)) as db:
                self.assertFalse(db.execute("SELECT 1 FROM sqlite_master WHERE name='big_number_shadow_v10400'").fetchone())


if __name__=='__main__':unittest.main(verbosity=2)
