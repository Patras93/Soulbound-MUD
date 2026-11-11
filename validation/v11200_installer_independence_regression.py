# -*- coding: utf-8 -*-
"""v112: installation must not import old release installers/readiness gates.

Only disposable fixtures. Never connects to players or starts an old server.
"""
from __future__ import annotations
import ast
import hashlib
import json
import sys
import tempfile
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))
from aktualizuj_soulbound import (
    UpdateError, require_v104_official_predeploy, run_update,
    verify_prior_manifest_data_only, v111_live_release_mapping,
)
from validation.v11200_closed_runtime_gate import inspect_files,source_files


def check():
    checks=0
    # A candidate may still contain old standalone tests, but no installed
    # code may import files which were excluded by the actual installer filter.
    paths={p.relative_to(ROOT):None for p in ROOT.rglob('*') if p.is_file()
           and '__pycache__' not in p.parts and p.suffix.lower() not in ('.pyc', '.db')}
    installed={p.as_posix() for p in v111_live_release_mapping(paths)}
    result=inspect_files(source_files(ROOT),installed,
        required_files={'server.py','aktualizuj_soulbound.py','systems/v11200_activation.py'})
    assert result['missing_import_count']==0,result['missing_imports'][:15]
    checks+=1
    for path in ('aktualizuj_soulbound.py','predeploy_nowej_wersji.py'):
        tree=ast.parse((ROOT/path).read_text(encoding='utf-8-sig'))
        forbidden={'systems.v10800_eq_cutover_bridge',
                   'systems.v11000_retired_installers',
                   'validation.v10800_eq107_readonly_reconcile',
                   'validation.v10800_release_readiness',
                   'validation.v10900_release_readiness'}
        assert not any(isinstance(n,ast.ImportFrom) and n.module in forbidden
                       for n in ast.walk(tree)),path
        checks+=1
    with tempfile.TemporaryDirectory(prefix='sb112_installer_only_') as folder:
        base=Path(folder)
        # Rejected old target can neither stop the old server nor create a
        # backup, even when a caller bypasses the interactive deploy BAT.
        for ver in ('108.00.0','109.00.0','110.00.0','111.00.0'):
            try:require_v104_official_predeploy(base,base/'test.zip',ver)
            except UpdateError:checks+=1
            else:raise AssertionError('stary instalator nie zablokowany: '+ver)
            try:run_update(base,base/'test.zip',ver,restart=False)
            except UpdateError:checks+=1
            else:raise AssertionError('stare run_update nie zablokowane: '+ver)
        assert not list(base.iterdir())
        checks+=1
        backup=base/'backup';backup.mkdir()
        for rel,content in {'VERSION':b'110.00.0\n','server.py':b'old_server',
                            'core/bootstrap_economy_professions.py':b'VERSION="110.00.0"',
                            'validation/old.py':b'old_check'}.items():
            p=backup/rel;p.parent.mkdir(exist_ok=True,parents=True);p.write_bytes(content)
        data={'schema':1,'version':'110.00.0','status':'PASS',
              'quality_gate':'ULTIMATE-60-PLUS','source_gate':'WINDOWS_PREDEPLOY_APPROVED',
              'archive_sha256':'a'*64,
              'files':{rel:hashlib.sha256((backup/rel).read_bytes()).hexdigest()
                       for rel in ('VERSION','server.py','core/bootstrap_economy_professions.py','validation/old.py')}}
        assert verify_prior_manifest_data_only(backup,data,'110.00.0');checks+=1
        assert not verify_prior_manifest_data_only(backup,data,'109.00.0');checks+=1
        tampered=json.loads(json.dumps(data));tampered['quality_gate']='UNKNOWN'
        assert not verify_prior_manifest_data_only(backup,tampered,'110.00.0');checks+=1
        (backup/'validation/old.py').write_text('locally edited',encoding='utf-8')
        assert not verify_prior_manifest_data_only(backup,data,'110.00.0');checks+=1
        assert (backup/'validation/old.py').read_text()=='locally edited';checks+=1
    print(f'V112 INSTALATOR BEZ STARYCH SKRYPTOW: {checks} kontroli PASS; '
          f'pozostale historyczne importy aktywnej gry: {result["old_version_import_count"]}')

if __name__=='__main__':check()
