# -*- coding: utf-8 -*-
"""Safe, local ZIP updater for Soulbound on Windows (Python standard library only).

New release ZIP: place it beside this script or pass its full path.
The updater does not download anything and never updates a running database.
"""
from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import socket
import stat
import subprocess
import sys
import tempfile
import time
import zipfile
from windows_launcher_state import wait_gone
from release_readme_cleanup import cleanup_legacy_readmes

ROOT = Path(__file__).resolve().parent
VERSION_PATTERN = re.compile(r'^\s*VERSION\s*=\s*[\'"]([0-9]+(?:\.[0-9]+){2})[\'"]', re.M)
RELEASE_PATTERN = re.compile(r'^Soulbound-MUD-v(\d+\.\d+\.\d+).*\.zip$', re.I)
SKIP_PARTS = {'__pycache__', 'logs', '.git'}
SQLITE_SUFFIXES = ('.db', '.db-wal', '.db-shm', '.sqlite', '.sqlite-wal', '.sqlite-shm', '.sqlite3', '.sqlite3-wal', '.sqlite3-shm')
PROTECTED_FILENAMES = {'.env', 'soulbound_control.json', 'soulbound_world_seed.txt', 'admin_level_caps.json', 'shop_progression_v7003.json', 'heritage_v7100.json', 'custom_races_v7600.json', 'custom_classes_v7700.json', 'era_v10300.json'}


class UpdateError(Exception):
    pass


def version_tuple(s: str) -> tuple[int, int, int]:
    return tuple(map(int, s.split('.')))


def file_version(p: Path) -> str:
    m = VERSION_PATTERN.search(p.read_text(encoding='utf-8-sig'))
    if not m:
        raise UpdateError(f'Brak numeru VERSION w pliku: {p}')
    return m.group(1)


def protected(relative: Path) -> bool:
    name = relative.name.lower()
    return (name.endswith(SQLITE_SUFFIXES)
            or name in PROTECTED_FILENAMES
            or name.endswith(('.pem', '.key', '.pfx'))
            or any(part.lower() in SKIP_PARTS for part in relative.parts)
            or relative.suffix.lower() == '.zip')


def archive_mapping(archive: zipfile.ZipFile) -> dict[Path, zipfile.ZipInfo]:
    mapping: dict[Path, zipfile.ZipInfo] = {}
    seen: set[str] = set()
    entries = [i for i in archive.infolist() if not i.is_dir()]
    prefixes = [str(PurePosixPath(i.filename).parts[0]) for i in entries]
    top = 'Soulbound-MUD' if prefixes and set(prefixes) == {'Soulbound-MUD'} else None
    for item in entries:
        raw = item.filename
        if raw.startswith('/') or '\\' in raw or '\x00' in raw or ':' in raw:
            raise UpdateError(f'Niebezpieczna nazwa w ZIP: {raw}')
        path = PurePosixPath(raw)
        if any(part in ('', '.', '..') for part in path.parts):
            raise UpdateError(f'Niebezpieczna sciezka ZIP: {raw}')
        if (item.external_attr >> 16) & 0o170000 == stat.S_IFLNK:
            raise UpdateError(f'ZIP zawiera dowiazanie symboliczne: {raw}')
        parts = path.parts[1:] if top else path.parts
        if not parts:
            raise UpdateError('ZIP zawiera plik zamiast folderu Soulbound.')
        relative = Path(*parts)
        k = str(relative).casefold()
        if k in seen:
            raise UpdateError(f'Powtarzajaca sie nazwa w ZIP: {relative}')
        seen.add(k)
        if protected(relative):
            if relative.name.lower().endswith(SQLITE_SUFFIXES):
                raise UpdateError(f'ZIP zawiera baze danych: {relative}. Przerwano, by chronic postacie.')
            continue
        mapping[relative] = item
    essential = {'server.py', 'CHANGELOG_PL.txt', 'core/bootstrap_economy_professions.py',
                 'START_Soulbound.bat', 'STOP_Soulbound.bat', 'predeploy_check.py'}
    missing = essential.difference(str(x).replace('\\', '/') for x in mapping)
    if missing:
        raise UpdateError('ZIP nie jest kompletna paczka Soulbound. Brakuje: '+', '.join(sorted(missing)))
    return mapping


def read_archive_version(archive: zipfile.ZipFile, mapping: dict[Path,zipfile.ZipInfo]) -> str:
    info = mapping[Path('core/bootstrap_economy_professions.py')]
    txt = archive.read(info).decode('utf-8-sig')
    m = VERSION_PATTERN.search(txt)
    if not m:
        raise UpdateError('Nie znaleziono VERSION w nowej paczce.')
    return m.group(1)


def find_release(root: Path, selected: Path | None, current_version: str) -> tuple[Path, str]:
    choices = [selected] if selected is not None else [p for p in root.glob('*.zip') if RELEASE_PATTERN.match(p.name)]
    found: list[tuple[tuple[int,int,int], Path, str]] = []
    for choice in choices:
        if not choice or not choice.is_file():
            if selected is not None:
                raise UpdateError(f'Nie znaleziono ZIP: {choice}')
            continue
        try:
            with zipfile.ZipFile(choice) as z:
                mapping = archive_mapping(z)
                ver = read_archive_version(z, mapping)
                if version_tuple(ver) >= (104, 0, 0):
                    version_entry = mapping.get(Path('VERSION'))
                    if version_entry is None or z.read(version_entry).decode('utf-8-sig').strip() != ver:
                        raise UpdateError('v104: VERSION, kod gry i nazwa ZIP musza byc zgodne.')
                if z.testzip():
                    raise UpdateError('ZIP jest uszkodzony.')
            if not RELEASE_PATTERN.match(choice.name):
                if selected is None:
                    continue
                raise UpdateError('ZIP musi miec nazwe Soulbound-MUD-vX.Y.Z*.zip')
            declared = RELEASE_PATTERN.match(choice.name).group(1)
            if declared != ver:
                raise UpdateError(f'Nazwa ZIP podaje {declared}, ale kod podaje {ver}.')
            found.append((version_tuple(ver), choice, ver))
        except (OSError, zipfile.BadZipFile, UnicodeError, ValueError) as exc:
            if selected is not None:
                raise UpdateError(f'Nie mozna otworzyc ZIP: {exc}') from exc
    if not found:
        raise UpdateError('Brak kompletnej paczki Soulbound-MUD-vX.Y.Z*.zip w folderze gry. Skopiuj ZIP obok pliku AKTUALIZUJ_Soulbound.bat.')
    _, path, new_ver = max(found, key=lambda a: a[0])
    if version_tuple(new_ver) <= version_tuple(current_version):
        raise UpdateError(f'Brak nowszej paczki. Masz v{current_version}, znaleziono v{new_ver}. Niczego nie zmieniono.')
    return path, new_ver



def require_v104_official_predeploy(root: Path, archive_path: Path, new_version: str) -> None:
    """Never stop the live server for a v104+ ZIP without a matching 60/60 PASS.

    Guard even --yes and direct run_update() callers. The official PREDEPLOY
    writes its result outside the installation, so the candidate ZIP cannot
    fabricate an approval by bundling a JSON file. Earlier releases retain
    their historic updater behavior.
    """
    if version_tuple(new_version) < (104, 0, 0):
        return
    state_file = root.parent / 'Soulbound_PREDEPLOY' / 'last_result.json'
    try:
        state = json.loads(state_file.read_text(encoding='utf-8'))
        if not isinstance(state, dict):
            raise ValueError('niepoprawny wynik')
    except (OSError, ValueError, UnicodeError) as exc:
        raise UpdateError('v104: brak zaliczonego oficjalnego PREDEPLOY 60/60 PLUS. '
                          'Uruchom PREDEPLOY_NOWEJ_WERSJI.bat; niczego nie zatrzymano.') from exc
    needed = (state.get('status') == 'PASS'
              and state.get('quality_gate') == 'ULTIMATE-60-PLUS'
              and type(state.get('completed_stages')) is int
              and state['completed_stages'] == 60
              and type(state.get('required_stages')) is int
              and state['required_stages'] == 60
              and type(state.get('returncode')) is int
              and state['returncode'] == 0
              and state.get('version') == new_version
              and state.get('installed_at_test') == file_version(
                  root / 'core/bootstrap_economy_professions.py'))
    if not needed:
        raise UpdateError('v104: brak zgodnego 60/60 PLUS dla tej wersji i aktualnie '
                          'zainstalowanej gry. Niczego nie zatrzymano.')
    try:
        approved = Path(state['zip']).resolve(strict=True)
        candidate = Path(archive_path).resolve(strict=True)
        if approved != candidate:
            raise UpdateError('v104: zatwierdzony PREDEPLOY dotyczy innej paczki ZIP.')
        digest = hashlib.sha256()
        with candidate.open('rb') as stream:
            for part in iter(lambda: stream.read(1024 * 1024), b''):
                digest.update(part)
        if digest.hexdigest() != state.get('sha256'):
            raise UpdateError('v104: zmieniono ZIP po PREDEPLOY. Wykonaj test ponownie.')
    except (OSError, TypeError, ValueError, KeyError) as exc:
        raise UpdateError('v104: nie mozna zweryfikowac zatwierdzonej paczki ZIP.') from exc


def port_open(port: int) -> bool:
    try:
        with socket.create_connection(('127.0.0.1', port), timeout=0.5):
            return True
    except OSError:
        return False


def stop_local_server(root: Path) -> bool:
    # Always use the authenticated STOP, even when the port is momentarily
    # free: an active crash supervisor could restart mid-copy.
    from windows_runtime_state import fallback_dir, read_state
    from windows_launcher_state import process_alive

    logs = (root / 'logs', fallback_dir(root))
    tracked = False
    for folder in logs:
        for filename in ('soulbound_control.json', 'soulbound_supervisor.json', 'soulbound_launcher.json'):
            entry = read_state(folder / filename)
            try:
                if (entry.get('root') == str(root) and process_alive(int(entry['pid']))):
                    tracked = True
            except (TypeError, ValueError, KeyError):
                continue
    # Stop utility itself checks both control copies, all owned PIDs,
    # watchdog state and port 4000. Never regard a free port as proof by itself.
    print('Weryfikuje uwierzytelniony STOP serwera i nadzorcy...', flush=True)
    result = subprocess.run([sys.executable, '-u', str(root / 'stop_soulbound_windows.py')],
                            cwd=Path(os.environ.get('TEMP') or tempfile.gettempdir()), timeout=180)
    if result.returncode != 0:
        raise UpdateError(f'STOP nie potwierdzil bezpiecznego zamkniecia (kod {result.returncode}). Nie podmieniam plikow.')
    if port_open(4000):
        raise UpdateError('Port 4000 nadal zajety po STOP. Aktualizacja wstrzymana.')
    return tracked


def backup_existing(root: Path, backup: Path) -> None:
    def ignore(path: str, names: list[str]) -> set[str]:
        ignored = set()
        for name in names:
            candidate = Path(path) / name
            if name.lower() in SKIP_PARTS or name.lower().endswith('.zip'):
                ignored.add(name)
            elif candidate.is_symlink():
                raise UpdateError(f'Nie tworze kopii dowiazania symbolicznego: {candidate}')
        return ignored
    shutil.copytree(root, backup, ignore=ignore)
    print(f'Kopia kodu, konfiguracji i zapisow: {backup}', flush=True)


def stage_release(archive_path: Path, target: Path, mapping: dict[Path,zipfile.ZipInfo]) -> None:
    target.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(archive_path) as z:
        for rel, info in mapping.items():
            dest = target / rel
            dest.parent.mkdir(parents=True, exist_ok=True)
            with z.open(info) as src, dest.open('wb') as out:
                shutil.copyfileobj(src, out)
    if not (target / 'server.py').is_file():
        raise UpdateError('Niepelna paczka po rozpakowaniu.')


def install_stage(root: Path, stage: Path, backup: Path) -> None:
    """Only replace release files; all live databases, logs and user files stay."""
    created: list[Path] = []
    try:
        for source in sorted(stage.rglob('*')):
            if not source.is_file():
                continue
            relative = source.relative_to(stage)
            if protected(relative):
                continue
            dest = root / relative
            if dest.is_symlink():
                raise UpdateError(f'Nie nadpisuje dowiazania symbolicznego: {dest}')
            if not dest.exists():
                created.append(dest)
            dest.parent.mkdir(parents=True, exist_ok=True)
            # Stage a complete copy beside destination, then replace atomically.
            staged = dest.with_name(dest.name + '.soulbound-new')
            shutil.copy2(source, staged)
            os.replace(staged, dest)
        # Retired Generator Core must never return from a stale older directory.
        (root / 'core' / 'generator_core.py').unlink(missing_ok=True)
        retired, _ = cleanup_legacy_readmes(root, backup)
        if retired:
            print(f'Usunieto {len(retired)} historycznych README z folderu gry; kopie sa w {backup}', flush=True)
    except Exception as exc:
        print('BLAD PODMIANY: przywracam poprzednie pliki z kopii...', flush=True)
        for dest in reversed(created):
            dest.unlink(missing_ok=True)
        # Restore originals from backup without disturbing user data/logs.
        for source in backup.rglob('*'):
            if source.is_file():
                rel = source.relative_to(backup)
                if not protected(rel):
                    dest = root / rel
                    dest.parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(source, dest)
        raise UpdateError(f'Aktualizacja nie powiodla sie; odtworzono poprzedni kod: {exc}') from exc


def run_update(root: Path, archive_path: Path, new_version: str, *, restart: bool = True) -> Path:
    # Critical: protect direct callers and --yes alike, before shutdown/backup.
    require_v104_official_predeploy(root, archive_path, new_version)
    # Pre-validate ZIP *before* touching running server.
    with zipfile.ZipFile(archive_path) as z:
        mapping = archive_mapping(z)
        if read_archive_version(z, mapping) != new_version or z.testzip():
            raise UpdateError('Niepoprawna paczka, instalacja zostala przerwana.')
        if version_tuple(new_version) >= (104, 0, 0):
            # Direct run_update() calls must obey exactly the same version
            # contract as find_release(), including the version-file entry.
            label = RELEASE_PATTERN.match(archive_path.name)
            entry = mapping.get(Path('VERSION'))
            if (label is None or label.group(1) != new_version
                or entry is None
                or z.read(entry).decode('utf-8-sig').strip() != new_version):
                raise UpdateError('v104: nazwa ZIP, VERSION i kod gry sa niespojne.')
    parent = root.parent
    name = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup = parent / f'Soulbound_BACKUP_{name}'
    idx = 1
    while backup.exists():
        backup = parent / f'Soulbound_BACKUP_{name}_{idx}'
        idx += 1
    stage = Path(tempfile.mkdtemp(prefix='.Soulbound_stage_', dir=parent))
    try:
        stage_release(archive_path, stage, mapping)
        # The ZIP was approved BEFORE staging. The source might change during
        # extraction (download, antivirus or another process). Verify the
        # approved SHA again BEFORE stopping the running server. This is a
        # separate fail-closed check; do not trust the earlier approval alone.
        require_v104_official_predeploy(root, archive_path, new_version)
        stop_local_server(root)
        backup_existing(root, backup)
        install_stage(root, stage, backup)
        if file_version(root / 'core/bootstrap_economy_professions.py') != new_version:
            raise UpdateError('Zmieniono pliki, ale numer wersji w katalogu gry jest niepoprawny. Sprawdz recznie backup.')
        print(f'AKTUALIZACJA ZAKONCZONA: Soulbound v{new_version}', flush=True)
        print('Zachowano bazy SQLite i logi. Kopia poprzedniej wersji pozostaje w folderze BACKUP.', flush=True)
        if restart and os.name == 'nt':
            launcher = root / 'START_Soulbound_UKRYTY.vbs'
            if launcher.is_file():
                subprocess.Popen(['wscript.exe', '//nologo', str(launcher)], cwd=root,
                                 creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
                print('Wyslano polecenie uruchomienia serwera w tle. Sprawdz logs\\serwer.log.', flush=True)
            else:
                print('Brak launchera VBS, uruchom serwer recznie przez START_Soulbound.bat.', flush=True)
        elif restart:
            print('Po aktualizacji na Windows uruchom START_Soulbound.bat.', flush=True)
        return backup
    finally:
        shutil.rmtree(stage, ignore_errors=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description='Soulbound: bezpieczna aktualizacja z lokalnej paczki ZIP.')
    parser.add_argument('zip_path', nargs='?', help='Opcjonalna pelna sciezka do nowego ZIP.')
    parser.add_argument('--yes', action='store_true', help='Potwierdz aktualizacje bez pytania (dla testow).')
    parser.add_argument('--no-start', action='store_true', help='Nie uruchamiaj serwera po aktualizacji.')
    args = parser.parse_args(argv)
    try:
        root = ROOT
        installed = file_version(root / 'core/bootstrap_economy_professions.py')
        selected = Path(args.zip_path).expanduser().resolve() if args.zip_path else None
        new_zip, new_ver = find_release(root, selected, installed)
        print(f'Obecna wersja: v{installed}', flush=True)
        print(f'Nowa wersja: v{new_ver}', flush=True)
        print(f'Paczka: {new_zip}', flush=True)
        require_v104_official_predeploy(root, new_zip, new_ver)
        print('Zachowam bazy postaci, logi i ustawienia prywatne. Przed podmiana utworze kopie starej gry.', flush=True)
        if not args.yes:
            if input('Wpisz TAK, aby zaktualizowac: ').strip().upper() != 'TAK':
                print('Anulowano, nie dokonano zmian.', flush=True)
                return 0
        run_update(root, new_zip, new_ver, restart=not args.no_start)
        return 0
    except (UpdateError, OSError, RuntimeError, zipfile.BadZipFile, subprocess.TimeoutExpired) as exc:
        print(f'BLAD: {exc}', file=sys.stderr, flush=True)
        print('Nie wymuszono zatrzymania zadnego procesu.', flush=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
