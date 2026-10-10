# -*- coding: utf-8 -*-
"""Windows launcher PID liveness checks; never terminates processes."""
from __future__ import annotations

import os
import time


def process_alive(pid: int) -> bool:
    if not isinstance(pid, int) or pid <= 0:
        return False
    if os.name == 'nt':
        import ctypes
        from ctypes import wintypes
        dll = ctypes.WinDLL('kernel32', use_last_error=True)
        dll.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        dll.OpenProcess.restype = wintypes.HANDLE
        dll.WaitForSingleObject.argtypes = [wintypes.HANDLE, wintypes.DWORD]
        dll.WaitForSingleObject.restype = wintypes.DWORD
        dll.CloseHandle.argtypes = [wintypes.HANDLE]
        dll.CloseHandle.restype = wintypes.BOOL
        handle = dll.OpenProcess(0x00100000, False, pid)  # SYNCHRONIZE
        if not handle:
            # Unknown/access denied means not safe to assume exited.
            return ctypes.get_last_error() != 87  # ERROR_INVALID_PARAMETER: PID gone
        try:
            return dll.WaitForSingleObject(handle, 0) != 0  # WAIT_OBJECT_0: exited
        finally:
            dll.CloseHandle(handle)
    try:
        os.kill(pid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:
        return True


def wait_gone(pid: int, timeout: float = 15.0) -> bool:
    deadline = time.monotonic() + timeout
    while process_alive(pid) and time.monotonic() < deadline:
        time.sleep(.1)
    return not process_alive(pid)
