# -*- coding: utf-8 -*-
"""v109 fail-closed runtime on all non-private paths."""
from __future__ import annotations
import os
import tempfile
from pathlib import Path
from unittest.mock import patch
from systems.v10900_staging_guard import private_trial_allowed,ensure_private_trial,authorized_runtime


def run():
    n=0
    def ck(condition,name):
        nonlocal n
        assert condition,name
        n+=1
    root=Path(__file__).resolve().parents[1]
    with tempfile.TemporaryDirectory(prefix='soulbound-v109-guard-') as temp:
        good=Path(temp)/'private.sqlite'
        prod=root/'soulbound.db'
        with patch.dict(os.environ,{'SOULBOUND_V109_STAGING':'1','SOULBOUND_V107_STAGING':'1'}):
            ck(private_trial_allowed(good),'private disposable staging permitted')
            ck(not private_trial_allowed(prod),'production database denied')
            ck(not private_trial_allowed(root/'data'/'soulbound.db'),'production subfolder denied')
            ck(not private_trial_allowed(Path(temp)/'private.txt'),'wrong DB extension denied')
            ck(not private_trial_allowed(Path(temp).parent/'loose.sqlite'),'ungrouped loose temp denied')
            ensure_private_trial(good)
            ck(True,'explicit isolated trial preflight')
            link=Path(temp)/'linked.sqlite'
            try:
                link.symlink_to(prod)
            except OSError:  # AUDIT_INTENTIONAL_PASS: expected exception in negative regression fixture
                pass
            else:
                ck(not private_trial_allowed(link),'symlink to production blocked')
            for key in ('SOULBOUND_V107_STAGING','SOULBOUND_V109_STAGING'):
                with patch.dict(os.environ,{key:'0'}):
                    ck(not private_trial_allowed(good),'missing staging authorization '+key)
        with patch.dict(os.environ, {'SOULBOUND_V109_STAGING':'0','SOULBOUND_V107_STAGING':'0'}):
            try:
                ensure_private_trial(prod)
            except PermissionError:
                ck(True,'production preflight hard fails')
            else:
                raise AssertionError('v109 could start on live DB')
    # Windows stores PREDEPLOY workers INSIDE TEMP; old prefix matching used
    # to mistake the copied game's own soulbound.db for a disposable trial.
    with tempfile.TemporaryDirectory(prefix='soulbound-predeploy-workers-') as td:
        candidate=Path(td)/'candidate-0'
        candidate.mkdir()
        (candidate/'VERSION').write_text('109.00.0',encoding='utf-8')
        (candidate/'server.py').write_text('# disposable code copy',encoding='utf-8')
        with patch.dict(os.environ,{'SOULBOUND_V109_STAGING':'1','SOULBOUND_V107_STAGING':'1'}):
            ck(not private_trial_allowed(candidate/'soulbound.db'),
               'Windows PREDEPLOY candidate canonical game DB denied')
            ck(not private_trial_allowed(candidate/'staged.sqlite'),
               'Windows PREDEPLOY code directory denied for alternate SQLite')
            ck(not private_trial_allowed(candidate/'data'/'staged.sqlite'),
               'Windows PREDEPLOY nested code directory denied')
    with tempfile.TemporaryDirectory(prefix='Soulbound_PREDEPLOY_') as td:
        source=Path(td)/'Soulbound-MUD'
        source.mkdir()
        (source/'VERSION').write_text('109.00.0',encoding='utf-8')
        (source/'server.py').write_text('# disposable code copy',encoding='utf-8')
        with patch.dict(os.environ,{'SOULBOUND_V109_STAGING':'1','SOULBOUND_V107_STAGING':'1'}):
            ck(not private_trial_allowed(source/'soulbound.db'),
               'Windows PREDEPLOY extracted source DB denied')
            ck(not private_trial_allowed(source/'arbitrary.sqlite'),
               'Windows PREDEPLOY extracted source alternate DB denied')
    # Szybki historyczny PREDEPLOY ma własny katalog sb104_tcp_lab_*
    # i nie może dostać niekontrolowanego dostępu do bazy produkcyjnej.
    with tempfile.TemporaryDirectory(prefix='sb104_tcp_lab_') as td:
        database=Path(td)/'tcp_test.sqlite'
        with patch.dict(os.environ,{'SOULBOUND_V109_STAGING':'1',
                                    'SOULBOUND_V107_STAGING':'1',
                                    'SOULBOUND_TCP_TEST_CHILD':'1',
                                    'SOULBOUND_HOST':'127.0.0.1',
                                    'SOULBOUND_PORT':'52088'}):
            ck(private_trial_allowed(database),'v104 private fast test DB permitted')
            ck(not private_trial_allowed(root/'soulbound.db'),'production DB denied during old fast audit')
            ck(not private_trial_allowed(Path(td)/'fake.sqlite'),'wrong fast DB filename denied')
            with patch.dict(os.environ,{'SOULBOUND_PORT':'4000'}):
                ck(not private_trial_allowed(database),'port 4000 denied even in fast audit')
            with patch.dict(os.environ,{'SOULBOUND_HOST':'0.0.0.0'}):
                ck(not private_trial_allowed(database),'remote listener denied for fast audit')
            with patch.dict(os.environ,{'SOULBOUND_TCP_TEST_CHILD':'0'}):
                ck(not private_trial_allowed(database),'missing fast test marker denied')
            link=Path(td)/'tcp_test-link.sqlite'
            try:
                link.symlink_to(database)
            except OSError:  # AUDIT_INTENTIONAL_PASS: expected exception in negative regression fixture
                pass
            else:
                ck(not private_trial_allowed(link),'symlinked DB denied in fast audit')
    # Original Windows PREDEPLOY 60 PLUS starts 4 import-server controls
    # on isolated snapshots. Only their exact TEMP directory/DB layouts pass.
    from systems.v10900_staging_guard import _official_predeploy_clone_allowed
    with tempfile.TemporaryDirectory(prefix='soulbound-predeploy-workers-') as td:
        worker=Path(td)/'candidate-0'
        worker.mkdir()
        # The file under test can itself live inside candidate-0 on Windows.
        # Never use its root as a "real installation" counterexample: that
        # is a valid PREDEPLOY worker by definition. Check a physical existing
        # non-worker source directory instead, even when the test is executed
        # from an official PREDEPLOY candidate.
        non_worker_root=Path(td)/'installed-game'
        non_worker_root.mkdir()
        env={'SOULBOUND_V108_PREDEPLOY':'1','SOULBOUND_HOST':'127.0.0.1',
             'SOULBOUND_PORT':'51987'}
        fixtures=(('sb-ultra-sqlite-migrate-','candidate.db'),
                  ('sb-ultimate-real-row-check-','isolated.sqlite'),
                  ('sb-ultimate60-clone-','candidate.sqlite'),
                  ('soulbound-catalog-test-','db.sqlite'))
        with patch.dict(os.environ,env):
            for prefix,filename in fixtures:
                with tempfile.TemporaryDirectory(prefix=prefix) as temp_dir:
                    valid=Path(temp_dir)/filename
                    ck(_official_predeploy_clone_allowed(valid,worker),
                       'Windows migration fixture allowed '+filename)
                    ck(not _official_predeploy_clone_allowed(Path(temp_dir)/'other.sqlite',worker),
                       'other database denied '+prefix)
                    with patch.dict(os.environ,{'SOULBOUND_PORT':'4000'}):
                        ck(not _official_predeploy_clone_allowed(valid,worker),
                           'prod port forbidden '+prefix)
                    with patch.dict(os.environ,{'SOULBOUND_HOST':'0.0.0.0'}):
                        ck(not _official_predeploy_clone_allowed(valid,worker),
                           'network listener forbidden '+prefix)
                    with patch.dict(os.environ,{'SOULBOUND_V108_PREDEPLOY':'0'}):
                        ck(not _official_predeploy_clone_allowed(valid,worker),
                           'no test authorization '+prefix)
                    ck(not _official_predeploy_clone_allowed(valid,non_worker_root),
                       'existing non-worker install folder forbidden '+prefix)
                    ck(not _official_predeploy_clone_allowed(root/'soulbound.db',worker),
                       'production DB forbidden '+prefix)
            fake=Path(td)/'candidate-other'
            fake.mkdir()
            ck(not _official_predeploy_clone_allowed(Path(td)/'candidate.db',fake),
               'incorrect worker source denied')
    source=(root/'server.py').read_text(encoding='utf-8')
    ck(source.index('ensure_authorized_start(')<source.index('_BOOT_SOCKET.bind'),
       'v109 check before port binding')
    code=(root/'server/mud_server.py').read_text(encoding='utf-8')
    ck('ensure_authorized_start(DB_PATH)' in code,'direct server construction guarded')
    ck((root/'VERSION').read_text().strip()=='109.00.0','source version exact')
    return n

if __name__=='__main__':
    print('V109 TEST ONLY BOOT GUARD:',run(),'PASS')
