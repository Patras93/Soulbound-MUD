# -*- coding: utf-8 -*-
"""v108: independent event clock and seasonal calendar (Europe/Warsaw server local time).

No scheduled grants, no SQLite writes; actual claims require an explicit command.
Over Cap begins 15 minutes AFTER x2 EXP ENDS: :30..:45 every hour.
"""
from __future__ import annotations
from datetime import date, datetime
import math
import time

HOUR = 3600
OVER_CAP_START = 30 * 60
OVER_CAP_DURATION = 15 * 60


def overcap_event_state(now=None):
    seconds = time.time() if now is None else float(now)
    offset = seconds % HOUR
    active = OVER_CAP_START <= offset < OVER_CAP_START + OVER_CAP_DURATION
    remaining = max(0, int(math.ceil(OVER_CAP_START + OVER_CAP_DURATION - offset))) if active else 0
    start_in = max(0, int(math.ceil(OVER_CAP_START - offset if offset < OVER_CAP_START else HOUR + OVER_CAP_START - offset)))
    return dict(active=active, multiplier=2 if active else 1,
                remaining_seconds=remaining, next_start_seconds=start_in,
                duration_seconds=OVER_CAP_DURATION)


def advent_day(value=None):
    # Local calendar: on a correctly configured Windows host this is Polish
    # local time. Do not rely on optional tzdata / zoneinfo on Windows.
    if value is None:
        day = datetime.now().astimezone().date()
    elif isinstance(value, datetime):
        day = value.date()
    elif isinstance(value, date):
        day = value
    else:
        raise TypeError('advent_day expects date/datetime')
    if day.month == 12:
        return day.day
    if day.month == 1 and day.day == 1:
        return 32
    return 0


def advent_reward_silver(day_number):
    day_number = int(day_number)
    if not 1 <= day_number <= 32:
        raise ValueError('Gift day outside event')
    # Deliberately currency-only while v107 physical equipment ledger is being repaired.
    return 10000 if day_number == 32 else 1000 + day_number * 250
