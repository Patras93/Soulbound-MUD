# -*- coding: utf-8 -*-
"""Offline v108 EQ rollback proof. Source database is opened read-only.

An isolated snapshot is captured with sqlite3.backup (including WAL-committed
pages); migration is rehearsed on a distinct disposable copy. A third DB is
restored from the pre-migration snapshot, never from the migrated clone. The
snapshot and restored copy must match by integrity check, complete schema and
all table records, including BLOB, sqlite_sequence and without-rowid tables,
and by the SHA-256 hash of the physical SQLite database image.

No production activation, source DB mutation, players or TCP sessions.
"""
from __future__ import annotations

from contextlib import closing
from hashlib import sha256
from pathlib import Path
import os
import sqlite3
import tempfile
import time

_MODULUS = 1 << 256


def _deadline(start, seconds):
    if time.monotonic() - start >= seconds:
        raise TimeoutError('Przekroczono bezpieczny limit audytu EQ')


def _bytes(value):
    """Unambiguous canonical SQLite typed-cell encoding, including raw BLOB."""
    if value is None:
        return b'N'
    if isinstance(value, bool):  # Python booleans are not stored by SQLite.
        value = int(value)
    if isinstance(value, int):
        raw = str(value).encode('ascii'); tag = b'I'
    elif isinstance(value, float):
        raw = value.hex().encode('ascii'); tag = b'F'
    elif isinstance(value, str):
        raw = value.encode('utf-8', 'surrogatepass'); tag = b'T'
    elif isinstance(value, (bytes, bytearray, memoryview)):
        raw = bytes(value); tag = b'B'
    else:
        raise TypeError('Nieznany typ pola SQLite')
    return tag + len(raw).to_bytes(8, 'big') + raw


def _fields(*values):
    return b''.join(_bytes(value) for value in values)


def _name(name):
    return '"' + str(name).replace('"', '""') + '"'


def file_sha256(path, start, seconds):
    digest = sha256()
    with Path(path).open('rb') as stream:
        while data := stream.read(1024 * 1024):
            _deadline(start, seconds)
            digest.update(data)
    return digest.hexdigest()


def fingerprint_database(conn, *, start=None, seconds=120):
    """Complete streaming fingerprint, invariant under SQL row iteration order.

    Per-row SHA256 digests are combined with modular sum + XOR and count to
    preserve multiplicity without storing or exposing individual player rows.
    Physical SHA256 is additionally compared in the restore proof; the logical
    digest is a diagnostic and not a substitute for page-for-page equality.
    """
    if start is None:
        start = time.monotonic()
    _deadline(start, seconds)
    valid = conn.execute('PRAGMA integrity_check').fetchone()
    if not valid or valid[0] != 'ok':
        raise sqlite3.DatabaseError('Niespójna baza SQLite')
    # Use sqlite_master (not a hard-coded list) so future gear tables, views,
    # triggers, indexes, sqlite_sequence and SQLite extension tables count.
    schema = conn.execute('SELECT type,name,tbl_name,sql FROM sqlite_master '
                          'ORDER BY type,name,tbl_name,sql').fetchall()
    digest = sha256(b'SOULBOUND-V108-EQ-SCHEMA-AND-ROWS-v1\0')
    for record in schema:
        _deadline(start, seconds)
        digest.update(_fields(*record))
    tables = sorted(str(record[1]) for record in schema if record[0] == 'table')
    total_rows = 0
    for table in tables:
        _deadline(start, seconds)
        # Every row, including empty tables, NULL, Unicode, BLOB and duplicates.
        rows = 0
        row_sum = 0
        row_xor = 0
        with closing(conn.execute('SELECT * FROM ' + _name(table))) as cursor:
            while True:
                batch = cursor.fetchmany(512)
                if not batch:
                    break
                _deadline(start, seconds)
                for row in batch:
                    value = int.from_bytes(sha256(b'ROW\0' + _fields(*row)).digest(), 'big')
                    row_sum = (row_sum + value) % _MODULUS
                    row_xor ^= value
                    rows += 1
        digest.update(_fields(table, rows))
        digest.update(row_sum.to_bytes(32, 'big'))
        digest.update(row_xor.to_bytes(32, 'big'))
        total_rows += rows
    _deadline(start, seconds)
    return {'sha256': digest.hexdigest(), 'tables': len(tables),
            'schema_objects': len(schema), 'rows': total_rows,
            'sqlite_integrity': True}


def _backup(source, destination, start, seconds):
    """Bounded SQLite online-backup API; destination is always disposable."""
    _deadline(start, seconds)
    with closing(sqlite3.connect(destination, timeout=2)) as dst:
        def progress(_status, _remaining, _total):
            _deadline(start, seconds)
        source.backup(dst, pages=256, progress=progress, sleep=0.02)
    _deadline(start, seconds)


def rehearse_restore(source_db, migrate_clone, *, limit_seconds=120):
    """Read-only source -> snapshot -> migrated clone -> independent restore.

    `migrate_clone` is called with a sqlite3.Connection to the disposable clone
    ONLY. All temporary files are destroyed when this function returns.
    Returns aggregate flags with no account IDs, items, SQL values or DB paths.
    """
    if not callable(migrate_clone):
        raise TypeError('Nieprawidłowa funkcja próbnej migracji')
    if not 0 < limit_seconds <= 3600:
        raise ValueError('Nieprawidłowy limit czasu')
    source = Path(source_db).expanduser().resolve(strict=True)
    if not source.is_file() or source.suffix.lower() not in ('.db', '.sqlite', '.sqlite3', '.db3'):
        raise ValueError('Podaj plik źródłowy SQLite')
    start = time.monotonic()
    with tempfile.TemporaryDirectory(prefix='soulbound108_eq_proof_') as directory:
        directory = Path(directory)
        snapshot = directory / 'PRE_MIGRATION_SNAPSHOT.sqlite'
        migrated = directory / 'MIGRATION_CLONE.sqlite'
        restored = directory / 'RESTORED_COPY.sqlite'
        # Never open the production/source filename with write privileges.
        with closing(sqlite3.connect(source.as_uri() + '?mode=ro', uri=True, timeout=2)) as origin:
            origin.execute('PRAGMA query_only=ON')
            _backup(origin, snapshot, start, limit_seconds)
        with closing(sqlite3.connect(snapshot.as_uri()+'?mode=ro', uri=True)) as original:
            before = fingerprint_database(original, start=start, seconds=limit_seconds)
        snapshot_hash = file_sha256(snapshot, start, limit_seconds)
        with closing(sqlite3.connect(snapshot.as_uri()+'?mode=ro', uri=True)) as original:
            _backup(original, migrated, start, limit_seconds)
        with closing(sqlite3.connect(migrated, timeout=2)) as trial:
            migration_result = migrate_clone(trial)
            trial.commit()
            migrated_integrity = fingerprint_database(trial, start=start, seconds=limit_seconds)['sqlite_integrity']
        with closing(sqlite3.connect(snapshot.as_uri()+'?mode=ro', uri=True)) as original:
            _backup(original, restored, start, limit_seconds)
        with closing(sqlite3.connect(restored.as_uri()+'?mode=ro', uri=True)) as result:
            after = fingerprint_database(result, start=start, seconds=limit_seconds)
        snapshot_unchanged = snapshot_hash == file_sha256(snapshot, start, limit_seconds)
        restored_bytes_equal = snapshot_hash == file_sha256(restored, start, limit_seconds)
        data_equal = (before == after)
        if not snapshot_unchanged or not restored_bytes_equal or not data_equal:
            raise RuntimeError('EQ v108: próba odtworzenia nie przywróciła pełnej bazy')
        _deadline(start, limit_seconds)
        return {'rollback_rehearsed': True,
                'rollback_data_equal': data_equal,
                'rollback_sqlite_integrity': after['sqlite_integrity'],
                'rollback_bytes_equal': restored_bytes_equal,
                'snapshot_unchanged': snapshot_unchanged,
                'migrated_sqlite_integrity': migrated_integrity,
                'schema_objects': before['schema_objects'],
                'tables': before['tables'], 'rows': before['rows'],
                'snapshot_sha256': before['sha256'],
                'migration_result': migration_result,
                'elapsed_seconds': round(time.monotonic()-start, 3)}
