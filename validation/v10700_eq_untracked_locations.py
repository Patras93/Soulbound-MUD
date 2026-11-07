# -*- coding: utf-8 -*-
"""Read-only audit of v105 locations not represented by the v106 per-copy ledger.

No player names, item identifiers, mail contents, or account IDs are logged.
The results are NECESSARY checks, never deployment authorization.
"""
from __future__ import annotations

import json
from collections import Counter

MODIFIER_TABLES = (
    'equipment_reforges', 'equipment_upgrades_v03042',
    'equipment_runes_v0925', 'equipment_socket_bonus_v03114',
    'tech_set_upgrades_v0320',
)
# Dynamic craft/deep loot can be physical even if not in the static ITEMS map.
DYNAMIC_PREFIXES = ('craftq_', 'deepq_', 'endlessq_')


def _tables(conn):
    return {str(r[0]) for r in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}


def _columns(conn, table):
    # `table` comes ONLY from a fixed allowlist or known sqlite_master names.
    return {str(r[1]) for r in conn.execute('PRAGMA table_info("'+table+'")')}


def _qty(qty):
    # SQLite can also contain malformed TEXT or REAL despite a declared INTEGER.
    if type(qty) is not int or qty <= 0 or qty > (2**63 - 1):
        raise ValueError('invalid quantity')
    return qty


def _house(conn,table,column,gear,summary):
    if table not in _tables(conn):
        return
    for (blob,) in conn.execute('SELECT "'+column+'" FROM "'+table+'"'):
        try:
            box=json.loads(blob or '{}')
            if not isinstance(box,dict):
                raise ValueError('not a mapping')
            for iid,qty in box.items():
                iid=str(iid)
                if iid not in gear and not iid.startswith(DYNAMIC_PREFIXES):
                    continue
                summary['housing_gear_units']+=_qty(qty)
                if iid not in gear:
                    summary['unresolved_dynamic_units']+=qty
        except (ValueError, TypeError, OverflowError):
            summary['housing_json_errors']+=1


def audit_untracked(conn,catalog):
    """Conservative aggregate checks over ALL legacy equipment storage routes.

    If a legacy route can hold a gear item but has no v106 physical instance
    mapping, it must be reconciled/converted explicitly before v107 release.
    """
    tables=_tables(conn)
    gear={str(k) for k,v in catalog.items() if isinstance(v,dict)
          and v.get('type') in ('armor','weapon')}
    result=Counter({
        'pending_mail_gear_units':0,
        'pending_mail_malformed':0,
        'housing_gear_units':0,
        'housing_json_errors':0,
        'ambiguous_modifiers':0,
        'orphaned_modifier_rows':0,
        'unresolved_dynamic_units':0,
    })
    inventory={}
    if 'inventory' in tables:
        for account,iid,qty in conn.execute(
                'SELECT account_id,item_id,quantity FROM inventory'):
            iid=str(iid)
            if iid in gear:
                inventory[(int(account),iid)]=qty
            elif iid.startswith(DYNAMIC_PREFIXES):
                try:result['unresolved_dynamic_units']+=_qty(qty)
                except ValueError:result['unresolved_dynamic_units']+=1
    for table in ('bank_items','profession_storage'):
        if table in tables:
            for iid,qty in conn.execute('SELECT item_id,quantity FROM "'+table+'"'):
                if str(iid).startswith(DYNAMIC_PREFIXES) and str(iid) not in gear:
                    try:result['unresolved_dynamic_units']+=_qty(qty)
                    except ValueError:result['unresolved_dynamic_units']+=1
    # Previous audit counted only inventory/bank/profession_storage, but house
    # storage uses JSON and has no physical-instance escrow at all.
    for table,column in (('player_housing_v03051','storage_json'),
                         ('housing_rooms_v03052','chest_json')):
        if table in tables and column in _columns(conn,table):
            _house(conn,table,column,gear,result)
    if 'player_mail_v03051' in tables:
        columns=_columns(conn,'player_mail_v03051')
        required={'attachment_kind','attachment_item_id','attachment_item_qty',
                  'attachment_claimed'}
        if not required.issubset(columns):
            result['pending_mail_malformed']+=1
        else:
            for iid,qty in conn.execute('''SELECT attachment_item_id,attachment_item_qty
                FROM player_mail_v03051 WHERE COALESCE(attachment_claimed,0) != 1
                   AND attachment_kind='item' '''):
                iid=str(iid)
                if iid not in gear and not iid.startswith(DYNAMIC_PREFIXES):
                    continue
                try:
                    result['pending_mail_gear_units']+=_qty(qty)
                    if iid not in gear:
                        result['unresolved_dynamic_units']+=qty
                except ValueError:
                    result['pending_mail_malformed']+=1
    for table in MODIFIER_TABLES:
        if table not in tables:
            continue
        if not {'account_id','item_id'}.issubset(_columns(conn,table)):
            result['ambiguous_modifiers']+=1
            continue
        for account,iid in conn.execute(
                'SELECT DISTINCT account_id,item_id FROM "'+table+'"'):
            iid=str(iid)
            if iid not in gear:
                continue
            quantity=inventory.get((int(account),iid),0)
            if not isinstance(quantity,int) or quantity < 1:
                result['orphaned_modifier_rows']+=1
            elif quantity>1:
                result['ambiguous_modifiers']+=1
    return dict(result)
