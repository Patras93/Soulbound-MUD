# -*- coding: utf-8 -*-
"""Version-independent read-only verification of a SQLite backup.

Compare full schema and row contents including binary blobs, not only row counts.
Only intended for *offline isolated* copy validation, never as an approval gate.
"""
from __future__ import annotations
import hashlib
import struct
import sqlite3


def _value_digest(value):
    digest=hashlib.sha256()
    if value is None:
        digest.update(b'N')
    elif isinstance(value, int):
        digest.update(b'I'+str(value).encode('ascii'))
    elif isinstance(value, float):
        digest.update(b'F'+struct.pack('!d',value))
    elif isinstance(value, str):
        digest.update(b'T'+value.encode('utf-8',errors='surrogatepass'))
    elif isinstance(value, bytes):
        digest.update(b'B'+value)
    else:
        raise TypeError('Nieznany typ danych SQLite: '+repr(type(value)))
    return digest.digest()


def fingerprint(db: sqlite3.Connection) -> str:
    """Canonical hash of schema and all table records (ordering-independent)."""
    d=hashlib.sha256()
    schema=list(db.execute('SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name,tbl_name,sql'))
    for item in schema:
        d.update(b'S')
        for v in item:
            d.update(_value_digest(v))
    # sqlite_sequence is included when present; virtual-table shadow tables too.
    for kind,name,table,sql in schema:
        if kind!='table' or name.startswith('sqlite_') and name!='sqlite_sequence':
            continue
        escaped='"'+name.replace('"','""')+'"'
        row_hashes=[]
        for record in db.execute('SELECT * FROM '+escaped):
            r=hashlib.sha256()
            for item in record:
                r.update(_value_digest(item))
            row_hashes.append(r.digest())
        d.update(b'T'+_value_digest(name)+struct.pack('!Q',len(row_hashes)))
        for h in sorted(row_hashes):
            d.update(h)
    return d.hexdigest()


def verify_equal(source: sqlite3.Connection, target: sqlite3.Connection) -> None:
    if source.execute('PRAGMA integrity_check').fetchone()!=('ok',):
        raise ValueError('Zrodlowa baza SQLite nie przeszla integrity_check')
    if target.execute('PRAGMA integrity_check').fetchone()!=('ok',):
        raise ValueError('Kopia SQLite nie przeszla integrity_check')
    if fingerprint(source)!=fingerprint(target):
        raise ValueError('Kopia SQLite rozni sie schematem lub zawartoscia rekordow, w tym EQ/BLOB')
