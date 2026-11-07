# -*- coding: utf-8 -*-
"""v106 DEVELOPMENT: conservative per-copy EQ migration for a DISPOSABLE DB CLONE.

The old inventory has one quantity per (account,item_id), not physical instances.
Automatic binding is safe ONLY when exactly one copy is present. Multi-copy
orphan/ambiguous v105 evolution stays in the unchanged old ledger and is
reported; the game must NOT switch to this new table until trading, bank,
mail, crafting and equip operations are implemented and TCP-tested.
"""
from __future__ import annotations
import sqlite3
import re
from uuid import uuid5, NAMESPACE_URL
from systems.equipment_evolution_v10500 import KEY_PREFIX,MAX_STAGE

# Only a staging memory/time safety bound; never a gameplay inventory cap.
MAX_REHEARSAL_COPIES_PER_TEMPLATE = 20000


def _manual_row(conn,account,item):
    """Read-only lookup; legacy rows without a reviewed slot remain unverified."""
    if conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' "
                    "AND name='v106_manual_evolution_allocations'").fetchone() is None:
        return None
    fields={str(col[1]) for col in conn.execute(
        'PRAGMA table_info(v106_manual_evolution_allocations)')}
    common=('SELECT chosen_ordinal,expected_quantity,legacy_stage,review_reference '
            'FROM v106_manual_evolution_allocations WHERE account_id=? AND item_id=?')
    if 'selected_worn_slot' not in fields:
        old=conn.execute(common,(account,item)).fetchone()
        return (*old, '__UNVERIFIED_HISTORIC_SLOT__') if old else None
    return conn.execute('SELECT chosen_ordinal,expected_quantity,legacy_stage,review_reference,selected_worn_slot '
        'FROM v106_manual_evolution_allocations WHERE account_id=? AND item_id=?',
        (account,item)).fetchone()


def _manual_verified(conn,account,item,qty,stage):
    """Require signed-off ordinal, exact physical ledger AND selected worn slot.

    The earlier 6-column review format omitted the reviewed worn slot. It
    therefore cannot prove what the reviewer actually approved and is treated
    as stale, never automatically upgraded to a production-ready decision.
    """
    row=_manual_row(conn,account,item)
    if row is None:return False
    ordinal,expected_count,old_stage,review_reference,selected_slot=row
    if (type(qty) is not int or type(stage) is not int or qty<2 or stage<1 or
            type(expected_count) is not int or expected_count!=qty or
            type(old_stage) is not int or old_stage!=stage or
            type(ordinal) is not int or not 1<=ordinal<=qty or
            not isinstance(review_reference,str) or
            not 8<=len(review_reference.strip())<=160 or
            (selected_slot is not None and (
                not isinstance(selected_slot,str) or not selected_slot.strip()))):
        return False
    tables={str(entry[0]) for entry in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name IN "
        "('equipment','v106_equipped_instances','v106_item_instances')")}
    if {'equipment','v106_equipped_instances','v106_item_instances'}-tables:
        return False
    existing=conn.execute('SELECT instance_id,evolution_stage,origin '
        'FROM v106_item_instances WHERE account_id=? AND item_id=?',
        (account,item)).fetchall()
    if len(existing)!=qty:return False
    # A review loses validity if previously untracked copies or template-wide
    # modifiers appear after sign-off. Audit should fail closed, not keep
    # labelling the historic allocation as verified.
    try:
        from systems.equipment_manual_reconcile_v10600 import _refuse_external_copies
        from systems.equipment_inventory_flow_v10600 import _legacy_modifiers
        if _legacy_modifiers(conn,account,item):return False
        _refuse_external_copies(conn,account,item)
    except (RuntimeError,ValueError,sqlite3.Error):
        return False
    expected={str(uuid5(NAMESPACE_URL,
        f'soulbound:v106:legacy:{account}:{item}' +
        (f':copy:{number}' if number>1 else ''))):
        (stage if number==ordinal else 0,'manual_legacy_review')
        for number in range(1,qty+1)}
    if {str(uid):(evo,origin) for uid,evo,origin in existing}!=expected:
        return False
    worn={str(entry[0]) for entry in conn.execute(
        'SELECT slot FROM equipment WHERE account_id=? AND item_id=?',
        (account,item))}
    bound={}
    for slot,uid in conn.execute('''SELECT s.slot,s.instance_id
            FROM v106_equipped_instances s JOIN v106_item_instances i
            ON i.instance_id=s.instance_id
            WHERE s.account_id=? AND i.account_id=? AND i.item_id=?''',
            (account,account,item)):
        if str(slot) in bound:return False
        bound[str(slot)]=str(uid)
    if set(bound)!=worn or any(uid not in expected for uid in bound.values()):
        return False
    # A corrupted legacy shadow table might lack UNIQUE(instance_id). Never
    # accept the same physical item equipped in two slots or accounts.
    if len(set(bound.values()))!=len(bound):
        return False
    for uid in bound.values():
        if conn.execute('SELECT COUNT(*) FROM v106_equipped_instances '
                        'WHERE instance_id=?',(uid,)).fetchone()[0]!=1:
            return False
    for slot in worn:
        target=conn.execute('SELECT instance_id FROM v106_equipped_instances '
                           'WHERE account_id=? AND slot=?',(account,slot)).fetchone()
        if target is None or str(target[0])!=bound[slot]:return False
    chosen=str(uuid5(NAMESPACE_URL, f'soulbound:v106:legacy:{account}:{item}' +
         (f':copy:{ordinal}' if ordinal>1 else '')))
    # Even swapping TWO otherwise valid copies between worn slots must not
    # silently reinterpret the reviewer's original, explicit slot selection.
    if worn:
        return selected_slot in worn and bound.get(selected_slot)==chosen
    return selected_slot is None


def _valid_legacy_stage(value):
    """Reject silent float truncation, malformed text and out-of-range stages."""
    if type(value) is int:
        stage = value
    elif isinstance(value, str) and re.fullmatch(r'[+-]?[0-9]+', value.strip()):
        stage = int(value.strip())
    else:
        raise ValueError('EQ: uszkodzony zapis historycznego etapu ewolucji')
    if not 0 <= stage <= MAX_STAGE:
        raise ValueError('EQ: historyczny etap ewolucji poza zakresem')
    return stage


def snapshot(conn,item_catalog):
    """Return a read-only migration plan for physical equipment in inventory."""
    equipped={k for k,v in item_catalog.items() if isinstance(v,dict)
              and v.get('type') in ('armor','weapon')}
    result=[];seen=set()
    for account,item_id,quantity in conn.execute(
            'SELECT account_id,item_id,quantity FROM inventory ORDER BY account_id,item_id'):
        if item_id not in equipped:continue
        row=conn.execute('SELECT value FROM player_records_v03051 '
             'WHERE account_id=? AND record_key=?',(account,KEY_PREFIX+item_id)).fetchone()
        if type(quantity) is not int or not 0 <= quantity <= MAX_REHEARSAL_COPIES_PER_TEMPLATE:
            raise ValueError('EQ: liczba fizycznych kopii wymaga odrębnej kontroli; próba migracji przerwana')
        stage=_valid_legacy_stage(row[0]) if row else 0
        seen.add((int(account),str(item_id)))
        result.append({'account_id':int(account),'item_id':str(item_id),
                'quantity':quantity,'legacy_stage':stage,
                'status':('verified_manual' if _manual_verified(conn,int(account),str(item_id),quantity,stage)
                          else 'verified' if quantity==1 or (quantity>1 and stage==0)
                          else 'requires_manual_reconciliation')})
    # Legacy stages without a currently owned item MUST also be reported.
    for account,key,stage in conn.execute(
            'SELECT account_id,record_key,value FROM player_records_v03051 '
            'WHERE substr(record_key,1,?)=? ORDER BY account_id,record_key',
            (len(KEY_PREFIX),KEY_PREFIX)):
        iid=str(key)[len(KEY_PREFIX):]
        if (int(account),iid) in seen:continue
        stage=_valid_legacy_stage(stage)
        if stage:
            result.append({'account_id':int(account),'item_id':iid,'quantity':0,
                           'legacy_stage':stage,'status':'requires_manual_reconciliation'})
    return result


def _schema(conn):
    # execute() does not silently commit a caller-owned transaction.
    conn.execute('''CREATE TABLE IF NOT EXISTS v106_item_instances (
            instance_id TEXT PRIMARY KEY, account_id INTEGER NOT NULL,
            item_id TEXT NOT NULL, evolution_stage INTEGER NOT NULL
                CHECK(evolution_stage BETWEEN 0 AND 10),
            origin TEXT NOT NULL DEFAULT 'legacy_unique'
        )''')
    conn.execute('''CREATE TABLE IF NOT EXISTS v106_evolution_migration_issues (
            account_id INTEGER NOT NULL, item_id TEXT NOT NULL,
            copies INTEGER NOT NULL, legacy_stage INTEGER NOT NULL,
            reason TEXT NOT NULL, PRIMARY KEY(account_id,item_id)
        )''')


def apply_to_explicit_test_copy(conn,item_catalog,*,confirm_disposable_copy=False):
    """Only after explicit confirmation; never called from normal server boot.

    A safe, conservative prototype. It does not delete or rewrite old records.
    Reconciliation of existing duplicates is intentionally NOT automatic.
    """
    if confirm_disposable_copy is not True:
        raise PermissionError('Najpierw wykonaj kopię SQLite i potwierdź test na KOPII.')
    # Important: snapshot before write ensures malformed legacy state is rejected.
    rows=snapshot(conn,item_catalog)
    outer=conn.in_transaction
    # DDL must be in the same SAVEPOINT as data writes. Otherwise a failed
    # migration could leave newly created physical-ledger tables behind on
    # the disposable copy, masquerading as a partially completed migration.
    conn.execute('SAVEPOINT v106_instance_migration')
    try:
        _schema(conn)
        created=ambiguous=0
        for row in rows:
            aid,iid,qty,stage=(row[x] for x in ('account_id','item_id','quantity','legacy_stage'))
            instance=str(uuid5(NAMESPACE_URL,f'soulbound:v106:legacy:{aid}:{iid}'))
            occupied=conn.execute('SELECT account_id,item_id,evolution_stage,origin '
                 'FROM v106_item_instances WHERE instance_id=?',(instance,)).fetchone()
            if _manual_row(conn,aid,iid) is not None:
                if row['status']!='verified_manual':
                    raise RuntimeError('v106 EQ: ręczna decyzja nie zgadza się z aktualnym stanem kopii')
                # A previously signed-off allocation is immutable and idempotent.
                conn.execute('DELETE FROM v106_evolution_migration_issues '
                             'WHERE account_id=? AND item_id=?',(aid,iid))
                continue
            if qty>1 and stage==0:
                # Unmodified identical copies have no legacy stage to misassign.
                # Deterministic UUIDs make this idempotent; never silently repair
                # a drifted or already re-owned physical ledger on a rerun.
                expected=[instance]+[str(uuid5(NAMESPACE_URL,
                   f'soulbound:v106:legacy:{aid}:{iid}:copy:{n}')) for n in range(2,qty+1)]
                actual=conn.execute('SELECT instance_id,evolution_stage,origin '
                     'FROM v106_item_instances WHERE account_id=? AND item_id=?',
                     (aid,iid)).fetchall()
                if actual and (len(actual)!=qty or
                        {r[0] for r in actual}!=set(expected) or
                        any(r[1]!=0 or r[2]!='legacy_unique' for r in actual)):
                    raise RuntimeError('v106 EQ: zmieniona liczba, etapy lub tożsamość kopii')
                # Also reject an expected ID occupied by a different owner.
                for iid_instance in expected:
                    occupied_by=conn.execute('SELECT account_id,item_id FROM v106_item_instances '
                        'WHERE instance_id=?',(iid_instance,)).fetchone()
                    if occupied_by is not None and tuple(occupied_by)!=(aid,iid):
                        raise RuntimeError('v106 EQ: konflikt właściciela fizycznej kopii')
                if not actual:
                    conn.executemany('INSERT INTO v106_item_instances '
                        '(instance_id,account_id,item_id,evolution_stage) VALUES(?,?,?,0)',
                        ((uid,aid,iid) for uid in expected))
                    created+=qty
                conn.execute('DELETE FROM v106_evolution_migration_issues '
                             'WHERE account_id=? AND item_id=?',(aid,iid))
                continue
            if qty!=1:
                if occupied is not None:
                    raise RuntimeError('v106 EQ: liczba kopii zmieniona po migracji; wymagana weryfikacja stanu')
                reason='wiele identycznych kopii bez identyfikatorów' if qty>1 else 'brak posiadanej kopii'
                conn.execute('INSERT INTO v106_evolution_migration_issues '
                   '(account_id,item_id,copies,legacy_stage,reason) VALUES(?,?,?,?,?) '
                   'ON CONFLICT(account_id,item_id) DO UPDATE SET '
                   'copies=excluded.copies,legacy_stage=excluded.legacy_stage,reason=excluded.reason',
                   (aid,iid,qty,stage,reason))
                ambiguous+=1;continue
            if occupied is not None and (
                    int(occupied[0]) != aid or str(occupied[1]) != iid or
                    str(occupied[3]) != 'legacy_unique'):
                raise RuntimeError('v106 EQ: niezgodna tożsamość istniejącej kopii')
            if occupied is None:
                conn.execute('INSERT INTO v106_item_instances'
                  '(instance_id,account_id,item_id,evolution_stage) VALUES(?,?,?,?)',
                  (instance,aid,iid,stage))
                created+=1
            elif int(occupied[2]) != stage:
                raise RuntimeError('Migracja ponowiona po zmianie ewolucji; wymaga rekonsyliacji')
            # A previously ambiguous item was reduced to one actual copy;
            # remove only this resolved diagnostic, never touch legacy EXP/gear.
            conn.execute('DELETE FROM v106_evolution_migration_issues '
                         'WHERE account_id=? AND item_id=?',(aid,iid))
        conn.execute('RELEASE SAVEPOINT v106_instance_migration')
        if not outer:conn.commit()
        return {'new_instances':created,'ambiguous':ambiguous,'inspected':len(rows),
                'status':'STAGING ONLY - not connected to gameplay'}
    except Exception:
        conn.execute('ROLLBACK TO SAVEPOINT v106_instance_migration')
        conn.execute('RELEASE SAVEPOINT v106_instance_migration')
        raise


def cutover_readiness(conn, item_catalog):
    """Read-only safety gate for future per-item deployment, NEVER migrates.

    This is intentionally a strict *necessary* condition, not authorization
    to enable live per-item mechanics: all direct SQL routes, bank, mail, shop,
    equipped slots and saves still need atomic transaction integration.
    """
    equipment={key for key,meta in item_catalog.items() if isinstance(meta,dict)
               and meta.get('type') in ('armor','weapon')}
    inventory={}
    issues=[]
    for account,item_id,count in conn.execute('SELECT account_id,item_id,quantity FROM inventory'):
        if item_id not in equipment:continue
        k=(int(account),str(item_id))
        try:
            if type(count) is not int or count<0:
                raise ValueError('quantity is not a nonnegative integer')
            inventory[k]=count
            if count>1:
                old=conn.execute('SELECT value FROM player_records_v03051 '
                    'WHERE account_id=? AND record_key=?',
                    (k[0],KEY_PREFIX+k[1])).fetchone()
                stage=_valid_legacy_stage(old[0]) if old else 0
                if stage>0:
                    # A legacy evolution stage belongs to an unknown physical
                    # copy. This remains a HARD blocker until explicitly reviewed.
                    if not _manual_verified(conn,k[0],k[1],count,stage):
                        issues.append((k[0],k[1],
                                       'wiele kopii z historyczną ewolucją bez potwierdzonej rekonsyliacji'))
                elif stage==0:
                    # Unenhanced duplicates carry NO history to assign. The
                    # migration already creates one deterministic zero-stage ID
                    # per copy; require those exact IDs, not merely a row count.
                    expected={str(uuid5(NAMESPACE_URL,
                        f'soulbound:v106:legacy:{k[0]}:{k[1]}' +
                        (f':copy:{n}' if n>1 else '')))
                        for n in range(1,count+1)}
                    try:
                        rows=conn.execute('SELECT instance_id,evolution_stage,origin '
                            'FROM v106_item_instances WHERE account_id=? AND item_id=?',k).fetchall()
                    except sqlite3.OperationalError as exc:
                        if 'no such table: v106_item_instances' in str(exc):
                            rows=[]
                        else:raise
                    if (len(rows)!=count or {uid for uid,_,_ in rows}!=expected or
                            any(evo!=0 or origin!='legacy_unique' for _,evo,origin in rows)):
                        issues.append((k[0],k[1],
                                       'nieulepszone kopie nie mają pełnych i zgodnych ID fizycznych'))
                else:
                    issues.append((k[0],k[1],'nieprawidłowy historyczny etap ewolucji'))
        except (ValueError,TypeError):
            issues.append((k[0],k[1],'nieprawidłowa liczba kopii'))
    for row in snapshot(conn,item_catalog):
        if row['status'] not in ('verified','verified_manual') and row['legacy_stage']>0:
            issues.append((row['account_id'],row['item_id'],'historyczna ewolucja bez jednoznacznej kopii'))
    try:
        eq=conn.execute('SELECT account_id,slot,item_id FROM equipment').fetchall()
    except sqlite3.OperationalError as exc:
        if 'no such table: equipment' in str(exc):
            issues.append((0,'equipment','brak tabeli założonego EQ'))
            eq=[]
        else:raise
    equipped={}
    for account,slot,item_id in eq:
        if item_id not in equipment:continue
        k=(int(account),str(item_id))
        equipped[k]=equipped.get(k,0)+1
        if equipped[k]>inventory.get(k,0):
            issues.append((k[0],k[1],'więcej założonych kopii niż w plecaku'))
    try:
        instances=conn.execute('SELECT instance_id,account_id,item_id,evolution_stage '
                               'FROM v106_item_instances').fetchall()
    except sqlite3.OperationalError as exc:
        if 'no such table: v106_item_instances' in str(exc):
            issues.append((0,'v106_item_instances','migracja kopii nie została uruchomiona'))
            instances=[]
        else:raise
    seen={}
    for instance,account,item_id,stage in instances:
        k=(int(account),str(item_id))
        seen[k]=seen.get(k,0)+1
        if (item_id not in equipment or not isinstance(stage,int) or
                not 0 <= stage <= MAX_STAGE or inventory.get(k,0)<seen[k]):
            issues.append((k[0],k[1],'osierocona lub nieprawidłowa instancja EQ'))
    for k,quantity in inventory.items():
        if quantity==1 and seen.get(k,0)!=1:
            issues.append((*k,'brak fizycznej kopii EQ po migracji'))
        elif quantity>1 and seen.get(k,0)!=quantity:
            issues.append((*k,'brak indywidualnej reprezentacji kopii EQ'))
    # Even with no blockers this remains a preflight, not a positive runtime gate.
    return {'snapshot_items':len(inventory),'instance_rows':len(instances),
            'equipped_rows':len(eq),'blocking_issues':tuple(sorted(set(issues))),
            'data_consistent':not issues,'gameplay_ready':False}
