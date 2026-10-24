# -*- coding: utf-8 -*-
"""FULL native combat in an isolated, disposable Soulbound server copy.

This does not approximate the combat formulas. It executes server.py unchanged
in a private filesystem with a consistent SQLite backup. No production DB,
network listener, or file from the source installation is opened writable.

The mode is intentionally *outside* the in-session simplified Guardian arena;
users connect to port 4900 locally, on a temporary clone of their characters.
Rewards/XP in this instance are discarded with its database on shutdown.
"""
from __future__ import annotations
import argparse
import os
import time
import signal
from pathlib import Path
from contextlib import closing
import re
import shutil
import socket
import sqlite3
import subprocess
import sys
import tempfile

EXCLUDE_DIRS = frozenset({
    '__pycache__', '.git', 'logs', 'NOWE_WERSJE', 'Soulbound_PREDEPLOY',
    'backups', 'backup', '.venv', 'venv', 'node_modules', 'tmp', 'temp',
})
EXCLUDE_FILES = frozenset({'.env', 'soulbound_control.json',
    'soulbound_launcher.json', 'soulbound_supervisor.json',
    'last_result.json', 'last_predeploy.json'})
DB_EXTENSIONS = ('.db', '.db-wal', '.db-shm', '.sqlite', '.sqlite-wal',
                 '.sqlite-shm', '.sqlite3', '.sqlite3-wal', '.sqlite3-shm')
SECRET_EXTENSIONS = ('.pem', '.key', '.pfx', '.p12')


def _ignore(directory, names):
    ignored = set()
    for name in names:
        path = Path(directory) / name
        lower = name.lower()
        if (path.is_symlink() or (path.is_dir() and lower in EXCLUDE_DIRS)
                or lower in EXCLUDE_FILES or lower.startswith('.env.') or lower.endswith(DB_EXTENSIONS)
                or lower.endswith(SECRET_EXTENSIONS)
                or lower.endswith(('.zip', '.log', '.pyc'))):
            ignored.add(name)
    return ignored


def _port_available(port):
    with socket.socket() as sock:
        sock.bind(('127.0.0.1', port))


def _backup_db(source, destination):
    # Source connection is STRICTLY read-only; SQLite online backup creates a
    # transactionally consistent copy even if source has live WAL writers.
    if not source.is_file():
        # New empty game: actual schema will be created by the private server.
        return False
    with closing(sqlite3.connect(source.resolve().as_uri() + '?mode=ro', uri=True,
                                 timeout=20)) as original:
        with closing(sqlite3.connect(str(destination), timeout=20)) as replica:
            original.backup(replica, pages=256, sleep=0.02)
            row = replica.execute('PRAGMA quick_check').fetchone()
            if not row or row[0] != 'ok':
                raise RuntimeError('Kopia bazy SQLite nie przeszla quick_check.')
            # A DB backed up from a WAL source inherits WAL journal mode.
            # Convert private copy to a standalone DELETE-mode database so
            # no orphan *-wal/*-shm sidecars are needed when launching.
            replica.execute('PRAGMA wal_checkpoint(TRUNCATE)')
            mode=replica.execute('PRAGMA journal_mode=DELETE').fetchone()[0]
            if mode.lower()!='delete':
                raise RuntimeError('Kopia SQLite nie wylaczyla trybu WAL.')
    return True


def make_clone(source: Path, target: Path, database: Path | None = None, fresh=False):
    source = source.resolve()
    target = target.resolve()
    if not (source / 'server.py').is_file() or not (source / 'VERSION').is_file():
        raise ValueError('Katalog zrodlowy musi zawierac server.py i VERSION.')
    if source == target or source in target.parents:
        raise ValueError('Kopia nie moze nadpisac katalogu produkcyjnego.')
    if target.exists():
        raise ValueError('Folder izolowanego serwera juz istnieje.')
    if fresh and database is not None:
        raise ValueError('Nie lacz --fresh z --database. Wybierz tylko jeden tryb.')
    # Never follow symbolic links to files outside the source root.
    shutil.copytree(source, target, ignore=_ignore, symlinks=False)
    origin_db = (database or (source / 'soulbound.db')).resolve()
    if not origin_db.is_file() and not fresh:
        raise FileNotFoundError('Brak bazy postaci: '+str(origin_db)+'; wskaz --database albo --fresh (pusta baza).')
    if not origin_db.is_file() and (source / 'soulbound.db-wal').exists():
        raise RuntimeError('WAL bez glownej bazy: przerwano, aby nie skopiowac blednego stanu.')
    # --fresh MUST never read or copy production accounts, even if a DB exists.
    copied = False if fresh else _backup_db(origin_db, target / 'soulbound.db')
    # Seed and generated world must agree with the original world if present.
    world_seed = source / 'soulbound_world_seed.txt'
    if world_seed.is_file():
        shutil.copy2(world_seed, target / 'soulbound_world_seed.txt')
    return copied


def _private_env(folder, port):
    env = os.environ.copy()
    # Admin identity mapping is not a password; keep it so admin live works
    # after logging in with a copied account on this private listener.
    admin_accounts = env.get("SOULBOUND_ADMIN_ACCOUNTS", "")
    for name in list(env):
        upper = name.upper()
        # A private game subprocess must never inherit cloud/app credentials.
        # Keep ordinary OS variables (PATH, SYSTEMROOT, TEMP, HOME) intact.
        if (upper.startswith(("SOULBOUND_", "RAILWAY_", "SMTP_", "AWS_",
                               "AZURE_", "GOOGLE_", "GITHUB_", "GH_",
                               "OPENAI_", "HF_", "WANDB_"))
                or upper in ("DATABASE_URL", "REDIS_URL")
                or re.search(r'(?:^|_)(?:PASSWORD|SECRET|TOKEN|CREDENTIALS|API_KEY|PRIVATE_KEY)$', upper)):
            env.pop(name, None)
    for name in ('PORT', 'RAILWAY_TCP_APPLICATION_PORT',
                 'RAILWAY_VOLUME_MOUNT_PATH', 'SOULBOUND_CONTROL_FILE',
                 'SOULBOUND_CONTROL_TOKEN', 'SOULBOUND_CONTROL_FALLBACK_FILE',
                 'SOULBOUND_DB', 'SOULBOUND_LOG_DIR', 'SOULBOUND_WORLD_SEED_FILE',
                 'SOULBOUND_HOST', 'SOULBOUND_PORT'):
        env.pop(name, None)
    env.update({
        'SOULBOUND_HOST': '127.0.0.1', 'SOULBOUND_PORT': str(port),
        'SOULBOUND_DB': str(folder / 'soulbound.db'),
        'SOULBOUND_WORLD_SEED_FILE': str(folder / 'soulbound_world_seed.txt'),
        'SOULBOUND_LOG_DIR': str(folder / 'logs'),
        'PYTHONUTF8': '1', 'PYTHONIOENCODING': 'utf-8',
        'PYTHONUNBUFFERED': '1',
    })
    if admin_accounts.strip():
        env['SOULBOUND_ADMIN_ACCOUNTS'] = admin_accounts
    return env


def _process_alive(pid):
    """Check the owning game process; fail closed if the owner has exited."""
    if not isinstance(pid, int) or pid <= 0 or pid == os.getpid():
        return False
    if os.name == 'nt':
        import ctypes
        kernel = ctypes.windll.kernel32
        kernel.OpenProcess.argtypes = [ctypes.c_uint32, ctypes.c_int, ctypes.c_uint32]
        kernel.OpenProcess.restype = ctypes.c_void_p
        kernel.WaitForSingleObject.argtypes = [ctypes.c_void_p, ctypes.c_uint32]
        kernel.WaitForSingleObject.restype = ctypes.c_uint32
        kernel.CloseHandle.argtypes = [ctypes.c_void_p]
        kernel.CloseHandle.restype = ctypes.c_int
        # SYNCHRONIZE | PROCESS_QUERY_LIMITED_INFORMATION, no mutation rights.
        handle = kernel.OpenProcess(0x00100000 | 0x1000, False, pid)
        if not handle:
            return False
        try:
            return kernel.WaitForSingleObject(handle, 0) == 0x102  # WAIT_TIMEOUT
        finally:
            kernel.CloseHandle(handle)
    try:
        os.kill(pid, 0)
        return True
    except (OSError, ValueError):
        return False


def _run_until_stopped(child, stop_file=None, parent_pid=None):
    """Stop private game on explicit marker or death of its owner."""
    while True:
        result = child.poll()
        if result is not None:
            return result
        if stop_file is not None and stop_file.exists():
            print('ADMIN LIVE: otrzymano polecenie zatrzymania prywatnej areny.', flush=True)
            return 0
        if parent_pid is not None and not _process_alive(parent_pid):
            print('ADMIN LIVE: glowny serwer zakonczyl prace; zamykam prywatna arene.', flush=True)
            return 0
        time.sleep(0.25)


def main(argv=None):
    parser = argparse.ArgumentParser(description='Izolowany PRAWDZIWY silnik walki Soulbound')
    parser.add_argument('--source', type=Path, default=Path(__file__).resolve().parent)
    parser.add_argument('--database', type=Path, default=None)
    parser.add_argument('--port', type=int, default=4900)
    parser.add_argument('--verify-only', action='store_true')
    parser.add_argument('--fresh', action='store_true', help='Nowy, pusty serwer testowy; bez danych postaci')
    parser.add_argument('--stop-file', type=Path, default=None, help='Prywatny znacznik zatrzymania instancji')
    parser.add_argument('--parent-pid', type=int, default=None, help='PID serwera nadzorujacego; po jego zamknieciu zakoncz test')
    args = parser.parse_args(argv)
    # External shutdown (including Windows stop processes) must still remove
    # the temporary copy; SIGTERM normally skips Python finally blocks.
    def _terminate_lab(_signum, _frame):
        raise KeyboardInterrupt()
    try:
        signal.signal(signal.SIGTERM, _terminate_lab)
        if hasattr(signal, 'SIGBREAK'):
            signal.signal(signal.SIGBREAK, _terminate_lab)
    except (ValueError, OSError):  # AUDIT_INTENTIONAL_PASS: signal handlers are unavailable in worker threads; shutdown retains normal cleanup
        pass
    if not 1024 <= args.port <= 65535 or args.port == 4000:
        parser.error('Port musi byc od 1024 do 65535 i inny niz produkcyjny 4000.')
    _port_available(args.port)
    source = args.source.resolve()
    scratch = Path(tempfile.mkdtemp(prefix='Soulbound_UOSS_REAL_'))
    private_root = scratch / 'gra'
    child = None
    try:
        print('KOPIUJE TYLKO DO IZOLACJI. Gra produkcyjna pozostaje nietknieta.', flush=True)
        default_db = Path(os.environ.get("SOULBOUND_DB", str(source / "soulbound.db")))
        copied = make_clone(source, private_root, None if args.fresh else (args.database or default_db), fresh=args.fresh)
        print('Baza w kopii: '+('migawka SQLite (WAL uwzgledniony)' if copied else 'nowa, pusta'),flush=True)
        if args.verify_only:
            print('PASS: izolacja plikow i kopia bazy. Niczego nie uruchomiono.', flush=True)
            return 0
        env = _private_env(private_root, args.port)
        print(f'PRAWDZIWY SILNIK: serwer testowy 127.0.0.1:{args.port}', flush=True)
        print('Polacz klient MUD z adresem 127.0.0.1 i portem '+str(args.port)+'.',flush=True)
        print('Tu istnieja rzeczywiste skille, AI, krytyki, EXP i loot, ale WSZYSTKO na kopii.',flush=True)
        print('Po zamknieciu kopia, nagrody i zmiany zostana USUNIETE.', flush=True)
        print('Ctrl+C wylacza tylko serwer testowy, NIE ten na porcie 4000.', flush=True)
        child = subprocess.Popen([sys.executable, '-u', 'server.py'], cwd=private_root, env=env)
        try:
            return _run_until_stopped(child, args.stop_file, args.parent_pid)
        except KeyboardInterrupt:
            print('Zatrzymuje wylacznie testowa instancje...',flush=True)
            return 0
    finally:
        if child is not None and child.poll() is None:
            child.terminate()
            try:
                child.wait(timeout=15)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait(timeout=10)
        # Never clean the source; only the unique private directory we created.
        shutil.rmtree(scratch, ignore_errors=False)
        print('Kopia testowa zostala usunieta; produkcyjna baza nienaruszona.',flush=True)


if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print('Zakonczono tylko instancje testowa.', flush=True)
        sys.exit(0)
    except (OSError, ValueError, RuntimeError, sqlite3.Error) as exc:
        print('IZOLOWANE UOSS: ODMOWA - '+str(exc), file=sys.stderr, flush=True)
        sys.exit(2)
