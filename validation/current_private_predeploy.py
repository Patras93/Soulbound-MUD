# -*- coding: utf-8 -*-
"""Version-neutral private FAST/FULL PREDEPLOY staging (v113+).

Never imports a previous release's activator or uses the installed database.
Every run creates its own TEMP directory and ephemeral localhost listener.
"""
from __future__ import annotations
import os
from pathlib import Path
import socket
import tempfile
from systems.universal_activation import _test_database

PREFIX='sbcurrent_fast_'
DROP_ENV=frozenset({
    'PORT','RAILWAY_TCP_APPLICATION_PORT','SOULBOUND_PORT',
    'SOULBOUND_HOST','SOULBOUND_DB','DATABASE_URL',
    'RAILWAY_VOLUME_MOUNT_PATH','SOULBOUND_WORLD_SEED_FILE',
    'SOULBOUND_WORLD_SEED','SOULBOUND_CONTROL_FILE',
    'SOULBOUND_CONTROL_TOKEN','SOULBOUND_ADMIN_ACCOUNTS',
    'SOULBOUND_FULL_AUDIT','SOULBOUND_HISTORICAL_AUDITS',
    'SOULBOUND_ULTRA_SOURCE_DB','SOULBOUND_SMTP_PASSWORD',
    'SOULBOUND_MAIL_PASSWORD','SMTP_PASSWORD','SOULBOUND_LOG_DIR',
    'SOULBOUND_BACKUP_DIR','HOST','DB_PATH','DATABASE_PATH',
    'SQLITE_PATH','PYTHONPATH',
})

def _validate(directory,port):
    home=Path(directory).resolve(strict=True)
    if (not home.is_dir() or not home.name.startswith(PREFIX)
        or home.is_symlink() or type(port) is not int
        or not 1025<=port<=65535 or port==4000
        or home.parent!=Path(tempfile.gettempdir()).resolve(strict=True)):
        raise PermissionError('PREDEPLOY: wymagane prywatne TEMP i localhost')
    return home

def isolated_predeploy_env(source_env,directory,port):
    home=_validate(directory,port)
    # No inherited staging flag, source database, secret or previous release
    # authority is permitted to influence this test environment.
    env={k:v for k,v in source_env.items()
         if k not in DROP_ENV and not k.startswith(('SOULBOUND_','RAILWAY_'))}
    env.update(SOULBOUND_HOST='127.0.0.1',SOULBOUND_PORT=str(port),
               PORT=str(port),SOULBOUND_DB=str(home/'tcp_test.sqlite'),
               SOULBOUND_WORLD_SEED_FILE=str(home/'world_seed.txt'),
               SOULBOUND_LOG_DIR=str(home/'logs'),
               SOULBOUND_UNIVERSAL_STAGING='1',
               SOULBOUND_TCP_TEST_CHILD='1',
               PYTHONUNBUFFERED='1',PYTHONDONTWRITEBYTECODE='1',
               PYTHONUTF8='1')
    return env

def authorize_private_lab(directory,port):
    home=_validate(directory,port)
    database=home/'tcp_test.sqlite'
    if (database.is_symlink() or os.environ.get('SOULBOUND_DB')!=str(database)
        or os.environ.get('SOULBOUND_HOST')!='127.0.0.1'
        or os.environ.get('SOULBOUND_PORT')!=str(port)
        or os.environ.get('PORT')!=str(port)
        or os.environ.get('SOULBOUND_UNIVERSAL_STAGING')!='1'
        or os.environ.get('SOULBOUND_TCP_TEST_CHILD')!='1'
        or not _test_database(database)):
        raise PermissionError('PREDEPLOY: odrzucono nieizolowana baze lub port')
    return True

def enable_isolated_fast_predeploy():
    lab=tempfile.TemporaryDirectory(prefix=PREFIX)
    try:
        with socket.socket(socket.AF_INET,socket.SOCK_STREAM) as probe:
            probe.bind(('127.0.0.1',0))
            port=probe.getsockname()[1]
        if port==4000:raise PermissionError('Port produkcyjny 4000 zabroniony')
        env=isolated_predeploy_env(dict(os.environ),lab.name,port)
        if Path(env['SOULBOUND_DB']).exists():
            raise FileExistsError('Testowa baza juz istnieje')
        os.environ.clear()
        os.environ.update(env)
        authorize_private_lab(lab.name,port)
        return lab,port
    except BaseException:
        lab.cleanup()
        raise
