# -*- coding: utf-8 -*-
"""v112: no historical runtime coupling; current staging/activation safety."""
from __future__ import annotations
import ast
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]

def run_regression():
    from core.runtime_manifest import RUNTIME_MODULES, FULL_RUNTIME_MODULES
    from systems.v11200_activation import _test_database, REQUIRED
    current='world/runtime_gameplay_finalize.py'
    assert current in RUNTIME_MODULES
    assert current in REQUIRED
    assert 'world/runtime_gameplay_finalize_v111.py' not in RUNTIME_MODULES
    assert not (ROOT/'world/runtime_gameplay_finalize_v111.py').exists()
    assert all(not rel.startswith('validation/') for rel in RUNTIME_MODULES)
    assert 'admin/audits.py' not in RUNTIME_MODULES
    assert 'systems/full_systems_audit_v03062.py' not in RUNTIME_MODULES
    assert 'admin/audits.py' in FULL_RUNTIME_MODULES
    assert 'admin/audits.py' not in REQUIRED
    native=(ROOT/'core/native_runtime.py').read_text('utf-8')
    assert 'candidate_validation =' not in native
    assert 'active_modules=tuple(RUNTIME_MODULES)' in native
    assert 'importlib.import_module(name)' in native
    assert '_seed_module' not in native and '_sync_modules' not in native
    runner=(ROOT/'testuj_soulbound_windows.py').read_text('utf-8')
    assert 'v112_extra=[]' in runner
    for relative,case in (('validation/predeploy_ultra_v2327.py','24'),
                          ('validation/predeploy_ultimate_v2328.py','50')):
        source=(ROOT/relative).read_text('utf-8')
        tree=ast.parse(source)
        assert any(isinstance(n,ast.keyword) and n.arg=='SOULBOUND_V112_STAGING'
                   and isinstance(n.value,ast.Constant) and n.value.value=='1'
                   for n in ast.walk(tree)),(case,'missing explicit staging flag')
        assert 'inherited_flags' not in source,(case,'legacy staging flags propagated')
    with tempfile.TemporaryDirectory(prefix='sb-ultimate-tcp-waves-') as td:
        good=Path(td)/'wave.sqlite'
        clean={'SOULBOUND_V112_STAGING':'1','SOULBOUND_HOST':'127.0.0.1',
               'SOULBOUND_PORT':'49129','SOULBOUND_DB':str(good)}
        with patch.dict(os.environ,clean,clear=True):
            assert _test_database(good)
            for change in ({'SOULBOUND_PORT':'4000'}, {'SOULBOUND_HOST':'0.0.0.0'},
                           {'SOULBOUND_V112_STAGING':'0'},
                           {'SOULBOUND_DB':str(ROOT/'soulbound.db')}):
                with patch.dict(os.environ,change):
                    assert not _test_database(os.environ['SOULBOUND_DB']),change
    from admin.fast_predeploy_audit_v0571 import FAST_PREDEPLOY_AUDIT_V0571 as scan
    assert scan['swallowed_exception_count']==0,scan['swallowed_exception_sites']
    assert scan['error_count']==0,scan['errors']
    return 28

if __name__=='__main__':
    print('V112 CURRENT RUNTIME / PREDEPLOY INDEPENDENCE: '+str(run_regression())+' checks PASS')
