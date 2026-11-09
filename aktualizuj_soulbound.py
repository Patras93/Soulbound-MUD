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

ROOT = Path(os.environ.get('SOULBOUND_LIVE_ROOT') or Path(__file__).resolve().parent).resolve()
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
        if relative.as_posix().casefold() in ('live_content/v107_release_activation.json', 'live_content/v108_release_activation.json', 'live_content/v109_release_activation.json', 'live_content/release_current.json'):
            raise UpdateError('Znaczniki zatwierdzenia v107/v108 moze utworzyc tylko instalator.')
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
    if new_version == '110.00.0':
        # Only today's installed version and today's approved ZIP matter.
        # Historical installer .py files and old approval manifests are irrelevant.
        if file_version(root/'core/bootstrap_economy_professions.py')!='109.00.0':
            raise UpdateError('v110: wymagana zainstalowana v109.00.0; bez migracji skokowej.')
    elif version_tuple(new_version) >= (110, 0, 0):
        raise UpdateError('v110: nieznana nowsza wersja bez osobnego zatwierdzenia.')
    elif new_version == '109.00.0':
        from validation.v10900_release_readiness import unmet_requirements as v109_missing
        if v109_missing(ROOT):
            raise UpdateError('v109: niekompletna integracja aktywacji, STOP zabroniony.')
        if file_version(root/'core/bootstrap_economy_professions.py')!='108.00.0':
            raise UpdateError('v109: wymagana zainstalowana produkcyjna v108.00.0.')
        from systems.v10800_activation import verify_root_for_test as verify_v108
        if not verify_v108(root):
            raise UpdateError('v109: brak trwałej autoryzacji zainstalowanej v108.')
    elif version_tuple(new_version) >= (108, 0, 0):
        if new_version != '108.00.0':
            raise UpdateError('Nieznany numer wydania, brak zweryfikowanej sciezki migracji.')
        from validation.v10800_release_readiness import unmet_requirements
        if unmet_requirements(ROOT):
            raise UpdateError('v108: niekompletna sciezka aktywacji i EQ; STOP zabroniony.')
        # v108 only upgrades certified v107 installations. Older transitions
        # need a separately validated migration; never infer it from VERSION.
        if file_version(root/'core/bootstrap_economy_professions.py')!='107.00.0':
            raise UpdateError('v108: aktualizacja wymaga wgranej produkcyjnej v107.00.0.')
    if version_tuple(new_version) < (104, 0, 0):
        return
    # Never replace the live v107 approval while testing a v108 ZIP.
    state_name = 'last_result_v108.json' if new_version == '108.00.0' else 'last_result.json'
    state_file = root.parent / 'Soulbound_PREDEPLOY' / state_name
    try:
        state = json.loads(state_file.read_text(encoding='utf-8'))
        if not isinstance(state, dict):
            raise ValueError('niepoprawny wynik')
        if new_version == '108.00.0' and (state.get('v108_release_gates_pass') is not True
                                                 or state.get('v108_eq_rebuild_trial_pass') is not True):
            raise UpdateError('v108: brak zaliczonej dodatkowej bramki wydania, niczego nie zatrzymano.')
        if new_version == '110.00.0' and state.get('v110_release_gates_pass') is not True:
            raise UpdateError('v110: brak osobnej bramki wydania; STOP zabroniony.')
        if new_version == '109.00.0' and state.get('v109_release_gates_pass') is not True:
            raise UpdateError('v109: brak zaliczonych osobnych bramek v109, STOP zabroniony.')
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
                  root / 'core/bootstrap_economy_professions.py')
              and (new_version != '108.00.0' or (state.get('v108_release_gates_pass') is True
                         and state.get('v108_eq_rebuild_trial_pass') is True))
              and (new_version != '109.00.0' or state.get('v109_release_gates_pass') is True)
              and (new_version != '110.00.0' or state.get('v110_release_gates_pass') is True))
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



def _restore_prior_code_after_v108_cutover_failure(root: Path, backup: Path, staged_files: set[Path]):
    """Rollback all previous release files, leaving live player files alone."""
    for relative in sorted(staged_files, reverse=True):
        if protected(relative):
            continue
        if not (backup/relative).is_file():
            destination=root/relative
            if destination.is_file():
                destination.unlink()
    for previous in backup.rglob('*'):
        if previous.is_file():
            relative=previous.relative_to(backup)
            if protected(relative):
                continue
            destination=root/relative
            destination.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(previous,destination)

    # Generated v108 manifest is installer-created rather than a ZIP member.
    # Do not leave it behind when reverting to the previous release.
    for generated in (Path('LIVE_CONTENT/v108_release_activation.json'),
                      Path('LIVE_CONTENT/v109_release_activation.json'),
                      Path('LIVE_CONTENT/release_current.json')):
        if not (backup/generated).exists():
            (root/generated).unlink(missing_ok=True)


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
        if new_version == '107.00.0':
            # Stage the release activation marker BEFORE stopping the server.
            # install_stage() installs it with the same rollback semantics as
            # source files; an unapproved ZIP cannot package its own marker.
            result_path = root.parent/'Soulbound_PREDEPLOY'/'last_result.json'
            result = json.loads(result_path.read_text(encoding='utf-8'))
            if (result.get('status') != 'PASS' or result.get('version') != new_version
                or result.get('sha256') != hashlib.sha256(archive_path.read_bytes()).hexdigest()
                or result.get('completed_stages') != 60
                or result.get('required_stages') != 60):
                raise UpdateError('Nie utworzono znacznika v107: brak zgodnego PREDEPLOY.')
            activation = stage/'LIVE_CONTENT'/'v107_release_activation.json'
            activation.parent.mkdir(parents=True, exist_ok=True)
            activation.write_text(json.dumps({
                'schema':1, 'version':new_version, 'sha256':result['sha256']},
                sort_keys=True)+'\n',encoding='utf-8')
        if new_version == '108.00.0':
            state = json.loads((root.parent/'Soulbound_PREDEPLOY'/'last_result_v108.json').read_text(encoding='utf-8'))
            if (state.get('status')!='PASS' or state.get('version')!=new_version
                or state.get('v108_release_gates_pass') is not True
                or state.get('v108_eq_rebuild_trial_pass') is not True
                or state.get('installed_at_test')!='107.00.0'
                or state.get('sha256')!=hashlib.sha256(archive_path.read_bytes()).hexdigest()):
                raise UpdateError('v108: brak zgodnego wyniku testow; brak STOP.')
            # Persist only verified release attestation INSIDE the install.
            # PREDEPLOY and the candidate ZIP are needed before STOP, not for
            # every restart after a successful install. No new DB marker/table.
            from systems.v10800_activation import activation_manifest, verify_root_for_test
            marker = stage/'LIVE_CONTENT'/'v108_release_activation.json'
            marker.parent.mkdir(parents=True,exist_ok=True)
            marker.write_text(json.dumps(activation_manifest(state, archive_path, stage),
                                         sort_keys=True, indent=2)+'\n',encoding='utf-8')
            if not verify_root_for_test(stage):
                raise UpdateError('v108: znacznik instalacji nie zweryfikowal plikow przed STOP.')
        if new_version == '110.00.0':
            state = json.loads((root.parent/'Soulbound_PREDEPLOY'/'last_result.json').read_text(encoding='utf-8'))
            from systems.v11000_activation import activation_manifest, verify
            marker=stage/'LIVE_CONTENT'/'release_current.json'
            marker.parent.mkdir(parents=True,exist_ok=True)
            marker.write_text(json.dumps(activation_manifest(state,archive_path,stage,mapping),
                                         sort_keys=True,indent=2)+'\n',encoding='utf-8')
            if not verify(stage):
                raise UpdateError('v110: manifest bieżącego wydania nie zgadza się ze stagingiem; brak STOP.')
        if new_version == '109.00.0':
            state = json.loads((root.parent/'Soulbound_PREDEPLOY'/'last_result.json').read_text(encoding='utf-8'))
            from systems.v10900_activation import activation_manifest, verify_root_for_test
            marker=stage/'LIVE_CONTENT'/'v109_release_activation.json'
            marker.parent.mkdir(parents=True,exist_ok=True)
            marker.write_text(json.dumps(activation_manifest(state,archive_path,stage),
                                         sort_keys=True,indent=2)+'\n',encoding='utf-8')
            if not verify_root_for_test(stage):
                raise UpdateError('v109: manifest stagingu nie zweryfikował kodu; brak STOP.')
        # The ZIP was approved BEFORE staging. The source might change during
        # extraction (download, antivirus or another process). Verify the
        # approved SHA again BEFORE stopping the running server. This is a
        # separate fail-closed check; do not trust the earlier approval alone.
        require_v104_official_predeploy(root, archive_path, new_version)
        stop_local_server(root)
        backup_existing(root, backup)
        if new_version == '108.00.0':
            # We MUST NOT install code v108 on the unrepaired v107 ledger. The
            # earlier Windows PREDEPLOY was executed on a freshly rebuilt
            # detached image. Now rebuild AGAIN on the *stopped* actual source,
            # verify source/backup preservation, then commit only after the
            # versioned code and install manifest have been installed.
            from validation.v10800_eq107_readonly_reconcile import take_snapshot
            from systems.v10800_eq_cutover_bridge import (prepare_from_snapshot,
                 commit_verified_copy, restore_sqlite_from_backup)
            live_db = root / 'soulbound.db'
            rollback_db = backup / 'V108_EQ_BEFORE_REBUILD_ROLLBACK.sqlite'
            take_snapshot(live_db,rollback_db)
            with tempfile.TemporaryDirectory(prefix='Soulbound_v108_EQ_COMMIT_',dir=parent) as working:
                scratch = Path(working)
                source_copy = scratch/'STOPPED_PRODUCTION_SNAPSHOT.sqlite'
                take_snapshot(live_db,source_copy)
                rebuilt,report = prepare_from_snapshot(source_copy,root,scratch)
                print('V108: nowy rebuild na ZATRZYMANEJ bazie:',
                      ', '.join(f'{k}={v}' for k,v in sorted(report.items())),flush=True)
                installed = False
                commit_started = False
                try:
                    install_stage(root, stage, backup)
                    installed = True
                    if file_version(root / 'core/bootstrap_economy_professions.py') != new_version:
                        raise UpdateError('V108: zly numer kodu przed przebudowa SQLite.')
                    commit_started = True
                    commit_verified_copy(rebuilt,live_db)
                    from systems.v10800_activation import verify_root_for_test
                    if not verify_root_for_test(root):
                        raise UpdateError('V108: manifest instalacji nie zgadza sie po przebudowie.')
                    print('V108: odtworzono zgodnosc fizycznego EQ bez utraty oryginalnych kopii.',flush=True)
                except BaseException:
                    # Fail closed even after partial write/DB backup. Restore
                    # v107 SQLite and v107 code to a stopped server. The
                    # permanent backup directory remains available for manual
                    # recovery if e.g. hardware fails during restoration.
                    errors=[]
                    if commit_started:
                        try: restore_sqlite_from_backup(rollback_db,live_db)
                        except BaseException as exc: errors.append('SQLITE:'+type(exc).__name__)
                    if installed:
                        try: _restore_prior_code_after_v108_cutover_failure(
                            root,backup,set(mapping))
                        except BaseException as exc: errors.append('KOD:'+type(exc).__name__)
                    if errors:
                        raise UpdateError('V108: przerwano, automatyczne cofniecie NIEPELNE: '
                                          +', '.join(errors)+'. Nie uruchamiaj bez kontroli.')
                    raise
        elif new_version == '110.00.0':
            installed=False
            try:
                install_stage(root,stage,backup)
                installed=True
                # Retire the old, exactly certified v109 BAT/Python launchers.
                # The backup exists; changed user files are not removed.
                from systems.v11000_retired_installers import retire
                retired, retained = retire(root, backup)
                print(f'V110: usunieto {len(retired)} identycznych starych launcherow; '
                      f'zachowano {len(retained)} plikow zmodyfikowanych.',flush=True)
                from systems.v11000_activation import verify
                if (file_version(root/'core/bootstrap_economy_professions.py') != new_version
                    or not verify(root)):
                    raise UpdateError('v110: niezgodne pliki lub manifest po instalacji.')
                from contextlib import closing
                import sqlite3
                db_path=root/'soulbound.db'
                with closing(sqlite3.connect(db_path.as_uri()+'?mode=ro',uri=True)) as conn:
                    conn.execute('PRAGMA query_only=ON')
                    if not conn.execute("SELECT 1 FROM sqlite_master "
                            "WHERE name='v107_eq_production_cutover'").fetchone():
                        raise UpdateError('v110: brak fizycznego rejestru EQ z v108.')
                    if conn.execute('PRAGMA quick_check').fetchone()[0]!='ok':
                        raise UpdateError('v110: kontrola SQLite nie powiodła się.')
                print('V110: bieżący manifest PASS; EQ i bazę graczy zachowano.',flush=True)
            except BaseException:
                if installed:
                    _restore_prior_code_after_v108_cutover_failure(root,backup,set(mapping)|{
                        Path('LIVE_CONTENT/release_current.json')})
                raise
        elif new_version == '109.00.0':
            installed=False
            try:
                install_stage(root,stage,backup)
                installed=True
                from systems.v10900_activation import verify_root_for_test
                if (file_version(root/'core/bootstrap_economy_professions.py') != new_version
                        or not verify_root_for_test(root)):
                    raise UpdateError('v109: po instalacji brak zgodnego znacznika i kodu.')
                # No EQ rebuild: preserve the certified v108 physical ledger.
                from contextlib import closing
                import sqlite3
                live_db=root/'soulbound.db'
                with closing(sqlite3.connect(live_db.as_uri()+'?mode=ro',uri=True)) as conn:
                    conn.execute('PRAGMA query_only=ON')
                    if not conn.execute("SELECT 1 FROM sqlite_master WHERE name='v107_eq_production_cutover'").fetchone():
                        raise UpdateError('v109: zniknęła istniejąca tabela EQ v108.')
                print('V109: kod i trwały manifest PASS, fizyczne EQ bez migracji.',flush=True)
            except BaseException:
                if installed:
                    _restore_prior_code_after_v108_cutover_failure(root,backup,set(mapping))
                raise
        else:
            install_stage(root, stage, backup)
        if file_version(root / 'core/bootstrap_economy_professions.py') != new_version:
            raise UpdateError('Zmieniono pliki, ale numer wersji w katalogu gry jest niepoprawny. Sprawdz recznie backup.')
        print(f'AKTUALIZACJA ZAKONCZONA: Soulbound v{new_version}', flush=True)
        print('Zachowano bazy SQLite i logi. Kopia poprzedniej wersji pozostaje w folderze BACKUP.', flush=True)
        if restart and os.name == 'nt':
            # Transparent Windows start: no Windows Script Host and no hidden VBS.
            launcher = root / 'START_Soulbound.bat'
            if launcher.is_file():
                subprocess.Popen([os.environ.get('COMSPEC', 'cmd.exe'), '/d', '/c', str(launcher)],
                                 cwd=str(root))
                print('Uruchomiono standardowy BAT. Sprawdz logs\\serwer.log.', flush=True)
            else:
                print('Brak START_Soulbound.bat. Uruchom serwer recznie.', flush=True)
        elif restart:
            print('Po aktualizacji na Windows uruchom START_Soulbound.bat.', flush=True)
        return backup
    finally:
        shutil.rmtree(stage, ignore_errors=True)


def main(argv: list[str] | None = None) -> int:
    # v107: do not use the existence of a v106 regression module as an
    # unconditional release block. Historical test files remain in every full
    # ZIP. The exact official 60/60 approval + SHA256 is the authority,
    # checked below and again inside run_update BEFORE any server STOP.
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
