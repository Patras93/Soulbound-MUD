# -*- coding: utf-8 -*-
"""Recreate known game-generated item definitions in a disposable EQ rehearsal.

This is a catalog-only operation: no SQL mutation, no equipment reallocation.
Unknown generated IDs remain unknown and block the existing safety gates.
"""
from __future__ import annotations


def restore_known_crafted_equipment(conn, catalog):
    """Resolve only IDs already present in the existing SQLite snapshot.

    The engine's own recipe decoder regenerates the exact item, including
    base defense, bonuses and slot. It is not inferred from an ID prefix.
    """
    from systems.crafting_quality import ensure_crafting_quality_variant_v0332
    count = 0
    sources = ('inventory', 'equipment', 'v106_item_instances')
    for source in sources:
        for (iid,) in conn.execute('SELECT DISTINCT item_id FROM "' + source + '"'):
            iid = str(iid)
            if not iid.startswith('craftq_') or iid in catalog:
                continue
            item = ensure_crafting_quality_variant_v0332(iid)
            if not (isinstance(item, dict) and item.get('type') in ('weapon', 'armor')
                    and isinstance(item.get('slot'), str) and item.get('slot')):
                continue
            # Game's ITEMS catalog must be the exact shared registry. Never
            # manufacture a replacement or trust a merely plausible name.
            if catalog.get(iid) is not item:
                raise ValueError('DYNAMIC_CATALOG_REGISTRY_NOT_SHARED')
            count += 1
    return count
