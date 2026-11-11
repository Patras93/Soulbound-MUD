# -*- coding: utf-8 -*-
"""Weryfikacja prawdziwej bazy EQ tylko na jej przejściowej kopii.

Nigdy nie otwiera oryginału w trybie zapisu. Nie włącza fizycznych kopii EQ
w działającej grze. Ambiwalentne/zdublowane historie ewolucji blokują wydanie.
"""
from __future__ import annotations
import argparse
from contextlib import closing
import os
from pathlib import Path
import sqlite3
import sys
import tempfile

# Windows PREDEPLOY launches this file by its path, not with ``python -m``.
# In that mode sys.path[0] points to validation/, so import systems/ fails.
# Resolve only the staged candidate root; never load modules from installed v105.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from systems.equipment_instances_v10600 import apply_to_explicit_test_copy, cutover_readiness


def verify(source):
    source=Path(source).expanduser().resolve(strict=True)
    if not source.is_file() or source.suffix.lower() not in ('.db','.sqlite','.sqlite3','.db3'):
        raise ValueError('Wymagana istniejąca baza SQLite; nie podano katalogu ani kopii pliku ZIP.')
    with tempfile.TemporaryDirectory(prefix='soulbound-v106-kopia-eq-') as tmp:
        dest=Path(tmp)/'KOPIA_TYLKO_TEST.sqlite'
        uri=source.as_uri()+'?mode=ro'
        with closing(sqlite3.connect(uri,uri=True,timeout=20)) as src:
            src.execute('PRAGMA query_only=ON')
            with closing(sqlite3.connect(dest)) as dst:
                src.backup(dst)
        with closing(sqlite3.connect(dest)) as clone:
            if clone.execute('PRAGMA integrity_check').fetchone()[0]!='ok':
                raise RuntimeError('Kopia SQLite jest niespójna: PRAGMA integrity_check FAIL')
            have={row[0] for row in clone.execute('SELECT name FROM sqlite_master WHERE type="table"')}
            required={'accounts','characters','inventory','equipment','player_records_v03051'}
            missing=required-have
            if missing:
                raise RuntimeError('Brak tabel wymaganych w migracji: '+', '.join(sorted(missing)))
            # CATALOG IS READ-ONLY. The staged v106 registry is needed to detect
            # both historical and proposed equipment item definitions.
            old=os.environ.get('SOULBOUND_V106_STAGING')
            os.environ['SOULBOUND_V106_STAGING']='1'
            try:
                from world.dynamic_content import ITEMS
            finally:
                if old is None:os.environ.pop('SOULBOUND_V106_STAGING',None)
                else:os.environ['SOULBOUND_V106_STAGING']=old
            before={table:clone.execute('SELECT COUNT(*) FROM '+table).fetchone()[0]
                    for table in required}
            result=apply_to_explicit_test_copy(clone,ITEMS,confirm_disposable_copy=True)
            ready=cutover_readiness(clone,ITEMS)
            if clone.execute('PRAGMA integrity_check').fetchone()[0]!='ok':
                raise RuntimeError('Kopia SQLite uszkodzona przez symulację migracji')
            after={table:clone.execute('SELECT COUNT(*) FROM '+table).fetchone()[0]
                   for table in required}
            if before!=after:
                raise AssertionError('Migracja zmieniła historyczne konta, postaci albo EQ na kopii')
            print('SQLITE: kopia LIVE wykonana w trybie read-only, integralność PASS',flush=True)
            print('Historyczne tabele / liczba rekordów: '+str(before),flush=True)
            print('Migracja kopii: '+str(result),flush=True)
            print('Kontrakt EQ: inspekcja='+str(ready['snapshot_items'])+
                  ', utworzone instancje='+str(ready['instance_rows'])+
                  ', niejednoznaczności='+str(len(ready['blocking_issues'])),flush=True)
            # Never print account identifiers or personal equipment in logs.
            if ready['snapshot_items']==0 and (before['inventory']>0 or before['equipment']>0):
                print('FAIL: obecne EQ nie zostało rozpoznane przez katalog; wymaga audytu.',flush=True)
                return 1
            if not ready['data_consistent']:
                print('FAIL: manualna rekonsyliacja historii kopii EQ konieczna. NIE WDRAŻAĆ.',flush=True)
                return 1
            print('PASS danych migrowanych na KOPII. NIE jest to zgoda na włączenie runtime EQ.',flush=True)
            assert not ready['gameplay_ready'], 'Nieoczekiwana autoryzacja fizycznego EQ'
            return 0


def main():
    ap=argparse.ArgumentParser(description='Kopia EQ v106: tylko odczyt produkcji, bez wdrażania')
    ap.add_argument('--db',default=os.environ.get('SOULBOUND_ULTRA_SOURCE_DB'),
                    help='Scieżka do prawdziwej bazy soulbound.db')
    args=ap.parse_args()
    if not args.db:
        print('FAIL: Brak bazy, użyj --db C:\\Soulbound-MUD\\soulbound.db',file=sys.stderr)
        return 2
    try: return verify(args.db)
    except (OSError,sqlite3.Error,ValueError,RuntimeError,AssertionError) as exc:
        print('FAIL BEZPIECZNEJ MIGRACJI NA KOPII: '+type(exc).__name__+': '+str(exc),file=sys.stderr)
        return 2

if __name__=='__main__':raise SystemExit(main())
