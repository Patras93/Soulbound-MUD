# -*- coding: utf-8 -*-
"""v104: precyzyjne mnozniki EXP powyzej granicy dokladnosci float.

Dla dawnych malych nagrod zachowuje dokladnie dotychczasowe round(float).
Dla ogromnych nagrod liczy na calkowitych licznikach i mianownikach,
zaokraglenie do parzystej przy remisie. To nie jest migracja bazy SQLite.
"""
from __future__ import annotations
import math
from decimal import Decimal
from fractions import Fraction

_FLOAT_EXACT_INTEGER = 1 << 53


def _nearest_even(numerator: int, denominator: int) -> int:
    if type(numerator) is not int or type(denominator) is not int or numerator < 0 or denominator <= 0:
        raise ValueError('Nieprawidlowy licznik/mianownik nagrody.')
    whole, remainder = divmod(numerator, denominator)
    twice = remainder * 2
    return whole + (twice > denominator or (twice == denominator and whole % 2 == 1))


def scale_multiplier_xp_v10400(amount: int, multiplier: int | float) -> int:
    if type(amount) is not int or amount < 0:
        raise ValueError('EXP musi byc nieujemna liczba calkowita.')
    if type(multiplier) not in (int, float) or (type(multiplier) is float and not math.isfinite(multiplier)) or multiplier < 0:
        raise ValueError('Nieprawidlowy mnoznik EXP.')
    if amount <= _FLOAT_EXACT_INTEGER:
        return int(round(amount * multiplier))
    numerator, denominator = (multiplier, 1) if type(multiplier) is int else multiplier.as_integer_ratio()
    return _nearest_even(amount * numerator, denominator)


def scale_percent_xp_v10400(amount: int, bonus_percent: int) -> int:
    if type(amount) is not int or amount < 0 or type(bonus_percent) is not int or bonus_percent < 0:
        raise ValueError('EXP i procent musza byc nieujemnymi int.')
    if amount <= _FLOAT_EXACT_INTEGER:
        return int(round(amount * (1.0 + bonus_percent / 100.0)))
    return _nearest_even(amount * (100 + bonus_percent), 100)


def scale_bonus_percent_v10400(amount: int, bonus_percent: int | float) -> int:
    """Final guild/mentor bonus, exact for huge EXP, legacy rounding for small.

    Historically the combat pipeline used round(amount * (1 + pct / 100)).
    Float amount conversion silently rounds >2**53 or raises above ~1e308.
    Preserve that exact legacy behaviour for small amounts and perform
    decimal-rational arithmetic for large amounts without float(amount).
    """
    if type(amount) is not int or amount < 0:
        raise ValueError('EXP musi byc nieujemna liczba calkowita.')
    if type(bonus_percent) not in (int, float):
        raise TypeError('Procent musi byc liczba calkowita lub skonczonym float.')
    if bonus_percent < 0 or (type(bonus_percent) is float and not math.isfinite(bonus_percent)):
        raise ValueError('Procent musi byc nieujemny i skonczony.')
    if amount <= _FLOAT_EXACT_INTEGER:
        return max(0, int(round(amount * (1.0 + bonus_percent / 100.0))))
    # Decimal(str(float)) uses the intended decimal percent rather than the
    # binary approximation, and Fraction performs exact rational rounding.
    bonus = Fraction(Decimal(str(bonus_percent)))
    factor = 1 + bonus / 100
    return _nearest_even(amount * factor.numerator, factor.denominator)
