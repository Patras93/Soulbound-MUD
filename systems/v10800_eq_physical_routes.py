# -*- coding: utf-8 -*-
"""v108 preflight: physical EQ ownership, worn slots and storage cross-check.

READ ONLY. Call only on a disposable migration clone. The result contains one
aggregate count, never player identifiers, instance UUIDs or equipment names.
An empty or corrupted ledger never becomes deployment approval.
"""
from __future__ import annotations
from uuid import UUID, uuid5, NAMESPACE_URL
from systems.equipment_instances_v10600 import MAX_REHEARSAL_COPIES_PER_TEMPLATE


def physical_route_conflicts(conn, catalog, *, allowed_isolated_nongear_ids=frozenset()):
    """Count conflicting physical identities across all legacy routes.

    The earlier migration audit checked count and existence of EQ instances,
    but could overlook an instance simultaneously in a bag and storage, a
    foreign-owner slot, or a missing worn-shadow binding when called directly.
    Do not repair, allocate or reassign any physical instance here.
    """
    tables = {str(r[0]) for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    required = {'inventory', 'equipment', 'v106_item_instances',
                'v106_equipped_instances', 'v106_stored_instances'}
    if not required.issubset(tables):
        return 1
    gear = {str(item) for item, meta in catalog.items()
            if isinstance(meta, dict) and meta.get('type') in ('weapon', 'armor')}
    # Strict by default; explicit copy-only allowance for preserved inert legacy rows.
    permitted = set(allowed_isolated_nongear_ids)
    # v107 already performed the one-time deterministic migration. Subsequent
    # legitimate trade and rewards preserve UUIDs but change owner/quantity.
    # Checking UUID5 against the *current* owner and amount would falsely
    # invalidate those copies. Historical pre-cutover identity is tested by
    # the first migration; after cutover retain UUID type, unique IDs, stage,
    # ownership and cross-route quantity/slot checks. Never silently create.
    post_v107 = 'v107_eq_production_cutover' in tables
    conflicts = 0
    old_bag = {}
    for owner, item, qty in conn.execute('SELECT account_id,item_id,quantity FROM inventory'):
        item = str(item)
        if item not in gear:
            continue
        key = (owner, item)
        if key in old_bag or type(qty) is not int or qty < 0:
            conflicts += 1
        old_bag[key] = qty
    physical = {}
    expected_legacy_ids = {}
    for uid, owner, item, stage, origin in conn.execute(
            'SELECT instance_id,account_id,item_id,evolution_stage,origin FROM v106_item_instances'):
        item = str(item)
        if uid in permitted:
            meta = catalog.get(item)
            if (not isinstance(meta,dict) or item in gear or stage != 0 or
                type(owner) is not int or owner < 1):
                conflicts += 1
            # Any stored or equipped reference to omitted ID conflicts below.
            continue
        if (uid in physical or type(uid) is not str or not uid or
                type(owner) is not int or owner < 1 or item not in gear or
                type(stage) is not int or not 0 <= stage <= 10):
            conflicts += 1
        if post_v107:
            versions = {'legacy_unique': 5, 'manual_legacy_review': 5,
                        'v106_inventory': 4, 'v108_recovered_stage0': 4}
            try:
                valid_uuid = UUID(uid)
                if str(valid_uuid) != uid or valid_uuid.version != versions.get(origin):
                    conflicts += 1
            except (ValueError, TypeError, AttributeError):
                conflicts += 1
            if origin == 'v108_recovered_stage0' and stage != 0:
                conflicts += 1
        elif origin in ('legacy_unique', 'manual_legacy_review'):
            key = (owner, item)
            if key not in expected_legacy_ids:
                qty = old_bag.get(key, 0)
                if type(qty) is not int or not 1 <= qty <= MAX_REHEARSAL_COPIES_PER_TEMPLATE:
                    expected_legacy_ids[key] = set()
                    conflicts += 1
                else:
                    expected_legacy_ids[key] = {str(uuid5(NAMESPACE_URL,
                        f'soulbound:v106:legacy:{owner}:{item}' +
                        (f':copy:{ordinal}' if ordinal > 1 else '')))
                        for ordinal in range(1, qty + 1)}
            if uid not in expected_legacy_ids[key]:
                conflicts += 1
        physical[uid] = (owner, item)
    old_worn = {}
    for owner, slot, item in conn.execute('SELECT account_id,slot,item_id FROM equipment'):
        item = str(item)
        if item not in gear:
            continue
        key = (owner, str(slot))
        if key in old_worn:
            conflicts += 1
        old_worn[key] = item
    shadow_worn, used_uids = set(), set()
    for owner, slot, uid in conn.execute(
            'SELECT account_id,slot,instance_id FROM v106_equipped_instances'):
        key = (owner, str(slot))
        if key in shadow_worn or uid in used_uids:
            conflicts += 1
        shadow_worn.add(key)
        used_uids.add(uid)
        if physical.get(uid) != (owner, old_worn.get(key)) or key not in old_worn:
            conflicts += 1
    conflicts += len(old_worn.keys() ^ shadow_worn)
    stored, stored_uids = set(), set()
    for uid, owner in conn.execute(
            'SELECT instance_id,account_id FROM v106_stored_instances'):
        if uid in stored_uids:
            conflicts += 1
        stored_uids.add(uid)
        if physical.get(uid) is None or physical[uid][0] != owner or uid in used_uids:
            conflicts += 1
        stored.add(uid)
    # A physically stored copy must not simultaneously count in legacy bag
    # inventory. Conversely, all unstored physical copies must have a bag entry.
    bag_counts = {}
    for uid, key in physical.items():
        if uid not in stored:
            bag_counts[key] = bag_counts.get(key, 0) + 1
    for key in old_bag.keys() | bag_counts.keys():
        qty = old_bag.get(key, 0)
        if type(qty) is not int or qty != bag_counts.get(key, 0):
            conflicts += 1
    return conflicts
