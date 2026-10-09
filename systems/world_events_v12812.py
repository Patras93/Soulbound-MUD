# -*- coding: utf-8 -*-
"""Four authentic 3-hour rotating world invasions; no fake kill counters.

One timed boss is alive per server across the underground cities. Existing
combat, corpse and party rewards remain authoritative. This is not Generator Core.
"""
import time

EVENTS = (
  ('basalt','Najazd Nieumarłych', 'Widmowy Hetman Najazdu', 'physical', 'dark'),
  ('echo','Atak Pradawnego Smoka', 'Smok Szafirowej Burzy', 'magic', 'lightning'),
  ('star','Oblężenie Podziemnego Miasta', 'Żelazny Generał Oblężenia', 'physical', 'fire'),
  ('myth','Przebudzenie Starożytnego Bossa', 'Pradawny Król Otchłani', 'magic', 'shadow'),
)
EVENT_SECONDS = 3 * 60 * 60

def active_city_event_v12812(now=None):
    moment=time.time() if now is None else float(now)
    slot=int(moment // EVENT_SECONDS)
    slug,title,boss,style,element=EVENTS[slot % len(EVENTS)]
    return {'slug':slug,'name':title,'boss_name':boss,'style':style,
            'element':element,'slot':slot,'expires_at':(slot+1)*EVENT_SECONDS,
            'room_id':f'v12812_city_{slug}_gate',
            'template_id':f'v12812_event_{slug}'}
