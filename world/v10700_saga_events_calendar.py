# -*- coding: utf-8 -*-
"""v107 hourly Chaos-hunt calendar, deterministic and restart-safe.

The 60 existing real kill quests rotate in six nonoverlapping groups. There
is no background writer, task worker or database schedule to lose on restart.
Accepted quests remain valid after their offer window; only *new* acceptance
is window-gated. Time is UTC Unix time, independent of local DST and reboot.
"""
from __future__ import annotations
import re
import time

WINDOW_SECONDS = 3600
TOTAL_EVENTS = 60
ACTIVE_EACH_WINDOW = 10
_PATTERN = re.compile(r'^v10700_saga_events_(\d{3})$')


def _time(when=None):
    when = time.time() if when is None else when
    if isinstance(when,bool) or not isinstance(when,(int,float)):
        raise TypeError('Nieprawidłowy czas wydarzenia')
    if not -10**12 <= when <= 10**12:
        raise ValueError('Nieprawidłowy zakres czasu')
    return int(when)


def slot(when=None):
    return _time(when)//WINDOW_SECONDS


def active_quest_ids(when=None):
    index = slot(when)%6
    return tuple(f'v10700_saga_events_{num:03d}'
                 for num in range(1,TOTAL_EVENTS+1)
                 if (num-1)%6==index)


def is_event(quest_id):
    match = _PATTERN.fullmatch(str(quest_id or ''))
    return match is not None and 1<=int(match.group(1))<=TOTAL_EVENTS


def is_active(quest_id, when=None):
    if not is_event(quest_id):
        return False
    return (int(str(quest_id)[-3:])-1)%6==slot(when)%6


def until_next_window(when=None):
    at=_time(when)
    return WINDOW_SECONDS-(at%WINDOW_SECONDS)


def until_active(quest_id,when=None):
    if not is_event(quest_id):
        raise ValueError('To nie jest wydarzenie Chaosu v107.')
    current=slot(when)
    group=(int(str(quest_id)[-3:])-1)%6
    delta=(group-current%6)%6
    if delta==0:return 0
    return until_next_window(when)+(delta-1)*WINDOW_SECONDS
