# -*- coding: utf-8 -*-
"""All 33 v107 safety/content slots on v110, adapting legacy-only assumptions.

Obsolete installer checks, exactly-30 registry assumptions, and an obsolete
TCP scratch-path are replaced by v110 compatibility checks. The functional
EQ/quest/combat coverage remains active in v110 equivalents, and the real
six-player TCP test runs separately as an obligatory fourth v110 gate. Independent v110 6/6 TCP, release, and
snapshot checks remain separately mandatory during Windows PREDEPLOY.
"""
from __future__ import annotations
import ast,os,shutil,sys,tempfile,subprocess,socket,signal,time,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
# The current v111 gate owns its 33 audit specs and isolated runner.
# No dependency on the v107 standalone launcher or previous installations.
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
REPLACEMENTS={
 'v8500_native_tcp_full_journey':('V110: dawna bramka TCP zachowana; 6 graczy osobno obowiązkowo','v11000_v85_tcp_compat'),
 'v10700_consolidated_content_regression':('V110: komplet zawartości v107, 30 historycznych klas i ras','v11100_holiday_contract'),
 'v10700_equipment_write_barrier_regression':('V110: pełna ochrona fizycznego EQ bez starych instalatorów','v11000_equipment_barrier_compat'),
 'v10700_activation_regression':('V110: manifest instalacji i niezmienność plików','v11100_release_activation_regression'),
 'v10700_upgrade_activation_install_regression':('V110: rzeczywisty test aktualizatora i backupu','v11100_release_activation_regression'),
 'v10700_installer_bridge_regression':('V110: tylko WDRAZAM oraz SHA','v11100_release_activation_regression'),
}

# Immutable review contract for the v111-inherited 33 historical behaviors.
SUITES_REVIEW_SHA256 = '7891f1f076dba8596aff41d666469c0f9f50abee196c2b42f12ba0760e693301'


def suites_reviewed():
    return (len(SUITES)==33 and len({(name,script,args) for name,script,args,deadline in SUITES})==33
            and hashlib.sha256(repr(SUITES).encode()).hexdigest()==SUITES_REVIEW_SHA256)


def main():
    if not suites_reviewed():
        print('V111 V107 AUDIT FAIL: zmieniono zestaw 33 bramek',flush=True)
        return 2
    if (ROOT/'VERSION').read_text(encoding='utf-8-sig').strip()!='111.00.0':
        print('V111/V107 AUDIT FAIL: expected v111 source',flush=True)
        return 2
    checked=0;fails=[]
    with tempfile.TemporaryDirectory(prefix='sb111_audit_code_') as temp:
        stage=Path(temp)/'Soulbound-MUD'
        shutil.copytree(ROOT,stage,ignore=ignored)
        srcs=list(stage.rglob('*.py'))
        for p in srcs:
            ast.parse(p.read_text(encoding='utf-8-sig'),filename=str(p))
        if not srcs:raise AssertionError('No source files in private audit')
        print(f'V111 V107 AUDIT: {len(srcs)} AST-valid sources, private TEMP only',flush=True)
        for n,(title,module,args,deadline) in enumerate(SUITES,1):
            if module in REPLACEMENTS:
                title,module=REPLACEMENTS[module]
                args=()
            code,output,duration=call(stage,'validation.'+module,args,deadline)
            checked+=1
            print(f'{n:02d}/{len(SUITES)} {"PASS" if code==0 else "FAIL"} '
                  f'{title}: {duration}s',flush=True)
            if code:
                fails.append((title,output[-550:]))
                print('REASON: '+output[-550:],flush=True)
        code,output,duration=call(stage,'validation.v11100_release_readiness',(),60)
        if code: fails.append(('V110 readiness',output[-550:]));print('READINESS FAIL '+output[-550:],flush=True)
        else:print('V110 READINESS: PASS',flush=True)
    if fails:
        print(f'V111/V107 FUNCTIONAL AUDIT FAIL: {len(fails)} failures / {checked} historical slots',flush=True)
        return 1
    print(f'V111/V107 FUNCTIONAL AUDIT PASS: {checked}/{len(SUITES)} slots; '
          f'{len(REPLACEMENTS)} legacy-only slots adapted with v110 safety and functional tests',flush=True)
    return 0

if __name__=='__main__':raise SystemExit(main())
