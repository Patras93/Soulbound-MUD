# -*- coding: utf-8 -*-
"""Cztery wydarzenia naprzemiennie, po 6 godzin UTC; bez zadań w tle."""
from world.events.registry import EVENT_SPECS
from world.v11000_realms import EVENTS,REGIONS,prefix
SLOT_SECONDS=6*3600
REQUIRED_KILLS=9

def rotation(now):
    now=int(now)
    slot=now//SLOT_SECONDS
    slug,title,region_idx=EVENTS[slot%len(EVENTS)]
    region_prefix=prefix(REGIONS[region_idx][0])
    return dict(slot=slot,slug=slug,title=title,region=REGIONS[region_idx][1],
                region_prefix=region_prefix,boss='v11000_event_'+slug+'_boss',
                begins_at=slot*SLOT_SECONDS,expires_at=(slot+1)*SLOT_SECONDS,
                needed=REQUIRED_KILLS)
