# -*- coding: utf-8 -*-
"""Fast isolated v112 regression: concurrent workers, failure and TCP ordering."""
from __future__ import annotations
import sys
import tempfile
import threading
import time
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:sys.path.insert(0,str(ROOT))
import testuj_soulbound_windows as tested


def run():
    checks=0
    assert 1 <= tested.PARALLEL_WORKERS <= 4;checks+=1
    with tempfile.TemporaryDirectory(prefix='sb112_parallel_contract_') as td:
        root=Path(td)/'candidate';root.mkdir()
        (root/'VERSION').write_text('112.00.0\n',encoding='utf-8')
        for script in ('fast.py','heavy.py','tcp.py'):
            (root/script).write_text('pass\n',encoding='utf-8')
        events=[]
        lock=threading.Lock()
        def run_one(script,env,deadline,output,root):
            started=time.monotonic()
            with lock:events.append(('start',script,started,str(root)))
            time.sleep(0.11)
            output('STAGE '+script)
            with lock:events.append(('end',script,time.monotonic(),str(root)))
            return 2 if script=='heavy.py' else 0
        msgs=[]
        cases=(('A','fast.py',60),('B','heavy.py',60),('C','tcp.py',60))
        with (patch.object(tested,'ROOT',root),
              patch.object(tested,'stage_env',return_value={}),
              patch.object(tested,'run_stage',side_effect=run_one)):
            results=tested.run_parallel_stages(cases,msgs.append,phase='V112',max_workers=3)
            assert [name for name,_ in results]==['A','B','C'];checks+=1
            assert [code for _,code in results]==[0,2,0];checks+=1
            starts=[e for e in events if e[0]=='start']
            ends=[e for e in events if e[0]=='end']
            assert len(starts)==3 and len(ends)==3;checks+=1
            assert max(e[2] for e in starts)<min(e[2] for e in ends);checks+=1
            assert len({e[3] for e in starts})==3;checks+=1
            assert sum('KONIEC:' in line for line in msgs)==3;checks+=1
            events.clear()
            order=(('PELNY AUDYT','heavy.py',60),
                   ('5 KLIENTOW TCP + RESTART','tcp.py',60),
                   ('KRÓTKI TEST','fast.py',60))
            results=tested.run_parallel_stages(order,msgs.append,phase='ETAP',max_workers=1)
            assert [name for name,_ in results]==[x[0] for x in order];checks+=1
            assert [e[1] for e in events if e[0]=='start']==['heavy.py','fast.py','tcp.py'];checks+=1
    print(f'V112 PREDEPLOY RÓWNOLEGŁY: {checks}/9 PASS')

if __name__=='__main__':run()
