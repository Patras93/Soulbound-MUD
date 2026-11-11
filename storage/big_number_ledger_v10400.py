# -*- coding: utf-8 -*-
"""v104 stage 10: transactional TEXT ledger, prepared for **offline rehearsal**.

IMPORTANT: not activated in the game or during Database.__init__. Existing
INTEGER fields are immutable here. Replay this only against a throwaway copy.
Before a migration is enabled, all legacy readers/writers must be converted.
"""
from __future__ import annotations

import sqlite3

from core.big_numbers_v10400 import canonical_uint, number
from storage.big_number_shadow_v10400 import (
    PILOT_COLUMNS, _validate_axis, install_shadow_schema,
    fetch_shadow, stage_shadow,
)


class StaleLegacyValueV104(RuntimeError):
    """The old INTEGER balance changed; abort instead of overwriting it."""


class MissingLedgerRowV104(LookupError):
    pass


def _legacy_value(conn: sqlite3.Connection, account_id: int,
                  axis: str, source_key: str) -> str:
    _validate_axis(axis, source_key)
    table, field = axis.split('.', 1)
    pk, allowed = PILOT_COLUMNS[table]
    if field not in allowed:
        raise ValueError('Nieznane pole.')
    # All SQL identifiers are from hardcoded PILOT_COLUMNS; only data is bound.
    if table == 'class_progress':
        row = conn.execute(
            f'SELECT "{field}" FROM "{table}" WHERE "{pk}"=? AND class_name=?',
            (account_id, source_key),
        ).fetchone()
    else:
        row = conn.execute(
            f'SELECT "{field}" FROM "{table}" WHERE "{pk}"=?',
            (account_id,),
        ).fetchone()
    if row is None:
        raise MissingLedgerRowV104('Nie ma wiersza zrodlowego, bez tworzenia konta.')
    if type(row[0]) is not int:
        raise ValueError('Zrodlo nie jest calkowita liczba SQLite.')
    return canonical_uint(row[0])


def _row(conn, account_id, axis, source_key):
    return conn.execute(
        '''SELECT balance_text,base_int64_text FROM big_number_shadow_v10400
           WHERE account_id=? AND axis=? AND source_key=?''',
        (account_id, axis, source_key),
    ).fetchone()


def get_exact_copy(conn: sqlite3.Connection, account_id: int, axis: str,
                   *, source_key: str = '') -> int:
    """Fetch TEXT balance only if the old source still matches its baseline."""
    _validate_axis(axis, source_key)
    account_id = int(account_id)
    row = _row(conn, account_id, axis, source_key)
    if row is None:
        raise MissingLedgerRowV104('Najpierw utworz ledger na kopii.')
    if _legacy_value(conn, account_id, axis, source_key) != row[1]:
        raise StaleLegacyValueV104('Legacy zmienilo sie od utworzenia snapshotu.')
    result = fetch_shadow(conn, account_id, axis, source_key=source_key)
    if result is None:
        raise MissingLedgerRowV104('Nie znaleziono wpisu TEXT.')
    return result


def add_exact_copy(conn: sqlite3.Connection, account_id: int, axis: str,
                   delta: int, *, source_key: str = '') -> int:
    """Atomic exact increment of TEXT on a disposable copy; never touches INTEGER.

    SAVEPOINT works inside an existing transaction too. A negative delta is
    allowed only if the resulting balance remains nonnegative.
    """
    _validate_axis(axis, source_key)
    account_id = int(account_id)
    if account_id < 1 or type(delta) is not int:
        raise ValueError('Niepoprawne ID lub przyrost.')
    conn.execute('SAVEPOINT v104_big_number_text_trial')
    try:
        install_shadow_schema(conn)
        row = _row(conn, account_id, axis, source_key)
        source = _legacy_value(conn, account_id, axis, source_key)
        if row is None:
            current = number(source)
            baseline = source
        else:
            baseline = row[1]
            if baseline != source:
                raise StaleLegacyValueV104('Przestarzaly baseline; przerwano caly przyrost.')
            current = get_exact_copy(conn, account_id, axis, source_key=source_key)
        updated = current + delta
        if updated < 0:
            raise ValueError('Saldo nie moze byc ujemne.')
        # Bounds, decimal format and SHA256 are rechecked on each write.
        canonical_uint(updated)
        stage_shadow(conn, account_id, axis, updated, source_key=source_key,
                     base_value=baseline)
        if fetch_shadow(conn, account_id, axis, source_key=source_key) != updated:
            raise AssertionError('Niespojny odczyt TEXT.')
        conn.execute('RELEASE SAVEPOINT v104_big_number_text_trial')
        return updated
    except BaseException:
        conn.execute('ROLLBACK TO SAVEPOINT v104_big_number_text_trial')
        conn.execute('RELEASE SAVEPOINT v104_big_number_text_trial')
        raise
