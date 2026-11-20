# -*- coding: utf-8 -*-
"""Read-only regression of version-neutral update guard and data-copy logic."""
from pathlib import Path
import tempfile
import json
import hashlib
import sqlite3
from contextlib import closing
from unittest.mock import patch
from types import SimpleNamespace
import inspect
import zipfile as zipmod
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from systems.universal_release_update import validate_approval, ensure_stopped_for_upgrade, activate_candidate, verify_stage, update, publish_in_place
import systems.universal_release_update as release_update
from systems.universal_release_update import retire_superseded_approved_files
from systems.current_fresh_install import target_for,_sqlite_snapshot
from aktualizuj_soulbound import UpdateError

def check():
    n=0
    with tempfile.TemporaryDirectory() as td:
        root=Path(td)/'Soulbound-MUD';root.mkdir()
        work=Path(td)/'Soulbound_PREDEPLOY';work.mkdir()
        zipfile=root/'Soulbound-MUD-v113.00.0.zip';zipfile.write_bytes(b'test ZIP bytes')
        checksum=hashlib.sha256(zipfile.read_bytes()).hexdigest()
        record={'status':'PASS','quality_gate':'ULTIMATE-60-PLUS','completed_stages':60,
                'required_stages':60,'returncode':0,'release_gates_pass':True,
                'version':'113.00.0','installed_at_test':'112.00.0',
                'sha256':checksum,'zip':str(zipfile)}
        state=work/'last_result.json'
        state.write_text(json.dumps(record))
        validate_approval(root,zipfile,'113.00.0',checksum,'112.00.0');n+=1
        for field,value in [('status','FAIL'),('quality_gate','OTHER'),('completed_stages',59),
                            ('returncode',1),('release_gates_pass',False),('version','114.00.0'),
                            ('installed_at_test','111.00.0'),('sha256','0'*64)]:
            mutant=dict(record);mutant[field]=value;state.write_text(json.dumps(mutant))
            try:validate_approval(root,zipfile,'113.00.0',checksum,'112.00.0')
            except UpdateError:n+=1
            else:raise AssertionError(field)
        state.write_text(json.dumps(record))
        assert target_for(root,'113.00.0').name=='Soulbound-MUD_V113_00_0_NOWA';n+=1
        assert target_for(root,'224.03.9').name=='Soulbound-MUD_V224_03_9_NOWA';n+=1
        old=Path(td)/'orig.sqlite';new=Path(td)/'copy.sqlite'
        with closing(sqlite3.connect(old)) as db:
            db.execute('CREATE TABLE eq (id INTEGER PRIMARY KEY, payload BLOB, exp TEXT)')
            db.execute('INSERT INTO eq VALUES(1,?,?)',(b'\x00\xff\x10','EXP123'))
            db.commit()
        assert _sqlite_snapshot(old,new)==1;n+=1
        with closing(sqlite3.connect(new)) as db:
            assert db.execute('SELECT payload,exp FROM eq').fetchone()==(b'\x00\xff\x10','EXP123');n+=1
        # Restored v113.00.7 behavior: approved Windows updates stop the owned
        # server AND watchdog, even if the listener port is temporarily free.
        for active in (True,False):
            with patch.object(release_update,'os',SimpleNamespace(name='nt')), \
                 patch('aktualizuj_soulbound.stop_local_server') as stop, \
                 patch('aktualizuj_soulbound.port_open',return_value=False) as listen:
                ensure_stopped_for_upgrade(root)
                stop.assert_called_once_with(root)
                listen.assert_called_once_with(4000)
                n+=1
        # No authenticated control -> never kill an unrelated listener.
        with patch.object(release_update,'os',SimpleNamespace(name='nt')), \
             patch('aktualizuj_soulbound.stop_local_server',side_effect=UpdateError('brak uwierzytelnienia')) as stop, \
             patch('aktualizuj_soulbound.port_open') as listen:
            try:ensure_stopped_for_upgrade(root)
            except UpdateError:n+=1
            else:raise AssertionError('Brak tokenu musi zablokowac aktualizacje')
            stop.assert_called_once()
            listen.assert_not_called()
        # STOP returned, but the port was reoccupied: fail closed.
        with patch.object(release_update,'os',SimpleNamespace(name='nt')), \
             patch('aktualizuj_soulbound.stop_local_server') as stop, \
             patch('aktualizuj_soulbound.port_open',return_value=True):
            try:ensure_stopped_for_upgrade(root)
            except UpdateError:n+=1
            else:raise AssertionError('Port jest zajety po STOP')
            stop.assert_called_once()
        # Linux does not kill unknown services: leave TeamTalk and any
        # future Linux daemon management to a dedicated service lifecycle.
        for busy in (False,True):
            with patch.object(release_update,'os',SimpleNamespace(name='posix')), \
                 patch('aktualizuj_soulbound.stop_local_server') as stop, \
                 patch('aktualizuj_soulbound.port_open',return_value=busy):
                if busy:
                    try:ensure_stopped_for_upgrade(root)
                    except UpdateError:n+=1
                    else:raise AssertionError('Busy Linux service must block')
                else:
                    ensure_stopped_for_upgrade(root);n+=1
                stop.assert_not_called()
        # Source-order contract: approval -> staged activation -> stop ->
        # reconfirm SHA/approval -> backup -> data transfer -> publication.
        src=inspect.getsource(update)
        preflight=src.index('if not verify_stage(stage)')
        stop=src.index('ensure_stopped_for_upgrade(root)')
        rehash=src.index("if sha256_file(archive_path)!=digest:",stop)
        reapprove=src.index('validate_approval(root,archive_path,new_version,digest,current)',stop)
        backup=src.index('backup_existing(root,backup)')
        transfer=src.index('report=carry_saved_data(backup,stage,protected)')
        publish=src.index('publish_in_place(stage,root,backup,protected)')
        assert preflight < stop < rehash < reapprove < backup < transfer < publish
        n+=1
        # Unapproved version or altered archive must block before any STOP.
        assert src.index('validate_approval(root,archive_path,new_version,digest,current)') < src.index('stage_release(archive_path,stage,production)') < stop
        assert "if port_open(4000):raise UpdateError('Port 4000 zajety" not in src
        assert 'target_for(root,new_version)' not in src and 'publish_clean(stage,target' not in src
        n+=1
        # REAL subprocess activation of an isolated, synthetic candidate,
        # using precisely the implementation invoked by update() before STOP.
        # This catches a broken Python -c string even if manifest unit tests pass.
        from systems.universal_activation import REQUIRED
        fixture=Path(td)/'candidate';fixture.mkdir()
        version='117.43.8'  # future-version fixture, never a release dependency
        archive=Path(td)/('Soulbound-MUD-v'+version+'-fixture.zip')
        source=Path(__file__).resolve().parents[1]
        with zipmod.ZipFile(archive,'w',compression=zipmod.ZIP_DEFLATED) as z:
            for name in tuple(REQUIRED)+('core/__init__.py','systems/__init__.py'):
                target=fixture/name;target.parent.mkdir(parents=True,exist_ok=True)
                if name=='VERSION':target.write_text(version+'\n',encoding='utf8')
                else:target.write_bytes((source/name).read_bytes())
                z.write(target,arcname='Soulbound-MUD/'+name)
        fixture_state=Path(td)/'candidate_approval.json'
        approval=dict(record,version=version,sha256=hashlib.sha256(archive.read_bytes()).hexdigest(),
                      zip=str(archive))
        fixture_state.write_text(json.dumps(approval),encoding='utf8')
        activate_candidate(fixture,fixture_state,archive)
        manifest_path=fixture/'config/release_current.json'
        manifest=json.loads(manifest_path.read_text(encoding='utf8'))
        assert manifest['version']==version and manifest['schema']==1;n+=1
        assert set(REQUIRED).issubset(manifest['files']) and verify_stage(fixture);n+=1
        assert not (fixture/'soulbound.db').exists();n+=1
        # No invalid gate may produce a valid candidate activation.
        original=manifest_path.read_bytes()
        bad=dict(approval,release_gates_pass=False)
        fixture_state.write_text(json.dumps(bad),encoding='utf8')
        try:activate_candidate(fixture,fixture_state,archive)
        except UpdateError:n+=1
        else:raise AssertionError('Niezaakceptowany PREDEPLOY aktywowal kandydata')
        assert manifest_path.read_bytes()==original and verify_stage(fixture);n+=1
        # Activation is tied to actual staged file bytes, not a label alone.
        target=fixture/'core/release_version.py'
        data=target.read_bytes();target.write_bytes(data+b'\n# tampered\n')
        assert not verify_stage(fixture);n+=1
        target.write_bytes(data)
        assert verify_stage(fixture);n+=1

        # FULL in-place code replacement with a real SQLite/BLOB fixture.
        # The old root path never changes; private saves stay byte-identical.
        from aktualizuj_soulbound import backup_existing, protected
        inroot=Path(td)/'old_game';inroot.mkdir()
        (inroot/'core').mkdir()
        (inroot/'core/bootstrap_economy_professions.py').write_text('VERSION = load_version()\n')
        (inroot/'VERSION').write_text('112.00.0\n')
        (inroot/'server.py').write_text('OLD SERVER\n')
        (inroot/'soulbound_world_seed.txt').write_text('SECRET-SEED')
        with closing(sqlite3.connect(inroot/'soulbound.db')) as db:
            db.execute('CREATE TABLE eq(id INTEGER PRIMARY KEY, raw BLOB)')
            db.execute('INSERT INTO eq VALUES (5, ?)',(b'\x00\xffSAVED-EQ',))
            db.commit()
        protected_before={p.relative_to(inroot):hashlib.sha256(p.read_bytes()).digest()
                          for p in inroot.rglob('*') if p.is_file() and protected(p.relative_to(inroot))}
        bak=Path(td)/'old_backup';backup_existing(inroot,bak)
        stage2=Path(td)/'new_code';stage2.mkdir()
        (stage2/'core').mkdir()
        (stage2/'core/bootstrap_economy_professions.py').write_text('VERSION = load_version()\n')
        (stage2/'VERSION').write_text('113.00.0\n')
        (stage2/'server.py').write_text('NEW SERVER\n')
        (stage2/'new_module.py').write_text('NEW MODULE\n')
        (stage2/'config').mkdir()
        (stage2/'config/release_current.json').write_text('{"proof": 1}')
        def check_stage(p):
            return (Path(p)/'VERSION').read_text().strip()=='113.00.0'
        with patch.object(release_update,'verify_stage',side_effect=check_stage):
            publish_in_place(stage2,inroot,bak,protected)
        assert inroot.is_dir() and (inroot/'VERSION').read_text().strip()=='113.00.0';n+=1
        assert (inroot/'server.py').read_text()=='NEW SERVER\n' and (inroot/'new_module.py').is_file();n+=1
        assert not any(p.name.startswith('old_game_V') for p in Path(td).iterdir());n+=1
        assert protected_before=={p.relative_to(inroot):hashlib.sha256(p.read_bytes()).digest()
                                  for p in inroot.rglob('*') if p.is_file() and protected(p.relative_to(inroot))};n+=1
        with closing(sqlite3.connect(inroot/'soulbound.db')) as db:
            assert db.execute('SELECT raw FROM eq WHERE id=5').fetchone()[0]==b'\x00\xffSAVED-EQ';n+=1

        # If post-install verification fails, every code file is restored
        # from the exact full backup, without erasing or migrating player data.
        failure_root=Path(td)/'old_game_fail'
        from shutil import copytree
        copytree(bak,failure_root)
        pre_data=hashlib.sha256((failure_root/'soulbound.db').read_bytes()).digest()
        with patch.object(release_update,'verify_stage',side_effect=lambda p: p==stage2):
            try:publish_in_place(stage2,failure_root,bak,protected)
            except UpdateError: n+=1
            else:raise AssertionError('Brak rollback po falszywym manifest verification')
        assert (failure_root/'VERSION').read_text().strip()=='112.00.0';n+=1
        assert (failure_root/'server.py').read_text()=='OLD SERVER\n';n+=1
        assert not (failure_root/'new_module.py').exists() and not (failure_root/'config/release_current.json').exists();n+=1
        assert hashlib.sha256((failure_root/'soulbound.db').read_bytes()).digest()==pre_data;n+=1

        # Reproduce Windows v115.00.4: post-install verifier regenerates
        # the nondurable SQLite SHM index before backup byte verification.
        shmroot=Path(td)/'old_game_shm'
        copytree(bak,shmroot)
        (shmroot/'soulbound.db-shm').write_bytes(b'index-before-backup')
        shmbackup=Path(td)/'old_backup_shm'
        backup_existing(shmroot,shmbackup)
        assert (shmbackup/'soulbound.db-shm').read_bytes()==b'index-before-backup';n+=1
        def verify_after_shm_change(path):
            path=Path(path)
            if path==shmroot:
                (path/'soulbound.db-shm').write_bytes(b'changed-index-postinstall')
            return path in (shmroot, stage2)
        with patch.object(release_update,'verify_stage',side_effect=verify_after_shm_change):
            publish_in_place(stage2,shmroot,shmbackup,protected)
        assert (shmroot/'VERSION').read_text().strip()=='113.00.0';n+=1
        assert (shmroot/'soulbound.db').read_bytes()==(shmbackup/'soulbound.db').read_bytes();n+=1
        assert (shmroot/'soulbound.db-shm').read_bytes()!= (shmbackup/'soulbound.db-shm').read_bytes();n+=1

        # Future-proof release retirement: after backup, remove only exactly
        # certified former *code*, not user-modified or unsigned scripts.
        oldroot=Path(td)/'old_approved_install';oldroot.mkdir()
        oldbackup=Path(td)/'old_approved_backup';oldbackup.mkdir()
        newstage=Path(td)/'next_approved_release';newstage.mkdir()
        oldbin=b'@echo off\r\nREM old reviewed starter\r\n'
        modified=b'print("locally modified")\n'
        keep=b'print("still part of the new version")\n'
        private=b'player secrets'
        entries={
            'Start-Soulbound-Windows.bat':oldbin,
            'user_changed.py':modified,
            'keep.py':keep,
            'soulbound.db':private,
        }
        manifest_files={}
        for relative, contents in entries.items():
            (oldroot/relative).write_bytes(contents)
            (oldbackup/relative).write_bytes(contents)
            manifest_files[relative]=hashlib.sha256(contents).hexdigest()
        (newstage/'keep.py').write_bytes(b'updated')
        (oldroot/'user_changed.py').write_bytes(b'print("edited by player")\n')
        (oldroot/'custom_addon.py').write_bytes(b'# custom user script\n')
        (oldbackup/'config').mkdir()
        marker=oldbackup/'config/release_current.json'
        marker.write_text(json.dumps({'files':manifest_files}),encoding='utf-8')
        with patch('systems.universal_activation.verify',return_value=False):
            assert retire_superseded_approved_files(oldroot,newstage,oldbackup,protected)==0
            assert (oldroot/'Start-Soulbound-Windows.bat').exists()
            n+=1
        with patch('systems.universal_activation.verify',return_value=True):
            assert retire_superseded_approved_files(oldroot,newstage,oldbackup,protected)==1
            n+=1
        assert not (oldroot/'Start-Soulbound-Windows.bat').exists();n+=1
        assert (oldbackup/'Start-Soulbound-Windows.bat').read_bytes()==oldbin;n+=1
        assert (oldroot/'user_changed.py').read_bytes()!=modified;n+=1
        assert (oldroot/'keep.py').read_bytes()==keep;n+=1
        assert (oldroot/'soulbound.db').read_bytes()==private;n+=1
        assert (oldroot/'custom_addon.py').exists();n+=1
        # v115.00.12: after signed retirement, empty historical directories
        # disappear, but never an unlisted file, edited code or a symlink.
        legacy=(oldroot/'legacy'/'obsolete')
        verified_backup=(oldbackup/'legacy'/'obsolete')
        legacy.mkdir(parents=True)
        verified_backup.mkdir(parents=True)
        payload=b'# old approved offline-only audit\n'
        (legacy/'audit.py').write_bytes(payload)
        (verified_backup/'audit.py').write_bytes(payload)
        (legacy/'user_notes.py').write_text('# local addon\n',encoding='utf8')
        marker.write_text(json.dumps({'files':{
            'legacy/obsolete/audit.py':hashlib.sha256(payload).hexdigest()}}),encoding='utf8')
        with patch('systems.universal_activation.verify',return_value=True):
            assert retire_superseded_approved_files(oldroot,newstage,oldbackup,protected)==1;n+=1
        assert not (legacy/'audit.py').exists();n+=1
        assert (legacy/'user_notes.py').read_text('utf8')=='# local addon\n';n+=1
        assert legacy.is_dir();n+=1
        # Remove the *local* untracked fixture ourselves; the approved
        # backup remains separate and no updater has touched it.
        (legacy/'user_notes.py').unlink()
        second=b'# second signed old test\n'
        (legacy/'audit2.py').write_bytes(second)
        (verified_backup/'audit2.py').write_bytes(second)
        marker.write_text(json.dumps({'files':{
            'legacy/obsolete/audit2.py':hashlib.sha256(second).hexdigest()}}),encoding='utf8')
        with patch('systems.universal_activation.verify',return_value=True):
            assert retire_superseded_approved_files(oldroot,newstage,oldbackup,protected)==1;n+=1
        assert not (oldroot/'legacy').exists();n+=1
        assert (verified_backup/'audit.py').read_bytes()==payload;n+=1
        # A signed-looking path redirected by a user symlink must be ignored.
        external=Path(td)/'external_owned';external.mkdir()
        (external/'outside.py').write_bytes(b'owner file')
        try:
            (oldroot/'redirect').symlink_to(external,target_is_directory=True)
        except (OSError,NotImplementedError):
            redirect_ok=False
        else:
            redirect_ok=True
        if redirect_ok:
            (oldbackup/'redirect').mkdir()
            (oldbackup/'redirect/outside.py').write_bytes(b'owner file')
        if redirect_ok:
            marker.write_text(json.dumps({'files':{
                'redirect/outside.py':hashlib.sha256(b'owner file').hexdigest()}}),encoding='utf8')
        if redirect_ok:
            with patch('systems.universal_activation.verify',return_value=True):
                assert retire_superseded_approved_files(oldroot,newstage,oldbackup,protected)==0;n+=1
            assert (external/'outside.py').read_bytes()==b'owner file';n+=1
            (oldroot/'redirect').unlink()
        marker.write_text(json.dumps({'files':manifest_files}),encoding='utf8')
        # Without the approved old bytes in backup, a matching live file
        # must still be preserved. No rename or deletion based on filenames.
        (oldroot/'Start-Soulbound-Windows.bat').write_bytes(oldbin)
        (oldbackup/'Start-Soulbound-Windows.bat').write_bytes(b'changed backup')
        with patch('systems.universal_activation.verify',return_value=True):
            assert retire_superseded_approved_files(oldroot,newstage,oldbackup,protected)==0
            n+=1
        assert (oldroot/'Start-Soulbound-Windows.bat').exists();n+=1
        # Paths outside an approved manifest cannot be deleted.
        marker.write_text(json.dumps({'files':{'../outside.py':hashlib.sha256(oldbin).hexdigest()}}),encoding='utf8')
        with patch('systems.universal_activation.verify',return_value=True):
            assert retire_superseded_approved_files(oldroot,newstage,oldbackup,protected)==0
            n+=1
        # v115.00.9 production-only pruning. The FULL archive retains
        # offline test fixtures; the approved installed runtime does not.
        from aktualizuj_soulbound import production_release_mapping
        candidates={Path(name):None for name in (
            'VERSION', 'server.py', 'CHANGELOG_PL.txt',
            'arena_real_izolowana.py', 'validation/test_v115_eliza_mercenary.py',
            'windows_autostart.py', 'windows_runtime_state.py',
            'windows_launcher_state.py', 'systems/windows_control_v1603.py',
            'predeploy_nowej_wersji.py', 'START_Soulbound.bat',
        )}
        with patch('aktualizuj_soulbound.sys.platform','linux'):
            linux={p.as_posix() for p in production_release_mapping(candidates)}
        with patch('aktualizuj_soulbound.sys.platform','win32'):
            windows={p.as_posix() for p in production_release_mapping(candidates)}
        assert not ('arena_real_izolowana.py' in linux or 'arena_real_izolowana.py' in windows);n+=1
        assert 'validation/test_v115_eliza_mercenary.py' not in linux|windows;n+=1
        assert all(p in linux for p in ('VERSION','server.py','CHANGELOG_PL.txt',
                                         'systems/windows_control_v1603.py','predeploy_nowej_wersji.py'));n+=1
        assert 'windows_autostart.py' in windows and 'windows_autostart.py' not in linux;n+=1
        for name in ('windows_runtime_state.py','windows_launcher_state.py'):
            assert name in windows and name not in linux;n+=1
        # The Linux runtime does NOT load Win32 process state just to import
        # the shared localhost control service. Force import failure in a
        # clean reload to catch future accidental eager imports.
        import importlib, asyncio, os, sys
        from unittest.mock import patch as _patch
        with _patch.dict(sys.modules, {'windows_runtime_state': None,
                                       'windows_launcher_state': None}):
            control = importlib.reload(importlib.import_module('systems.windows_control_v1603'))
            with _patch.dict(os.environ, {'SOULBOUND_CONTROL_TOKEN': '',
                                         'SOULBOUND_CONTROL_FILE': ''}):
                assert asyncio.run(control.start_control_v1603(asyncio.Event())) is None;n+=1
        # The shared module does not accidentally re-enable old imports.
        control_src=(Path(__file__).resolve().parents[1]/'systems/windows_control_v1603.py').read_text('utf-8')
        assert 'from windows_runtime_state import write_state, remove_matching' not in control_src;n+=1
        # A real localhost control endpoint can still start and stop without
        # a Windows fallback file and without loading either Win32 helper.
        with tempfile.TemporaryDirectory(prefix='sb11510_control_') as isolated:
            from unittest.mock import patch as _patch
            control_path=str(Path(isolated)/'control.json')
            with _patch.dict(sys.modules, {'windows_runtime_state': None,
                                           'windows_launcher_state': None}), \
                 _patch.dict(os.environ, {'SOULBOUND_CONTROL_TOKEN': 'x'*40,
                                          'SOULBOUND_CONTROL_FILE': control_path,
                                          'SOULBOUND_CONTROL_FALLBACK_FILE': ''}):
                async def _control_cycle():
                    result=await control.start_control_v1603(asyncio.Event())
                    assert result is not None and Path(control_path).is_file()
                    await result.close()
                    assert not Path(control_path).exists()
                asyncio.run(_control_cycle());n+=1
        assert 'START_Soulbound.bat' in windows and 'START_Soulbound.bat' not in linux;n+=1
        # The update entrypoint has no eager Win32 helper import either.
        updater_text=(Path(__file__).resolve().parents[1]/'aktualizuj_soulbound.py').read_text('utf-8')
        assert 'from windows_launcher_state import wait_gone' not in updater_text;n+=1
        # v115.00.11: v107 standalone audit merged, not silently discarded.
        import hashlib as _hashlib
        from validation import v11100_v107_functional_audit as historic
        assert not (Path(__file__).resolve().parents[1]/'audyt_v107_windows_przed_predeploy.py').exists();n+=1
        assert len(historic.SUITES)==33 and historic.suites_reviewed();n+=1
        assert historic.SCRIPT=='validation.v10700_release_readiness';n+=1
        with tempfile.TemporaryDirectory(prefix='sb11511_history_') as hdir:
            historical_root=Path(hdir)
            (historical_root/'VERSION').write_text('107.00.0')
            (historical_root/'core').mkdir()
            (historical_root/'core/bootstrap_economy_professions.py').write_text("VERSION = '107.00.0'\n")
            (historical_root/'fixture.py').write_text('x=1\n')
            assert historic.check_sources(historical_root)[1]=='107.00.0';n+=1
            (historical_root/'fixture.db').write_bytes(b'private fixture')
            try:historic.check_sources(historical_root)
            except RuntimeError:n+=1
            else:raise AssertionError('Historyczny audyt nie moze zawierac bazy')
            (historical_root/'fixture.db').unlink()
            with patch.object(historic,'ROOT',historical_root), \
                 patch.object(historic,'legacy_v107_main',return_value=7) as old_runner, \
                 patch.object(historic,'main',return_value=8) as new_runner:
                assert historic.entrypoint()==7;n+=1
                old_runner.assert_called_once();new_runner.assert_not_called()
                (historical_root/'VERSION').write_text('111.00.0')
                assert historic.entrypoint()==8;n+=1
                new_runner.assert_called_once()
        assert "from validation.v11100_v107_functional_audit import SUITES,call,ignored" in (Path(__file__).resolve().parents[1]/'validation/v11000_v107_functional_audit.py').read_text('utf-8');n+=1
        assert "else 'validation/v11100_v107_functional_audit.py'" in (Path(__file__).resolve().parents[1]/'testuj_soulbound_windows.py').read_text('utf-8');n+=1
        # Offline arena is used ONLY by the complete regression archive.
        source_root=Path(__file__).resolve().parents[1]
        for source in source_root.rglob('*.py'):
            rel=source.relative_to(source_root)
            if 'validation' in rel.parts or rel.name=='arena_real_izolowana.py':
                continue
            if 'arena_real_izolowana' in source.read_text(encoding='utf-8-sig'):
                # A static mapping / historical note is harmless, an import is not.
                for ln in source.read_text(encoding='utf-8-sig').splitlines():
                    if 'arena_real_izolowana' in ln and ('import' in ln or 'open(' in ln):
                        raise AssertionError('Production code depends on offline arena: '+str(rel))
        n+=1
    print('CURRENT UNIVERSAL UPDATE: '+str(n)+' checks PASS')

if __name__=='__main__':check()
