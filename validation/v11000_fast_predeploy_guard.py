# -*- coding: utf-8 -*-
"""Wlacz testowy tryb v110 tylko po utworzeniu izolowanego labu v104.

Nigdy nie umozliwia dostepu do produkcyjnej bazy ani portu 4000.
"""
from __future__ import annotations
import os
from pathlib import Path


def authorize_private_lab(lab, port):
    from systems.v11000_activation import _test_database
    root = Path(lab).resolve(strict=True)
    expected_db = root / 'tcp_test.sqlite'
    if (not root.name.startswith('sb104_tcp_lab_') or not root.is_dir()
        or str(Path(os.environ.get('SOULBOUND_DB','')).resolve()) != str(expected_db)
        or os.environ.get('SOULBOUND_HOST')!='127.0.0.1'
        or os.environ.get('SOULBOUND_TCP_TEST_CHILD')!='1'
        or int(os.environ.get('SOULBOUND_PORT','0')) != port
        or not 1025 <= port <= 65535 or port == 4000
        or expected_db.is_symlink()):
        raise PermissionError('v110: szybki PREDEPLOY wymaga odizolowanego localhost labu')
    # Explicitly required by the production authorization guard. Flags alone
    # cannot authorize a live DB, another filename or production TCP port.
    os.environ.update(SOULBOUND_V107_STAGING='1',
        SOULBOUND_V109_STAGING='1', SOULBOUND_V110_STAGING='1')
    if not _test_database(expected_db):
        raise PermissionError('v110: odmowa autoryzacji bazy testowej')
    return True
