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


# Exact bytes from v114.00.6; other similarly named files are user-owned.
V114_CANDIDATE_ONLY_NOTES = {
    'v114_REMOVED_EDITOR_FILES_AUDIT.txt': '1b63084a6ad11c06db65d4e4835f9ff501e4e302909e304c03ba0a1c48a3a53b',
    'v114_WORK_IN_PROGRESS.txt': '14b4291d8eefca4811d49b4df14e0817854176772b2f302305ba05f34498598f',
}


# Dokladne SHA256 dokumentow blednie rozprowadzonych w v115.00.1.
# Wersje edytowane przez uzytkownika i pliki o innych bajtach sa zachowane.
V115_DISTRIBUTED_NOTES = {
    'CZYTAJ_LINUX_PL.txt': 'c8873774b733bcc8a717cb151e57ceb1729866fc457ed4e38522671b688be4db',
    'CZYTAJ_NAJPIERW_V114_PL.txt': 'f28dedb84bc31e69f76953a4a5208853b98b56d644391709cd4a51830e7edddb',
    'CZYTAJ_SAMODZIELNY.md': '16c1ba0a8aa7e49feac98e4f5b99afd1dc217c4f98aea5f4d2019cc4370eda57',
    'CZYTAJ_V115_PL.txt': '3b99839780de612c07915ee4569d7b2fbc2b96d8a8ec3bd0028c241111a0c33c',
    'ETAP12_KOREKTA_STARYCH_EXPOWISK_PL.txt': 'c66a1474b69dac74e6c909a84d17b120aa0ecf012619bc7dd9b07899a4ad7f8d',
    'ETAP13_RZECZYWISTE_TRASY_PL.txt': '833d437c36695413ff6e55544b455c5040197cb9e4ebf77028e09d7f72bc9901',
    'ETAP14_ZMIANY_PL.txt': 'be7a1003907a1673bbb3e16cd731e56c236f8813ae29e1c8c7c3589e8392f499',
    'ETAP20_ZMIANY_PL.txt': '9ecfa837bc1cce73920afa36a57c28ee3cc595d1397b0579605703bd204df44f',
    'ETAP21_ZMIANY_PL.txt': 'c288b32a4ec8c136c54f386a8bf38a19e8836ad324ed8178a23d197cc8cebecf',
    'ETAP27_ZMIANY_PL.txt': '4e29ccd40645f106ad3c21de5a3e51ab961eee31943cdd0812a4b40a7bc46e2e',
    'V115_ETAP10_PL.txt': '0286519d025373961ed72df5bec47e81129e305b203134363fba9801e7c02015',
    'V115_ETAP11_PL.txt': '87ac541f6fd9f938494a6110e2f909bfec947b900c65f13ce72b3a091e95b5ff',
    'V115_ETAP4_PL.txt': '37bfea1cb6c4fbc1ae5271616691f7c444eaeb551e5c22436eb08710f1242418',
    'V115_ETAP5_PL.txt': 'f1d9b4d528ac4b9d01206be3729fed2605e654e1a3d30030f770c64da37330a4',
    'V115_ETAP6_PL.txt': 'b9b27d0e2778d66710b9fc1cafb1bea211022baa8660d94ebc4c5339935283e1',
    'V115_ETAP7_PL.txt': 'aa87c0955a15ae5dc8224767798eb7566df8dd0f9e6a88d22984ab4fccf172bd',
    'V115_ETAP9_PL.txt': '8fef00db7320cabfc32a60c3d8df229eca6ada76bab08b1d6c39ffd56e4986fd',
    'V115_ROZPOCZETE_PL.txt': '232978c3f848f4223d7d9f2070b04dbe16ce4c38ef219ea237b6f047b53647fb',
}


class ReadmeCleanupError(RuntimeError):
    pass


def _sha(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b''):
            h.update(block)
    return h.hexdigest()


def cleanup_legacy_readmes(root: Path, backup: Path | None = None) -> tuple[list[str], Path | None]:
    """Backup and unlink historical readmes and exactly authenticated v114 notes.

    If backup is None, create a timestamped sibling backup, not a directory
    inside the installation. Never follow symlinks (including backup paths).
    Returns (removed basenames, backup folder), or ([], None) for a clean root.
    """
    root = Path(root)
    if not root.is_dir() or root.is_symlink():
        raise ReadmeCleanupError('Niepoprawny folder gry; sprzatanie anulowane.')
    old = [root / name for name in LEGACY_READMES if (root / name).exists() or (root / name).is_symlink()]
    for name, expected in {**V114_CANDIDATE_ONLY_NOTES, **V115_DISTRIBUTED_NOTES}.items():
        candidate = root / name
        if candidate.is_file() and not candidate.is_symlink() and _sha(candidate) == expected:
            old.append(candidate)
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
