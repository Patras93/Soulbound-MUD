# -*- coding: utf-8 -*-
"""Read-only offline audit of one SQLite file; no player data printed.

No automatic migrations. --db path opens SQLite read-only. Full backup and
shadow rehearsal must run separately on a disposable copy.
"""
from __future__ import annotations

import argparse
from contextlib import closing
from pathlib import Path
import sqlite3

DANGER_PERCENT = 90
COLUMNS = {
    'character_xp', 'soul_xp', 'xp', 'character_level', 'soul_level',
    'level', 'silver', 'gold', 'mithril', 'strength', 'dexterity',
    'constitution', 'intelligence', 'willpower', 'charisma',
    'max_hp', 'hp', 'damage', 'amount', 'reward_silver', 'quantity',
}
INT64_MAX=(1<<63)-1


def audit(conn: sqlite3.Connection) -> dict:
    """Report totals but never names, passwords, individual account IDs or balances."""
    integrity=conn.execute('PRAGMA integrity_check').fetchone()[0]
    if integrity!='ok':
        raise RuntimeError('SQLite integrity_check nie przeszedl.')
    report={'tables':0,'numeric_columns':0,'rows_checked':0,
            'near_int64':0,'negative_values':0,'unparseable_values':0,
            'max_decimal_digits':0,'integrity':'PASS'}
    tables=[row[0] for row in conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")]
    report['tables']=len(tables)
    for table in tables:
        if table.startswith('sqlite_'):
            continue
        cols=[]
        for _,name,dtype,*_ in conn.execute('PRAGMA table_info("'+table.replace('"','""')+'")'):
            if ('INT' in str(dtype).upper() and name in COLUMNS):
                cols.append(name)
        for col in cols:
            report['numeric_columns']+=1
            safe_table='"'+table.replace('"','""')+'"'
            safe_col='"'+col.replace('"','""')+'"'
            cursor=conn.execute(f'SELECT {safe_col} FROM {safe_table}')
            while True:
                chunk=cursor.fetchmany(2048)
                if not chunk: break
                report['rows_checked']+=len(chunk)
                for (v,) in chunk:
                    if v is None: continue
                    if type(v) is not int:
                        report['unparseable_values']+=1
                        continue
                    if v<0:report['negative_values']+=1
                    if v>=INT64_MAX*DANGER_PERCENT//100:
                        report['near_int64']+=1
                    report['max_decimal_digits']=max(report['max_decimal_digits'],len(str(v)))
    return report


def open_read_only(db_path: str):
    path=Path(db_path).expanduser().resolve(strict=True)
    if not path.is_file():raise ValueError('Nie znaleziono pliku SQLite.')
    # mode=ro prevents writes even when a user accidentally passes a live DB.
    return sqlite3.connect(path.as_uri()+'?mode=ro', uri=True)


def main(argv=None):
    parser=argparse.ArgumentParser(description='Soulbound v104: audyt SQLite tylko do odczytu.')
    parser.add_argument('--db',required=True,help='Sciezka bazy; otwierana w trybie read-only')
    args=parser.parse_args(argv)
    with closing(open_read_only(args.db)) as conn:
        report=audit(conn)
    print('AUDYT LICZB V104 (TYLKO ODCZYT):')
    for key,val in report.items():print(f'  {key}: {val}')
    if report['near_int64'] or report['negative_values'] or report['unparseable_values']:
        print('UWAGA: wymagany przeglad wskazanych kategorii; brak modyfikacji bazy.')
    else:
        print('PASS: nie wykryto zagrozen w skanowanych wartosciach; pozostale operacje SQL nadal wymagaja migracji.')


if __name__=='__main__':main()
