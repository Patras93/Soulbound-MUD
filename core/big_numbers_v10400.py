# -*- coding: utf-8 -*-
"""v104 ETAP 1: decimal TEXT number foundation (not a live game cap override).

No floats, no SQL numeric SUM/CAST on decimal TEXT. Positive large values are
stored as canonical strings. Resource guard applies to a *single operation*;
this is NOT the player's progression limit. Integration with legacy INTEGER
columns remains blocked until every dependent gameplay write is migrated.
"""
from __future__ import annotations

import re

SQLITE_INT64_MIN = -(1 << 63)
SQLITE_INT64_MAX = (1 << 63) - 1
# CPython's default int<->str guard is 4300 decimal digits; stay beneath it.
MAX_DECIMAL_DIGITS_PER_OPERATION = 4096
_DECIMAL = re.compile(r"^[0-9]+$", re.ASCII)


def canonical_uint(value: int | str) -> str:
    """Canonical, nonnegative base-10 text; never parse via float or SQLite."""
    if isinstance(value, bool) or not isinstance(value, (int, str)):
        raise TypeError('Oczekiwana liczba calkowita lub tekst dziesietny.')
    if isinstance(value, int):
        if value < 0:
            raise ValueError('Liczba nie moze byc ujemna.')
        if value.bit_length() > 13610:
            raise ValueError('Operacja przekracza bezpieczny rozmiar wejscia.')
        raw = str(value)
    else:
        raw = value
        if not raw or len(raw) > MAX_DECIMAL_DIGITS_PER_OPERATION:
            raise ValueError('Nieprawidlowa dlugosc liczby dziesietnej.')
        if not _DECIMAL.fullmatch(raw):
            raise ValueError('Dozwolone sa tylko cyfry 0-9, bez znaku i spacji.')
    if len(raw) > MAX_DECIMAL_DIGITS_PER_OPERATION:
        raise ValueError('Operacja przekracza bezpieczny rozmiar wejscia.')
    return raw.lstrip('0') or '0'


def number(value: int | str) -> int:
    return int(canonical_uint(value))


def add(left: int | str, right: int | str) -> str:
    return canonical_uint(number(left) + number(right))


def subtract(left: int | str, right: int | str) -> str:
    a, b = number(left), number(right)
    if b > a:
        raise ValueError('Nie wolno uzyskac ujemnego salda.')
    return canonical_uint(a - b)


def compare(left: int | str, right: int | str) -> int:
    a, b = canonical_uint(left), canonical_uint(right)
    if len(a) != len(b):
        return (len(a) > len(b)) - (len(a) < len(b))
    return (a > b) - (a < b)


def sortable(value: int | str) -> tuple[int, str]:
    """For Python sorting; SQLite TEXT ORDER BY alone sorts numerically wrong."""
    s = canonical_uint(value)
    return len(s), s


def legacy_sqlite_uint(value: int | str) -> int:
    """Explicitly refuse silent clamping or floating point SQLite overflow."""
    n = number(value)
    if n > SQLITE_INT64_MAX:
        raise OverflowError('Wartosc przekracza SQLite int64; wymagany zapis TEXT v104.')
    return n


def sum_values(values) -> str:
    """Use Python integers for a decimal TEXT aggregate, never SQL SUM(TEXT)."""
    total = 0
    for value in values:
        total += number(value)
    return canonical_uint(total)
