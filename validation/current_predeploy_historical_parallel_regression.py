# -*- coding: utf-8 -*-
"""Synthetic proof: historical PREDEPLOY keeps every mandatory isolated gate."""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import sys
from threading import Lock
from time import sleep
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0,str(ROOT))
from validation.current_predeploy_historical_parallel import (
    HistoricalGateBatch, private_historical_subprocess_run,
)


def run_regression():
    count=0
    lock=Lock()
    active=0
    maximum=0
    received=[]
    def gate(number):
        nonlocal active,maximum
        with lock:
            active+=1
            maximum=max(maximum,active)
        sleep(0.035)
        with lock:
            active-=1
        return number
    batch=HistoricalGateBatch(max_workers=2)
    for number in range(5):
        batch.add(lambda i=number: gate(i),lambda result:received.append(result))
    assert batch.run()==5
    count+=1
    assert received==[0,1,2,3,4]
    count+=1
    assert maximum==2
    count+=1
    try: batch.run()
    except RuntimeError: count+=1
    else: raise AssertionError('Batch repeated tests')
    failed=HistoricalGateBatch(max_workers=2)
    completed=[]
    for number in range(4):
        def check(i=number):
            if i==3: raise AssertionError('simulated historical FAIL')
            return i
        failed.add(check, lambda result:completed.append(result))
    try: failed.run()
    except AssertionError as exc:
        assert '4/4' in str(exc) and 'simulated historical FAIL' in str(exc)
        count+=1
    else: raise AssertionError('Historical FAIL was hidden')
    assert not completed, 'Failing batch must never report overall PASS'
    count+=1
    # Validate the exact runtime settings passed to child without launching it.
    from subprocess import CompletedProcess
    calls=[]
    def fake_run(argv, **kwargs):
        calls.append((tuple(argv),dict(kwargs)))
        env=kwargs['env']
        assert env['SOULBOUND_HOST']=='127.0.0.1'
        assert env['SOULBOUND_PORT']!='4000'
        assert env['SOULBOUND_DB'].endswith('tcp_test.sqlite')
        assert env['SOULBOUND_UNIVERSAL_STAGING']=='1'
        assert 'SOULBOUND_ULTRA_SOURCE_DB' not in env
        assert Path(env['SOULBOUND_DB']).parent.is_dir()
        return CompletedProcess(argv,0,'OK','')
    with patch('validation.current_predeploy_historical_parallel.subprocess.run',fake_run), patch.dict('os.environ',{'SOULBOUND_ULTRA_SOURCE_DB':'C:/production/soulbound.db'}):
        r=private_historical_subprocess_run([sys.executable,'-c','pass'],capture_output=True,text=True)
        assert r.returncode==0
    assert calls and not Path(calls[0][1]['env']['SOULBOUND_DB']).parent.exists()
    count+=1
    # Optional FULL mode must be retained, never accidentally made production.
    with patch('validation.current_predeploy_historical_parallel.subprocess.run',fake_run), patch.dict('os.environ',{'SOULBOUND_FULL_AUDIT':'1'}):
        private_historical_subprocess_run([sys.executable,'-c','pass'])
    assert calls[-1][1]['env']['SOULBOUND_FULL_AUDIT']=='1'
    count+=1
    # v114: historical retired runtime editor checks are retired, NOT passed by a
    # fake historical callback. The replacement code must enumerate the real
    # current gameplay suites and retain their mandatory subprocess exit codes.
    for filename, expected in (
        ('predeploy_check.py', ('validation.v11400_soul_infinite_regression',
                                'validation.current_published_readonly_regression')),
        ('predeploy_full.py', ('validation/current_only_server_smoke.py',
                               'validation/current_jammer_cast_regression.py')),
    ):
        content=(ROOT/filename).read_text(encoding='utf-8')
        import ast
        tree=ast.parse(content)
        assert '_sb_parallel_historical' not in content, filename
        assert 'returncode' in content and 'raise AssertionError' in content, filename
        assert all(name in content for name in expected), filename
        assert any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute)
                   and n.func.attr=='run' for n in ast.walk(tree)), filename
        count+=1
    print(f'HISTORICAL PREDEPLOY ISOLATION: {count}/{count} PASS')
    return count

if __name__=='__main__': run_regression()
