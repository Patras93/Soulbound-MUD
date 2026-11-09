# -*- coding: utf-8 -*-
"""v109 durable release marker, exact staged ZIP and fail-closed boot tests."""
from __future__ import annotations
import hashlib
import json
import tempfile
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile,ZIP_DEFLATED
from systems.v10900_activation import (REQUIRED,MARKER,VERSION,SOURCE_VERSION,
                                         activation_manifest,verify_root_for_test)
from systems.v10900_staging_guard import authorized_runtime,ensure_authorized_start

ROOT=Path(__file__).resolve().parents[1]

def run():
    n=0
    def ck(truth,message):
        nonlocal n
        assert truth,message
        n+=1
    with tempfile.TemporaryDirectory(prefix='soulbound-v109-act-') as td:
        base=Path(td)
        stage=base/'candidate'
        installed=base/'installed'
        members=set(REQUIRED)|{'CHANGELOG_PL.txt','START_Soulbound.bat',
                               'STOP_Soulbound.bat','predeploy_check.py'}
        for rel in sorted(members):
            path=stage/rel
            path.parent.mkdir(parents=True,exist_ok=True)
            if rel=='VERSION':path.write_text(VERSION,encoding='utf-8')
            elif rel=='core/bootstrap_economy_professions.py':path.write_text('VERSION = "'+VERSION+'"\n')
            else:path.write_bytes((rel+'\n').encode())
        archive=base/'Soulbound-MUD-v109.00.0-test.zip'
        with ZipFile(archive,'w',ZIP_DEFLATED) as z:
            for p in sorted(stage.rglob('*')):
                if p.is_file():z.write(p,'Soulbound-MUD/'+p.relative_to(stage).as_posix())
        sha=hashlib.sha256(archive.read_bytes()).hexdigest()
        state=dict(status='PASS',quality_gate='ULTIMATE-60-PLUS',
                   returncode=0,completed_stages=60,required_stages=60,
                   version=VERSION,installed_at_test=SOURCE_VERSION,
                   v109_release_gates_pass=True,sha256=sha)
        for key,value in [('v109_release_gates_pass',False),('installed_at_test','107.00.0'),
                          ('completed_stages',59),('returncode',1),('sha256','0'*64),
                          ('version','108.00.0')]:
            bad=dict(state,key='no')
            bad[key]=value
            try:activation_manifest(bad,archive,stage)
            except ValueError:ck(True,'bad state denied '+key)
            else:raise AssertionError('invalid approval accepted '+key)
        test_file=stage/'world/v10900_horizons.py'
        original_bytes=test_file.read_bytes()
        test_file.write_text('changed after ZIP',encoding='utf-8')
        try:activation_manifest(state,archive,stage)
        except ValueError:ck(True,'stage mutation denied before stop')
        else:raise AssertionError('changed stage accepted')
        # Exact bytes matter: Windows text-mode write_text changes LF to CRLF.
        test_file.write_bytes(original_bytes)
        extra=stage/'evil.txt'
        extra.write_text('unexpected')
        try:activation_manifest(state,archive,stage)
        except ValueError:ck(True,'injected file denied')
        else:raise AssertionError('extra stage file accepted')
        extra.unlink()
        manifest=activation_manifest(state,archive,stage)
        ck(manifest['sha256']==sha and len(manifest['files'])==len(REQUIRED),'complete approved manifest')
        with ZipFile(archive) as z:z.extractall(base/'extracted')
        source=base/'extracted'/'Soulbound-MUD'
        import shutil
        shutil.copytree(source,installed)
        marker=installed/MARKER
        marker.parent.mkdir(parents=True,exist_ok=True)
        marker.write_text(json.dumps(manifest),encoding='utf-8')
        db=installed/'soulbound.db'
        db.touch()
        ck(verify_root_for_test(installed),'clean installed marker verified')
        with patch.dict('os.environ',{'SOULBOUND_V109_STAGING':'0','SOULBOUND_V107_STAGING':'0'}):
            ck(authorized_runtime(db,root=installed)=='production','production startup allowed only after approval')
            ck(ensure_authorized_start(db,root=installed)=='production','canonical production DB allowed')
            ck(authorized_runtime(base/'other.db',root=installed) is None,'other SQLite rejected')
        shutil.rmtree(base/'Soulbound_PREDEPLOY',ignore_errors=True)
        ck(verify_root_for_test(installed),'PREDEPLOY folder not required after install')
        guard=installed/'server/mud_server.py'
        guard.write_text('tampered')
        ck(not verify_root_for_test(installed),'tampered installed server denied')
        try:ensure_authorized_start(db,root=installed)
        except PermissionError:ck(True,'tampered server refuses production')
        else:raise AssertionError('tampered server allowed')
        guard.write_bytes((stage/'server/mud_server.py').read_bytes())
        ck(verify_root_for_test(installed),'restored exact code accepted')
        marker.unlink()
        ck(not verify_root_for_test(installed),'missing marker denied')
        ck(authorized_runtime(db,root=installed) is None,'missing marker cannot start')
        marker.write_text(json.dumps(manifest),encoding='utf-8')
        db.unlink()
        try:
            db.symlink_to(base/'outside.db')
        except OSError as exc:
            # Non-elevated Windows accounts commonly fail os.symlink with
            # WinError 1314. The security assertion must still be executed:
            # simulate exactly the symlink flag that authorized_runtime checks,
            # without changing the running account's privileges or weakening
            # the actual boot guard.
            if getattr(exc,'winerror',None) != 1314:
                raise
            real_is_symlink=Path.is_symlink
            def simulated_is_symlink(path):
                return path == db or real_is_symlink(path)
            with patch.object(Path,'is_symlink',simulated_is_symlink):
                ck(authorized_runtime(db,root=installed) is None,
                   'symlink DB denied even without Windows symlink privilege')
        else:
            ck(authorized_runtime(db,root=installed) is None,
               'symlinked DB denied')
    print('V109 ACTIVATION AND BOOT:',n,'checks PASS; synthetic only')
    return n

if __name__=='__main__':run()
