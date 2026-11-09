# -*- coding: utf-8 -*-
"""Offline predeploy candidate ZIP in disposable workspace, never in production.

Source-controlled quality gate: tests the EXACT future release contents. The
working Soulbound server can stay online; all test databases are temporary.
"""
from __future__ import annotations
import argparse
import signal
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import sqlite3
from contextlib import closing
import stat
import subprocess
import sys
import tempfile
import time
import zipfile

ROOT = Path(os.environ.get('SOULBOUND_LIVE_ROOT') or Path(__file__).resolve().parent).resolve()
WORK = ROOT.parent / 'Soulbound_PREDEPLOY'
INBOX = ROOT / 'NOWE_WERSJE'
STATE = WORK / 'last_result.json'
PATTERN = re.compile(r'^Soulbound-MUD-v(\d+\.\d+\.\d+).*\.zip$', re.I)
VERSION = re.compile(r'^\s*VERSION\s*=\s*[\'\"](\d+\.\d+\.\d+)[\'\"]', re.M)
REQUIRED = ('server.py', 'CHANGELOG_PL.txt', 'core/bootstrap_economy_professions.py',
            'testuj_soulbound_windows.py', 'predeploy_check.py', 'predeploy_full.py',
            'validation/v2102_tcp_six_players.py', 'validation/predeploy_ultra_v2327.py',
            'validation/predeploy_ultimate_v2328.py', 'validation/predeploy_ultimate60_v2329.py',
            'validation/predeploy_plus_v2330.py',
            'validation/predeploy_plus_gate_v2330.py',
            'START_Soulbound.bat',
            'STOP_Soulbound.bat', 'Dockerfile')
SKIP = {'__pycache__', 'logs', '.git'}
BAD_EXT = ('.db', '.db-wal', '.db-shm', '.sqlite', '.sqlite-wal', '.sqlite-shm',
           '.sqlite3', '.sqlite3-wal', '.sqlite3-shm')


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024*1024), b''):
            digest.update(block)
    return digest.hexdigest()


def version_tuple(s):
    return tuple(int(n) for n in s.split('.'))


def installed_version():
    verfile = ROOT / 'core' / 'bootstrap_economy_professions.py'
    m = VERSION.search(verfile.read_text(encoding='utf-8-sig'))
    if not m:
        raise ValueError('Brak numeru wersji aktualnej gry')
    return m.group(1)


def pick_zip(selected):
    if selected:
        return Path(selected).expanduser().resolve()
    if not INBOX.is_dir():
        raise ValueError('Brak folderu NOWE_WERSJE. Utworz go przy grze i skopiuj tam nowy ZIP.')
    choices = []
    for p in INBOX.glob('*.zip'):
        m = PATTERN.fullmatch(p.name)
        if m:
            choices.append((version_tuple(m.group(1)), p.stat().st_mtime, p))
    if not choices:
        raise ValueError('Brak Soulbound-MUD-vX.Y.Z*.zip w NOWE_WERSJE.')
    return max(choices)[2].resolve()


def inspect_zip(zippath):
    if not zippath.is_file():
        raise ValueError('Brak ZIP: '+str(zippath))
    m = PATTERN.fullmatch(zippath.name)
    if not m:
        raise ValueError('Nazwa musi zaczynac sie Soulbound-MUD-vX.Y.Z i konczyc .zip')
    with zipfile.ZipFile(zippath) as z:
        entries = [i for i in z.infolist() if not i.is_dir()]
        if not entries or len(entries) > 3000:
            raise ValueError('Paczka pusta albo za duzo plikow.')
        if sum(i.file_size for i in entries) > 300*1024*1024:
            raise ValueError('Paczka za duza - mozliwy ZIP bomb.')
        prefixes = {i.filename.split('/')[0] for i in entries}
        strip_top = prefixes == {'Soulbound-MUD'}
        mapping = {}
        for i in entries:
            s=i.filename
            if (s.startswith('/') or '\\' in s or ':' in s or '\x00' in s
                or (i.external_attr >> 16) & 0o170000 == stat.S_IFLNK):
                raise ValueError('Niebezpieczny wpis ZIP: '+s)
            parts = s.split('/')
            if any(part in ('', '.', '..') for part in parts):
                raise ValueError('Niebezpieczna sciezka ZIP: '+s)
            rel = '/'.join(parts[1:] if strip_top else parts)
            if not rel:
                raise ValueError('Niepelna struktura ZIP')
            key=rel.casefold()
            if key in mapping:
                raise ValueError('Zdublowana nazwa w ZIP: '+rel)
            mapping[key]=(rel, i)
            if rel.lower().endswith(BAD_EXT):
                raise ValueError('ZIP zawiera baze postaci ('+rel+'). Nie testuje wydania z baza.')
        for need in REQUIRED:
            if need.casefold() not in mapping:
                raise ValueError('Brak wymaganego pliku: '+need)
        body = z.read(mapping['core/bootstrap_economy_professions.py'][1]).decode('utf-8-sig')
        version_match=VERSION.search(body)
        ver=version_match.group(1) if version_match else None
        if ver != m.group(1):
            raise ValueError(f'Numer wersji pliku gry {ver} nie zgadza sie z ZIP v{m.group(1)}')
        # Both version markers must agree. Historically an RC archive could
        # advertise v104 while leaving its actual game at v103.
        root_version = mapping.get('version')
        if root_version is None:
            raise ValueError('Brak pliku VERSION w kandydacie.')
        root_text = z.read(root_version[1]).decode('utf-8-sig').strip()
        if root_text != ver:
            raise ValueError(f'Plik VERSION ({root_text}) nie zgadza sie z kodem ({ver}).')
        if ver in ('108.00.0','109.00.0'):
            for required_v108 in ('validation/v10800_release_readiness.py',
                                  'validation/v10800_offline_suite.py',
                                  'systems/v10800_activation.py',
                                  'validation/v10800_v107_equipment_compat_gate.py'):
                if required_v108.casefold() not in mapping:
                    raise ValueError('v108: brak produkcyjnej bramki '+required_v108+
                                     '; stare 60/60 nie wystarcza')
        if ver == '110.00.0':
            for needed in ('systems/v11000_activation.py',
                           'world/v11000_realms.py',
                           'core/v11000_archetypes.py',
                           'validation/v11000_release_suite.py',
                           'validation/v11000_release_readiness.py'):
                if needed.casefold() not in mapping:
                    raise ValueError('v110: brak niezależnej bramki '+needed)
            if 'live_content/release_current.json' in mapping:
                raise ValueError('v110: manifest wydania generuje tylko instalator po PASS')
        if ver == '109.00.0':
            for needed in ('systems/v10900_activation.py', 'systems/v10900_gifts.py',
                           'world/v10900_horizons.py', 'validation/v10900_release_suite.py',
                           'validation/v10900_release_readiness.py'):
                if needed.casefold() not in mapping:
                    raise ValueError('v109: brak wymaganej bramki: '+needed)
            if 'live_content/v109_release_activation.json' in mapping:
                raise ValueError('v109: instalacyjnego znacznika aktywacji nie wolno umieszczać w ZIP')
        invalid = z.testzip()
        if invalid:
            raise ValueError('Uszkodzony plik w ZIP: '+invalid)
    return ver, mapping


def source_review(stage_root):
    """Human-readable change list; never treat file comparison as semantic balance test."""
    important = ('server.py', 'data/', 'systems/', 'core/', 'player/',
                 'storage/', 'world/', 'quests/')
    changes=[]
    for candidate in sorted(stage_root.rglob('*')):
        if not candidate.is_file():
            continue
        rel=candidate.relative_to(stage_root).as_posix()
        if not any(rel == x or (x.endswith('/') and rel.startswith(x)) for x in important):
            continue
        installed=ROOT/rel
        if not installed.is_file() or sha256(installed)!=sha256(candidate):
            changes.append(rel)
    return changes


def save_state(state):
    WORK.mkdir(parents=True,exist_ok=True)
    temp=STATE.with_name('.'+STATE.name+'.tmp')
    try:
        temp.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding='utf-8')
        os.replace(temp, STATE)
    finally:
        temp.unlink(missing_ok=True)


def stage(zip_path, target, mapping):
    # Every candidate source resides inside an isolated temporary folder.
    with zipfile.ZipFile(zip_path) as z:
        for rel,info in mapping.values():
            if any(p.lower() in SKIP for p in rel.split('/')):
                continue
            out = target.joinpath(*rel.split('/'))
            out.parent.mkdir(parents=True,exist_ok=True)
            with z.open(info) as src, out.open('wb') as dst:
                shutil.copyfileobj(src,dst)


def _terminate_test_tree(proc):
    """Kill timed-out Windows tests and their children; Unix process group."""
    if proc.poll() is not None:
        return
    if os.name == 'nt':
        # The test may have created several local TCP children. Killing only
        # the parent leaves them running and can disrupt later test attempts.
        try:
            subprocess.run(['taskkill', '/PID', str(proc.pid), '/T', '/F'],
                           stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                           stderr=subprocess.DEVNULL, timeout=15, check=False)
        except (OSError, subprocess.TimeoutExpired) as exc:
            print('OSTRZEZENIE: taskkill nie potwierdzil zamkniecia drzewa: '+str(exc), file=sys.stderr)
    else:
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except ProcessLookupError:
            # Group already ended; still verify the direct child below.
            proc.poll()
    if proc.poll() is None:
        proc.kill()
    try:
        proc.wait(timeout=15)
    except subprocess.TimeoutExpired:
        raise TimeoutError('Nie mozna zakonczyc odizolowanego procesu PREDEPLOY.')


def create_detached_source_snapshot(source_db, destination, *, timeout_seconds=180):
    """Capture committed source DB + WAL using SQLite backup, not file copying.

    The production DB is opened with mode=ro and never given to candidate code.
    SQLite backup preserves the committed WAL image without uncommitted rows.
    Nothing in this function upgrades, migrates or modifies source contents.
    The caller owns the destination and must remove it after testing.
    """
    source = Path(source_db).expanduser().resolve()
    destination = Path(destination).expanduser().resolve()
    if source == destination or not source.is_file():
        raise RuntimeError('Brak oddzielnej, istniejacej bazy SQLite do audytu')
    if destination.exists():
        raise RuntimeError('Odmowa nadpisania istniejacej migawki SQLite')
    if not isinstance(timeout_seconds, (int, float)) or not 0 < timeout_seconds <= 3600:
        raise ValueError('Nieprawidlowy limit przygotowania kopii SQLite')
    began = time.monotonic()
    uri = source.as_uri() + '?mode=ro'
    try:
        with closing(sqlite3.connect(uri, uri=True, timeout=4)) as origin:
            origin.execute('PRAGMA query_only=ON')
            tables = {str(row[0]) for row in origin.execute(
                "SELECT name FROM sqlite_master WHERE type='table'")}
            if not {'accounts', 'characters'}.issubset(tables):
                raise RuntimeError('SQLite nie ma tabel kont i postaci')
            with closing(sqlite3.connect(destination, timeout=4)) as frozen:
                def progress(_status, _remaining, _total):
                    if time.monotonic() - began > timeout_seconds:
                        raise TimeoutError('Kopia SQLite przekroczyla limit czasu')
                origin.backup(frozen, pages=128, progress=progress, sleep=0.05)
        with closing(sqlite3.connect(destination.as_uri() + '?mode=ro', uri=True,
                                     timeout=4)) as check:
            if check.execute('PRAGMA integrity_check').fetchone()[0] != 'ok':
                raise RuntimeError('Odlaczona kopia SQLite nie przeszla integrity_check')
            if not {'accounts', 'characters'}.issubset({str(row[0]) for row in
                check.execute("SELECT name FROM sqlite_master WHERE type='table'")}):
                raise RuntimeError('Odlaczona kopia SQLite jest niekompletna')
    except (sqlite3.Error, RuntimeError, TimeoutError):
        # Failure is never a PASS; partially copied file is not reusable.
        destination.unlink(missing_ok=True)
        raise
    return destination


def run_tests(stage_root, logpath, *, timeout_seconds=5400, source_db=None):
    """Run the staged Windows gate against a frozen, disposable SQLite backup.

    Candidate scripts receive only a *detached* snapshot path. The actual live
    path must never enter a child process' SOULBOUND_ULTRA_SOURCE_DB variable.
    A predeploy run cannot silently substitute a synthetic empty database.
    """
    if not isinstance(timeout_seconds, int) or timeout_seconds < 1:
        raise ValueError('Niepoprawny limit czasu PREDEPLOY.')
    env = os.environ.copy()
    for key in list(env):
        if key.upper().startswith(('SOULBOUND_', 'RAILWAY_')) or key.upper() in (
                'DATABASE_URL', 'PYTHONPATH', 'SMTP_PASSWORD', 'PGPASSWORD',
                'AWS_SECRET_ACCESS_KEY', 'AWS_SESSION_TOKEN', 'OPENAI_API_KEY'):
            env.pop(key, None)
    env.update(PYTHONUTF8='1', PYTHONIOENCODING='utf-8', PYTHONUNBUFFERED='1',
               PYTHONDONTWRITEBYTECODE='1')
    live = Path(source_db or os.environ.get('SOULBOUND_DB') or str(ROOT / 'soulbound.db'))
    if not live.is_absolute():
        live = ROOT / live
    ver=(Path(stage_root)/'VERSION').read_text(encoding='utf-8-sig').strip()
    prefix='sb110_predeploy_sqlite_frozen_' if ver == '110.00.0' else 'Soulbound_PREDEPLOY_SQLITE_FROZEN_'
    if ver == '110.00.0':
        env.update(SOULBOUND_V107_STAGING='1',SOULBOUND_V109_STAGING='1',
                   SOULBOUND_V110_STAGING='1')
    with tempfile.TemporaryDirectory(prefix=prefix) as frozen_dir:
        snapshot = create_detached_source_snapshot(
            live, Path(frozen_dir)/'SOURCE_COMMITTED_SNAPSHOT.sqlite')
        # v108 needs the result of a conservative EQ rebuild during PREDEPLOY.
        # The original source and old pre-v107 backup remain read-only. The
        # live installer MUST repeat this rehearsal after STOP, on fresh data.
        if (Path(stage_root)/'VERSION').read_text(encoding='utf-8-sig').strip() == '108.00.0':
            from systems.v10800_eq_cutover_bridge import prepare_from_snapshot
            prepared,counts = prepare_from_snapshot(snapshot,live.parent,Path(frozen_dir))
            snapshot = prepared
            with logpath.open('a',encoding='utf-8') as report:
                report.write('V108 PREDEPLOY REBUILD SNAPSHOT PASS: '
                    +', '.join(f'{k}={v}' for k,v in sorted(counts.items()))+'\n')
        env['SOULBOUND_ULTRA_SOURCE_DB'] = str(snapshot)
        env['SOULBOUND_DB'] = str(snapshot)  # no fallthrough to production
        env['SOULBOUND_HOST'] = '127.0.0.1'
        flags = getattr(subprocess, 'CREATE_NEW_PROCESS_GROUP', 0) if os.name == 'nt' else 0
        with logpath.open('a', encoding='utf-8', errors='replace') as output:
            output.write(f'\nTESTY WINDOWS: limit {timeout_seconds} sekund; '
                         'baza odlaczona przez SQLite backup + WAL.\n')
            output.flush()
            proc = subprocess.Popen(
                [sys.executable, '-u', str(stage_root / 'testuj_soulbound_windows.py')],
                cwd=stage_root, env=env, creationflags=flags,
                start_new_session=(os.name != 'nt'),
                stdin=subprocess.DEVNULL, stdout=output, stderr=subprocess.STDOUT)
            try:
                code = proc.wait(timeout=timeout_seconds)
            except subprocess.TimeoutExpired as error:
                _terminate_test_tree(proc)
                output.write('\nTIMEOUT: Windows PREDEPLOY nie zakonczyl sie; FAIL.\n')
                output.flush()
                raise TimeoutError('Windows PREDEPLOY przekroczyl limit i zostal zakonczony.') from error
            except BaseException:
                _terminate_test_tree(proc)
                raise
            if os.name != 'nt':
                try: os.killpg(proc.pid, signal.SIGKILL)
                except ProcessLookupError: proc.poll()
            output.write(f'\nTESTY WINDOWS: kod wyjscia {code}.\n')
            output.flush()
            return code


def verified_staged_pass(code, staged_log, version):
    """Consume the staged test log BEFORE its TemporaryDirectory is removed."""
    if code != 0 or not Path(staged_log).is_file():
        return False
    log = Path(staged_log).read_text(encoding='utf-8', errors='replace')
    basic = ('WYNIK KONCOWY: PASS - WSZYSTKIE 60 ETAPOW PLUS' in log and
             'PLUS CHECKS PASS' in log)
    if version == '108.00.0':
        basic = basic and 'V108 RELEASE GATES PASS' in log
    elif version == '109.00.0':
        basic = basic and 'V109 RELEASE GATES PASS' in log
    elif version == '110.00.0':
        basic = basic and 'V110 RELEASE GATES PASS' in log
    return basic


def main(argv=None):
    ap=argparse.ArgumentParser(description='Pelny PREDEPLOY osobnej paczki Soulbound ZIP.')
    ap.add_argument('zip_path',nargs='?',help='ZIP (mozesz przeciagnac na BAT)')
    args=ap.parse_args(argv)
    state=None
    start=datetime.now().astimezone().isoformat(timespec='seconds')
    try:
        zip_path=pick_zip(args.zip_path)
        version,mapping=inspect_zip(zip_path)
        active=installed_version()
        if version_tuple(version) < version_tuple(active):
            raise ValueError(f'Nowa paczka v{version} jest starsza od dzialajacej v{active}.')
        checksum=sha256(zip_path)
        WORK.mkdir(parents=True,exist_ok=True)
        (WORK/'logs').mkdir(exist_ok=True)
        stamp=datetime.now().strftime('%Y%m%d-%H%M%S')
        log=WORK/'logs'/f'PREDEPLOY-v{version}-{stamp}.log'
        state={'status':'TESTING','quality_gate':'ULTIMATE-60-PLUS','required_stages':60,'zip':str(zip_path),'version':version,
               'sha256':checksum,'installed_at_test':active,'started_at':start,
               'log':str(log)}
        save_state(state)
        print(f'PREDEPLOY: testowana paczka: {zip_path}',flush=True)
        print(f'Wersja produkcyjna: v{active}; kandydat: v{version}',flush=True)
        print('Serwer pozostaje uruchomiony; testy otrzymaja odlaczona migawke SQLite (WAL).',flush=True)
        print('Testy ULTIMATE PLUS: 60 etapow, >5000 asercji PLUS, migracja LIVE na kopii SQLite.',flush=True)
        print(f'Log: {log}',flush=True)
        with log.open('w',encoding='utf-8') as report:
            report.write(f'PREDEPLOY Soulbound v{version} | {start}\nZIP: {zip_path}\nSHA256: {checksum}\n')
        with tempfile.TemporaryDirectory(prefix='Soulbound_PREDEPLOY_') as scratch:
            target=Path(scratch)/'Soulbound-MUD'
            target.mkdir()
            stage(zip_path,target,mapping)
            differences=source_review(target)
            state['changed_game_files']=differences[:200]
            state['changed_game_file_count']=len(differences)
            save_state(state)
            print(f'POROWNANIE KODU GRY: {len(differences)} plikow roznych od zainstalowanych.',flush=True)
            for change in differences[:30]:
                print('  ZMIANA KODU: '+change,flush=True)
            if len(differences)>30:
                print(f'  ... i {len(differences)-30} dalszych zmian.',flush=True)
            print('To porownanie plikow, nie automatyczna aprobata zmian balansu.',flush=True)
            result=run_tests(target,log)
            # Do not treat a last line from stdout as proof; trust exit status AND log summary.
            staged_log=target/'logs'/'TESTY_Soulbound.log'
            # The staged folder disappears at the end of this with-block.
            # Capture its proof while it still exists, including the v108 gate.
            verified = verified_staged_pass(result, staged_log, version)
        # Verify the exact tested archive has not changed meanwhile.
        if version == '108.00.0':
            state['v108_eq_rebuild_trial_pass'] = ('V108 PREDEPLOY REBUILD SNAPSHOT PASS:'
                                                  in log.read_text(encoding='utf-8',errors='replace'))
            verified = verified and state['v108_eq_rebuild_trial_pass']
        verified=verified and sha256(zip_path)==checksum
        state['finished_at']=datetime.now().astimezone().isoformat(timespec='seconds')
        state['status']='PASS' if verified else 'FAIL'
        state['completed_stages']=60 if verified else 0
        state['returncode']=result
        if version == '108.00.0':
            state['v108_release_gates_pass'] = bool(verified)
        if version == '109.00.0':
            state['v109_release_gates_pass'] = bool(verified)
        if version == '110.00.0':
            state['v110_release_gates_pass'] = bool(verified)
        save_state(state)
        print('\nWYNIK PREDEPLOY: '+state['status'],flush=True)
        print('Produkcja nietknieta. '+('Mozna rozwazyc WDROZ_PO_PREDEPLOY.bat.' if verified
                                    else 'NIE WDRAZAJ. Sprawdz log.'),flush=True)
        print('Pelny log: '+str(log),flush=True)
        return 0 if verified else 1
    except (OSError,ValueError,RuntimeError,zipfile.BadZipFile,UnicodeError,KeyboardInterrupt) as exc:
        print('PREDEPLOY FAIL: '+type(exc).__name__+': '+str(exc),file=sys.stderr,flush=True)
        if state:
            state['status']='FAIL'
            state['error']=str(exc)
            state['finished_at']=datetime.now().astimezone().isoformat(timespec='seconds')
            save_state(state)
        return 2

if __name__=='__main__':
    raise SystemExit(main())
