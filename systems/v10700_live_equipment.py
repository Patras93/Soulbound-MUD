# -*- coding: utf-8 -*-
"""v107 approved physical-EQ activation, with persistent rollback snapshot.

This function is called ONLY after server boot has registered dynamic gear,
AND only after v107 release activation has verified 60/60 PLUS and exact
candidate source hashes. Never run this against a live source while players
are connected. On an error it aborts startup rather than inferring item IDs.
"""
from __future__ import annotations

from contextlib import closing
from pathlib import Path
from datetime import datetime, timezone
import os
import sqlite3
import tempfile

from systems.equipment_shadow_slots_v10600 import prepare_on_disposable_copy, _check_account
from systems.v10700_equipment_write_barrier import install_on_migrated_connection


def _require_approved():
    from systems.v10700_activation import production_approved
    if not production_approved():
        raise PermissionError('EQ v107: brak autoryzowanego pełnego PREDEPLOY')


def _check_all_accounts(conn, catalog):
    accounts={int(row[0]) for row in conn.execute('SELECT account_id FROM equipment')}
    accounts.update(int(row[0]) for row in conn.execute('SELECT DISTINCT account_id FROM inventory'))
    accounts.update(int(row[0]) for row in conn.execute('SELECT DISTINCT account_id FROM v106_item_instances'))
    accounts.update(int(row[0]) for row in conn.execute('SELECT DISTINCT account_id FROM v106_stored_instances'))
    # Cover shadow-only accounts whose physical UID/legacy equipment row vanished.
    # No automatic repairs: the existing _check_account fails closed.
    accounts.update(int(row[0]) for row in conn.execute('SELECT DISTINCT account_id FROM v106_equipped_instances'))
    for aid in sorted(accounts):
        _check_account(conn,aid,catalog)


def _backup_and_check(conn, catalog, output):
    """Never rehearse on the immutable rollback backup itself."""
    from validation.v10700_eq_ledger_live_clone import analyze_copy
    raw=getattr(conn,'_connection',conn)
    with closing(sqlite3.connect(output)) as rollback_backup:
        raw.backup(rollback_backup)
        if rollback_backup.execute('PRAGMA integrity_check').fetchone()[0]!='ok':
            raise RuntimeError('EQ v107: kopia cofania uszkodzona')
    fd,temporary=tempfile.mkstemp(prefix='sb107_eq_rehearsal_',suffix='.sqlite',
                                 dir=Path(output).parent)
    os.close(fd)
    try:
        with closing(sqlite3.connect(temporary)) as rehearsal:
            with closing(sqlite3.connect(Path(output).as_uri()+'?mode=ro',uri=True)) as origin:
                origin.backup(rehearsal)
            report=analyze_copy(rehearsal,catalog)
            if rehearsal.execute('PRAGMA integrity_check').fetchone()[0]!='ok':
                raise RuntimeError('EQ v107: migracja próby uszkodziła SQLite')
        return report
    finally:
        Path(temporary).unlink(missing_ok=True)


def activate_production_ledger(db, catalog):
    """Fail-closed one-time live conversion, never callable from staging flags.

    A persistent backup is made and rehearsed BEFORE any live migration. After
    a successful one-time conversion, future boots validate instead of
    recreating IDs or resetting evolved stages. Each connection gets its own
    TEMP SQL write barrier; a module flag alone never permits legacy writes.
    """
    _require_approved()
    if db.conn.in_transaction:
        raise RuntimeError('EQ v107: niezakończona transakcja przed migracją')
    if getattr(db,'_v107_eq_live_active',False):
        raise RuntimeError('EQ v107: podwójna inicjalizacja')
    if not isinstance(catalog,dict) or not catalog:
        raise RuntimeError('EQ v107: brak zainicjowanego katalogu')
    if db.path==':memory:':
        raise PermissionError('EQ v107: migracja wymaga trwałej bazy SQLite')
    conn=db.conn
    marker=conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' "
                        "AND name='v107_eq_production_cutover'").fetchone()
    if marker is not None:
        rows=conn.execute('SELECT cutover_version,backup_name FROM v107_eq_production_cutover').fetchall()
        if len(rows)!=1 or rows[0][0]!='107.00.0':
            raise RuntimeError('EQ v107: nieznany lub uszkodzony znacznik migracji')
        backup=Path(db.path).resolve().parent/'backups'/rows[0][1]
        if not backup.is_file():
            raise RuntimeError('EQ v107: zaginęła migawka umożliwiająca wycofanie')
        _check_all_accounts(conn,catalog)
    else:
        # Database must be idle before copying; do not race against players.
        home=Path(db.path).resolve().parent/'backups'
        home.mkdir(parents=True,exist_ok=True)
        fd,filename=tempfile.mkstemp(prefix='soulbound_v106_before_eq107_',suffix='.sqlite',dir=home)
        os.close(fd)
        backup=Path(filename)
        try:
            _backup_and_check(conn,catalog,backup)
        except BaseException:
            backup.unlink(missing_ok=True)
            raise
        # No migration until the independently backed-up database is verified.
        conn.execute('SAVEPOINT sb107_eq_live_cutover')
        try:
            prepare_on_disposable_copy(conn,catalog,confirm_disposable_copy=True)
            _check_all_accounts(conn,catalog)
            conn.execute('''CREATE TABLE v107_eq_production_cutover (
                cutover_version TEXT NOT NULL PRIMARY KEY,
                backup_name TEXT NOT NULL,
                cutover_utc TEXT NOT NULL
            )''')
            conn.execute('INSERT INTO v107_eq_production_cutover VALUES(?,?,?)',(
                '107.00.0',backup.name,datetime.now(timezone.utc).isoformat()))
            conn.execute('RELEASE SAVEPOINT sb107_eq_live_cutover')
            conn.commit()
        except BaseException:
            conn.execute('ROLLBACK TO SAVEPOINT sb107_eq_live_cutover')
            conn.execute('RELEASE SAVEPOINT sb107_eq_live_cutover')
            conn.rollback()
            raise
    # Precreate escrow before TEMP barriers are installed. Future mail SQL
    # cannot create an unguarded identity table after player logins begin.
    from systems.equipment_mail_v10600 import _schema as _ensure_mail_escrow
    _ensure_mail_escrow(conn)
    conn.commit()
    db._v106_shadow_item_catalog=catalog
    db._v106_shadow_slots_disposable_copy=True  # older adapter compatibility
    db._v106_bank_shadow_disposable_copy=True
    db._v106_storage_shadow_disposable_copy=True
    db._v106_mail_shadow_disposable_copy=True
    db._v107_eq_migration_committed=True
    db._v107_eq_live_active=True
    try:
        install_on_migrated_connection(db,catalog,approved_test_copy=False)
    except BaseException:
        db._v107_eq_live_active=False
        db._v107_eq_migration_committed=False
        raise
    return True


def production_copy_evolution(db, account_id, slot, instance_id):
    """Only a released live session can evolve one exact worn physical copy."""
    _require_approved()
    if (not getattr(db,'_v107_eq_live_active',False)
            or not getattr(db,'_v107_eq_migration_committed',False)
            or not getattr(db.conn,'_v107_eq_write_barrier_active',False)):
        raise PermissionError('EQ v107: brak aktywnego rejestru z ochroną SQLite')
    from systems.equipment_evolution_stats_v10600 import evolve_equipped_copy_on_disposable_test
    return evolve_equipped_copy_on_disposable_test(
        db,account_id,slot,instance_id,confirm_disposable_copy=False)
