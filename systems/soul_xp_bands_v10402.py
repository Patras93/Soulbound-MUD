# -*- coding: utf-8 -*-
"""Runtime Soul Level XP requirement bands for v104.00.2.

Default 100 percent is byte-for-byte compatible with the previously authored
requirements. Admin Live publishes only one validated, server-wide band table,
never individual player progression or historical Soul Tier unlock gates.
"""

BANDS = {
    'v10400_soul_501_1000': (501, 1000),
    'v10400_soul_1001_5000': (1001, 5000),
    'v10400_soul_5001_10000': (5001, 10000),
}
MIN_PERCENT = 25
MAX_PERCENT = 400
_rates = {name: 100 for name in BANDS}


def current_percent(identifier):
    return _rates[identifier]


def percent_for_level(level):
    try:
        level = int(level)
    except (ValueError, TypeError, OverflowError):
        return 100
    for name, (low, high) in BANDS.items():
        if low <= level <= high:
            return _rates[name]
    return 100


def update_rates(new):
    if not isinstance(new, dict) or set(new) != set(BANDS):
        raise ValueError('Niezgodne pasma Soul Level EXP')
    if any(type(value) is not int or not MIN_PERCENT <= value <= MAX_PERCENT
           for value in new.values()):
        raise ValueError('Nieprawidłowy procent progu EXP Soul Level')
    _rates.clear()
    _rates.update(new)


def requirement(level, authored):
    value = max(1, int(authored))
    return max(1, (value * percent_for_level(level) + 50) // 100)
