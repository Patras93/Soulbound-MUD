# -*- coding: utf-8 -*-
"""Independent, non-deploying v107 Windows audit. Never opens production SQLite.

This is a test of candidate code, *not* an approval of deployment.
The actual 60/60 PLUS Windows PREDEPLOY must run separately after all
release blockers are removed and on the real installation's DB copy.
"""
from __future__ import annotations

import ast
from datetime import datetime
import os
from pathlib import Path
import re
import shutil
import socket
import signal
import subprocess
import sys
import tempfile
import time

ROOT = Path(__file__).resolve().parent
SCRIPT = 'validation.v10700_release_readiness'
SUITES = (
    ('Historyczny v85: TCP szczury, realna walka, SQLite i sprzatanie',
     'v8500_native_tcp_full_journey', (), 300),
    ('2000 questow, klasy, rasy, profesje i SQLite', 'v10700_consolidated_content_regression', (), 180),
    ('Autoryzowana aktywacja v107 i bezlimitu po 800 bez stagingu', 'v10700_activation_regression', (), 240),
    ('Instalacja v106 do v107, backup i zgodny znacznik', 'v10700_upgrade_activation_install_regression', (), 90),
    ('Wydarzenia Chaosu - rotacja godzinowa i questy', 'v10700_events_rotation_regression', (), 90),
    ('Pomost v106 do v107 - kontrola zgody i SHA256', 'v10700_installer_bridge_regression', (), 90),
    ('EQ SQLite - bank, magazyn, ewolucja na klonie', 'v10700_eq_ledger_live_clone_regression', (), 90),
    ('EQ: poczta, mieszkania, modyfikacje, dynamiczne ID', 'v10700_eq_untracked_locations_regression', (), 90),
    ('EQ: surowe bank transfer i skrzynia domowa musza odmowic', 'v10700_eq_route_guards_regression', (), 90),
    ('EQ: SQLite blokuje nieksiegowane operacje ze sprzetem', 'v10700_equipment_write_barrier_regression', (), 90),
    ('EQ: fizyczne kopie przechodza tylko przez atomowe adaptery', 'v10700_equipment_barrier_real_adapters', (), 90),
    ('EQ: zapis transakcji cofa sie bez zmiany bazy zrodlowej', 'v10700_eq_real_backup_rehearsal_regression', (), 120),
    ('EQ: autoryzowana migracja i ewolucja kopii, backup nietkniety', 'v10700_production_eq_cutover_regression', (), 120),
    ('Windows: zamykanie polaczen SQLite przed kasowaniem TEMP', 'v10700_windows_sqlite_handle_regression', (), 120),
    ('EQ: kowal, przekucia i runy nie traca zasobow', 'v10700_forge_resource_guard_regression', (), 90),
    ('PREDEPLOY Windows: PID testu, nie EOF procesow potomnych', 'v10700_predeploy_output_regression', (), 30),
    ('Optymalizacja mapy/NPC bez zmian wynikow', 'v10700_catalog_performance_regression', (), 120),
    ('Magitek - podstawy', 'v10700_magitek_regression', (), 120),
    ('Magitek - wsparcie', 'v10700_magitek_support_regression', (), 120),
    ('Magitek - Magicite', 'v10700_magitek_magicite_regression', (), 120),
    ('Magitek - Diffuser', 'v10700_magitek_diffuser_regression', (), 120),
    ('Magitek - wybor celu', 'v10700_magitek_target_router_regression', (), 120),
    ('Bez dawnych rajdow - v106 wylaczone', 'v10700_no_raids_regression', (), 180),
    ('Bez dawnych rajdow - v106 wlaczone', 'v10700_no_raids_regression', ('--with-v106',), 180),
    ('Ratowanie postaci z dawnych rajdow', 'v10700_raid_character_rescue_regression', (), 180),
    ('Kraina Owadów - pierwsza czesc', 'v10700_insects_expansion_regression', (), 120),
    ('Kraina Owadów - zadania SQLite', 'v10700_insects_quest_sqlite_regression', (), 120),
    ('Kraina Owadów - druga czesc', 'v10700_insects_plus_regression', (), 120),
    ('Kraina Owadów - druga czesc SQLite', 'v10700_insects_plus_sqlite_regression', (), 120),
    ('Pierwsze 5 krain - swiat', 'v10700_chaos_chapter_one_regression', (), 120),
    ('Pierwsze 5 krain - SQLite', 'v10700_chaos_chapter_one_sqlite_regression', (), 120),
    ('Pozostale 25 krain - swiat', 'v10700_chaos_30_realms_regression', (), 120),
    ('Pozostale 25 krain - SQLite', 'v10700_chaos_30_realms_sqlite_regression', (), 120),
)
DB_SUFFIXES = ('.db', '.db-wal', '.db-shm', '.sqlite', '.sqlite-wal', '.sqlite-shm',
               '.sqlite3', '.sqlite3-wal', '.sqlite3-shm')
SKIP_DIRS = {'logs', '__pycache__', '.git', '.venv', 'venv', 'backups', 'backup',
             'nowe_wersje', '.pytest_cache', '.mypy_cache'}


def ignored(folder: str, names: list[str]) -> set[str]:
    out = set()
    base = Path(folder)
    for name in names:
        p = base / name
        if (name.lower() in SKIP_DIRS or p.is_symlink() or
                name.lower().endswith(('.zip', '.log') + DB_SUFFIXES) or
                (p.is_file() and p.stat().st_size > 50_000_000)):
            out.add(name)
    return out


def check_sources(stage: Path) -> tuple[int, str]:
    version = (stage / 'VERSION').read_text(encoding='utf-8-sig').strip()
    bootstrap = (stage / 'core/bootstrap_economy_professions.py').read_text(encoding='utf-8-sig')
    actual = re.search(r'^\s*VERSION\s*=\s*[\'"](\d+\.\d+\.\d+)[\'"]', bootstrap, re.M)
    if version not in ('107.00.0','108.00.0','109.00.0') or actual is None or actual.group(1) != version:
        raise RuntimeError('Niezgodne VERSION i kod gry v107.')
    sources = list(stage.rglob('*.py'))
    if not sources:
        raise RuntimeError('Brak zrodel Python w kopii testowej.')
    for path in sources:
        try:
            ast.parse(path.read_text(encoding='utf-8-sig'), filename=str(path))
        except (SyntaxError, UnicodeError) as exc:
            raise RuntimeError(f'Blad skladni: {path.relative_to(stage)}: {exc}') from exc
    if any(p.is_file() and p.name.lower().endswith(DB_SUFFIXES) for p in stage.rglob('*')):
        raise RuntimeError('Kopia testowa zawiera baze SQLite - przerwano.')
    return len(sources), version


def call(stage: Path, module: str, args: tuple[str, ...] = (), seconds: int = 120):
    env = dict(os.environ)
    # Do not pass any live DB, Windows control file, secret or hosting port to
    # the tested child. A private test DB and seed are created per invocation.
    for key in ('SOULBOUND_DB', 'SOULBOUND_ULTRA_SOURCE_DB',
                'SOULBOUND_V106_STAGING', 'PORT', 'RAILWAY_TCP_APPLICATION_PORT',
                'RAILWAY_VOLUME_MOUNT_PATH', 'DATABASE_URL',
                'SOULBOUND_WORLD_SEED_FILE', 'SOULBOUND_WORLD_SEED',
                'SOULBOUND_ADMIN_ACCOUNTS', 'SOULBOUND_CONTROL_FILE',
                'SOULBOUND_CONTROL_TOKEN', 'SOULBOUND_SMTP_PASSWORD',
                'SOULBOUND_MAIL_PASSWORD', 'SMTP_PASSWORD'):
        env.pop(key, None)
    env['SOULBOUND_V107_STAGING'] = '1'
    # Regressions inherited by v109 run ONLY against isolated TEMP SQLite.
    # Keep the v109 production guard active: both flags and the TEMP-path
    # restriction are enforced by systems.v10900_staging_guard.
    check_version = (stage / 'VERSION').read_text(encoding='utf-8-sig').strip()
    if check_version in ('109.00.0', '110.00.0'):
        env['SOULBOUND_V109_STAGING'] = '1'
        # Only disposable TCP lab subtrees are accepted by the v108 guard.
        env['SOULBOUND_V108_PREDEPLOY'] = '1'
    if check_version == '110.00.0':
        # Only under TEMP/sb110_*; never a live DB or installed game tree.
        env['SOULBOUND_V110_STAGING'] = '1'
    env['SOULBOUND_HOST'] = '127.0.0.1'
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    env['PYTHONIOENCODING'] = 'utf-8'
    env['PYTHONUTF8'] = '1'
    cmd = [sys.executable, '-B', '-m', module, *args]
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix='sb110_legacy_db_' if check_version == '110.00.0' else 'soulbound_107_test_db_') as test_home:
        env['SOULBOUND_DB'] = str(Path(test_home)/'audyt_test.sqlite')
        env['SOULBOUND_WORLD_SEED_FILE'] = str(Path(test_home)/'test_seed.txt')
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
            probe.bind(('127.0.0.1', 0))
            env['SOULBOUND_PORT'] = str(probe.getsockname()[1])
        flags = subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
        # A gate may spawn a descendant which inherits stdout.  Waiting for
        # PIPE EOF with communicate() can falsely time out after the direct
        # test process already exited.  The spool does not depend on that EOF.
        with tempfile.TemporaryFile(mode='w+b') as spool:
            p = subprocess.Popen(cmd, cwd=stage, env=env, stdout=spool,
                                 stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL,
                                 creationflags=flags, start_new_session=(os.name != 'nt'))
            timed_out = False
            try:
                code = p.wait(timeout=seconds)
            except subprocess.TimeoutExpired:
                timed_out = True
                code = 124
                if os.name == 'nt':
                    # Kill only this test's own process tree; never live game.
                    try:
                        subprocess.run(['taskkill', '/PID', str(p.pid), '/T', '/F'],
                                       stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                       stderr=subprocess.DEVNULL, timeout=15, check=False)
                    except (OSError, subprocess.TimeoutExpired):
                        p.kill()
                else:
                    try:
                        os.killpg(p.pid, signal.SIGKILL)
                    except ProcessLookupError:  # AUDIT_INTENTIONAL_PASS: child already ended
                        pass
                if p.poll() is None:
                    p.kill()
                p.wait(timeout=15)
            spool.seek(0)
            output = spool.read().decode('utf-8', errors='replace')
            elapsed = round(time.monotonic() - started, 1)
            if timed_out:
                return 124, output[-1000:] + '\nPRZEKROCZONO CZAS TESTU; NIE WDRAZAJ.', elapsed
            return code, output, elapsed


def main() -> int:
    stamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log = ROOT / 'logs' / f'AUDYT_V107_WINDOWS_{stamp}.log'
    log.parent.mkdir(parents=True, exist_ok=True)
    with log.open('w', encoding='utf-8', buffering=1) as fp:
        def say(msg=''):
            print(msg, flush=True)
            fp.write(msg+'\n')
        say('SOULBOUND v107.00.0 - AUDYT KODU WINDOWS PRZED PREDEPLOY')
        say('Katalog: '+str(ROOT))
        say('Python: '+sys.version.splitlines()[0])
        say('Baza graczy: NIE OTWIERANA. Serwer produkcyjny: NIE ZATRZYMYWANY.')
        say('Testy v107 w kopii tymczasowej, bez wdrazania.')
        if not (ROOT / 'VERSION').is_file():
            say('FAIL: Nie znaleziono VERSION. Rozpakuj pelny ZIP.');return 2
        if os.name == 'nt' and sys.version_info < (3, 12):
            say('FAIL: Wymagany Python 3.12 lub nowszy.');return 2
        try:
            with tempfile.TemporaryDirectory(prefix='soulbound_v107_windows_audit_') as directory:
                stage = Path(directory) / 'Soulbound-MUD'
                shutil.copytree(ROOT, stage, ignore=ignored)
                count, version = check_sources(stage)
                say(f'SKLADNIA: PASS ({count} plikow Python); VERSION: {version}')
                failures = 0
                for index, (name, script, args, deadline) in enumerate(SUITES, 1):
                    code, output, elapsed = call(stage, 'validation.'+script, args, deadline)
                    say(f'{index:02d}/{len(SUITES)} {"PASS" if code == 0 else "FAIL"}: {name} ({elapsed:.1f} s)')
                    if output.strip():
                        # Keep the final messages and error trace accessible in the log.
                        fp.write(output.rstrip()+'\n')
                    if code:
                        failures += 1
                        say('  Powod: kod '+str(code)+'; '+output.strip()[-500:])
                code, readiness, elapsed = call(stage, SCRIPT, (), 30)
                say('GOTOWOSC PRODUKCYJNA: '+('PASS' if code == 0 else 'FAIL'))
                if readiness.strip():
                    say(readiness.rstrip())
                if failures:
                    say(f'WYNIK: FAIL; {failures}/{len(SUITES)} testow kodu nie przeszlo. NIE WDRAZAJ.')
                    return 1
                say(f'TESTY KODU v107: PASS {len(SUITES)}/{len(SUITES)}.')
                if code:
                    say('WYNIK PRODUKCYJNY: FAIL - blokady wymagaja naprawy. Nie uruchamiaj WDROZ_PO_PREDEPLOY.bat.')
                    return 3
                # Even a green release-readiness check is not enough for deployment.
                say('WYNIK: KOD PRZESZEDL; uruchom osobno PREDEPLOY_NOWEJ_WERSJI.bat 60/60 PLUS na Windows.')
                say('Zgoda na wdrozenie jest mozliwa dopiero po oficjalnym PREDEPLOY 60/60 PLUS.')
                return 0
        except (OSError, RuntimeError, shutil.Error) as exc:
            say('FAIL: Blad audytu: '+type(exc).__name__+': '+str(exc))
            return 2
        finally:
            say('LOG AUDYTU: '+str(log))


if __name__ == '__main__':
    raise SystemExit(main())
