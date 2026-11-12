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
from systems.universal_release_update import validate_approval, ensure_stopped_for_upgrade, activate_candidate, verify_stage, update
import systems.universal_release_update as release_update
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
        publish=src.index('publish_clean(stage,target,verify_stage)')
        assert preflight < stop < rehash < reapprove < backup < transfer < publish
        n+=1
        # Unapproved version or altered archive must block before any STOP.
        assert src.index('validate_approval(root,archive_path,new_version,digest,current)') < src.index('stage_release(archive_path,stage,production)') < stop
        assert "if port_open(4000):raise UpdateError('Port 4000 zajety" not in src
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
        manifest_path=fixture/'LIVE_CONTENT/release_current.json'
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
    print('CURRENT UNIVERSAL UPDATE: '+str(n)+' checks PASS')

if __name__=='__main__':check()
