# -*- coding: utf-8 -*-
"""v112: independent signed manifest and fail-closed v111->v112 transition."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
from tempfile import TemporaryDirectory
from shutil import copy2
import os
from unittest.mock import patch
import sys

from systems import v11200_activation as activation

ROOT=Path(__file__).resolve().parents[1]
def main():
    assert activation.VERSION=='112.00.0'
    assert 'systems/v11200_activation.py' in activation.REQUIRED
    assert 'systems/runtime_activation.py' in activation.REQUIRED
    assert not any(name in activation.REQUIRED for name in (
        'systems/v10700_activation.py', 'systems/v11000_activation.py',
        'systems/v11100_holiday_activation.py'))
    with TemporaryDirectory(prefix='sb112_activation_') as folder:
        temp=Path(folder)
        stage=temp/'stage'
        stage.mkdir()
        members=set(activation.REQUIRED)|{'CHANGELOG_PL.txt'}
        for rel in sorted(members):
            source=ROOT/rel
            dest=stage/rel
            dest.parent.mkdir(parents=True,exist_ok=True)
            copy2(source,dest)
        archive=temp/'test_only.zip'
        archive.write_bytes(b'no production archive')
        state={
            'status':'PASS','quality_gate':'ULTIMATE-60-PLUS',
            'returncode':0,'completed_stages':60,'required_stages':60,
            'version':'112.00.0','installed_at_test':'111.00.0',
            'v112_release_gates_pass':True,
            'sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),
        }
        # v112 must also repair a verified but broken v110 installation.
        accepted_v110=dict(state,installed_at_test='110.00.0')
        assert activation.activation_manifest(accepted_v110,archive,stage,{rel:None for rel in members})['version']=='112.00.0'
        bad=dict(state,installed_at_test='109.00.0')
        for invalid in (bad,dict(state,v112_release_gates_pass=False),
                        dict(state,completed_stages=59),dict(state,sha256='0'*64)):
            try:activation.activation_manifest(invalid,archive,stage,{rel:None for rel in members})
            except ValueError:
                rejected = True
            else:raise AssertionError('v112 activation must reject mismatched approval')
        assert not activation.verify(stage), 'no marker = no production approval'
        manifest=activation.activation_manifest(state,archive,stage,{rel:None for rel in members})
        assert 'CHANGELOG_PL.txt' not in manifest['files']
        marker=stage/activation.MARKER
        marker.parent.mkdir(parents=True,exist_ok=True)
        marker.write_text(json.dumps(manifest),encoding='utf-8')
        assert activation.verify(stage), 'signed 112 stage should pass'
        (stage/'CHANGELOG_PL.txt').unlink()
        assert activation.verify(stage), 'optional changelog must not be required'
        code=stage/'systems/v11200_activation.py'
        code.write_bytes(code.read_bytes()+b'\n# modified after approval\n')
        assert not activation.verify(stage), 'modified code invalidates manifest'
    with TemporaryDirectory(prefix='sb-ultra-5-tcp-') as folder:
        db=Path(folder)/'stress.db'
        db.write_bytes(b'')
        env={'SOULBOUND_V107_STAGING':'1','SOULBOUND_V109_STAGING':'1',
             'SOULBOUND_V110_STAGING':'1','SOULBOUND_V111_STAGING':'1',
             'SOULBOUND_V112_STAGING':'1','SOULBOUND_HOST':'127.0.0.1',
             'SOULBOUND_PORT':'49455'}
        with patch.dict(os.environ,env,clear=True):
            assert activation._test_database(str(db))
            assert not activation._test_database(str(ROOT/'soulbound.db'))
            os.environ.pop('SOULBOUND_V112_STAGING')
            assert not activation._test_database(str(db)), 'missing current flag must be blocked'
            os.environ['SOULBOUND_V112_STAGING']='1'
            # v112 must not import or need earlier activation modules.
            os.environ.pop('SOULBOUND_V107_STAGING',None)
            os.environ.pop('SOULBOUND_V109_STAGING',None)
            os.environ.pop('SOULBOUND_V110_STAGING',None)
            os.environ.pop('SOULBOUND_V111_STAGING',None)
            with patch.dict(sys.modules, {'systems.v11000_activation':None,
                                          'systems.v11100_holiday_activation':None}):
                assert activation._test_database(str(db))
            os.environ['SOULBOUND_PORT']='4000'
            assert not activation._test_database(str(db)), 'production port is forbidden'
            os.environ['SOULBOUND_PORT']='49455'
            os.environ['SOULBOUND_HOST']='0.0.0.0'
            assert not activation._test_database(str(db)), 'public host forbidden'
            os.environ['SOULBOUND_HOST']='127.0.0.1'
            unknown=Path(folder)/'unrelated.sqlite'
            assert not activation._test_database(str(unknown)), 'wrong lab filename forbidden'
        with TemporaryDirectory(prefix='sb112_lab_') as standalone:
            path=Path(standalone)/'fresh.sqlite'
            env={'SOULBOUND_V112_STAGING':'1','SOULBOUND_HOST':'127.0.0.1',
                 'SOULBOUND_PORT':'49455'}
            with patch.dict(os.environ,env,clear=True):
                assert activation._test_database(str(path)), 'current release lab allowed'
                real_db=Path(standalone)/'soulbound.db'
                assert not activation._test_database(str(real_db)), 'player db name forbidden'
    print('V112 APPROVAL PASS: signed files, version transition, tamper, stale PASS, private DB')

if __name__=='__main__':main()
