# -*- coding: utf-8 -*-
"""v106 STAGING: stat bonuses from the exact equipped physical EQ instance.

Read-only. Does not alter v105 legacy evolution, migration, or player records.
Fail closed if an enabled experimental physical slot ledger is inconsistent.
"""
from __future__ import annotations

import os
from systems.equipment_evolution_v10500 import current_stage, MAX_STAGE


def equipped_evolution_stage(db, account_id, slot, item_id):
    """Return the evolution level for a worn *instance*, never its item template.

    v105 without the explicit disposable-copy marker uses the existing legacy
    per-template stage. An armed staging DB must have the same checked physical
    slot ID and owner. No fallback to template bonus is allowed when it differs.
    """
    from systems.v10700_eq_runtime_gate import is_enabled
    if not is_enabled(db):
        return current_stage(db.conn, account_id, item_id)
    catalog = getattr(db, '_v106_shadow_item_catalog', None)
    if not isinstance(catalog, dict):
        raise RuntimeError('v106 bonus EQ: brak katalogu fizycznych kopii')
    item_id, slot = str(item_id), str(slot)
    if catalog.get(item_id, {}).get('type') not in ('armor', 'weapon'):
        return current_stage(db.conn, account_id, item_id)
    from systems.equipment_shadow_slots_v10600 import equipped_copy
    found = equipped_copy(db.conn, account_id, slot, catalog)
    if found is None or found[1] != item_id:
        raise RuntimeError('v106 bonus EQ: slot nie wskazuje właściwej fizycznej sztuki')
    stage = found[2]
    if type(stage) is not int or not 0 <= stage <= MAX_STAGE:
        raise ValueError('v106 bonus EQ: nieprawidłowy etap ewolucji kopii')
    return stage


def evolve_equipped_copy_on_disposable_test(db, account_id, slot, instance_id,
                                           *, confirm_disposable_copy=False, commit=True):
    """Authorised per-copy operation; scoped SQL identity write permission."""
    from systems.v10700_equipment_write_barrier import approved_instance_operation
    with approved_instance_operation(db.conn):
        return _evolve_equipped_copy_transaction(
            db,account_id,slot,instance_id,
            confirm_disposable_copy=confirm_disposable_copy,commit=commit)


def _evolve_equipped_copy_transaction(db, account_id, slot, instance_id,
                                       *, confirm_disposable_copy=False, commit=True):
    """Spend v105 materials for one exact worn armor copy (staging, DB-only).

    Only the explicitly gated staging Haldor command may call it. The physical identity, material decrement and
    per-copy stage share one SQLite savepoint. Existing legacy player records
    and the separate v105 evolve command are never rewritten.
    """
    from systems.v10700_eq_runtime_gate import is_enabled
    if not is_enabled(db):
        raise PermissionError('v107 EQ: fizyczny rejestr nie jest aktywny')
    if not getattr(db,'_v107_eq_live_active',False) and confirm_disposable_copy is not True:
        raise PermissionError('v106: ewolucja fizycznej kopii wymaga potwierdzonej bazy testowej')
    catalog=getattr(db,'_v106_shadow_item_catalog',None)
    if not isinstance(catalog,dict):
        raise RuntimeError('v106: brak katalogu EQ')
    from systems.equipment_shadow_slots_v10600 import equipped_copy
    from systems.equipment_evolution_v10500 import required_materials
    conn=db.conn; aid=int(account_id)
    outer=conn.in_transaction
    started_pending=not outer and not commit
    if started_pending:conn.execute('BEGIN')
    conn.execute('SAVEPOINT sb106_evolve_one_copy')
    try:
        found=equipped_copy(conn,aid,str(slot),catalog)
        if not found or found[0]!=str(instance_id):
            raise RuntimeError('v106: sztuka EQ nie znajduje się w podanym slocie')
        _,item_id,stage=found
        if catalog[item_id].get('type')!='armor':
            raise ValueError('v106: ewolucja dotyczy tylko pancerza')
        if type(stage) is not int or not 0<=stage<=MAX_STAGE:
            raise ValueError('v106: nieprawidłowy etap fizycznego EQ')
        if stage==MAX_STAGE:
            conn.execute('RELEASE SAVEPOINT sb106_evolve_one_copy')
            if not outer and commit:conn.commit()
            return False,stage
        target=stage+1
        materials=required_materials(target)
        for material,amount in materials.items():
            row=conn.execute('SELECT quantity FROM profession_storage WHERE '
                'account_id=? AND container=? AND item_id=?',
                (aid,'craftbox',material)).fetchone()
            if not row or type(row[0]) is not int or row[0]<amount:
                conn.execute('ROLLBACK TO SAVEPOINT sb106_evolve_one_copy')
                conn.execute('RELEASE SAVEPOINT sb106_evolve_one_copy')
                if started_pending:conn.rollback()
                return False,stage
        for material,amount in materials.items():
            cur=conn.execute('UPDATE profession_storage SET quantity=quantity-? '
                'WHERE account_id=? AND container=? AND item_id=? AND quantity>=?',
                (amount,aid,'craftbox',material,amount))
            if cur.rowcount!=1:raise RuntimeError('v106: zmiana materiałów w trakcie ewolucji')
        cur=conn.execute('UPDATE v106_item_instances SET evolution_stage=? '
            'WHERE instance_id=? AND account_id=? AND item_id=? AND evolution_stage=?',
            (target,instance_id,aid,item_id,stage))
        if cur.rowcount!=1:raise RuntimeError('v106: równoległa zmiana etapu EQ')
        # Verify shadow equipment and inventory still match, before RELEASE.
        from systems.equipment_shadow_slots_v10600 import _check_account
        _check_account(conn,aid,catalog)
        conn.execute('RELEASE SAVEPOINT sb106_evolve_one_copy')
        if not outer and commit:conn.commit()
        return True,target
    except BaseException:
        conn.execute('ROLLBACK TO SAVEPOINT sb106_evolve_one_copy')
        conn.execute('RELEASE SAVEPOINT sb106_evolve_one_copy')
        if started_pending:conn.rollback()
        raise
