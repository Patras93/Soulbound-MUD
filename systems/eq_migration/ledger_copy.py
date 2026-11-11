# -*- coding: utf-8 -*-
"""Read-only preflight for v107 physical EQ on a SQLite backup of live v106.

No production writes, no post-audit deployment approval. Reports only aggregate
counts, never player names, account IDs, item IDs or private records.
"""
from __future__ import annotations
import argparse
import hashlib
from contextlib import closing
import os
from pathlib import Path
import sqlite3
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from systems.equipment_instances_v10600 import (
    snapshot,apply_to_explicit_test_copy,cutover_readiness,
)
from systems.equipment_shadow_slots_v10600 import prepare_on_disposable_copy
from systems.eq_migration.locations import audit_untracked
from systems.v10800_eq_reconciliation_plan import reconciliation_summary
from systems.v10800_eq_restore_rehearsal import _fields
from systems.v10800_eq_physical_routes import physical_route_conflicts


def _tables(conn):
    return {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}


def _legacy_data_digest(conn):
    """Fingerprint only; never print/store any player rows or item IDs."""
    digest=hashlib.sha256()
    for table,columns,order in (
        ('inventory','account_id,item_id,quantity','account_id,item_id'),
        ('equipment','account_id,slot,item_id','account_id,slot'),
        ('bank_items','account_id,item_id,quantity','account_id,item_id'),
        ('profession_storage','account_id,container,item_id,quantity',
         'account_id,container,item_id'),
        ('player_records_v03051','account_id,record_key,value',
         'account_id,record_key')):
        digest.update(table.encode('ascii'))
        for row in conn.execute('SELECT '+columns+' FROM '+table+' ORDER BY '+order):
            # Typed, length-prefixed cells: BLOB b'x' and TEXT "b'x'"
            # must not produce the same legacy-data fingerprint.
            payload=_fields(*row)
            digest.update(len(payload).to_bytes(8,'big'))
            digest.update(payload)
    return digest.digest()


def analyze_copy(conn,catalog):
    """Only disposable COPY, never raw live connection."""
    have=_tables(conn)
    required={'accounts','characters','inventory','equipment','bank_items',
              'profession_storage','player_records_v03051'}
    if missing:=required-have:
        raise RuntimeError('Brak tabel EQ: '+', '.join(sorted(missing)))
    gear={str(iid) for iid,meta in catalog.items() if isinstance(meta,dict)
          and meta.get('type') in ('armor','weapon')}
    result=dict(gear_types=len(gear),inventory_units=0,bank_units=0,
                profession_storage_units=0,legacy_ambiguous=0,
                worn_without_inventory=0,invalid_quantities=0,
                missing_shadow_bindings=0,physical_route_conflicts=0,ledger_rows=0,
                legacy_mutated_on_clone=0,ledger_not_idempotent=0)
    counts={}
    for account,item,qty in conn.execute('SELECT account_id,item_id,quantity FROM inventory'):
        if str(item) not in gear:continue
        if type(qty) is not int or qty<0:
            result['invalid_quantities']+=1
            continue
        counts[(account,item)]=qty
        result['inventory_units']+=qty
    for table,label in (('bank_items','bank_units'),('profession_storage','profession_storage_units')):
        for item,qty in conn.execute('SELECT item_id,quantity FROM '+table):
            if str(item) not in gear:continue
            if type(qty) is not int or qty<0:result['invalid_quantities']+=1
            else:result[label]+=qty
    for account,item in conn.execute('SELECT account_id,item_id FROM equipment'):
        if str(item) in gear and counts.get((account,item),0)<1:
            result['worn_without_inventory']+=1
    rows=snapshot(conn,catalog)
    result['legacy_ambiguous']=sum(r['status']=='requires_manual_reconciliation' for r in rows)
    result.update(reconciliation_summary(conn,catalog,rows=rows))
    # v107 was already officially cut over: NEVER rerun the v106 first-time
    # allocator. New drops and transfers have immutable UUID4 IDs, and their
    # owners/quantities may legitimately differ from the v107 migration day.
    # Their proof is cross-route and quantity consistency, not reconstructing
    # a historical UUID5 from the current owner's inventory amount.
    if 'v107_eq_production_cutover' in have:
        try:
            marker=conn.execute('SELECT cutover_version,backup_name '
                'FROM v107_eq_production_cutover').fetchall()
            if (len(marker)!=1 or marker[0][0]!='107.00.0' or
                    not isinstance(marker[0][1],str) or not marker[0][1]):
                result['missing_shadow_bindings']+=1
            result['ledger_rows']=conn.execute('SELECT COUNT(*) FROM v106_item_instances').fetchone()[0]
            result['physical_route_conflicts']=physical_route_conflicts(conn,catalog)
            # COUNT mismatch is an independent blocker, even if route checker
            # also detects it. No recovery is performed in the PREDEPLOY gate.
            bags={(aid,str(iid)): qty for aid,iid,qty in conn.execute(
                'SELECT account_id,item_id,quantity FROM inventory') if str(iid) in gear}
            copies={}
            stored={str(uid) for (uid,) in conn.execute(
                'SELECT instance_id FROM v106_stored_instances')}
            for uid,aid,iid in conn.execute(
                'SELECT instance_id,account_id,item_id FROM v106_item_instances'):
                if str(iid) in gear and str(uid) not in stored:
                    key=(aid,str(iid));copies[key]=copies.get(key,0)+1
            result['missing_shadow_bindings']+=sum(
                bags.get(k,0)!=copies.get(k,0) for k in bags.keys()|copies.keys())
        except (RuntimeError,ValueError,TypeError,sqlite3.Error):
            result['missing_shadow_bindings']+=1
    else:
        # Rehearse the FIRST migration on a disposable copy only. A failed
        # clone is reported as unresolved, never as a fabricated PASS.
        try:
            original_digest=_legacy_data_digest(conn)
            prepare_on_disposable_copy(conn,catalog,confirm_disposable_copy=True)
            if _legacy_data_digest(conn)!=original_digest:
                result['legacy_mutated_on_clone']+=1
            before=tuple(tuple(r) for r in conn.execute(
                'SELECT instance_id,account_id,item_id,evolution_stage,origin '
                'FROM v106_item_instances ORDER BY instance_id'))
            prepare_on_disposable_copy(conn,catalog,confirm_disposable_copy=True)
            after=tuple(tuple(r) for r in conn.execute(
                'SELECT instance_id,account_id,item_id,evolution_stage,origin '
                'FROM v106_item_instances ORDER BY instance_id'))
            if before!=after or _legacy_data_digest(conn)!=original_digest:
                result['ledger_not_idempotent']+=1
            ready=cutover_readiness(conn,catalog)
            result['ledger_rows']=ready['instance_rows']
            result['missing_shadow_bindings']=len(ready['blocking_issues'])
            result['physical_route_conflicts']=physical_route_conflicts(conn,catalog)
        except (RuntimeError,ValueError,sqlite3.Error):
            result['missing_shadow_bindings']+=1
    # Previously unseen locations and template-scoped modifiers: any positive
    # count prevents lossless physical migration, even when inventory alone is
    # consistent. A live cutover must also cover all runtime write paths.
    result.update(audit_untracked(conn,catalog))
    result['blocking_count']=sum(result[key] for key in (
        'bank_units','profession_storage_units','legacy_ambiguous',
        'worn_without_inventory','invalid_quantities','missing_shadow_bindings',
        'physical_route_conflicts',
        'pending_mail_gear_units','pending_mail_malformed',
        'housing_gear_units','housing_json_errors','ambiguous_modifiers',
        'orphaned_modifier_rows','unresolved_dynamic_units',
        'legacy_mutated_on_clone','ledger_not_idempotent'))
    # Even 0 data issues is NOT full route/ledger safety: market, mail, shop,
    # trade, drops and crafting need a verified live per-instance integration.
    result['live_per_copy_enabled']=False
    return result


def audit_live_db(source,catalog):
    source=Path(source).expanduser().resolve(strict=True)
    if source.suffix.lower() not in ('.db','.sqlite','.sqlite3','.db3'):
        raise ValueError('Podaj prawdziwy plik bazy SQLite.')
    with tempfile.TemporaryDirectory(prefix='soulbound107-eq-clone-') as home:
        target=Path(home)/'test_only.sqlite'
        with closing(sqlite3.connect(source.as_uri()+'?mode=ro',uri=True,timeout=15)) as origin:
            origin.execute('PRAGMA query_only=ON')
            with closing(sqlite3.connect(target)) as clone:
                origin.backup(clone)
        with closing(sqlite3.connect(target)) as database:
            if database.execute('PRAGMA integrity_check').fetchone()[0]!='ok':
                raise RuntimeError('Przeniesiona kopia SQLite jest niespójna.')
            report=analyze_copy(database,catalog)
            if database.execute('PRAGMA integrity_check').fetchone()[0]!='ok':
                raise RuntimeError('Testowana kopia SQLite jest niespójna po migracji.')
        return report


def main(argv=None):
    ap=argparse.ArgumentParser(description='v107 EQ: test na klonie prawdziwej SQLite')
    ap.add_argument('--db',default=os.environ.get('SOULBOUND_ULTRA_SOURCE_DB') or r'C:\Soulbound-MUD\soulbound.db')
    args=ap.parse_args(argv)
    try:
        # The full candidate registry is read-only and initialized in staging
        # from a separate Python process. No gameplay server is started.
        previous=os.environ.get('SOULBOUND_V107_STAGING')
        os.environ['SOULBOUND_V107_STAGING']='1'
        try:
            from world.dynamic_content import ITEMS
        finally:
            if previous is None:os.environ.pop('SOULBOUND_V107_STAGING',None)
            else:os.environ['SOULBOUND_V107_STAGING']=previous
        report=audit_live_db(args.db,ITEMS)
        print('V107 FIZYCZNE EQ: baza produkcyjna wyłącznie odczyt, migracja na kopii.',flush=True)
        for key in ('gear_types','inventory_units','bank_units','profession_storage_units',
                    'legacy_ambiguous','worn_without_inventory','invalid_quantities',
                    'ledger_rows','missing_shadow_bindings','physical_route_conflicts',
                    'pending_mail_gear_units','pending_mail_malformed',
                    'housing_gear_units','housing_json_errors',
                    'ambiguous_modifiers','orphaned_modifier_rows',
                    'unresolved_dynamic_units','legacy_mutated_on_clone',
                    'ledger_not_idempotent','blocking_count'):
            print(key+' = '+str(report[key]),flush=True)
        print('WYNIK: DANE ZBADANE; fizyczne EQ 2.0 nadal NIE JEST GOTOWE do produkcji.',flush=True)
        return 3 if report['blocking_count'] else 4  # never a release PASS
    except (OSError,RuntimeError,ValueError,sqlite3.Error) as exc:
        print('FAIL KLONU EQ: '+type(exc).__name__+'; przerwano bez zmiany bazy. '+
              'Szczegóły kont i przedmiotów nie są zapisywane w logu.',file=sys.stderr)
        return 2

if __name__=='__main__':raise SystemExit(main())
