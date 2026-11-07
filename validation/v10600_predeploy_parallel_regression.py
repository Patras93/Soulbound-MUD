# -*- coding: utf-8 -*-
"""Guardrails for concurrent but fully isolated Windows PREDEPLOY execution."""
from __future__ import annotations
from pathlib import Path
import tempfile
import threading
from unittest.mock import patch

import testuj_soulbound_windows as gate


def run_regression():
    checks = 0
    with tempfile.TemporaryDirectory(prefix='sb-fast-predeploy-guard-') as td:
        root = Path(td)/'candidate'
        root.mkdir()
        (root/'sample.py').write_text("print('PASS')\n", encoding='utf-8')
        seen = []
        messages = []
        lock = threading.Lock()

        def fake_stage(script, env, deadline, say, *, root):
            nonlocal checks
            assert (root/'sample.py').read_text('utf-8').strip() == "print('PASS')"
            assert Path(env['SOULBOUND_DB']).parent.exists()
            assert env['SOULBOUND_HOST'] == '127.0.0.1'
            assert 1 <= int(env['SOULBOUND_PORT']) <= 65535
            with lock:
                seen.append((script, str(root), env['SOULBOUND_DB'],
                             env.get('SOULBOUND_V106_STAGING')))
                checks += 4
            say('PLUS CHECKS PASS')
            return 7 if script.startswith('sample.py --case bad') else 0

        items = tuple((f'test {i}', f'sample.py --case {i}', 5) for i in range(7))
        with patch.object(gate, 'ROOT', root), patch.object(gate, 'run_stage', fake_stage):
            res = gate.run_parallel_stages(items, messages.append, max_workers=3)
            assert len(res)==7 and all(code==0 for _,code in res)
            checks += 1
            assert {name for name, *_ in seen} == {script for _,script,_ in items}
            checks += 1
            assert len({row[2] for row in seen})==7
            checks += 1
            assert 1<=len({row[1] for row in seen})<=3
            checks += 1
            assert sum('PLUS CHECKS PASS' in s for s in messages)==7
            checks += 1
            bad = gate.run_parallel_stages((('negative','sample.py --case bad',5),),
                                           messages.append,max_workers=3)
            assert bad == [('negative',7)]
            checks += 1
            one = gate.run_parallel_stages((('V106 live','sample.py --case good',5),
                                            ('V106 EQ NA KOPII','sample.py --case copy',5)),
                                           messages.append,max_workers=2,staging_v106=True)
            assert len(one)==2 and all(code==0 for _,code in one)
            last = seen[-2:]
            assert [v[3] for v in last if 'good' in v[0]]==['1']
            assert [v[3] for v in last if 'copy' in v[0]]==[None]
            checks += 3
            missing = gate.run_parallel_stages((('brak','missing.py',5),), messages.append, max_workers=1)
            assert missing == [('brak',2)]
            checks += 1
            assert not list(root.glob('*.sqlite'))
            checks += 1
    print(f'V106 OPTYMALIZACJA PREDEPLOY: {checks} kontroli PASS; fail-closed i 3 izolacje', flush=True)
    return checks

if __name__=='__main__':
    run_regression()
