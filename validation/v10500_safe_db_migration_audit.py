# -*- coding: utf-8 -*-
"""Soulbound v105: non-destructive migration rehearsal of a v104 SQLite DB.

Only opens input DB with SQLite mode=ro; all writes and migration calls target
an SQLite backup inside TemporaryDirectory.  Not a substitute for Windows
PREDEPLOY 60/60 PLUS on the exact final release archive.
"""
from __future__ import annotations

import argparse
from contextlib import closing
from hashlib import sha256
import sqlite3
from pathlib import Path
from tempfile import TemporaryDirectory

# Only persisted PLAYER-owned tables, not derived catalogs/ever-changing schema.
PROTECTED = (
    'accounts', 'characters', 'quests', 'inventory', 'equipment',
    'player_records_v03051', 'equipment_runes_v0925',
    'equipment_reforges', 'equipment_upgrades_v03042',
    'equipment_socket_bonus_v03114', 'profession_storage',
    'account_wallet', 'class_progress', 'professions', 'tools',
)


def fingerprint(db):
    """Per-table sha256 of *all* rows, stable across VACUUM/SQLite row order."""
    summary={}
    for table in PROTECTED:
        if not db.execute('SELECT 1 FROM sqlite_master WHERE type=? AND name=?',
                          ('table', table)).fetchone():
            continue
        columns=[c[1] for c in db.execute(f'PRAGMA table_info("{table}")')]
        if not columns:
            raise ValueError('Brak kolumn tabeli: '+table)
        # Sorting by the entire row avoids assuming a rowid in WITHOUT ROWID tables.
        # SQLite compares each column by its declared affinity; hash encoded row
        # values without converting EXP to floats or summing huge numbers.
        quoted=','.join('"'+c.replace('"','""')+'"' for c in columns)
        h=sha256(repr(tuple(columns)).encode('utf-8'))
        count=0
        for row in db.execute(f'SELECT {quoted} FROM "{table}" ORDER BY {quoted}'):
            values=tuple(row)
            encoded=repr(values).encode('utf-8',errors='surrogatepass')
            h.update(len(encoded).to_bytes(8,'big'));h.update(encoded)
            count+=1
        summary[table]=(count,h.hexdigest())
    return summary


def rehearse(input_path):
    path=Path(input_path).expanduser().resolve(strict=True)
    if not path.is_file() or path.suffix.lower() not in ('.db','.sqlite','.sqlite3'):
        raise ValueError('Podaj ścieżkę do bazy SQLite .db/.sqlite/.sqlite3.')
    from storage.database import Database
    source_uri=path.as_uri()+'?mode=ro'
    with closing(sqlite3.connect(source_uri,uri=True)) as original:
        original.execute('PRAGMA query_only=ON')
        with TemporaryDirectory(prefix='sb105_migration_readonly_') as temp:
            snapshot=Path(temp)/'rehearsal.sqlite'
            with closing(sqlite3.connect(snapshot)) as target:
                original.backup(target)
            with closing(sqlite3.connect(snapshot)) as before_db:
                before=fingerprint(before_db)
                if before_db.execute('PRAGMA quick_check').fetchone()[0]!='ok':
                    raise ValueError('Wejściowy snapshot SQLite jest uszkodzony.')
            if 'characters' not in before or 'quests' not in before:
                raise ValueError('Brak wymaganych tabel postaci/questów: to nie jest poprawna baza Soulbound.')
            # This is the identical v105 schema startup applied to a BACKUP,
            # never to the source file. Close/reopen to prove persistency.
            test_db=Database(str(snapshot))
            test_db.conn.close()
            with closing(sqlite3.connect(snapshot)) as migrated:
                after=fingerprint(migrated)
                if migrated.execute('PRAGMA integrity_check').fetchone()[0]!='ok':
                    raise AssertionError('Integralność kopii po migracji: FAIL.')
            changes={name:(before.get(name),after.get(name)) for name in before if before[name]!=after.get(name)}
            if changes:
                raise AssertionError('Migracja zmieniła dane graczy: '+', '.join(changes))
            # Repeated startup may add only schema metadata, never mutate
            # existing player records or earned quest progress.
            test_db=Database(str(snapshot))
            test_db.conn.close()
            with closing(sqlite3.connect(snapshot)) as repeated:
                if fingerprint(repeated)!=after:
                    raise AssertionError('Powtórna migracja nie jest idempotentna.')
                if repeated.execute('PRAGMA integrity_check').fetchone()[0]!='ok':
                    raise AssertionError('Powtórna migracja: SQLite FAIL.')
            return {'tables':len(before),'accounts':before.get('accounts',(0,))[0],
                    'characters':before.get('characters',(0,))[0],
                    'quests':before.get('quests',(0,))[0],
                    'sqlite':'PASS', 'player_records_unchanged':True,
                    'repeated_startup':'PASS', 'original_mode':'read-only'}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description='V105 migracja bazy: tylko odczyt oryginału, zapis do TEMP')
    parser.add_argument('--db',required=True,help='ścieżka do bazy istniejącego Soulbound')
    args=parser.parse_args()
    print('V105 MIGRACJA SQLITE: '+repr(rehearse(args.db)),flush=True)
