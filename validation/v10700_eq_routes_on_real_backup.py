# -*- coding: utf-8 -*-
"""Exercise real gear adapters on a disposable SQLite backup of v106 live data.

Never starts the server or changes the source DB. Prints aggregate verification
counts only; no private player/account/item identifiers are logged. This test is
NOT a production-activation or deployment approval.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from contextlib import closing
import os
from pathlib import Path
import sqlite3
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from storage.database import _DeferredCommitConnection
from storage.db_inventory import DatabaseInventoryMixin
from systems.equipment_shadow_slots_v10600 import prepare_on_disposable_copy, _check_account
from systems.v10700_equipment_write_barrier import install_on_migrated_connection
from validation.v10700_eq_ledger_live_clone import analyze_copy, _legacy_data_digest


def _physical_digest(conn):
    """Compare full affected-table content before and after SAVEPOINT rollback."""
    digest=hashlib.sha256()
    existing={str(row[0]) for row in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'")}
    for table in ('inventory','equipment','bank_items','profession_storage',
                  'player_records_v03051','shop_purchase_lots_v1175',
                  'v106_item_instances','v106_equipped_instances',
                  'v106_stored_instances','v106_evolution_migration_issues',
                  'v106_mail_equipment_escrow','player_mail_v03051'):
        if table not in existing:
            continue
        digest.update(table.encode('ascii'))
        rows=list(conn.execute('SELECT * FROM "'+table+'"'))
        values=sorted(json.dumps(tuple(row),default=str,ensure_ascii=False,sort_keys=True)
                      for row in rows)
        for value in values:
            digest.update(value.encode('utf-8'))
            digest.update(b'\n')
    return digest.digest()


class GearTestDB(DatabaseInventoryMixin):
    def __init__(self, conn, catalog):
        self.conn=conn
        self._v106_shadow_slots_disposable_copy=True
        self._v106_shadow_item_catalog=catalog
        self._v106_bank_shadow_disposable_copy=True
        self._v106_storage_shadow_disposable_copy=True
        self._v106_mail_shadow_disposable_copy=True


def exercise_clone(connection, catalog):
    """May only be called with a copied/temporary database connection."""
    conn=connection
    report=analyze_copy(conn,catalog)
    if report['blocking_count']:
        raise RuntimeError('Zatrzymano: niespójne dane fizycznych kopii')
    db=GearTestDB(conn,catalog)
    installed=install_on_migrated_connection(db,catalog,approved_test_copy=True)
    if installed!=report['gear_types']:
        raise RuntimeError('Katalog sprzętu zmienił się między audytem a testem')
    gear=[str(iid) for iid,item in catalog.items() if isinstance(item,dict) and item.get('type')=='armor']
    if not gear:
        raise RuntimeError('Brak pancerzy do testów transakcyjnych')
    # Never expose real IDs. Use a new, absent template for an existing account.
    rows=conn.execute('SELECT id FROM accounts ORDER BY id').fetchall()
    if len(rows)<2:
        raise RuntimeError('Test wymaga co najmniej dwóch istniejących kont w kopii')
    account_a=int(rows[0][0]);account_b=int(rows[1][0]);item_id=None
    for candidate in gear:
        if all(conn.execute('SELECT 1 FROM inventory WHERE account_id=? AND item_id=?',
                            (account,candidate)).fetchone() is None for account in (account_a,account_b)):
            item_id=candidate
            break
    if item_id is None:
        raise RuntimeError('Brak wolnego wzorca pancerza do testu na kopii')
    from systems.equipment_evolution_v10500 import required_materials
    from systems.equipment_evolution_stats_v10600 import evolve_equipped_copy_on_disposable_test
    checks=0
    old=_legacy_data_digest(conn)
    physical_before=_physical_digest(conn)
    conn.execute('SAVEPOINT v107_test_rehearsal_rollback')
    try:
        def check(value):
            nonlocal checks
            if not value:
                raise RuntimeError('Niespójność operacji fizycznego EQ w kopii')
            checks+=1
        check(not getattr(conn,'_v107_eq_write_depth',0))
        try:
            conn.execute('INSERT INTO inventory(account_id,item_id,quantity) VALUES(?,?,1)',
                         (account_a,item_id))
        except sqlite3.DatabaseError:
            checks+=1
        else:
            raise RuntimeError('Stary zapis SQL ominął fizyczny rejestr')
        db.add_item(account_a,item_id,3,commit=False)
        check(db.item_qty(account_a,item_id)==3)
        ids={str(r[0]) for r in conn.execute('SELECT instance_id FROM v106_item_instances '
                'WHERE account_id=? AND item_id=?',(account_a,item_id))}
        check(len(ids)==3)
        db.equip(account_a,'v107_test_temporary_slot',item_id,commit=False)
        worn=conn.execute('SELECT instance_id FROM v106_equipped_instances '
                          'WHERE account_id=? AND slot=?',(account_a,'v107_test_temporary_slot')).fetchone()
        check(worn is not None and str(worn[0]) in ids)
        check(db.remove_item(account_a,item_id,3,commit=False) is False)
        check(db.transfer_inventory_item(account_a,account_b,item_id,1) is True)
        check(db.item_qty(account_a,item_id)==2 and db.item_qty(account_b,item_id)==1)
        _check_account(conn,account_a,catalog);_check_account(conn,account_b,catalog)
        check(db.move_bank_equipment_v106(account_b,item_id,1,commit=False))
        check(db.item_qty(account_b,item_id)==0 and db.bank_item_qty(account_b,item_id)==1)
        check(db.move_bank_equipment_v106(account_b,item_id,1,withdraw=True,commit=False))
        check(db.item_qty(account_b,item_id)==1 and db.bank_item_qty(account_b,item_id)==0)
        check(db.move_storage_equipment_v106(account_b,'craftbox',item_id,1,commit=False))
        check(db.item_qty(account_b,item_id)==0 and db.storage_qty(account_b,'craftbox',item_id)==1)
        check(db.move_storage_equipment_v106(account_b,'craftbox',item_id,1,withdraw=True,commit=False))
        check(db.item_qty(account_b,item_id)==1 and db.storage_qty(account_b,'craftbox',item_id)==0)
        # The exact stage changes only on the chosen worn copy. All materials,
        # inventory and stage changes are reverted by the outer test SAVEPOINT.
        for material,amount in required_materials(1).items():
            conn.execute('INSERT INTO profession_storage(account_id,container,item_id,quantity) '
                         'VALUES(?,?,?,?) ON CONFLICT(account_id,container,item_id) '
                         'DO UPDATE SET quantity=quantity+excluded.quantity',
                         (account_a,'craftbox',material,amount))
        evolved, stage=evolve_equipped_copy_on_disposable_test(
            db,account_a,'v107_test_temporary_slot',str(worn[0]),
            confirm_disposable_copy=True,commit=False)
        check(evolved and stage==1)
        check(conn.execute('SELECT evolution_stage FROM v106_item_instances '
                           'WHERE instance_id=?',(str(worn[0]),)).fetchone()[0]==1)
        check(db.remove_item(account_a,item_id,1,commit=False) is True)
        check(conn.execute('PRAGMA integrity_check').fetchone()[0]=='ok')
        check(not getattr(conn,'_v107_eq_write_depth',0))
    finally:
        conn.execute('ROLLBACK TO SAVEPOINT v107_test_rehearsal_rollback')
        conn.execute('RELEASE SAVEPOINT v107_test_rehearsal_rollback')
    if _legacy_data_digest(conn)!=old or _physical_digest(conn)!=physical_before:
        raise RuntimeError('Test nie cofnął wszystkich zmian wyposażenia i danych historycznych')
    if conn.execute('PRAGMA integrity_check').fetchone()[0]!='ok':
        raise RuntimeError('Integralność SQLite nie została przywrócona')
    return checks


def audit_readonly(source,catalog):
    source=Path(source).expanduser().resolve(strict=True)
    if source.suffix.lower() not in ('.db','.sqlite','.sqlite3','.db3'):
        raise ValueError('Nieobsługiwana nazwa bazy SQLite')
    with tempfile.TemporaryDirectory(prefix='v107-physical-routes-') as directory:
        clone=Path(directory)/'disposable.db'
        with closing(sqlite3.connect(source.as_uri()+'?mode=ro',uri=True,timeout=15)) as original:
            original.execute('PRAGMA query_only=ON')
            with closing(sqlite3.connect(clone)) as target:
                original.backup(target)
        raw=sqlite3.connect(clone)
        raw.row_factory=sqlite3.Row
        raw.execute('PRAGMA foreign_keys=ON')
        db=_DeferredCommitConnection(raw)
        try:
            result=exercise_clone(db,catalog)
        finally:
            db.close()
    return result


def main(argv=None):
    parser=argparse.ArgumentParser()
    parser.add_argument('--db',default=os.environ.get('SOULBOUND_ULTRA_SOURCE_DB') or r'C:\Soulbound-MUD\soulbound.db')
    args=parser.parse_args(argv)
    prior=os.environ.get('SOULBOUND_V106_STAGING')
    os.environ['SOULBOUND_V106_STAGING']='1'
    try:
        from world.dynamic_content import ITEMS
        count=audit_readonly(args.db,ITEMS)
        print('V107 EQ OPERACJE NA KOPII: '+str(count)+' kontroli PASS, źródło bez zmian.')
        print('WYNIK: TEST KODU, NIE POZWALA NA WDROZENIE.')
        return 0
    except Exception as exc:
        # Deliberately never include exception text that may leak player/item IDs.
        print('V107 EQ OPERACJE NA KOPII: FAIL ('+type(exc).__name__+').',file=sys.stderr)
        return 3
    finally:
        if prior is None:os.environ.pop('SOULBOUND_V106_STAGING',None)
        else:os.environ['SOULBOUND_V106_STAGING']=prior

if __name__=='__main__':raise SystemExit(main())
