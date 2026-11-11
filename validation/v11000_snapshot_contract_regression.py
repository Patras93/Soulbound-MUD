# -*- coding: utf-8 -*-
"""v110: independent synthetic tests of read-only snapshot 1:1 integrity.

No access to production, user accounts, or real character data. A successful
fixture is NOT approval of the mandatory Windows real-database gate.
"""
from __future__ import annotations
from contextlib import closing, redirect_stdout
import io
import os
import shutil
import sys
from pathlib import Path
import sqlite3
import tempfile
from unittest.mock import patch
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from validation.v11000_snapshot_preservation import (
    REQUIRED_TABLES, audit_snapshot, fingerprint, is_predeploy_snapshot_path, main,
)


def run_regression():
    count = 0
    with tempfile.TemporaryDirectory(prefix='sb110_predeploy_sqlite_frozen_') as temp:
        path = Path(temp) / 'SOURCE_COMMITTED_SNAPSHOT.sqlite'
        with closing(sqlite3.connect(path)) as db:
            for name in sorted(REQUIRED_TABLES):
                primary = 'INTEGER PRIMARY KEY AUTOINCREMENT' if name == 'accounts' else 'INTEGER PRIMARY KEY'
                db.execute(f'CREATE TABLE "{name}" (id {primary}, payload BLOB)')
            db.execute('INSERT INTO "accounts" VALUES (13, ?)', (sqlite3.Binary(b'temp'),))
            db.execute('DELETE FROM "accounts" WHERE id=13')
            db.execute('INSERT INTO "accounts" VALUES (1, ?)', (sqlite3.Binary(b'A\x00\xff'),))
            db.execute('INSERT INTO "characters" VALUES (2, ?)', ('ąęśćół',))
            db.execute('INSERT INTO "v106_item_instances" VALUES (3, ?)', (sqlite3.Binary(b'ITEM\x00'),))
            db.execute('PRAGMA user_version=109')
            db.execute('PRAGMA application_id=127945')
            db.commit()
        old_bytes = path.read_bytes()
        result = audit_snapshot(path)
        assert result['tables'] >= len(REQUIRED_TABLES)
        assert result['accounts'] == 1 and result['characters'] == 1
        assert result['instances'] == 1 and len(result['sha256']) == 64
        with closing(sqlite3.connect(path)) as seq_db:
            assert seq_db.execute("SELECT seq FROM sqlite_sequence WHERE name='accounts'").fetchone()[0] == 13
        count += 1  # next auto-ID must survive a 1:1 backup
        assert path.read_bytes() == old_bytes  # no source mutation
        count += 5
        # Exercise the same entrypoint used by Windows PREDEPLOY, not just
        # the helper called by other tests.  The synthetic path is isolated.
        with patch.dict(os.environ, {'SOULBOUND_ULTRA_SOURCE_DB': str(path)}):
            with redirect_stdout(io.StringIO()) as output:
                assert main() == 0
            assert 'V110 DANE GRACZY I SQLITE: PASS' in output.getvalue()
        count += 1
        # A v109 production updater and a v110 updater create DIFFERENT
        # private TEMP folder prefixes. Exercise both real main() code paths.
        with tempfile.TemporaryDirectory(prefix='Soulbound_PREDEPLOY_SQLITE_FROZEN_') as legacy_temp:
            legacy_path = Path(legacy_temp) / 'SOURCE_COMMITTED_SNAPSHOT.sqlite'
            shutil.copy2(path, legacy_path)  # synthetic fixture, not user data
            with patch.dict(os.environ, {'SOULBOUND_ULTRA_SOURCE_DB': str(legacy_path)}):
                with redirect_stdout(io.StringIO()) as output:
                    assert main() == 0, output.getvalue()
                assert 'V110 DANE GRACZY I SQLITE: PASS' in output.getvalue()
            assert is_predeploy_snapshot_path(str(legacy_path))
            count += 2
            # Prefix alone is insufficient: the source must sit directly
            # below the OS temp root, not in an arbitrary nested directory.
            with tempfile.TemporaryDirectory(prefix='nested-not-predeploy-') as nested:
                spoof = Path(nested) / legacy_path.parent.name / legacy_path.name
                spoof.parent.mkdir()
                shutil.copy2(legacy_path, spoof)
                assert not is_predeploy_snapshot_path(str(spoof))
                with patch.dict(os.environ, {'SOULBOUND_ULTRA_SOURCE_DB': str(spoof)}):
                    with redirect_stdout(io.StringIO()):
                        assert main() == 3
                count += 2
        with closing(sqlite3.connect(path)) as db:
            base_hash, _ = fingerprint(db)
        for pragma, value in [('user_version', 110), ('application_id', 127946)]:
            with closing(sqlite3.connect(path)) as db:
                db.execute(f'PRAGMA {pragma}={value}')
            with closing(sqlite3.connect(path)) as db:
                changed_hash, _ = fingerprint(db)
            assert changed_hash != base_hash, pragma
            count += 1
            with closing(sqlite3.connect(path)) as db:
                db.execute(f'PRAGMA {pragma}={109 if pragma=="user_version" else 127945}')
        with closing(sqlite3.connect(path)) as db:
            rechecked, _ = fingerprint(db)
        assert rechecked == base_hash
        count += 1
        # Deleting a physical-equipment table must fail, never pass as 1:1.
        with closing(sqlite3.connect(path)) as db:
            db.execute('DROP TABLE "v106_stored_instances"')
            db.commit()
        try:
            audit_snapshot(path)
        except RuntimeError as exc:
            assert 'tabel' in str(exc)
            count += 1
        else:
            raise AssertionError('Missing physical equipment table was accepted')
        # A DB with the expected basename but invalid SQLite bytes also fails.
        path.write_bytes(b'not a sqlite database')
        try:
            audit_snapshot(path)
        except sqlite3.DatabaseError:
            count += 1
        else:
            raise AssertionError('Damaged SQLite was accepted')
        # Readiness guard refuses absent proof; this is not the live DB test.
        with patch.dict(os.environ, {'SOULBOUND_ULTRA_SOURCE_DB': ''}):
            with redirect_stdout(io.StringIO()):
                assert main() == 3
        count += 1
        # No candidate code should silently turn an ordinary SQLite filename
        # into a source snapshot just because it exists.
        other = Path(temp) / 'ordinary_database.sqlite'
        other.write_bytes(b'not a SQLite db')
        try:
            audit_snapshot(other)
        except RuntimeError:
            count += 1
        else:
            raise AssertionError('Ordinary database basename accepted')
    return count


if __name__ == '__main__':
    print(f'V110 SQLITE SNAPSHOT CONTRACT: {run_regression()} PASS; '
          'read-only, BLOB, pragmas, fail-closed; synthetic fixture ONLY', flush=True)
