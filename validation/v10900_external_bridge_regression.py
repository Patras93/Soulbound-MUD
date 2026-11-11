# -*- coding: utf-8 -*-
"""v109 external bridge contract, synthetic v108 attestation and SQLite only.

No live STOP, no deployment and no real production DB. Ensures v109 does not
replace the authenticated v108 tools before an independent 60/60+ approval.
"""
from __future__ import annotations
from contextlib import closing
import hashlib
import json
import shutil
import sys
import sqlite3
from pathlib import Path
import tempfile
from unittest.mock import patch
from zipfile import ZipFile, ZIP_DEFLATED

from systems import v10800_activation as old_activation
from systems.v10900_activation import REQUIRED as NEW_REQUIRED
from predeploy_nowej_wersji import REQUIRED as PREDEPLOY_REQUIRED
from predeploy_v109_z_zewnatrz import (preflight as test_preflight,
                                       main as predeploy_main,
                                       _candidate_matches_zip)
from wdroz_v109_z_zewnatrz import (preflight as deployment_preflight,
                                   main as deployment_main)
from aktualizuj_soulbound import UpdateError

ROOT = Path(__file__).resolve().parents[1]


def run() -> int:
    checks = 0
    def ck(result, reason):
        nonlocal checks
        assert result, reason
        checks += 1
    with tempfile.TemporaryDirectory(prefix='soulbound_v109_external_bridge_') as scratch:
        parent = Path(scratch)
        live = parent/'Installed_v108'
        required = set(NEW_REQUIRED)|set(PREDEPLOY_REQUIRED)|{
            'VERSION', 'core/bootstrap_economy_professions.py',
            'systems/v10800_activation.py','validation/v10800_release_readiness.py',
            'validation/v10800_offline_suite.py',
            'validation/v10800_v107_equipment_compat_gate.py',
            'predeploy_v109_z_zewnatrz.py','wdroz_v109_z_zewnatrz.py',
            'validation/v10900_external_bridge_regression.py',
            'validation/v10900_release_readiness.py', 'validation/v10900_release_suite.py',
            'windows_launcher_state.py', 'release_readme_cleanup.py',
            'predeploy_v109_standard_router.py',
            'PREDEPLOY_NOWEJ_WERSJI.bat',
            'validation/v10900_standard_predeploy_router_regression.py',
            'CHANGELOG_PL.txt', 'START_Soulbound.bat', 'STOP_Soulbound.bat',
            'predeploy_check.py', 'Dockerfile',
        }
        ck(all((ROOT/name).is_file() for name in required),'required v109 files present')
        archive = parent/'Soulbound-MUD-v109.00.0-EXTERNAL-TEST.zip'
        with ZipFile(archive,'w',ZIP_DEFLATED) as zipped:
            for name in sorted(required):
                zipped.write(ROOT/name,'Soulbound-MUD/'+name)
        # Synthetic installed v108 fixture: it has no v109 modules or new tools;
        # it models only the durable manifest and source guards, not authentic
        # production v108 runtime binaries or a signed Windows PREDEPLOY.
        for name in old_activation.REQUIRED:
            dest=live/name
            dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(ROOT/name,dest)
        (live/'VERSION').write_text('108.00.0\n',encoding='utf-8')
        (live/'core/bootstrap_economy_professions.py').write_text(
            'VERSION="108.00.0"\n',encoding='utf-8')
        for name in ('server.py',):
            dest=live/name
            dest.parent.mkdir(parents=True,exist_ok=True)
            shutil.copy2(ROOT/name,dest)
        db=live/'soulbound.db'
        with closing(sqlite3.connect(db)) as conn:
            conn.execute('CREATE TABLE characters(name TEXT, exp INTEGER)')
            conn.execute('INSERT INTO characters VALUES (?,?)',('NIE_ZMIENIAJ',987654))
            conn.commit()
        db_before=db.read_bytes()
        from systems.v10800_activation import MARKER
        marker=live/MARKER
        marker.parent.mkdir(parents=True,exist_ok=True)
        manifest=dict(schema=2,version='108.00.0',installed_at_test='107.00.0',
                     status='PASS',quality_gate='ULTIMATE-60-PLUS',returncode=0,
                     completed_stages=60,required_stages=60,
                     v108_release_gates_pass=True,v108_eq_rebuild_trial_pass=True,
                     sha256='a'*64,
                     files={name:hashlib.sha256((live/name).read_bytes()).hexdigest()
                            for name in old_activation.REQUIRED})
        marker.write_text(json.dumps(manifest),encoding='utf-8')
        ck(old_activation.verify_root_for_test(live),'synthetic current v108 manifest valid')
        ck(not (live/'systems/v10900_activation.py').exists(),'no v109 module preinstalled')
        original_tool=(live/'aktualizuj_soulbound.py').read_bytes()
        got_live,got_archive=test_preflight(live,archive)
        ck(got_live==live and got_archive==archive,'external predeploy accepts exact candidate')
        ck(old_activation.verify_root_for_test(live),'preflight preserved v108 authorization')
        ck(db.read_bytes()==db_before,'preflight did not touch SQLite')
        ck((live/'aktualizuj_soulbound.py').read_bytes()==original_tool,'old tool not replaced')
        import predeploy_nowej_wersji as pd
        saved=(pd.ROOT,pd.WORK,pd.STATE,pd.INBOX)
        try:
            with patch.object(pd,'main',return_value=0) as runner:
                ck(predeploy_main(['--instalacja',str(live),'--zip',str(archive)])==0,
                   'external v109 PREDEPLOY entry is reachable')
                ck(pd.ROOT==live and pd.STATE==live.parent/'Soulbound_PREDEPLOY'/'last_result.json',
                   'external PREDEPLOY bases all official proofs on installed v108 parent')
                runner.assert_called_once_with([str(archive)]);checks+=1
        finally:
            pd.ROOT,pd.WORK,pd.STATE,pd.INBOX=saved
        ck(old_activation.verify_root_for_test(live),'PREDEPLOY bridge never invalidated v108')
        ck(db.read_bytes()==db_before,'bridge did not write SQLite')
        # v109 stores ONLY the historical BAT as the user-facing PREDEPLOY.
        # Verify the release ZIP and test directory do not need extra BATs.
        with ZipFile(archive) as standard_zip:
            names=set(standard_zip.namelist())
            ck('Soulbound-MUD/PREDEPLOY_NOWEJ_WERSJI.bat' in names,
               'original standard predeploy remains in release')
            for extra in ('PREDEPLOY.bat','V109_PREDEPLOY_Z_ZEWNATRZ.bat',
                          'V109_WDROZ_Z_ZEWNATRZ.bat','ZAINSTALUJ_PREDEPLOY.bat'):
                ck('Soulbound-MUD/'+extra not in names,
                   'no redundant launcher '+extra)
        ck(not (live/'predeploy_v109_standard_router.py').exists(),
           'PREDEPLOY does not overlay authenticated v108 during tests')
        ck(old_activation.verify_root_for_test(live),
           'standard preparation leaves v108 approval intact')
        ck((live/'aktualizuj_soulbound.py').read_bytes()==original_tool,
           'standard preparation leaves protected updater intact')
        ck(db.read_bytes()==db_before,'standard preparation keeps SQLite intact')
        # SHA of candidate sources must be unchanged; forge one archive entry.
        bad=parent/'Soulbound-MUD-v109.00.0-ALTERED.zip'
        with ZipFile(archive) as original,ZipFile(bad,'w',ZIP_DEFLATED) as zipped:
            for name in original.namelist():
                content=original.read(name)
                if name.endswith('/wdroz_v109_z_zewnatrz.py'):
                    content += b'\n# altered after extraction\n'
                zipped.writestr(name,content)
        try: _candidate_matches_zip(bad)
        except UpdateError: ck(True,'modified extracted vs zip deploy bridge blocked')
        else: raise AssertionError('modified candidate accepted')
        # Testy offline moga dzialac bez manifestu; wdrozenie NIE.
        for bad_manifest in ({'sha256':'x'}, {'required_stages':59},
                             {'status':'FAIL'}, {'v108_release_gates_pass':False}):
            marker.write_text(json.dumps(manifest|bad_manifest),encoding='utf-8')
            checked_live,checked_zip=test_preflight(live,archive)
            ck(checked_live==live and checked_zip==archive,'offline predeploy allows invalid manifest')
            try:deployment_preflight(live,archive)
            except UpdateError:ck(True,'deployment rejects invalid manifest')
            else:raise AssertionError('deployment accepted invalid v108 activation')
        marker.unlink()
        checked_live,checked_zip=test_preflight(live,archive)
        ck(checked_live==live and checked_zip==archive,'offline predeploy allows missing manifest')
        ck(db.read_bytes()==db_before,'missing-manifest tests preserved database')
        ck((live/'aktualizuj_soulbound.py').read_bytes()==original_tool,'missing-manifest kept approved updater')
        try:deployment_preflight(live,archive)
        except UpdateError:ck(True,'deployment rejects missing manifest')
        else:raise AssertionError('deployment accepted missing manifest')
        marker.write_text(json.dumps(manifest),encoding='utf-8')
        state=dict(status='PASS',quality_gate='ULTIMATE-60-PLUS',
                   completed_stages=60,required_stages=60,returncode=0,
                   version='109.00.0',installed_at_test='108.00.0',
                   v109_release_gates_pass=True,zip=str(archive),
                   sha256=hashlib.sha256(archive.read_bytes()).hexdigest())
        record=live.parent/'Soulbound_PREDEPLOY'/'last_result.json'
        record.parent.mkdir(exist_ok=True)
        for change in ({'status':'FAIL'}, {'completed_stages':59},
                       {'sha256':'0'*64}, {'installed_at_test':'107.00.0'},
                       {'v109_release_gates_pass':False}):
            record.write_text(json.dumps(state|change),encoding='utf-8')
            try: deployment_preflight(live,archive)
            except UpdateError: ck(True,'failed PREDEPLOY proof blocks external deployment')
            else: raise AssertionError('bad PREDEPLOY proof accepted')
        record.write_text(json.dumps(state),encoding='utf-8')
        checked,ver=deployment_preflight(live,archive)
        ck(checked==archive and ver=='109.00.0','exact approved deployment preflight')
        ck(deployment_main(['--instalacja',str(live),'--zip',str(archive),'--sprawdz'])==0,
           'read-only deployment check no STOP')
        ck(old_activation.verify_root_for_test(live),'external deployment check keeps v108 authorization')
        ck(db.read_bytes()==db_before,'external deployment check preserved SQLite bytes')
        ck(not (live/'systems/v10900_activation.py').exists(),'external check installed no v109 files')
    print('V109 EXTERNAL v108->v109 BRIDGE:',checks,'checks PASS; synthetic only; no Windows STOP')
    return checks

if __name__=='__main__':run()
