# -*- coding: utf-8 -*-
"""Ochrona prywatnego TCP oraz czystej paczki Soulbound v104.

Bez importowania serwera, bez otwierania portu, bez dostępu do baz graczy.
"""
from __future__ import annotations

import os
import re
from pathlib import Path

# Żadne połączenie testowe nie może odziedziczyć produkcyjnych parametrów.
DROP_ENV = {
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
}

# Nazwy SQLite - także pomocnicze WAL/SHM/journal i ukryte kopie baz.
_DB_PATTERN = re.compile(r'(?i)(?:\.db|\.sqlite|\.sqlite3)(?:-(?:wal|shm|journal))?$')
_FORBIDDEN_NAMES = {'.env', 'id_rsa', 'id_ed25519', 'credentials.json', 'token.json'}
_FORBIDDEN_DIRS = {'__pycache__', '.git', '.venv', 'venv'}


def private_tcp_environment(source_env, temporary_dir, port):
    """Utwórz środowisko nowego serwera *wyłącznie* na loopback i w /tmp.

    Port 4000 odrzucony; wszystkie ścieżki bazy/logów poza testem usunięte.
    `temporary_dir` to istniejący katalog tymczasowy o kontrolowanej nazwie.
    """
    work = Path(temporary_dir).resolve(strict=True)
    if not work.is_dir() or not work.name.startswith('sb104_tcp_lab_'):
        raise ValueError('TCP: wymagany odizolowany katalog testowy sb104_tcp_lab_.')
    if type(port) is not int or not (1025 <= port <= 65535) or port == 4000:
        raise ValueError('TCP: niedozwolony port; produkcyjny 4000 jest zabroniony.')
    env = {k:v for k,v in source_env.items()
           if k not in DROP_ENV and not k.startswith(('RAILWAY_', 'SOULBOUND_SECRET_', 'SOULBOUND_TOKEN_'))}
    env.update({
        'SOULBOUND_HOST': '127.0.0.1',
        'SOULBOUND_PORT': str(port),
        'PORT': str(port),
        'SOULBOUND_DB': str(work / 'tcp_test.sqlite'),
        'SOULBOUND_LOG_DIR': str(work / 'logs'),
        'SOULBOUND_WORLD_SEED_FILE': str(work / 'world_seed.txt'),
        'SOULBOUND_TCP_TEST_CHILD': '1',
        'PYTHONUNBUFFERED': '1',
        'PYTHONDONTWRITEBYTECODE': '1',
        'PYTHONUTF8': '1',
    })
    return env


def forbidden_release_paths(names):
    """Zwraca zakazane ścieżki w archiwum; bada też podkatalogi."""
    problems=[]
    for path in names:
        pieces = Path(path.replace('\\', '/')).parts
        if path.startswith('/') or '..' in pieces or not pieces:
            problems.append(path)
            continue
        if any(piece.lower() in _FORBIDDEN_DIRS for piece in pieces[:-1]):
            problems.append(path)
            continue
        name=pieces[-1].lower()
        if (name in _FORBIDDEN_NAMES or _DB_PATTERN.search(name)
                or name.endswith(('.pyc','.pyo','.log','.bak','.db3'))
                or name.startswith('.env.') or name.endswith(('.pem','.key'))):
            problems.append(path)
    return problems
