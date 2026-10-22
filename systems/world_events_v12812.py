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
    from systems.live_olc22_state import WORLD_OVERRIDES
    seconds=int(WORLD_OVERRIDES.get('event_cycle_minutes',180))*60
    seconds=max(1800,min(43200,seconds))
    # Offset is measured from the old UTC epoch boundary. Zero preserves v22.
    offset=int(WORLD_OVERRIDES.get('event_offset_minutes',0))*60
    slot=int((moment-offset) // seconds)
    by_slug={row[0]:row for row in EVENTS}
    order=WORLD_OVERRIDES.get('event_order') or [row[0] for row in EVENTS]
    if not isinstance(order,list) or len(order)!=len(EVENTS) or set(order)!=set(by_slug):
        order=[row[0] for row in EVENTS]
    from systems.live_olc26_world import event_catalog
    custom=event_catalog()
    # Keep original order (and optional older OLC rotation), append authored events.
    # Each new definition has its own mob template but reuses an existing arena.
    from systems.live_olc28_expansion import event_weight
    from systems.live_olc32_finale import event_allowed
    order=list(order)+[slug for slug in sorted(custom) if event_allowed(slug,moment)
                       for _ in range(event_weight(slug))]
    slug=order[slot % len(order)]
    if slug in custom:
        data=custom[slug]
        return {'slug':slug,'name':data['name'],'boss_name':data['boss_name'],
                'style':data['style'],'element':data['element'], 'slot':slot,
                'expires_at':(slot+1)*seconds+offset,
                'room_id':__import__('systems.live_olc29_creation',fromlist=['authored_arena']).authored_arena(slug,f"v12812_city_{data['city']}_gate"),
                'template_id':'v26_event_'+slug}
    slug,title,boss,style,element=by_slug[slug]
    from systems.live_olc24_revolution import ACTIVE
    edited = ACTIVE['events'].get(slug,{})
    title=edited.get('title',title)
    boss=edited.get('boss_name',boss)
    style=edited.get('style',style)
    element=edited.get('element',element)
    return {'slug':slug,'name':title,'boss_name':boss,'style':style,
            'element':element,'slot':slot,'expires_at':(slot+1)*seconds+offset,
            'room_id':f'v12812_city_{slug}_gate',
            'template_id':f'v12812_event_{slug}'}
