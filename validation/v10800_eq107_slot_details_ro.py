# -*- coding: utf-8 -*-
"""Aggregate-only diagnostic of *existing* v107 worn-gear links.

Reads a detached SQLite snapshot. Never exposes IDs, player names, template
names or slots; never creates or repairs physical copies.
"""
from __future__ import annotations
from collections import Counter


def summarize(conn, gear):
    if not gear:
        raise ValueError('Brak katalogu EQ')
    required = {'equipment', 'v106_equipped_instances', 'v106_item_instances',
                'v106_stored_instances'}
    existing = {str(r[0]) for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    if required - existing:
        raise ValueError('Niepelny schemat starego EQ')
    out = Counter()
    gear = set(map(str, gear))
    original = {}
    for aid, slot, iid in conn.execute('SELECT account_id,slot,item_id FROM equipment'):
        key = (aid, str(slot))
        if str(iid) not in gear:
            out['SLOT_NIEZNANY_LUB_NIESPRZETOWY_SZABLON'] += 1
            continue
        out['SLOTY_EQUIPMENT'] += 1
        if key in original:
            out['SLOTY_POWTORZONE_EQUIPMENT'] += 1
        original[key] = str(iid)
    physical = {}
    for uid, aid, iid in conn.execute(
            'SELECT instance_id,account_id,item_id FROM v106_item_instances'):
        physical[uid] = (aid, str(iid))
    stored = {r[0] for r in conn.execute('SELECT instance_id FROM v106_stored_instances')}
    shadow = {}
    used = set()
    for aid, slot, uid in conn.execute(
            'SELECT account_id,slot,instance_id FROM v106_equipped_instances'):
        key = (aid, str(slot))
        out['SLOTY_CIENIA'] += 1
        if key in shadow:
            out['SLOTY_POWTORZONE_CIENIA'] += 1
        shadow[key] = uid
        if uid in used:
            out['KOPIA_PRZYPISANA_WIELOKROTNIE'] += 1
        used.add(uid)
        if key not in original:
            out['CIEN_BEZ_EQUIPMENT'] += 1
        if uid not in physical:
            out['CIEN_BRAK_FIZYCZNEJ_KOPII'] += 1
            continue
        owner, item = physical[uid]
        if owner != aid:
            out['CIEN_INNY_WLASCICIEL'] += 1
        if item not in gear:
            out['CIEN_NIEZNANY_SZABLON'] += 1
        if key in original and item != original[key]:
            out['CIEN_INNY_PRZEDMIOT'] += 1
        if uid in stored:
            out['CIEN_W_MAGAZYNIE'] += 1
    for key in original.keys() - shadow.keys():
        out['EQUIPMENT_BEZ_CIENIA'] += 1
    # A compact summary of the independent deficits, even if the slot gate
    # has rejected the trial before inspecting physical quantities.
    try:
        from validation.v10800_v107_drift_details_ro import classify_snapshot
        catalog = {key: {'type': 'weapon'} for key in gear}
        c = classify_snapshot(conn, catalog)
        out['BRAKUJACE_KOPIE'] = c['deficit_copies']
        out['GRUPY_BRAKUJACYCH_KOPII'] = c['deficit_groups']
        out['NADMIAROWE_KOPIE'] = c['surplus_copies']
        out['NIEZGODNE_SLOTY_OGOLNIE'] = c['worn_slot_mismatches']
    except (ValueError, TypeError, KeyError):
        out['DIAGNOSTYKA_LICZNIKOW_NIEPELNA'] += 1
    # Always return the same fixed fields and only small integers.
    keys = (
        'SLOTY_EQUIPMENT', 'SLOTY_CIENIA',
        'EQUIPMENT_BEZ_CIENIA', 'CIEN_BEZ_EQUIPMENT',
        'CIEN_INNY_PRZEDMIOT', 'CIEN_INNY_WLASCICIEL',
        'CIEN_BRAK_FIZYCZNEJ_KOPII', 'CIEN_W_MAGAZYNIE',
        'CIEN_NIEZNANY_SZABLON', 'KOPIA_PRZYPISANA_WIELOKROTNIE',
        'SLOTY_POWTORZONE_EQUIPMENT', 'SLOTY_POWTORZONE_CIENIA',
        'SLOT_NIEZNANY_LUB_NIESPRZETOWY_SZABLON',
        'NIEZGODNE_SLOTY_OGOLNIE',
        'GRUPY_BRAKUJACYCH_KOPII', 'BRAKUJACE_KOPIE',
        'NADMIAROWE_KOPIE', 'DIAGNOSTYKA_LICZNIKOW_NIEPELNA'
    )
    return {k: int(out[k]) for k in keys}
