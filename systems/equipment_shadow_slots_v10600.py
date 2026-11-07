# -*- coding: utf-8 -*-
"""v106 SHADOW ONLY: atomic association of concrete gear instances with worn slots.

No live migration, no gameplay authorization. `prepare_on_disposable_copy()`
works on an isolated DB clone only. All normal v105 routes remain unchanged.
Some transfers, bank, storage and mail methods have staging-only adapters;
crafting and remaining direct-SQL operations still require integration.
"""
from __future__ import annotations
import sqlite3
from systems.equipment_instances_v10600 import apply_to_explicit_test_copy


def _require_copy(confirmed):
    if confirmed is not True:
        raise PermissionError('v106 EQ: tylko potwierdzona, tymczasowa kopia SQLite.')


def _equipment_catalog(catalog):
    return {str(iid) for iid, item in catalog.items()
            if isinstance(item,dict) and item.get('type') in ('armor','weapon')}


def _schema(conn):
    conn.execute('''CREATE TABLE IF NOT EXISTS v106_equipped_instances (
        account_id INTEGER NOT NULL, slot TEXT NOT NULL,
        instance_id TEXT NOT NULL UNIQUE,
        PRIMARY KEY(account_id,slot),
        FOREIGN KEY(instance_id) REFERENCES v106_item_instances(instance_id)
    )''')
    conn.execute('''CREATE TABLE IF NOT EXISTS v106_stored_instances (
        instance_id TEXT PRIMARY KEY, account_id INTEGER NOT NULL,
        storage_kind TEXT NOT NULL, container TEXT NOT NULL DEFAULT '',
        FOREIGN KEY(instance_id) REFERENCES v106_item_instances(instance_id)
    )''')


def _check_account(conn,aid,catalog):
    """Fail closed if a legacy slot was changed outside the shadow adapter."""
    def is_gear(item_id):
        entry=catalog.get(str(item_id))
        return isinstance(entry,dict) and entry.get('type') in ('armor','weapon')
    eq={(str(slot),str(iid)) for slot,iid in conn.execute(
        'SELECT slot,item_id FROM equipment WHERE account_id=?',(aid,))
        if is_gear(iid)}
    shadow={}
    for slot,instance,iid,owner in conn.execute('''
       SELECT s.slot,s.instance_id,i.item_id,i.account_id
       FROM v106_equipped_instances s
       LEFT JOIN v106_item_instances i ON s.instance_id=i.instance_id
       WHERE s.account_id=?''',(aid,)):
        if owner is None or int(owner)!=int(aid) or not is_gear(iid):
            raise RuntimeError('v106 EQ: cień wskazuje cudzą lub usuniętą kopię')
        if str(slot) in shadow:
            raise RuntimeError('v106 EQ: zduplikowany slot')
        shadow[str(slot)]=str(iid)
    if eq!={(slot,item) for slot,item in shadow.items()}:
        raise RuntimeError('v106 EQ: wyposażenie i kopie slotów nie są zgodne')
    inventory={str(iid):qty for iid,qty in conn.execute(
        'SELECT item_id,quantity FROM inventory WHERE account_id=?',(aid,))
        if is_gear(iid)}
    instances={}
    for iid, in conn.execute('''SELECT i.item_id FROM v106_item_instances i
             LEFT JOIN v106_stored_instances st ON st.instance_id=i.instance_id
             WHERE i.account_id=? AND st.instance_id IS NULL''',(aid,)):

        if is_gear(iid):
            instances[str(iid)]=instances.get(str(iid),0)+1
    # A banked physical copy cannot also be equipped or owned by another account.
    for uid,stored_owner,actual_owner in conn.execute('''
        SELECT st.instance_id,st.account_id,i.account_id
        FROM v106_stored_instances st LEFT JOIN v106_item_instances i
        ON st.instance_id=i.instance_id WHERE st.account_id=?''',(aid,)):
        if actual_owner is None or int(actual_owner)!=int(stored_owner):
            raise RuntimeError('v106 EQ: magazyn wskazuje cudzą lub brakującą kopię')
        if conn.execute('SELECT 1 FROM v106_equipped_instances WHERE instance_id=?',
                        (uid,)).fetchone():
            raise RuntimeError('v106 EQ: założona sztuka znajduje się w magazynie')
    for iid in set(inventory)|set(instances)|{item for _,item in eq}:
        count=inventory.get(iid,0)
        if type(count)!=int or count<0:
            raise RuntimeError('v106 EQ: błędna liczba przedmiotów')
        # Never auto-repair an untracked sell/drop/mail/bank operation.
        if count!=instances.get(iid,0):
            raise RuntimeError('v106 EQ: liczba kopii nie zgadza się z inventory')
        worn=sum(item==iid for _,item in eq)
        if worn>count:
            raise RuntimeError('v106 EQ: więcej założonych kopii niż posiadanych')


def prepare_on_disposable_copy(conn,catalog,*,confirm_disposable_copy=False):
    """Idempotent bind of all pre-existing armor/weapon slots on an isolated DB.

    Ambiguous historical stages are not assigned to any one copy. If a worn
    item has no unambiguous physical instance, the entire binding rolls back.
    """
    _require_copy(confirm_disposable_copy)
    # Any migration failure must not leave partially bound slots.
    outer=conn.in_transaction
    conn.execute('SAVEPOINT sb106_prepare_slots')
    try:
        migrated=apply_to_explicit_test_copy(conn,catalog,confirm_disposable_copy=True)
        _schema(conn)
        known=_equipment_catalog(catalog)
        done=0
        rows=conn.execute('SELECT account_id,slot,item_id FROM equipment '
                          'ORDER BY account_id,slot').fetchall()
        for aid,slot,iid in rows:
            if str(iid) not in known:continue
            aid=int(aid);slot=str(slot);iid=str(iid)
            existing=conn.execute('SELECT instance_id FROM v106_equipped_instances '
                'WHERE account_id=? AND slot=?',(aid,slot)).fetchone()
            if existing:
                owned=conn.execute('SELECT account_id,item_id FROM v106_item_instances '
                       'WHERE instance_id=?',(existing[0],)).fetchone()
                if owned is None or tuple(owned)!=(aid,iid):
                    raise RuntimeError('v106 EQ: rozbieżność istniejącego przypisania do slotu')
                continue
            copies=conn.execute('SELECT instance_id FROM v106_item_instances '
               'WHERE account_id=? AND item_id=? ORDER BY instance_id',(aid,iid)).fetchall()
            if not copies:
                raise RuntimeError(f'v106 EQ: niejednoznaczna sztuka w slocie {slot}')
            available=[row[0] for row in copies if conn.execute(
               'SELECT 1 FROM v106_equipped_instances WHERE instance_id=?',
               (row[0],)).fetchone() is None]
            if not available:
                raise RuntimeError('v106 EQ: brak wolnej, fizycznej kopii dla slotu')
            conn.execute('INSERT INTO v106_equipped_instances(account_id,slot,instance_id) '
                         'VALUES(?,?,?)',(aid,slot,available[0]))
            done+=1
        for aid, in conn.execute('SELECT DISTINCT account_id FROM equipment'):
            _check_account(conn,int(aid),catalog)
        conn.execute('RELEASE SAVEPOINT sb106_prepare_slots')
        if not outer:conn.commit()
        return {'new_slot_bindings':done,'migrated':migrated,
                'status':'STAGING ONLY - trading/mail/bank not integrated'}
    except Exception:
        conn.execute('ROLLBACK TO SAVEPOINT sb106_prepare_slots')
        conn.execute('RELEASE SAVEPOINT sb106_prepare_slots')
        raise


def attach_by_item(conn,aid,slot,iid,catalog,*,commit=True,confirm_disposable_copy=False):
    """Atomic experimental equip: real v105 equipment + per-copy slot binding."""
    _require_copy(confirm_disposable_copy)
    aid=int(aid);slot=str(slot);iid=str(iid)
    if not slot or iid not in _equipment_catalog(catalog):
        raise ValueError('v106 EQ: nieprawidłowy slot lub typ przedmiotu')
    outer=conn.in_transaction
    # v105 DatabaseInventoryMixin.equip(..., commit=False) must leave its SQL
    # changes pending even when no caller-owned transaction existed yet.
    # A top-level SAVEPOINT alone would auto-commit on RELEASE in sqlite3.
    started_pending=not outer and not commit
    if started_pending:
        conn.execute('BEGIN')
    conn.execute('SAVEPOINT sb106_equip_slot')
    try:
        _check_account(conn,aid,catalog)
        qty=conn.execute('SELECT quantity FROM inventory WHERE account_id=? AND item_id=?',
                         (aid,iid)).fetchone()
        quantity=qty[0] if qty else 0
        if type(quantity)!=int or quantity<1:
            raise RuntimeError('v106 EQ: nie masz tego przedmiotu')
        existing=conn.execute('SELECT instance_id FROM v106_equipped_instances '
                              'WHERE account_id=? AND slot=?',(aid,slot)).fetchone()
        if existing:
            old=conn.execute('SELECT item_id FROM v106_item_instances WHERE instance_id=?',
                             (existing[0],)).fetchone()
            if old and str(old[0])==iid:
                # No-op; preserves the previous physical instance.
                conn.execute('RELEASE SAVEPOINT sb106_equip_slot')
                if commit and not outer:conn.commit()
                return existing[0]
        candidates=conn.execute('''SELECT i.instance_id,i.evolution_stage
            FROM v106_item_instances i LEFT JOIN v106_equipped_instances s
            ON s.instance_id=i.instance_id
            LEFT JOIN v106_stored_instances st ON st.instance_id=i.instance_id
            WHERE i.account_id=? AND i.item_id=? AND s.instance_id IS NULL
              AND st.instance_id IS NULL ORDER BY i.instance_id''',(aid,iid)).fetchall()
        if not candidates:
            raise RuntimeError('v106 EQ: brak wolnej kopii do założenia')
        if len(candidates)>1 and any(int(stage)>0 for _,stage in candidates):
            raise RuntimeError('v106 EQ: wybierz dokładną kopię z ewolucją; nie zgaduję')
        chosen=str(candidates[0][0])
        conn.execute('''INSERT INTO equipment(account_id,slot,item_id) VALUES(?,?,?)
              ON CONFLICT(account_id,slot) DO UPDATE SET item_id=excluded.item_id''',
              (aid,slot,iid))
        conn.execute('''INSERT INTO v106_equipped_instances(account_id,slot,instance_id)
              VALUES(?,?,?) ON CONFLICT(account_id,slot)
              DO UPDATE SET instance_id=excluded.instance_id''',(aid,slot,chosen))
        _check_account(conn,aid,catalog)
        conn.execute('RELEASE SAVEPOINT sb106_equip_slot')
        if commit and not outer:conn.commit()
        return chosen
    except Exception:
        conn.execute('ROLLBACK TO SAVEPOINT sb106_equip_slot')
        conn.execute('RELEASE SAVEPOINT sb106_equip_slot')
        if started_pending:
            conn.rollback()
        raise


def detach(conn,aid,slot,catalog,*,confirm_disposable_copy=False):
    _require_copy(confirm_disposable_copy)
    aid=int(aid);slot=str(slot)
    outer=conn.in_transaction
    conn.execute('SAVEPOINT sb106_unequip_slot')
    try:
        _check_account(conn,aid,catalog)
        conn.execute('DELETE FROM equipment WHERE account_id=? AND slot=?',(aid,slot))
        conn.execute('DELETE FROM v106_equipped_instances WHERE account_id=? AND slot=?',(aid,slot))
        _check_account(conn,aid,catalog)
        conn.execute('RELEASE SAVEPOINT sb106_unequip_slot')
        if not outer:conn.commit()
    except Exception:
        conn.execute('ROLLBACK TO SAVEPOINT sb106_unequip_slot')
        conn.execute('RELEASE SAVEPOINT sb106_unequip_slot')
        raise


def equipped_copy(conn,aid,slot,catalog):
    """Read-only debug information; no gameplay-facing stat switch yet."""
    _check_account(conn,int(aid),catalog)
    row=conn.execute('''SELECT i.instance_id,i.item_id,i.evolution_stage
        FROM v106_equipped_instances s JOIN v106_item_instances i
        ON i.instance_id=s.instance_id
        WHERE s.account_id=? AND s.slot=?''',(int(aid),str(slot))).fetchone()
    return tuple(row) if row is not None else None
