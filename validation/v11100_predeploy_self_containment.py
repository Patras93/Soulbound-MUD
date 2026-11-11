# -*- coding: utf-8 -*-
"""v111: required current release paths, not historical file backups.

This is an independent quick gate. It never substitutes for 60 Windows stages.
"""
from __future__ import annotations
import tempfile,zipfile
from pathlib import Path
from predeploy_nowej_wersji import inspect_zip, REQUIRED as CANDIDATE_CORE
from aktualizuj_soulbound import archive_mapping, v111_live_release_mapping
from validation.v11100_release_suite import GATES
from testuj_soulbound_windows import STAGES,v107_gate_proof
from systems.v11100_holiday_activation import REQUIRED as LIVE_REQUIRED

ROOT=Path(__file__).resolve().parents[1]
OBSOLETE_QUEST=(
    'data/catalogs_v109/quests_01.py', 'data/catalogs_v109/quests_02.py',
    'data/catalogs_v109/quests_03.py',
    'world/quests_v110/__init__.py', 'world/quests_v110/classes.py',
    'world/quests_v110/races.py', 'world/quests_v110/events.py',
    'world/quests_v110/regional.py',
)
OBSOLETE_AUDITS=('admin/audits.py', 'admin/v410_equipment_audits.py',
                 'systems/full_systems_audit_v03062.py')

def main():
    assert len(STAGES)==60,('PREDEPLOY must retain 60 stages',len(STAGES))
    assert len({name for name, *_ in STAGES})==60
    assert 'validation/v11100_predeploy_self_containment.py' in GATES
    # A previous release's audit file must no longer provide the v111 runner.
    from validation.v11100_v107_functional_audit import (
        SUITES as V111_COMPAT_SUITES,suites_reviewed)
    assert suites_reviewed() and len(V111_COMPAT_SUITES)==33
    # Current FAST/FULL entrypoints are standalone from v110 test launchers.
    from validation.v11100_current_tail_isolation import AUDITS as TAIL,regression
    assert len(TAIL)==5 and regression()>=45
    fast=(ROOT/'predeploy_check.py').read_text('utf8')
    full=(ROOT/'predeploy_full.py').read_text('utf8')
    for script in (fast,full):
        assert 'from validation.v11100_current_tail_isolation import' in script
        assert 'from validation.v11000_legacy_tail_isolation import' not in script
        for key in TAIL:
            assert f"_v110_legacy_tail('{key}')" in script
    assert 'from validation.v11100_private_fast_gate import' in fast
    assert 'from validation.v11000_fast_predeploy_guard import' not in fast
    assert 'from validation.v11100_private_fast_gate import enable_isolated_fast_predeploy' in fast
    assert 'from validation.v11100_private_fast_gate import isolated_predeploy_env' in full
    assert 'from validation.v10400_fast_predeploy_isolation import' not in fast
    assert 'from validation.v10400_fast_predeploy_isolation import' not in full
    isolation_source=(ROOT/'validation/v11100_private_fast_gate.py').read_text('utf8')
    assert 'from validation.v10400_release_isolation_guard import' not in isolation_source
    assert 'from validation.v10400_fast_predeploy_isolation import' not in isolation_source
    from validation.v11100_private_fast_gate import (
        isolated_predeploy_env as current_private_env,
        _DROP_LIVE_ENV_V111, enable_isolated_fast_predeploy)
    # Boundary tests use a fresh lab and intentionally malicious inherited
    # environment. No production database, Railway secret, or port survives.
    with tempfile.TemporaryDirectory(prefix='sb104_tcp_lab_') as lab:
        dirty={field:'SENSITIVE' for field in _DROP_LIVE_ENV_V111}
        dirty.update(RAILWAY_SECRET_TOKEN='SENSITIVE',
                     SOULBOUND_SECRET_TEST='SENSITIVE',
                     SOULBOUND_TOKEN_TEST='SENSITIVE',
                     PATH='safe',SOULBOUND_V111_STAGING='0')
        current=current_private_env(dirty,lab,49129)
        assert current['SOULBOUND_HOST']=='127.0.0.1'
        assert current['SOULBOUND_DB']==str(Path(lab).resolve()/'tcp_test.sqlite')
        assert current['PORT']==current['SOULBOUND_PORT']=='49129'
        assert current['PATH']=='safe'
        assert not any('SENSITIVE'==value for value in current.values())
        for key in ('DATABASE_URL','RAILWAY_TCP_APPLICATION_PORT',
                    'SOULBOUND_CONTROL_TOKEN','RAILWAY_SECRET_TOKEN',
                    'SOULBOUND_ADMIN_ACCOUNTS','SOULBOUND_SECRET_TEST',
                    'SOULBOUND_TOKEN_TEST'):
            assert key not in current,key
        assert current['SOULBOUND_TCP_TEST_CHILD']=='1'
        for bad in (4000, 0, 1024, 65536, True, '49129'):
            try:current_private_env({},lab,bad)
            except ValueError:
                rejected = True
            else:raise AssertionError(('unsafe v111 FAST port',bad))
        try:current_private_env({},Path(lab).parent,49129)
        except ValueError:
            rejected = True
        else:raise AssertionError('untrusted v111 FAST directory')
    # The active runner is safe on its own; no old v104 modules are imported
    # when its environment is prepared in an isolated subprocess.
    import subprocess, sys, os
    code="import os, sys\nfrom validation.v11100_private_fast_gate import enable_isolated_fast_predeploy\nlab, port=enable_isolated_fast_predeploy()\ntry:\n    assert os.environ['SOULBOUND_HOST']=='127.0.0.1'\n    assert os.environ['SOULBOUND_DB'].endswith('tcp_test.sqlite')\n    assert port != 4000\n    assert 'validation.v10400_fast_predeploy_isolation' not in sys.modules\n    assert 'validation.v10400_release_isolation_guard' not in sys.modules\n    assert 'RAILWAY_SECRET_TOKEN' not in os.environ\nfinally:lab.cleanup()\n"
    subenv=os.environ.copy()
    subenv['RAILWAY_SECRET_TOKEN']='DUMMY_SECRET_TEST_VALUE'
    run=subprocess.run([sys.executable,'-c',code],cwd=ROOT,env=subenv,
                       capture_output=True,text=True,timeout=12)
    assert run.returncode==0,(run.stdout,run.stderr)
    # Negative security tests do not import game runtime or touch real DB.
    from validation.v11100_private_fast_gate import authorize_private_lab
    from unittest.mock import patch
    import os
    with tempfile.TemporaryDirectory(prefix='sb104_tcp_lab_') as lab:
        path=Path(lab)/'tcp_test.sqlite'
        env={'SOULBOUND_DB':str(path),'SOULBOUND_HOST':'127.0.0.1',
             'SOULBOUND_PORT':'49129','PORT':'49129',
             'SOULBOUND_TCP_TEST_CHILD':'1'}
        with patch.dict(os.environ,env,clear=True):
            assert authorize_private_lab(lab,49129) is True
            assert os.environ.get('SOULBOUND_V111_STAGING')=='1'
            assert not path.exists()
            for bad in ({'SOULBOUND_PORT':'4000'},
                        {'SOULBOUND_HOST':'0.0.0.0'},
                        {'SOULBOUND_DB':str(ROOT/'soulbound.db')},
                        {'SOULBOUND_TCP_TEST_CHILD':'0'},
                        {'PORT':'4000'}):
                with patch.dict(os.environ,bad):
                    try:authorize_private_lab(lab,49129)
                    except PermissionError:
                        rejected = True
                    else:raise AssertionError(('unprotected FAST environment',bad))
            for port in (4000,1024,65536):
                try:authorize_private_lab(lab,port)
                except PermissionError:
                    rejected = True
                else:raise AssertionError(('unauthorized port',port))
    current_audit=(ROOT/'validation/v11100_v107_functional_audit.py').read_text('utf8')
    assert 'from audyt_v107_windows_przed_predeploy import' not in current_audit
    assert v107_gate_proof('111.00.0',[]) is False
    assert v107_gate_proof('111.00.0',[('V107',1)]) is False
    assert v107_gate_proof('111.00.0',[('V107',0),('V107',0)]) is False
    assert v107_gate_proof('111.00.0',[('V107',0)]) is True
    assert v107_gate_proof('110.00.0',[]) is False
    assert v107_gate_proof('106.00.0',[]) is True
    assert v107_gate_proof('112.00.0',[]) is False
    assert v107_gate_proof('unknown',[]) is False
    assert not any(x in LIVE_REQUIRED for x in (*OBSOLETE_QUEST,*OBSOLETE_AUDITS))
    # Old quest copies must be absent even from the FULL release candidate.
    assert all(not (ROOT/rel).exists() for rel in OBSOLETE_QUEST), (
        'retired quest copies still shipped',
        [rel for rel in OBSOLETE_QUEST if (ROOT/rel).exists()])
    from validation.v11100_canonical_quests_regression import run as current_quests
    assert current_quests() >= 16
    # The approved code's source list must be standalone; it must not import
    # the previous release activation module merely to obtain required files.
    source=(ROOT/'systems/v11100_holiday_activation.py').read_text(encoding='utf8')
    assert 'from systems.v11000_activation import CORE' not in source
    needed=set(CANDIDATE_CORE)|{'VERSION',
       'systems/v11100_holiday_activation.py',
       'validation/v11100_release_suite.py',
       'validation/v11100_release_readiness.py',
       'validation/v11100_release_activation_regression.py',
       'validation/v11100_predeploy_self_containment.py',
       'validation/v11100_current_tail_isolation.py',
       'validation/v11100_private_fast_gate.py',
       'world/quests/base_01.py','world/quests/base_02.py','world/quests/base_03.py',
       'world/quests/classes.py','world/quests/races.py',
       'world/quests/events.py','world/quests/regional.py'}
    assert not needed.intersection((*OBSOLETE_QUEST,*OBSOLETE_AUDITS))
    with tempfile.TemporaryDirectory(prefix='sb111_no_old_files_') as td:
        archive=Path(td)/'Soulbound-MUD-v111.00.0-independence.zip'
        with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
            for rel in sorted(needed):
                z.write(ROOT/rel,'Soulbound-MUD/'+rel)
        version,found=inspect_zip(archive)
        assert version=='111.00.0'
        assert not any(rel.casefold() in found for rel in (*OBSOLETE_QUEST,*OBSOLETE_AUDITS))
        with zipfile.ZipFile(archive) as z:
            release=v111_live_release_mapping(archive_mapping(z))
        assert not any(Path(rel) in release for rel in (*OBSOLETE_QUEST,*OBSOLETE_AUDITS))
        assert Path('world/quests/classes.py') in release
    print('V111 PREDEPLOY CURRENT SOURCE PASS: 60 stages; 33 v107 checks independent; '
          'candidate ZIP needs no old quest snapshots or archived audits',flush=True)

if __name__=='__main__':main()
