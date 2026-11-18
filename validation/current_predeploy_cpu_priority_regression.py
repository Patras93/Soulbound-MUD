# -*- coding: utf-8 -*-
"""Verify faster PREDEPLOY parallel scheduling; no gates skipped, no real DB."""
from __future__ import annotations
import sys
from io import StringIO
from contextlib import redirect_stdout
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Lock
import time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def run_regression():
    import testuj_soulbound_windows as runner
    checks = 0
    with TemporaryDirectory(prefix='sb-predeploy-cpu-proof-') as directory:
        source = Path(directory) / 'source'
        source.mkdir()
        (source / 'VERSION').write_text('113.00.30', encoding='utf-8')
        (source / 'gate.py').write_text('pass\n', encoding='utf-8')
        gates = [
            ('SZYBKI PREDEPLOY', 'gate.py', 4),
            ('PELNY AUDYT', 'gate.py', 4),
            *[(f'SYNTETYCZNA BRAMKA {i}', 'gate.py', 4) for i in range(12)],
        ]
        lock = Lock()
        running_short = 0
        max_during_heavy = 0
        completed_audits = set()
        called = []
        def fake_stage(script, env, deadline, say, *, root=None, stop_event=None):
            nonlocal running_short, max_during_heavy
            # Identify the test process using worker-specific immutable root;
            # mandatory audits are launched first, without stalling other gates.
            with lock:
                index = len(called)
                called.append(index)
                if index >= 2:
                    running_short += 1
                    if len(completed_audits) < 2:
                        max_during_heavy = max(max_during_heavy, running_short)
            if index < 2:
                time.sleep(0.27)
            else:
                time.sleep(0.04)
            with lock:
                if index < 2:
                    completed_audits.add(index)
                else:
                    running_short -= 1
            return 0
        # These first two gates model concurrent full/quick audits.
        with patch.object(runner, 'ROOT', source), patch.object(runner, 'run_stage', fake_stage):
            results = runner.run_parallel_stages(gates, lambda text: None, max_workers=8)
        assert len(results) == len(gates) and all(code == 0 for _, code in results)
        checks += 1
        assert len(called) == len(gates), 'Every gate should execute precisely once'
        checks += 1
        assert max_during_heavy >= 3, ('other independent gates were needlessly throttled', max_during_heavy)
        checks += 1
        assert len(completed_audits) == 2
        checks += 1
        # Simulate release proof without launching a live server or accessing
        # the real player database. Both the successful and failed fifth gate
        # must retain their exact identity and fail-closed outcome.
        for failing in (None, 'SZESC GRACZY TCP, QUESTY I RESTART'):
            recorded=[]
            def fake_run_batch(stages, say, **kwargs):
                recorded.append(tuple(name for name, _, _ in stages))
                if len(stages)==65:
                    say('PLUS CHECKS PASS')
                return [(name, int(name==failing)) for name,_,_ in stages]
            fake_env={'SOULBOUND_ULTRA_SOURCE_DB':str(source/'db-test.sqlite')}
            (source/'db-test.sqlite').write_bytes(b'isolated fake, never used')
            with patch.object(runner, 'ROOT', source), \
                 patch.object(runner, 'LOG', source/'test_log.txt'), \
                 patch.object(runner, 'source_db_for_gate', lambda:source/'db-test.sqlite'), \
                 patch.object(runner, 'stage_env', lambda scratch:fake_env), \
                 patch.object(runner, 'run_stage', lambda *args,**kw:0), \
                 patch.object(runner, 'run_parallel_stages',fake_run_batch):
                with redirect_stdout(StringIO()):
                    result=runner.main()
            assert result==(0 if failing is None else 1), ('release proof not fail-closed', failing, result)
            assert len(recorded)==1 and len(recorded[0])==65
            assert recorded[0][:60]==tuple(name for name,_,_ in runner.STAGES)
            assert recorded[0][-1]=='SZESC GRACZY TCP, QUESTY I RESTART' 
            checks+=1
    # Regression for the old 24-minute full-audit -> TCP scheduling barrier.
    # Synthetic source and mocked process launch: never opens ports or touches
    # a real database. The 5-client stage MUST finish while FULL is still busy.
    with TemporaryDirectory(prefix='sb-predeploy-tcp-overlap-') as directory:
        source = Path(directory) / 'source'
        source.mkdir()
        (source / 'VERSION').write_text('113.00.34', encoding='utf-8')
        for filename in ('fast.py', 'full.py', 'short.py', 'tcp.py'):
            (source / filename).write_text('pass\n', encoding='utf-8')
        gates = [
            ('SZYBKI PREDEPLOY', 'fast.py', 4),
            ('PELNY AUDYT', 'full.py', 4),
            *[(f'KONTROLA {i}', 'short.py', 4) for i in range(10)],
            ('5 KLIENTOW TCP + RESTART', 'tcp.py', 4),
        ]
        audit_finished = set()
        tcp_was_parallel = []
        def simulate_stage(script, env, deadline, say, *, root=None, stop_event=None):
            if script == 'full.py':
                time.sleep(0.30)
                audit_finished.add('full')
            elif script == 'fast.py':
                time.sleep(0.30)
                audit_finished.add('fast')
            elif script == 'tcp.py':
                tcp_was_parallel.append('full' not in audit_finished)
            else:
                time.sleep(0.012)
            return 0
        with patch.object(runner, 'ROOT', source), patch.object(runner, 'run_stage', simulate_stage):
            results = runner.run_parallel_stages(gates, lambda text: None, max_workers=4)
        assert len(results) == len(gates) and all(code == 0 for _, code in results)
        checks += 1
        assert tcp_was_parallel == [True], 'TCP improperly waited for completion of full audit'
        checks += 1
        # A failing 5-client gate cannot be hidden behind both passing audits.
        def fail_tcp(script, env, deadline, say, *, root=None, stop_event=None):
            if script == 'full.py':
                time.sleep(0.15)
            return 7 if script == 'tcp.py' else 0
        with patch.object(runner, 'ROOT', source), patch.object(runner, 'run_stage', fail_tcp):
            failed = runner.run_parallel_stages(gates, lambda text: None, max_workers=4)
        assert len(failed) == len(gates) and dict(failed)['5 KLIENTOW TCP + RESTART'] == 7
        assert any(code != 0 for _, code in failed), 'TCP FAIL hidden'
        checks += 1
    print(f'PREDEPLOY PARALLEL THROUGHPUT: {checks}/{checks} PASS')
    return checks

if __name__ == '__main__':
    run_regression()
