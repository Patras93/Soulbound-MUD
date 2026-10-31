# -*- coding: utf-8 -*-
"""Isolate the legacy FAST PREDEPLOY before ANY gameplay import.

Some old audit modules import server.py as a side effect, which binds an
actual TCP listener immediately.  Never let this happen on the deployment
port or with the player's database.  This applies only to a direct invocation
of predeploy_check.py, never to normal game startup.
"""
from __future__ import annotations
import os
from pathlib import Path
import socket
import tempfile
from validation.v10400_release_isolation_guard import private_tcp_environment


def isolated_predeploy_env(source, folder: str, port: int) -> dict[str, str]:
    return private_tcp_environment(source, folder, port)


def enable_isolated_fast_predeploy():
    lab = tempfile.TemporaryDirectory(prefix='sb104_tcp_lab_')
    try:
        # Socket reservation while discovering a non-production ephemeral port.
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(('127.0.0.1', 0))
            port = sock.getsockname()[1]
        if port == 4000:
            raise RuntimeError('TCP PREDEPLOY: losowy port 4000 jest zabroniony.')
        env = isolated_predeploy_env(dict(os.environ), lab.name, port)
        db = Path(env['SOULBOUND_DB'])
        if db.exists():
            raise FileExistsError('TCP PREDEPLOY: testowa baza juz istnieje.')
        os.environ.clear()
        os.environ.update(env)
        return lab, port
    except BaseException:
        lab.cleanup()
        raise
