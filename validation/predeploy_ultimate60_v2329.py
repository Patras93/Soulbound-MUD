# -*- coding: utf-8 -*-
"""Ten independently failing predeploy gates 51-60; no production writes.

The additional suite reuses assertion-bearing real game regression scripts where
possible. Case 60 checks migration safety for an independently cloned current DB.
"""
from __future__ import annotations
import argparse
from contextlib import closing
import hashlib
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))

REGRESSIONS={
    51: ('REJESTR KOMEND - ENUMERACJA I ROUTING', 'validation.v2302_exhaustive_game_coverage', "import server,runpy;runpy.run_module('validation.v2302_exhaustive_game_coverage',run_name='__main__')"),
    52: ('ZLECENIA LOWCOW - POSTEP GRUPY I NAJEMNICY', 'validation.hunters_mercenaries_v12212', None),
    53: ('WYSOKIE LOCHY - SKALOWANIE I PRZEZYWALNOSC', 'validation.v2325_deep_dungeon_pressure', None),
    54: ('PORTALE - CHECKPOINT I PRAWA DRUZYNY', 'validation.v2010_unlocked_portals', None),
    55: ('ZAMOWIENIA - RECEPTURY I NAGRODY', 'validation.v1406_orders_regression',
         "import server;from validation.v1406_orders_regression import run_orders_regression_v1406 as f;print(f())"),
    56: ('ODKRYWANIE I BAZA - TRWALOSC', 'validation.v2322_auto_exploration', None),
    57: ('ZADANIA KLASOWE - CZAS I ODNAWIANIE', 'validation.v1289_class_quest_cadence', None),
    58: ('GILDIE - POZIOMY I KOSZTY', 'validation.v1710_guild800', None),
    59: ('PRZYWOLANIA I DRUZYNA - LECZENIE', 'validation.v1711_companion_healing', None),
}

def regression(n):
    title,mod,script=REGRESSIONS[n]
    path=ROOT.joinpath(*mod.split('.')).with_suffix('.py')
    if not path.is_file():
        raise AssertionError(f'{title}: brak {path.relative_to(ROOT)}')
    cmd=[sys.executable,'-u','-c',script] if script else [sys.executable,'-u','-m',mod]
    result=subprocess.run(cmd,cwd=ROOT,stdin=subprocess.DEVNULL,capture_output=True,
                          text=True,encoding='utf-8',errors='replace',timeout=220)
    output=(result.stdout+'\n'+result.stderr).strip()
    if output:
        print(output[-11000:],flush=True)
    if result.returncode:
        raise AssertionError(f'{title}: blad, exit={result.returncode}')
    if not output.strip():
        raise AssertionError(f'{title}: tester nie wypisal wyniku, mozliwy pusty test')
    print(f'{title}: osobna regresja PASS',flush=True)


def schema_and_data_preserved():
    """Backup the live DB read-only; migrate the clone with candidate code.

    All pre-existing rows must survive unchanged for releases with no game-data
    migration; intentional data transformations must update this contract with
    explicit assertions, not silently drop checks.
    """
    source=os.environ.get('SOULBOUND_ULTRA_SOURCE_DB','').strip()
    if not source or not Path(source).is_file():
        raise AssertionError('Brak dostepnej bazy do testu migracji (SOURCE_DB)')
    with tempfile.TemporaryDirectory(prefix='sb-ultimate60-clone-') as td:
        path=Path(td)/'candidate.sqlite'
        uri=Path(source).resolve().as_uri()+'?mode=ro'
        with closing(sqlite3.connect(uri,uri=True,timeout=25)) as src:
            if src.execute('PRAGMA integrity_check').fetchone()[0]!='ok':
                raise AssertionError('Baza zrodlowa nie spelnia integrity_check')
            with closing(sqlite3.connect(path)) as dst:
                src.backup(dst)
        def snapshot(conn):
            tables={r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
            result={}
            for table in sorted(tables):
                identifier='"'+table.replace('"','""')+'"'
                h=hashlib.sha256()
                rows=0
                # Comparison independent of rowid and naturally insensitive to row order.
                items=[]
                for values in conn.execute('SELECT * FROM '+identifier):
                    items.append(repr(tuple(values)).encode('utf-8','backslashreplace'))
                for item in sorted(items):
                    h.update(len(item).to_bytes(8,'big')+item)
                    rows+=1
                result[table]=(rows,h.hexdigest())
            return result
        def schema_objects(conn):
            # Keep existing indexes/triggers/views and all existing column contracts.
            objects = { (kind, name): statement for kind, name, statement in
                conn.execute("SELECT type,name,sql FROM sqlite_master "
                             "WHERE type IN ('view','trigger','index') AND name NOT LIKE 'sqlite_%'") }
            columns = {}
            for table in (r[0] for r in conn.execute(
                    "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")):
                safe = table.replace('"', '""')
                columns[table] = [(x[1],x[2],x[3],x[5]) for x in
                                  conn.execute(f'PRAGMA table_info("{safe}")')]
            return objects, columns
        with closing(sqlite3.connect(path)) as db:
            before=snapshot(db)
            objects_before, columns_before = schema_objects(db)
        # Run this candidate's actual schema migration on the clone (not the source).
        os.environ['SOULBOUND_DB']=str(path)
        os.environ['SOULBOUND_HOST']='127.0.0.1'
        os.environ['SOULBOUND_WORLD_SEED_FILE']=str(Path(td)/'seed.txt')
        import server
        from storage.database import Database
        d=Database(str(path))
        try:
            if d.conn.execute('PRAGMA integrity_check').fetchone()[0]!='ok':
                raise AssertionError('Integrity check po migracji FAIL')
            issues=d.conn.execute('PRAGMA foreign_key_check').fetchall()
            if issues:
                raise AssertionError('Foreign keys po migracji: '+str(issues[:5]))
            after=snapshot(d.conn)
            objects_after, columns_after = schema_objects(d.conn)
            deleted_objects = sorted(k for k,v in objects_before.items()
                                     if objects_after.get(k) != v)
            broken_columns = sorted(table for table, cols in columns_before.items()
                                    if table not in columns_after or
                                    any(col not in columns_after[table] for col in cols))
            if deleted_objects or broken_columns:
                raise AssertionError('SQLITE SCHEMA DRIFT: objects '+str(deleted_objects[:8])
                                     +'; existing columns '+str(broken_columns[:8]))
            lost=sorted(set(before)-set(after))
            changed=[t for t in before if before[t]!=after.get(t)]
            if lost or changed:
                raise AssertionError('Nieautoryzowana zmiana danych; usuniete tabele: '
                                     +str(lost[:12])+'; zmienione tabele: '+str(changed[:12]))
        finally:
            d.conn.close()
    print(f'Migracja kopii SQLite: {len(before)} tabel, zachowane indeksy/triggery/widoki i kolumny, bez zmiany wierszy, FK PASS',flush=True)

CASES={60:schema_and_data_preserved}

def main():
    p=argparse.ArgumentParser()
    p.add_argument('--case',required=True,type=int)
    n=p.parse_args().case
    if n in REGRESSIONS:regression(n)
    elif n in CASES:CASES[n]()
    else:raise ValueError('Nieznany etap ULTIMATE 60: '+str(n))
    print(f'ULTIMATE CASE {n}/60 PASS',flush=True)

if __name__=='__main__':main()
