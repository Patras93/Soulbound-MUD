# -*- coding: utf-8 -*-
"""Offline fixtures for full-data SQLite/WAL/EQ backup verification."""
from __future__ import annotations
from contextlib import closing
from pathlib import Path
import sqlite3
import tempfile
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from systems.current_sqlite_integrity import fingerprint,verify_equal
from systems.v11200_fresh_install import _sqlite_snapshot,FreshInstallError


def run():
    count=0
    with tempfile.TemporaryDirectory(prefix='sb112_sqlite_check_') as d:
        root=Path(d);src=root/'source.db';dst=root/'backup.db'
        with closing(sqlite3.connect(src)) as conn:
            conn.execute('PRAGMA journal_mode=WAL')
            conn.execute('CREATE TABLE characters (id INTEGER PRIMARY KEY, name TEXT, exp INTEGER)')
            conn.execute('CREATE TABLE eq (id INTEGER PRIMARY KEY AUTOINCREMENT, owner INTEGER, item BLOB)')
            conn.execute('CREATE INDEX eq_owner ON eq(owner)')
            conn.execute('CREATE VIEW eq_names AS SELECT owner FROM eq')
            conn.execute('CREATE TRIGGER eq_guard AFTER INSERT ON eq BEGIN SELECT 1; END')
            conn.execute('INSERT INTO characters VALUES(1,?,?)',('Żółw',900))
            conn.execute('INSERT INTO eq(owner,item) VALUES(?,?)',(1,b'\x00\xff\x00armor'))
            conn.commit()
            assert _sqlite_snapshot(src,dst)==3;count+=1
            with closing(sqlite3.connect(dst)) as copy:
                verify_equal(conn,copy);count+=1
                assert fingerprint(conn)==fingerprint(copy);count+=1
                copy.execute('UPDATE eq SET item=? WHERE id=1',(b'\x00\xff\x00sword',));copy.commit()
                try:verify_equal(conn,copy)
                except ValueError:count+=1
                else:raise AssertionError('BLOB corruption not detected')
                copy.execute('UPDATE eq SET item=? WHERE id=1',(b'\x00\xff\x00armor',))
                copy.execute('UPDATE characters SET exp=901 WHERE id=1');copy.commit()
                try:verify_equal(conn,copy)
                except ValueError:count+=1
                else:raise AssertionError('same-count character mutation not detected')
                copy.execute('UPDATE characters SET exp=900 WHERE id=1');copy.commit()
                verify_equal(conn,copy);count+=1
                copy.execute('DROP VIEW eq_names');copy.commit()
                try:verify_equal(conn,copy)
                except ValueError:count+=1
                else:raise AssertionError('schema drift not detected')
            # A second snapshot is unaffected by the deliberately mutated first copy.
            assert _sqlite_snapshot(src,root/'second.db')==3;count+=1
            # Prevent accidental overwrite with a non-SQLite file.
            bad=root/'not_database.db';bad.write_bytes(b'not sqlite')
            try:_sqlite_snapshot(bad,root/'bad_copy.db')
            except (FreshInstallError,sqlite3.DatabaseError):count+=1
            else:raise AssertionError('non-database was accepted')
    return count

if __name__=='__main__':
    n=run();print(f'V112 SQLITE FULL CONTENT: {n}/{n} PASS')
