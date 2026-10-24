# -*- coding: utf-8 -*-
"""Retire ONLY known obsolete release README files from the install root.

Never delete custom documentation or recursively scan directories. Every removed
file has a byte-identical copy outside the game directory before deletion.
This also runs at first Windows startup because older installed updaters cannot
execute the newer updater's cleanup code during the same deployment.
"""
from __future__ import annotations

from datetime import datetime
import hashlib
from pathlib import Path
import shutil

LEGACY_READMES = (
    'README_v98_ADMIN_LIVE_PL.txt',
    'README_v99_ADMIN_LIVE_PL.txt',
    'README_v100_ADMIN_LIVE_PL.txt',
    'README_v101_ADMIN_LIVE_PL.txt',
    'README_v102_ADMIN_LIVE_PL.txt',
    'README_v102_00_1_PREDEPLOY_FIX_PL.txt',
    'README_v102_00_2_PREDEPLOY_FIX_PL.txt',
    'README_v102_00_3_PREDEPLOY_FIX_PL.txt',
)


class ReadmeCleanupError(RuntimeError):
    pass


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def cleanup_legacy_readmes(root: Path, backup: Path | None = None) -> tuple[list[str], Path | None]:
    """Backup and unlink only 8 exact basenames in root; idempotent.

    If backup is None, create a timestamped sibling backup, not a directory
    inside the installation. Never follow symlinks (including backup paths).
    Returns (removed basenames, backup folder), or ([], None) for a clean root.
    """
    root = Path(root)
    if not root.is_dir() or root.is_symlink():
        raise ReadmeCleanupError('Niepoprawny folder gry; sprzatanie anulowane.')
    old = [root / name for name in LEGACY_READMES if (root / name).exists() or (root / name).is_symlink()]
    if not old:
        return [], None
    for src in old:
        if src.is_symlink() or not src.is_file():
            raise ReadmeCleanupError(f'Nie usuwam linku ani katalogu: {src.name}')
    if backup is None:
        stem = f'Soulbound_BACKUP_README_{datetime.now().strftime("%Y%m%d_%H%M%S")}'
        backup = root.parent / stem
        counter = 1
        while backup.exists() or backup.is_symlink():
            backup = root.parent / f'{stem}_{counter}'
            counter += 1
    backup = Path(backup)
    if backup == root or backup.parent != root.parent or backup.is_symlink():
        raise ReadmeCleanupError('Kopia README musi byc bezpiecznym folderem obok instalacji.')
    if backup.exists() and not backup.is_dir():
        raise ReadmeCleanupError('Folder kopii README nie jest katalogiem.')
    backup.mkdir(parents=True, exist_ok=True)
    # PREPARE: never delete anything until all byte-identical backups exist.
    for src in old:
        saved = backup / src.name
        if saved.is_symlink() or (saved.exists() and not saved.is_file()):
            raise ReadmeCleanupError(f'Niepoprawna kopia: {saved.name}')
        if not saved.exists():
            shutil.copy2(src, saved)
        if _sha(saved) != _sha(src):
            raise ReadmeCleanupError(f'Kopia README niezgodna z oryginalem: {src.name}')
    removed: list[Path] = []
    try:
        for src in old:
            # Recheck before unlink; this must never turn into deletion of symlinks.
            if src.is_symlink() or not src.is_file() or _sha(src) != _sha(backup / src.name):
                raise ReadmeCleanupError(f'Plik README zmieniony podczas sprzatania: {src.name}')
            src.unlink()
            removed.append(src)
    except (OSError, ReadmeCleanupError):
        # A partial failure leaves previous data in place, restoring from backup.
        for src in removed:
            shutil.copy2(backup / src.name, src)
        raise
    return [src.name for src in removed], backup
