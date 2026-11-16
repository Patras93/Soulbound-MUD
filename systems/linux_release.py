# -*- coding: utf-8 -*-
"""Soulbound Linux: reproducible PREDEPLOY and conservative first-install/upgrade.

This module operates only on a full current ZIP and a separately supplied SQLite.
Never starts an unapproved candidate, kills a foreign process or overwrites saves.
"""
from __future__ import annotations

import argparse
from contextlib import closing
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import socket
import sqlite3
import subprocess
import sys
import tempfile
import time
import zipfile

ROOT = Path(__file__).resolve().parents[1]
VERSION = (ROOT / 'VERSION').read_text(encoding='utf-8-sig').strip()
MAX_SECONDS = 5400
MAIN_LOG = 'logs/TESTY_Soulbound.log'
SERVICE_NAME = 'soulbound.service'
SERVICE_IDENTITY = '# Managed-By: Soulbound-Linux\n'


class LinuxReleaseError(RuntimeError):
    pass


def require_linux():
    if sys.platform != 'linux':
        raise LinuxReleaseError('Ten instalator wymaga Linux')
    if sys.version_info < (3, 11):
        raise LinuxReleaseError('Wymagany Python 3.11 lub nowszy')


def digest(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1048576),b''):
            h.update(chunk)
    return h.hexdigest()


def load_json(path):
    with Path(path).open('r',encoding='utf-8') as f:
        return json.load(f)


def save_json(path, data):
    path=Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name('.'+path.name+'.'+str(os.getpid())+'.tmp')
    try:
        tmp.write_text(json.dumps(data,ensure_ascii=False,indent=2,sort_keys=True)+'\n',encoding='utf-8')
        os.replace(tmp,path)
    finally:
        tmp.unlink(missing_ok=True)


def _plain_folder(path):
    path=Path(path).expanduser().absolute()
    if path.is_symlink():
        raise LinuxReleaseError('Nie korzystam z dowiazania symbolicznego: '+str(path))
    return path


def source_database(path):
    path=_plain_folder(path)
    if not path.is_file() or path.name.endswith(('-wal','-shm')):
        raise LinuxReleaseError('Nie znaleziono zrodlowej bazy SQLite: '+str(path))
    return path


def snap_database(source, dest):
    """Read-only SQLite API backup, including committed WAL; full row+schema audit."""
    from systems.current_sqlite_integrity import fingerprint, verify_equal
    source=source_database(source)
    dest=Path(dest)
    if dest.exists() or dest.is_symlink() or source.resolve()==dest.resolve():
        raise LinuxReleaseError('Nie nadpisuje istniejacej bazy lub pliku kopii')
    dest.parent.mkdir(parents=True,exist_ok=True)
    try:
        with closing(sqlite3.connect(source.resolve().as_uri()+'?mode=ro', uri=True, timeout=30)) as original:
            original.execute('PRAGMA query_only=ON')
            if original.execute('PRAGMA integrity_check').fetchone()!=('ok',):
                raise LinuxReleaseError('Baza wejsciowa nie przeszla integrity_check')
            if not {'accounts','characters'} <= {r[0] for r in original.execute("SELECT name FROM sqlite_master WHERE type='table'")}:
                raise LinuxReleaseError('Brakuje tabel accounts / characters w bazie wejsciowej')
            with closing(sqlite3.connect(dest)) as copy:
                original.backup(copy, pages=256,sleep=0.1)
                verify_equal(original,copy)
                fp=fingerprint(copy)
        return fp
    except (sqlite3.Error,ValueError) as exc:
        raise LinuxReleaseError('Nieudany backup bazy SQLite: '+str(exc)) from exc


def fingerprint_source(source):
    from systems.current_sqlite_integrity import fingerprint
    source=source_database(source)
    with closing(sqlite3.connect(source.resolve().as_uri()+'?mode=ro',uri=True,timeout=30)) as con:
        con.execute('PRAGMA query_only=ON')
        if con.execute('PRAGMA integrity_check').fetchone()!=('ok',):
            raise LinuxReleaseError('Niepoprawna integralnosc SQLite')
        return fingerprint(con)


def archive_info(archive):
    from aktualizuj_soulbound import archive_mapping, production_release_mapping, read_archive_version
    archive=Path(archive).expanduser().resolve(strict=True)
    if archive.is_symlink() or not archive.is_file():
        raise LinuxReleaseError('Niebezpieczna lokalizacja ZIP')
    if not re.fullmatch(r'Soulbound-MUD-v'+re.escape(VERSION)+r'.*\.zip',archive.name,re.I):
        raise LinuxReleaseError('Nazwa ZIP nie zgadza sie z VERSION '+VERSION)
    with zipfile.ZipFile(archive) as z:
        mapping=archive_mapping(z)
        if any(name.suffix.lower() in ('.bat','.cmd','.vbs','.ps1') for name in mapping):
            raise LinuxReleaseError('Paczka Linux zawiera skrypty Windows')
        if read_archive_version(z,mapping)!=VERSION or z.read(mapping[Path('VERSION')]).decode('utf-8-sig').strip()!=VERSION:
            raise LinuxReleaseError('Niezgodna wersja w ZIP')
        if z.testzip() is not None:
            raise LinuxReleaseError('ZIP CRC FAIL')
        for required in ('systems/linux_release.py','PREDEPLOY_NOWEJ_WERSJI.sh','WDROZ_PO_PREDEPLOY.sh',
                         'validation/current_linux_release_regression.py',
                         'validation/current_linux_deploy_rehearsal.py',
                         'validation/linux_predeploy_runner.py',
                         'validation/linux_legacy_windows_fixtures.py'):
            if Path(required) not in mapping:
                raise LinuxReleaseError('Niepelna paczka Linux: '+required)
        # Current launcher must be byte-identical with archive; otherwise
        # an attacker could forge the receipt with a modified extracted script.
        for required in ('systems/linux_release.py','VERSION','systems/universal_activation.py'):
            if not (ROOT/required).is_file() or digest(ROOT/required)!=hashlib.sha256(z.read(mapping[Path(required)])).hexdigest():
                raise LinuxReleaseError('Zmieniono kod instalatora wzgledem ZIP: '+required)
        return archive, mapping,production_release_mapping(mapping)


def _extract(archive, mapping, destination):
    destination=Path(destination)
    if destination.exists() and any(destination.iterdir()):
        raise LinuxReleaseError('Docelowy staging nie jest pusty')
    destination.mkdir(parents=True,exist_ok=True)
    with zipfile.ZipFile(archive) as z:
        for rel,info in mapping.items():
            target=destination/rel
            target.parent.mkdir(parents=True,exist_ok=True)
            with z.open(info) as reader, target.open('xb') as writer:
                shutil.copyfileobj(reader,writer)
            if target.suffix == '.sh':
                target.chmod(0o750)


def _read_gate_proof(log):
    content=Path(log).read_text(encoding='utf-8',errors='replace')
    needed=('WYNIK KONCOWY: PASS - WSZYSTKIE 60 ETAPOW PLUS',
            'SOULBOUND RELEASE GATES PASS','PLUS CHECKS PASS',
            'UNIVERSAL RELEASE SAFETY: 20/20 PASS',
            'TCP 6 GRACZY: PASS',
            'PASS - FIZYCZNE EQ NA KOPII BAZY (kod 0)')
    return all(token in content for token in needed)


def predeploy(archive, database, approval, *, stage_hooks=None):
    # Explicit candidate-only hooks: the LIVE runtime may never import
    # validation or historic fixture data as a transitive dependency.
    if stage_hooks is None or len(stage_hooks)!=2:
        raise LinuxReleaseError('Uzyj PREDEPLOY_NOWEJ_WERSJI.sh z pelnej paczki Linux')
    prepare_fixtures, remove_fixtures = stage_hooks
    require_linux()
    archive,mapping,_=archive_info(archive)
    database=source_database(database)
    approval=_plain_folder(approval)
    if not approval.parent.is_dir() or approval.parent.is_symlink():
        raise LinuxReleaseError('Nie ma katalogu na wynik PREDEPLOY')
    original_sha=digest(archive)
    started=datetime.now(timezone.utc).isoformat()
    state={'schema':1,'platform':'linux','version':VERSION,
           'quality_gate':'ULTIMATE-60-PLUS','status':'TESTING',
           'zip':str(archive),'sha256':original_sha,'database':str(database),
           'required_stages':60,'completed_stages':0,'returncode':-1,
           'release_gates_pass':False,'started_at':started,'installed_at_test':'LINUX_FIRST_OR_UPGRADE'}
    save_json(approval,state)
    log_path=approval.parent/'PREDEPLOY_LINUX.log'
    state['log']=str(log_path)
    save_json(approval,state)
    try:
        with tempfile.TemporaryDirectory(prefix='Soulbound_PREDEPLOY_LINUX_') as folder:
            tmp=Path(folder)
            detached=tmp/'SOURCE_COMMITTED_SNAPSHOT.sqlite'
            db_fingerprint=snap_database(database,detached)
            state['db_fingerprint']=db_fingerprint
            stage=tmp/'Soulbound-MUD'
            _extract(archive,mapping,stage)
            # Archive-internal offline hooks set up historical BAT test
            # samples only in the TEMP tree; runtime has no validation imports.
            fixtures=prepare_fixtures(stage)
            if fixtures!=12:
                raise LinuxReleaseError('Niekompletny zestaw historycznych testow')
            env={**os.environ,'PYTHONUTF8':'1','PYTHONIOENCODING':'utf-8',
                 'PYTHONUNBUFFERED':'1','PYTHONDONTWRITEBYTECODE':'1',
                 'SOULBOUND_ULTRA_SOURCE_DB':str(detached),'SOULBOUND_DB':str(detached),
                 'SOULBOUND_HOST':'127.0.0.1','SOULBOUND_UNIVERSAL_STAGING':'1',
                 'SOULBOUND_LINUX_ARCHIVE':str(archive)}
            for key in ('PORT','RAILWAY_TCP_APPLICATION_PORT','SOULBOUND_PORT','SOULBOUND_LIVE_ROOT'):
                env.pop(key,None)
            with log_path.open('w',encoding='utf-8') as out:
                out.write(f'PREDEPLOY LINUX v{VERSION}; ZIP SHA256={original_sha}\n')
                out.flush()
                proc=subprocess.run([sys.executable,'-u','testuj_soulbound_windows.py'],cwd=stage,env=env,
                          stdin=subprocess.DEVNULL,stdout=out,stderr=subprocess.STDOUT,timeout=MAX_SECONDS)
            staged_log=stage/MAIN_LOG
            verified=(proc.returncode==0 and staged_log.is_file() and _read_gate_proof(staged_log))
            if not verified:
                raise LinuxReleaseError('Pelny Linux PREDEPLOY 60/60 + dodatkowe bramki FAIL; zobacz '+str(log_path))
            # Remove the disposable Windows fixtures BEFORE Linux-specific
            # checks and before the activation manifest is ever examined.
            remove_fixtures(stage)
            if any(stage.glob('*.bat')):
                raise LinuxReleaseError('Pliki testowe BAT pozostaly po PREDEPLOY')
            # Independent Linux-specific controls, never replace the 60.
            with log_path.open('a',encoding='utf-8') as out:
                for validator in ('validation/current_linux_release_regression.py',
                                  'validation/current_linux_deploy_rehearsal.py',
                         'validation/linux_predeploy_runner.py',
                         'validation/linux_legacy_windows_fixtures.py'):
                    out.write('\nSTART '+validator+'\n');out.flush()
                    plat=subprocess.run([sys.executable,'-u',validator],
                              cwd=stage,env=env,stdin=subprocess.DEVNULL,stdout=out,
                              stderr=subprocess.STDOUT,timeout=240)
                    out.write('\nLINUX CONTRACT EXIT '+validator+' '+str(plat.returncode)+'\n')
                    if plat.returncode:
                        raise LinuxReleaseError('Brak PASS testu '+validator)
            if fingerprint_source(database)!=db_fingerprint:
                raise LinuxReleaseError('Baza wejsciowa zmienila sie podczas PREDEPLOY')
            if digest(archive)!=original_sha:
                raise LinuxReleaseError('ZIP zmieniono podczas PREDEPLOY')
            state.update(status='PASS',completed_stages=60,returncode=0,
                         release_gates_pass=True,linux_contract_pass=True,
                         finished_at=datetime.now(timezone.utc).isoformat(),
                         log_sha256=digest(log_path))
            save_json(approval,state)
            print('LINUX PREDEPLOY: 60/60 PLUS + v105 3/3 + universal 20/20 + Linux PASS',flush=True)
    except (Exception,KeyboardInterrupt) as exc:
        state.update(status='FAIL',completed_stages=0,returncode=1,
                     release_gates_pass=False,error=str(exc),finished_at=datetime.now(timezone.utc).isoformat())
        save_json(approval,state)
        raise
    return state


def validate_approval(archive, database, approval):
    state=load_json(approval)
    log_path=Path(state.get('log') or '/nonexistent/soulbound-linux-predeploy.log')
    verified_log=(log_path.is_file() and not log_path.is_symlink()
                  and state.get('log_sha256')==digest(log_path)
                  and _read_gate_proof(log_path)
                  and 'LINUX CONTRACT EXIT validation/current_linux_release_regression.py 0'
                      in log_path.read_text(encoding='utf-8',errors='replace')
                  and 'LINUX CONTRACT EXIT validation/current_linux_deploy_rehearsal.py 0'
                      in log_path.read_text(encoding='utf-8',errors='replace'))
    if (state.get('platform')!='linux' or state.get('status')!='PASS'
        or state.get('quality_gate')!='ULTIMATE-60-PLUS'
        or type(state.get('completed_stages')) is not int or state.get('completed_stages')!=60
        or type(state.get('required_stages')) is not int or state.get('required_stages')!=60
        or type(state.get('returncode')) is not int or state.get('returncode')!=0
        or state.get('release_gates_pass') is not True
        or state.get('linux_contract_pass') is not True
        or not verified_log
        or state.get('version')!=VERSION
        or state.get('installed_at_test')!='LINUX_FIRST_OR_UPGRADE'
        or state.get('sha256')!=digest(archive)
        or Path(state['zip']).resolve(strict=True)!=Path(archive).resolve(strict=True)
        or state.get('db_fingerprint')!=fingerprint_source(database)):
        raise LinuxReleaseError('Brak waznego PREDEPLOY Linux dla dokladnie tego ZIP i tej bazy')
    return state


def _port_occupied():
    import errno
    with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as s:
        try:
            s.bind(('0.0.0.0',4000))
        except OSError as exc:
            if exc.errno in (errno.EADDRINUSE,errno.EACCES):
                return True
            raise
    return False


def _unit_path():
    return Path.home()/'.config/systemd/user'/SERVICE_NAME


def _service_unit(workspace):
    workspace=Path(workspace).resolve()
    exe=sys.executable
    if any(c in str(workspace) for c in ('\n','\r','"','%','\\')) or ' ' in str(workspace):
        raise LinuxReleaseError('Katalog instalacji systemd nie moze zawierac spacji ani znakow specjalnych')
    return (SERVICE_IDENTITY+
        '[Unit]\nDescription=Soulbound MUD Linux\nAfter=network.target\n\n'
        '[Service]\nType=simple\nWorkingDirectory='+str(workspace/'current')+'\n'
        'ExecStart='+exe+' -u '+str(workspace/'current'/'server.py')+'\n'
        'Environment=PYTHONUTF8=1\nEnvironment=PYTHONUNBUFFERED=1\n'
        'Environment=SOULBOUND_HOST=0.0.0.0\nEnvironment=SOULBOUND_PORT=4000\n'
        'Environment=SOULBOUND_MAX_CLIENTS=6\n'
        'Environment=SOULBOUND_DB='+str(workspace/'current'/'soulbound.db')+'\n'
        'Restart=on-failure\nRestartSec=5\nTimeoutStopSec=90\nKillMode=control-group\n\n'
        '[Install]\nWantedBy=default.target\n')


def service_control(workspace, operation):
    """Control only a user service whose exact unit content we own."""
    unit=_unit_path()
    if not unit.is_file() or unit.is_symlink() or unit.read_text(encoding='utf-8')!=_service_unit(workspace):
        raise LinuxReleaseError('Brak naszej uslugi systemd; nie zatrzymuje obcego procesu')
    if shutil.which('systemctl') is None:
        raise LinuxReleaseError('Nie ma systemctl')
    return subprocess.run(['systemctl','--user',operation,SERVICE_NAME],
                          stdout=subprocess.PIPE,stderr=subprocess.STDOUT,
                          text=True,timeout=120,check=True)


def _protect_workspace(workspace,source_database_path,*,allow_inside=False):
    workspace=_plain_folder(workspace)
    if str(workspace) in ('/','/opt','/home','/tmp'):
        raise LinuxReleaseError('Wybierz osobny katalog Soulbound')
    source_database_path=source_database(source_database_path)
    if not allow_inside and (workspace==source_database_path.parent or workspace in source_database_path.parents):
        # Keep import source outside all release/backups for independent recovery.
        raise LinuxReleaseError('Zrodlowa baza musi byc poza katalogiem docelowym')
    return workspace


def deploy(archive,database,approval,workspace,*,no_start=False):
    require_linux()
    archive,mapping,production=archive_info(archive)
    database=source_database(database)
    workspace=_protect_workspace(workspace,database,allow_inside=(Path(workspace).expanduser().absolute()/'current').is_symlink())
    approval=_plain_folder(approval)
    state=validate_approval(archive,database,approval)
    from systems.universal_release_update import activate_candidate,verify_stage
    from systems.current_fresh_install import _sqlite_snapshot, carry_saved_data
    from aktualizuj_soulbound import protected
    if workspace.is_symlink():
        raise LinuxReleaseError('Katalog roboczy jest dowiazaniem symbolicznym')
    if workspace.exists() and not workspace.is_dir():
        raise LinuxReleaseError('Zly katalog instalacji')
    if (workspace/'current').is_symlink() and not (workspace/'current').exists():
        raise LinuxReleaseError('Uszkodzony symlink current; niczego nie nadpisuje')
    fresh=not (workspace/'current').exists()
    if not fresh:
        link=workspace/'current'
        if not link.is_symlink():raise LinuxReleaseError('Zainstalowane current musi byc naszym dowiazaniem')
        old=link.resolve(strict=True)
        if old.parent!=(workspace/'releases').resolve(strict=True):
            raise LinuxReleaseError('Nieprawidlowy aktualny katalog wydania')
        if not verify_stage(old):
            raise LinuxReleaseError('Stara gra nie ma waznego manifestu wydania')
    else:
        old=None
    workspace.mkdir(parents=True,exist_ok=True)
    (workspace/'releases').mkdir(exist_ok=True)
    (workspace/'backups').mkdir(exist_ok=True)
    target=workspace/'releases'/('v'+VERSION)
    if target.exists() or target.is_symlink():
        raise LinuxReleaseError('Katalog wersji docelowej juz istnieje')
    current=workspace/'current'
    unit=_unit_path()
    have_service=(not fresh and unit.exists() and not unit.is_symlink()
                  and unit.read_text(encoding='utf-8')==_service_unit(workspace))
    if not fresh and unit.exists() and not have_service:
        raise LinuxReleaseError('Istnieje obca usluga systemd o tej nazwie')
    stage=Path(tempfile.mkdtemp(prefix='.Soulbound_linux_stage_',dir=workspace/'releases'))
    published=False
    stopped=False
    try:
        _extract(archive,production,stage)
        # Only the exact candidate can activate itself. This runs its Python.
        activate_candidate(stage,approval,archive)
        if not verify_stage(stage):
            raise LinuxReleaseError('Aktywacja kandydata nie przeszla')
        if digest(archive)!=state['sha256']:
            raise LinuxReleaseError('ZIP zmieniono po aktywacji')
        validate_approval(archive,database,approval)
        if have_service:
            print('Soulbound Linux: automatyczny STOP wlasnej uslugi...',flush=True)
            service_control(workspace,'stop')
            stopped=True
        if _port_occupied():
            raise LinuxReleaseError('Port 4000 zajety; nie koncze obcego procesu')
        # Recheck identity after service stop, before copying private data.
        validate_approval(archive,database,approval)
        stamp=datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S_%f')
        backup=workspace/'backups'/('soulbound_before_v'+VERSION+'_'+stamp+'.sqlite')
        fp=snap_database(database,backup)
        if fp!=state['db_fingerprint']:
            raise LinuxReleaseError('Zmiana rekordow bazy podczas backupu')
        if old is not None and database.resolve() != (old/'soulbound.db').resolve():
            raise LinuxReleaseError('Podczas aktualizacji podano obca baze zamiast bazy aktualnej gry')
        if old:
            # Full backup of old code+private files, independent of new version.
            code_backup=workspace/'backups'/('old_release_'+stamp)
            if any(path.is_symlink() for path in old.rglob('*')):
                raise LinuxReleaseError('Dowiazanie w starym wydaniu: backup zablokowany')
            shutil.copytree(old,code_backup,symlinks=False)
            # Copy only mutable settings and any additional SQLite databases.
            stats=carry_saved_data(code_backup,stage,protected)
            if fingerprint_source(stage/'soulbound.db')!=fp:
                raise LinuxReleaseError('Baza zmieniona przy przenoszeniu danych')
        else:
            _sqlite_snapshot(backup,stage/'soulbound.db')
            stats={'sqlite_files':1}
        if not verify_stage(stage):
            raise LinuxReleaseError('Manifest nie przeszedl po kopiowaniu SQLite')
        if fingerprint_source(stage/'soulbound.db')!=fp:
            raise LinuxReleaseError('Baza instalacji rozni sie od kopii wejsciowej')
        if current.exists() and not current.is_symlink():
            raise LinuxReleaseError('current juz istnieje i nie jest naszym symlinkiem')
        if not (workspace/'releases').is_dir() or (workspace/'releases').is_symlink():
            raise LinuxReleaseError('Niebezpieczny katalog wydan')
        os.rename(stage,target)
        published=True
        link_temp=workspace/('.current.new.'+str(os.getpid()))
        link_temp.symlink_to(target)
        os.replace(link_temp,current)
        if not verify_stage(target):
            raise LinuxReleaseError('Bledna aktywacja wydania po publikacji')
        print('LINUX INSTALACJA PASS v'+VERSION+'; baza porownana 1:1 z backupem; wydanie '+str(target),flush=True)
        if have_service and not no_start:
            service_control(workspace,'start')
            healthy=False
            for _ in range(30):
                status=subprocess.run(['systemctl','--user','is-active','--quiet',SERVICE_NAME],
                                      check=False,timeout=10)
                if status.returncode==0 and _port_occupied():
                    healthy=True
                    break
                time.sleep(1)
            if not healthy:
                raise LinuxReleaseError('Nowa usluga nie osiagnela stanu active/listening; przywracam stare wydanie')
            print('Soulbound Linux: usluga uruchomiona i port 4000 aktywny',flush=True)
        elif fresh:
            print('PIERWSZA INSTALACJA: uruchom START_Soulbound.sh w rozpakowanej grze albo zainstaluj usluge',flush=True)
        return target
    except BaseException:
        # Roll back current pointer even if no managed service existed.
        try:
            if current.is_symlink() and current.resolve()==target:
                if old is not None:
                    oldlink=workspace/('.current.rollback.'+str(os.getpid()))
                    oldlink.symlink_to(old)
                    os.replace(oldlink,current)
                else:
                    current.unlink()
            if stopped and have_service:
                service_control(workspace,'start')
        except (OSError,subprocess.SubprocessError,LinuxReleaseError) as problem:
            print('UWAGA: nie udalo sie przywrocic starej uslugi: '+str(problem),file=sys.stderr)
        raise
    finally:
        if not published:shutil.rmtree(stage,ignore_errors=True)


def install_service(workspace):
    require_linux()
    workspace=_plain_folder(workspace)
    current=workspace/'current'
    if not current.is_symlink() or not current.resolve(strict=True).is_dir():
        raise LinuxReleaseError('Najpierw zainstaluj wydanie')
    from systems.runtime_activation import verify
    if not verify(current):
        raise LinuxReleaseError('Nie ma zatwierdzonej aktywacji gry')
    if _port_occupied():
        raise LinuxReleaseError('Port 4000 juz zajety; nie przejmuje obcego procesu')
    unit=_unit_path()
    if shutil.which('systemctl') is None:
        raise LinuxReleaseError('Brak systemctl w Linux')
    subprocess.run(['systemctl','--user','show-environment'],check=True,
                   stdin=subprocess.DEVNULL,stdout=subprocess.DEVNULL,timeout=15)
    if unit.exists() or unit.is_symlink():
        if unit.is_symlink() or unit.read_text(encoding='utf-8')!=_service_unit(workspace):
            raise LinuxReleaseError('Istnieje obca usluga soulbound.service')
    unit.parent.mkdir(parents=True,exist_ok=True)
    unit.write_text(_service_unit(workspace),encoding='utf-8')
    subprocess.run(['systemctl','--user','daemon-reload'],check=True,timeout=30)
    subprocess.run(['systemctl','--user','enable','--now',SERVICE_NAME],check=True,timeout=120)
    print('SYSTEMD USER: instalacja uslugi Soulbound PASS',flush=True)


def parser():
    p=argparse.ArgumentParser(description='Soulbound MUD Linux — pierwsza instalacja i aktualizacje')
    sub=p.add_subparsers(dest='action',required=True)
    for command in ('predeploy','deploy'):
        a=sub.add_parser(command)
        a.add_argument('--zip',required=True)
        a.add_argument('--db',required=True)
        a.add_argument('--approval',default=str(ROOT.parent/'Soulbound_PREDEPLOY_LINUX'/'last_result.json'))
        if command=='deploy':
            a.add_argument('--workspace',default=str(Path.home()/'Soulbound-Linux'))
            a.add_argument('--no-start',action='store_true')
    for action in ('install-service','start-service','stop-service','status-service'):
        service=sub.add_parser(action)
        service.add_argument('--workspace',default=str(Path.home()/'Soulbound-Linux'))
    return p


def main(argv=None):
    args=parser().parse_args(argv)
    try:
        if args.action=='predeploy':predeploy(args.zip,args.db,args.approval)
        elif args.action=='deploy':deploy(args.zip,args.db,args.approval,args.workspace,no_start=args.no_start)
        elif args.action=='install-service':install_service(args.workspace)
        else:
            result=service_control(_plain_folder(args.workspace),
                {'start-service':'start','stop-service':'stop','status-service':'is-active'}[args.action])
            print(result.stdout.strip() or ('Soulbound '+args.action+' PASS'),flush=True)
        return 0
    except (LinuxReleaseError,OSError,ValueError,KeyError,sqlite3.Error,zipfile.BadZipFile,
            subprocess.SubprocessError,subprocess.TimeoutExpired) as exc:
        print('SOULBOUND LINUX FAIL: '+type(exc).__name__+': '+str(exc),file=sys.stderr,flush=True)
        return 2


if __name__=='__main__':raise SystemExit(main())
