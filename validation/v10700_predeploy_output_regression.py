# -*- coding: utf-8 -*-
"""Windows PREDEPLOY: direct parent PID must not wait for descendant stdout.

The grandchild must be reaped before its temporary workspace is deleted.
"""
from __future__ import annotations

import os
from pathlib import Path
import sys
import tempfile
import time


def wait_for_child_exit(pid: int, *, timeout_ms: int = 8000) -> bool:
    """Wait for one exact owned child PID on Windows, without touching the game."""
    if os.name != 'nt':
        return True  # A completion sentinel is checked separately on POSIX.
    import ctypes
    from ctypes import wintypes
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
    kernel.WaitForSingleObject.restype = wintypes.DWORD
    kernel.CloseHandle.argtypes = [wintypes.HANDLE]
    kernel.CloseHandle.restype = wintypes.BOOL
    # The process may have exited before we can obtain its handle.
    handle = kernel.OpenProcess(0x00100000, False, pid)  # SYNCHRONIZE only
    if not handle:
        return True
    try:
        return kernel.WaitForSingleObject(handle, timeout_ms) == 0
    finally:
        kernel.CloseHandle(handle)


def run() -> int:
    import testuj_soulbound_windows as gate
    checks = 0
    with tempfile.TemporaryDirectory(prefix='sb107_output_contract_') as td:
        home = Path(td)
        sentinel = home / 'done.flag'
        completed = home / 'child.done'
        pid_file = home / 'child.pid'
        child_code = (
            "import pathlib,time\n"
            f"p=pathlib.Path({str(sentinel)!r})\n"
            "end=time.monotonic()+20\n"
            "while not p.exists() and time.monotonic()<end: time.sleep(.05)\n"
            "p.with_name('child.done').write_text('ok',encoding='utf-8')\n"
        )
        parent_code = (
            "import pathlib,subprocess,sys,tempfile\n"
            f"p=subprocess.Popen([sys.executable,'-c',{child_code!r}], "
            # An orphaned child holding cwd=home prevents rmtree() on Windows.
            "stdout=sys.stdout,stderr=sys.stderr,stdin=subprocess.DEVNULL,"
            "cwd=tempfile.gettempdir())\n"
            f"pathlib.Path({str(pid_file)!r}).write_text(str(p.pid),encoding='utf-8')\n"
            "print('GATE-PARENT-EXITED',flush=True)\n"
        )
        (home / 'parent.py').write_text(parent_code, encoding='utf-8')
        lines: list[str] = []
        began = time.monotonic()
        try:
            code = gate.run_stage('parent.py', os.environ.copy(), 8,
                                  lines.append, root=home)
        finally:
            # Release the child even on error, then wait before deleting TEMP.
            sentinel.write_text('stop', encoding='utf-8')
            cutoff = time.monotonic() + 10
            while not completed.is_file() and time.monotonic() < cutoff:
                time.sleep(.05)
            assert completed.is_file(), 'Proces potomny nie zakonczyl testu.'
            assert pid_file.is_file(), 'Brak PID procesu potomnego.'
            assert wait_for_child_exit(int(pid_file.read_text(encoding='utf-8'))), (
                'Proces potomny nie zwolnil zasobow Windows.')
        elapsed = time.monotonic() - began
        assert code == 0, f'Gate waited on descendant stdout: code={code}, lines={lines[-5:]}'
        checks += 1
        assert elapsed < 8, elapsed
        checks += 1
        assert any('GATE-PARENT-EXITED' in line for line in lines), lines
        checks += 1
        assert completed.is_file(), 'Brak potwierdzenia konca procesu'
        checks += 1
    # The temporary directory must be removable on Windows without WinError 32.
    return checks


if __name__ == '__main__':
    print(f'V107 PREDEPLOY OUTPUT PID: {run()} checks PASS', flush=True)
