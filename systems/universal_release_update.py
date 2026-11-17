# -*- coding: utf-8 -*-
"""Future-version installer: never execute historical source code.

Runs only after a matched full 60/60 PLUS approval. No fixed target version.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
import subprocess
import sys
from systems.current_fresh_install import carry_saved_data


def validate_approval(root, archive_path, version, digest, installed):
    from aktualizuj_soulbound import UpdateError
    source=Path(root).parent/'Soulbound_PREDEPLOY'/'last_result.json'
    try:
        state=json.loads(source.read_text(encoding='utf-8'))
        ok=(state.get('status')=='PASS' and state.get('quality_gate')=='ULTIMATE-60-PLUS'
            and type(state.get('completed_stages')) is int and state['completed_stages']==60
            and type(state.get('required_stages')) is int and state['required_stages']==60
            and type(state.get('returncode')) is int and state['returncode']==0
            and state.get('release_gates_pass') is True
            and state.get('version')==version and state.get('installed_at_test')==installed
            and state.get('sha256')==digest
            and Path(state['zip']).resolve(strict=True)==Path(archive_path).resolve(strict=True))
    except (OSError,ValueError,KeyError,TypeError,json.JSONDecodeError):ok=False
    if not ok:raise UpdateError('Brak zgodnego PREDEPLOY 60/60 PLUS dla obecnej bazy i ZIP')



def verify_private_backup(root, backup, protected_predicate):
    """Require byte-for-byte backup of every protected user file, not just DB/WAL.

    Backup must be complete and stable before any player data is transferred.
    This does not certify live database consistency: that is checked separately
    by the offline SQLite snapshot and PREDEPLOY.
    """
    from aktualizuj_soulbound import UpdateError, sha256_file
    root, backup = Path(root), Path(backup)
    if not root.is_dir() or not backup.is_dir():
        raise UpdateError('Brak katalogu gry lub pelnej kopii bezpieczenstwa')
    checked = 0
    for source in sorted(root.rglob('*')):
        relative = source.relative_to(root)
        # Ignore exactly the same volatile directories as the full backup.
        # A symlink within a protected save path is still forbidden below.
        if not protected_predicate(relative):
            continue
        if source.is_symlink():
            raise UpdateError('Dowiazanie symboliczne w danych graczy: '+str(source))
        if not source.is_file():
            continue
        dest = backup / relative
        if dest.is_symlink() or not dest.is_file():
            raise UpdateError('Brak pliku danych w backupie: '+str(relative))
        if source.stat().st_size != dest.stat().st_size or sha256_file(source) != sha256_file(dest):
            raise UpdateError('Niezgodna zawartosc kopii danych: '+str(relative))
        checked += 1
    return checked


def verify_stage(root):
    """Run candidate activation code in its OWN interpreter, not prior release's imports."""
    import os
    env=os.environ.copy()
    env['PYTHONDONTWRITEBYTECODE']='1'
    env['SOULBOUND_LIVE_ROOT']=str(root)
    script="""from systems.runtime_activation import verify
import sys
from pathlib import Path
sys.exit(0 if verify(Path.cwd()) else 34)
"""
    p=subprocess.run([sys.executable,'-c',script],cwd=root,env=env,timeout=90,
                     stdin=subprocess.DEVNULL,capture_output=True,text=True)
    return p.returncode==0


def activate_candidate(stage: Path, state: Path, archive_path: Path) -> None:
    """Activate a fully staged candidate in its own interpreter before STOP.

    Uses only the candidate's version-neutral activation API; no production
    data, prior release modules, or update-side installation artefacts.
    """
    from aktualizuj_soulbound import UpdateError
    script="""import json,sys
from pathlib import Path
from systems.runtime_activation import activation_manifest,verify
root=Path.cwd(); state=json.loads(Path(sys.argv[1]).read_text(encoding='utf-8'))
from zipfile import ZipFile
with ZipFile(sys.argv[2]) as z:
  mapping={Path(i.filename[len('Soulbound-MUD/'):]):i for i in z.infolist()
           if i.filename.startswith('Soulbound-MUD/') and not i.is_dir()}
  mapping={p:i for p,i in mapping.items() if (root/p).is_file()}
manifest=activation_manifest(state,Path(sys.argv[2]),root,mapping)
from systems.runtime_activation import MARKER
marker=root/MARKER;marker.parent.mkdir(parents=True,exist_ok=True)
marker.write_text(json.dumps(manifest,sort_keys=True,indent=2)+chr(10),encoding='utf-8')
sys.exit(0 if verify(root) else 35)
"""
    # Compiling the exact generated script catches quote and newline errors
    # before the subprocess has an opportunity to change any candidate file.
    compile(script, '<soulbound-candidate-activation>', 'exec')
    proc=subprocess.run([sys.executable,'-c',script,str(state),str(archive_path)],
                        cwd=stage,stdin=subprocess.DEVNULL,capture_output=True,
                        text=True,timeout=120)
    if proc.returncode!=0:
        raise UpdateError('Nieudana aktywacja kandydata: '+(proc.stderr+proc.stdout)[-800:])


def ensure_stopped_for_upgrade(root: Path) -> None:
    """Stop the owned Windows instance and watchdog; refuse foreign processes.

    Run only AFTER candidate activation, matching PREDEPLOY and SHA256 checks,
    but BEFORE backing up SQLite. Even an apparently free port is not proof
    that a watchdog cannot restart the old server during the cutover.
    """
    from aktualizuj_soulbound import UpdateError, port_open, stop_local_server
    if os.name == 'nt':
        print('Soulbound: automatyczny, uwierzytelniony STOP przed aktualizacja...', flush=True)
        stop_local_server(root)
    # Linux service lifecycle is handled separately, without killing another
    # process just because it happens to own port 4000.
    if port_open(4000):
        raise UpdateError('Port 4000 nadal zajety po sprawdzeniu STOP. Nie dotykam danych ani obcego procesu.')


def publish_in_place(stage: Path, root: Path, backup: Path, protected_predicate) -> None:
    """Install approved code at the original path and roll back on ANY failure.

    The BAT invoking the updater has cwd=root on Windows, so renaming the
    entire live directory is unsafe (WinError 32). Only release files are
    replaced; live SQLite, WAL, player data and local settings are untouched.
    """
    from aktualizuj_soulbound import (UpdateError, install_stage,
        _restore_prior_code_after_v108_cutover_failure, file_version)
    stage, root, backup = map(Path, (stage,root,backup))
    if stage.is_symlink() or root.is_symlink() or backup.is_symlink():
        raise UpdateError('Dowiazanie symboliczne w sciezce aktualizacji')
    if not verify_stage(stage):
        raise UpdateError('Kandydat nie przeszedl weryfikacji przed podmiana')
    files={source.relative_to(stage) for source in stage.rglob('*') if source.is_file()}
    if not files:
        raise UpdateError('Nie ma plikow nowej wersji do instalacji')
    installed_version=(stage/'VERSION').read_text(encoding='utf-8-sig').strip()
    try:
        install_stage(root,stage,backup)
        if (root/'VERSION').read_text(encoding='utf-8-sig').strip()!=installed_version:
            raise UpdateError('VERSION nie zgadza sie po podmianie w starym folderze')
        if file_version(root/'core/bootstrap_economy_professions.py')!=installed_version:
            raise UpdateError('Kod i VERSION rozne po podmianie')
        if not verify_stage(root):
            raise UpdateError('Manifest aktywacji nie zgadza sie po podmianie w starym folderze')
        # Check protected original bytes AGAIN after code replacement.
        verify_private_backup(root,backup,protected_predicate)
        from systems.current_retire_live_content import retire
        removed=retire(root,backup)
        if removed:print(f'Usunieto LIVE_CONTENT po pelnym backupie ({removed} plikow).',flush=True)
    except BaseException as cause:
        try:
            _restore_prior_code_after_v108_cutover_failure(root,backup,files)
            verify_private_backup(root,backup,protected_predicate)
        except BaseException as rollback_error:
            raise UpdateError('UWAGA: blad podczas przywracania kodu; zachowaj backup '
                              +str(backup)+'; przyczyna: '+str(rollback_error)) from cause
        raise UpdateError('Podmiana kodu nieudana. Przywrocono stara wersje z backupu: '
                          +str(cause)) from cause


def restart_windows_without_console(launcher=None, *, installed_root=None) -> int:
    """Launch from the INSTALLED root, never from temporary Generic_Bridge.

    A release-owned updater executes in an isolated extracted copy. Importing
    uruchom_w_tle in that interpreter makes its __file__/ROOT point to TEMP.
    That spawns a watchdog from TEMP, locking the bridge (WinError 32) and
    potentially starting the wrong game directory. Use the installed script.

    The optional callable is only a dependency injection for isolated tests.
    """
    if launcher is not None:
        return int(launcher())
    if installed_root is None:
        raise RuntimeError('Brak katalogu instalacji dla startu Soulbound.')
    installed_root = Path(installed_root).resolve(strict=True)
    installed_script = installed_root / 'uruchom_w_tle.py'
    if not installed_script.is_file() or installed_script.is_symlink():
        raise RuntimeError('Brak zaufanego uruchamiacza w katalogu instalacji: '
                           + str(installed_script))
    environment = os.environ.copy()
    environment['SOULBOUND_LIVE_ROOT'] = str(installed_root)
    environment['PYTHONDONTWRITEBYTECODE'] = '1'
    completed = subprocess.run(
        [sys.executable, '-u', str(installed_script)],
        cwd=str(installed_root), env=environment, stdin=subprocess.DEVNULL,
        timeout=40, creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0),
    )
    return int(completed.returncode)


def retire_generated_bytecode_caches(root: Path) -> tuple[int, int]:
    """Remove only disposable .pyc files after successful in-place publication.

    Never traverse links, touch saved data, or delete folders with unknown files.
    Called after the verified full backup and while the server is stopped.
    """
    root = Path(root).resolve(strict=True)
    allowed = {'core', 'systems', 'player', 'world', 'storage', 'config',
               'data', 'events', 'network', 'server', 'server_parts_v109',
               'admin', 'validation', 'narzedzia'}
    candidates = [root] + [root / name for name in sorted(allowed)
                           if (root / name).is_dir() and not (root / name).is_symlink()]
    removed_files = removed_dirs = 0
    for subtree in candidates:
        for cache in sorted(subtree.rglob('__pycache__'), key=lambda p: len(p.parts), reverse=True):
            if cache.is_symlink() or not cache.is_dir():
                continue
            if any(parent.is_symlink() for parent in cache.parents if parent != root):
                continue
            if subtree == root and cache.parent != root:
                continue  # root scan is intentionally non-recursive
            entries = list(cache.iterdir())
            if any(not entry.is_file() or entry.is_symlink()
                   or entry.suffix.lower() != '.pyc' for entry in entries):
                continue
            try:
                for file in entries:
                    file.unlink()
                    removed_files += 1
                cache.rmdir()
                removed_dirs += 1
            except OSError as exc:
                print('UWAGA: nie udalo sie sprzatnac '+str(cache)+': '+str(exc), flush=True)
    return removed_dirs, removed_files


def update(root, archive_path, new_version, mapping, *,restart=True):
    """Replace code IN PLACE after backup and full candidate verification; keep player data."""
    import shutil
    import tempfile
    import zipfile
    from datetime import datetime
    from aktualizuj_soulbound import (UpdateError, version_tuple, file_version, sha256_file,
        backup_existing,stage_release,port_open,protected)
    from systems.current_fresh_install import FreshInstallError
    root=Path(root).resolve()
    current=file_version(root/'core/bootstrap_economy_professions.py')
    if version_tuple(new_version)<=version_tuple(current):
        raise UpdateError('Nowa wersja musi byc nowsza niz zainstalowana')
    # Defense in depth: direct Python calls must verify the same release identity
    # as PREDEPLOY and the permanent BAT entrypoints, before backup or STOP.
    archive_path=Path(archive_path).resolve(strict=True)
    import re
    match=re.fullmatch(r'Soulbound-MUD-v(\d+\.\d+\.\d+).*\.zip',archive_path.name,re.I)
    if not match or match.group(1)!=new_version:
        raise UpdateError('Nazwa ZIP nie odpowiada numerowi nowej wersji')
    with zipfile.ZipFile(archive_path) as source_zip:
        checked=__import__('aktualizuj_soulbound').archive_mapping(source_zip)
        if set(checked)!=set(mapping):
            raise UpdateError('Mapa plikow ZIP zmienila sie od weryfikacji')
        if __import__('aktualizuj_soulbound').read_archive_version(source_zip,checked)!=new_version:
            raise UpdateError('Wersja w kodzie ZIP nie zgadza sie z nazwa')
        entry=checked.get(Path('VERSION'))
        if entry is None or source_zip.read(entry).decode('utf-8-sig').strip()!=new_version:
            raise UpdateError('Wersja w VERSION nie zgadza sie z nazwa ZIP')
        if source_zip.testzip():
            raise UpdateError('Archiwum ZIP nie przeszlo kontroli CRC')
    if (root/'VERSION').read_text(encoding='utf-8-sig').strip()!=current:
        raise UpdateError('Numer wersji zainstalowanej gry jest niespojny')
    digest=sha256_file(archive_path)
    validate_approval(root,archive_path,new_version,digest,current)
    date=datetime.now().strftime('%Y%m%d_%H%M%S')
    backup=root.parent/('Soulbound_BACKUP_'+date)
    ix=0
    while backup.exists():
        ix+=1;backup=root.parent/('Soulbound_BACKUP_'+date+'_'+str(ix))
    stage=Path(tempfile.mkdtemp(prefix='.Soulbound_universal_',dir=root.parent))
    installed=False
    try:
        # Candidate contains full offline tests but production only gets runtime.
        # Reviewed, release-neutral production selection; all 60/60 and
        # historical fixtures remain in the full candidate ZIP only.
        from aktualizuj_soulbound import production_release_mapping
        production=production_release_mapping(mapping)
        stage_release(archive_path,stage,production)
        # The very same activation subprocess is exercised by the universal
        # regression gate; never embed an untested one-off -c script here.
        state=root.parent/'Soulbound_PREDEPLOY'/'last_result.json'
        activate_candidate(stage, state, archive_path)
        # Recheck external PREDEPLOY and archive BEFORE backup and publication.
        if sha256_file(archive_path)!=digest:raise UpdateError('ZIP zmieniono podczas instalacji')
        validate_approval(root,archive_path,new_version,digest,current)
        if not verify_stage(stage):raise UpdateError('Manifest stagingu odrzucony')
        # All approval/activation checks MUST finish before STOP. This uses
        # authenticated shutdown of the OLD Windows service, never a port kill.
        ensure_stopped_for_upgrade(root)
        # A long graceful STOP is an external race window: revalidate the
        # exact approved candidate once more before copying any private data.
        if sha256_file(archive_path)!=digest:
            raise UpdateError('ZIP zmieniono w czasie STOP. Dane graczy nietkniete.')
        validate_approval(root,archive_path,new_version,digest,current)
        backup_existing(root,backup)
        if not (backup/'soulbound.db').is_file():raise UpdateError('Brak bazy w backupie')
        protected_count = verify_private_backup(root,backup,protected)
        if protected_count < 1:
            raise UpdateError('Nie znaleziono danych graczy w kopii bezpieczenstwa')
        report=carry_saved_data(backup,stage,protected)
        if not verify_stage(stage):raise UpdateError('Manifest zmieniony po kopiowaniu zapisow')
        # Never create Soulbound-MUD_V..._NOWA. The existing path is stable.
        publish_in_place(stage,root,backup,protected)
        installed=True
        try:
            caches, bytecodes = retire_generated_bytecode_caches(root)
            print(f'PYTHON CACHE: usunieto {caches} katalogow __pycache__ i {bytecodes} plikow .pyc.', flush=True)
        except OSError as exc:
            print('UWAGA: sprzatanie __pycache__ niezakonczone: '+str(exc), flush=True)
        print('AKTUALIZACJA W MIEJSCU PASS: v'+new_version+'; katalog: '+str(root),flush=True)
        print('Dane graczy nietkniete; zbadane bazy: '+str(report['sqlite_files'])+
              '; tabele: '+str(report['tables_checked']),flush=True)
        print('Pelny backup starszego kodu i danych: '+str(backup),flush=True)
        # On Windows, migrate ONLY an already enabled autostart from the old
        # visible Startup CMD to HKCU Run + pythonw (no startup console).
        # This is post-publication, never from an isolated PREDEPLOY clone.
        if os.name == 'nt':
            try:
                # Import from the installed root. The updater interpreter
                # runs out of the temporary bridge and must not migrate Startup
                # entries using TEMP as its ownership root.
                import importlib.util
                active_autostart = root / 'windows_autostart.py'
                if not active_autostart.is_file() or active_autostart.is_symlink():
                    raise RuntimeError('Brak autostartu w zainstalowanym kodzie')
                spec = importlib.util.spec_from_file_location(
                    '_soulbound_installed_autostart', active_autostart)
                if spec is None or spec.loader is None:
                    raise RuntimeError('Nie mozna zaladowac zainstalowanego autostartu')
                live_autostart = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(live_autostart)
                migrated = live_autostart.migrate_if_enabled()
                if migrated:
                    print('AUTOSTART: od teraz Soulbound rusza w tle bez okna CMD.',flush=True)
            except (OSError, RuntimeError, ValueError, UnicodeError) as exc:
                print('UWAGA: autostart nie zostal przeniesiony: '+str(exc)+
                      '. Mozna uzyc AUTOSTART_WLACZ_Soulbound.bat.',flush=True)
        if restart and os.name=='nt':
            try:
                code = restart_windows_without_console(installed_root=root)
                if code:
                    print('UWAGA: kod zainstalowano, ale uruchamiacz w tle zwrocil kod '
                          + str(code) + '. Sprawdz logs\\start.log.', flush=True)
                else:
                    print('Uruchomiono Soulbound w tle bez okna CMD.', flush=True)
            except (OSError, RuntimeError, ValueError) as exc:
                print('UWAGA: kod zainstalowano, ale start w tle sie nie powiodl: '
                      +str(exc),flush=True)
        return backup
    except (OSError,FreshInstallError,subprocess.TimeoutExpired) as exc:
        raise UpdateError('Bezpieczna aktualizacja przerwana: '+str(exc)) from exc
    finally:
        # Source ZIP is still in NOWE_WERSJE. Stage always was an isolated copy.
        shutil.rmtree(stage,ignore_errors=True)
