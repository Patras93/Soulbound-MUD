# -*- coding: utf-8 -*-
"""Fail-closed preflight of the four legacy BigNumber pilot tables.

Operates on a temporary SQLite snapshot, never on a production DB connection.
The expected cell count is checked against shadow entries after the rehearsal.
This is NOT a production migration switch.
"""
from __future__ import annotations

import sqlite3
from storage.big_number_shadow_v10400 import PILOT_COLUMNS


KEY_COLUMNS = {
    'class_progress': 'class_name',
}


def inspect_pilot_snapshot(conn: sqlite3.Connection) -> dict:
    """Check structure, row types and count *all* cells before any copying.

    SQLite SUM on an EXP/currency column is deliberately never used.
    The only SQL aggregation used here counts rows, not values.
    """
    outcome = {'rows': {}, 'cells': {}, 'total_rows': 0, 'total_cells': 0}
    for table, (pk, axes) in PILOT_COLUMNS.items():
        present = {
            row[1]: row[2].upper() for row in conn.execute(f'PRAGMA table_info("{table}")')
        }
        required = (pk, *axes) + ((KEY_COLUMNS[table],) if table in KEY_COLUMNS else ())
        missing = [col for col in required if col not in present]
        if missing:
            raise ValueError(f'BigNumber PRECHECK: {table}: brak tabeli lub kolumn: {", ".join(missing)}')
        for name in (pk, *axes):
            # SQLite affinity is relevant: shadow comparisons cannot safely
            # reconcile a REAL/TEXT legacy column with the int64 baseline.
            if 'INT' not in present[name]:
                raise ValueError(f'BigNumber PRECHECK: {table}.{name}: niezgodny typ INTEGER.')
        extra = (KEY_COLUMNS[table],) if table in KEY_COLUMNS else ()
        selected = ','.join(f'"{col}"' for col in (*required,))
        count = 0
        cells = 0
        seen = set()
        for record in conn.execute(f'SELECT {selected} FROM "{table}"'):
            key_value, *remaining = record
            if type(key_value) is not int or key_value < 1:
                raise ValueError(f'BigNumber PRECHECK: {table}: niepoprawny identyfikator konta.')
            if extra:
                subkey = remaining.pop(-1)
                if not isinstance(subkey, str) or not subkey or len(subkey) > 160:
                    raise ValueError(f'BigNumber PRECHECK: {table}: niepoprawny klucz klasy.')
                key = (key_value, subkey)
            else:
                key = (key_value,)
            if key in seen:
                raise ValueError(f'BigNumber PRECHECK: {table}: powielony identyfikator.')
            seen.add(key)
            count += 1
            for val in remaining:
                if type(val) is not int or val < 0:
                    raise ValueError(f'BigNumber PRECHECK: {table}: niekanoniczna wartosc INTEGER.')
                cells += 1
        outcome['rows'][table] = count
        outcome['cells'][table] = cells
        outcome['total_rows'] += count
        outcome['total_cells'] += cells
    return outcome


def require_exact_pilot_coverage(conn: sqlite3.Connection, expected: dict) -> None:
    """Verify a signed shadow entry exists for every legacy numeric cell."""
    # This does not merely compare global totals: exact axis coverage avoids a
    # missing one and duplicated another cancelling each other out.
    from storage.big_number_shadow_v10400 import fetch_shadow
    for table, (pk, axes) in PILOT_COLUMNS.items():
        keycol = KEY_COLUMNS.get(table)
        fields = (pk,) + ((keycol,) if keycol else ()) + tuple(axes)
        query = ','.join(f'"{field}"' for field in fields)
        count = 0
        for row in conn.execute(f'SELECT {query} FROM "{table}"'):
            uid = row[0]
            source_key = str(row[1]) if keycol else ''
            values = row[2:] if keycol else row[1:]
            for axis, legacy in zip(axes, values):
                exact = fetch_shadow(conn, uid, f'{table}.{axis}', source_key=source_key)
                if exact is None:
                    raise ValueError(f'BigNumber PRECHECK: nieprzeniesione pole {table}.{axis}.')
                count += 1
        if count != expected['cells'][table]:
            raise ValueError(f'BigNumber PRECHECK: niezgodna liczba pol {table}.')
