# -*- coding: utf-8 -*-
"""Readable real event schedule, derived from the exact live rotation."""
from datetime import datetime
from systems.world_events_v12812 import active_city_event_v12812

def event_calendar_lines(count=8, *, now=None):
    import time
    if type(count) is not int or not 1 <= count <= 24:
        raise ValueError('Liczba wydarzeń w podglądzie: 1–24.')
    start = time.time() if now is None else float(now)
    rows = ['HARMONOGRAM NAJAZDÓW PODZIEMI — czas lokalny serwera:']
    current = active_city_event_v12812(start)
    rows.append('Teraz: '+current['name']+'. Koniec: '+datetime.fromtimestamp(current['expires_at']).strftime('%Y-%m-%d %H:%M')+'.')
    next_start = current['expires_at']
    for index in range(1,count+1):
        ev = active_city_event_v12812(next_start + 1)
        rows.append(f'{index}. {datetime.fromtimestamp(next_start).strftime("%Y-%m-%d %H:%M")}: {ev["name"]}; koniec {datetime.fromtimestamp(ev["expires_at"]).strftime("%Y-%m-%d %H:%M")}.')
        next_start = ev['expires_at']
    return rows
