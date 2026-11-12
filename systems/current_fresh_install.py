# -*- coding: utf-8 -*-
"""Version-independent clean-folder install of approved release code.

Never starts a broken v110/v111 executable. Existing game directory is read-only.
The only bridge from that directory is an SQLite committed backup plus named
private data, after full source backup and before atomic publication.
"""
from __future__ import annotations
from contextlib import closing
from pathlib import Path
import os
import shutil
import sqlite3
from systems.current_sqlite_integrity import verify_equal

SKIP_PROCESS_STATE = frozenset({'soulbound_control.json','soulbound_supervisor.json',
                                 'soulbound_launcher.json','last_result.json'})
SQL_DB_EXTS = ('.db','.sqlite','.sqlite3')
SQL_SIDECARS = ('-wal','-shm')

class FreshInstallError(RuntimeError):
    pass


def target_for(source: Path, version: str) -> Path:
    source=Path(source)
    if not version or len(version.split('.')) != 3 or any(not x.isdigit() for x in version.split('.')):
        raise FreshInstallError('Niepoprawny numer docelowej wersji')
    return source.with_name(source.name+'_V'+version.replace('.','_')+'_NOWA')


def _sqlite_snapshot(source: Path, dest: Path) -> int:
    """Copy all committed data, including WAL; do not transfer old WAL/SHM."""
    if source.is_symlink() or not source.is_file() or dest.is_symlink():
        raise FreshInstallError('Niebezpieczna baza danych: '+str(source))
    dest.parent.mkdir(parents=True,exist_ok=True)
    try:
        # URI read-only: never initializes/migrates the old database.
        with closing(sqlite3.connect(source.resolve().as_uri()+'?mode=ro',uri=True,timeout=15)) as old:
            old.execute('PRAGMA query_only=ON')
            if old.execute('PRAGMA integrity_check').fetchone()!=('ok',):
                raise FreshInstallError('Niepoprawna integralnosc bazy przed kopia')
            with closing(sqlite3.connect(dest)) as new:
                old.backup(new,pages=256,sleep=0.1)
                if new.execute('PRAGMA integrity_check').fetchone()!=('ok',):
                    raise FreshInstallError('Niepoprawna integralnosc nowej kopii SQLite')
                # Full deterministic schema+row+BLOB verification (not just row counts).
                try:
                    verify_equal(old, new)
                except ValueError as exc:
                    raise FreshInstallError(str(exc)) from exc
                # Preserve table-count metrics for update reports.
                names=[row[0] for row in old.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
                fresh=[row[0] for row in new.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")]
                if names!=fresh:raise FreshInstallError('Zmiana schematu tabel w nowej kopii')
                for name in names:
                    quoted='"'+name.replace('"','""')+'"'
                    a=old.execute('SELECT COUNT(*) FROM '+quoted).fetchone()[0]
                    b=new.execute('SELECT COUNT(*) FROM '+quoted).fetchone()[0]
                    if a != b: raise FreshInstallError('Zmiana liczby rekordow: '+name)
                return len(names)
    except sqlite3.Error as exc:
        raise FreshInstallError('Nie udalo sie wykonac bezpiecznej kopii SQLite: '+str(exc)) from exc


def carry_saved_data(backup: Path, stage: Path, protected_predicate) -> dict:
    """Transfer only mutable player data/settings from FULL verified old backup.

    Candidate code is already staged and tested; do not copy any old .py, BAT,
    migrations, archives, stale process controls or release metadata into it.
    """
    backup=Path(backup);stage=Path(stage)
    if not backup.is_dir() or backup.is_symlink() or not stage.is_dir() or stage.is_symlink():
        raise FreshInstallError('Brak bezpiecznej kopii lub nowego stagingu')
    if not (backup/'soulbound.db').is_file():
        raise FreshInstallError('W kopii bezpieczenstwa nie ma zapisow soulbound.db')
    stats={'sqlite_files':0,'tables_checked':0,'private_files':0}
    for source in sorted(backup.rglob('*')):
        if source.is_symlink():
            raise FreshInstallError('Dowiazanie w kopii graczy: '+str(source))
        if not source.is_file():continue
        rel=source.relative_to(backup)
        if rel.name.lower() in SKIP_PROCESS_STATE or rel.name.lower().endswith(SQL_SIDECARS):
            continue
        if rel.suffix.lower()=='.zip' or not protected_predicate(rel):continue
        # Never let legacy code, manifest, or user-controlled symlinks enter a new release.
        if rel.suffix.lower() in ('.py','.pyc','.bat','.exe','.dll'):
            continue
        dest=stage/rel
        if dest.is_symlink():raise FreshInstallError('Dowiazanie w stagingu: '+str(dest))
        if rel.suffix.lower() in SQL_DB_EXTS:
            stats['tables_checked']+=_sqlite_snapshot(source,dest)
            stats['sqlite_files']+=1
        else:
            dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(source,dest)
            stats['private_files']+=1
    if not (stage/'soulbound.db').is_file():
        raise FreshInstallError('Brak kopii SQLite po przeniesieniu zapisow')
    return stats


def publish_clean(stage: Path, target: Path, verifier) -> Path:
    """Atomic same-parent publication after all checks; never overwrite target."""
    stage=Path(stage);target=Path(target)
    if stage.is_symlink() or not stage.is_dir() or target.is_symlink() or target.exists():
        raise FreshInstallError('Katalog docelowy juz istnieje albo jest niebezpieczny: '+str(target))
    if stage.parent != target.parent:
        raise FreshInstallError('Staging i cel nie leza na tym samym woluminie')
    if not verifier(stage):
        raise FreshInstallError('Kod stagingu nie ma prawidlowego podpisanego manifestu')
    os.rename(stage,target)
    if not verifier(target):
        # Keep a failed candidate from appearing as an installable new game.
        # The source game is still read-only; stage is cleaned by the caller.
        try:
            os.rename(target,stage)
        except OSError as exc:
            raise FreshInstallError('Po publikacji manifest nie przeszedl; sprawdz nowy katalog: '+str(target)) from exc
        raise FreshInstallError('Weryfikacja po publikacji nie powiodla sie, nowy katalog wycofany')
    return target
