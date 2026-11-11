# -*- coding: utf-8 -*-
"""Strict offline coverage for the v104 progression axes beyond four pilot tables.

No live-game activation. This module is used only on the disposable SQLite
backup created by validation.v10400_migration_rehearsal.
"""
from __future__ import annotations

from storage.big_number_shadow_v10400 import (
    EXTRA_COPY_PROGRESS_AXES, EXTRA_COPY_WORK_AXES,
    check_shadow_legacy_mirrors, fetch_shadow, install_shadow_schema, stage_shadow,
)

CHAR_FIELDS = tuple(axis.partition('.')[2] for axis in EXTRA_COPY_PROGRESS_AXES)
WORK_TABLES = {'professions': 'profession', 'tools': 'tool_type'}


def _columns(conn, table):
    return {row[1]: str(row[2]).upper() for row in conn.execute(f'PRAGMA table_info("{table}")')}


def extended_schema_present(conn):
    """Old pilot-only fixtures remain supported, but no partial full schema."""
    char_cols = _columns(conn, 'characters')
    # A genuine Soulbound database has accounts; its extended progression
    # layout must not be treated as a permissive pilot-only fixture even if
    # someone dropped *all* extended columns and both work tables.
    return (bool(_columns(conn, 'accounts'))
            or any(field in char_cols for field in CHAR_FIELDS)
            or any(_columns(conn, table) for table in WORK_TABLES))


def _shape(conn):
    result = {'characters': ('account_id', '', CHAR_FIELDS)}
    result.update((table, ('account_id', subkey, ('xp',)))
                  for table, subkey in WORK_TABLES.items())
    for table, (pk, subkey, fields) in result.items():
        cols = _columns(conn, table)
        required = (pk, *fields) + ((subkey,) if subkey else ())
        absent = [field for field in required if field not in cols]
        if absent:
            raise ValueError(f'BigNumber EXTENDED: {table}: brak tabeli lub kolumny: {", ".join(absent)}')
        for field in (pk, *fields):
            if 'INT' not in cols[field]:
                raise ValueError(f'BigNumber EXTENDED: {table}.{field}: wymagany INTEGER.')
        if subkey and 'TEXT' not in cols[subkey]:
            raise ValueError(f'BigNumber EXTENDED: {table}.{subkey}: wymagany TEXT.')
    return result


def _iterate(conn, schema):
    for table, (pk, subkey, fields) in schema.items():
        names = (pk,) + ((subkey,) if subkey else ()) + fields
        columns = ','.join('"'+name+'"' for name in names)
        seen = set()
        for row in conn.execute(f'SELECT {columns} FROM "{table}"'):
            uid = row[0]
            if type(uid) is not int or uid < 1:
                raise ValueError(f'BigNumber EXTENDED: {table}: niepoprawny identyfikator.')
            key = row[1] if subkey else ''
            if subkey and (not isinstance(key, str) or not key.strip() or len(key) > 160):
                raise ValueError(f'BigNumber EXTENDED: {table}: niepoprawny klucz.')
            identity = (uid, key)
            if identity in seen:
                raise ValueError(f'BigNumber EXTENDED: {table}: powielony rekord.')
            seen.add(identity)
            values = row[2:] if subkey else row[1:]
            for field, value in zip(fields, values):
                if type(value) is not int or value < 0:
                    raise ValueError(f'BigNumber EXTENDED: {table}.{field}: niekanoniczna wartosc.')
                yield uid, table + '.' + field, key, value


def inspect_extended_snapshot(conn):
    """Fail closed when extended layout is present but incomplete."""
    if not extended_schema_present(conn):
        return {'enabled': False, 'cells': 0}
    schema = _shape(conn)
    return {'enabled': True, 'cells': sum(1 for _ in _iterate(conn, schema))}


def mirror_extended_copy(conn, snapshot):
    """Called INSIDE the caller's SAVEPOINT, leaves legacy INTEGER unchanged."""
    if not snapshot['enabled']:
        return 0
    schema = _shape(conn)
    install_shadow_schema(conn)
    inserted = 0
    for uid, axis, key, legacy in _iterate(conn, schema):
        existing = fetch_shadow(conn, uid, axis, source_key=key)
        if existing is not None:
            # check_shadow_legacy_mirrors validates the preserved INTEGER base.
            continue
        stage_shadow(conn, uid, axis, legacy, source_key=key, base_value=legacy)
        inserted += 1
    check_extended_coverage(conn, snapshot)
    return inserted


def check_extended_coverage(conn, snapshot):
    if not snapshot['enabled']:
        return 0
    schema = _shape(conn)
    count = 0
    for uid, axis, key, value in _iterate(conn, schema):
        if fetch_shadow(conn, uid, axis, source_key=key) is None:
            raise ValueError(f'BigNumber EXTENDED: nieprzeniesiona wartosc {axis}.')
        count += 1
    if count != snapshot['cells']:
        raise ValueError('BigNumber EXTENDED: niezgodna liczba wartosci.')
    check_shadow_legacy_mirrors(conn)
    return count
