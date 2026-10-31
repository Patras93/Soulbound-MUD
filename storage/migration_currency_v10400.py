# -*- coding: utf-8 -*-
"""Bezpieczne przeliczenie istniejących sald przed migracją starych kont.

Ważne: to NIE jest aktywacja produkcyjnego BigNumber. Pomaga wstrzymać
migrację, zanim SQL SUM lub SQLite REAL utraci dokładność starych danych.
"""
from __future__ import annotations

from core.sqlite_numeric_guard_v10400 import require_sqlite_int64


CURRENCY_FIELDS = ('silver', 'gold', 'mithril')


def sum_slot_currency_v104(conn, master_id: int, table: str):
    """Sumuj *w Python int*, nigdy SQLite SUM/REAL. Tylko stała lista tabel.

    Zwróć pełne wartości int (nie obcinaj jeszcze do limitu), by istniejąca
    normalizacja mogła zgłosić błąd przed pierwszym zapisem transakcyjnym.
    """
    if table == 'characters':
        query = '''SELECT c.silver,c.gold,c.mithril
            FROM account_characters ac
            JOIN characters c ON c.account_id=ac.character_account_id
            WHERE ac.master_account_id=?'''
    elif table == 'bank_balances':
        query = '''SELECT b.silver,b.gold,b.mithril
            FROM account_characters ac
            LEFT JOIN bank_balances b ON b.account_id=ac.character_account_id
            WHERE ac.master_account_id=?'''
    else:
        raise ValueError('Nieznane źródło pieniędzy.')
    totals = [0, 0, 0]
    for row in conn.execute(query, (int(master_id),)):
        for i, axis in enumerate(CURRENCY_FIELDS):
            raw = row[i]
            if raw is None and table == 'bank_balances':
                continue  # LEFT JOIN bez konta bankowego
            # Odrzuć float/TEXT i liczby ujemne przed jakimkolwiek UPDATE.
            value = require_sqlite_int64(table + '.' + axis, raw)
            if value < 0:
                raise ValueError('Ujemne saldo w ' + table + '.' + axis)
            totals[i] += value
    return tuple(totals)


def strict_legacy_coins_v104(silver, gold, mithril, legacy_currency_to_coins):
    """Stara konwersja nominałów bez cast REAL, zaokrągleń i ujemnych sald."""
    values = []
    for axis, raw in zip(CURRENCY_FIELDS, (silver, gold, mithril)):
        v = require_sqlite_int64('legacy_currency.' + axis, raw)
        if v < 0:
            raise ValueError('Ujemne saldo starej waluty: ' + axis)
        values.append(v)
    result = legacy_currency_to_coins(*values)
    # Przed konwersją do kolumn INTEGER gwarantuj bezpieczny limit ekonomii.
    from core.bootstrap_economy_professions import CURRENCY_SQLITE_SAFE_TOTAL
    if result > CURRENCY_SQLITE_SAFE_TOTAL:
        from core.sqlite_numeric_guard_v10400 import SQLiteNumericLimitV104
        raise SQLiteNumericLimitV104(
            'Stara waluta: pełna kwota poza bezpiecznym zakresem zapisu SQLite.'
        )
    return require_sqlite_int64('legacy_currency.coins', result)
