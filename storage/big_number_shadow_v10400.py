# -*- coding: utf-8 -*-
"""v104 ETAP 1: opt-in, non-destructive shadow-store rehearsal.

This module is NOT wired into normal player writes. It must be executed only
on a disposable database copy until all gameplay read/write paths migrate.
"""
from __future__ import annotations

from hashlib import sha256
import sqlite3
from core.big_numbers_v10400 import canonical_uint, legacy_sqlite_uint

# Explicitly specified pilot columns only; no dynamic identifiers from users.
PILOT_COLUMNS = {
    'characters': ('account_id', ('character_xp', 'soul_xp', 'silver', 'gold', 'mithril')),
    'account_wallet': ('master_account_id', ('silver', 'gold', 'mithril')),
    'bank_balances': ('account_id', ('silver', 'gold', 'mithril')),
    'class_progress': ('account_id', ('xp',)),
}


# Additional character axes are available exclusively to the guarded offline
# rehearsal API. Do NOT add them to PILOT_COLUMNS: the legacy mirror operation
# is a separate tool and must retain its old scope/expected row counts.
EXTRA_COPY_WORK_AXES = ('professions.xp', 'tools.xp')

EXTRA_COPY_PROGRESS_AXES = (
    'characters.character_level', 'characters.soul_level',
    'characters.soul_tier', 'characters.soul_weapon_mastery_level',
    'characters.soul_weapon_mastery_xp', 'characters.stat_progress',
    'characters.strength_progress', 'characters.dexterity_progress',
    'characters.constitution_progress', 'characters.intelligence_progress',
    'characters.willpower_progress', 'characters.charisma_progress',
)


def fingerprint(text: str) -> str:
    return sha256(text.encode('utf-8')).hexdigest()  # ASCII checksums remain identical


def _validate_axis(axis: str, subkey: str) -> None:
    if axis not in ({f'{table}.{field}' for table, (_, fields) in PILOT_COLUMNS.items() for field in fields}
                     | set(EXTRA_COPY_PROGRESS_AXES) | set(EXTRA_COPY_WORK_AXES)):
        raise ValueError('Niedozwolona os liczbowa w migracji probnej.')
    if not isinstance(subkey, str) or len(subkey) > 160:
        raise ValueError('Niedozwolony klucz osi.')
    if axis in ('class_progress.xp', *EXTRA_COPY_WORK_AXES) and not subkey:
        raise ValueError('Dla biegłości podaj nazwe klasy w source_key.')
    if axis not in ('class_progress.xp', *EXTRA_COPY_WORK_AXES) and subkey:
        raise ValueError('Nieoczekiwany klucz w osi bez podzialu na klasy.')


def install_shadow_schema(conn: sqlite3.Connection) -> None:
    """Only on a disposable copy. Never called in production init()."""
    conn.execute('''CREATE TABLE IF NOT EXISTS big_number_shadow_v10400 (
       account_id INTEGER NOT NULL,
       axis TEXT NOT NULL,
       source_key TEXT NOT NULL DEFAULT '',
       balance_text TEXT NOT NULL,
       base_int64_text TEXT NOT NULL,
       sha256 TEXT NOT NULL,
       PRIMARY KEY (account_id, axis, source_key)
    )''')


def stage_shadow(conn: sqlite3.Connection, account_id: int, axis: str,
                 value: str | int, *, source_key: str = '', base_value: str | int = 0) -> None:
    """Stage a value for a future migration; does not affect the actual game."""
    _validate_axis(axis, source_key)
    uid = legacy_sqlite_uint(account_id)
    text, original = canonical_uint(value), canonical_uint(base_value)
    if uid < 1:
        raise ValueError('Brak konta.')
    digest = fingerprint(f'{uid}|{axis}|{source_key}|{text}|{original}')
    conn.execute('''INSERT INTO big_number_shadow_v10400
       (account_id,axis,source_key,balance_text,base_int64_text,sha256)
       VALUES (?,?,?,?,?,?)
       ON CONFLICT(account_id,axis,source_key) DO UPDATE SET
        balance_text=excluded.balance_text,
        base_int64_text=excluded.base_int64_text,
        sha256=excluded.sha256''', (uid, axis, source_key, text, original, digest))


def fetch_shadow(conn: sqlite3.Connection, account_id: int, axis: str, *, source_key: str = '') -> int | None:
    _validate_axis(axis, source_key)
    row = conn.execute('''SELECT balance_text,base_int64_text,sha256
        FROM big_number_shadow_v10400 WHERE account_id=? AND axis=? AND source_key=?''',
        (legacy_sqlite_uint(account_id), axis, source_key)).fetchone()
    if row is None:
        return None
    text, original, digest = tuple(row)
    text, original = canonical_uint(text), canonical_uint(original)
    expected = fingerprint(f'{int(account_id)}|{axis}|{source_key}|{text}|{original}')
    if expected != digest:
        raise ValueError('Niespojny wpis shadow (checksum).')
    return int(text)


def check_shadow_legacy_mirrors(conn: sqlite3.Connection) -> int:
    """Copy-only gate: verify signed shadow AND each unchanged legacy mirror.

    A valid SHA256 is insufficient if a legacy writer changed an INTEGER
    after migration. Reject stale, orphaned and non-integer values.
    SQL identifiers are selected exclusively from internal fixed allowlists.
    """
    checked = check_shadow(conn)
    allowed = {table: (pk, set(fields)) for table, (pk, fields) in PILOT_COLUMNS.items()}
    allowed['characters'][1].update(axis.split('.', 1)[1] for axis in EXTRA_COPY_PROGRESS_AXES)
    allowed['professions'] = ('account_id', {'xp'})
    allowed['tools'] = ('account_id', {'xp'})
    subkeys = {'class_progress': 'class_name', 'professions': 'profession', 'tools': 'tool_type'}
    for uid, axis, key, baseline in conn.execute('''SELECT
        account_id,axis,source_key,base_int64_text
        FROM big_number_shadow_v10400'''):
        table, field = axis.split('.', 1)
        if table not in allowed or field not in allowed[table][1]:
            raise ValueError('BigNumber: nieznane pole w shadow.')
        pk = allowed[table][0]
        if table in subkeys:
            other = subkeys[table]
            current = conn.execute(
                f'SELECT "{field}" FROM "{table}" WHERE "{pk}"=? AND "{other}"=?',
                (uid, key)).fetchone()
        else:
            current = conn.execute(
                f'SELECT "{field}" FROM "{table}" WHERE "{pk}"=?',
                (uid,)).fetchone()
        if current is None:
            raise ValueError(f'BigNumber: osierocony rekord shadow: {axis}.')
        actual = current[0]
        if type(actual) is not int or actual < 0:
            raise ValueError(f'BigNumber: uszkodzone INTEGER w {axis}.')
        if canonical_uint(actual) != baseline:
            raise ValueError(f'BigNumber: stary zapis INTEGER zmieniony poza migracja: {axis}.')
    return checked


def mirror_legacy_copy(conn: sqlite3.Connection) -> dict[str,int]:
    """Mirror legacy values on an explicitly supplied disposable db connection.

    Old columns are NEVER modified; missing tables skipped, no synthetic users.
    Existing pilot shadow values cannot be overwritten by re-running a mirror.
    """
    install_shadow_schema(conn)
    check_shadow_legacy_mirrors(conn)  # no silent reuse of stale shadows
    counts = {}
    for table,(pk,fields) in PILOT_COLUMNS.items():
        present={r[1] for r in conn.execute(f'PRAGMA table_info("{table}")')}
        if not {pk,*fields}.issubset(present):
            counts[table]=0
            continue
        extra = ('class_name',) if table == 'class_progress' else ()
        if not set(extra).issubset(present):
            counts[table]=0
            continue
        selected = ','.join([f'"{pk}"', *(f'"{v}"' for v in extra),
                             *(f'"{v}"' for v in fields)])
        rows = conn.execute(f'SELECT {selected} FROM "{table}"')
        inserted = 0
        for row in rows:
            uid = row[0]
            if uid is None:
                continue
            subkey = str(row[1]) if extra else ''
            for field,raw in zip(fields, row[1+len(extra):]):
                if raw is None:
                    continue
                axis=f'{table}.{field}'
                if fetch_shadow(conn,uid,axis,source_key=subkey) is not None:
                    continue
                original=canonical_uint(raw)
                stage_shadow(conn, uid, axis, original,
                             source_key=subkey, base_value=original)
                inserted+=1
        counts[table]=inserted
    return counts


def check_shadow(conn: sqlite3.Connection) -> int:
    """Checksum every entry, assert canonical format and preserved baseline."""
    count=0
    for uid,axis,key,value,original,digest in conn.execute('''SELECT
      account_id,axis,source_key,balance_text,base_int64_text,sha256
      FROM big_number_shadow_v10400'''):
        _validate_axis(axis,key)
        if canonical_uint(value)!=value or canonical_uint(original)!=original:
            raise ValueError('Niekanoniczna liczba TEXT.')
        if fingerprint(f'{uid}|{axis}|{key}|{value}|{original}')!=digest:
            raise ValueError('Bledna suma kontrolna shadow.')
        count+=1
    return count
