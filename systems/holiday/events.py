# -*- coding: utf-8 -*-
"""Kalendarz bonusów v111: czysta logika, bez baz danych i skutków ubocznych."""
from __future__ import annotations
from datetime import date, timedelta
from systems.holiday.calendar import local_day, occasions, MONTHS

# Okazje pozostają specjalne także wtedy, gdy święto wypada blisko końca miesiąca.
MAJOR = {'Wielkanoc': 3, 'Boże Narodzenie': 3, 'Halloween': 3,
         'Nowy Rok': 2, 'Mikołajki': 2, 'Noc Kupały': 2,
         'Tłusty Czwartek': 2, 'Andrzejki': 2}

def festival(day=None):
    """Aktywne okazje oraz bonusy. Priorytet: duże święto > mniejsze > weekend."""
    d=local_day(day)
    named=occasions(d)
    # Festiwal trwa cały miesiąc; świąteczny finał ma wyższy mnożnik.
    factor=1.5 if d.weekday()>=5 else 1.25
    for name in named:
        factor=max(factor, 2.0 if MAJOR.get(name,0)>=3 else 1.5)
    return {'date':d,'month':d.month,'name':MONTHS[d.month-1][1],
            'occasions':named,'bonus':factor,
            'daily':d.toordinal()%7+1,'weekly':(d.isocalendar().week-1)%4+1}

def holiday_reward(mob_id:str, value:int, day=None, *,exact=False):
    """Bonus tylko dla mobów świątecznego ekspowiska AKTUALNEGO miesiąca.

    Nie zmienia nagród w starych lokacjach ani źródłowych exact XP.
    Wynik zabezpieczony przed przekroczeniem bezpiecznego limitu.
    """
    amount=max(0,int(value))
    if exact or not isinstance(mob_id,str):return amount
    state=festival(day)
    prefix=f'v11100_holiday_{state["month"]:02d}_'
    if not mob_id.startswith(prefix):return amount
    return min(2**63-1, int(amount*state['bonus']))

def calendar_text(day=None):
    state=festival(day)
    from systems.holiday.schedule import active_schedule
    schedule=active_schedule(state['date'])
    today=', '.join(event['name'] for event in schedule['active']) or 'festiwal miesiąca'
    return (f'SWIETA V111: {state["date"]:%d.%m.%Y}, {state["name"]}. '
            f'Dzisiaj: {today}. Bonus EXP w expowisku miesiąca: '
            f'x{state["bonus"]:.2f}. Codzienna próba {state["daily"]}/7, '
            f'tygodniowe wyzwanie {state["weekly"]}/4. '
            'W pozostałych expowiskach nagrody standardowe. '
            'Rejestr wyzwań: dziennie 5 zwycięstw, tygodniowo 1 boss; '
            'Nagrody za próby przyznawane automatycznie po ukończeniu; '
            'prezenty codzienne nadal obsługuje system v109.')
