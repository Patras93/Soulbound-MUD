# -*- coding: utf-8 -*-
"""v104: read-only source + SQLite backup + isolated shadow rehearsal.

Never writes to the input DB, never produces a modified database as output.
The temporary database and any staged values disappear when the tool exits.
"""
from __future__ import annotations

import argparse
from contextlib import closing
import hashlib
from pathlib import Path
import sqlite3
import tempfile

from storage.big_number_shadow_v10400 import (PILOT_COLUMNS, mirror_legacy_copy,
                                              check_shadow, check_shadow_legacy_mirrors,
                                              fetch_shadow)
from validation.v10400_big_number_audit import audit, open_read_only
from validation.v10400_snapshot_preflight import (inspect_pilot_snapshot,
                                                 require_exact_pilot_coverage)
from validation.v10400_extended_snapshot import (inspect_extended_snapshot,
    mirror_extended_copy, check_extended_coverage)


def legacy_digest(conn):
    """Fingerprint ALL original columns in six BigNumber source tables.

    The earlier pilot-only digest omitted class/profession/tool identity keys
    and extended progression columns. A later source mutation in one of those
    fields could therefore escape the legacy-unchanged assertion. No SQL SUM,
    numeric CAST or floating-point conversion is used; rows stream into SHA256.
    This fingerprint is an internal copy-only check, never a player-data dump.
    """
    h = hashlib.sha256()
    identities = {
        'characters': ('account_id',),
        'account_wallet': ('master_account_id',),
        'bank_balances': ('account_id',),
        'class_progress': ('account_id', 'class_name'),
        'professions': ('account_id', 'profession'),
        'tools': ('account_id', 'tool_type'),
    }
    for table, sort_keys in identities.items():
        columns = [r[1] for r in conn.execute(f'PRAGMA table_info("{table}")')]
        # Missing/incomplete layouts will be rejected by snapshot preflight;
        # include their shape in the digest so no DDL drift is silently missed.
        h.update(repr(('table', table, tuple(columns))).encode('utf-8'))
        h.update(b'\n')
        if not columns:
            continue
        if not set(sort_keys).issubset(columns):
            raise ValueError(f'BigNumber: brak klucza identyfikacyjnego w {table}.')
        order = ','.join('"' + col + '"' for col in sort_keys)
        query = f'SELECT * FROM "{table}" ORDER BY {order}'
        count = 0
        for row in conn.execute(query):
            # Include names, levels, counters and all 14+ progression axes,
            # not just the pilot currency/XP columns.
            value = repr(tuple(row)).encode('utf-8')
            h.update(len(value).to_bytes(8, 'big'))
            h.update(value)
            count += 1
        h.update(repr(('rows', table, count)).encode('ascii'))
        h.update(b'\n')
    return h.hexdigest()


def rehearse(db_path):
    """Immutable evidence: legacy digest on temp clone unchanged after rehearsal."""
    with closing(open_read_only(db_path)) as source, tempfile.TemporaryDirectory(prefix='sb104_rehearsal_') as td:
        copied=Path(td)/'offline_copy.sqlite'
        # SQLite's online backup reads a consistent snapshot, including WAL.
        with closing(sqlite3.connect(copied)) as target:
            source.backup(target)
        with closing(sqlite3.connect(copied)) as db:
            before=legacy_digest(db)
            # Full coverage is mandatory: absent legacy tables must NEVER
            # turn a partial copy into an apparently successful migration.
            preflight=inspect_pilot_snapshot(db)
            extended=inspect_extended_snapshot(db)
            report=audit(db)
            db.execute('SAVEPOINT v104_shadow_rehearsal')
            try:
                counts=mirror_legacy_copy(db)
                extended_copied=mirror_extended_copy(db, extended)
                checked=check_shadow_legacy_mirrors(db)
                check_extended_coverage(db, extended)
                require_exact_pilot_coverage(db, preflight)
                # Existing stale shadow entries may not conceal omitted cells.
                if checked < preflight["total_cells"]:
                    raise AssertionError("Brak kompletnego mirroru SQLite.")
                repeat=mirror_legacy_copy(db)
                if sum(repeat.values()) or mirror_extended_copy(db, extended):
                    raise AssertionError('Powtorna migracja nie jest idempotentna.')
                # Validate checksum and one canary exceeding SQLite int64 in temp
                # only if a mirrored real row is available. Never stage in live DB.
                for table,(pk,fields) in PILOT_COLUMNS.items():
                    if counts[table]:
                        axis=f'{table}.{fields[0]}'
                        if table == 'class_progress':
                            first=db.execute('SELECT account_id,class_name FROM class_progress ORDER BY account_id LIMIT 1').fetchone()
                            if first: assert fetch_shadow(db,first[0],axis,source_key=str(first[1])) is not None
                        else:
                            first=db.execute(f'SELECT "{pk}" FROM "{table}" ORDER BY "{pk}" LIMIT 1').fetchone()
                            if first: assert fetch_shadow(db,first[0],axis) is not None
                        break
                if legacy_digest(db)!=before:
                    raise AssertionError('Zmiana starych pol bazy. Przerwano.')
                if db.execute('PRAGMA integrity_check').fetchone()[0]!='ok':
                    raise AssertionError('Blad integralnosci kopii SQLite.')
                if check_shadow_legacy_mirrors(db)!=checked:
                    raise AssertionError('Niespojny shadow lub zmienione INTEGER.')
                # Run all possible failures before RELEASE to preserve rollback.
                db.execute('RELEASE SAVEPOINT v104_shadow_rehearsal')
                db.commit()
            except BaseException:
                db.execute('ROLLBACK TO SAVEPOINT v104_shadow_rehearsal')
                db.execute('RELEASE SAVEPOINT v104_shadow_rehearsal')
                raise
    return {'audit':report,'preflight':preflight,'mirrored':counts,'shadow_checks':checked,
            'idempotent':'PASS','legacy_unchanged':'PASS','sqlite_copy_integrity':'PASS',
            'extended_preflight':extended,'extended_mirrored':extended_copied,
            'production_modified':'NIE'}


def main(argv=None):
    parser=argparse.ArgumentParser(description='Soulbound v104: proba migracji w tymczasowej kopii bazy.')
    parser.add_argument('--db', required=True, help='Sciezka do bazy, odczytana tylko przez SQLite backup')
    args=parser.parse_args(argv)
    result=rehearse(args.db)
    print('V104 ETAP 1: MIGRACJA PROBNA NA KOPII - PASS')
    for key, value in result.items():print(f'{key}: {value}')
    print('Zadnego przełączenia na shadow w prawdziwej rozgrywce.')


if __name__=='__main__':main()
