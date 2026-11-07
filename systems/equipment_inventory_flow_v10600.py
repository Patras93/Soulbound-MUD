# -*- coding: utf-8 -*-
"""v106 STAGING: atomic inventory/per-copy EQ operations on disposable SQLite.

This does NOT enable a live cutover. Only storage.db_inventory methods with an
explicit disposable-copy marker can call the adapter. Other direct SQL paths
(marketplace, crafting, scripts) require separate integration.
"""
from __future__ import annotations

import os
from uuid import uuid4
from systems.equipment_shadow_slots_v10600 import _check_account, _equipment_catalog
from systems.equipment_evolution_v10500 import is_evolved
from core.sqlite_numeric_guard_v10400 import require_sqlite_int64


def tracked(db, item_id):
    """Protect all normal inventory routes when physical EQ is armed."""
    from systems.v10700_eq_runtime_gate import is_enabled
    if not is_enabled(db):
        return False
    item_id=str(item_id)
    item=db._v106_shadow_item_catalog.get(item_id)
    if not isinstance(item,dict):
        # Generated craft/deep items must be registered before they can be
        # added. Otherwise they could bypass the physical ledger entirely.
        if item_id.startswith(('craftq_','deepq_','endlessq_')):
            raise RuntimeError('v107 EQ: niezarejestrowany dynamiczny sprzęt')
        return False
    return item.get('type') in ('armor','weapon')


def forbid_unintegrated(db,item_id,route):
    if tracked(db,item_id):
        raise RuntimeError('v106 EQ: operacja '+str(route)+' jeszcze nie obsługuje '
                           'fizycznej kopii; zapis odrzucony bez zmian')


# Historical v105 forge/rune/upgrade metadata is per (account,item_id).
# Until it is migrated per physical copy, do not let a transfer/removal/new
# duplicate inherit, orphan or silently drop those modifications.
_LEGACY_MODIFIER_TABLES=(
    'equipment_reforges', 'equipment_upgrades_v03042', 'equipment_runes_v0925',
    'equipment_socket_bonus_v03114', 'tech_set_upgrades_v0320',
)


def _legacy_modifiers(conn,account,item):
    existing={str(row[0]) for row in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' ")}
    for table in _LEGACY_MODIFIER_TABLES:
        if table in existing and conn.execute(
                f'SELECT 1 FROM {table} WHERE account_id=? AND item_id=? LIMIT 1',
                (account,item)).fetchone():
            return True
    return False


def _qty(conn,account,item):
    row=conn.execute('SELECT quantity FROM inventory WHERE account_id=? AND item_id=?',
                     (account,item)).fetchone()
    return require_sqlite_int64('inventory.quantity', row[0]) if row else 0


def _write_qty(conn,account,item,qty):
    qty=require_sqlite_int64('inventory.quantity',qty)
    if qty<0:raise ValueError('v106 EQ: ujemna liczba przedmiotów')
    if qty==0:
        conn.execute('DELETE FROM inventory WHERE account_id=? AND item_id=?',(account,item))
    else:
        conn.execute('INSERT INTO inventory(account_id,item_id,quantity) VALUES(?,?,?) '
                     'ON CONFLICT(account_id,item_id) DO UPDATE SET quantity=excluded.quantity',
                     (account,item,qty))


def _atomic(conn,callback,*,commit=True):
    # A production-style SQLite barrier, when installed on an approved test
    # clone, must be lifted only for this checked and atomic physical adapter.
    from systems.v10700_equipment_write_barrier import approved_instance_operation
    with approved_instance_operation(conn):
        return _atomic_inner(conn,callback,commit=commit)


def _atomic_inner(conn,callback,*,commit=True):
    outer=conn.in_transaction
    own_pending=not outer and not commit
    if own_pending:conn.execute('BEGIN')
    conn.execute('SAVEPOINT v106_equipment_inventory_operation')
    try:
        result=callback()
        conn.execute('RELEASE SAVEPOINT v106_equipment_inventory_operation')
        if commit and not outer:conn.commit()
        return result
    except BaseException:
        conn.execute('ROLLBACK TO SAVEPOINT v106_equipment_inventory_operation')
        conn.execute('RELEASE SAVEPOINT v106_equipment_inventory_operation')
        if own_pending:conn.rollback()
        raise


def _stage_zero_not_worn(conn,account,item,qty):
    rows=conn.execute('''SELECT i.instance_id FROM v106_item_instances i
        LEFT JOIN v106_equipped_instances s ON i.instance_id=s.instance_id
        LEFT JOIN v106_stored_instances st ON i.instance_id=st.instance_id
        WHERE i.account_id=? AND i.item_id=? AND i.evolution_stage=0
          AND s.instance_id IS NULL AND st.instance_id IS NULL
        ORDER BY i.instance_id''',
        (account,item)).fetchall()
    return [str(row[0]) for row in rows[:qty]] if len(rows)>=qty else []


def add(db,account,item,qty,*,commit=True):
    """Drops/purchases in the normal inventory method get new distinct IDs."""
    account=int(account);item=str(item)
    qty=require_sqlite_int64('v106.add.quantity',qty)
    if qty<1:raise ValueError('v106 EQ: ilość musi być dodatnia')
    conn=db.conn;cat=db._v106_shadow_item_catalog
    def operation():
        _check_account(conn,account,cat)
        if is_evolved(conn,account,item) or _legacy_modifiers(conn,account,item):
            raise RuntimeError('v106 EQ: stare ulepszenie tego ID - nie dokładaj kopii')
        balance=_qty(conn,account,item)
        _write_qty(conn,account,item,require_sqlite_int64('v106.add.total',balance+qty))
        for _ in range(qty):
            conn.execute('INSERT INTO v106_item_instances '
                '(instance_id,account_id,item_id,evolution_stage,origin) VALUES(?,?,?,0,?)',
                (str(uuid4()),account,item,'v106_inventory'))
        _check_account(conn,account,cat)
    return _atomic(conn,operation,commit=commit)


def remove(db,account,item,qty,*,commit=True):
    """Consume/sell only untouched, non-equipped copies; never lose their stage."""
    account=int(account);item=str(item)
    qty=require_sqlite_int64('v106.remove.quantity',qty)
    if qty<1:raise ValueError('v106 EQ: ilość musi być dodatnia')
    conn=db.conn;cat=db._v106_shadow_item_catalog
    def operation():
        _check_account(conn,account,cat)
        if _qty(conn,account,item)<qty:return False
        if is_evolved(conn,account,item) or _legacy_modifiers(conn,account,item):return False
        ids=_stage_zero_not_worn(conn,account,item,qty)
        if len(ids)!=qty:return False
        for uid in ids:
            conn.execute('DELETE FROM v106_item_instances WHERE instance_id=?',(uid,))
        _write_qty(conn,account,item,_qty(conn,account,item)-qty)
        db._consume_shop_purchase_lots_v1175(account,item,qty)
        _check_account(conn,account,cat)
        return True
    return _atomic(conn,operation,commit=commit)


def transfer(db,source,target,item,qty=1):
    """Transfer original unmodified physical IDs, preserving cost basis atomically."""
    source=int(source);target=int(target);item=str(item)
    qty=require_sqlite_int64('v106.transfer.quantity',qty)
    if qty<1 or source==target:return False
    conn=db.conn;cat=db._v106_shadow_item_catalog
    def operation():
        _check_account(conn,source,cat)
        _check_account(conn,target,cat)
        if any(is_evolved(conn,aid,item) or _legacy_modifiers(conn,aid,item)
               for aid in (source,target)):return False
        count=_qty(conn,source,item)
        if count<qty:return False
        ids=_stage_zero_not_worn(conn,source,item,qty)
        if len(ids)!=qty:return False
        target_qty=_qty(conn,target,item)
        updated_target=require_sqlite_int64('v106.transfer.total',target_qty+qty)
        for uid in ids:
            conn.execute('UPDATE v106_item_instances SET account_id=? WHERE instance_id=? AND account_id=?',
                         (target,uid,source))
        _write_qty(conn,source,item,count-qty)
        _write_qty(conn,target,item,updated_target)
        db._consume_shop_purchase_lots_v1175(source,item,qty,transfer_to=target)
        _check_account(conn,source,cat)
        _check_account(conn,target,cat)
        return True
    return _atomic(conn,operation,commit=True)
# Bank v106: only the integrated two-sided action below can move a physical
# item. The legacy add_bank_item/remove_bank_item methods remain fail-closed.
def _bank_qty(conn,account,item):
    row=conn.execute('SELECT quantity FROM bank_items WHERE account_id=? AND item_id=?',
                     (account,item)).fetchone()
    return require_sqlite_int64('bank_items.quantity',row[0]) if row else 0


def _bank_write_qty(conn,account,item,qty):
    qty=require_sqlite_int64('bank_items.quantity',qty)
    if qty<0:raise ValueError('v106 EQ: ujemna ilość w banku')
    if qty==0:
        conn.execute('DELETE FROM bank_items WHERE account_id=? AND item_id=?',(account,item))
    else:
        conn.execute('INSERT INTO bank_items(account_id,item_id,quantity) VALUES(?,?,?) '
                     'ON CONFLICT(account_id,item_id) DO UPDATE SET quantity=excluded.quantity',
                     (account,item,qty))


def _check_bank(conn,account,item):
    """Old bank items have no physical IDs; reject until reconciled on a clone."""
    expected=_bank_qty(conn,account,item)
    rows=conn.execute('''SELECT st.instance_id,i.account_id,i.item_id,i.evolution_stage
        FROM v106_stored_instances st LEFT JOIN v106_item_instances i
        ON st.instance_id=i.instance_id WHERE st.account_id=?
            AND st.storage_kind='bank' AND st.container='' AND i.item_id=?''',
        (account,item)).fetchall()
    if expected!=len(rows) or any(owner!=account or stage!=0
                                  for _,owner,_,stage in rows):
        raise RuntimeError('v106 EQ: istniejący stan banku wymaga uzgodnienia kopii na kopii bazy')
    return [row[0] for row in rows]


def _move_basis_without_commit(db,account,from_item,to_item,qty):
    """v105 cost lots; intentionally NOT using legacy helper which commits."""
    remaining=qty
    rows=db.conn.execute('SELECT paid_silver,quantity FROM shop_purchase_lots_v1175 '
                         'WHERE account_id=? AND item_id=? ORDER BY paid_silver',
                         (account,from_item)).fetchall()
    for row in rows:
        units=min(remaining,require_sqlite_int64('shop_purchase_lots.quantity',row[1]))
        if units<=0:break
        cost=require_sqlite_int64('shop_purchase_lots.paid_silver',row[0])
        if units==row[1]:
            db.conn.execute('DELETE FROM shop_purchase_lots_v1175 '
                            'WHERE account_id=? AND item_id=? AND paid_silver=?',
                            (account,from_item,cost))
        else:
            db.conn.execute('UPDATE shop_purchase_lots_v1175 SET quantity=quantity-? '
                            'WHERE account_id=? AND item_id=? AND paid_silver=?',
                            (units,account,from_item,cost))
        db.record_shop_purchase_v1175(account,to_item,units,cost,commit=False)
        remaining-=units


def bank_move(db,account,item,qty=1,*,withdraw=False,commit=True):
    """Atomic inventory <-> bank transfer of untouched physical IDs, test copy ONLY.

    Old untracked bank contents stay untouched, never fabricated. The caller
    must explicitly opt in to bank movements in addition to shadow staging.
    """
    if not tracked(db,item) or not getattr(db,'_v106_bank_shadow_disposable_copy',False):
        raise PermissionError('v106 EQ: bank kopii testowej nieaktywny')
    account=int(account);item=str(item)
    qty=require_sqlite_int64('v106.bank.quantity',qty)
    if qty<1:raise ValueError('v106 EQ: ilość musi być dodatnia')
    conn=db.conn;cat=db._v106_shadow_item_catalog
    def operation():
        _check_account(conn,account,cat)
        banked=_check_bank(conn,account,item)
        if is_evolved(conn,account,item) or _legacy_modifiers(conn,account,item):
            return False
        if withdraw:
            if len(banked)<qty:return False
            selected=sorted(banked)[:qty]
            new_qty=require_sqlite_int64('v106.bank.inventory_total',_qty(conn,account,item)+qty)
            conn.executemany('DELETE FROM v106_stored_instances WHERE instance_id=?',
                             ((uid,) for uid in selected))
            _bank_write_qty(conn,account,item,len(banked)-qty)
            _write_qty(conn,account,item,new_qty)
            _move_basis_without_commit(db,account,db.bank_purchase_lot_key_v1175(item),item,qty)
        else:
            if _qty(conn,account,item)<qty:return False
            selected=_stage_zero_not_worn(conn,account,item,qty)
            if len(selected)!=qty:return False
            conn.executemany('INSERT INTO v106_stored_instances '
                '(instance_id,account_id,storage_kind,container) VALUES(?,?,?,?)',
                ((uid,account,'bank','') for uid in selected))
            _write_qty(conn,account,item,_qty(conn,account,item)-qty)
            _bank_write_qty(conn,account,item,require_sqlite_int64('v106.bank.total',len(banked)+qty))
            _move_basis_without_commit(db,account,item,db.bank_purchase_lot_key_v1175(item),qty)
        _check_account(conn,account,cat)
        _check_bank(conn,account,item)
        return True
    return _atomic(conn,operation,commit=commit)


def reconcile_legacy_bank_on_disposable_copy(db,*,confirm_disposable_copy=False):
    """Explicit migration of old stage-zero bank gear; NEVER at server startup.

    Existing v105 bank rows remain untouched. Only equipment without a legacy
    stage/runes/reforge is assigned deterministic physical IDs. Any uncertainty
    rejects the WHOLE procedure without partial writes.
    """
    if confirm_disposable_copy is not True or not getattr(
            db,'_v106_shadow_slots_disposable_copy',False):
        raise PermissionError('v106 EQ: uzgadnianie tylko na jawnej kopii testowej')
    if os.environ.get('SOULBOUND_V106_STAGING')!='1':
        raise PermissionError('v106 EQ: brak trybu testowego')
    from uuid import uuid5,NAMESPACE_URL
    conn=db.conn;cat=db._v106_shadow_item_catalog
    known=_equipment_catalog(cat)
    def operation():
        made=0;inspected=0
        rows=conn.execute('SELECT account_id,item_id,quantity FROM bank_items '
                          'ORDER BY account_id,item_id').fetchall()
        for aid,iid,raw_qty in rows:
            aid=int(aid);iid=str(iid)
            if iid not in known:continue
            qty=require_sqlite_int64('v106.bank.legacy_count',raw_qty)
            if qty<=0 or qty>20000:
                raise RuntimeError('v106 EQ: nieprawidłowy lub zbyt duży stan banku do bezpiecznego uzgodnienia')
            inspected+=1
            _check_account(conn,aid,cat)
            if is_evolved(conn,aid,iid) or _legacy_modifiers(conn,aid,iid):
                raise RuntimeError('v106 EQ: historyczne ulepszenie w banku wymaga ręcznego rozstrzygnięcia')
            present=conn.execute('''SELECT st.instance_id FROM v106_stored_instances st
                JOIN v106_item_instances i ON i.instance_id=st.instance_id
                WHERE st.account_id=? AND i.item_id=?
                      AND st.storage_kind='bank' AND st.container='' ''',
                (aid,iid)).fetchall()
            if present:
                _check_bank(conn,aid,iid)
                continue
            for ix in range(qty):
                uid=str(uuid5(NAMESPACE_URL,f'soulbound:v106:legacy:bank:{aid}:{iid}:{ix+1}'))
                existing=conn.execute('SELECT 1 FROM v106_item_instances WHERE instance_id=?',
                                      (uid,)).fetchone()
                if existing:raise RuntimeError('v106 EQ: kolizja identyfikatora starej sztuki w banku')
                conn.execute('INSERT INTO v106_item_instances '
                             '(instance_id,account_id,item_id,evolution_stage,origin) '
                             'VALUES(?,?,?,0,?)',(uid,aid,iid,'legacy_bank_zero'))
                conn.execute('INSERT INTO v106_stored_instances '
                             '(instance_id,account_id,storage_kind,container) VALUES(?,?,?,?)',
                             (uid,aid,'bank',''))
                made+=1
            _check_bank(conn,aid,iid)
            _check_account(conn,aid,cat)
        # Banked physical copies without a matching v105 bank quantity are corrupt.
        for aid,iid in conn.execute('''SELECT DISTINCT st.account_id,i.item_id
            FROM v106_stored_instances st JOIN v106_item_instances i
            ON i.instance_id=st.instance_id WHERE st.storage_kind='bank' '''):
            _check_bank(conn,int(aid),str(iid))
        return {'inspected':inspected,'new_instances':made,'status':'ONLY TEST COPY'}
    return _atomic(conn,operation,commit=True)


def _storage_location(container):
    container=str(container)
    if not (1<=len(container)<=64 and container.replace('_','').isalnum()):
        raise ValueError('v106 EQ: nieprawidłowy magazyn')
    return container


def _storage_qty(conn,account,container,item):
    row=conn.execute('SELECT quantity FROM profession_storage '
                     'WHERE account_id=? AND container=? AND item_id=?',
                     (account,container,item)).fetchone()
    return require_sqlite_int64('profession_storage.quantity',row[0]) if row else 0


def _storage_write_qty(conn,account,container,item,qty):
    qty=require_sqlite_int64('profession_storage.quantity',qty)
    if qty<0:raise ValueError('v106 EQ: ujemny magazyn')
    if qty==0:
        conn.execute('DELETE FROM profession_storage '
                     'WHERE account_id=? AND container=? AND item_id=?',
                     (account,container,item))
    else:
        conn.execute('INSERT INTO profession_storage(account_id,container,item_id,quantity) '
                     'VALUES(?,?,?,?) ON CONFLICT(account_id,container,item_id) '
                     'DO UPDATE SET quantity=excluded.quantity',
                     (account,container,item,qty))


def _check_storage(conn,account,container,item):
    qty=_storage_qty(conn,account,container,item)
    rows=conn.execute('''SELECT st.instance_id,i.account_id,i.evolution_stage
        FROM v106_stored_instances st JOIN v106_item_instances i
        ON i.instance_id=st.instance_id
        WHERE st.account_id=? AND st.storage_kind='storage'
          AND st.container=? AND i.item_id=?''',(account,container,item)).fetchall()
    if qty!=len(rows) or any(owner!=account or stage!=0 for _,owner,stage in rows):
        raise RuntimeError('v106 EQ: historyczny magazyn wymaga osobnego uzgodnienia')
    return [row[0] for row in rows]


def storage_move(db,account,container,item,qty=1,*,withdraw=False,commit=True):
    """Staging-only atomic physical gear move between inventory and one container.

    Ordinary crafting, mail, storage add/remove and direct SQL remain blocked.
    """
    if not tracked(db,item) or not getattr(db,'_v106_storage_shadow_disposable_copy',False):
        raise PermissionError('v106 EQ: magazyn kopii testowej nieaktywny')
    container=_storage_location(container)
    account=int(account);item=str(item)
    qty=require_sqlite_int64('v106.storage.qty',qty)
    if qty<1:raise ValueError('v106 EQ: ilość musi być dodatnia')
    conn=db.conn;catalog=db._v106_shadow_item_catalog
    def operation():
        _check_account(conn,account,catalog)
        stored=_check_storage(conn,account,container,item)
        if is_evolved(conn,account,item) or _legacy_modifiers(conn,account,item):
            return False
        basis='__storage_v106__:'+container+':'+item
        if withdraw:
            if len(stored)<qty:return False
            selected=sorted(stored)[:qty]
            updated=require_sqlite_int64('v106.storage.inventory',_qty(conn,account,item)+qty)
            conn.executemany('DELETE FROM v106_stored_instances WHERE instance_id=?',
                             ((uid,) for uid in selected))
            _storage_write_qty(conn,account,container,item,len(stored)-qty)
            _write_qty(conn,account,item,updated)
            _move_basis_without_commit(db,account,basis,item,qty)
        else:
            if _qty(conn,account,item)<qty:return False
            selected=_stage_zero_not_worn(conn,account,item,qty)
            if len(selected)!=qty:return False
            conn.executemany('INSERT INTO v106_stored_instances '
                '(instance_id,account_id,storage_kind,container) VALUES(?,?,?,?)',
                ((uid,account,'storage',container) for uid in selected))
            _write_qty(conn,account,item,_qty(conn,account,item)-qty)
            _storage_write_qty(conn,account,container,item,
                               require_sqlite_int64('v106.storage.total',len(stored)+qty))
            _move_basis_without_commit(db,account,item,basis,qty)
        _check_account(conn,account,catalog)
        _check_storage(conn,account,container,item)
        return True
    return _atomic(conn,operation,commit=commit)
