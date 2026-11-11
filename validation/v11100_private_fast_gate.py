# -*- coding: utf-8 -*-
"""v111: private FAST PREDEPLOY environment, never production authorization."""
from __future__ import annotations
import os
from pathlib import Path


def authorize_private_lab(lab, port):
    from systems.v11100_holiday_activation import _test_database
    if type(port) is not int or not 1025 <= port <= 65535 or port == 4000:
        raise PermissionError('v111 FAST: niedozwolony port testowy')
    root=Path(lab).resolve(strict=True)
    expected_db=root/'tcp_test.sqlite'
    try:
        actual_db=Path(os.environ.get('SOULBOUND_DB','')).resolve()
        env_port=int(os.environ.get('SOULBOUND_PORT',''))
    except (OSError,ValueError,TypeError):
        raise PermissionError('v111 FAST: nieprawidlowa baza lub port testowy') from None
    if (not root.is_dir() or not root.name.startswith('sb104_tcp_lab_')
        or actual_db!=expected_db or expected_db.is_symlink()
        or os.environ.get('SOULBOUND_HOST')!='127.0.0.1'
        or os.environ.get('SOULBOUND_TCP_TEST_CHILD')!='1'
        or env_port!=port or os.environ.get('PORT')!=str(port)):
        raise PermissionError('v111 FAST: wymagany odizolowany localhost i prywatna baza')
    # The active current authorization demands all inherited compatibility
    # flags; only this already-isolated lab may set them. Flags by themselves
    # cannot ever enable a live database or the production listener.
    os.environ.update(SOULBOUND_V107_STAGING='1',SOULBOUND_V109_STAGING='1',
                      SOULBOUND_V110_STAGING='1',SOULBOUND_V111_STAGING='1')
    if (Path(__file__).resolve().parents[1]/'VERSION').read_text(encoding='utf-8-sig').strip() == '112.00.0':
        os.environ['SOULBOUND_V112_STAGING']='1'
    if not _test_database(expected_db):
        raise PermissionError('v111 FAST: testowa baza odrzucona przez aktualna aktywacje')
    return True


# Active v111 FAST/FULL isolation. Keep it here rather than importing a
# historical v104 test runner (which may be removed from a modern candidate).
# Strip any inherited live credentials, paths and listener settings before
# importing storage, server, or historical test modules.
import socket
import tempfile

_DROP_LIVE_ENV_V111 = frozenset({
    'PORT', 'RAILWAY_TCP_APPLICATION_PORT', 'SOULBOUND_PORT',
    'SOULBOUND_HOST', 'SOULBOUND_DB', 'DATABASE_URL',
    'RAILWAY_VOLUME_MOUNT_PATH', 'SOULBOUND_WORLD_SEED_FILE',
    'SOULBOUND_WORLD_SEED', 'SOULBOUND_CONTROL_FILE',
    'SOULBOUND_CONTROL_TOKEN', 'SOULBOUND_ADMIN_ACCOUNTS',
    'SOULBOUND_FULL_AUDIT', 'SOULBOUND_HISTORICAL_AUDITS',
    'SOULBOUND_ULTRA_SOURCE_DB',
    'SOULBOUND_SMTP_PASSWORD', 'SOULBOUND_MAIL_PASSWORD',
    'SMTP_PASSWORD', 'SOULBOUND_LOG_DIR', 'SOULBOUND_BACKUP_DIR',
    'HOST', 'DB_PATH', 'DATABASE_PATH', 'SQLITE_PATH', 'PYTHONPATH',
})


def isolated_predeploy_env(source_env, temporary_dir, port):
    """Create the only permitted FAST/FULL private TCP environment.

    No live DB, listener, secret, Railway endpoint or user-controlled paths
    survive. A dedicated temporary lab and nonproduction port are mandatory.
    """
    work = Path(temporary_dir).resolve(strict=True)
    if not work.is_dir() or not work.name.startswith('sb104_tcp_lab_'):
        raise ValueError('v111 PREDEPLOY: wymagany prywatny katalog testowy')
    if type(port) is not int or not 1025 <= port <= 65535 or port == 4000:
        raise ValueError('v111 PREDEPLOY: niedozwolony port')
    env = {key:value for key,value in source_env.items()
           if key not in _DROP_LIVE_ENV_V111
           and not key.startswith(('RAILWAY_', 'SOULBOUND_SECRET_', 'SOULBOUND_TOKEN_'))}
    env.update({
        'SOULBOUND_HOST':'127.0.0.1',
        'SOULBOUND_PORT':str(port),
        'PORT':str(port),
        'SOULBOUND_DB':str(work/'tcp_test.sqlite'),
        'SOULBOUND_LOG_DIR':str(work/'logs'),
        'SOULBOUND_WORLD_SEED_FILE':str(work/'world_seed.txt'),
        'SOULBOUND_TCP_TEST_CHILD':'1',
        'PYTHONUNBUFFERED':'1',
        'PYTHONDONTWRITEBYTECODE':'1',
        'PYTHONUTF8':'1',
    })
    return env


def enable_isolated_fast_predeploy():
    """Protect a direct FAST invocation BEFORE its first gameplay import."""
    lab = tempfile.TemporaryDirectory(prefix='sb104_tcp_lab_')
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind(('127.0.0.1',0))
            port=sock.getsockname()[1]
        if port == 4000:
            raise RuntimeError('v111 PREDEPLOY: port produkcyjny jest zabroniony')
        env=isolated_predeploy_env(dict(os.environ),lab.name,port)
        db=Path(env['SOULBOUND_DB'])
        if db.exists() or db.is_symlink():
            raise FileExistsError('v111 PREDEPLOY: testowa baza juz istnieje')
        os.environ.clear()
        os.environ.update(env)
        return lab,port
    except BaseException:
        lab.cleanup()
        raise
