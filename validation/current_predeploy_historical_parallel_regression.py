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
    # The real auditors must register ALL known isolated historical child
    # gates and call the strict batch exactly once, not just pass a mock test.
    import ast
    for filename, minimum in (('predeploy_check.py', 26), ('predeploy_full.py', 36)):
        tree=ast.parse((ROOT / filename).read_text(encoding='utf-8'))
        queued=[n for n in ast.walk(tree) if isinstance(n, ast.Call)
                and isinstance(n.func, ast.Attribute)
                and isinstance(n.func.value, ast.Name)
                and n.func.value.id=='_sb_parallel_historical' and n.func.attr=='add']
        ran=[n for n in ast.walk(tree) if isinstance(n, ast.Call)
             and isinstance(n.func, ast.Attribute)
             and isinstance(n.func.value, ast.Name)
             and n.func.value.id=='_sb_parallel_historical' and n.func.attr=='run']
        assert len(queued)>=minimum and len(ran)==1, (filename, len(queued), len(ran))
        methods=[n for n in ast.walk(tree) if isinstance(n,ast.Call)
                 and isinstance(n.func,ast.Name)
                 and n.func.id=='_sb_private_historical_run']
        assert len(methods)>=minimum, (filename,'missing isolated child environment')
        count+=1
    print(f'HISTORICAL PREDEPLOY ISOLATION: {count}/{count} PASS')
    return count

if __name__=='__main__': run_regression()
