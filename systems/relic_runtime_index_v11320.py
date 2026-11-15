# -*- coding: utf-8 -*-
"""Runtime Soul Weapon relic ID index; every ownership check remains live SQLite.

The 203k+ item templates used to be scanned on each HP/mana/skill call.
A conservative 0.5s refresh plus invalidation on registered ITEMS mutations
keeps runtime O(number of relics) rather than O(all world items).
"""
from __future__ import annotations
import time
from data import catalog_mutations

_CACHED = None


def relic_candidates_v11320(items):
    global _CACHED
    now = time.monotonic()
    stamp = getattr(catalog_mutations, 'ITEMS_GENERATION_V11320', 0)
    old = _CACHED
    if (old is not None and old[0] is items and old[1] == len(items)
            and old[2] == stamp and 0 <= now - old[3] < 0.5):
        ids = old[4]
    else:
        ids = tuple(item_id for item_id, item in items.items()
                    if isinstance(item, dict) and item.get('type') == 'soul_weapon_relic')
        _CACHED = (items, len(items), stamp, now, ids)
    # Retrieve the CURRENT dict rather than memoizing objects; same-ID
    # replacement or current-level/ownership must never use stale values.
    return ((item_id, item) for item_id in ids
            if isinstance((item := items.get(item_id)), dict)
            and item.get('type') == 'soul_weapon_relic')
