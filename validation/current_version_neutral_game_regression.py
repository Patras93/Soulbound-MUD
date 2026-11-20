# -*- coding: utf-8 -*-
"""Guard core gameplay and fresh install against release-specific activation."""
from __future__ import annotations
from pathlib import Path
import sqlite3
import sys
import tempfile
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from systems import current_install
from systems.current_install_ledger import initialize_empty_ledger
from systems.universal_activation import current_version

ROOT=Path(__file__).resolve().parents[1]
TARGETS=(
 'systems/runtime_activation.py',
 'player/session_mixins/command_special_handlers.py',
 'systems/magitek/magicite.py',
 'systems/holiday/combat.py',
 'systems/current_install.py',
 'systems/current_install_bootstrap.py',
 'systems/current_install_ledger.py',
)

def run():
    checks=0
    for name in TARGETS:
        content=(ROOT/name).read_text(encoding='utf-8')
        assert 'from systems.v11200_activation import' not in content, name
        assert 'SOULBOUND_V112_STAGING' not in content, name
        checks+=2
    from aktualizuj_soulbound import production_release_mapping
    assert 'systems/v11200_activation.py' not in {p.as_posix() for p in production_release_mapping({Path('systems/v11200_activation.py'):None,Path('systems/runtime_activation.py'):None})}
    checks+=1
    from core.release_version import load_version
    from aktualizuj_soulbound import file_version,read_archive_version,archive_mapping
    import zipfile
    assert load_version(ROOT)==current_version(ROOT)
    assert file_version(ROOT/'core/bootstrap_economy_professions.py')==load_version(ROOT)
    checks+=2
    with tempfile.TemporaryDirectory(prefix='sb_version_zip_') as temporary:
        archive=Path(temporary)/'candidate.zip'
        with zipfile.ZipFile(archive,'w') as z:
            for rel in ('VERSION','core/bootstrap_economy_professions.py','core/release_version.py'):
                z.write(ROOT/rel, 'Soulbound-MUD/'+rel)
            for rel in ('server.py','START_Soulbound.bat','STOP_Soulbound.bat','predeploy_check.py'):
                z.writestr('Soulbound-MUD/'+rel,'fixture')
        with zipfile.ZipFile(archive) as z:
            mapping=archive_mapping(z)
            assert read_archive_version(z,mapping)==load_version(ROOT)
        checks+=1
    assert current_install.VERSION==current_version(ROOT)
    assert current_install.VALIDATORS[0]=='validation.current_universal_release_suite'
    checks+=2
    for future in ('113.00.0','114.09.2','220.00.0'):
        with tempfile.TemporaryDirectory(prefix='sb_current_versions_') as temp:
            root=Path(temp)
            (root/'VERSION').write_text(future,encoding='utf-8')
            assert current_version(root)==future
            checks+=1
    with tempfile.TemporaryDirectory(prefix='sb_current_install_unit_') as temp:
        db=sqlite3.connect(Path(temp)/'scratch.sqlite')
        try:
            for table in ('accounts','characters','inventory','equipment','bank_items','profession_storage'):
                db.execute('CREATE TABLE '+table+' (id INTEGER)')
            db.commit()
            result=initialize_empty_ledger(db)
            assert result['version']==current_version(ROOT)
            assert db.execute('SELECT version FROM current_install_origin').fetchone()[0]==current_version(ROOT)
            assert db.execute('PRAGMA integrity_check').fetchone()[0]=='ok'
            checks+=3
        finally:db.close()
    # A release's own universal modules determine activation/update.  Old
    # installed-version-specific paths are NOT used for modern candidates.
    from unittest.mock import patch
    from aktualizuj_soulbound import run_update, UpdateError
    from predeploy_nowej_wersji import verified_staged_pass
    import wdroz_po_predeploy as deploy
    import json
    from systems import universal_release_update
    with tempfile.TemporaryDirectory(prefix='sb_future_dispatch_') as temp:
        home=Path(temp)
        evidence=home/'proof.log'
        evidence.write_text('WYNIK KONCOWY: PASS - WSZYSTKIE 60 ETAPOW PLUS\n'
                            'PLUS CHECKS PASS\nSOULBOUND RELEASE GATES PASS\n',
                            encoding='utf-8')
        candidates=(current_version(ROOT),'219.47.5','301.00.1')
        for future in candidates:
            assert verified_staged_pass(0,evidence,future,current_contract=True)
            assert not verified_staged_pass(1,evidence,future,current_contract=True)
            checks+=2
            archive=home/('Soulbound-MUD-v'+future+'-fixture.zip')
            with zipfile.ZipFile(archive,'w') as z:
                for rel in ('VERSION','core/bootstrap_economy_professions.py',
                            'core/release_version.py','server.py',
                            'predeploy_check.py','START_Soulbound.bat','STOP_Soulbound.bat',
                            'systems/runtime_activation.py',
                            'systems/universal_release_update.py',
                            'systems/current_fresh_install.py'):
                    if rel=='VERSION':data=future+'\n'
                    elif (ROOT/rel).is_file():data=(ROOT/rel).read_bytes()
                    else:data=b'fixture\n'
                    z.writestr('Soulbound-MUD/'+rel,data)
            with patch.object(universal_release_update,'update',return_value=home/'backup') as call:
                assert run_update(home,archive,future,restart=False)==home/'backup'
                assert call.call_count==1
                assert call.call_args.args[2]==future
                checks+=2
            statefile=home/'last_result.json'
            record={'status':'PASS','quality_gate':'ULTIMATE-60-PLUS',
                    'required_stages':60,'completed_stages':60,'returncode':0,
                    'release_gates_pass':True,'version':future,
                    'installed_at_test':'115.00.12','sha256':'a'*64,
                    'zip':str(archive),'finished_at':'fixture'}
            statefile.write_text(json.dumps(record),encoding='utf-8')
            current_modules={name:None for name in (
                'systems/runtime_activation.py',
                'systems/universal_release_update.py',
                'systems/current_fresh_install.py')}
            with patch.object(deploy,'STATE',statefile), \
                 patch.object(deploy,'ROOT',home), \
                 patch.object(deploy,'sha256',return_value='a'*64), \
                 patch.object(deploy,'installed_version',return_value='115.00.12'), \
                 patch.object(deploy,'inspect_zip',return_value=(future,current_modules)), \
                 patch('builtins.input',return_value='WDRAZAM'), \
                 patch.object(deploy.subprocess,'call',return_value=0) as invoked:
                assert deploy.main()==0
                assert invoked.call_count==1
                checks+=2
                record['release_gates_pass']=False
                statefile.write_text(json.dumps(record),encoding='utf-8')
                invoked.reset_mock()
                assert deploy.main()==1
                invoked.assert_not_called()
                checks+=2
                record['release_gates_pass']=True
                record['sha256']='b'*64
                statefile.write_text(json.dumps(record),encoding='utf-8')
                assert deploy.main()==1
                invoked.assert_not_called()
                checks+=2
        # No universal API: a future label must not run the historical updater.
        bad=home/'Soulbound-MUD-v220.00.0-bad.zip'
        with zipfile.ZipFile(bad,'w') as z:
            for rel in ('VERSION','core/bootstrap_economy_professions.py',
                        'server.py','START_Soulbound.bat','STOP_Soulbound.bat',
                        'predeploy_check.py'):
                z.writestr('Soulbound-MUD/'+rel,
                           '220.00.0\n' if rel=='VERSION' else
                           (ROOT/rel).read_bytes() if (ROOT/rel).is_file() else b'x')
        try:run_update(home,bad,'220.00.0',restart=False)
        except UpdateError:checks+=1
        else:raise AssertionError('Brak uniwersalnego API nie zablokowal wydania')
    # The full ULTIMATE security case is cheap and must be part of the
    # universal 47/47 suite.  Otherwise a stale mock can break the user's
    # 60/60 PREDEPLOY after all local release tests pass.
    from validation.predeploy_ultimate_v2328 import deployment_fail_closed
    deployment_fail_closed()
    checks+=1
    print(f'VERSION-NEUTRAL GAME: {checks}/{checks} PASS')

if __name__=='__main__':run()
