# -*- coding: utf-8 -*-
"""v108: frozen-snapshot rehearsal and stop-only guarded SQLite EQ cutover.

All player data remains on the user's PC. PREDEPLOY only prepares private
SQLite copies. Committing a copy requires verified STOP, official release
approval and a code/data backup taken by the installer before writes.
"""
from __future__ import annotations

from contextlib import closing
from pathlib import Path
import os
import shutil
import sqlite3
import tempfile


def prepare_from_snapshot(detached_source, live_root, scratch_root):
    """Return validated rebuilt copy and anonymous counters, never mutate live.

    The historical baseline is resolved *from the frozen source marker*, not
    by guessing a file name or taking the user's newest hourly backup.
    """
    from validation.v10800_eq107_readonly_reconcile import locate_original_backup, take_snapshot
    from validation.v10800_eq_rebuild_copy import run
    from validation.v10800_v107_equipment_compat_gate import audit_read_only

    source=Path(detached_source).resolve(strict=True)
    live=Path(live_root).resolve(strict=True)
    scratch=Path(scratch_root).resolve(strict=True)
    if (not source.is_file() or source.is_symlink() or source == live/'soulbound.db'
        or source.is_relative_to(live) or not (live/'soulbound.db').is_file()):
        raise RuntimeError('Brak bezpiecznej migawki lub bazy produkcyjnej')
    if scratch == live or scratch.is_relative_to(live) or live.is_relative_to(scratch):
        raise RuntimeError('Robocze bazy nie moga znajdowac sie w instalacji')
    fixture=scratch/'source_fixture'
    output=scratch/'rebuilt_candidate'
    fixture.mkdir()
    (fixture/'backups').mkdir()
    shutil.copyfile(source,fixture/'soulbound.db')
    with closing(sqlite3.connect(source.as_uri()+'?mode=ro',uri=True)) as frozen:
        frozen.execute('PRAGMA query_only=ON')
        baseline=locate_original_backup(live/'soulbound.db',frozen)
        # Refuse symlinks and mismatched marker before copying the baseline.
    take_snapshot(baseline, fixture/'backups'/baseline.name)
    result=run(fixture,output)
    result_db=output/'REBUILT_TEST_ONLY.sqlite'
    if not result_db.is_file() or result_db.is_symlink():
        raise RuntimeError('Nie utworzono poprawnej odlaczonej kopii EQ')
    audit_read_only(result_db)
    return result_db,result


def commit_verified_copy(rebuilt_path, live_db_path):
    """Replace the stopped-server SQLite content via SQLite backup API.

    This is NOT an authorization to run: only the official updater calls it,
    after STOP and a separate, verified full live backup. Never unlink WAL.
    """
    source=Path(rebuilt_path).resolve(strict=True)
    target=Path(live_db_path).resolve(strict=True)
    if not source.is_file() or source.is_symlink() or not target.is_file() or target.is_symlink():
        raise RuntimeError('Niedozwolona baza lub dowiazanie symboliczne')
    if source==target:
        raise RuntimeError('Nie wolno kopiowac bazy na nia sama')
    with closing(sqlite3.connect(source.as_uri()+'?mode=ro',uri=True)) as trial:
        trial.execute('PRAGMA query_only=ON')
        if trial.execute('PRAGMA integrity_check').fetchone()[0]!='ok':
            raise RuntimeError('Odbudowana baza nie przeszla integrity_check')
        with closing(sqlite3.connect(target)) as live:
            if live.in_transaction:
                raise RuntimeError('Baza produkcyjna ma otwarta transakcje')
            trial.backup(live, pages=128, sleep=0.05)
            if live.execute('PRAGMA integrity_check').fetchone()[0]!='ok':
                raise RuntimeError('Niepoprawna baza po zapisie')
    from validation.v10800_v107_equipment_compat_gate import audit_read_only
    from validation.v10800_eq107_readonly_reconcile import take_snapshot
    with tempfile.TemporaryDirectory(prefix='sb108_post_commit_verify_') as folder:
        standalone = Path(folder)/'AFTER_COMMIT.sqlite'
        take_snapshot(target,standalone)
        audit_read_only(standalone)


def restore_sqlite_from_backup(backup_database, live_db_path):
    """Best-effort rollback helper, used only after safe STOP."""
    source=Path(backup_database).resolve(strict=True)
    target=Path(live_db_path).resolve(strict=True)
    with closing(sqlite3.connect(source.as_uri()+'?mode=ro',uri=True)) as original:
        original.execute('PRAGMA query_only=ON')
        if original.execute('PRAGMA integrity_check').fetchone()[0]!='ok':
            raise RuntimeError('Kopia wycofania jest niespojna')
        with closing(sqlite3.connect(target)) as live:
            original.backup(live, pages=128, sleep=0.05)
            if live.execute('PRAGMA integrity_check').fetchone()[0]!='ok':
                raise RuntimeError('Nieudane przywracanie SQLite')
