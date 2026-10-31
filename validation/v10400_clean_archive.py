# -*- coding: utf-8 -*-
"""Build and verify a Soulbound v104 candidate ZIP with one user-facing text file.

Only CHANGELOG_PL.txt is distributed. The generated world seed stays owned by the
installation, not by release archives. This does not perform a deployment or
change VERSION, player data, or the source tree.
"""
from __future__ import annotations

import argparse
import hashlib
from pathlib import Path
import stat
import zipfile

ROOT = Path(__file__).resolve().parents[1]
ALLOWED_TEXT = 'CHANGELOG_PL.txt'
DISALLOWED_SUFFIXES = ('.db', '.db-wal', '.db-shm', '.sqlite', '.sqlite-wal',
                       '.sqlite-shm', '.sqlite3', '.sqlite3-wal', '.sqlite3-shm',
                       '.log', '.md', '.csv', '.pyc', '.pyo')
SKIPPED_DIRS = {'__pycache__', '.git', '.pytest_cache', '.mypy_cache', 'logs'}
DOCUMENT_SUFFIXES = ('.txt', '.md', '.log', '.csv', '.rst')


def file_list(root: Path) -> list[tuple[str, Path]]:
    """Select code and data without temporary diagnostics or text clutter."""
    root = Path(root)
    found: list[tuple[str, Path]] = []
    for path in root.rglob('*'):
        rel = path.relative_to(root).as_posix()
        if any(part in SKIPPED_DIRS for part in path.relative_to(root).parts):
            continue
        if path.is_symlink():
            raise ValueError(f'Niebezpieczny link w paczce: {rel}')
        if not path.is_file():
            continue
        lower = rel.lower()
        if lower.endswith(DISALLOWED_SUFFIXES) and not lower.endswith(DOCUMENT_SUFFIXES):
            raise ValueError(f'Nie dolaczaj baz/cache/sekretow: {rel}')
        if path.suffix.lower() in DOCUMENT_SUFFIXES and rel != ALLOWED_TEXT:
            continue
        if path.name.lower() in {'.env', 'credentials.json', 'private.key'}:
            raise ValueError(f'Nie dolaczaj poufnych danych: {rel}')
        found.append((rel, path))
    from validation.v10400_release_isolation_guard import forbidden_release_paths
    unsafe = forbidden_release_paths([rel for rel, _ in found])
    if unsafe:
        raise ValueError('Niebezpieczne pliki w paczce: '+', '.join(unsafe[:10]))
    names = [rel.casefold() for rel, _ in found]
    if len(names) != len(set(names)):
        raise ValueError('Powtarzajace sie sciezki w paczce.')
    if not (root / ALLOWED_TEXT).is_file():
        raise ValueError('Brak jedynego CHANGELOG_PL.txt.')
    for necessary in ('VERSION', 'server.py', 'predeploy_check.py',
                      'core/bootstrap_economy_professions.py'):
        if necessary not in {name for name, _ in found}:
            raise ValueError(f'Brak krytycznego pliku: {necessary}')
    return sorted(found)


def verify_archive(output: Path, expected: list[tuple[str, Path]]) -> tuple[int, str]:
    """Check all CRCs and every archived byte against the source (no extra report)."""
    expected_map = {name: path for name, path in expected}
    with zipfile.ZipFile(output) as z:
        names = z.namelist()
        if len(names) != len(expected_map) or set(names) != set(expected_map):
            raise AssertionError('Niekompletna lub nadmiarowa paczka ZIP.')
        if [n for n in names if n.lower().endswith(DOCUMENT_SUFFIXES)] != [ALLOWED_TEXT]:
            raise AssertionError('W ZIP musi byc tylko jeden dokument tekstowy: CHANGELOG_PL.txt.')
        bad = z.testzip()
        if bad:
            raise AssertionError('Uszkodzony wpis ZIP: '+bad)
        for name, path in expected_map.items():
            source_sha = hashlib.sha256(path.read_bytes()).digest()
            archived_sha = hashlib.sha256(z.read(name)).digest()
            if source_sha != archived_sha:
                raise AssertionError('Roznica zawartosci w ZIP: '+name)
    return len(expected_map), hashlib.sha256(output.read_bytes()).hexdigest()


def pack(root: Path, output: Path) -> tuple[int, str]:
    root = Path(root).resolve()
    output = Path(output).resolve()
    if output.is_relative_to(root):
        raise ValueError('Wynikowy ZIP musi byc poza katalogiem zrodel.')
    files = file_list(root)
    output.parent.mkdir(parents=True, exist_ok=True)
    temp = output.with_name(output.name+'.part')
    try:
        with zipfile.ZipFile(temp, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6,
                             allowZip64=True) as z:
            for name, path in files:
                z.write(path, arcname=name)
        verify_archive(temp, files)
        temp.replace(output)
    finally:
        temp.unlink(missing_ok=True)
    return verify_archive(output, files)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Jedna czysta paczka Soulbound v104')
    parser.add_argument('output', type=Path, help='Docelowa sciezka .zip poza grą')
    args = parser.parse_args()
    n, sha = pack(ROOT, args.output)
    print(f'ZIP PASS: {n} plikow; tylko {ALLOWED_TEXT} z dokumentow tekstowych.')
    print(f'SHA256: {sha}')
    print('Status RC: brak zgody na wdrozenie bez BigNumber i Windows 60/60.')
