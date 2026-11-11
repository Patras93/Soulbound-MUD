# -*- coding: utf-8 -*-
"""Niepoświadczona paczka musi zostać zablokowana (adversarial)."""
from __future__ import annotations
from pathlib import Path
from tempfile import TemporaryDirectory
from types import SimpleNamespace
from unittest.mock import patch
import os
import json
from systems import v11100_holiday_activation as a

def main():
    with TemporaryDirectory(prefix='sb111_activation_test_') as temp:
        root=Path(temp)
        (root/'VERSION').write_text(a.VERSION,encoding='utf-8')
        assert not a.verify(root)
        marker=root/a.MARKER
        marker.parent.mkdir()
        marker.write_text(json.dumps({'schema':1,'version':a.VERSION,
            'status':'PASS','quality_gate':'ULTIMATE-60-PLUS',
            'source_gate':'WINDOWS_PREDEPLOY_APPROVED',
            'archive_sha256':'0'*64,'files':{}}),encoding='utf-8')
        assert not a.verify(root), 'sam znacznik nie może zatwierdzić instalacji'
        assert not a.production_approved(), 'niezatwierdzona paczka nie może włączyć produkcji'
        try: a.activation_manifest({'status':'PASS'},root,root,{})
        except ValueError as exc: assert 'brak zatwierdzenia PREDEPLOY' in str(exc)
        else:raise AssertionError('brak 60/60 nie może wystawić manifestu')
        marker.unlink()
        assert not a.verify(root)
    with TemporaryDirectory(prefix='sb-ultra-5-tcp-') as directory:
        private=Path(directory)/'stress.db'
        private.write_bytes(b'')
        flags={
            'SOULBOUND_V107_STAGING':'1','SOULBOUND_V109_STAGING':'1',
            'SOULBOUND_V110_STAGING':'1','SOULBOUND_V111_STAGING':'1',
            'SOULBOUND_HOST':'127.0.0.1','SOULBOUND_PORT':'49455',
        }
        with patch.dict(os.environ,flags,clear=True):
            assert a._test_database(str(private))
            assert not a._test_database(str(a.ROOT/'soulbound.db'))
            os.environ.pop('SOULBOUND_V111_STAGING')
            assert not a._test_database(str(private))
    # v85's second private UOSS launcher must retain *existing* approval,
    # but no missing v111 flag may be fabricated in the child environment.
    from arena_real_izolowana import _private_env
    with TemporaryDirectory(prefix='soulbound-v111-v85-staging-') as temp:
        folder=Path(temp)/'gra'
        folder.mkdir()
        (folder/'VERSION').write_text('111.00.0',encoding='utf-8')
        parent={
            'SOULBOUND_V107_STAGING':'1','SOULBOUND_V109_STAGING':'1',
            'SOULBOUND_V110_STAGING':'1','SOULBOUND_V111_STAGING':'1',
        }
        with patch.dict(os.environ,parent,clear=True):
            inherited=_private_env(folder,55409)
            assert all(inherited.get(key)=='1' for key in parent)
            assert inherited['SOULBOUND_DB']==str(folder/'soulbound.db')
            assert inherited['SOULBOUND_HOST']=='127.0.0.1'
            assert inherited['SOULBOUND_PORT']=='55409'
            os.environ.pop('SOULBOUND_V111_STAGING')
            assert 'SOULBOUND_V111_STAGING' not in _private_env(folder,55409)
            os.environ['SOULBOUND_V111_STAGING']='1'
            os.environ.pop('SOULBOUND_V109_STAGING')
            assert 'SOULBOUND_V111_STAGING' not in _private_env(folder,55409)
            os.environ['SOULBOUND_V109_STAGING']='1'
            (folder/'VERSION').write_text('110.00.0',encoding='utf-8')
            assert 'SOULBOUND_V111_STAGING' not in _private_env(folder,55409)
    # Dokumentacja pozostaje w wydaniu, ale nie moze podpisywac kodu gry.
    from shutil import copy2
    import hashlib
    with TemporaryDirectory(prefix='sb111_optional_changelog_') as temp:
        stage=Path(temp)/'game'
        stage.mkdir()
        source=Path(__file__).resolve().parents[1]
        members=set(a.REQUIRED)|{'VERSION','CHANGELOG_PL.txt'}
        for rel in sorted(members):
            target=stage/rel
            target.parent.mkdir(parents=True,exist_ok=True)
            copy2(source/rel,target)
        archive=Path(temp)/'source.zip'
        archive.write_bytes(b'isolated test only')
        digest=hashlib.sha256(archive.read_bytes()).hexdigest()
        state={'status':'PASS','quality_gate':'ULTIMATE-60-PLUS',
            'returncode':0,'completed_stages':60,'required_stages':60,
            'version':'111.00.0','installed_at_test':'110.00.0',
            'v111_release_gates_pass':True,'sha256':digest}
        manifest=a.activation_manifest(state,archive,stage,{rel:None for rel in members})
        assert 'CHANGELOG_PL.txt' not in manifest['files']
        marker=stage/a.MARKER
        marker.parent.mkdir(parents=True,exist_ok=True)
        marker.write_text(json.dumps(manifest),encoding='utf-8')
        assert a.verify(stage), 'signed code must start with changelog'
        (stage/'CHANGELOG_PL.txt').write_text('Aktualizowana historia PL',encoding='utf-8')
        assert a.verify(stage), 'editing changelog must not disable game'
        (stage/'CHANGELOG_PL.txt').unlink()
        assert a.verify(stage), 'missing changelog must not disable game'
        protected=stage/'systems/v11100_holiday_activation.py'
        protected.write_bytes(protected.read_bytes()+b'\n# changed after approval')
        assert not a.verify(stage), 'code tampering must still block runtime'
    # PREDEPLOY and updater must also accept an archive without optional text.
    from zipfile import ZipFile, ZIP_DEFLATED
    from predeploy_nowej_wersji import REQUIRED as PREDEPLOY_REQUIRED, inspect_zip
    from aktualizuj_soulbound import archive_mapping
    with TemporaryDirectory(prefix='sb111_zip_without_changelog_') as temp:
        archive=Path(temp)/'Soulbound-MUD-v111.00.0-test.zip'
        names=set(PREDEPLOY_REQUIRED)|{'VERSION',
            'systems/v11100_holiday_activation.py',
            'validation/v11100_release_suite.py',
            'validation/v11100_release_readiness.py',
            'validation/v11100_release_activation_regression.py'}
        assert 'CHANGELOG_PL.txt' not in names
        with ZipFile(archive,'w',ZIP_DEFLATED) as zipped:
            for rel in sorted(names):
                zipped.write(source/rel, 'Soulbound-MUD/'+rel)
        version,mapping=inspect_zip(archive)
        assert version=='111.00.0' and 'CHANGELOG_PL.txt' not in mapping
        with ZipFile(archive) as zipped:
            safe=archive_mapping(zipped)
            assert all(x.name!='CHANGELOG_PL.txt' for x in safe)
    # Regression for production failure 2026-11-09: the approved v110
    # server used to crash because Magitek NPC was gated on a test flag.
    # Never generate or install a real approval manifest in this test.
    import runpy
    npc_module=source/'data/npcs.py'
    with patch.dict(os.environ, {}, clear=True):
        with patch('systems.v11100_holiday_activation.production_approved', return_value=True):
            certified=runpy.run_path(str(npc_module))['NPCS']
            assert certified['teacher_magitek_v107']['teacher_class']=='Magitek'
        with patch('systems.v11100_holiday_activation.production_approved', return_value=False):
            unauthorized=runpy.run_path(str(npc_module))['NPCS']
            assert 'teacher_magitek_v107' not in unauthorized
        assert 'SOULBOUND_V107_STAGING' not in os.environ
    # Approved old EQ must restart WITHOUT a historical v106 rollback file.
    # Real ledger drift must still be refused; both are tested on private SQLite.
    from validation.v10700_production_eq_cutover_regression import run as _live_eq_test
    assert _live_eq_test() >= 23
    print('V111 EQ CURRENT STATE PASS: old backup optional, corrupted gear blocked')
    print('V111 MAGITEK LIVE NPC PASS: certified production needs no staging flag; unsigned remains blocked')
    print('V111 ACTIVATION REGRESSION PASS: no marker / forged / incomplete / no gate / isolated Windows TCP staging')
if __name__=='__main__':main()
