# -*- coding: utf-8 -*-
"""Private worker: bootstrap current schemas into an exclusively NEW database."""
from __future__ import annotations
import argparse
import os
from pathlib import Path
import tempfile


def initialize(database):
    database = Path(database).resolve()
    temporary = Path(tempfile.gettempdir()).resolve()
    relative = database.relative_to(temporary)
    if len(relative.parts) < 2 or not relative.parts[0].startswith('sb112_current_install_'):
        raise ValueError('Bootstrap only works inside its disposable current-install lab')
    if database.name != 'new.sqlite' or database.is_symlink():
        raise ValueError('Unexpected bootstrap database path')
    if (os.environ.get('SOULBOUND_V112_STAGING') != '1'
            or os.environ.get('SOULBOUND_DB') != str(database)
            or os.environ.get('SOULBOUND_HOST') != '127.0.0.1'):
        raise ValueError('Missing isolated current bootstrap environment')
    # Exclusive creation makes overwriting an existing SQLite file impossible.
    descriptor = os.open(database, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    os.close(descriptor)
    import server
    from systems.current_install_ledger import initialize_empty_ledger
    db = None
    try:
        db = server.Database(str(database))
        result = initialize_empty_ledger(db.conn)
        db.conn.execute('PRAGMA wal_checkpoint(TRUNCATE)')
        db.conn.close()
        db = None
        return result
    finally:
        if db is not None:
            db.conn.close()
        server._BOOT_SOCKET.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', required=True)
    args = parser.parse_args()
    result = initialize(args.database)
    print('CURRENT EMPTY DATABASE BOOTSTRAP PASS: ' + result['origin'])

if __name__ == '__main__':
    main()
