# -*- coding: utf-8 -*-
"""Guard the future-version PREDEPLOY and six-client staging contract.

No production SQLite, game port or historical activation file is touched.
"""
from __future__ import annotations
import os
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from testuj_soulbound_windows import stage_env, future_release_proof
from systems.universal_activation import _test_database


def check():
    count=0
    expected=(
        ('UNIWERSALNE TESTY NOWEGO WYDANIA',0),
        ('FIZYCZNE EQ NA KOPII BAZY',0),
        ('SZESC GRACZY TCP, QUESTY I RESTART',0),
    )
    assert future_release_proof('113.00.0',expected);count+=1
    assert future_release_proof('224.03.9',expected);count+=1
    assert future_release_proof('112.00.0',());count+=1
    for values in ((),expected[:2],expected[1:],expected[:1]+(expected[1][0],1),
                   (('ZASTEPSTWO EQ',0),expected[1],expected[2]),
                   (expected[0],expected[2],expected[1])):
        assert not future_release_proof('113.00.0',values),values
        count+=1
    with tempfile.TemporaryDirectory(prefix='soulbound-predeploy-stage-') as folder:
        env=stage_env(folder)
        database=Path(env['SOULBOUND_DB'])
        assert database.parent==Path(folder) and database.name=='audit.sqlite';count+=1
        assert env['SOULBOUND_UNIVERSAL_STAGING']=='1';count+=1
        assert env['SOULBOUND_HOST']=='127.0.0.1';count+=1
        assert env['SOULBOUND_PORT']!='4000';count+=1
        with patch.dict(os.environ,env,clear=True):
            assert _test_database(database);count+=1
            for mutation in ({'SOULBOUND_UNIVERSAL_STAGING':'0'},
                             {'SOULBOUND_HOST':'0.0.0.0'},
                             {'SOULBOUND_PORT':'4000'},
                             {'SOULBOUND_DB':str(ROOT/'soulbound.db')}):
                with patch.dict(os.environ,mutation):
                    assert not _test_database(os.environ['SOULBOUND_DB']),mutation
                    count+=1
        assert not database.exists(),'fixture wrote a real SQLite database';count+=1
    print(f'CURRENT STAGING / FUTURE RELEASE PROOF: {count} checks PASS')
    return count

if __name__=='__main__':check()
