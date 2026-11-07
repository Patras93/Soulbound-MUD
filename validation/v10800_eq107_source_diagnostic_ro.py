# -*- coding: utf-8 -*-
"""Anonymous, read-only comparison of detached current v107 and pre-v107 snapshots.

Heuristic clues only. Does NOT resolve slot ownership or authorize repair.
Print only fixed aggregate integers; never identify accounts, items, slots or UIDs.
This module never connects to source databases itself.
"""
from __future__ import annotations
from collections import Counter, defaultdict


KEYS = (
    'SLOTY_ROZNE_SZABLONY',
    'SLOTY_W_BACKUPIE_JAK_EQUIPMENT',
    'SLOTY_W_BACKUPIE_JAK_CIEN',
    'SLOTY_W_BACKUPIE_INNE_NIZ_OBIE_STRONY',
    'SLOTY_NIEOBECNE_W_BACKUPIE',
    'SLOTY_BRAK_WOLNEJ_ZGODNEJ_KOPII',
    'SLOTY_JEDNA_WOLNA_ZGODNA_KOPIA_BEZ_EWOLUCJI',
    'SLOTY_JEDNA_WOLNA_ZGODNA_KOPIA_Z_EWOLUCJA',
    'SLOTY_WIELE_WOLNYCH_ZGODNYCH_KOPII',
    'BRAKI_SZTUK_POKRYTE_PRZYROSTEM_OD_BACKUPU',
    'BRAKI_SZTUK_BEZ_POKRYCIA_W_PRZYROSCIE',
    'BRAKI_GRUPY_BEZ_WYSTARCZAJACEGO_PRZYROSTU',
    'BRAKI_GRUPY_Z_ZALOZONYM_SZABLONEM',
    'BRAKI_GRUPY_Z_ROZWINIETA_KOPIA',
    'BRAKI_GRUPY_Z_KOPIA_W_MAGAZYNIE',
    'BRAKI_GRUPY_WYMAGAJACE_HISTORII',
)


def compare_snapshots(current, previous, gear):
    """Compare only isolated snapshots. Counts are clues, never a repair plan."""
    if not gear:
        raise ValueError('Pusty katalog EQ')
    gear = {str(x) for x in gear}
    before_tables = {str(r[0]) for r in previous.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    if not {'equipment', 'inventory'} <= before_tables:
        raise ValueError('Oryginalny backup nie zawiera equipment/inventory')

    before_slots = {(aid, str(slot)): str(item) for aid, slot, item in previous.execute(
        'SELECT account_id,slot,item_id FROM equipment')}
    before_bag = {(aid, str(item)): int(qty) for aid, item, qty in previous.execute(
        'SELECT account_id,item_id,quantity FROM inventory')
        if str(item) in gear and type(qty) is int and qty >= 0}

    worn = {(aid, str(slot)): str(item) for aid, slot, item in current.execute(
        'SELECT account_id,slot,item_id FROM equipment') if str(item) in gear}
    physical = {}
    quantity = Counter()
    free = defaultdict(list)
    for uid, aid, item, stage in current.execute(
        'SELECT instance_id,account_id,item_id,evolution_stage FROM v106_item_instances'):
        physical[uid] = (aid, str(item), stage)
    active_ids = {row[0] for row in current.execute('SELECT instance_id FROM v106_equipped_instances')}
    stored_ids = {row[0] for row in current.execute('SELECT instance_id FROM v106_stored_instances')}
    for uid, (aid, item, stage) in physical.items():
        if item not in gear:
            continue
        if uid not in stored_ids:
            quantity[(aid, item)] += 1
        if uid not in stored_ids and uid not in active_ids:
            free[(aid, item)].append(stage)

    out = Counter()
    for aid, slot, uid in current.execute(
        'SELECT account_id,slot,instance_id FROM v106_equipped_instances'):
        key = (aid, str(slot))
        if key not in worn or uid not in physical:
            continue
        shadow_item = physical[uid][1]
        if worn[key] == shadow_item:
            continue
        out['SLOTY_ROZNE_SZABLONY'] += 1
        baseline = before_slots.get(key)
        if baseline is None:
            out['SLOTY_NIEOBECNE_W_BACKUPIE'] += 1
        elif baseline == worn[key]:
            out['SLOTY_W_BACKUPIE_JAK_EQUIPMENT'] += 1
        elif baseline == shadow_item:
            out['SLOTY_W_BACKUPIE_JAK_CIEN'] += 1
        else:
            out['SLOTY_W_BACKUPIE_INNE_NIZ_OBIE_STRONY'] += 1
        candidates = free.get((aid, worn[key]), ())
        if not candidates:
            out['SLOTY_BRAK_WOLNEJ_ZGODNEJ_KOPII'] += 1
        elif len(candidates) == 1:
            if type(candidates[0]) is int and candidates[0] == 0:
                out['SLOTY_JEDNA_WOLNA_ZGODNA_KOPIA_BEZ_EWOLUCJI'] += 1
            else:
                out['SLOTY_JEDNA_WOLNA_ZGODNA_KOPIA_Z_EWOLUCJA'] += 1
        else:
            out['SLOTY_WIELE_WOLNYCH_ZGODNYCH_KOPII'] += 1

    bag = Counter()
    for aid, item, count in current.execute('SELECT account_id,item_id,quantity FROM inventory'):
        if str(item) in gear and type(count) is int and count >= 0:
            bag[(aid, str(item))] += count
    worn_values = {(aid, item) for (aid, slot), item in worn.items()}
    evolved = {(aid, item) for _uid, (aid, item, stage) in physical.items()
               if type(stage) is int and stage > 0}
    banked = {(physical[uid][0], physical[uid][1]) for uid in stored_ids if uid in physical}

    for key in bag.keys() | quantity.keys():
        deficit = bag.get(key, 0) - quantity.get(key, 0)
        if deficit <= 0:
            continue
        growth = max(0, bag[key] - before_bag.get(key, 0))
        out['BRAKI_SZTUK_POKRYTE_PRZYROSTEM_OD_BACKUPU'] += min(deficit, growth)
        out['BRAKI_SZTUK_BEZ_POKRYCIA_W_PRZYROSCIE'] += max(0, deficit - growth)
        if growth < deficit:
            out['BRAKI_GRUPY_BEZ_WYSTARCZAJACEGO_PRZYROSTU'] += 1
        if key in worn_values:
            out['BRAKI_GRUPY_Z_ZALOZONYM_SZABLONEM'] += 1
        if key in evolved:
            out['BRAKI_GRUPY_Z_ROZWINIETA_KOPIA'] += 1
        if key in banked:
            out['BRAKI_GRUPY_Z_KOPIA_W_MAGAZYNIE'] += 1
        if growth < deficit or key in worn_values or key in evolved or key in banked:
            out['BRAKI_GRUPY_WYMAGAJACE_HISTORII'] += 1
    return {k: int(out[k]) for k in KEYS}
