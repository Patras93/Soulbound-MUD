# -*- coding: utf-8 -*-
"""v110: fail-closed, read-only WAL-aware integrity and reversible snapshot gate.

Only the disposable copy passed from Windows PREDEPLOY is opened. This code
never touches C:\\Soulbound-MUD\\soulbound.db and never stores character rows
or personal data in its logs. SQLite's online backup creates a SECOND copy,
which must have exactly the same schema and every SQL row (including BLOBs).
"""
from __future__ import annotations
from contextlib import closing
import hashlib
import os
from pathlib import Path
import sqlite3
import struct
import sys
import tempfile
import time

REQUIRED_TABLES = frozenset({
    'accounts', 'characters', 'inventory', 'equipment',
    'v106_item_instances', 'v106_equipped_instances',
    'v106_stored_instances', 'v107_eq_production_cutover',
})


def _feed(h, item):
    """Unambiguous serialization with data type and length, including BLOBs."""
    if item is None:
        kind, value = b'N', b''
    elif isinstance(item, bytes):
        kind, value = b'B', item
    elif isinstance(item, int):
        kind, value = b'I', str(item).encode('ascii')
    elif isinstance(item, float):
        kind, value = b'F', struct.pack('!d', item)
    else:
        kind, value = b'T', item.encode('utf-8', 'surrogatepass')
    h.update(kind + struct.pack('!Q', len(value)))
    h.update(value)


def fingerprint(conn):
    """Full SQLite logical fingerprint; respects rowid and WITHOUT ROWID tables."""
    conn.execute('PRAGMA query_only=ON')
    if conn.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
        raise RuntimeError('SQLite integrity_check FAIL')
    h = hashlib.sha256()
    # PRAGMA user_version and application_id are persistent database metadata,
    # not rows in sqlite_master.  Ignoring them would let a migration silently
    # change an install/schema marker while the alleged 1:1 digest stayed equal.
    for pragma in ('user_version', 'application_id', 'encoding'):
        _feed(h, pragma)
        _feed(h, conn.execute('PRAGMA ' + pragma).fetchone()[0])
    schema = conn.execute('SELECT type,name,tbl_name,sql FROM sqlite_master '
                          'ORDER BY type,name,tbl_name,sql').fetchall()
    for record in schema:
        for col in record:
            _feed(h, col)
    tables = {name: sql or '' for kind, name, _, sql in schema if kind == 'table'}
    if not REQUIRED_TABLES <= tables.keys():
        raise RuntimeError('Brak istniejących tabel kont, postaci albo ekwipunku')
    counts = {}
    for name, sql in sorted(tables.items()):
        escaped = '"' + name.replace('"', '""') + '"'
        # SELECT rowid is unavailable on WITHOUT ROWID and virtual tables.
        # sqlite_master includes sqlite_sequence, but not virtual shadow tables
        # consistently across SQLite versions; stable ordering is essential.
        cols = [r[1] for r in conn.execute('PRAGMA table_xinfo(' + escaped + ')') if r[6] != 1]
        quoted_cols = ','.join('"' + c.replace('"', '""') + '"' for c in cols)
        if 'WITHOUT ROWID' not in sql.upper() and not sql.upper().lstrip().startswith('CREATE VIRTUAL TABLE'):
            query = 'SELECT rowid,* FROM ' + escaped + ' ORDER BY rowid'
        else:
            query = 'SELECT * FROM ' + escaped
            if quoted_cols:
                query += ' ORDER BY ' + quoted_cols
        counter = 0
        try:
            for row in conn.execute(query):
                for col in row:
                    _feed(h, col)
                h.update(b'\xff')
                counter += 1
        except sqlite3.OperationalError as exc:
            raise RuntimeError('Nie można bezpiecznie odczytać tabeli: ' + name) from exc
        _feed(h, name)
        _feed(h, counter)
        counts[name] = counter
    return h.hexdigest(), counts


def audit_snapshot(source, *, timeout_seconds=600):
    """Source is already a disposable copy. Verify exact backup and no writes."""
    source = Path(source)
    if source.is_symlink() or not source.is_file() or source.suffix.lower() != '.sqlite':
        raise RuntimeError('Wymagana istniejąca, odłączona migawka SQLite')
    source = source.resolve(strict=True)
    if source.name != 'SOURCE_COMMITTED_SNAPSHOT.sqlite':
        raise RuntimeError('Odmowa badania potencjalnej żywej bazy zamiast migawki PREDEPLOY')
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix='V110_BACKUP_REHEARSAL_') as scratch:
        restored = Path(scratch) / 'RESTORED_VERIFIED.sqlite'
        with closing(sqlite3.connect(source.as_uri() + '?mode=ro', uri=True, timeout=5)) as original:
            original.execute('PRAGMA query_only=ON')
            before, counts = fingerprint(original)
            with closing(sqlite3.connect(restored, timeout=5)) as destination:
                def progress(_status, _remaining, _total):
                    if time.monotonic() - started > timeout_seconds:
                        raise TimeoutError('Odtworzenie kopii przekroczyło limit')
                original.backup(destination, pages=128, progress=progress, sleep=0.05)
            after, again = fingerprint(original)
            if after != before or again != counts:
                raise RuntimeError('Migawka źródłowa zmieniła się podczas audytu')
        with closing(sqlite3.connect(restored.as_uri() + '?mode=ro', uri=True, timeout=5)) as copy:
            copy_digest, copy_counts = fingerprint(copy)
        if copy_digest != before or copy_counts != counts:
            raise RuntimeError('Odtworzona kopia SQLite różni się od migawki')
        # No character/account identifiers are printed, only aggregate counts.
        return dict(tables=len(counts), accounts=counts['accounts'],
                    characters=counts['characters'], instances=counts['v106_item_instances'],
                    sha256=before)


# The PREDEPLOY driver belongs to the *installed* release, not the candidate.
# A production v109 -> candidate v110 upgrade still uses the v109 folder name,
# while the v110 driver uses its new name. Both are isolated OS-TEMP snapshots.
FROZEN_DIR_PREFIXES = (
    'Soulbound_PREDEPLOY_SQLITE_FROZEN_',
    'sb110_predeploy_sqlite_frozen_',
)


def is_predeploy_snapshot_path(value):
    """Accept only a detached source in an immediate system TEMP child folder."""
    if not value:
        return False
    try:
        path = Path(value)
        if (not path.is_absolute() or path.name != 'SOURCE_COMMITTED_SNAPSHOT.sqlite'
                or path.is_symlink() or path.parent.is_symlink()):
            return False
        parent = path.parent.resolve(strict=True)
        temp_root = Path(tempfile.gettempdir()).resolve(strict=True)
        return (parent.parent == temp_root
                and any(parent.name.startswith(prefix) and len(parent.name) > len(prefix)
                        for prefix in FROZEN_DIR_PREFIXES)
                and path.is_file())
    except (OSError, RuntimeError, ValueError):
        return False


def main():
    # Refuse live DBs. Both v109 and v110 runners pass one detached SQLite
    # backup with a fixed basename in a random, immediate OS-TEMP directory.
    path = os.environ.get('SOULBOUND_ULTRA_SOURCE_DB', '')
    if not is_predeploy_snapshot_path(path):
        print('V110 AUDYT DANYCH: BRAK BEZPIECZNEJ MIGAWKI PREDEPLOY — FAIL', flush=True)
        return 3
    try:
        result = audit_snapshot(path)
        print('V110 DANE GRACZY I SQLITE: PASS; tabele={tables}, konta={accounts}, '
              'postacie={characters}, kopie EQ={instances}; odtworzenie 1:1, '
              'bez zmian oryginalu.'.format(**result), flush=True)
        return 0
    except (OSError, sqlite3.Error, RuntimeError, TimeoutError, ValueError) as exc:
        print('V110 DANE GRACZY I SQLITE: FAIL; '+type(exc).__name__+': '+str(exc),flush=True)
        return 3

if __name__ == '__main__':
    raise SystemExit(main())
