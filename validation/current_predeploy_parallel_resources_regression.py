# -*- coding: utf-8 -*-
"""Current parallel PREDEPLOY: CPU/RAM policy and eight isolated candidates."""
from __future__ import annotations
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch
import os
import sys
import ast
import threading
import time

ROOT=Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))
import testuj_soulbound_windows as harness


def check_no_swallowed_handlers(path):
    """Use the identical empty-except AST rule as the historical full audit."""
    source=Path(path).read_text(encoding='utf-8')
    lines=source.splitlines()
    tree=ast.parse(source,filename=str(path))
    bad=[]
    for node in ast.walk(tree):
        if isinstance(node,ast.ExceptHandler) and len(node.body)==1 and isinstance(node.body[0],ast.Pass):
            line=lines[node.lineno-1]
            if 'AUDIT_INTENTIONAL_PASS' not in line:
                bad.append(node.lineno)
    if bad:
        raise AssertionError(f'Nieklasyfikowane puste except: {path}:{bad}')
    return True


def run():
    checks=0
    M=1024*1024
    assert harness.MAX_PARALLEL_WORKERS == 8; checks+=1
    # 16 logical cores and enough free RAM => 8 real isolated processes.
    assert harness.recommended_predeploy_workers(16, 12*1024*M)==8; checks+=1
    assert harness.recommended_predeploy_workers(8, 12*1024*M)==4; checks+=1
    assert harness.recommended_predeploy_workers(4, 12*1024*M)==2; checks+=1
    assert harness.recommended_predeploy_workers(2, 12*1024*M)==1; checks+=1
    assert harness.recommended_predeploy_workers(16, 3*1024*M)==1; checks+=1
    assert harness.recommended_predeploy_workers(16, 5*1024*M)==4; checks+=1
    assert harness.recommended_predeploy_workers(16, 7*1024*M)==6; checks+=1
    # A missing memory reading must not launch eight heavy processes.
    with patch.object(harness,'available_predeploy_memory_bytes',return_value=None):
        assert harness.recommended_predeploy_workers(16)==4; checks+=1
    assert 1 <= harness.PARALLEL_WORKERS <= 8; checks+=1
    assert len(harness.STAGES)==60; checks+=1
    # Both platform branches must be selected by sys.platform, not by the
    # host os.name; the latter stays 'nt' in this Linux simulation on Windows.
    import ctypes
    from types import SimpleNamespace
    class FakeKernel32:
        def GlobalMemoryStatusEx(self, byref_status):
            status=byref_status._obj
            assert status.dwLength==ctypes.sizeof(status)
            status.ullAvailPhys=8*1024**3
            return 1
    with patch.object(harness.sys, 'platform', 'win32'):
        with patch.object(ctypes, 'windll', create=True,
                          new=SimpleNamespace(kernel32=FakeKernel32())):
            assert harness.available_predeploy_memory_bytes()==8*1024**3; checks+=1
    # Simulate missing/unreadable/invalid Linux cgroup without relying on
    # the host OS, and require safe behavior when available RAM is unknown.
    import io
    real_open = open
    def fake_open(path, *args, **kwargs):
        if str(path) == '/proc/meminfo':
            return io.StringIO('MemAvailable: 12582912 kB\n')
        return real_open(path, *args, **kwargs)
    with patch.object(harness.sys, 'platform', 'linux'):
        with patch('builtins.open', side_effect=fake_open):
            with patch.object(Path, 'read_text', side_effect=PermissionError('cgroup inaccessible')):
                assert harness.available_predeploy_memory_bytes() is None; checks+=1
            with patch.object(Path, 'read_text', side_effect=FileNotFoundError('cgroup v1')):
                assert harness.available_predeploy_memory_bytes()==12*1024**3; checks+=1
            with patch.object(Path, 'read_text', return_value='max'):
                assert harness.available_predeploy_memory_bytes()==12*1024**3; checks+=1
            with patch.object(Path, 'read_text', side_effect=['99999999', 'garbled']):
                assert harness.available_predeploy_memory_bytes() is None; checks+=1
    assert check_no_swallowed_handlers(ROOT / 'testuj_soulbound_windows.py'); checks+=1
    with TemporaryDirectory(prefix='sb11319_parallel_8_') as td:
        source=Path(td)/'source';source.mkdir()
        (source/'VERSION').write_text('113.00.19\n',encoding='utf-8')
        cases=[]
        for i in range(8):
            name=f'test_{i}.py'
            (source/name).write_text('pass\n',encoding='utf-8')
            cases.append((f'TEST {i}',name,10))
        barrier=threading.Barrier(8,timeout=10)
        active=set(); seen=[]; lock=threading.Lock()
        def simulated_stage(script,env,deadline,say,*,root,stop_event=None):
            # This is a concurrency/ownership test, not the long 60/60 suite.
            with lock:
                active.add(str(root));seen.append((script,str(root)))
            barrier.wait()
            say('SIMULATED PASS '+script)
            with lock:
                assert len(active)==8
            return 0
        messages=[]
        with (patch.object(harness,'ROOT',source),
              patch.object(harness,'stage_env',return_value={}),
              patch.object(harness,'run_stage',side_effect=simulated_stage)):
            outcome=harness.run_parallel_stages(cases,messages.append,
                                                phase='CURRENT',max_workers=8)
        assert len(outcome)==8 and all(code==0 for _,code in outcome);checks+=1
        assert len(seen)==8 and len(set(root for _,root in seen))==8;checks+=1
        assert sum('KONIEC:' in line for line in messages)==8;checks+=1
    print(f'PREDEPLOY CPU/RAM + 8 IZOLOWANYCH KOPII: {checks}/{checks} PASS',flush=True)
    return checks


if __name__=='__main__':run()
