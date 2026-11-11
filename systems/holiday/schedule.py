# -*- coding: utf-8 -*-
"""v111: deterministyczne okna świąt i wyzwań, bez skutków ubocznych.

Święta nie są zadaniami systemowymi. Przypomnienia i bonus EXP mogą użyć
jednej funkcji active_schedule zamiast osobnego timera lub usługi w tle.
"""
from __future__ import annotations
from datetime import date, datetime, time, timedelta
from systems.holiday.calendar import FIXED, MONTHS, WARSAW, local_day, movable
# Okno kończy się o północy po ostatnim dniu (koniec wyłączny).
# Dni ruchome wyliczamy corocznie według computus, nie na sztywno dla 2027.
WINDOW_DAYS = {
    'Nowy Rok': 2, 'Trzech Króli': 1, 'Walentynki': 3,
    'Tłusty Czwartek': 1, 'Wielkanoc': 2,
    'Noc Kupały': 2, 'Halloween': 3, 'Wszystkich Świętych': 1,
    'Andrzejki': 1, 'Mikołajki': 2, 'Boże Narodzenie': 3,
    'Sylwester': 1,
}


def _dates(year: int):
    for m, d, name in FIXED:
        if name == 'Sylwester':
            yield date(year, m, d), name
        elif name == 'Boże Narodzenie':
            yield date(year, m, d), name
        elif name not in ('Drugi Dzień Świąt',):
            yield date(year, m, d), name
    for day, name in movable(year):
        if name == 'Poniedziałek Wielkanocny':
            continue  # objęty dwudniowym okresem wielkanocnym
        yield day, name


def active_schedule(now=None):
    """Aktualny festiwal miesiąca oraz nieprzekraczające granic dat eventy.

    Przyjmuje date lub datetime z timezone; naive datetime jest odrzucany.
    Zwrot w pełni odtwarzalny i niezależny od zegara serwera poza argumentem.
    """
    day = local_day(now)
    month = MONTHS[day.month - 1]
    active = []
    for year in (day.year - 1, day.year):
        for start, label in _dates(year):
            end = start + timedelta(days=WINDOW_DAYS.get(label, 1))
            if start <= day < end:
                active.append((start, label, end))
    active.sort(key=lambda item: (item[0], item[1]))
    tomorrow = day + timedelta(days=1)
    month_end = date(tomorrow.year, tomorrow.month, 1) if tomorrow.month != day.month else None
    if month_end is None:
        if day.month == 12:
            month_end = date(day.year + 1, 1, 1)
        else:
            month_end = date(day.year, day.month + 1, 1)
    return {
        'day': day,
        'month': day.month,
        'zone': month[0],
        'festival': month[1],
        'boss': month[2],
        'month_ends_at': datetime.combine(month_end, time(), tzinfo=WARSAW),
        'active': tuple({'name': name,
                         'starts_at': datetime.combine(start, time(), tzinfo=WARSAW),
                         'ends_at': datetime.combine(end, time(), tzinfo=WARSAW)}
                        for start, name, end in active),
        'daily_key': day.isoformat(),
        'weekly_key': f'{day.isocalendar().year}-W{day.isocalendar().week:02d}',
    }


def seasonal_message(now=None):
    s = active_schedule(now)
    names = ', '.join(e['name'] for e in s['active']) or 'festiwal miesiąca'
    return (f'WYDARZENIA SWIATECZNE: {s["day"]:%d.%m.%Y}; {names}. '
            f'Expowisko: {s["zone"]}, boss: {s["boss"]}. '
            f'Wyzwanie dzienne {s["daily_key"]}, tygodniowe {s["weekly_key"]}.')
