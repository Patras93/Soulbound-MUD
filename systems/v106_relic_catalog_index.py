# -*- coding: utf-8 -*-
"""v106 staging: fast catalog index for Soul Weapon relic candidates.

Normal v105 path is untouched. This is ONLY an index of item template IDs;
individual ownership/level/current-selection queries still use real SQLite.
Temporary catalog changes are observed within one second (and immediately
when dictionary length changes). No ownership or equipment memoization.
"""
from __future__ import annotations
import os
import time

_CATALOG = None


def soul_weapon_relic_catalog_v106(items):
    global _CATALOG
    if os.environ.get('SOULBOUND_V106_STAGING') != '1':
        raise RuntimeError('Indeks relikwii v106 działa wyłącznie w staging.')
    now=time.monotonic()
    old=_CATALOG
    if (old is not None and old[0] is items and old[1]==len(items)
            and 0 <= now-old[2] < 1.0):
        return old[3]
    entries=tuple((item_id,item) for item_id,item in items.items()
                  if isinstance(item,dict) and item.get('type')=='soul_weapon_relic')
    _CATALOG=(items,len(items),time.monotonic(),entries)
    return entries
