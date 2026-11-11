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
# Only candidate PREDEPLOY needs the full historical validation suite.
# The live installation retains merely the legacy verification helpers still
# imported by the current server, administrator or approved migration code.
# All candidate modules are extracted into an isolated TEMP worktree for 60/60.
V111_OLD_MIGRATION_TOOLS = frozenset({
    'systems/v11000_retired_installers.py',
    'systems/v10800_eq_cutover_bridge.py',  # historical v108-only migration
})
# Modules imported only by offline PREDEPLOY/regression scripts. They must remain
# in the full candidate ZIP, never in the production installation. Each entry
# was checked against the live module manifest and source imports in v111.
# Do not add gameplay/world modules based on names or age alone.
V111_CANDIDATE_ONLY_PYTHON_FILES = frozenset({
    'admin/audits.py',
    'systems/full_systems_audit_v03062.py',
    'admin/audit_rules_v406.py',
    'admin/v410_release_audits.py',
    'admin/v410_equipment_audits.py',  # original v0.30 equipment audits: offline only
    'admin/city_services_fast_v1225.py',
    'admin/cross_system_audit_v1001.py',
    'admin/fast_predeploy_audit_v0571.py',
    'admin/mob_display_name_audit_v11129.py',
    # Read-only source inspector and the staged v104 BigNumber prototype are
    # kept in the full PREDEPLOY archive, never in live gameplay.
    'core/source_contracts.py',
    'storage/big_number_events_v10400.py',
    'storage/big_number_ledger_v10400.py',
    'storage/big_number_reward_bundle_v10400.py',
    'systems/equipment_craft_reward_audit_v10600.py',
    'systems/quest_calendar_v10600.py',
    'systems/v106_raid_combat_forecast.py',
    'systems/v10800_eq_dynamic_catalog.py',
})
# Obsolete generated-core entrypoint: remove only when the previous
# certified manifest includes the unchanged exact file, never unconditionally.
V111_CERTIFIED_OBSOLETE_RUNTIME = frozenset({'core/generator_core.py'})
V111_CANDIDATE_ONLY_ROOT_FILES = frozenset({
    'predeploy_check.py', 'predeploy_full.py', 'testuj_soulbound_windows.py',
    'TESTUJ_Soulbound.bat', '_debug_boot_local.py',
    'audyt_v107_windows_przed_predeploy.py', 'sprawdz_v104_zbiorczo.py',
})


# Current runtime uses systems.runtime_activation only. Historical activators
# remain in the full candidate exclusively for offline regression fixtures.
V112_HISTORICAL_ACTIVATION_FILES = frozenset({
    'systems/v10700_activation.py', 'systems/v10800_activation.py',
    'systems/v10900_activation.py', 'systems/v10900_staging_guard.py',
    'systems/v11000_activation.py', 'systems/v11100_holiday_activation.py',
    'systems/v10800_predeploy_isolation.py',
})


# Reviewed after current explicit import migration. These exact split helpers
# and globals binders have no importers in the installed source closure.
# Keep their original sources only in the full offline regression candidate.
V112_OBSOLETE_RUNTIME_GLUE_FILES = frozenset({
    'admin/v410_help_audits.py',
    'admin/v410_help_refresh.py',
    'core/legacy_function_binding_v410.py',
    'core/legacy_method_binding_v4200.py',
    'core/v410_class_skill_audits.py',
    'core/v410_mec_mastery.py',
    'core/v410_progression_helpers.py',
    'network/v420_chests.py',
    'network/v420_lookups.py',
    'player/session_methods_v4200/__init__.py',
    'player/session_methods_v4200/atlascodex_part01.py',
    'player/session_methods_v4200/atlascodex_part02.py',
    'player/session_methods_v4200/atlascodex_part03.py',
    'player/session_methods_v4200/combatrealtime_part01.py',
    'player/session_methods_v4200/combatrealtime_part02.py',
    'player/session_methods_v4200/combatrealtime_part03.py',
    'player/session_methods_v4200/combatskills_part01.py',
    'player/session_methods_v4200/combatskills_part02.py',
    'player/session_methods_v4200/dungeonprogression_part01.py',
    'player/session_methods_v4200/dungeonprogression_part02.py',
    'player/session_methods_v4200/dungeonprogression_part03.py',
    'player/session_methods_v4200/gathering_part01.py',
    'player/session_methods_v4200/gathering_part02.py',
    'player/session_methods_v4200/gathering_part03.py',
    'player/session_methods_v4200/guidenavigation_part01.py',
    'player/session_methods_v4200/guidenavigation_part02.py',
    'player/session_methods_v4200/guidenavigation_part03.py',
    'player/session_methods_v4200/inventoryequipment_part01.py',
    'player/session_methods_v4200/inventoryequipment_part02.py',
    'player/session_methods_v4200/inventoryequipment_part03.py',
    'player/session_methods_v4200/inventoryequipment_part04.py',
    'player/session_methods_v4200/inventoryequipment_part05.py',
    'player/session_methods_v4200/ioauthcharacter_part01.py',
    'player/session_methods_v4200/ioauthcharacter_part02.py',
    'player/session_methods_v4200/ioauthcharacter_part03.py',
    'player/session_methods_v4200/party_part01.py',
    'player/session_methods_v4200/party_part02.py',
    'player/session_methods_v4200/party_part03.py',
    'player/session_methods_v4200/perceptionmaps_part01.py',
    'player/session_methods_v4200/perceptionmaps_part02.py',
    'player/session_methods_v4200/perceptionmaps_part03.py',
    'player/session_methods_v4200/professionstorage_part01.py',
    'player/session_methods_v4200/professionstorage_part02.py',
    'player/session_methods_v4200/professionstorage_part03.py',
    'player/session_methods_v4200/skilllearning_part01.py',
    'player/session_methods_v4200/skilllearning_part02.py',
    'player/session_methods_v4200/skilllearning_part03.py',
    'player/session_methods_v4200/skilllearning_part04.py',
    'storage/methods_v4200/__init__.py',
    'storage/methods_v4200/databaseworld_part01.py',
    'storage/methods_v4200/databaseworld_part02.py',
    'systems/v410_craft_recipes.py',
    'systems/v410_dungeon_builders.py',
    'systems/v410_dungeon_loot.py',
    'systems/v410_dungeon_regions.py',
    'systems/v410_equipment_shops.py',
    'systems/v410_gem_registration.py',
    'systems/v410_material_profiles.py',
    'systems/v410_resource_registration.py',
    'world/v410_dynamic_collectors.py',
    'world/v410_dynamic_instances.py',
    'world/v410_dynamic_regions.py',
    'world/v410_generation_frontier.py',
    'world/v410_generation_islands.py',
    'world/v410_generation_waters.py',
    'world/v410_infinite_floors.py',
    'world/v410_world_economy.py',
    'world/v420_equipment_config.py',
    'world/v420_generation_mobs.py',
    'world/v420_generation_random.py',
    'world/v420_help_config.py',
    'world/v420_runtime_class_equipment.py',
    'world/v420_runtime_regions.py',
    'world/v420_runtime_world_audits.py',
})


def v111_live_release_mapping(mapping: dict[Path, zipfile.ZipInfo]) -> dict[Path, zipfile.ZipInfo]:
    """Only install code needed on a running host; never reduce ZIP PREDEPLOY."""
    from core.runtime_manifest import FULL_AUDIT_ONLY_MODULES
    offline_admin_audits = frozenset(FULL_AUDIT_ONLY_MODULES)
    result={}
    for rel,info in mapping.items():
        parts=rel.parts
        if (rel.as_posix() in offline_admin_audits
                or rel.as_posix() in V112_HISTORICAL_ACTIVATION_FILES
                or rel.as_posix() in V112_OBSOLETE_RUNTIME_GLUE_FILES
                or rel.as_posix() in V111_OLD_MIGRATION_TOOLS
                or rel.as_posix() in V111_CANDIDATE_ONLY_PYTHON_FILES):
            continue
        # The released v111 server does not contain historical validation.
        # All live imports were relocated to core/ and systems/.
        if parts[0]=='validation':
            continue
        # Historyczne źródła questów zachowujemy w ZIP-ie tylko dla
        # regresji v109/v110; działająca gra używa world/quests/.
        if (len(parts)==3 and parts[0:2]==('data','catalogs_v109')
                and parts[2] in {'quests_01.py','quests_02.py','quests_03.py'}):
            continue
        if len(parts)==3 and parts[0:2]==('world','quests_v110'):
            continue
        if len(parts)==1 and parts[0] in V111_CANDIDATE_ONLY_ROOT_FILES:
            continue
        result[rel]=info
    return result


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
    essential = {'server.py', 'core/bootstrap_economy_professions.py',
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



def v112_base_preflight(root: Path) -> str:
    """Read-only safety gate for a *broken* v110/v111 installation.

    The player database and completed physical EQ migration are the trusted
    base-state evidence, not a missing/invalid v111 manifest.  This does not
    authorize a v112 release: exact Windows PREDEPLOY 60/60 PLUS + SHA256 is
    checked independently afterwards, and a complete backup precedes writes.

    Both certified and recovery sources must pass the same SQLite checks;
    historical v106 rollback snapshots are deliberately never required.
    """
    import sqlite3
    from contextlib import closing
    root = Path(root)
    version_file = root / 'VERSION'
    base_code = root / 'core/bootstrap_economy_professions.py'
    database = root / 'soulbound.db'
    if (root.is_symlink() or version_file.is_symlink() or
        base_code.is_symlink() or database.is_symlink()):
        raise UpdateError('v112: niebezpieczne dowiazanie w bazowej instalacji.')
    try:
        installed = version_file.read_text(encoding='utf-8-sig').strip()
        if installed not in ('110.00.0','111.00.0') or file_version(base_code) != installed:
            raise UpdateError('v112: źródło danych musi mieć zgodne VERSION i kod v110/v111.')
        if not database.is_file():
            raise UpdateError('v112: nie znaleziono bazy postaci soulbound.db.')
        with closing(sqlite3.connect(database.as_uri()+'?mode=ro',uri=True,timeout=10)) as conn:
            conn.execute('PRAGMA query_only=ON')
            if conn.execute('PRAGMA integrity_check').fetchone() != ('ok',):
                raise UpdateError('v112: bledy integralnosci SQLite; aktualizacja zablokowana.')
            must_have={'v107_eq_production_cutover','v106_equipped_instances',
                       'v106_stored_instances','v106_item_instances','equipment','inventory'}
            found={row[0] for row in conn.execute(
                "SELECT name FROM sqlite_master WHERE type='table'")}
            absent=must_have-found
            if absent:
                raise UpdateError('v112: brak aktywnego rejestru fizycznego EQ: '
                                  +', '.join(sorted(absent)))
            rows=conn.execute('SELECT cutover_version,backup_name '
                              'FROM v107_eq_production_cutover').fetchall()
            if (len(rows)!=1 or rows[0][0]!='107.00.0'
                    or not isinstance(rows[0][1],str)
                    or not rows[0][1] or Path(rows[0][1]).name!=rows[0][1]):
                raise UpdateError('v112: niezgodny znacznik zakonczonej migracji EQ.')
            for table in ('v106_equipped_instances','v106_stored_instances'):
                if conn.execute('PRAGMA foreign_key_check("'+table+'")').fetchone():
                    raise UpdateError('v112: bledne powiazania EQ w tabeli '+table)
        # v111 may have a missing or stale manifest after a failed install.
        # An approved v112 candidate can repair it without ever importing
        # a prior release activator or trying to recreate a v106 snapshot.
        return 'validated-ledger'
    except sqlite3.Error as exc:
        raise UpdateError('v112: nie moge bezpiecznie odczytac SQLite/EQ: '+str(exc)) from exc
    except (OSError, UnicodeError, ValueError) as exc:
        raise UpdateError('v112: nie mozna sprawdzic podstawy aktualizacji: '+str(exc)) from exc


def require_v104_official_predeploy(root: Path, archive_path: Path, new_version: str) -> None:
    """Never stop the live server for a v104+ ZIP without a matching 60/60 PASS.

    Guard even --yes and direct run_update() callers. The official PREDEPLOY
    writes its result outside the installation, so the candidate ZIP cannot
    fabricate an approval by bundling a JSON file. Earlier releases retain
    their historic updater behavior.
    """
    # Only v112 is an installable target for this release. A broken v110/v111
    # may be used as a data source after the strict SQLite / EQ preflight.
    if new_version != '112.00.0':
        raise UpdateError('Ten instalator obsluguje tylko niezalezne wydanie v112.00.0.')
    v112_base_preflight(root)
    print('V112: baza v110/v111 i fizyczne EQ sprawdzone tylko do odczytu; '
          'wymagane 60/60 PLUS i pełny backup.',flush=True)
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
        if new_version == '112.00.0' and state.get('v112_release_gates_pass') is not True:
            raise UpdateError('v112: brak osobnej bramki; STOP zabroniony.')
        if new_version == '111.00.0' and state.get('v111_release_gates_pass') is not True:
            raise UpdateError('v111: brak osobnej bramki; STOP zabroniony.')
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
              and (new_version != '110.00.0' or state.get('v110_release_gates_pass') is True)
              and (new_version != '111.00.0' or state.get('v111_release_gates_pass') is True)
              and (new_version != '112.00.0' or state.get('v112_release_gates_pass') is True))
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


def verify_prior_manifest_data_only(backup: Path, record: dict, old_version: str) -> bool:
    """v112-only parser for an old *data* manifest; never imports old code.

    Any missing, tampered or locally modified source blocks cleanup. No version
    marker alone authorizes deletion: all declared files must have matching
    SHA256 in the backed-up installation first.
    """
    if old_version not in ('110.00.0', '111.00.0') or not isinstance(record,dict):
        return False
    if (type(record.get('schema')) is not int or record.get('schema')!=1
        or record.get('version')!=old_version or record.get('status')!='PASS'
        or record.get('quality_gate')!='ULTIMATE-60-PLUS'
        or record.get('source_gate')!='WINDOWS_PREDEPLOY_APPROVED'):
        return False
    archive_hash=record.get('archive_sha256')
    if not isinstance(archive_hash,str) or not re.fullmatch(r'[0-9a-f]{64}',archive_hash):
        return False
    files=record.get('files')
    if not isinstance(files,dict) or len(files)<3:
        return False
    if not {'VERSION','server.py','core/bootstrap_economy_professions.py'}.issubset(files):
        return False
    for name, expected in files.items():
        if not isinstance(name,str) or not name or '\\' in name:
            return False
        relative=Path(name)
        if relative.is_absolute() or '..' in relative.parts or name.startswith('/'):
            return False
        if not isinstance(expected,str) or not re.fullmatch(r'[0-9a-f]{64}',expected):
            return False
        candidate=backup/relative
        if not candidate.is_file() or candidate.is_symlink() or sha256_file(candidate)!=expected:
            return False
    return True


def retire_certified_v111_test_files(root: Path, stage: Path, backup: Path) -> int:
    """Retire verified historical tools from approved v110/v111 after backup.

    Only files listed and signed in the previous version's *complete* approval
    may be removed; locally modified files and unknown releases are preserved.
    The previous code backup permits a full rollback of every removal.
    """
    if not (stage/'VERSION').is_file() or (stage/'VERSION').read_text(encoding='utf-8-sig').strip() not in ('111.00.0','112.00.0'):
        return 0
    old_manifest=backup/'LIVE_CONTENT/release_current.json'
    if not old_manifest.is_file():
        print('V111 porządki: brak poprzedniego manifestu; starych testów nie kasuję.', flush=True)
        return 0
    try:
        old_version=(backup/'VERSION').read_text(encoding='utf-8-sig').strip()
        record=json.loads(old_manifest.read_text(encoding='utf-8'))
        if not verify_prior_manifest_data_only(backup,record,old_version):
            print('V112: poprzedni manifest jest niepelny lub niespojny; bez usuwania plikow.',flush=True)
            return 0
        hashes=record['files']
    except (OSError,ValueError,KeyError,TypeError,UnicodeError):
        return 0
    removed=0
    from core.runtime_manifest import FULL_AUDIT_ONLY_MODULES
    offline_admin_audits = frozenset(FULL_AUDIT_ONLY_MODULES)
    for name,expected in hashes.items():
        if not isinstance(name,str) or not isinstance(expected,str):
            continue
        rel=Path(name)
        if (rel.is_absolute() or '..' in rel.parts or len(rel.parts)==0
            or not (rel.parts[0]=='validation' or
                rel.as_posix() in offline_admin_audits or
                rel.as_posix() in V111_OLD_MIGRATION_TOOLS or
                rel.as_posix() in V111_CANDIDATE_ONLY_PYTHON_FILES or
                rel.as_posix() in V111_CERTIFIED_OBSOLETE_RUNTIME or
                (len(rel.parts)==1 and rel.name in V111_CANDIDATE_ONLY_ROOT_FILES))):
            continue
        if (stage/rel).exists() or protected(rel):
            continue
        target=root/rel
        if target.is_file() and not target.is_symlink() and hashlib.sha256(target.read_bytes()).hexdigest()==expected:
            target.unlink()
            removed+=1
    if removed:
        print(f'V111: usunięto {removed} potwierdzonych historycznych testów; backup zachowany.',flush=True)
    return removed


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
        # Retire obsolete source only through the exact previous signed
        # manifest + SHA256 + full backup. Locally modified files stay.
        retire_certified_v111_test_files(root, stage, backup)
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


def v112_certified_boot_rehearsal(root: Path, staged_root: Path, *, timeout=240) -> None:
    """Start exact approved v112 code against an isolated backup of live DB.

    This is intentionally BEFORE STOP or any install write. Running the
    production authorization + migrated EQ ledger on a disposable copy catches
    failures that a new/empty SQLite smoke test cannot detect. The original
    player DB, source code and port 4000 are never passed to this child.
    """
    import sqlite3
    from contextlib import closing
    from systems.v11200_activation import verify
    if not verify(staged_root):
        raise UpdateError('v112: test kopii graczy nie ma podpisanego kodu stagingu.')
    with tempfile.TemporaryDirectory(prefix='sb112_production_copy_boot_') as scratch:
        copy = Path(scratch)/'players_test.sqlite'
        source = Path(root)/'soulbound.db'
        if not source.is_file() or source.is_symlink():
            raise UpdateError('v112: brak bezpiecznej zrodlowej bazy postaci.')
        try:
            with closing(sqlite3.connect(source.as_uri()+'?mode=ro',uri=True,timeout=15)) as live:
                with closing(sqlite3.connect(copy,timeout=15)) as test:
                    live.backup(test,pages=256,sleep=0.05)
                    if test.execute('PRAGMA integrity_check').fetchone()!=('ok',):
                        raise UpdateError('v112: niespojna probna kopia bazy postaci.')
        except sqlite3.Error as exc:
            raise UpdateError('v112: nie udalo sie sklonowac SQLite bez zapisu: '+str(exc)) from exc
        with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as sock:
            sock.bind(('127.0.0.1',0))
            test_port=sock.getsockname()[1]
        env=os.environ.copy()
        for key in tuple(env):
            if key.startswith('SOULBOUND_V') and key.endswith('_STAGING'):
                env.pop(key,None)
        for key in ('SOULBOUND_LIVE_ROOT','SOULBOUND_ULTRA_SOURCE_DB',
                    'RAILWAY_TCP_APPLICATION_PORT','PORT','SOULBOUND_TCP_TEST_CHILD'):
            env.pop(key,None)
        env.update(SOULBOUND_DB=str(copy),SOULBOUND_HOST='127.0.0.1',
                   SOULBOUND_PORT=str(test_port),PYTHONPATH=str(staged_root),
                   PYTHONDONTWRITEBYTECODE='1',PYTHONUTF8='1')
        # A failed boot can still create non-daemon game threads. Always
        # terminate this *disposable child process* on success or failure;
        # otherwise subprocess.run may wait until timeout and hide the real
        # traceback even though the startup exception was immediate.
        script=(
            "import os,sys,traceback\n"
            "try:\n"
            " import server\n"
            " from server.mud_server import MudServer\n"
            " s=MudServer()\n"
            " s.db.conn.close()\n"
            " server._BOOT_SOCKET.close()\n"
            " print('V112 PRODUCTION-COPY BOOT PASS',flush=True)\n"
            "except BaseException:\n"
            " traceback.print_exc()\n"
            " sys.stderr.flush()\n"
            " os._exit(21)\n"
            "os._exit(0)\n"
        )
        print('V112: uruchamiam nowy kod i fizyczne EQ na ODLACZONEJ kopii '
              'prawdziwej bazy, localhost, przed STOP...',flush=True)
        try:
            result=subprocess.run([sys.executable,'-u','-c',script],cwd=staged_root,
                env=env,capture_output=True,text=True,stdin=subprocess.DEVNULL,
                timeout=timeout)
        except subprocess.TimeoutExpired as exc:
            raise UpdateError('v112: rozruch na kopii bazy przekroczyl limit; '
                              'STOP zabroniony.') from exc
        except OSError as exc:
            raise UpdateError('v112: nie mozna uruchomic probnego serwera: '+str(exc)) from exc
        if (result.returncode!=0 or
            'V112 PRODUCTION-COPY BOOT PASS' not in result.stdout):
            details=(result.stdout+'\n'+result.stderr).strip()[-1300:]
            raise UpdateError('v112: rozruch na kopii PRAWDZIWEJ bazy FAIL; '
                              'produkcja nietknieta. '+details)
        print('V112: pelny rozruch na kopii bazy, fizyczne EQ, '
              '38 klas / 38 ras / questy: PASS. Bez zmian produkcji.',flush=True)


def v112_confirm_backup(root: Path, backup: Path) -> None:
    """After confirmed STOP, prove source database and WAL were copied 1:1."""
    for name in ('soulbound.db','soulbound.db-wal','soulbound.db-shm'):
        source=Path(root)/name
        if source.is_file():
            copy=Path(backup)/name
            if not copy.is_file() or sha256_file(source)!=sha256_file(copy):
                raise UpdateError('v112: backup nie zachowal pliku '+name+'. STOP; bez instalacji.')


def sha256_file(file: Path) -> str:
    digest=hashlib.sha256()
    with Path(file).open('rb') as source:
        for chunk in iter(lambda: source.read(1024*1024),b''):
            digest.update(chunk)
    return digest.hexdigest()


def run_update(root: Path, archive_path: Path, new_version: str, *, restart: bool = True, fresh: bool = True) -> Path:
    if new_version != '112.00.0':
        raise UpdateError('Biezacy aktualizator v112 nie instaluje starszych wydan.')
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
    # The ZIP was verified IN FULL above. Only the approved production subset
    # is staged/installed and placed into the permanent activation manifest.
    # Prior installed historical audits are retired separately only if their
    # unchanged SHA matches the previously certified installation manifest.
    if new_version in ('111.00.0','112.00.0'):
        mapping = v111_live_release_mapping(mapping)
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
        # The only activation contract allowed to install this code is v112.
        state=json.loads((root.parent/'Soulbound_PREDEPLOY'/'last_result.json').read_text(encoding='utf-8'))
        from systems.v11200_activation import activation_manifest,verify
        marker=stage/'LIVE_CONTENT'/'release_current.json'
        marker.parent.mkdir(parents=True,exist_ok=True)
        marker.write_text(json.dumps(activation_manifest(state,archive_path,stage,mapping),
                                     sort_keys=True,indent=2)+'\n',encoding='utf-8')
        if not verify(stage):
            raise UpdateError('v112: manifest stagingu nie zgadza sie z kodem; brak STOP.')
        # The ZIP was approved BEFORE staging. The source might change during
        # extraction (download, antivirus or another process). Verify the
        # approved SHA again BEFORE stopping the running server. This is a
        # separate fail-closed check; do not trust the earlier approval alone.
        require_v104_official_predeploy(root, archive_path, new_version)
        if new_version == '112.00.0':
            v112_certified_boot_rehearsal(root, stage)
            # A fresh read-only recheck after the snapshot rehearsal.
            v112_base_preflight(root)
        if fresh:
            # The v110/v111 executable may be corrupted. Never run its STOP,
            # installer or server. The source directory remains unchanged.
            from systems.v11200_fresh_install import (
                target_for, carry_saved_data, publish_clean, FreshInstallError)
            target=target_for(root,new_version)
            if target.exists() or target.is_symlink():
                raise UpdateError('v112: nowy katalog juz istnieje; niczego nie nadpisze: '+str(target))
            if port_open(4000):
                raise UpdateError('v112: port 4000 zajety. Zamknij proces serwera przed czysta instalacja.')
            # No old code is executed in this path.
            backup_existing(root,backup)
            v112_confirm_backup(root,backup)
            try:
                report=carry_saved_data(backup,stage,protected)
                if not verify(stage):
                    raise UpdateError('v112: manifest zmieniony po przeniesieniu zapisow')
                import sqlite3
                from contextlib import closing
                with closing(sqlite3.connect((stage/'soulbound.db').as_uri()+'?mode=ro',uri=True)) as conn:
                    conn.execute('PRAGMA query_only=ON')
                    if conn.execute('PRAGMA quick_check').fetchone()!=('ok',):
                        raise UpdateError('v112: kopia graczy nie jest integralna')
                    if not conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='v107_eq_production_cutover'").fetchone():
                        raise UpdateError('v112: nowy katalog nie zachowal rejestru EQ')
                publish_clean(stage,target,verify)
            except (FreshInstallError, OSError, sqlite3.Error) as exc:
                raise UpdateError('v112: czysta instalacja nieudana, stary folder nietkniety: '+str(exc)) from exc
            print('V112: CZYSTA INSTALACJA PASS; nowy katalog: '+str(target),flush=True)
            print('Zapisow SQLite: '+str(report['sqlite_files'])+'; tabel: '+str(report['tables_checked'])+'; plikow prywatnych: '+str(report['private_files']),flush=True)
            print('Stara gra i pelny backup pozostaja niezmienione.',flush=True)
            if restart and os.name == 'nt':
                subprocess.Popen([os.environ.get('COMSPEC','cmd.exe'),'/d','/c',str(target/'START_Soulbound.bat')],cwd=str(target))
                print('Uruchomiono v112 z NOWEGO katalogu.',flush=True)
            return backup
        raise UpdateError('v112: instalacja w miejscu jest wylaczona; wymagana czysta instalacja')
        stop_local_server(root)
        backup_existing(root, backup)
        if new_version == '112.00.0':
            v112_confirm_backup(root, backup)
        # The broken old release is only a source of SQLite data and settings.
        # No old release migration, activation or cleanup scripts run here.
        installed=False
        try:
            install_stage(root,stage,backup)
            installed=True
            from systems.v11200_activation import verify
            if (file_version(root/'core/bootstrap_economy_professions.py')!=new_version
                 or not verify(root)):
                raise UpdateError('v112: zainstalowany kod nie zgadza sie z manifestem.')
            from contextlib import closing
            import sqlite3
            with closing(sqlite3.connect((root/'soulbound.db').as_uri()+'?mode=ro',uri=True)) as conn:
                conn.execute('PRAGMA query_only=ON')
                if not conn.execute("SELECT 1 FROM sqlite_master WHERE name='v107_eq_production_cutover'").fetchone():
                    raise UpdateError('v112: brak rejestru fizycznego EQ.')
                if conn.execute('PRAGMA quick_check').fetchone()[0]!='ok':
                    raise UpdateError('v112: niespojna baza SQLite.')
            print('V112: manifest i spojnosc SQLite/EQ PASS.',flush=True)
        except BaseException:
            if installed:
                _restore_prior_code_after_v108_cutover_failure(root,backup,set(mapping)|{
                    Path('LIVE_CONTENT/release_current.json')})
            raise
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
    parser.add_argument('--fresh', action='store_true', help='Zainstaluj v112 do NOWEGO katalogu (bez uruchamiania starej wersji).')
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
        print('V112: zapisze pelny backup, a nowa gre utworze w osobnym katalogu. Stary silnik pozostanie nietkniety.',flush=True)
        if not args.yes:
            if input('Wpisz TAK, aby zaktualizowac: ').strip().upper() != 'TAK':
                print('Anulowano, nie dokonano zmian.', flush=True)
                return 0
        run_update(root, new_zip, new_ver, restart=not args.no_start, fresh=True)
        return 0
    except (UpdateError, OSError, RuntimeError, zipfile.BadZipFile, subprocess.TimeoutExpired) as exc:
        print(f'BLAD: {exc}', file=sys.stderr, flush=True)
        print('Nie wymuszono zatrzymania zadnego procesu.', flush=True)
        return 1


if __name__ == '__main__':
    sys.exit(main())
