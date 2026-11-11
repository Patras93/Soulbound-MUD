# -*- coding: utf-8 -*-
"""Narrow v110 staging whitelist for old FAST PREDEPLOY without live DB access."""
from __future__ import annotations
import os,sys,tempfile
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
from systems.v11000_activation import _test_database


def main():
    with tempfile.TemporaryDirectory(prefix='sb104_tcp_lab_') as temp:
        fixture=Path(temp)/'tcp_test.sqlite'
        base={'SOULBOUND_V110_STAGING':'1','SOULBOUND_V109_STAGING':'1',
              'SOULBOUND_V107_STAGING':'1','SOULBOUND_TCP_TEST_CHILD':'1',
              'SOULBOUND_HOST':'127.0.0.1','SOULBOUND_PORT':'45889'}
        with patch.dict(os.environ,base,clear=False):
            assert _test_database(fixture)
            assert not _test_database(Path(temp)/'soulbound.db')
            assert not _test_database(Path(temp)/'other.sqlite')
            assert not _test_database(Path(ROOT)/'soulbound.db')
            with patch.dict(os.environ,{'SOULBOUND_PORT':'4000'}):
                assert not _test_database(fixture)
            with patch.dict(os.environ,{'SOULBOUND_HOST':'0.0.0.0'}):
                assert not _test_database(fixture)
            with patch.dict(os.environ,{'SOULBOUND_TCP_TEST_CHILD':'0'}):
                assert not _test_database(fixture)
            with patch.dict(os.environ,{'SOULBOUND_V110_STAGING':'0'}):
                assert not _test_database(fixture)
        # No case may create or replace the real live database.
        assert not fixture.exists()
    # The Windows 60/60 harness creates these known, disposable test roots.
    # Keep the approval flags, loopback and non-production port mandatory.
    exact={
        'soulbound-tcp5-':'five_players.sqlite',
        'sb-ultra-5-tcp-':'stress.db',
        'sb-ultimate-tcp-waves-':'wave.sqlite',
        'sb-ultra-sqlite-migrate-':'candidate.db',
        'sb-ultimate-real-row-check-':'isolated.sqlite',
        'sb-ultimate60-clone-':'candidate.sqlite',
    }
    checked=9
    with patch.dict(os.environ,base,clear=False):
        for prefix,basename in exact.items():
            with tempfile.TemporaryDirectory(prefix=prefix) as folder:
                db=Path(folder)/basename
                assert _test_database(db), (prefix,basename)
                checked+=1
                assert not _test_database(Path(folder)/'unrelated.sqlite'),prefix
                checked+=1
                assert not _test_database(Path(folder)/'soulbound.db'),prefix
                checked+=1
        for prefix in ('sb110_predeploy_stage_','soulbound-coverage-','sb110_catalogue_'):
            with tempfile.TemporaryDirectory(prefix=prefix) as folder:
                db=Path(folder)/'coverage.sqlite'
                assert _test_database(db),prefix
                checked+=1
                with patch.dict(os.environ,{'SOULBOUND_V110_STAGING':'0'}):
                    assert not _test_database(db),prefix
                checked+=1
                with patch.dict(os.environ,{'SOULBOUND_PORT':'4000'}):
                    assert not _test_database(db),prefix
                checked+=1
    # v85's REAL native TCP check launches a SECOND disposable code copy.
    # It uses only TEMP/Soulbound_UOSS_REAL_*/gra/soulbound.db; the normal
    # production soulbound.db must remain denied everywhere else.
    from unittest.mock import patch as _patch
    from systems import v11000_activation as activation
    from arena_real_izolowana import _private_env
    with tempfile.TemporaryDirectory(prefix='Soulbound_UOSS_REAL_') as sandbox:
        clone=Path(sandbox)/'gra'
        clone.mkdir()
        (clone/'VERSION').write_text('110.00.0',encoding='utf-8')
        own_db=clone/'soulbound.db'
        with _patch.object(activation,'ROOT',clone):
            with patch.dict(os.environ,base,clear=False):
                assert _test_database(own_db), 'Approved synthetic UOSS clone denied'
                checked+=1
                assert not _test_database(clone/'other.db')
                checked+=1
                assert not _test_database(Path(sandbox)/'soulbound.db')
                checked+=1
                assert not _test_database(ROOT/'soulbound.db')
                checked+=1
                with patch.dict(os.environ,{'SOULBOUND_PORT':'4000'}):
                    assert not _test_database(own_db)
                checked+=1
                with patch.dict(os.environ,{'SOULBOUND_V110_STAGING':'0'}):
                    assert not _test_database(own_db)
                checked+=1
                with patch.dict(os.environ,{'SOULBOUND_HOST':'0.0.0.0'}):
                    assert not _test_database(own_db)
                checked+=1
                with patch.dict(os.environ,{'SOULBOUND_CONTROL_TOKEN':'secret'}):
                    clean=_private_env(clone,58031)
                assert all(clean.get(k)=='1' for k in
                    ('SOULBOUND_V107_STAGING','SOULBOUND_V109_STAGING','SOULBOUND_V110_STAGING'))
                checked+=1
                assert 'SOULBOUND_CONTROL_TOKEN' not in clean
                checked+=1
                with patch.dict(os.environ,{'SOULBOUND_V109_STAGING':'0'}):
                    clean=_private_env(clone,58031)
                assert not any(k in clean for k in
                    ('SOULBOUND_V107_STAGING','SOULBOUND_V109_STAGING','SOULBOUND_V110_STAGING'))
                checked+=1
        # A regular game source cannot impersonate the UOSS copy, even if
        # all three staging flags are present in a synthetic test environment.
        with patch.dict(os.environ,base,clear=False):
            assert not _test_database(own_db)
            checked+=1
    # Regression for the real Windows scheduling bug: the five-player
    # kill-and-quest gate must start AFTER the CPU-heavy full audit ends.
    # Exercise the actual dispatcher on three tiny files, not a source grep.
    import testuj_soulbound_windows as harness
    with tempfile.TemporaryDirectory(prefix='sb110_ordering_') as folder:
        scratch=Path(folder)
        src=scratch/'source'
        src.mkdir()
        (src/'VERSION').write_text('110.00.0',encoding='utf-8')
        marker=scratch/'full_audit_complete.txt'
        (src/'toy_full.py').write_text(
            'from pathlib import Path\nimport time\ntime.sleep(0.5)\n'
            +f'Path({str(marker)!r}).write_text("complete")\n',encoding='utf-8')
        (src/'toy_short.py').write_text('pass\n',encoding='utf-8')
        (src/'toy_tcp.py').write_text(
            f'from pathlib import Path\nassert Path({str(marker)!r}).read_text()=="complete"\n',
            encoding='utf-8')
        outputs=[]
        with patch.object(harness,'ROOT',src):
            summary=harness.run_parallel_stages((
                ('PELNY AUDYT','toy_full.py',10),
                ('KROTKA KONTROLA','toy_short.py',10),
                ('5 KLIENTOW TCP + RESTART','toy_tcp.py',10),
            ),outputs.append,max_workers=3)
        assert len(summary)==3 and all(code==0 for _,code in summary)
        checked+=1
        audit_finish=next(i for i,m in enumerate(outputs) if 'KONIEC: PELNY AUDYT' in m)
        tcp_start=next(i for i,m in enumerate(outputs) if 'START: ETAP 3/3: 5 KLIENTOW TCP' in m)
        assert audit_finish < tcp_start
        checked+=1
        assert marker.read_text(encoding='utf-8')=='complete'
        checked+=1
    print(f'V110 WINDOWS PREDEPLOY ISOLATION: {checked}/{checked} PASS; '
          'known scratch DBs only, no production port or approval bypass',flush=True)

if __name__=='__main__':main()
