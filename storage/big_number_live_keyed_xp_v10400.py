# -*- coding: utf-8 -*-
"""Production exact TEXT XP for classes, professions and tools (v104).

No INTEGER -> REAL conversion. The old SQLite column is only a saturated
compatibility mirror. Checksummed decimal TEXT is authoritative after the first
write. Direct legacy SQL may not modify an already-shadowed XP mirror.

This module does not enable character, wallet, bank or combat BigNumber.
"""
from __future__ import annotations

from hashlib import sha256

from core.big_numbers_v10400 import SQLITE_INT64_MAX, canonical_uint, number
from core.sqlite_numeric_guard_v10400 import require_sqlite_int64

# SQL identifiers are *fixed constants*, never caller input.
ROUTES = {
    'class': ('class_progress', 'class_name', None),
    'profession': ('professions', 'profession', 'actions'),
    'tool': ('tools', 'tool_type', 'uses'),
}


def _route(kind, account_id, key):
    if kind not in ROUTES:
        raise ValueError('BigNumber: nieznany rodzaj postepu.')
    uid = require_sqlite_int64('account_id', account_id)
    if uid <= 0 or not isinstance(key, str) or not key.strip() or len(key) > 160:
        raise ValueError('BigNumber: nieprawidlowy klucz postepu.')
    return uid, ROUTES[kind]


def _digest(uid, kind, key, value, mirror):
    return sha256(f'{uid}|{kind}|{key}|{value}|{mirror}'.encode('utf-8')).hexdigest()


def _receipt(uid, kind, key):
    return sha256(f'{uid}|{kind}|{key}|receipt'.encode('utf-8')).hexdigest()


def install_live_keyed_xp(conn):
    """Idempotent schema and fail-closed triggers; never migrates player rows."""
    conn.execute('''CREATE TABLE IF NOT EXISTS big_number_live_keyed_xp_v10400 (
        account_id INTEGER NOT NULL, kind TEXT NOT NULL, source_key TEXT NOT NULL,
        value_text TEXT NOT NULL, mirror_text TEXT NOT NULL, checksum TEXT NOT NULL,
        PRIMARY KEY (account_id,kind,source_key),
        FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE)''')
    conn.execute('''CREATE TABLE IF NOT EXISTS big_number_live_keyed_receipt_v10400 (
        account_id INTEGER NOT NULL, kind TEXT NOT NULL, source_key TEXT NOT NULL,
        checksum TEXT NOT NULL,
        PRIMARY KEY (account_id,kind,source_key),
        FOREIGN KEY(account_id) REFERENCES accounts(id) ON DELETE CASCADE)''')
    for kind, (table, key_col, _counter_col) in ROUTES.items():
        table_exists = conn.execute('SELECT 1 FROM sqlite_master WHERE type=\'table\' AND name=?',
                                    (table,)).fetchone()
        if table_exists is None:
            continue
        # Stage the new shadow *first*, then update the legacy mirror inside
        # the same SAVEPOINT. The trigger makes unconverted writers fail.
        for operation, column_filter in (('INSERT', ''), ('UPDATE', ' OF xp')):
            # INSERT OR IGNORE executes BEFORE INSERT triggers even when a
            # matching profile already exists. Never reject harmless lazy
            # ensure_* inserts that cannot change any existing XP.
            absent = (f'NOT EXISTS(SELECT 1 FROM \"{table}\" WHERE account_id=NEW.account_id AND \"{key_col}\"=NEW.\"{key_col}\") AND ' if operation == 'INSERT' else '')
            trigger = f'sb104_exact_{kind}_{operation.lower()}'
            conn.execute(f'''CREATE TRIGGER IF NOT EXISTS "{trigger}"
              BEFORE {operation}{column_filter} ON "{table}"
              WHEN {absent}EXISTS(
                SELECT 1 FROM big_number_live_keyed_xp_v10400 AS s
                 WHERE s.account_id=NEW.account_id AND s.kind='{kind}'
                   AND s.source_key=NEW."{key_col}"
                   AND s.mirror_text != CAST(NEW.xp AS TEXT))
              BEGIN SELECT RAISE(ABORT,'SB104: niezgodny lustrzany XP; uzyj metody zapisu BigNumber'); END''')


def _existing_row(db, uid, kind, key):
    table, key_col, _ = ROUTES[kind]
    row = db.conn.execute(
        f'SELECT xp FROM "{table}" WHERE account_id=? AND "{key_col}"=?',
        (uid, key)).fetchone()
    if row is None:
        raise LookupError('BigNumber: brak profilu klasy, profesji lub narzedzia.')
    if type(row[0]) is not int or row[0] < 0:
        raise ValueError('BigNumber: uszkodzony starszy zapis INTEGER.')
    return row[0]


def read_live_keyed_xp(db, account_id, kind, key):
    uid, _ = _route(kind, account_id, key)
    legacy = _existing_row(db, uid, kind, key)
    receipt = db.conn.execute('''SELECT checksum FROM big_number_live_keyed_receipt_v10400
        WHERE account_id=? AND kind=? AND source_key=?''', (uid, kind, key)).fetchone()
    exact = db.conn.execute('''SELECT value_text,mirror_text,checksum
        FROM big_number_live_keyed_xp_v10400
        WHERE account_id=? AND kind=? AND source_key=?''', (uid, kind, key)).fetchone()
    if receipt is not None and receipt[0] != _receipt(uid, kind, key):
        raise ValueError('BigNumber: uszkodzone potwierdzenie rekordu.')
    if receipt is not None and exact is None:
        raise ValueError('BigNumber: zniknal dokladny zapis TEXT — odmowa odczytu.')
    if exact is None:
        return legacy
    value, mirror, checksum = exact
    value = canonical_uint(value)
    mirror = canonical_uint(mirror)
    if checksum != _digest(uid, kind, key, value, mirror):
        raise ValueError('BigNumber: bledna suma kontrolna EXP.')
    if mirror != str(legacy) or int(mirror) != min(number(value), SQLITE_INT64_MAX):
        raise ValueError('BigNumber: przestarzaly zapis INTEGER, odmowa utraty EXP.')
    if receipt is None:
        raise ValueError('BigNumber: brak potwierdzenia dokladnego zapisu EXP.')
    return number(value)


def write_live_keyed_xp(db, account_id, kind, key, *, xp, level, counter=None):
    uid, (_table, _key_col, counter_col) = _route(kind, account_id, key)
    exact = canonical_uint(xp)
    mirror = min(number(exact), SQLITE_INT64_MAX)
    require_sqlite_int64(_table + '.level', level)
    if counter_col is None:
        if counter is not None:
            raise ValueError('Klasa nie posiada licznika pracy.')
    else:
        require_sqlite_int64(_table + '.' + counter_col, counter)
    conn = db.conn
    conn.execute('SAVEPOINT sb104_live_keyed_xp')
    try:
        # Detect lost/corrupted shadow before touching ANY player progress.
        read_live_keyed_xp(db, uid, kind, key)
        existing_exact = conn.execute('''SELECT 1 FROM big_number_live_keyed_xp_v10400
            WHERE account_id=? AND kind=? AND source_key=?''',
            (uid,kind,key)).fetchone()
        if mirror == number(exact) and existing_exact is None:
            # Ordinary in-range XP stays on the historical INTEGER path;
            # only an overflow or previously-migrated axis needs TEXT.
            if counter_col is None:
                cursor = conn.execute(
                    f'UPDATE "{_table}" SET level=?,xp=? WHERE account_id=? AND "{_key_col}"=?',
                    (level, mirror, uid, key))
            else:
                cursor = conn.execute(
                    f'UPDATE "{_table}" SET level=?,xp=?,"{counter_col}"=? WHERE account_id=? AND "{_key_col}"=?',
                    (level, mirror, counter, uid, key))
            if cursor.rowcount != 1:
                raise LookupError('BigNumber: nie znaleziono wiersza do zapisu.')
            conn.execute('RELEASE SAVEPOINT sb104_live_keyed_xp')
            return number(exact)
        conn.execute('''INSERT INTO big_number_live_keyed_xp_v10400
            (account_id,kind,source_key,value_text,mirror_text,checksum)
            VALUES(?,?,?,?,?,?) ON CONFLICT(account_id,kind,source_key)
            DO UPDATE SET value_text=excluded.value_text,
                mirror_text=excluded.mirror_text,checksum=excluded.checksum''',
            (uid, kind, key, exact, str(mirror), _digest(uid,kind,key,exact,str(mirror))))
        conn.execute('''INSERT INTO big_number_live_keyed_receipt_v10400
            (account_id,kind,source_key,checksum) VALUES(?,?,?,?)
            ON CONFLICT(account_id,kind,source_key) DO UPDATE SET checksum=excluded.checksum''',
            (uid,kind,key,_receipt(uid,kind,key)))
        if counter_col is None:
            cursor = conn.execute(
                f'UPDATE "{_table}" SET level=?,xp=? WHERE account_id=? AND "{_key_col}"=?',
                (level, mirror, uid, key))
        else:
            cursor = conn.execute(
                f'UPDATE "{_table}" SET level=?,xp=?,"{counter_col}"=? WHERE account_id=? AND "{_key_col}"=?',
                (level, mirror, counter, uid, key))
        if cursor.rowcount != 1:
            raise LookupError('BigNumber: nie znaleziono wiersza do zapisu.')
        if read_live_keyed_xp(db, uid, kind, key) != number(exact):
            raise AssertionError('BigNumber: niezgodny odczyt po zapisie.')
        conn.execute('RELEASE SAVEPOINT sb104_live_keyed_xp')
    except BaseException:
        try:
            conn.execute('ROLLBACK TO SAVEPOINT sb104_live_keyed_xp')
        finally:
            conn.execute('RELEASE SAVEPOINT sb104_live_keyed_xp')
        raise
    return number(exact)
