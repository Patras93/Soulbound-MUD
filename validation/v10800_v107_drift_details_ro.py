# -*- coding: utf-8 -*-
"""Aggregate-only read-only classification of an *existing* v107 EQ ledger.

No migration, reconciliation, SQL writes, item identifiers or account IDs are
returned.  This is NOT a repair proposal and does not authorize any deployment.
The caller supplies an already detached WAL-consistent SQLite snapshot.
"""
from __future__ import annotations
from collections import Counter, defaultdict


def classify_snapshot(conn, catalog):
    """Inspect legacy bag/physical-copy mismatches without mutating `conn`.

    All counters are integers. Treat unknown templates and missing schema as
    diagnostic limitations, not as permission to create physical items.
    """
    if not isinstance(catalog, dict) or not catalog:
        raise ValueError('Brak katalogu przedmiotów')
    required = {'inventory', 'equipment', 'v106_item_instances',
                'v106_stored_instances', 'v106_equipped_instances'}
    present = {str(row[0]) for row in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    if not required.issubset(present):
        raise ValueError('Niekompletny schemat EQ v107')
    gear = {str(iid) for iid, meta in catalog.items()
            if isinstance(meta, dict) and meta.get('type') in ('armor', 'weapon')}
    if not gear:
        raise ValueError('Katalog nie zawiera sprzętu')

    out = Counter()
    bag = defaultdict(int)
    for aid, item, qty in conn.execute('SELECT account_id,item_id,quantity FROM inventory'):
        item = str(item)
        if item not in gear:
            continue
        out['bag_gear_rows'] += 1
        if type(aid) is not int or aid < 1 or type(qty) is not int or qty < 0:
            out['invalid_bag_rows'] += 1
            continue
        bag[(aid, item)] += qty

    stored_rows = tuple(conn.execute('SELECT instance_id,account_id FROM v106_stored_instances'))
    stored_ids = {uid for uid, _ in stored_rows}
    if len(stored_rows) != len(stored_ids):
        out['duplicate_stored_ids'] = len(stored_rows) - len(stored_ids)
    physical = defaultdict(int)
    evolved = Counter()
    ids = set()
    owner_by_uid = {}
    item_by_uid = {}
    for uid, aid, iid, stage, origin in conn.execute(
            'SELECT instance_id,account_id,item_id,evolution_stage,origin FROM v106_item_instances'):
        out['physical_instances'] += 1
        if uid in ids:
            out['duplicate_physical_ids'] += 1
        ids.add(uid)
        owner_by_uid[uid] = aid
        item_by_uid[uid] = str(iid)
        if (not isinstance(uid, str) or not uid or type(aid) is not int or aid < 1 or
                type(stage) is not int or stage < 0 or stage > 10 or
                not isinstance(origin, str) or not origin):
            out['invalid_physical_rows'] += 1
        if str(iid) not in gear:
            out['unrecognized_physical_templates'] += 1
            continue
        if uid not in stored_ids:
            physical[(aid, str(iid))] += 1
        if type(stage) is int and stage > 0:
            evolved[(aid, str(iid))] += 1

    for uid, owner in stored_rows:
        if uid not in ids:
            out['orphan_stored_ids'] += 1
        elif owner_by_uid[uid] != owner:
            out['stored_owner_conflicts'] += 1

    for key in set(bag) | set(physical):
        difference = bag.get(key, 0) - physical.get(key, 0)
        if difference > 0:
            out['deficit_groups'] += 1
            out['deficit_copies'] += difference
            if evolved[key]:
                out['deficit_groups_with_evolved_copies'] += 1
        elif difference < 0:
            out['surplus_groups'] += 1
            out['surplus_copies'] += -difference

    # Compare actual worn (account,slot,template) with v106 instance shadow.
    worn = Counter((aid, str(slot), str(item)) for aid, slot, item in conn.execute(
        'SELECT account_id,slot,item_id FROM equipment') if str(item) in gear)
    shadow = Counter()
    for aid, slot, uid in conn.execute(
        'SELECT account_id,slot,instance_id FROM v106_equipped_instances'):
        if uid not in ids:
            out['orphan_worn_ids'] += 1
            continue
        if owner_by_uid[uid] != aid:
            out['worn_owner_conflicts'] += 1
        item = item_by_uid[uid]
        if item in gear:
            shadow[(aid, str(slot), item)] += 1
    out['worn_slot_mismatches'] = sum((worn - shadow).values()) + sum((shadow - worn).values())
    out['stored_instances'] = len(stored_rows)
    out['worn_shadow_slots'] = sum(shadow.values())
    return {name: int(out[name]) for name in (
        'physical_instances', 'bag_gear_rows', 'stored_instances', 'worn_shadow_slots',
        'deficit_groups', 'deficit_copies', 'surplus_groups', 'surplus_copies',
        'deficit_groups_with_evolved_copies', 'worn_slot_mismatches',
        'unrecognized_physical_templates', 'invalid_bag_rows',
        'invalid_physical_rows', 'duplicate_physical_ids',
        'duplicate_stored_ids', 'orphan_stored_ids', 'stored_owner_conflicts',
        'orphan_worn_ids', 'worn_owner_conflicts')}


def safe_summary(out):
    """Only fixed English identifiers and decimal counters; no player data."""
    keys = ('deficit_groups', 'deficit_copies', 'surplus_groups', 'surplus_copies',
            'worn_slot_mismatches', 'invalid_physical_rows',
            'unrecognized_physical_templates')
    return '; '.join(f'{key}={int(out[key])}' for key in keys)
