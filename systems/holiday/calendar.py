# -*- coding: utf-8 -*-
"""v111 draft: deterministic Polish holiday and fantasy season calendar, no I/O or SQLite."""
from __future__ import annotations
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from pathlib import Path


def _load_warsaw_timezone():
    # On Windows CPython can lack the system IANA timezone database entirely.
    # This project carries a *single* compiled IANA TZif as a deterministic
    # fallback.  Do not silently substitute the machine's current UTC offset:
    # it would give wrong holidays at midnight when DST changes.
    try:
        return ZoneInfo('Europe/Warsaw')
    except ZoneInfoNotFoundError:
        fallback = Path(__file__).resolve().parents[2] / 'data' / 'tzdb' / 'Europe_Warsaw.tzif'
        with fallback.open('rb') as source:
            return ZoneInfo.from_file(source, key='Europe/Warsaw')


WARSAW = _load_warsaw_timezone()
MONTHS = (
    ('Korony Zimy', 'Królewskie Przebudzenie', 'Lodowy Regent'),
    ('Serca i Słodkości', 'Festiwal Serc', 'Cukrowy Pożeracz'),
    ('Odrodzenie Wiosny', 'Wiosenne Odrodzenie', 'Złoty Zając'),
    ('Miesiąc Psot', 'Śmiech Goblinów', 'Arcypsotnik'),
    ('Turniej Bohaterów', 'Festiwal Bohaterów', 'Mistrz Turnieju'),
    ('Noc Kupały', 'Kwiat Paproci', 'Strażnik Przesilenia'),
    ('Letnie Morza', 'Piracka Przygoda', 'Kraken Przypływu'),
    ('Święto Plonów', 'Złote Żniwa', 'Żniwny Golem'),
    ('Tajemnice Jesieni', 'Skarby Starych Ruin', 'Strażnik Liści'),
    ('Halloween', 'Noc Umarłych', 'Król Dyni'),
    ('Święto Dusz', 'Wspomnienia Dusz', 'Prorok Mgły'),
    ('Zimowa Magia', 'Dary Zimy', 'Mroźny Smok'),
)
# Fixed date occasions, including popular observances; not a list of public holidays.
FIXED = (
    (1,1,'Nowy Rok'), (1,6,'Trzech Króli'), (2,14,'Walentynki'),
    (3,8,'Dzień Kobiet'), (3,21,'Pierwszy Dzień Wiosny'),
    (4,1,'Prima Aprilis'), (4,22,'Dzień Ziemi'),
    (5,1,'Święto Pracy'), (5,3,'Święto Konstytucji 3 Maja'), (5,26,'Dzień Matki'),
    (6,1,'Dzień Dziecka'), (6,21,'Początek Lata'), (6,23,'Noc Kupały'),
    (7,1,'Początek Letnich Wypraw'), (8,15,'Święto Wojska Polskiego'),
    (9,1,'Początek Jesiennych Wypraw'), (9,30,'Dzień Chłopaka'),
    (10,31,'Halloween'), (11,1,'Wszystkich Świętych'),
    (11,11,'Święto Niepodległości'), (11,30,'Andrzejki'),
    (12,6,'Mikołajki'), (12,24,'Wigilia'),
    (12,25,'Boże Narodzenie'), (12,26,'Drugi Dzień Świąt'),
    (12,31,'Sylwester'),
)

def easter(year:int)->date:
    """Gregorian computus (Meeus/Jones/Butcher), valid in Gregorian years."""
    if not 1583<=year<=4099:raise ValueError('year outside supported calendar')
    a=year%19;b=year//100;c=year%100;d=b//4;e=b%4
    f=(b+8)//25;g=(b-f+1)//3;h=(19*a+b-d-g+15)%30
    i=c//4;k=c%4;l=(32+2*e+2*i-h-k)%7
    m=(a+11*h+22*l)//451;month=(h+l-7*m+114)//31
    day=(h+l-7*m+114)%31+1
    return date(year,month,day)

def movable(year:int):
    holy=easter(year)
    return ((holy-timedelta(days=52),'Tłusty Czwartek'),
            (holy,'Wielkanoc'),(holy+timedelta(days=1),'Poniedziałek Wielkanocny'),
            (holy+timedelta(days=49),'Zielone Świątki'),
            (holy+timedelta(days=60),'Boże Ciało'))

def occasions(day:date):
    return tuple(name for month,num,name in FIXED if (day.month,day.day)==(month,num)) + tuple(
        name for when,name in movable(day.year) if when==day)

def local_day(now=None):
    if now is None:return datetime.now(WARSAW).date()
    if isinstance(now,datetime):
        if now.tzinfo is None:raise ValueError('naive datetime not allowed')
        return now.astimezone(WARSAW).date()
    if isinstance(now,date):return now
    raise TypeError('expected date or timezone-aware datetime')

def today(now=None):
    d=local_day(now);slug,title,boss=MONTHS[d.month-1]
    return {'date':d,'month':d.month,'region':slug,'title':title,'boss':boss,
            'occasions':occasions(d),'weekly_challenge':(d.isocalendar().week-1)%4+1,
            'daily_challenge':d.toordinal()%7+1}

def text_status(now=None):
    s=today(now);events=', '.join(s['occasions']) if s['occasions'] else 'brak święta dzisiaj'
    return (f'KALENDARZ V111: {s["date"]:%d.%m.%Y}; {s["title"]}. '
            f'Okazje: {events}. Expowisko: {s["region"]}; boss: {s["boss"]}. '
            f'Codzienne polowanie i tygodniowa próba bossa w tym expowisku. '
            'Komenda wyprawy: prowadź <nazwa expowiska>.')
