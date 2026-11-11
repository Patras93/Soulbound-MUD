# -*- coding: utf-8 -*-
"""v108 Windows gate: preserve v107 player equipment, no v108 EQ 2.0 migration.

The PREDEPLOY harness MUST supply a detached WAL-consistent snapshot.  This
checker never writes to it, and never creates physical items or shadow IDs.
Unlike the cancelled EQ 2.0 reconciliation gate, it does not require upgrading
inventory to a *new* physical ledger, but it MUST prove v107 can restart.
"""
from __future__ import annotations
from pathlib import Path
from contextlib import closing
import os
import sqlite3
import sys

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))


def audit_read_only(source):
    path=Path(source).resolve(strict=True)
    if path.is_symlink() or not path.is_file() or not path.name.endswith('.sqlite'):
        raise RuntimeError('Brak odłączonej migawki SQLite')
    with closing(sqlite3.connect(path.as_uri()+'?mode=ro',uri=True)) as db:
        db.execute('PRAGMA query_only=ON')
        if db.execute('PRAGMA integrity_check').fetchone()[0]!='ok':
            raise RuntimeError('Niepoprawna integralność obrazu v107')
        tables={r[0] for r in db.execute('SELECT name FROM sqlite_master WHERE type="table"')}
        required={'v107_eq_production_cutover','v106_item_instances',
                  'v106_equipped_instances','inventory','equipment',
                  'v106_stored_instances'}
        if not required<=tables:
            raise RuntimeError('Brak wymaganych tabel istniejącego EQ v107')
        if 'v108_eq_production_cutover' in tables:
            raise RuntimeError('Nieoczekiwana migracja EQ v108 mimo wycofania funkcji')
        rows=db.execute('SELECT cutover_version,backup_name FROM v107_eq_production_cutover').fetchall()
        if len(rows)!=1 or rows[0][0]!='107.00.0' or not rows[0][1]:
            raise RuntimeError('Nieprawidłowy dotychczasowy znacznik EQ v107')
        # Do not silently ship a version that cannot pass the existing v107
        # startup guard.  The check must be read-only and count both bag and
        # worn-slot consistency. No reconciliation, stage changes or SQL writes.
        previous=os.environ.get('SOULBOUND_V107_STAGING')
        os.environ['SOULBOUND_V107_STAGING']='1'
        try:
            from world.dynamic_content import ITEMS
            from systems.v10700_live_equipment import _check_all_accounts
            _check_all_accounts(db, ITEMS)
        finally:
            if previous is None:os.environ.pop('SOULBOUND_V107_STAGING',None)
            else:os.environ['SOULBOUND_V107_STAGING']=previous
        return db.execute('SELECT COUNT(*) FROM v106_item_instances').fetchone()[0]


def main():
    source=os.environ.get('SOULBOUND_ULTRA_SOURCE_DB','')
    if not source:
        print('V108 v107 EQ: BRAK ODŁĄCZONEJ MIGAWKI; FAIL',flush=True)
        return 3
    try:
        count=audit_read_only(source)
        print('V108 BEZ EQ 2.0: OCHRONA DANYCH V107 PASS; istniejących kopii: '+str(count)+
              '; brak migracji, brak zapisów.',flush=True)
        return 0
    except Exception as exc:
        # Details are read-only and aggregate-only. An error in diagnostics
        # must NEVER turn an existing FAIL into a successful release.
        try:
            from validation.v10800_v107_drift_details_ro import classify_snapshot, safe_summary
            path=Path(source).resolve(strict=True)
            if path.is_file() and path.suffix.lower()=='.sqlite':
                with closing(sqlite3.connect(path.as_uri()+'?mode=ro',uri=True)) as db:
                    db.execute('PRAGMA query_only=ON')
                    previous=os.environ.get('SOULBOUND_V107_STAGING')
                    os.environ['SOULBOUND_V107_STAGING']='1'
                    try:
                        from world.dynamic_content import ITEMS
                        info=classify_snapshot(db,ITEMS)
                        print('V108 V107 EQ - DIAGNOSTYKA TYLKO ODCZYT: '+safe_summary(info),flush=True)
                    finally:
                        if previous is None:os.environ.pop('SOULBOUND_V107_STAGING',None)
                        else:os.environ['SOULBOUND_V107_STAGING']=previous
        except Exception:
            print('V108 V107 EQ - SZCZEGOLY NIEDOSTEPNE; BRAK ZGODY NA WDROZENIE',flush=True)
        print('V108 BEZ EQ 2.0: NIE WDRAZAJ. Istniejące dane v107 wymagają '
              'zgodności przed restartem: '+type(exc).__name__,flush=True)
        return 3


if __name__=='__main__':
    raise SystemExit(main())
