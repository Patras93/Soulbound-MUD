# -*- coding: utf-8 -*-
"""Offline predeploy candidate ZIP in disposable workspace, never in production.

Source-controlled quality gate: tests the EXACT future release contents. The
working Soulbound server can stay online; all test databases are temporary.
"""
from __future__ import annotations
import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tempfile
import time
import zipfile

ROOT = Path(__file__).resolve().parent
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
    temp=STATE.with_name('.last_result.json.tmp')
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


def run_tests(stage_root, logpath):
    env=os.environ.copy()
    for key in list(env):
        if key.upper().startswith(('SOULBOUND_', 'RAILWAY_')) or key.upper() in ('DATABASE_URL', 'PYTHONPATH'):
            env.pop(key, None)
    env.update(PYTHONUTF8='1',PYTHONIOENCODING='utf-8',PYTHONUNBUFFERED='1',
               PYTHONDONTWRITEBYTECODE='1')
    # Test a read-only *snapshot* of current player SQLite. The candidate
    # opens the real source only using sqlite3 mode=ro and writes to tmp.
    live = Path(os.environ.get('SOULBOUND_DB') or str(ROOT / 'soulbound.db'))
    if not live.is_absolute():
        live = ROOT / live
    env['SOULBOUND_ULTRA_SOURCE_DB'] = str(live.resolve())
    flags = getattr(subprocess, 'CREATE_NEW_PROCESS_GROUP', 0) if os.name=='nt' else 0
    proc = subprocess.Popen([sys.executable, '-u', str(stage_root/'testuj_soulbound_windows.py')],
                            cwd=stage_root, env=env, creationflags=flags,
                            start_new_session=(os.name!='nt'), stdin=subprocess.DEVNULL,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            encoding='utf-8',errors='replace',bufsize=1)
    with logpath.open('a', encoding='utf-8',errors='replace') as out:
        try:
            assert proc.stdout is not None
            for line in proc.stdout:
                print(line,end='',flush=True)
                out.write(line)
            return proc.wait()
        except BaseException:
            if proc.poll() is None:
                if os.name=='nt':
                    subprocess.run(['taskkill','/PID',str(proc.pid),'/T','/F'],
                                   stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
                else:
                    proc.kill()
                proc.wait()
            raise


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
        print('Serwer nie jest zatrzymywany; z prawdziwej bazy powstaje kopia TYLKO DO ODCZYTU.',flush=True)
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
            verified=(result==0 and staged_log.is_file() and
                      'WYNIK KONCOWY: PASS - WSZYSTKIE 60 ETAPOW PLUS' in
                      staged_log.read_text(encoding='utf-8',errors='replace') and
                      'PLUS CHECKS PASS' in staged_log.read_text(encoding='utf-8',errors='replace'))
        # Verify archive was not modified during test execution.
        verified=verified and sha256(zip_path)==checksum
        state['finished_at']=datetime.now().astimezone().isoformat(timespec='seconds')
        state['status']='PASS' if verified else 'FAIL'
        state['completed_stages']=60 if verified else 0
        state['returncode']=result
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
